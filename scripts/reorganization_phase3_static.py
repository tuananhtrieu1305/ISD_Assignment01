"""Publish six small static result demos from recorded scientific artifacts."""
from pathlib import Path
import csv
import hashlib
import json
import math
import shutil

ROOT=Path(__file__).resolve().parents[1]
P3=ROOT/'docs/reorganization/phase3'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_name(p.name+'.phase3-tmp');temp.write_text(s,encoding='utf-8');temp.replace(p)
def value(v):
    try:
        n=float(v)
        return n if math.isfinite(n) else None
    except (ValueError,TypeError):return v
def csv_rows(p,limit=100):
    with p.open(encoding='utf-8-sig',newline='') as stream:
        rows=[]
        for i,row in enumerate(csv.DictReader(stream)):
            if i>=limit:break
            rows.append({k:value(v) for k,v in row.items()})
        return rows

receipts=[]
def source(p):
    receipts.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
    return p.relative_to(ROOT).as_posix()
def table(p):return {'source':source(p),'rows':csv_rows(p)}
def notebook_links(project,task):
    config=load(ROOT/project/'project.json')
    entries=[r for r in config['notebooks'] if '/training/' not in r['path']]
    preferred=[r for r in entries if task.lower() in r['path'].lower()]
    if not preferred:preferred=entries[:1]
    rows=[]
    for r in preferred:
        src=ROOT/project/r['path'];dst=ROOT/project/'web/notebooks'/src.name
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
        rows.append({'title':src.stem,'href':'notebooks/'+src.name,'sha256':sha(dst)})
    return rows

