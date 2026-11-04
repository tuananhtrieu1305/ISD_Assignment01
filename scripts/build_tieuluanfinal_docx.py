"""Surgical OOXML replacement of Chapter6; preserve every other package part."""
from pathlib import Path
from copy import deepcopy
from io import BytesIO
import hashlib
import json
import re
import zipfile
from lxml import etree as E
from docx import Document
from docx.shared import Inches

ROOT=Path(__file__).resolve().parents[1]
FINAL=ROOT/'tieuluanfinal'
SOURCE=Path('/mnt/c/Users/anhca/Downloads/tieuluan03_CT_08_anhtt.docx')
OUT=FINAL/'report/final/Tieu_Luan_AI_Final.docx'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS={'w':W,'r':R}
XML='http://www.w3.org/XML/1998/namespace'


def digest(data):return hashlib.sha256(data).hexdigest()
def text(node):return ''.join(child.text or '' for child in node.iter('{'+W+'}t'))
def q(name):return '{'+W+'}'+name


def build():
    analysis=json.loads((FINAL/'artifacts/final_ch06/notebook_analysis.json').read_text())
    job=json.loads((FINAL/'artifacts/final_ch06/live_job_r11.json').read_text())
    rag=job['results']['agentic_rag'];direct=job['results']['llm_direct']
    with zipfile.ZipFile(SOURCE) as source:
        entries={x.filename:source.read(x.filename) for x in source.infolist()}
        infos=source.infolist()
    root=E.fromstring(entries['word/document.xml']);body=root.find('w:body',NS)
    original=list(body)
    start=next(i for i,p in enumerate(original) if text(p).startswith('CHƯƠNG 6.') and i>1000)
    end=next(i for i,p in enumerate(original[start+1:],start+1) if text(p)=='KẾT LUẬN')
    if original[end-2].tag==q('bookmarkStart') and original[end-1].tag==q('bookmarkEnd'):end-=2
    # Chapter boundary bookmark pairs precede the title, as in the supplied source.
    preserved_title=deepcopy(original[start])
    body_p=deepcopy(original[start+4]);head2=deepcopy(original[start+3])
    def p(value,heading=None):
        node=deepcopy(preserved_title if heading==1 else head2 if heading==2 else body_p)
        for child in list(node):
            if child.tag!=q('pPr'):node.remove(child)
        props=node.find('w:pPr',NS)
        if props is None:props=E.SubElement(node,q('pPr'))
        # New material uses the real template's styles and geometry, in black.
        for c in props.xpath('.//w:color',namespaces=NS):c.set(q('val'),'000000')
        run=E.SubElement(node,q('r'));rp=E.SubElement(run,q('rPr'))
        E.SubElement(rp,q('color')).set(q('val'),'000000')
        t=E.SubElement(run,q('t'));t.set('{'+XML+'}space','preserve');t.text=value
        return node
    def table(headers,rows,widths=None):
        widths=widths or [int(9638/len(headers))]*len(headers)
        node=E.Element(q('tbl'));props=E.SubElement(node,q('tblPr'))
        E.SubElement(props,q('tblW'),{q('w'):'9638',q('type'):'dxa'})
        borders=E.SubElement(props,q('tblBorders'))
        for name in ['top','left','bottom','right','insideH','insideV']:
            E.SubElement(borders,q(name),{q('val'):'single',q('sz'):'4',q('color'):'D9D9D9'})
        margins=E.SubElement(props,q('tblCellMar'))
        for side in ['top','bottom','left','right']:E.SubElement(margins,q(side),{q('w'):'95',q('type'):'dxa'})
        grid=E.SubElement(node,q('tblGrid'))
        for width in widths:E.SubElement(grid,q('gridCol'),{q('w'):str(width)})
        for index,row in enumerate([headers,*rows]):
            tr=E.SubElement(node,q('tr'));trp=E.SubElement(tr,q('trPr'));E.SubElement(trp,q('cantSplit'))
            if index==0:E.SubElement(trp,q('tblHeader'))
            for value,width in zip(row,widths):
                cell=E.SubElement(tr,q('tc'));cp=E.SubElement(cell,q('tcPr'))
                E.SubElement(cp,q('tcW'),{q('w'):str(width),q('type'):'dxa'})
                E.SubElement(cp,q('vAlign'),{q('val'):'center'})
                if index==0:E.SubElement(cp,q('shd'),{q('fill'):'E7E6E6'})
                para=p(str(value));pp=para.find('w:pPr',NS)
                for child in list(pp):pp.remove(child)
                E.SubElement(pp,q('spacing'),{q('before'):'40',q('after'):'40',q('line'):'240',q('lineRule'):'auto'})
                E.SubElement(pp,q('ind'),{q('firstLine'):'0'})
                rp=para.find('w:r/w:rPr',NS)
                E.SubElement(rp,q('sz'),{q('val'):'23'})
                if index==0:E.SubElement(rp,q('b'))
                cell.append(para)
        return node
    new=[];headings=[];tables=[];figures=[]
    def para(value):new.append(p(value))
    def heading(value):
        node=p(value,2);new.append(node);headings.append(node)
    def tab(caption,headers,rows,widths=None):
        node=p(caption);new.append(node);tables.append(node);new.append(table(headers,rows,widths));para('')
    new.append(p('CHƯƠNG 6. HỆ ĐA TÁC TỬ (MULTI-AGENT SYSTEMS)',1))
    heading('6.1. Agent và phối hợp nhiều agent')
    para('Một agent là thành phần nhận đầu vào, thực hiện một nhiệm vụ trong phạm vi được phép và chuyển kết quả cho thành phần khác. Trong hệ này, các agent là các vai trò phần mềm; không phải mỗi agent là một mô hình được huấn luyện riêng. Việc tách vai trò giúp quan sát được câu hỏi đã được hiểu thế nào, bằng chứng đến từ đâu và câu trả lời có được kiểm tra trước khi phát hành hay không.')
    para('Bài toán minh họa là hỏi đáp kiến thức tiểu đường bằng tiếng Việt. Hệ mới dùng bốn vai trò Coordinator, Knowledge Agent, Reporter và Verifier. Risk Agent và hồ sơ CDC không tham gia luồng này: người dùng chỉ nhập một câu hỏi. LLM trực tiếp được đặt cạnh pipeline để đối chiếu trên cùng câu hỏi và cùng model Gemini 3 Flash, mã trả về gemini-3-flash-preview [NB6–KQ2, KQ4].')
    heading('6.2. Dữ liệu và kho tri thức')
    para('Nguồn văn bản là MedQuAD, tập hỏi đáp y khoa tổng hợp từ các website thuộc NIH. Bản dùng trong chương này là snapshot riêng, phục hồi ngữ cảnh và URL nguồn; không thay đổi dữ liệu của Chương 5. Nội dung nguồn chủ yếu bằng tiếng Anh, còn câu hỏi và câu trả lời demo bằng tiếng Việt. Đây là tài liệu lịch sử, không được mặc định là hướng dẫn y khoa mới nhất.')
    tab('Bảng 6.1. Dữ liệu phục vụ hệ hỏi đáp', ['Thành phần','Kích cỡ thực tế','Mục đích và giới hạn'],[
        ['Corpus MedQuAD','45 tài liệu; 210 ngữ cảnh hỏi đáp; 316 đoạn; 409 tham chiếu','Kho truy hồi; một đoạn có thể có nhiều tham chiếu nguồn.'],
        ['Mini-KG dẫn xuất','35 thực thể; 35 assertion có kiểm nguồn; 20 đoạn seed','Định hướng tìm nguồn theo thực thể/quan hệ, không phải dataset y khoa độc lập.'],
        ['Bộ câu hỏi mới','20 development; 40 held-out đã chuẩn bị','Chương phân tích một lượt demo đã lưu; chưa có benchmark 40 cặp của bản hiện hành.']
    ],[2400,3000,4238])
    para('Phân bố 45 tài liệu: NIDDK 27, MedlinePlus 14, SeniorHealth 2, NHLBI 1 và NINDS 1. Mỗi đoạn dài 71–2.579 ký tự, trung bình khoảng 1.103 ký tự. Chia theo câu, mục tiêu mềm 1.600 ký tự, chồng lấn một câu và gộp đoạn trùng giúp giữ ngữ cảnh nhưng có thể tạo nguồn gần giống nhau. Những con số này được đếm từ dữ liệu, không phải metric độ chính xác [NB6–KQ1].')
    para('Ví dụ assertion kg2-a014 nối diabetes → MAY_DAMAGE → kidney_damage, kèm điều kiện “over time; hyperglycemia” và đoạn m2c-62f2377845eb99ad274e. Câu nguồn nêu đường huyết cao do tiểu đường có thể làm tổn thương thận theo thời gian. Chiều này không đủ chứng minh bệnh thận gây tiểu đường. Mỗi cạnh giữ câu trích, URL, chunk ID và trạng thái kiểm nguồn; kiểm bởi trợ lý chưa tương đương thẩm định chuyên gia [NB6–KQ1].')
    heading('6.3. Kiến trúc bốn agent')
    tab('Bảng 6.2. Đầu vào và đầu ra của bốn agent', ['Vai trò','Xử lý','Chuyển cho bước sau'],[
        ['Coordinator','Gemini xác định phạm vi, giữ chiều quan hệ và tạo tối đa 3 truy vấn.','Câu hỏi gốc, truy vấn, thực thể và điều kiện.'],
        ['Knowledge Agent','BM25 + embedding + tra KG; gộp RRF; rerank local.','Các đoạn được chọn, điểm/hạng và nguồn.'],
        ['Reporter','Gemini viết bản nháp từ evidence, tạo claims và citation.','Bản nháp tiếng Việt và liên kết claim–chunk.'],
        ['Verifier','Một call Gemini kiểm ý nghĩa/điều kiện, có thể sửa ngay; Python kiểm cấu trúc và nguồn.','Cho phát hành hoặc chặn, kèm nhận xét kiểm tra.']
    ],[2200,4050,3388])
    para('Luồng duy nhất: Câu hỏi → Coordinator → Knowledge Agent → Reporter → Verifier → Câu trả lời. Retrieval và rerank là hai công đoạn bên trong Knowledge Agent; phát hành là thao tác sau kiểm chứng. Vì vậy sáu stage được ghi trong journal không phải sáu agent hay một pipeline khác.')
    para('Một cặp so sánh đầy đủ dùng bốn generation request: một cho LLM trực tiếp, một Coordinator, một Reporter và một Verifier. Embedding truy vấn có hạn mức riêng; reranker chạy local, không gọi Gemini để xếp hạng lại. Hai nhánh cùng dùng một tiêu chuẩn kiểm nguồn, không có luật riêng theo câu hỏi để ép nhánh trực tiếp trả lời sai.')
    heading('6.4. Hợp hàm và giải thích từng hàm')
    para('Có thể đọc hệ như hợp các hàm theo chiều dữ liệu: lập kế hoạch(câu hỏi) → truy hồi(kế hoạch) → xếp hạng(câu hỏi, ứng viên) → soạn nháp(câu hỏi, evidence) → kiểm tra(bản nháp, evidence) → phát hành. Đầu ra của hàm trước là đầu vào của hàm sau; không cần một công thức phức tạp để hiểu cách hệ phối hợp.')
    para('PreRetriever.process giữ câu hỏi gốc và bổ sung truy vấn. HybridSearcher._fuse gộp thứ hạng BM25, semantic và KG bằng RRF. Retriever.retrieve gom nhiều truy vấn, loại trùng theo chunk ID. LocalEvidenceReranker.rerank chấm lại ứng viên và giữ top 6; trọng số lượt minh họa là RRF 0,55, độ phủ từ 0,35 và nguồn KG 0,10. Các trọng số là thiết kế của demo, không phải mức tin cậy y khoa.')
    para('PromptBuilder.build_context đánh số nguồn để Reporter trích dẫn. GeminiGenerator.generate tạo bản nháp có claims. SemanticVerifier.verify kiểm độ hỗ trợ của từng claim và điều kiện, đồng thời cho phép sửa trong cùng một call; CodeVerifier.verify chặn citation không giải được, thiếu provenance hoặc schema sai. AgenticRuntime.rag điều phối các hàm trên và ghi input/output của từng stage. Code đầy đủ nằm trong notebook 04_Multi_Agent.ipynb; backend chỉ là bản export phục vụ web.')
    heading('6.5. Kết quả minh họa từ notebook')
    para('Lượt chạy ngày 03/11/2026, journal 56d62ac4-77f4-4cf8-a2e7-f01584c2e240, revision four-agent-r11, nhận câu hỏi: “Đi bộ có giúp tôi giảm hơn 50% nguy cơ tiểu đường không?”. Notebook đọc lại nguyên trạng hai câu trả lời và trace đã lưu; việc lập báo cáo không phát sinh request Gemini, huấn luyện hay forward TEST mới [NB6–KQ2].')
    para('Coordinator tạo ba truy vấn: câu tiếng Việt gốc; “walking reduce diabetes risk by more than 50 percent”; “effect of walking on diabetes prevention percentage”. Knowledge Agent gộp còn 20 ứng viên, reranker giữ 6 đoạn. Trong chính lượt này, KG trả 0 ứng viên phù hợp; không thể quy kết kết quả trả lời cho đóng góp của KG [NB6–KQ2, KQ3].')
    rows=[]
    for index,row in enumerate(analysis['rerank_top6'],1):
        short=row['chunk_id'].replace('m2c-','')[:8]
        rows.append([str(index),short,str(row['input_rank']),str(row['model_rank']),f"{row['rerank_score']:.5f}"])
    tab('Bảng 6.3. Sáu đoạn đứng đầu sau rerank', ['Nguồn','ID rút gọn','Hạng vào','Hạng ra','Điểm'], rows,[1300,2600,1800,1800,2138])
    para('Cả sáu đoạn giữ nguyên thứ tự trong lượt này. Rerank thực hiện lọc top 6 nhưng chưa cho thấy cải thiện thứ hạng. Nguồn 1 là “Am I at Risk for Type 2 Diabetes?”, có 3.234 người nguy cơ cao và can thiệp đi bộ kết hợp chế độ ăn. Nguồn 5 nói người trên 60 tuổi giảm nguy cơ 71%; nguồn 6 mô tả nhóm thay đổi lối sống có nguy cơ chưa bằng một nửa nhóm không thay đổi. Điểm xếp hạng không phải xác suất câu trả lời đúng [NB6–KQ3].')
    para('Trích LLM trực tiếp: “Không thể khẳng định đi bộ giúp bạn giảm hơn 50% nguy cơ tiểu đường.” Sau đó nhánh này cũng nhắc DPP, kết hợp vận động với ăn uống/giảm cân và phân biệt kết quả nhóm với cá nhân. Nhánh trực tiếp có kiến thức liên quan; việc không có citation nội bộ không tự chứng minh câu trả lời sai [NB6–KQ4].')
    para('Trích pipeline: “Tuy nhiên, kết quả này đạt được từ sự kết hợp giữa vận động và giảm cân, không chỉ riêng việc đi bộ đơn lẻ.” Phần trước dẫn nghiên cứu DPP, 3.234 người nguy cơ cao, đi bộ khoảng 30 phút/ngày × 5 ngày/tuần và giảm 5–7% trọng lượng, kèm [Nguồn 1], [Nguồn 5], [Nguồn 6]. Đây là lợi thế về khả năng đối chiếu bằng chứng, không phải một ước lượng nguy cơ cá nhân [NB6–KQ4].')
    metrics={r['variant']:r for r in analysis['metrics']}
    tab('Bảng 6.4. Chi phí xử lý quan sát trên một lượt', ['Chỉ số','LLM trực tiếp','Đa agent + RAG'],[
        ['Thời gian nhánh',f"{metrics['llm_direct']['seconds']:.3f} giây",f"{metrics['agentic_rag']['seconds']:.3f} giây"],
        ['Generation request live','1','3'],
        ['Tổng generation token','1.015','9.849'],
        ['Query embedding','Không dùng','1 live + 2 cache local'],
        ['Đoạn được chọn / được dẫn','0 / 0','6 / 5']
    ],[3900,2700,3038])
    # The chart itself was emitted by KQ6 of the executed notebook.
    chart=FINAL/'artifacts/final_ch06/stage_latency.png'
    doc=Document();doc.add_paragraph().add_run().add_picture(str(chart),width=Inches(6.4))
    drawing=deepcopy(doc.paragraphs[0]._p)
    for blip in drawing.xpath('.//*[local-name()="blip"]'):blip.set('{'+R+'}embed','rIdFinalLatency')
    new.append(drawing)
    caption=p('Hình 6.1. Thời gian các stage của một lượt RAG. Nguồn: output NB6–KQ6, journal r11 đã lưu.')
    new.append(caption);figures.append(caption)
    para('Trục ngang là giây, mỗi thanh là một stage. Reporter khoảng 4,219 giây và Verifier khoảng 3,195 giây, lớn hơn truy hồi 0,826 giây và rerank local 0,031 giây. Toàn nhánh RAG khoảng 11,175 giây, gồm điều phối và I/O ngoài thời gian stage. Hai nhánh chạy tuần tự; không dùng biểu đồ này làm latency trung bình hay cam kết thời gian đáp ứng [NB6–KQ5, KQ6].')
    heading('6.6. Phân tích và giới hạn')
    para('Verifier duyệt cả ba claim và không ghi nhận lỗi integrity; trong lượt này không sửa bản nháp. Tuy vậy câu mở đầu của pipeline “Có ... giúp bạn” vẫn dễ khiến người đọc hiểu thành bảo đảm cho cá nhân. Điều kiện can thiệp kết hợp đã có ở cuối nhưng nên được đặt ngay đầu. Đây là ví dụ cho thấy cùng LLM tự kiểm chưa bảo đảm loại hết cách diễn đạt quá mạnh [NB6–KQ4].')
    para('Kết quả quan sát được là pipeline cung cấp đường kiểm chứng: claim → chunk → snapshot/URL, đổi lại dùng nhiều token, request và thời gian hơn. Cả hai nhánh đều có nội dung hữu ích. Một câu development không đủ chứng minh bên nào chính xác hơn; chưa có tỷ lệ thắng hay accuracy mới cho bộ 40 câu. Các kết quả A0/A1/A2 và TEST cũ thuộc baseline đã lưu, không chuyển thành metric của hệ Gemini này.')
    para('Mini-KG nhỏ có thể bỏ sót quan hệ; không tìm thấy cạnh không có nghĩa quan hệ không tồn tại. Nguồn có thể trùng ý hoặc lỗi thời. Citation hợp lệ chỉ xác nhận truy được nguồn, không tự xác nhận mọi diễn giải là đúng. Demo không thu bệnh án, không chẩn đoán, kê đơn hay thay tư vấn chuyên môn.')
    heading('6.7. Notebook và truy vết đầu ra')
    para('Notebook 04_Multi_Agent.ipynb chứa toàn bộ code và sáu mục output: KQ1 đếm dữ liệu/tra KG; KQ2 đọc journal và các stage; KQ3 bảng xếp hạng và nguồn; KQ4 hai câu trả lời cùng Verifier; KQ5 tổng hợp thời gian/token/request; KQ6 biểu đồ thời gian. Ký hiệu [NB6–KQn] trong chương chỉ trực tiếp đến các mục này. Mặc định RUN_API, RUN_EVALUATION, RUN_TRAINING và RUN_TEST đều False; Run All không gửi câu hỏi mới lên Gemini.')
    para('Nguồn corpus: https://github.com/abachaa/MedQuAD. Snapshot minh họa DPP/NIDDK: https://github.com/abachaa/MedQuAD/blob/577bd37b96c02d1833b2c9eed2de9f96964e96cb/5_NIDDK_QA/0000022.xml. Snapshot SeniorHealth: cùng commit, 7_SeniorHealth_QA/0000015.xml. ID đầy đủ, URL gốc và câu trích nằm trong output KQ3; journal gốc tại artifacts/final_ch06/live_job_r11.json. MedQuAD giữ attribution/điều khoản nguồn trong dataset card.')
    heading('6.8. Triển khai ngắn')
    para('Tab Multi-Agent của demo tổng hợp sử dụng implementation bốn agent đã đóng gói trong tieuluanfinal, tách với các chương khoa học cũ. Người dùng nhập câu hỏi, bấm Trả lời, xem hai đáp án; tab Luồng xử lý hiển thị input/output thật; tab Đồ thị tri thức cho xem cạnh, chiều và nguồn. KG chạy bằng SVG local, không cần Neo4j.')
    para('Từ Git Bash tại thư mục assign, chạy: bash tieuluanfinal/scripts/run_web.sh, rồi mở http://127.0.0.1:8040/agents. Key chỉ được nạp ở backend; dùng chung môi trường và sổ quota local đang có, không chép key vào notebook hoặc frontend. Hệ kiểm hạn mức trước khi tạo lượt, giữ journal khi lỗi/quota và không gọi model qua health check. Bản bàn giao đã kiểm local; chưa commit, push hoặc deploy cloud.')
    # Preserve every original bookmark to avoid breaking external/internal anchors.
    old_nodes=original[start:end]
    bookmarks=[deepcopy(x) for n in old_nodes for x in n.iter() if x.tag in {q('bookmarkStart'),q('bookmarkEnd')}]
    old_headings=[n for n in old_nodes if n.tag==q('p') and re.match(r'^6\.\d\. ',text(n))]
    old_heading_anchors={}
    for n in original[:start]:
        links=n.findall('w:hyperlink',NS)
        if links and re.match(r'^6\.\d\. ',text(n)):
            old_heading_anchors[text(n)[:3]]=links[0].get('{'+W+'}anchor')
    by_name={x.get(q('name')):x for x in bookmarks if x.tag==q('bookmarkStart')}
    placed=set()
    def anchor(node,name):
        if name in by_name:
            begin=by_name[name];bid=begin.get(q('id'))
            finish=next(x for x in bookmarks if x.tag==q('bookmarkEnd') and x.get(q('id'))==bid)
            position=1 if node.find('w:pPr',NS) is not None else 0
            node.insert(position,deepcopy(begin));node.append(deepcopy(finish));placed.add(bid)
    for node in headings:anchor(node,old_heading_anchors.get(text(node)[:3]))
    # Associate only Chapter6 navigation entries with the corresponding new slots.
    nav_changes=[]
    nav_head={text(n)[:3]:text(n) for n in headings}
    table_map={f'Bảng 6.{i+1}':text(n) for i,n in enumerate(tables)}
    for node in original[:start]:
        value=text(node);replacement=None;target=None
        if re.match(r'^6\.\d\. ',value):replacement=nav_head.get(value[:3])
        if value.startswith('Bảng 6.'):
            key=re.match(r'Bảng 6\.\d+',value).group();replacement=table_map.get(key)
            if replacement:target=tables[int(key.rsplit('.',1)[-1])-1]
            else:body.remove(node);nav_changes.append({'removed':value});continue
        if value.startswith('Hình 6.'):
            if value.startswith('Hình 6.1.'):
                replacement=text(figures[0]);target=figures[0]
            else:body.remove(node);nav_changes.append({'removed':value});continue
        if replacement:
            links=node.findall('w:hyperlink',NS)
            if target is not None and links:anchor(target,links[0].get(q('anchor')))
            ts=node.findall('.//w:t',NS)
            if ts:
                # Keep run/paragraph/link formatting and tabs; only replace label text.
                for t in ts:t.text=''
                ts[0].text=replacement
            nav_changes.append({'before':value,'after':replacement})
    # Remaining historical anchors resolve to the new chapter title, not missing nodes.
    for begin in bookmarks:
        if begin.tag!=q('bookmarkStart') or begin.get(q('id')) in placed:continue
        anchor(new[0],begin.get(q('name')))
    for node in old_nodes:body.remove(node)
    insert_at=list(body).index(original[end])
    for i,node in enumerate(new):body.insert(insert_at+i,node)
    document_bytes=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
    # Relationships and media are the only other modified/added package elements.
    rels=E.fromstring(entries['word/_rels/document.xml.rels'])
    rel=E.SubElement(rels,'{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
    rel.set('Id','rIdFinalLatency');rel.set('Type',R+'/image');rel.set('Target','media/final_ch06_latency.png')
    replacements={'word/document.xml':document_bytes,
        'word/_rels/document.xml.rels':E.tostring(rels,xml_declaration=True,encoding='UTF-8',standalone=True)}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as result:
        for info in infos:result.writestr(info,replacements.get(info.filename,entries[info.filename]))
        result.writestr('word/media/final_ch06_latency.png',chart.read_bytes())
    # Exact scope check on original XML elements outside Chapter6 and its indexes.
    allowed_nav={id(n) for n in original[:start] if re.match(r'^(6\.\d\. |Bảng 6\.|Hình 6\.)',text(n))}
    # Compare serialized untouched elements against freshly parsed source (not mutated refs).
    before=E.fromstring(entries['word/document.xml']).find('w:body',NS)
    untouched=0
    for i,node in enumerate(before):
        if start<=i<end:continue
        value=text(node)
        if i<start and re.match(r'^(6\.\d\. |Bảng 6\.|Hình 6\.)',value):continue
        assert E.tostring(node)==E.tostring(original[i]),f'Unexpected non-Ch6 change at {i}'
        untouched+=1
    with zipfile.ZipFile(OUT) as result:
        for name,data in entries.items():
            if name not in replacements:assert result.read(name)==data,name
    report={'source':str(SOURCE),'source_sha256':digest(SOURCE.read_bytes()),'output':str(OUT),'output_sha256':digest(OUT.read_bytes()),
        'old_chapter6_element_range':[start,end],'new_chapter6_elements':len(new),'preserved_outside_body_elements':untouched,
        'unchanged_package_parts':len(entries)-len(replacements),'modified_parts':list(replacements),'added_media':['word/media/final_ch06_latency.png'],
        'chapter6_navigation_changes':nav_changes,'journal':job['id'],'new_API_calls':0,'training_steps':0,'scientific_TEST_forward':0}
    target=FINAL/'docs/final_revision/document_scope.json';target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    # Human-readable source is extracted from exactly the authored nodes.
    manuscript='\n\n'.join(text(n) for n in new if text(n))
    (FINAL/'report/final/ch06_multi_agent.md').write_text(manuscript+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='chapter6_navigation_changes'}))


if __name__=='__main__':build()
