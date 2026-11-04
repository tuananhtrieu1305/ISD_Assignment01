"""Verify actual HTTP download targets without constructing models or serving APIs."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import urlopen
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/notebook_revision/v1'

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def main():
    rows=[]
    for project in ['A01','A02','A03','A04','A05','A06','agent01','agent02']:
        web=ROOT/project/'web'
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(web)))
        thread=Thread(target=server.serve_forever,daemon=True);thread.start()
        address=f'http://127.0.0.1:{server.server_port}/'
        try:
            with urlopen(address) as response:assert response.status==200
            release=json.loads((web/'release-reorg.json').read_text())
            expected={Path(r['path']).relative_to(project+'/web').as_posix():r for r in release['notebook_downloads']}
            for href,record in expected.items():
                with urlopen(address+href) as response:content=response.read();assert response.status==200
                assert hashlib.sha256(content).hexdigest()==record['sha256'],href
                canonical=ROOT/project/'notebooks'/Path(href).name
                assert content==canonical.read_bytes(),href
                json.loads(content)
                rows.append({'project':project,'href':href,'status':200,'sha256':record['sha256'],'matches_current_notebook':True})
            if project.startswith('A'):
                with urlopen(address+'data.js') as response:data=json.loads(response.read().decode().split('=',1)[1].strip().rstrip(';'))
                for task in data['tasks']:
                    for link in task['notebooks']:
                        assert link['href'] in expected,(project,task['id'],link)
                        assert link['sha256']==expected[link['href']]['sha256']
        finally:
            server.shutdown();server.server_close();thread.join()
    (OUT/'web_check.json').write_text(json.dumps({'status':'PASS','downloads':rows,'training_steps':0,'scientific_TEST_forward':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('HTTP downloads and link/SHA parity PASS:',len(rows))

if __name__=='__main__':main()