for project in ['A01','A02','A03','A04','A05','A06']:
    base=ROOT/project
    tasks=[]
    if project in {'A01','A02'}:
        for task,title in [('diabetes','Pima · Tiểu đường'),('house','Giá nhà Việt Nam')]+([('customer_behavior','Hành vi khách hàng')] if project=='A02' else []):
            p=base/f'artifacts/{task}_metadata.json';metadata=load(p)
            fixture={f:0 for f in metadata['features']}
            fixture.update({k:v for k,v in {'Glucose':120,'BMI':28,'Age':35,'Pregnancies':2,'BloodPressure':75,'DiabetesPedigreeFunction':0.5,'Area':65,'Frontage':5,'Access Road':6,'Floors':3,'Bedrooms':3,'Bathrooms':2}.items() if k in fixture})
            for f in metadata.get('categorical_features',[]):fixture[f]='unknown'
            if metadata.get('text_feature'):fixture[metadata['text_feature']]=''
            tasks.append({'id':task,'title':title,'description':'Mô hình ML truyền thống của đúng phiên bản assignment. Mẫu JSON là fixture minh họa có thể chỉnh sửa, không phải một hàng TEST.','tables':[{'source':source(p),'rows':[{'Model':metadata['selected_model'],**metadata.get('test_metrics',{})}]}],'models':[r['name'] for r in metadata['available_models'].values()],'fixture':fixture,'endpoint':'/api/'+task.replace('_','-')+'/compare','notebooks':notebook_links(project,task),'samples':[]})
    elif project in {'A03','A04'}:
        parent=base/('artifacts/pipeline' if project=='A03' else 'artifacts/pipeline04')
        for folder in sorted(p for p in parent.iterdir() if p.is_dir()):
            task=folder.name
            metric_root=folder if project=='A03' else folder/'metrics'
            paths=sorted(metric_root.glob('*comparison.csv'))
            if not paths:continue
            tables=[table(p) for p in paths]
            fixture_path=folder/'demo_input.json'
            taskrow={'id':task,'title':{'diabetes':'CDC · Tiểu đường','house_price':'Giá nhà','customer_behavior':'Hành vi khách hàng','mnist':'MNIST · Chữ số','cifar10':'CIFAR-10 · Ảnh màu'}[task],'description':'Số liệu gốc của từng mô hình và cải tiến; các bảng có thể khác scope validation/TEST. Đọc tên nguồn trước khi so sánh.','tables':tables,'models':[],'samples':[],'notebooks':notebook_links(project,task)}
            if project=='A03' and fixture_path.exists():
                taskrow.update(fixture=load(fixture_path),endpoint='/api/'+{'house_price':'house','customer_behavior':'customer-behavior'}.get(task,task)+'/compare')
                prediction=folder/'demo_prediction.json'
                if prediction.exists():taskrow['saved_output']={'source':source(prediction),'value':load(prediction)}
            tasks.append(taskrow)
    elif project=='A05':
        for task,title in [('eurosat','EuroSAT · Vệ tinh'),('oxford_pets','Oxford-IIIT Pet'),('diabetes','CDC · Ba lớp')]:
            p=base/f'results/metrics/{task}_models.csv'
            if not p.exists() and task=='oxford_pets':p=base/'results/metrics/oxford_pets_models.csv'
            tables=[table(p)]
            predictions=sorted((base/'results/metrics').glob(task+'_*_test_predictions.csv'))
            desc={'eurosat':'Phân loại10 nhóm phủ bề mặt từ ảnh vệ tinh. So sánh bốn kiến trúc Keras: Basic, AlexNet-inspired, VGG-inspired và ResNet-inspired.','oxford_pets':'Phân loại37 giống mèo/chó từ ảnh RGB. Các kiến trúc Keras có độ sâu và số tham số khác nhau; kiến trúc lớn hơn không đảm bảo kết quả tốt hơn.','diabetes':'Phân loại3 nhóm từ21 đặc trưng sức khỏe bằng Conv1D. Thứ tự feature bảng không phải quan hệ không gian tự nhiên; đây là một thí nghiệm kiến trúc. Cả bốn mô hình dùng Keras.'}[task]
            tasks.append({'id':task,'title':title,'description':desc,'tables':tables,'models':[str(r.get('model_family','')) for r in tables[0]['rows']],'samples':[{'source':source(p),'rows':csv_rows(p,8)} for p in predictions[:1]],'notebooks':notebook_links(project,'CDC' if task=='diabetes' else task.replace('_',''))})
    else:
        for task,title in [('customer','Online Retail II · Khách hàng'),('stock','AAPL · Giá đóng cửa')]:
            rows=[];samples=[]
            for framework in ['keras','pytorch']:
                p=base/f'results/metrics/{framework}_{task}_metrics.json';doc=load(p)
                metrics=doc.get('test_metrics_real_scale',doc.get('test_metrics',doc.get('metrics',doc.get('evaluation',{}).get('metrics',{}))))
                def flatten(d,prefix=''):
                    output={}
                    if isinstance(d,dict):
                        for k,v in d.items():
                            if isinstance(v,dict):output.update(flatten(v,prefix+k+'.'))
                            elif isinstance(v,(int,float)) and not isinstance(v,bool):output[prefix+k]=v
                    return output
                if not metrics:metrics={k:v for k,v in doc.items() if k in {'accuracy','precision','recall','f1','roc_auc','mae','rmse','r2'}}
                rows.append({'Model':framework,**flatten(metrics)})
                for key in ['naive_test_metrics_real_scale','naive_baseline','naive_metrics','baseline_metrics']:
                    if key in doc and framework=='keras':rows.append({'Model':'Naive baseline',**flatten(doc[key])})
                source(p)
                pp=base/f'results/predictions/{framework}_{task}_predictions.csv'
                samples.append({'source':source(pp),'rows':csv_rows(pp,40)})
            description='Dự báo Close của phiên tiếp theo từ30 phiên trước, đơn vị USD. So với baseline lấy Close cuối cửa sổ. RMSE/MAE nhỏ hơn tốt hơn; R² không có đơn vị và có thể âm.' if task=='stock' else 'Phân loại nguy cơ rời bỏ từ chuỗi hành vi theo tuần. So sánh RNN Keras/PyTorch; xác suất là đầu ra của mô hình, không phải nhãn thật.'
            tasks.append({'id':task,'title':title,'description':description+' Dưới đây là kết quả TEST đã lưu, không phải một lần đánh giá mới.','tables':[{'source':f'A06/results/metrics/*_{task}_metrics.json','rows':rows}],'models':['Keras RNN','PyTorch RNN']+(['Naive baseline'] if task=='stock' else []),'samples':samples,'notebooks':notebook_links(project,'Stock' if task=='stock' else 'Customer')})
    doc={'project':project,'title':{'A01':'Những mô hình đầu tiên.','A02':'Đọc hành vi từ dữ liệu.','A03':'Từ ML đến mạng sâu.','A04':'So sánh qua kiến trúc.','A05':'Nhìn dữ liệu bằng CNN.','A06':'Học từ những chuỗi dài.'}[project],'tasks':tasks,'mode':'Chọn bài toán, xem kết quả và thử một đầu vào của bạn.' if project in {'A01','A02','A03'} else 'So sánh mô hình từ kết quả notebook đã thực thi.','training_executed':False,'scientific_TEST_forward':False}
    write(base/'web/data.js','window.ASSIGN_DATA = '+json.dumps(doc,ensure_ascii=False,allow_nan=False)+';\n')
    for name in ['index.html','lab.js','lab.css']:
        src=ROOT/'_shared/web'/name
        write(base/'web'/name,src.read_text(encoding='utf-8').replace('__PROJECT__',project))
save_doc={'sources':list({r['path']:r for r in receipts}.values()),'training_steps':0,'scientific_TEST_forward':0,'scope':'CSV/JSON recorded outputs only; fixture inputs explicitly synthetic'}
write(P3/'static_sources.json',json.dumps(save_doc,ensure_ascii=False,indent=2)+'\n')
print('Six static demos exported from',len(save_doc['sources']),'recorded inputs')
