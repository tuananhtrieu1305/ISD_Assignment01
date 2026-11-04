"""Check the same source standard reaches both real prompt paths; zero provider calls."""
from pathlib import Path
from types import SimpleNamespace
import ast,asyncio,hashlib,json,tempfile

P=Path(__file__).resolve().parents[2];backend=P/'web/backend/project01_llm_v2'
policy_path=P/'config/prompts/source_verification_vi.txt'
assert policy_path.is_file(),'Shared source policy missing'
policy=policy_path.read_text(encoding='utf-8').strip()
assert policy and all(text not in policy for text in ['58%','50%','Đi bộ','nếu gặp câu hỏi'])
checks=[]
def ok(value,name):
    assert value,name
    checks.append(name)

ns={'Path':Path,'__file__':str(backend/'generation.py')}
tree=ast.parse((backend/'generation.py').read_text(encoding='utf-8'))
loader=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='load_source_verification_policy')
exec(compile(ast.Module(body=[loader],type_ignores=[]),'<actual-policy-loader>','exec'),ns)
ok(ns['load_source_verification_policy']()==policy,'loader reads the standalone UTF-8 policy')
with tempfile.TemporaryDirectory() as temporary:
    blank=Path(temporary)/'empty.txt';blank.write_text('  ',encoding='utf-8')
    try:ns['load_source_verification_policy'](blank)
    except ValueError:pass
    else:raise AssertionError('Empty policy silently accepted')
ok(True,'empty policy is rejected explicitly')

class Template:
    @staticmethod
    def from_messages(rows):return SimpleNamespace(rows=rows)
ns.update(ChatPromptTemplate=Template,SYSTEM_PROMPT='Existing Reporter rules',SOURCE_VERIFICATION_POLICY=policy,
          Sequence=list,SearchResult=object,BaseMessage=object)
builder=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='PromptBuilder')
exec(compile(ast.Module(body=[builder],type_ignores=[]),'<actual-prompt-builder>','exec'),ns)
ok(policy in ns['PromptBuilder']().template.rows[0][1],'Reporter system message includes the shared policy verbatim')

agents=ast.parse((backend/'agents.py').read_text(encoding='utf-8'))
runtime=next(node for node in agents.body if isinstance(node,ast.ClassDef) and node.name=='AgenticRuntime')
direct=next(node for node in runtime.body if isinstance(node,ast.AsyncFunctionDef) and node.name=='direct')
class Gateway:
    def __init__(self):self.observations=[];self.config={'generation_model':'test'};self.prompts=[]
    async def generate(self,prompt,call_id,tokens):
        self.prompts.append(prompt);return {'text':'offline fixture','cache_status':'mock'}
ns.update(time=SimpleNamespace(monotonic=lambda:0),CALIBRATION_POLICY='Existing calibration rules',
          SOURCE_POLICY_SHA256=hashlib.sha256(policy.encode()).hexdigest())
exec(compile(ast.Module(body=[direct],type_ignores=[]),'<actual-direct-method>','exec'),ns)
async def main():
    gateway=Gateway();result=await ns['direct'](SimpleNamespace(gateway=gateway),'Câu hỏi bất kỳ','offline-policy-r9')
    ok(policy in gateway.prompts[0],'direct branch receives exactly the same source policy')
    ok(len(gateway.prompts)==1,'direct branch still makes one generation call')
    ok(result['source_policy_sha256']==ns['SOURCE_POLICY_SHA256'],'direct result records the actual policy hash')
    ok('kiến thức sẵn có' in gateway.prompts[0],'direct is still allowed to use its knowledge')
    ok('58%' not in policy and '50%' not in policy,'policy contains no question-specific answer override')
    print(json.dumps({'status':'PASS','checks':checks,'new_generation_API_calls':0,'new_embedding_API_calls':0},ensure_ascii=False,indent=2))
asyncio.run(main())
