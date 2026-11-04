from __future__ import annotations

import base64
import csv
import html
import json
import struct
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


OUT = Path("A03_CT_anhtt.053.docx")
PIPELINE = Path("pipeline")

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"

EMU_PER_INCH = 914400


@dataclass
class ImageItem:
    key: str
    title: str
    note: str
    data: bytes
    width_px: int
    height_px: int
    rid: str
    docpr_id: int


def esc(text: object) -> str:
    return html.escape("" if text is None else str(text), quote=False)


def rpr(bold=False, italic=False, size=None, color=None, font="Times New Roman") -> str:
    parts = [f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:eastAsia="{font}" w:cs="{font}"/>']
    if bold:
        parts.append("<w:b/><w:bCs/>")
    if italic:
        parts.append("<w:i/><w:iCs/>")
    if color:
        parts.append(f'<w:color w:val="{color}"/>')
    if size:
        parts.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    return "<w:rPr>" + "".join(parts) + "</w:rPr>"


def run(text: object, **kwargs) -> str:
    value = esc(text)
    space = ' xml:space="preserve"' if value.startswith(" ") or value.endswith(" ") else ""
    return f"<w:r>{rpr(**kwargs)}<w:t{space}>{value}</w:t></w:r>"


def p(text="", style=None, align=None, bold=False, italic=False, size=None, color=None, before=0, after=120, line=360) -> str:
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    ppr.append(f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>')
    return "<w:p><w:pPr>" + "".join(ppr) + "</w:pPr>" + run(text, bold=bold, italic=italic, size=size, color=color) + "</w:p>"


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt(value, digits=3):
    try:
        x = float(value)
        if abs(x) >= 100:
            return f"{x:,.3f}".rstrip("0").rstrip(".")
        return f"{x:.{digits}f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value)


def text_table(title: str, rows: list[dict], columns: list[str]) -> str:
    xml = [p(title, bold=True, color="1F4E79", size=23, before=100, after=60, line=300)]
    xml.append(p(" | ".join(columns), bold=True, size=20, color="365F91", after=50, line=280))
    for row in rows:
        xml.append(p(" | ".join(str(row.get(c, "")) for c in columns), size=20, after=40, line=280))
    xml.append(p("", after=80))
    return "".join(xml)


def metric_table(title: str, rows: list[dict], columns: list[str]) -> str:
    formatted = []
    for row in rows:
        formatted.append({"Model": row["Model"], **{c: fmt(row.get(c, "")) for c in columns if c != "Model"}})
    return text_table(title, formatted, columns)


def load_bundle(slug: str):
    root = PIPELINE / slug
    return {
        "metadata": read_json(root / "metadata.json"),
        "schema": read_json(root / "feature_schema.json"),
        "final": read_csv(root / "final_comparison.csv"),
        "dl": read_csv(root / "dl_comparison.csv"),
        "demo_in": read_json(root / "demo_input.json"),
        "demo_pred": read_json(root / "demo_prediction.json"),
    }


CAPTIONS = {
    "diabetes": [
        ("Hình 2.1. Phân bố target Diabetes_binary", "Biểu đồ cho thấy hai lớp gần cân bằng sau cleaning, là cơ sở để dùng F1, Recall và ROC-AUC thay vì chỉ nhìn Accuracy."),
        ("Hình 2.2. Phân bố các biến sức khỏe chính", "Các biến BMI, MentHlth, PhysHlth, GenHlth, Age, Education và Income có thang đo khác nhau, vì vậy scaling sau imputation là cần thiết."),
        ("Hình 2.3. Tỷ lệ xuất hiện của binary indicators", "Một số indicator xuất hiện rất phổ biến như CholCheck, AnyHealthcare, Veggies, trong khi Stroke hoặc HvyAlcoholConsump hiếm hơn."),
        ("Hình 2.4. Quan hệ giữa health indicators và target", "HighBP, HighChol, DiffWalk và GenHlth cho thấy khác biệt rõ giữa hai nhóm target, nhưng đây là quan hệ quan sát chứ không phải kết luận nhân quả."),
        ("Hình 2.5. Outlier và phân bố biến liên tục/biến đếm", "BMI và các biến số ngày sức khỏe xấu có đuôi phải, tuy nhiên các giá trị này vẫn có ý nghĩa trong khảo sát."),
        ("Hình 2.6. Learning curve của DL baseline", "Baseline học được tín hiệu nhưng tốc độ cải thiện và khả năng tổng quát còn hạn chế so với mô hình cải tiến."),
        ("Hình 2.7. Learning curve của Improved DNN", "Validation split và early stopping giúp quá trình huấn luyện ổn định hơn, giảm rủi ro overfitting."),
        ("Hình 2.8. So sánh kết quả sáu mô hình Diabetes", "Improved DNN đạt F1 cao nhất, trong khi Random Forest vẫn có ROC-AUC rất cạnh tranh."),
        ("Hình 2.9. Confusion matrix của mô hình Diabetes cuối", "Ngưỡng 0.30 làm Recall class 1 cao, phù hợp với mục tiêu phát hiện nhóm nguy cơ."),
    ],
    "house_price": [
        ("Hình 3.1. Phân bố target giá nhà và log target", "Target được quan sát ở cả đơn vị tỷ VND và log1p để đánh giá khả năng ổn định hóa quá trình training."),
        ("Hình 3.2. Phân bố numeric features", "Diện tích, mặt tiền, đường vào, số tầng và số phòng có phân bố khác nhau, nhiều trường có missing nên cần imputation."),
        ("Hình 3.3. Phân bố categorical/location features", "City và district có cardinality cao, do đó one-hot encoding phải hỗ trợ handle_unknown khi inference."),
        ("Hình 3.4. Quan hệ diện tích và giá", "Quan hệ giữa area và price không tuyến tính đơn giản, giải thích vì sao Linear Regression hoạt động kém."),
        ("Hình 3.5. Correlation giữa numeric features và price", "Bathrooms, Bedrooms và Floors có tương quan với price cao hơn Area_m2 trong bộ dữ liệu đã xử lý."),
        ("Hình 3.6. Learning curve của DL baseline cho regression", "Baseline dùng output linear và MSE trên target gốc, kết quả tương đối tốt nhưng nhạy với scale giá."),
        ("Hình 3.7. Learning curve của Improved DNN cho regression", "Training trên standardized log target giúp tối ưu ổn định và cải thiện RMSE sau inverse-transform."),
        ("Hình 3.8. So sánh kết quả sáu mô hình House Price", "Improved DNN có RMSE thấp nhất, nhưng khoảng cách với Random Forest không quá lớn."),
        ("Hình 3.9. Predicted vs Actual của mô hình cuối", "Các điểm dự đoán bám theo xu hướng chung nhưng vẫn có sai số ở một số vùng giá."),
        ("Hình 3.10. Residual plot của mô hình cuối", "Residual cho thấy còn sai số hệ thống nhất định, đặc biệt khi thông tin location/categorical chưa đủ chi tiết."),
    ],
    "customer_behavior": [
        ("Hình 4.1. Phân bố target churn", "Class churn chỉ chiếm 16.94%, vì vậy Accuracy không phản ánh đầy đủ năng lực phát hiện khách rời bỏ."),
        ("Hình 4.2. So sánh hành vi theo churn", "Nhóm churn thường có total_spent và completed_orders thấp hơn, đồng thời recency cao hơn."),
        ("Hình 4.3. Interest discovery theo category/brand/channel/device", "Các biến preference giúp biểu diễn sở thích khách hàng, không chỉ phục vụ dự đoán churn."),
        ("Hình 4.4. Correlation/association của feature hành vi", "Các biến liên quan đến mức độ hoạt động có tương quan âm với churn, phù hợp với trực giác nghiệp vụ."),
        ("Hình 4.5. Learning curve của DL baseline trong bài toán churn", "Baseline có Accuracy cao nhưng F1 bằng 0 do không bắt được churner tại threshold mặc định."),
        ("Hình 4.6. Learning curve của Improved DNN có class weighting", "Class-weighted BCE và threshold tuning giúp mô hình quan tâm hơn đến class thiểu số."),
        ("Hình 4.7. So sánh kết quả sáu mô hình Customer Behavior", "Improved DNN đạt F1 cao nhất, dù Random Forest có ROC-AUC tốt hơn một chút."),
        ("Hình 4.8. Confusion matrix của mô hình churn cuối", "Mô hình chấp nhận nhiều false positives để tăng Recall, phù hợp khi mục tiêu là phát hiện khách có rủi ro."),
    ],
}


def extract_images(notebook: Path, slug: str, start_rid: int, start_docpr: int):
    nb = read_json(notebook)
    images = []
    idx = 0
    rid_num = start_rid
    docpr = start_docpr
    for cell in nb["cells"]:
        for output in cell.get("outputs", []) or []:
            data = output.get("data", {})
            if "image/png" not in data:
                continue
            idx += 1
            raw = data["image/png"]
            raw = "".join(raw) if isinstance(raw, list) else raw
            blob = base64.b64decode(raw)
            width, height = struct.unpack(">II", blob[16:24])
            title, note = CAPTIONS[slug][idx - 1]
            images.append(ImageItem(f"{slug}_{idx:02d}.png", title, note, blob, width, height, f"rId{rid_num}", docpr))
            rid_num += 1
            docpr += 1
    return images, rid_num, docpr


rid = 10
docpr = 1
diabetes_images, rid, docpr = extract_images(PIPELINE / "diabetes_pipeline.ipynb", "diabetes", rid, docpr)
house_images, rid, docpr = extract_images(PIPELINE / "house_price_pipeline.ipynb", "house_price", rid, docpr)
customer_images, rid, docpr = extract_images(PIPELINE / "customer_behavior_pipeline.ipynb", "customer_behavior", rid, docpr)
all_images = diabetes_images + house_images + customer_images

diabetes = load_bundle("diabetes")
house = load_bundle("house_price")
customer = load_bundle("customer_behavior")


def image_paragraph(img: ImageItem, max_w_in=6.15, max_h_in=4.65) -> str:
    w_in = img.width_px / 150
    h_in = img.height_px / 150
    scale = min(max_w_in / w_in, max_h_in / h_in, 1.0)
    cx = int(w_in * scale * EMU_PER_INCH)
    cy = int(h_in * scale * EMU_PER_INCH)
    return f'''<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="100"/></w:pPr><w:r><w:drawing>
<wp:inline distT="0" distB="0" distL="0" distR="0">
<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>
<wp:docPr id="{img.docpr_id}" name="{esc(img.title)}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>
<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:pic><pic:nvPicPr><pic:cNvPr id="{img.docpr_id}" name="{esc(img.key)}"/><pic:cNvPicPr/></pic:nvPicPr>
<pic:blipFill><a:blip r:embed="{img.rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>
</pic:pic></a:graphicData></a:graphic>
</wp:inline></w:drawing></w:r></w:p>'''


def figure_page(img: ImageItem, extra: str = "") -> str:
    text = [
        p(img.title, style="Caption", align="center"),
        image_paragraph(img),
        p("Nhận xét. " + img.note),
    ]
    if extra:
        text.append(p(extra))
    text.append(page_break())
    return "".join(text)


doc: list[str] = []

# Front matter
doc += [
    p("BỘ GIÁO DỤC VÀ ĐÀO TẠO", align="center", bold=True, size=28, after=80),
    p("TRƯỜNG ...", align="center", bold=True, size=28, after=80),
    p("KHOA ...", align="center", bold=True, size=28, after=520),
    p("BÁO CÁO ASSIGNMENT 03", align="center", bold=True, size=38, color="1F4E79", after=220),
    p("INTELLIGENT SYSTEM DEVELOPMENT", align="center", bold=True, size=32, after=320),
    p("XÂY DỰNG PIPELINE MACHINE LEARNING VÀ DEEP LEARNING", align="center", bold=True, size=27, after=80),
    p("CHO DIABETES, HOUSE PRICE VÀ CUSTOMER BEHAVIOR", align="center", bold=True, size=27, after=500),
    p("Giảng viên hướng dẫn: ...", align="center", size=26, after=100),
    p("Sinh viên thực hiện: ...", align="center", size=26, after=100),
    p("MSSV: ...", align="center", size=26, after=100),
    p("Lớp: ...", align="center", size=26, after=650),
    p("TP. Hồ Chí Minh, tháng 09 năm 2026", align="center", bold=True, size=26),
    page_break(),
    p("THÔNG TIN BÀI LÀM", style="Heading1", align="center"),
    p("Môn học: Intelligent System Development"),
    p("Assignment: Assignment 03"),
    p("Sinh viên thực hiện: ..."),
    p("MSSV: ..."),
    p("Lớp: ..."),
    p("Giảng viên hướng dẫn: ..."),
    p("Dữ liệu thực nghiệm được lấy từ ba notebook trong thư mục pipeline, gồm diabetes_pipeline.ipynb, house_price_pipeline.ipynb và customer_behavior_pipeline.ipynb. Các notebook đã xuất kèm metadata, feature schema, bảng so sánh mô hình, artifact mô hình và demo inference cho từng ứng dụng."),
    p("Báo cáo trình bày lại toàn bộ quá trình theo hướng học thuật: xác định bài toán, khảo sát dữ liệu, kiểm tra chất lượng, phân tích leakage, thiết kế biểu diễn dữ liệu, xây dựng preprocessing pipeline, huấn luyện mô hình Machine Learning, mở rộng phần Deep Learning và đánh giá mô hình được chọn."),
    page_break(),
    p("LỜI MỞ ĐẦU", style="Heading1", align="center"),
    p("Trong các hệ thống thông minh, hiệu quả của mô hình không chỉ phụ thuộc vào thuật toán mà còn phụ thuộc rất lớn vào cách dữ liệu được tổ chức và kiểm soát trước khi huấn luyện. Nếu dữ liệu bị rò rỉ target, preprocessing được fit sai thời điểm hoặc metric đánh giá không phù hợp với mục tiêu, kết quả thực nghiệm có thể cao nhưng không phản ánh năng lực triển khai thực tế."),
    p("Assignment 03 được thực hiện nhằm xây dựng ba pipeline có khả năng xử lý các dạng dữ liệu khác nhau: dữ liệu khảo sát sức khỏe dạng tabular, dữ liệu giá nhà có nhiều biến location/categorical và dữ liệu hành vi khách hàng đa bảng có yếu tố thời gian. Mỗi pipeline đều được kiểm tra từ bước dữ liệu thô đến bước inference sau khi đóng gói artifact."),
    p("Điểm mở rộng quan trọng của assignment này là phần Deep Learning. Bên cạnh năm mô hình Machine Learning truyền thống, mỗi ứng dụng đều có một mô hình DL baseline theo kiến trúc mẫu và một Improved DNN được cải tiến bằng các kỹ thuật huấn luyện ổn định hơn. Nhờ vậy, báo cáo có thể so sánh vai trò của Deep Learning trong từng bối cảnh thay vì chỉ ghi nhận kết quả cuối."),
    page_break(),
    p("MỤC LỤC", style="Heading1", align="center"),
]
for title, page in [
    ("LỜI MỞ ĐẦU", "3"),
    ("CHƯƠNG 1. TỔNG QUAN VÀ CƠ SỞ PHƯƠNG PHÁP", "7"),
    ("CHƯƠNG 2. ỨNG DỤNG 1: DIABETES CLASSIFICATION", "8"),
    ("CHƯƠNG 3. ỨNG DỤNG 2: VIETNAM HOUSE PRICE REGRESSION", "20"),
    ("CHƯƠNG 4. ỨNG DỤNG 3: CUSTOMER BEHAVIOR / INTEREST DISCOVERY", "33"),
    ("CHƯƠNG 5. TỔNG HỢP KẾT QUẢ VÀ THẢO LUẬN", "44"),
    ("KẾT LUẬN", "45"),
    ("PHỤ LỤC", "46"),
]:
    doc.append(p(f"{title} {' .' * 52} {page}", style="TOCText", after=60))
doc.append(page_break())
doc.append(p("DANH MỤC HÌNH", style="Heading1", align="center"))
for img in all_images:
    doc.append(p(img.title, style="TOCText", after=36, line=280))
doc.append(page_break())
doc.append(p("DANH MỤC BẢNG", style="Heading1", align="center"))
for title in [
    "Bảng 1.1. Tổng quan ba bài toán thực nghiệm",
    "Bảng 2.1. Kết quả sáu mô hình trên Diabetes",
    "Bảng 2.2. So sánh Deep Learning trên Diabetes",
    "Bảng 3.1. Kết quả sáu mô hình trên Vietnam House Price",
    "Bảng 3.2. So sánh Deep Learning trên Vietnam House Price",
    "Bảng 4.1. Kết quả sáu mô hình trên Customer Behavior",
    "Bảng 4.2. So sánh Deep Learning trên Customer Behavior",
    "Bảng 5.1. Mô hình được chọn và artifact đầu ra",
]:
    doc.append(p(title, style="TOCText", after=60))
doc.append(page_break())

# Chapter 1
doc += [
    p("CHƯƠNG 1. TỔNG QUAN VÀ CƠ SỞ PHƯƠNG PHÁP", style="Heading1"),
    p("1.1. Mục tiêu thực nghiệm", style="Heading2"),
    p("Mục tiêu của Assignment 03 là xây dựng một quy trình thực nghiệm có thể lặp lại cho ba bài toán dự đoán. Quy trình này bắt đầu từ dữ liệu thô, đi qua các bước khám phá dữ liệu, làm sạch, kiểm tra rò rỉ, biểu diễn dữ liệu, tiền xử lý, huấn luyện mô hình và cuối cùng là đóng gói pipeline để dự đoán lại trên dữ liệu demo."),
    p("Ba ứng dụng được chọn đại diện cho ba tình huống phổ biến trong phát triển hệ thống thông minh: phân loại nhị phân với dữ liệu tabular đã mã hóa, hồi quy với dữ liệu bất động sản có biến categorical cardinality cao, và phân loại churn từ dữ liệu hành vi đa nguồn. Việc triển khai cả ba bài toán trong cùng một assignment giúp đánh giá khả năng tổng quát của quy trình thay vì chỉ tối ưu một trường hợp riêng lẻ."),
    p("1.2. Tổng quan dữ liệu", style="Heading2"),
    doc and "",
]
doc.append(text_table("Bảng 1.1. Tổng quan ba bài toán thực nghiệm", [
    {"Ứng dụng": "Diabetes", "Bài toán": "Binary classification", "Target": "Diabetes_binary", "Quy mô": "69,057 dòng sau cleaning; 21 feature"},
    {"Ứng dụng": "House Price", "Bài toán": "Regression", "Target": "Price_BillionVND", "Quy mô": "30,223 dòng sau cleaning; 154 feature sau preprocessing"},
    {"Ứng dụng": "Customer Behavior", "Bài toán": "Binary classification", "Target": "is_churned", "Quy mô": "10,000 customers; 51 feature trước preprocessing"},
], ["Ứng dụng", "Bài toán", "Target", "Quy mô"]))
doc += [
    p("1.3. Nguyên tắc kiểm soát leakage", style="Heading2"),
    p("Leakage được kiểm tra theo hai hướng. Thứ nhất là loại bỏ trực tiếp các cột target hoặc cột được dẫn xuất từ target khỏi feature matrix. Thứ hai là kiểm soát thời điểm fit preprocessing và thời điểm lấy dữ liệu hành vi. Tất cả imputer, scaler, encoder và TF-IDF vectorizer chỉ được fit trên training split; riêng Customer Behavior còn đặt prediction-time boundary để loại bỏ sự kiện xảy ra sau cutoff."),
    p("1.4. Đánh giá mô hình", style="Heading2"),
    p("Với classification, báo cáo dùng Accuracy, Precision, Recall, F1 và ROC-AUC. Trong đó F1 được chọn làm metric chính vì hai bài toán classification đều cần cân bằng giữa phát hiện đúng class 1 và hạn chế cảnh báo sai. Với regression, báo cáo dùng MAE, MSE, RMSE, R2 và MAPE, trong đó RMSE được chọn làm metric chính do lỗi lớn trong dự đoán giá nhà cần bị phạt mạnh hơn."),
    p("1.5. Deep Learning trong báo cáo", style="Heading2"),
    p("Mỗi ứng dụng gồm hai mức Deep Learning. DL baseline giữ tinh thần của kiến trúc mẫu: input -> 16 -> 8 -> output, triển khai bằng NumPy và dùng cơ chế tối ưu đơn giản. Improved DNN được cải tiến theo đặc thù bài toán: classification dùng threshold tuning, Customer Behavior thêm class-weighted BCE, còn House Price dùng standardized log1p target và inverse-transform khi đánh giá."),
    page_break(),
]


def add_app_intro(chapter_title: str, paragraphs: list[str]):
    doc.append(p(chapter_title, style="Heading1"))
    for para in paragraphs:
        doc.append(p(para))
    doc.append(page_break())


add_app_intro("CHƯƠNG 2. ỨNG DỤNG 1: DIABETES CLASSIFICATION", [
    "Bài toán Diabetes Classification sử dụng bộ CDC Diabetes Health Indicators / BRFSS 2015 balanced. Target là Diabetes_binary, đầu vào gồm 21 health indicators như HighBP, HighChol, BMI, Smoker, Stroke, GenHlth, Age, Education và Income. Các biến này chủ yếu là indicator hoặc ordinal code, do đó cần diễn giải theo ngữ cảnh survey thay vì xem tất cả như biến liên tục thông thường.",
    "Dữ liệu gốc có 70,692 dòng và 22 cột. Sau khi kiểm tra chất lượng dữ liệu, notebook loại 1,635 exact duplicates trước split, còn 69,057 dòng. Missing value bằng 0, nhưng các giá trị 0 trong MentHlth, PhysHlth hoặc binary indicators được giữ lại vì đây là giá trị có nghĩa, ví dụ 0 ngày sức khỏe không tốt hoặc không có tiền sử bệnh.",
    "Vì mục tiêu ứng dụng là phát hiện nhóm nguy cơ tiểu đường, báo cáo không chọn mô hình chỉ dựa vào Accuracy. F1 được dùng làm metric chính, đồng thời Recall và ROC-AUC được xem xét để đánh giá khả năng phát hiện class 1.",
])
for img in diabetes_images[:5]:
    doc.append(figure_page(img))
doc.append(metric_table("Bảng 2.1. Kết quả sáu mô hình trên Diabetes", diabetes["final"], ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]))
doc += [
    p("Nhận xét. Random Forest là mô hình Machine Learning mạnh nhất theo F1 với F1 = 0.760 và ROC-AUC = 0.821. Logistic Regression và SVM có kết quả gần nhau, chứng tỏ dữ liệu health indicators có tín hiệu tuyến tính nhất định nhưng vẫn được cải thiện bởi mô hình phi tuyến."),
    page_break(),
    p("2.6. Deep Learning cho Diabetes", style="Heading2"),
    p("DL baseline sử dụng kiến trúc input -> 16 -> 8 -> 1 với ReLU/ReLU/Sigmoid, Binary Cross Entropy, full-batch gradient descent, learning rate 0.01 và 1000 epochs. Improved DNN bổ sung validation split, hidden layers lớn hơn, mini-batch training, L2 regularization, early stopping và tuning ngưỡng quyết định."),
]
for img in diabetes_images[5:]:
    doc.append(figure_page(img))
doc.append(metric_table("Bảng 2.2. So sánh Deep Learning trên Diabetes", diabetes["dl"], ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]))
doc += [
    p("Improved DNN đạt F1 = 0.771 và Recall = 0.926 với threshold 0.30. So với DL baseline, F1 tăng từ 0.731 lên 0.771, ROC-AUC tăng từ 0.780 lên 0.819. Kết quả này cho thấy cải tiến quan trọng không chỉ nằm ở số layer mà còn ở cách chọn ngưỡng và kiểm soát quá trình huấn luyện."),
    p("Pipeline cuối được lưu dưới dạng model.npz cùng preprocessor.joblib, metadata.json, feature_schema.json, demo_input.json và demo_prediction.json. Demo inference trả probability_class_1 = 0.300 và predicted_class = 1."),
    page_break(),
]

