# GENERATED from notebooks/01_Data_KB_RAG.ipynb; source SHA256 e66fdae9d414f4450b83ae1c19a4ee9e6cd184103ece1c1eeeed2c05b67aeb5f
# Edit notebook cells; export with scripts/llm_v2_phase2/notebooks.py export.
"""Shared Gemini SDK, durable call cache and cross-process free-tier queue."""

from pathlib import Path

from datetime import datetime,timezone

from zoneinfo import ZoneInfo

from contextlib import contextmanager

import asyncio,fcntl,hashlib,json,os,sqlite3,threading,time

from google import genai

from google.genai import types

from langchain_core.language_models.chat_models import BaseChatModel

from langchain_core.messages import AIMessage

from langchain_core.outputs import ChatGeneration,ChatResult

from pydantic import ConfigDict

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temporary.replace(path)

def load_key(root):
    key=os.environ.get('GEMINI_API_KEY','').strip()
    if not key and (Path(root)/'.env').exists():
        for line in (Path(root)/'.env').read_text().splitlines():
            name,_,value=line.partition('=')
            if name.strip()=='GEMINI_API_KEY':key=value.strip().strip('\"\'')
    return key

class ProviderUnavailable(RuntimeError):
    def __init__(self,code,message):super().__init__(message);self.code=code

