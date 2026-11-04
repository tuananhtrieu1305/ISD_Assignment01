"""Exercise actual changed functions with stdlib-only fakes; no API or model calls."""
from pathlib import Path
from types import SimpleNamespace
import abc,ast,asyncio,json,math,re

P=Path(__file__).resolve().parents[2]
checks=[]
def ok(condition,name):
    assert condition,name
    checks.append(name)

def definitions(module,names,namespace):
    tree=ast.parse((P/'web/backend/project01_llm_v2'/f'{module}.py').read_text(encoding='utf-8'))
    selected=[node for node in tree.body if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names]
    assert len(selected)==len(names),f'Missing definitions: {names}'
    exec(compile(ast.Module(body=selected,type_ignores=[]),f'<actual-{module}>','exec'),namespace)

ns={'math':math,'re':re,'json':json,'ABC':abc.ABC,'abstractmethod':abc.abstractmethod,'BaseMessage':object}
definitions('generation',['risk_summary','BaseGenerator'],ns)
definitions('agents',['CodeVerifier'],ns)

RISK={'score':0.71234567,'class_id':1,'class_name':'prediabetes or diabetes','unit':'historical_binary_model_score','calibrated_incidence_risk':False,'model_sha256':'test-model'}
prefix=ns['risk_summary'](RISK)
ok('0.712346' in prefix and 'không phải xác suất mắc bệnh năm tới' in prefix,'tool summary preserves score and meaning')
ok(ns['risk_summary'](None)=='','knowledge-only behavior has no synthetic risk score')
for bad in [dict(RISK,score=float('nan')),dict(RISK,score=1.5),dict(RISK,calibrated_incidence_risk=True),dict(RISK,class_id=0),dict(RISK,class_name='made up')]:
    try:ns['risk_summary'](bad)
    except (ValueError,TypeError):pass
    else:raise AssertionError('invalid local risk accepted')
ok(True,'invalid score, class and calibration metadata rejected')

class Gateway:
    def __init__(self):self.calls=[]
    async def generate(self,prompt,call_id,max_tokens):
        self.calls.append((prompt,call_id,max_tokens));return {'text':'draft'}
class Builder:
    def build_messages(self,question,results):return [SimpleNamespace(type='human',content=question)]
class Generator(ns['BaseGenerator']):
    pass

async def main():
    gateway=Gateway();generator=Generator(gateway,'offline',Builder())
    await generator.generate('Question',[],risk=RISK)
    prompt=gateway.calls[0][0]
    ok(len(gateway.calls)==1,'Reporter still uses one generation call')
    ok('0.712346' in prompt and 'CDC' in prompt,'Reporter receives local tool output')
    ok('high_bp' not in prompt and 'income' not in prompt,'Reporter does not receive raw profile fields')
    await generator.generate('Knowledge question',[])
    ok('0.712346' not in gateway.calls[1][0],'risk context cannot leak into knowledge-only requests')

    evidence=[SimpleNamespace(chunk_id='c1',content='Physical activity helps control blood glucose.',metadata=SimpleNamespace(source_refs=[{'source':'public snapshot'}]))]
    claim=SimpleNamespace(id='1',text_vi='Physical activity helps control blood glucose.',citation_chunk_ids=['c1'])
    draft=SimpleNamespace(answer_vi=prefix+'Vận động giúp kiểm soát đường huyết. [Nguồn 1]',claims=[claim])
    verifier=ns['CodeVerifier']()
    review,row=await verifier.verify('Q',draft,evidence,risk=RISK)
    ok(review['approved'] and review['risk_integrity_ok'] and row['sdk_calls']==0,'Verifier checks the composed answer and local tool result without an API call')
    draft.answer_vi=draft.answer_vi.replace('0.712346','0.999999')
    review,_=await verifier.verify('Q',draft,evidence,risk=RISK)
    ok(not review['approved'] and 'risk_summary_mismatch' in review['code_errors'],'Verifier rejects altered local score')
    draft.answer_vi='Chưa đủ căn cứ.'
    review,_=await verifier.verify('Q',draft,[],risk=None)
    ok(not review['approved'],'missing citations are still rejected')
    empty=SimpleNamespace(answer_vi='Chưa đủ căn cứ.',claims=[])
    review,_=await verifier.verify('Q',empty,[],risk=None)
    ok(review['approved'],'knowledge-only abstention still works')
    print(json.dumps({'status':'PASS','checks':checks,'live_API_calls':0},ensure_ascii=False,indent=2))

asyncio.run(main())
