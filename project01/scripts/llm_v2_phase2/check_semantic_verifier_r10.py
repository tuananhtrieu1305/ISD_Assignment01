"""Offline tests for one-call semantic review, hard integrity and full-profile guard."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import asyncio,copy,json,sys,tempfile
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'web/backend'))
from project01_llm_v2.agents import SemanticVerifier,CodeVerifier,AgenticRuntime
from project01_llm_v2.schemas import Draft,Claim,SearchResult,MetaData
from project01_llm_v2.transport import create_app
from project01_llm_v2.generation import risk_summary

checks=[]
def ok(value,name):assert value,name;checks.append(name)
E=[SearchResult(chunk_id='e1',chunk_index=0,score=.1,content='Walking 30 minutes on 5 days per week is part of a combined lifestyle intervention.',
 metadata=MetaData(document_id='d1',title='Offline synthetic evidence',source='https://example.org/test',source_refs=[{'source':'test-only'}]))]
D=Draft(answer_vi='Trong chương trình lối sống kết hợp, 150 phút/tuần tương đương 30 phút × 5 ngày. [Nguồn 1]',
 claims=[Claim(id='1',text_vi='30 phút mỗi ngày trong 5 ngày tương đương 150 phút/tuần.',citation_chunk_ids=['e1'])])
def decision(draft=D):return {'approved':True,'numeric_ok':True,'scope_ok':True,'answer_matches_claims':True,
 'claim_reviews':[{'claim_id':c.id,'status':'supported','evidence_ids':c.citation_chunk_ids,'reason_vi':'Phép quy đổi có căn cứ trong đoạn nguồn.'} for c in draft.claims],
 'feedback':'Đủ căn cứ trong evidence; không bảo đảm hiệu quả cá nhân.','corrected_draft':None}
class Gateway:
 def __init__(self,value):self.value=value;self.calls=[]
 async def generate(self,prompt,call_id,tokens):
  self.calls.append((prompt,call_id,tokens));return {'text':self.value if isinstance(self.value,str) else json.dumps(self.value,ensure_ascii=False),'cache_status':'offline_test_double'}

async def main():
 review,_=await CodeVerifier().verify('Q',D,E)
 ok(not review['approved'],'old exact-digit checker reproduces false rejection of 30 times5 equals150')
 g=Gateway(decision());review,_=await SemanticVerifier(g).verify('Q',D,E,'offline')
 ok(review['approved'] and len(g.calls)==1,'semantic verifier can accept a supported arithmetic paraphrase with one API slot')
 ok(review['provider']=='gemini_semantic_plus_local_integrity','semantic provider is disclosed')
 g=Gateway(decision());bad=D.model_copy(deep=True);bad.claims[0].citation_chunk_ids=['unknown']
 review,_=await SemanticVerifier(g).verify('Q',bad,E,'offline')
 ok(not review['approved'] and len(g.calls)==0,'unknown citation cannot be waved through by an LLM')
 risk={'score':.3,'class_id':0,'class_name':'no diabetes','unit':'historical_binary_model_score','calibrated_incidence_risk':False}
 draft=D.model_copy(deep=True);draft.answer_vi=risk_summary(risk)+draft.answer_vi
 g=Gateway(decision(draft));changed=draft.model_copy(deep=True);changed.answer_vi=changed.answer_vi.replace('0.300000','0.900000')
 review,_=await SemanticVerifier(g).verify('Q',changed,E,'offline',risk)
 ok(not review['approved'] and not g.calls,'changed local CDC score remains a hard failure')
 fixed=D.model_copy(deep=True);fixed.answer_vi='Chỉ diễn đạt kết quả trong phạm vi chương trình kết hợp. [Nguồn 1]'
 value=decision(fixed);value['corrected_draft']=fixed.model_dump();g=Gateway(value)
 review,_=await SemanticVerifier(g).verify('Q',D,E,'offline')
 ok(review['approved'] and review['revised_draft']['answer_vi']==fixed.answer_vi,'one-call correction is returned for release after integrity checks')
 value=decision();value['claim_reviews'][0]['status']='unsupported';g=Gateway(value)
 review,_=await SemanticVerifier(g).verify('Q',D,E,'offline')
 ok(not review['approved'],'approved=true cannot override an unsupported claim status')
 value=decision();value['corrected_draft']={'answer_vi':'Chưa đủ căn cứ.','claims':[],'limitations':[]};value['claim_reviews']=[]
 review,_=await SemanticVerifier(Gateway(value)).verify('Q',D,E,'offline')
 ok(not review['approved'],'Verifier cannot erase every claim and call a generic abstention an approved correction')
 for value in ['invalid JSON',{'approved':True},dict(decision(),claim_reviews=[])]:
  g=Gateway(value);review,_=await SemanticVerifier(g).verify('Q',D,E,'offline')
  ok(not review['approved'] and len(g.calls)==1,'invalid or incomplete verifier response fails closed without retry')

 class BudgetRuntime:
  def __init__(self,*args,**kwargs):pass
  def readiness(self):return {'status':'ready','usage':{'generation_cap':18,'generation_attempts':15}}
 with tempfile.TemporaryDirectory() as folder,patch('project01_llm_v2.transport.AgenticRuntime',BudgetRuntime),patch('project01_llm_v2.transport.threading.Thread'):
  client=create_app(folder,True).test_client()
  response=client.post('/api/v2/compare',json={'question':'Q','mode':'combined','profile':None})
  ok(response.status_code==422,'combined mode cannot create a job without a profile')
  response=client.post('/api/v2/compare',json={'question':'Q','mode':'knowledge'})
  ok(response.status_code==429 and '4' in response.json['error']['message'],'backend reserves four generation slots')
 ok('4' in str(AgenticRuntime.readiness.__code__.co_consts),'runtime exposes updated generation budget')
 output={'status':'PASS','checks':checks,'new_generation_API_calls':0,'new_embedding_API_calls':0}
 folder=P/'artifacts/llm_v2/phase2/development/semantic_verifier_r10';folder.mkdir(parents=True,exist_ok=True)
 (folder/'unit_verification.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(output,ensure_ascii=False,indent=2))
asyncio.run(main())