class GeminiGateway:
    """One file lock serializes generation/embedding across CLI and Flask workers.

    Claims are written before sending. An unknown/failed claim never silently
    replays; successfully cached calls let an interrupted pipeline resume stages.
    """
    def __init__(self,root,allow_api=False):
        self.root=Path(root)
        active=self.root/'docs/llm_v2/runtime_config.json'
        self.config=read_json(active if active.exists() else self.root/'docs/llm_v2/provider_config.example.json')
        assert self.config['allow_paid_api'] is False and self.config['paid_spend_limit_usd']==0
        assert self.config.get('endpoint','v1beta/interactions') in {'v1beta/interactions','v1beta/generateContent'}
        self.key=load_key(self.root);self.allow_api=allow_api
        self.folder=self.root/'artifacts/llm_v2/runtime';self.folder.mkdir(parents=True,exist_ok=True)
        self.db=self.folder/'calls.sqlite3';self.lock=threading.Lock()
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS calls(id TEXT PRIMARY KEY,kind TEXT,day TEXT,created REAL,status TEXT,request TEXT,response TEXT)')
            # Preserve known Phase1 consumption in the provider day of its receipt.
            if not db.execute('SELECT 1 FROM calls LIMIT 1').fetchone():
                for name,kind in [('gemini_preflight.json','generation'),('gemini_interactions_preflight.json','generation'),('gemini_embedding_preflight.json','embedding')]:
                    row=read_json(self.root/'artifacts/llm_v2/phase1'/name)
                    stamp=datetime.fromisoformat(row['date']).timestamp();day=datetime.fromtimestamp(stamp,timezone.utc).astimezone(ZoneInfo('America/Los_Angeles')).date().isoformat()
                    db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?)',('phase1-'+name,kind,day,stamp,'historical','{}','{}'))
        self.client=None;self.observations=[]

    def connect(self):return sqlite3.connect(self.db,timeout=120)

    @contextmanager
    def exclusive(self):
        with self.lock, (self.folder/'queue.lock').open('a') as handle:
            fcntl.flock(handle,fcntl.LOCK_EX)
            try:yield
            finally:fcntl.flock(handle,fcntl.LOCK_UN)

    def usage(self):
        day=datetime.now(ZoneInfo('America/Los_Angeles')).date().isoformat()
        with self.connect() as db:
            counts=dict(db.execute('SELECT kind,count(*) FROM calls WHERE day=? GROUP BY kind',(day,)))
            last=db.execute("SELECT status,created FROM calls WHERE kind='generation' ORDER BY created DESC LIMIT 1").fetchone()
        return {'provider_day':day,'generation_attempts':counts.get('generation',0),'embedding_attempts':counts.get('embedding',0),
                'generation_cap':18,'embedding_cap':900,'external_usage_unknown':True,'paid_budget_usd':0,
                'last_generation_status':last[0] if last else None,'last_generation_at':last[1] if last else None,
                'readiness_is_not_live_provider_probe':True}

    def call(self,kind,body,call_id):
        started=time.monotonic();identifier=digest({'id':call_id,'kind':kind,'body':body})
        with self.exclusive():
            with self.connect() as db:old=db.execute('SELECT status,response FROM calls WHERE id=?',(identifier,)).fetchone()
            if old:
                if old[0]=='complete':
                    result=json.loads(old[1]);result['cache_status']='local_cache'
                    result['original_provider_latency_ms']=result['latency_ms'];result['latency_ms']=(time.monotonic()-started)*1000
                    self.observations.append({k:v for k,v in result.items() if k not in {'text','vectors'}}|{'kind':kind})
                    return result
                raise ProviderUnavailable('claim_'+old[0],'Lượt API này đã được gửi nhưng chưa có kết quả hoàn chỉnh; không tự gửi lại.')
            if not self.allow_api:raise ProviderUnavailable('api_disabled','RUN_API=False; chưa cho phép gọi API.')
            if not self.key:raise ProviderUnavailable('missing_key','Backend chưa có GEMINI_API_KEY.')
            now=time.time();day=datetime.now(ZoneInfo('America/Los_Angeles')).date().isoformat()
            cap,rpm,tpm=(18,4,250000) if kind=='generation' else (900,60,30000)
            # Conservative byte upper bound for input token rate, plus output reserve.
            token_reserve=len(json.dumps(body,ensure_ascii=False).encode())+(body.get('generation_config',{}).get('max_output_tokens',0))
            if token_reserve>tpm:raise ProviderUnavailable('input_budget','Input vượt ngân sách token của một phút.')
            with self.connect() as db:
                count=db.execute('SELECT count(*) FROM calls WHERE kind=? AND day=?',(kind,day)).fetchone()[0]
                recent=db.execute('SELECT created,request FROM calls WHERE kind=? AND created>? ORDER BY created',(kind,now-60)).fetchall()
            if count>=cap:raise ProviderUnavailable('waiting_quota','Đã dùng ngân sách API hôm nay. Lưu checkpoint và tiếp tục sau ngày reset của provider.')
            recent_tokens=sum(len(request.encode())+768 for _,request in recent)
            if recent and (len(recent)>=rpm or recent_tokens+token_reserve>tpm):
                raise ProviderUnavailable('waiting_minute','Đang chờ hạn mức theo phút; thử lại lượt chưa gửi sau tối đa 60 giây.')
            safe_request=json.dumps(body,ensure_ascii=False).replace(self.key,'[REDACTED]')
            with self.connect() as db:db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?)',(identifier,kind,day,now,'claimed',safe_request,None))
            receipt_folder=self.root/'artifacts/llm_v2/phase2/api_calls';receipt_folder.mkdir(parents=True,exist_ok=True)
            atomic_json(receipt_folder/(identifier+'_claim.json'),{'call_id':identifier,'kind':kind,'created':now,'call_prefix':call_id,'request':json.loads(safe_request),'status':'claimed'})
            try:
                if self.client is None:
                    self.client=genai.Client(api_key=self.key,http_options=types.HttpOptions(api_version='v1beta',timeout=180000,retry_options=types.HttpRetryOptions(attempts=0)))
                if kind=='generation' and body.get('endpoint',self.config.get('endpoint'))=='v1beta/generateContent':
                    config=body['generation_config']
                    response=self.client.models.generate_content(model=body['model'],contents=body['input'],
                        config=types.GenerateContentConfig(temperature=config['temperature'],max_output_tokens=config['max_output_tokens'],
                            thinking_config=types.ThinkingConfig(thinking_level=config['thinking_level'])))
                    payload=response.model_dump(mode='json',exclude_none=True)
                    candidates=payload.get('candidates',[])
                    text='\n'.join(p.get('text','') for c in candidates for p in c.get('content',{}).get('parts',[]) if not p.get('thought'))
                    metadata=payload.get('usage_metadata',{})
                    usage={'input_tokens':metadata.get('prompt_token_count'),'output_tokens':metadata.get('candidates_token_count'),
                           'thought_tokens':metadata.get('thoughts_token_count'),'total_tokens':metadata.get('total_token_count'),
                           'provider_usage_metadata':metadata}
                    finish=[c.get('finish_reason') for c in candidates]
                    result={'text':text,'usage':usage,'model_returned':payload.get('model_version'),
                            'response_status':'completed' if text.strip() else 'empty','finish_reasons':finish,'cache_status':'live'}
                    if not text.strip() or any(reason!='STOP' for reason in finish):
                        safe_incomplete=json.loads(json.dumps(result,ensure_ascii=False).replace(self.key,'[REDACTED]'))
                        atomic_json(receipt_folder/(identifier+'_incomplete_response.json'),{'call_id':identifier,'response':safe_incomplete})
                        raise ProviderUnavailable('output_incomplete','Gemini đã phản hồi nhưng đầu ra bị cắt hoặc chưa hoàn tất; không phát hành câu trả lời thiếu.')
                elif kind=='generation':
                    wire={k:v for k,v in body.items() if k!='endpoint'}
                    response=self.client.interactions.create(**wire,api_version='v1beta',timeout=180.0,automatic_continuation=False)
                    payload=response.model_dump(mode='json',exclude_none=True)
                    # Only final output text/usage; never persist thought steps.
                    text=getattr(response,'output_text',None)
                    if not text:
                        texts=[]
                        for step in payload.get('steps',[]):
                            if step.get('type')=='model_output':
                                for item in step.get('content',[]):
                                    if item.get('type')=='text':texts.append(item.get('text',''))
                        text='\n'.join(texts)
                    result={'text':text or '', 'usage':payload.get('usage'), 'model_returned':payload.get('model'),
                            'response_status':payload.get('status'),'cache_status':'live'}
                    if payload.get('status')!='completed' or not text:raise ProviderUnavailable('empty_response','Provider chưa trả câu trả lời hoàn chỉnh.')
                else:
                    response=self.client.models.embed_content(model=body['model'],contents=body['contents'],
                        config=types.EmbedContentConfig(task_type=body['task_type'],output_dimensionality=768))
                    vectors=[r.values for r in response.embeddings]
                    result={'vectors':vectors,'usage':None,'model_returned':body['model'],'cache_status':'live'}
                result.update(model_requested=body['model'],latency_ms=(time.monotonic()-started)*1000,attempts=1,call_id=identifier,
                              paid_cost_usd=0,invoice_verified=False,endpoint=body.get('endpoint',self.config.get('endpoint','v1beta/interactions')) if kind=='generation' else 'v1beta/embedding',sdk_calls=1)
                safe=json.dumps(result,ensure_ascii=False).replace(self.key,'[REDACTED]')
                with self.connect() as db:db.execute('UPDATE calls SET status=?,response=? WHERE id=?',('complete',safe,identifier))
                safe_result=json.loads(safe)
                atomic_json(receipt_folder/(identifier+'_response.json'),{'call_id':identifier,'status':'complete','response':safe_result})
                self.observations.append({k:v for k,v in safe_result.items() if k not in {'text','vectors'}}|{'kind':kind})
                return safe_result
            except Exception as exc:
                code=getattr(exc,'status_code',getattr(exc,'code',None));status='waiting_quota' if code==429 else 'unknown'
                atomic_json(receipt_folder/(identifier+'_error.json'),{'call_id':identifier,'status':status,'error_type':type(exc).__name__,'http_status':code if isinstance(code,int) else None})
                self.observations.append({'call_id':identifier,'kind':kind,'status':status,'cache_status':'live','model_requested':body['model'],'model_returned':None,'usage':None,'attempts':1,'latency_ms':(time.monotonic()-started)*1000,'error_type':type(exc).__name__,'http_status':code if isinstance(code,int) else None})
                # A rejected/unknown call remains consumed locally. No hidden SDK retry.
                with self.connect() as db:db.execute('UPDATE calls SET status=?,response=? WHERE id=?',(status,json.dumps({'error_type':type(exc).__name__,'http_status':code if isinstance(code,int) else None,'latency_ms':(time.monotonic()-started)*1000}),identifier))
                if isinstance(exc,ProviderUnavailable):raise
                raise ProviderUnavailable(status,'Gemini chưa hoàn tất request; chi tiết an toàn đã lưu, không tự chạy lại claim.') from None

    async def generate(self,prompt,call_id,max_output_tokens=768):
        body={'model':self.config['generation_model'],'endpoint':self.config['endpoint'],'input':prompt,'store':False,
              'generation_config':{'temperature':0,'thinking_level':self.config.get('thinking_level','low'),'max_output_tokens':max(max_output_tokens,self.config.get('minimum_output_tokens',0))}}
        return await asyncio.to_thread(self.call,'generation',body,call_id)

    async def embed(self,texts,task):
        body={'model':'gemini-embedding-001','contents':texts,'task_type':task}
        return await asyncio.to_thread(self.call,'embedding',body,'embedding:'+digest(body))

class GeminiChatBridge(BaseChatModel):
    """LangChain runnable adapter preserves the group's prompt|llm|parser flow."""
    gateway:object
    call_prefix:str='development'
    model_config=ConfigDict(arbitrary_types_allowed=True)

    @property
    def _llm_type(self):return 'gemini-configured-free'

    def _generate(self,messages,stop=None,run_manager=None,**kwargs):
        prompt='\n\n'.join(f'{m.type}: {m.content}' for m in messages)
        body={'model':self.gateway.config['generation_model'],'endpoint':self.gateway.config['endpoint'],'input':prompt,'store':False,'generation_config':{'temperature':0,'thinking_level':self.gateway.config.get('thinking_level','low'),'max_output_tokens':max(512,self.gateway.config.get('minimum_output_tokens',0))}}
        row=self.gateway.call('generation',body,self.call_prefix+':strategy')
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=row['text']))])

    async def _agenerate(self,messages,stop=None,run_manager=None,**kwargs):
        return await asyncio.to_thread(self._generate,messages,stop,run_manager,**kwargs)

