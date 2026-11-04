"""Publish current notebook downloads and documentation, preserving previous files."""
from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/notebook_revision/v1'

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    manifest=load(OUT/'manifest.json')
    previous=load(OUT/'presentation_backup.json')['files'] if (OUT/'presentation_backup.json').exists() else []
    known={r['path'] for r in previous}
    def preserve(path):
        relative=path.relative_to(ROOT).as_posix()
        if not path.exists() or relative in known:return
        archive=OUT/'presentation_before'/relative
        archive.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,archive)
        previous.append({'path':relative,'archived_path':archive.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size})
        known.add(relative)
        save(OUT/'presentation_backup.json',{'files':previous})
    preserve(ROOT/'AGENTS.md')
    preserve(ROOT/'scripts/verify_reorganization.py')
    downloads=[]
    for project in manifest['projects']:
        name=project['project'];base=ROOT/name;entries=project['notebooks']
        if name in {'A01','A02','A03','A04','A05','A06','agent01','agent02'}:
            web=base/'web';target=web/'notebooks' if name.startswith('A') else web
            expected={Path(e['path']).name for e in entries}
            for old in target.glob('*.ipynb'):
                preserve(old)
                if old.name not in expected:old.unlink()
            for entry in entries:
                destination=target/Path(entry['path']).name
                preserve(destination);shutil.copyfile(base/entry['path'],destination)
                downloads.append({'path':destination.relative_to(ROOT).as_posix(),'sha256':sha(destination),'bytes':destination.stat().st_size})
            data_path=web/'data.js';preserve(data_path)
            if name.startswith('A'):
                data= json.loads(data_path.read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
                for task in data['tasks']:
                    if name=='A04':files=['03_CIFAR10_CNN.ipynb' if task['id']=='cifar10' else '02_MNIST_CNN.ipynb' if task['id']=='mnist' else '01_Tabular_DNN.ipynb']
                    elif name=='A05':files=[{'eurosat':'02_EuroSAT_CNN.ipynb','oxford_pets':'03_Oxford_Pets_CNN.ipynb','diabetes':'04_CDC_Diabetes_CNN.ipynb'}[task['id']],'01_CNN_Co_Ban_Va_So_Sanh.ipynb']
                    elif name=='A06':files=['02_Customer_Behavior.ipynb' if task['id']=='customer' else '03_Stock_Price.ipynb','01_RNN_Co_Ban.ipynb','04_So_Sanh_Framework.ipynb']
                    else:files=[Path(e['href']).name for e in task['notebooks']]
                    task['notebooks']=[{'title':Path(f).stem,'href':'notebooks/'+f,'sha256':sha(target/f)} for f in files]
                data_path.write_text('window.ASSIGN_DATA = '+json.dumps(data,ensure_ascii=False)+';\n',encoding='utf-8')
            release_path=web/'release-reorg.json';preserve(release_path)
            release=load(release_path);release['revision']='NOTEBOOK-inline-v1'
            release['previous_revision']='REORG-Phase3'
            release['notebook_downloads']=[r for r in downloads if r['path'].startswith(name+'/')]
            for asset in release.get('assets',[]):
                path=ROOT/asset['path']
                asset.update(sha256=sha(path),bytes=path.stat().st_size)
            save(release_path,release)
        readme=base/'README.md';preserve(readme)
        text=readme.read_text(encoding='utf-8-sig')
        start=text.index('Thêm `-Notebook') if 'Thêm `-Notebook' in text else text.index('Notebook hiện hành được gộp thành')
        end=text.index('`provenance/runtime/assign/`',start)
        table='| Notebook | Kernel hỗ trợ | Nội dung |\n|---|---|---|\n'
        for e in entries:
            frameworks=', '.join(e.get('supported_frameworks',[e['framework']]))
            role='Code đầy đủ ngay trong cell; mặc định không train/TEST lại' if e.get('embedded_module_count',0) else 'Code notebook trực tiếp; output lịch sử giữ nguyên'
            table+=f"| [{Path(e['path']).name}]({e['path']}) | {frameworks} | {role} |\n"
        replacement='Notebook hiện hành được gộp thành **'+str(len(entries))+' file**; toàn bộ cây `notebooks/` luôn tối đa 4 notebook. Xem [cách đọc và chạy notebook](../docs/notebook_revision/v1/README.md).\n\n'+table+'\n'
        replacement+='Bản trước khi gộp nằm ở `provenance/notebooks_before_inline_v1/notebooks/`, giữ nguyên byte và output. Kết quả chạy mới từ runner nằm tại `artifacts/notebook_runs/`, không sinh thêm notebook trong `notebooks/`.\n\n'
        if name not in {'A01','A02','A03','agent01'}:
            replacement+='`%%inline_module` chạy **source có ngay trong cell** trong namespace riêng, không đọc implementation từ file `.py`. Chạy từ trên xuống; sau khi sửa một hàm/lớp, chạy lại cell đó và các cell sử dụng nó. Code dữ liệu, loss/optimizer, model và train/evaluate đều có thể đọc trong notebook. Giữ `RUN_EXPERIMENTS=False` khi xem lại bài đã khóa.\n\n'
        text=text[:start]+replacement+text[end:]
        readme.write_text(text,encoding='utf-8')
        notebook_readme=base/'notebooks/README.md'
        notebook_readme.write_text('# Notebook hiện hành\n\n'+replacement+'Chọn kernel theo [README bài](../README.md). Mở [hướng dẫn chung](../../docs/notebook_revision/v1/README.md).\n',encoding='utf-8')
        web_readme=base/'web/README.md';preserve(web_readme)
        text=web_readme.read_text(encoding='utf-8-sig')
        marker='\n<!-- notebook-inline-v1 -->'
        if marker in text:text=text.split(marker)[0]
        text+=marker+'\n\nNotebook đã gộp, đầy đủ source trong cell: [danh sách hiện hành](../README.md). Bản tải notebook trên web (nếu có) trùng SHA-256 với `../notebooks/`; mở trong repository để dùng dataset và kernel hiện có.\n'
        web_readme.write_text(text,encoding='utf-8')
    root_readme=ROOT/'README.md';preserve(root_readme)
    text=root_readme.read_text(encoding='utf-8-sig')
    for project in manifest['projects']:
        pattern=r'(\| \['+re.escape(project['project'])+r'\].*? \| .*? \| )\d+( \|)'
        text=re.sub(pattern,lambda m:m[1]+str(len(project['notebooks']))+m[2],text)
    text=text.replace('notebooks/diabetes_pipeline04.ipynb','notebooks/01_Tabular_DNN.ipynb').replace('<bai>/notebooks/executed/','<bai>/artifacts/notebook_runs/')
    marker='\n<!-- notebook-inline-v1 -->'
    if marker in text:text=text.split(marker)[0]
    text+=marker+'\n\n**Notebook hiện hành: 29 file, mỗi bài tối đa 4.** Code thuật toán nằm trực tiếp trong cell; các tiểu luận không còn chỉ là notebook xem kết quả/import implementation. Đọc [hướng dẫn notebook](docs/notebook_revision/v1/README.md) và [biên bản revision](docs/notebook_revision/v1/report.md). REORG ba phase vẫn giữ biên bản lịch sử; revision notebook có checkpoint riêng.\n'
    root_readme.write_text(text,encoding='utf-8')
    save(OUT/'web_downloads.json',{'files':downloads,'training_steps':0,'scientific_TEST_forward':0})
    print('Published',len(downloads),'notebook downloads; updated 11 project READMEs')

if __name__=='__main__':main()