add_app_intro("CHƯƠNG 3. ỨNG DỤNG 2: VIETNAM HOUSE PRICE REGRESSION", [
    "Bài toán thứ hai dự đoán giá nhà tại Việt Nam theo đơn vị tỷ VND. Dataset là House Price Prediction Dataset Vietnam 2024, target là Price_BillionVND. Đây là bài toán regression, do đó RMSE được chọn làm metric chính vì phản ánh rõ các lỗi dự đoán lớn.",
    "Dữ liệu có 30,229 dòng ban đầu và sau cleaning còn 30,223 dòng. Notebook chuẩn hóa diện tích, giá và parse Address thành city, district, ward/street. Các biến price-derived như Price, Price_BillionVND, Log_Price_BillionVND và price_per_m2_million được loại khỏi X để tránh leakage.",
    "Missing value tập trung ở Balcony direction, House direction, Furniture state, Access Road và Frontage. Thay vì drop row, pipeline dùng median imputation cho numeric và Unknown imputation cho categorical. Sau one-hot encoding, số chiều transformed feature tăng lên 154.",
])
for img in house_images[:5]:
    doc.append(figure_page(img))
doc.append(metric_table("Bảng 3.1. Kết quả sáu mô hình trên Vietnam House Price", house["final"], ["Model", "MAE", "MSE", "RMSE", "R2", "MAPE"]))
doc += [
    p("Nhận xét. Random Forest là mô hình ML tốt nhất với RMSE = 1.440 tỷ VND. Linear Regression cho kết quả rất kém, R2 âm lớn, xác nhận quan hệ giữa giá nhà và các thuộc tính mô tả không phù hợp với giả định tuyến tính đơn giản."),
    page_break(),
    p("3.6. Deep Learning cho House Price", style="Heading2"),
    p("DL baseline được điều chỉnh từ classification sang regression bằng output linear và MSE loss. Improved DNN huấn luyện trên standardized log1p target, sau đó inverse-transform bằng expm1 để tính metric cuối ở đơn vị tỷ VND. Cách này giúp giảm độ nhạy với scale giá và làm quá trình tối ưu ổn định hơn."),
]
for img in house_images[5:]:
    doc.append(figure_page(img))
doc.append(metric_table("Bảng 3.2. So sánh Deep Learning trên Vietnam House Price", house["dl"], ["Model", "MAE", "MSE", "RMSE", "R2", "MAPE"]))
doc += [
    p("Improved DNN đạt RMSE = 1.417 tỷ VND, tốt hơn Teacher DL Baseline RMSE = 1.457 và tốt hơn Random Forest RMSE = 1.440. Tuy nhiên khoảng cách không quá lớn, vì vậy kết luận hợp lý là Deep Learning cải thiện nhẹ nhưng chưa tạo ưu thế tuyệt đối trên dữ liệu tabular bất động sản."),
    p("Artifact cuối gồm model.npz, preprocessor.joblib, metadata.json, feature_schema.json, demo input và demo prediction. Với demo listing tại Hưng Yên, Văn Giang, diện tích 84 m2 và 4 tầng, pipeline dự đoán giá khoảng 8.961 tỷ VND."),
    page_break(),
]

add_app_intro("CHƯƠNG 4. ỨNG DỤNG 3: CUSTOMER BEHAVIOR / INTEREST DISCOVERY", [
    "Ứng dụng thứ ba dự đoán churn ở cấp customer và đồng thời biểu diễn interest thông qua hành vi giao dịch, phiên truy cập, sản phẩm và review. Dữ liệu gốc gồm 10,000 customers, 1,000 products, 120,000 transactions, 80,000 sessions và 25,000 reviews.",
    "Điểm quan trọng nhất của pipeline là prediction-time boundary. Event cuối cùng là 2024-12-30 23:59:05, cutoff được đặt tại 2024-10-01 23:59:05. Các transaction, session và review sau cutoff bị loại khi tạo feature để giảm nguy cơ dùng thông tin tương lai.",
    "Target is_churned mất cân bằng rõ: 83.06% không churn và 16.94% churn. Do đó F1, Recall và Precision quan trọng hơn Accuracy. Feature cuối gồm 43 numeric, 7 categorical và 1 text feature, sau preprocessing tạo matrix 368 chiều.",
])
for img in customer_images[:4]:
    doc.append(figure_page(img))
doc.append(metric_table("Bảng 4.1. Kết quả sáu mô hình trên Customer Behavior", customer["final"], ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]))
doc += [
    p("Nhận xét. Logistic Regression là mô hình ML tốt nhất theo F1 với F1 = 0.356, còn Random Forest có ROC-AUC cao nhất trong nhóm ML với 0.679. KNN và Gradient Boosting có Accuracy cao nhưng Recall rất thấp, cho thấy Accuracy không phù hợp với bài toán churn imbalance."),
    page_break(),
    p("4.6. Deep Learning cho Customer Behavior", style="Heading2"),
    p("DL baseline đạt Accuracy 0.831 nhưng F1 = 0 do gần như không dự đoán được churner ở threshold 0.5. Improved DNN thêm mini-batch, L2 regularization, early stopping, class-weighted BCE và threshold tuning để tăng khả năng phát hiện class thiểu số."),
]
for img in customer_images[4:]:
    doc.append(figure_page(img))
doc.append(metric_table("Bảng 4.2. So sánh Deep Learning trên Customer Behavior", customer["dl"], ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]))
doc += [
    p("Improved DNN đạt F1 = 0.364 và Recall = 0.658, cao hơn toàn bộ các mô hình khác theo metric chọn mô hình. Precision chỉ đạt 0.252, nghĩa là mô hình chấp nhận nhiều false positives để bắt được nhiều khách có nguy cơ churn hơn. Trong thực tế chăm sóc khách hàng, lựa chọn này có thể hợp lý nếu chi phí tiếp cận nhầm thấp hơn chi phí bỏ sót khách sắp rời bỏ."),
    p("Demo inference cho khách hàng Premium, total_transactions = 22, completed_orders = 15, total_spent = 649.36 và days_since_last_transaction = 4 trả probability_class_1 = 0.172, predicted_class = 0 với threshold 0.49."),
    page_break(),
]

doc += [
    p("CHƯƠNG 5. TỔNG HỢP KẾT QUẢ VÀ THẢO LUẬN", style="Heading1"),
    p("5.1. So sánh mô hình được chọn", style="Heading2"),
]
doc.append(text_table("Bảng 5.1. Mô hình được chọn và artifact đầu ra", [
    {"Ứng dụng": "Diabetes", "Metric": "F1", "Model": "Improved DNN", "Kết quả": "F1 = 0.771; Recall = 0.926"},
    {"Ứng dụng": "House Price", "Metric": "RMSE", "Model": "Improved DNN", "Kết quả": "RMSE = 1.417 tỷ VND; R2 = 0.580"},
    {"Ứng dụng": "Customer Behavior", "Metric": "F1", "Model": "Improved DNN", "Kết quả": "F1 = 0.364; Recall = 0.658"},
], ["Ứng dụng", "Metric", "Model", "Kết quả"]))
doc += [
    p("5.2. Thảo luận", style="Heading2"),
    p("Improved DNN được chọn ở cả ba ứng dụng, nhưng mức độ thuyết phục khác nhau. Với Diabetes, mô hình cải tiến tăng F1 rõ rệt nhờ tuning threshold. Với House Price, DNN tốt hơn Random Forest nhưng khoảng cách nhỏ, phản ánh đặc điểm thường gặp của dữ liệu tabular: mô hình cây vẫn rất cạnh tranh. Với Customer Behavior, DNN tăng Recall và F1 so với baseline, nhưng ROC-AUC của Random Forest vẫn cao hơn, do đó cần cân nhắc mục tiêu nghiệp vụ khi triển khai."),
    p("5.3. Hạn chế", style="Heading2"),
    p("Các thực nghiệm chủ yếu dựa trên một train/test split, chưa mở rộng sang cross-validation. House Price còn phụ thuộc vào chất lượng parsing địa chỉ và mức độ đầy đủ của biến location. Customer Behavior đã có cutoff để hạn chế thông tin tương lai, nhưng dataset không cung cấp churn_date chính xác nên outcome window vẫn còn hạn chế."),
    p("5.4. Hướng phát triển", style="Heading2"),
    p("Các hướng cải thiện gồm tuning hyperparameter có hệ thống hơn, đánh giá bằng cross-validation, calibration xác suất cho classification, bổ sung explainability và xây dựng API inference để kiểm tra feature schema ở thời điểm dự đoán. Với Customer Behavior, việc có churn_date sẽ giúp định nghĩa nhãn và cửa sổ dự đoán chặt chẽ hơn."),
    page_break(),
    p("KẾT LUẬN", style="Heading1", align="center"),
    p("Assignment 03 đã hoàn thành ba pipeline Machine Learning và Deep Learning cho ba bài toán có bản chất khác nhau. Báo cáo cho thấy quy trình xử lý dữ liệu có vai trò quyết định trong kết quả mô hình: duplicate cần được loại trước split, missing value cần xử lý theo ngữ nghĩa, target-derived columns phải bị loại khỏi X, và preprocessing chỉ được fit trên training split."),
    p("Phần Deep Learning đã được triển khai như một thành phần thực nghiệm độc lập. DL baseline giúp tạo mốc so sánh với kiến trúc mẫu, còn Improved DNN cho thấy hiệu quả của validation split, regularization, early stopping, threshold tuning, class weighting và target transformation. Tuy nhiên, kết quả cũng cho thấy cần đánh giá theo metric phù hợp thay vì mặc định xem mô hình sâu luôn tốt hơn mô hình truyền thống."),
    p("Sản phẩm cuối của mỗi pipeline gồm model, preprocessor, metadata, feature schema, demo input và demo prediction. Đây là bước cần thiết để chuyển từ notebook thực nghiệm sang một pipeline có khả năng tái sử dụng, kiểm tra lại và triển khai trong hệ thống thông minh."),
    page_break(),
    p("PHỤ LỤC", style="Heading1"),
    p("A.1. Danh sách artifact", style="Heading2"),
    p("Diabetes: pipeline/diabetes/model.npz, preprocessor.joblib, metadata.json, feature_schema.json, final_comparison.csv, dl_comparison.csv, demo_input.json, demo_prediction.json."),
    p("House Price: pipeline/house_price/model.npz, preprocessor.joblib, metadata.json, feature_schema.json, final_comparison.csv, dl_comparison.csv, demo_input.json, demo_prediction.json."),
    p("Customer Behavior: pipeline/customer_behavior/model.npz, preprocessor.joblib, metadata.json, feature_schema.json, final_comparison.csv, dl_comparison.csv, demo_input.json, demo_prediction.json."),
    p("A.2. Demo inference tóm tắt", style="Heading2"),
    p(f"Diabetes: probability_class_1 = {fmt(diabetes['demo_pred'].get('probability_class_1'))}, predicted_class = {diabetes['demo_pred'].get('predicted_class')}, threshold = {fmt(diabetes['demo_pred'].get('threshold'))}."),
    p(f"House Price: predicted_price_billion_vnd = {fmt(house['demo_pred'].get('predicted_price_billion_vnd'))}."),
    p(f"Customer Behavior: probability_class_1 = {fmt(customer['demo_pred'].get('probability_class_1'))}, predicted_class = {customer['demo_pred'].get('predicted_class')}, threshold = {fmt(customer['demo_pred'].get('threshold'))}."),
    p("A.3. Tài liệu tham khảo", style="Heading2"),
    p("1. pipeline/diabetes_pipeline.ipynb"),
    p("2. pipeline/house_price_pipeline.ipynb"),
    p("3. pipeline/customer_behavior_pipeline.ipynb"),
    p("4. Các file metadata, feature schema, bảng so sánh mô hình và demo inference trong thư mục pipeline của từng ứng dụng."),
]


def styles_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{NS_W}">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="180"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman"/><w:b/><w:bCs/><w:color w:val="1F4E79"/><w:sz w:val="30"/><w:szCs w:val="30"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="160" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman"/><w:b/><w:bCs/><w:color w:val="365F91"/><w:sz w:val="25"/><w:szCs w:val="25"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="Caption"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="80" w:after="80" w:line="300" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman"/><w:b/><w:bCs/><w:color w:val="1F4E79"/><w:sz w:val="23"/><w:szCs w:val="23"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TOCText"><w:name w:val="TOC Text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="36" w:line="280" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>
</w:styles>'''


def document_xml() -> str:
    body = "".join(doc)
    sect = '<w:sectPr><w:footerReference w:type="default" r:id="rId2"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1008" w:bottom="1008" w:left="1008" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{NS_W}" xmlns:r="{NS_R}" xmlns:wp="{NS_WP}" xmlns:a="{NS_A}" xmlns:pic="{NS_PIC}"><w:body>{body}{sect}</w:body></w:document>'''


def footer_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="{NS_W}" xmlns:r="{NS_R}">
<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r>{rpr(size=20)}<w:t>Assignment 03 - Intelligent System Development</w:t></w:r></w:p>
</w:ftr>'''


def package():
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''
    image_rels = "\n".join(
        f'<Relationship Id="{img.rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{img.key}"/>'
        for img in all_images
    )
    doc_rels = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
{image_rels}
</Relationships>'''
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    core = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>A03_CT_anhtt.053</dc:title><dc:subject>Assignment 03 Intelligent System Development</dc:subject><dc:creator>...</dc:creator><cp:lastModifiedBy>...</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>'''
    app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Codex</Application></Properties>'''

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document_xml())
        z.writestr("word/_rels/document.xml.rels", doc_rels)
        z.writestr("word/styles.xml", styles_xml())
        z.writestr("word/footer1.xml", footer_xml())
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        for img in all_images:
            z.writestr(f"word/media/{img.key}", img.data)


package()
print(OUT.resolve())
