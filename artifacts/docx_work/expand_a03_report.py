import copy
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
}

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

W = "{" + NS["w"] + "}"
R = "{" + NS["r"] + "}"
REL = "{" + NS["rel"] + "}"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


BODY_FONT = "Times New Roman"
CAPTION_BLUE = "1F4E79"

ORIGINAL_TABLE_CAPTIONS = [
    "Bảng 1.1. Tổng quan ba bài toán thực nghiệm",
    "Bảng 2.1. Kết quả sáu mô hình trên Diabetes",
    "Bảng 2.2. So sánh DL baseline và Improved DNN trên Diabetes",
    "Bảng 3.1. Kết quả sáu mô hình trên House Price",
    "Bảng 3.2. So sánh DL baseline và Improved DNN trên House Price",
    "Bảng 4.1. Kết quả sáu mô hình trên Customer Behavior",
    "Bảng 4.2. So sánh DL baseline và Improved DNN trên Customer Behavior",
    "Bảng 5.1. Tổng hợp mô hình được chọn cuối cùng",
]


def qn(namespace, name):
    return "{" + NS[namespace] + "}" + name


def local_name(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def text_of(node):
    return "".join(t.text or "" for t in node.iter(W + "t"))


def collapse_space(text):
    return re.sub(r"\s+", " ", text or "").strip()


def copy_without_change_nodes(node):
    node = copy.deepcopy(node)
    strip_change_nodes_inplace(node)
    return node


def strip_change_nodes_inplace(node):
    for child in list(node):
        if local_name(child.tag).endswith("Change"):
            node.remove(child)
        else:
            strip_change_nodes_inplace(child)


def normalize_float_attributes(data):
    def repl(match):
        prefix = match.group(1)
        number = match.group(2)
        suffix = match.group(3)
        if prefix.lower() == b'version="':
            return match.group(0)
        return prefix + str(int(round(float(number)))).encode("ascii") + suffix

    return re.sub(rb'([A-Za-z0-9_:\-.]+=")(\d+\.\d+)(")', repl, data)


def rpr(size=None, bold=False, italic=False, color=None, underline=False):
    props = ET.Element(W + "rPr")
    fonts = ET.SubElement(props, W + "rFonts")
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(W + attr, BODY_FONT)
    if bold:
        ET.SubElement(props, W + "b")
    if italic:
        ET.SubElement(props, W + "i")
    if color:
        color_el = ET.SubElement(props, W + "color")
        color_el.set(W + "val", color)
    if underline:
        u = ET.SubElement(props, W + "u")
        u.set(W + "val", "single")
    if size:
        sz = ET.SubElement(props, W + "sz")
        sz.set(W + "val", str(size))
        sz_cs = ET.SubElement(props, W + "szCs")
        sz_cs.set(W + "val", str(size))
    return props


def ppr(style=None, align=None, before=0, after=120, line=360):
    props = ET.Element(W + "pPr")
    if style:
        pstyle = ET.SubElement(props, W + "pStyle")
        pstyle.set(W + "val", style)
    spacing = ET.SubElement(props, W + "spacing")
    spacing.set(W + "before", str(before))
    spacing.set(W + "after", str(after))
    spacing.set(W + "line", str(line))
    spacing.set(W + "lineRule", "auto")
    if align:
        jc = ET.SubElement(props, W + "jc")
        jc.set(W + "val", align)
    return props


def run(text, size=None, bold=False, italic=False, color=None, underline=False):
    r = ET.Element(W + "r")
    r.append(rpr(size=size, bold=bold, italic=italic, color=color, underline=underline))
    t = ET.SubElement(r, W + "t")
    t.set(XML_SPACE, "preserve")
    t.text = text
    return r


def paragraph(
    text="",
    style=None,
    align=None,
    size=24,
    bold=False,
    italic=False,
    color=None,
    before=0,
    after=120,
    line=360,
):
    p = ET.Element(W + "p")
    p.append(ppr(style=style, align=align, before=before, after=after, line=line))
    if text:
        p.append(run(text, size=size, bold=bold, italic=italic, color=color))
    return p


def heading1(text, page_break=False):
    elements = []
    if page_break:
        elements.append(page_break_para())
    elements.append(paragraph(text, style="Heading1", size=None))
    return elements


def heading2(text):
    return paragraph(text, style="Heading2", size=None)


def body(text, after=120):
    return paragraph(text, size=24, after=after, line=360)


def compact_body(text, after=40, bold=False):
    return paragraph(text, size=21, bold=bold, after=after, line=300)


def toc_title(text, page_break=False):
    elements = []
    if page_break:
        elements.append(page_break_para())
    elements.append(paragraph(text, align="center", size=40, bold=True, after=160, line=360))
    return elements


def list_entry(text):
    return paragraph(text, size=23, after=70, line=300)


def caption(text, center=False):
    return paragraph(
        text,
        align="center" if center else None,
        size=23,
        bold=True,
        color=CAPTION_BLUE,
        after=80,
        line=300,
    )


def page_break_para():
    p = ET.Element(W + "p")
    r = ET.SubElement(p, W + "r")
    br = ET.SubElement(r, W + "br")
    br.set(W + "type", "page")
    return p


def has_page_break(p):
    for br in p.findall(".//" + W + "br"):
        if br.get(W + "type") == "page":
            return True
    return False


def hyperlink_paragraph(prefix, link_text, rid):
    p = paragraph("", align="left", size=24, after=120, line=360)
    if prefix:
        p.append(run(prefix, size=24))
    hyperlink = ET.Element(W + "hyperlink")
    hyperlink.set(R + "id", rid)
    hyperlink.append(run(link_text, size=24, color="0563C1", underline=True))
    p.append(hyperlink)
    return p


def pseudo_table(rows):
    elements = []
    for index, row in enumerate(rows):
        clean_cells = [collapse_space(cell).replace("|", "/") for cell in row]
        line = " | ".join(clean_cells)
        if line:
            elements.append(compact_body(line, bold=index == 0))
    elements.append(paragraph("", size=21, after=80, line=300))
    return elements


def rows_from_table(table):
    rows = []
    for tr in table.findall(W + "tr"):
        cells = []
        for tc in tr.findall(W + "tc"):
            cells.append(collapse_space(text_of(tc)))
        if any(cells):
            rows.append(cells)
    return rows


def collect_caption_titles(children, additional_tables):
    figures = []
    tables = []
    seen_tables = set()
    for child in children:
        if child.tag != W + "p":
            continue
        text = collapse_space(text_of(child))
        if text.startswith("Hình "):
            figures.append(text)
        elif text.startswith("Bảng ") and text not in seen_tables:
            tables.append(text)
            seen_tables.add(text)
    for text in ORIGINAL_TABLE_CAPTIONS + additional_tables:
        if text not in seen_tables:
            tables.append(text)
            seen_tables.add(text)
    return figures, tables


def build_reference_links(rels_root, urls):
    existing_ids = []
    for rel in rels_root.findall(REL + "Relationship"):
        rid = rel.get("Id", "")
        if rid.startswith("rId") and rid[3:].isdigit():
            existing_ids.append(int(rid[3:]))
    next_id = max(existing_ids or [0]) + 1
    url_to_rid = {}
    for url in urls:
        rid = f"rId{next_id}"
        next_id += 1
        rel = ET.SubElement(rels_root, REL + "Relationship")
        rel.set("Id", rid)
        rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink")
        rel.set("Target", url)
        rel.set("TargetMode", "External")
        url_to_rid[url] = rid
    return url_to_rid


def remove_old_blank_gap(children):
    toc_idx = None
    ch1_idx = None
    for idx, child in enumerate(children):
        if child.tag == W + "p" and collapse_space(text_of(child)) == "Mục lục":
            toc_idx = idx
        if toc_idx is not None and child.tag == W + "p" and collapse_space(text_of(child)).startswith("CHƯƠNG 1."):
            ch1_idx = idx
            break
    if toc_idx is None or ch1_idx is None or ch1_idx <= toc_idx + 1:
        return toc_idx, children
    return toc_idx, children[: toc_idx + 1] + children[ch1_idx:]


def previous_text(children):
    for child in reversed(children):
        if child.tag == W + "p":
            text = collapse_space(text_of(child))
            if text:
                return text
    return ""


def remove_known_sparse_breaks(children):
    cleaned = []
    for index, child in enumerate(children):
        if child.tag == W + "p" and not collapse_space(text_of(child)) and has_page_break(child):
            prev = previous_text(cleaned)
            next_text = ""
            for nxt in children[index + 1 :]:
                next_text = collapse_space(text_of(nxt))
                if next_text:
                    break
            if prev.startswith("Nhận xét. BMI") and next_text.startswith("Bảng 2.1."):
                continue
        cleaned.append(child)
    return cleaned


def build_front_lists(figure_titles, table_titles):
    elements = []
    elements.extend(toc_title("Danh sách hình ảnh"))
    if figure_titles:
        for item in figure_titles:
            elements.append(list_entry(item))
    else:
        elements.append(list_entry("Chưa có hình ảnh được đánh số trong báo cáo."))
    elements.append(page_break_para())
    elements.extend(toc_title("Danh sách bảng"))
    if table_titles:
        for item in table_titles:
            elements.append(list_entry(item))
    else:
        elements.append(list_entry("Chưa có bảng được đánh số trong báo cáo."))
    elements.append(page_break_para())
    return elements


def build_added_sections(url_to_rid):
    repo_url = "https://github.com/tuananhtrieu1305/ISD_Assignment01"
    diabetes_nb = repo_url + "/blob/main/pipeline/diabetes_pipeline.ipynb"
    house_nb = repo_url + "/blob/main/pipeline/house_price_pipeline.ipynb"
    customer_nb = repo_url + "/blob/main/pipeline/customer_behavior_pipeline.ipynb"

    elements = []
    elements.extend(heading1("CHƯƠNG 6. PHÂN TÍCH THIẾT KẾ VÀ TRIỂN KHAI HỆ THỐNG", page_break=True))
    elements.append(heading2("6.1. Kiến trúc tổng thể"))
    elements.append(body("Hệ thống được tổ chức theo mô hình client - server, trong đó toàn bộ quá trình huấn luyện và đóng gói mô hình được thực hiện trong thư mục pipeline, còn quá trình phục vụ dự đoán được tách ra tại tầng backend. Cách tổ chức này giúp phần giao diện chỉ cần quan tâm tới dữ liệu đầu vào, trạng thái gửi yêu cầu và hiển thị kết quả, trong khi backend chịu trách nhiệm nạp mô hình, tiền xử lý dữ liệu và đảm bảo định dạng phản hồi thống nhất."))
    elements.append(body("Ba bài toán trong báo cáo gồm phân loại nguy cơ tiểu đường, hồi quy giá nhà tại Việt Nam và phát hiện nhóm hành vi khách hàng. Mỗi bài toán có một bộ artifact riêng, bao gồm metadata.json, feature_schema.json, preprocessor.joblib và model.npz. Bộ metadata lưu thông tin mô hình và các tham số quan trọng, feature_schema mô tả trường nhập liệu, preprocessor thực hiện biến đổi dữ liệu trước khi suy luận, còn model.npz lưu trọng số của mạng nơ-ron đã huấn luyện."))
    elements.append(body("Luồng triển khai tổng thể bắt đầu từ notebook, nơi dữ liệu được làm sạch, phân tích, huấn luyện và đánh giá. Sau khi chọn mô hình phù hợp, notebook xuất ra các artifact cố định để backend sử dụng. Web app và mobile app không đọc trực tiếp notebook mà gọi API của backend, nhờ đó giao diện không phụ thuộc vào chi tiết nội bộ của mô hình và có thể thay đổi cách trình bày mà không ảnh hưởng tới pipeline học máy."))
    elements.append(body("Thiết kế này cũng giúp việc mở rộng trở nên rõ ràng hơn. Khi cần bổ sung bài toán mới, nhóm phát triển có thể tạo thêm một thư mục pipeline tương tự, bổ sung schema và endpoint tương ứng ở backend, sau đó thêm màn hình nhập liệu ở web và mobile. Phần contract quan trọng nhất là feature_schema, vì đây là nơi thống nhất tên trường, kiểu dữ liệu, giá trị mặc định và nhóm hiển thị trên giao diện."))

    elements.append(caption("Bảng 6.1. Nhóm API chính của hệ thống"))
    elements.extend(
        pseudo_table(
            [
                ["Nhóm", "Endpoint", "Vai trò"],
                ["Metadata", "/health, /api/models, /api/schemas", "Kiểm tra trạng thái dịch vụ và trả về thông tin schema cho giao diện"],
                ["Diabetes", "/api/diabetes, /api/diabetes/compare", "Dự đoán nguy cơ tiểu đường và so sánh nhiều hồ sơ đầu vào"],
                ["House Price", "/api/house, /api/house/compare", "Dự đoán giá nhà sau khi tiền xử lý đặc trưng diện tích, vị trí và pháp lý"],
                ["Customer Behavior", "/api/customer-behavior, /api/customer-behavior/compare", "Ước lượng nhóm quan tâm hành vi khách hàng từ các tín hiệu nhân khẩu học và sở thích"],
            ]
        )
    )

    elements.append(page_break_para())
    elements.append(heading2("6.2. Thiết kế Backend"))
    elements.append(body("Backend được xây dựng bằng Flask và mở CORS để web app, mobile app có thể gọi API trong môi trường phát triển. Khi ứng dụng khởi động, backend duyệt qua ba thư mục mô hình trong pipeline, đọc metadata, schema, preprocessor và trọng số. Việc nạp trước như vậy làm giảm độ trễ khi người dùng gửi yêu cầu, đồng thời giúp endpoint /health phản ánh chính xác tình trạng sẵn sàng của từng pipeline."))
    elements.append(body("Ở tầng xử lý request, backend nhận dữ liệu JSON và chuyển đổi thành DataFrame một dòng theo đúng danh sách feature_names. Cách làm này phù hợp với các preprocessor được lưu từ giai đoạn huấn luyện, vì thứ tự cột và tên cột phải khớp với dữ liệu đã dùng trong notebook. Nếu một trường bị thiếu, backend có thể dựa vào giá trị mặc định trong schema hoặc trả lỗi rõ ràng, tránh để mô hình suy luận trên dữ liệu không đầy đủ."))
    elements.append(body("Mô hình DNN được triển khai lại bằng NumPy thay vì phụ thuộc trực tiếp vào framework huấn luyện. Với bài toán phân loại, đầu ra cuối cùng đi qua sigmoid và được so sánh với threshold lưu trong metadata. Với bài toán hồi quy, đầu ra tuyến tính được đưa về thang log chuẩn hóa, sau đó biến đổi ngược bằng target_log_mean, target_log_std và hàm expm1 để nhận giá trị tiền tệ cuối cùng. Cách lưu tham số này giúp kết quả inference ở backend bám sát notebook ban đầu."))
    elements.append(body("Các endpoint compare phục vụ nhu cầu so sánh nhiều kịch bản đầu vào. Chức năng này đặc biệt hữu ích với bài toán giá nhà và hành vi khách hàng, vì người dùng có thể thay đổi một vài đặc trưng như diện tích, vị trí, thu nhập hoặc mức quan tâm và quan sát sự thay đổi của kết quả. Về mặt thiết kế, compare không tạo mô hình mới mà chỉ lặp lại cùng một pipeline dự đoán trên nhiều hồ sơ, sau đó gom kết quả trả về theo danh sách."))
    elements.append(body("Một điểm quan trọng của backend là tách rõ phần metadata khỏi phần logic xử lý. Các nhãn, mô tả ngắn, loại bài toán, threshold và tham số chuẩn hóa không nên viết cứng trong giao diện. Khi cần cập nhật mô hình, nhóm chỉ cần thay artifact trong pipeline và kiểm tra lại schema, hạn chế rủi ro giao diện hiển thị sai so với mô hình đang chạy."))

    elements.append(page_break_para())
    elements.append(heading2("6.3. Thiết kế Web Frontend"))
    elements.append(body("Web frontend được xây dựng bằng React, TypeScript và Vite. Các request tới backend được gom trong predictionApi.ts để định nghĩa rõ kiểu dữ liệu đầu vào và đầu ra cho từng bài toán. Việc khai báo type giúp phát hiện sớm sai lệch giữa giao diện và API, đặc biệt với bài toán Customer Behavior có số lượng đặc trưng lớn hơn hai bài toán còn lại."))
    elements.append(body("Về mặt trải nghiệm người dùng, giao diện web cần tránh hiển thị quá nhiều ô nhập liệu cùng lúc. Vì vậy các trường được chia thành nhóm theo ý nghĩa nghiệp vụ, ví dụ nhóm thông tin sức khỏe, chỉ số xét nghiệm, thông tin bất động sản, vị trí, tiện ích, nhân khẩu học hoặc nhóm sở thích. Mỗi nhóm được đặt trong dropdown có thể đóng mở, giúp người dùng tập trung vào một phần dữ liệu tại một thời điểm mà vẫn không mất khả năng rà soát toàn bộ biểu mẫu."))
    elements.append(body("Các ô nhập liệu được thiết kế để bám theo feature_schema thay vì tự suy đoán từ giao diện. Trường số sử dụng input dạng numeric, trường phân loại sử dụng lựa chọn cố định, còn những thuộc tính nhị phân dùng kiểu chọn phù hợp. Cách này giúp giảm lỗi nhập liệu và làm rõ ý nghĩa từng biến đối với người dùng cuối. Khi schema thay đổi, phần web chỉ cần cập nhật mapping hiển thị mà không phải thay đổi toàn bộ luồng gọi API."))
    elements.append(body("Kết quả dự đoán trên web được đặt gần khu vực thao tác chính, bao gồm nhãn dự đoán, xác suất hoặc giá trị ước lượng và một số thông tin giải thích ngắn. Với bài toán phân loại, giao diện ưu tiên thể hiện mức rủi ro và ngưỡng quyết định. Với bài toán hồi quy, giao diện thể hiện giá trị tiền tệ theo định dạng dễ đọc. Với bài toán hành vi khách hàng, giao diện cần nhấn mạnh nhóm quan tâm được dự đoán để người dùng hiểu mục tiêu phân khúc."))
    elements.append(body("Bản web cũng cần có các trạng thái rõ ràng cho loading, lỗi kết nối và dữ liệu chưa hợp lệ. Khi backend chưa chạy, thông báo lỗi không nên chỉ là lỗi kỹ thuật mà cần cho biết API base URL và gợi ý kiểm tra dịch vụ. Đây là chi tiết nhỏ nhưng quan trọng trong một hệ thống demo, vì báo cáo không chỉ đánh giá mô hình mà còn đánh giá khả năng triển khai thành ứng dụng hoàn chỉnh."))

    elements.append(page_break_para())
    elements.append(heading2("6.4. Thiết kế Mobile App"))
    elements.append(body("Mobile app được xây dựng bằng Expo và React Native, chia sẻ cùng cách gọi API với web nhưng phải tối ưu cho màn hình nhỏ. Khác với web, mobile không có đủ không gian để đặt nhiều cột hoặc nhiều nhóm nhập liệu cạnh nhau, vì vậy cấu trúc dropdown theo từng nhóm càng quan trọng. Người dùng có thể mở lần lượt từng nhóm, nhập dữ liệu và quay lại nhóm trước mà bố cục không bị quá dài hoặc rối."))
    elements.append(body("Các thành phần nhập liệu trên mobile cần có vùng chạm đủ lớn, khoảng cách hợp lý và trạng thái mở đóng mượt. Với các trường chọn, app nên dùng danh sách lựa chọn rõ ràng thay vì yêu cầu người dùng gõ tay giá trị phân loại. Với trường số, bàn phím numeric giúp giảm lỗi nhập. Những lựa chọn này làm cho app phù hợp hơn với bối cảnh thao tác nhanh trên thiết bị di động."))
    elements.append(body("Mobile app vẫn giữ cùng contract với backend: dữ liệu gửi lên phải trùng tên trường và kiểu dữ liệu với schema. Điểm khác biệt nằm ở cách tổ chức màn hình, trạng thái điều hướng và phản hồi sau khi dự đoán. Sau khi có kết quả, app nên hiển thị tóm tắt ngắn gọn, sau đó cho phép người dùng quay lại chỉnh từng nhóm dữ liệu mà không phải nhập lại toàn bộ biểu mẫu."))
    elements.append(body("Trong assignment này, bản mobile đóng vai trò chứng minh rằng pipeline học máy không bị giới hạn ở một giao diện web. Khi API đã ổn định, cùng một backend có thể phục vụ nhiều client khác nhau. Điều này phản ánh tư duy thiết kế hệ thống thông minh theo hướng tái sử dụng dịch vụ, trong đó mô hình học máy được đóng gói như một năng lực nền tảng và giao diện chỉ là các lớp truy cập khác nhau."))

    elements.append(page_break_para())
    elements.append(heading2("6.5. Đồng bộ schema giữa notebook, API và giao diện"))
    elements.append(body("Ba notebook trong pipeline không chỉ tạo mô hình mà còn là nguồn gốc của schema đầu vào. Mỗi notebook cần xác định rõ feature_names, kiểu dữ liệu, các biến phân loại và ví dụ đầu vào mẫu. Khi xuất feature_schema.json, những thông tin này trở thành tài liệu máy đọc được cho backend và frontend. Đây là cầu nối quan trọng giữa phần nghiên cứu mô hình và phần triển khai ứng dụng."))
    elements.append(body("Với Diabetes Classification, schema gồm các thông tin sức khỏe và chỉ số lâm sàng như giới tính, tuổi, BMI, HbA1c, mức đường huyết, tiền sử hút thuốc, bệnh tim mạch và tăng huyết áp. Các trường này cần được nhóm lại theo thông tin cá nhân, bệnh nền và chỉ số xét nghiệm để người dùng dễ hiểu hơn. Nếu đặt tất cả trong một danh sách dài, giao diện sẽ khó đọc và dễ nhập thiếu dữ liệu."))
    elements.append(body("Với Vietnam House Price Regression, schema gồm các thuộc tính về diện tích, vị trí hành chính, số phòng, pháp lý, nội thất, mặt tiền và đặc điểm bất động sản. Đây là bài toán nhạy với dữ liệu phân loại, do giá nhà thường thay đổi mạnh theo quận, huyện, loại nhà và trạng thái giấy tờ. Vì vậy giao diện cần dùng dropdown cho các trường có tập giá trị cố định, đồng thời định dạng kết quả theo đơn vị tiền tệ phù hợp với người dùng Việt Nam."))
    elements.append(body("Với Customer Behavior, số lượng đặc trưng lớn hơn và nhiều trường biểu diễn mức độ quan tâm, thói quen hoặc đặc điểm nhân khẩu học. Nếu không gom nhóm, màn hình sẽ tạo cảm giác quá tải. Việc chia thành các nhóm như thông tin cá nhân, hành vi tiêu dùng, kênh tương tác và sở thích giúp người dùng nhìn thấy cấu trúc của bài toán, đồng thời giảm khả năng nhập nhầm giữa các trường có tên gần giống nhau."))
    elements.append(body("Quy tắc đồng bộ quan trọng là không để frontend tự đặt tên biến khác với backend. Khi giao diện muốn hiển thị nhãn tiếng Việt có dấu, phần nhãn chỉ nên nằm ở UI, còn key gửi API vẫn giữ nguyên theo schema. Như vậy báo cáo vừa đáp ứng yêu cầu trình bày tiếng Việt dễ đọc, vừa giữ tính nhất quán kỹ thuật của hệ thống."))

    elements.append(page_break_para())
    elements.append(heading2("6.6. Luồng inference và kiểm thử triển khai"))
    elements.append(body("Luồng inference bắt đầu khi người dùng nhấn nút dự đoán trên web hoặc mobile. Client kiểm tra dữ liệu cơ bản, tạo JSON payload và gửi tới endpoint tương ứng. Backend nhận request, chuẩn hóa payload theo schema, đưa dữ liệu qua preprocessor.joblib rồi chuyển vector đặc trưng đã biến đổi vào mô hình NumPy. Kết quả sau cùng được chuyển về dạng JSON để giao diện hiển thị."))
    elements.append(body("Ở bài toán phân loại, backend cần trả về nhãn dự đoán và xác suất để người dùng hiểu mức độ tin cậy tương đối. Ở bài toán hồi quy, backend cần trả về giá trị dự đoán đã biến đổi ngược về đơn vị thực. Ở bài toán hành vi khách hàng, backend cần trả về nhóm hoặc nhãn hành vi kèm mô tả ngắn. Các phản hồi này nên thống nhất về cấu trúc để frontend có thể xử lý loading, success và error theo cùng một mẫu."))
    elements.append(body("Kiểm thử triển khai nên bao gồm ba lớp. Lớp thứ nhất là kiểm thử artifact, đảm bảo các file metadata, schema, preprocessor và model.npz tồn tại đủ trong từng thư mục pipeline. Lớp thứ hai là kiểm thử API, gửi demo_input từ schema tới từng endpoint và kiểm tra phản hồi có đủ trường kết quả. Lớp thứ ba là kiểm thử giao diện, nhập dữ liệu trên web và mobile để chắc chắn các dropdown, input và trạng thái kết quả hoạt động như mong muốn."))
    elements.append(body("Ngoài kiểm thử chức năng, cần kiểm tra khả năng tái lập kết quả. Nếu notebook được chạy lại trên cùng dữ liệu và cùng tham số, artifact xuất ra nên có cùng cấu trúc schema và cùng ý nghĩa đầu ra. Trường hợp mô hình được huấn luyện lại với kết quả khác, metadata phải cập nhật phiên bản hoặc thông tin đánh giá để báo cáo và giao diện không nhầm lẫn giữa các lần thử nghiệm."))

    elements.append(heading2("6.7. Rủi ro và hướng kiểm soát"))
    elements.append(body("Rủi ro đầu tiên là sai lệch dữ liệu giữa tập huấn luyện và dữ liệu người dùng nhập trong thực tế. Ví dụ, phân bố tuổi, thu nhập, khu vực nhà đất hoặc thói quen tiêu dùng có thể thay đổi theo thời gian. Khi dữ liệu thực tế khác xa dữ liệu huấn luyện, mô hình vẫn trả kết quả nhưng độ tin cậy giảm. Cách kiểm soát là lưu lại phiên bản dữ liệu, theo dõi thống kê đầu vào và định kỳ đánh giá lại mô hình."))
    elements.append(body("Rủi ro thứ hai là lỗi schema. Nếu frontend gửi thiếu trường hoặc dùng key sai, preprocessor có thể không xử lý được hoặc cho ra vector không đúng ý nghĩa. Vì vậy backend phải coi schema là hợp đồng bắt buộc, còn frontend phải dùng schema để sinh hoặc kiểm tra biểu mẫu. Việc thêm dropdown và gom nhóm input không chỉ phục vụ thẩm mỹ mà còn làm giảm rủi ro nhập sai."))
    elements.append(body("Rủi ro thứ ba là cách diễn giải kết quả. Với các bài toán dự đoán sức khỏe hoặc giá trị tài sản, kết quả của mô hình chỉ nên được xem như tham khảo trong phạm vi học thuật. Báo cáo cần trình bày rõ giới hạn này để tránh hiểu mô hình như một công cụ chẩn đoán hoặc định giá chính thức. Đây là yêu cầu quan trọng khi đưa các hệ thống thông minh từ notebook sang ứng dụng có giao diện người dùng."))

    elements.append(page_break_para())
    elements.append(heading2("6.8. Liên kết mã nguồn và notebook"))
    elements.append(body("Toàn bộ mã nguồn, notebook pipeline và các artifact mô hình được đặt cùng repository để tiện kiểm tra. Việc gắn link trực tiếp giúp người đọc báo cáo truy xuất lại quy trình huấn luyện, xem cấu trúc backend, đối chiếu phần web và mobile, đồng thời kiểm chứng rằng kết quả trình bày trong báo cáo có thể liên hệ với mã nguồn thực tế."))
    elements.append(hyperlink_paragraph("GitHub repository: ", repo_url, url_to_rid[repo_url]))
    elements.append(hyperlink_paragraph("Notebook Diabetes Classification: ", diabetes_nb, url_to_rid[diabetes_nb]))
    elements.append(hyperlink_paragraph("Notebook Vietnam House Price Regression: ", house_nb, url_to_rid[house_nb]))
    elements.append(hyperlink_paragraph("Notebook Customer Behavior / Interest Discovery: ", customer_nb, url_to_rid[customer_nb]))
    elements.append(body("Các đường dẫn trên tương ứng với thư mục pipeline trong project. Khi chạy lại notebook, cần kiểm tra rằng artifact xuất ra vẫn nằm trong các thư mục pipeline/diabetes, pipeline/house_price và pipeline/customer_behavior để backend có thể nạp đúng mô hình."))

    elements.extend(heading1("KẾT LUẬN", page_break=True))
    elements.append(body("Assignment 03 không chỉ dừng ở việc huấn luyện ba mô hình học máy mà còn mở rộng sang bài toán đóng gói và triển khai thành hệ thống có thể sử dụng. Qua ba ứng dụng, báo cáo cho thấy mỗi loại bài toán có đặc trưng riêng: Diabetes Classification tập trung vào phân loại rủi ro, Vietnam House Price Regression tập trung vào giá trị liên tục, còn Customer Behavior hướng tới nhận diện nhóm hành vi hoặc mức quan tâm của khách hàng."))
    elements.append(body("Việc bổ sung backend, web frontend và mobile app giúp pipeline trở nên hoàn chỉnh hơn. Backend giữ vai trò phục vụ mô hình và bảo vệ tính nhất quán dữ liệu; web frontend cung cấp trải nghiệm nhập liệu đầy đủ trên màn hình lớn; mobile app chứng minh khả năng mở rộng sang thiết bị di động. Sự kết hợp này phù hợp với mục tiêu của học phần phát triển các hệ thống thông minh, vì mô hình chỉ thật sự có ý nghĩa khi được tích hợp vào một luồng sử dụng rõ ràng."))
    elements.append(body("Bên cạnh kết quả đạt được, hệ thống vẫn còn những hạn chế như kích thước dữ liệu, độ ổn định của mô hình khi gặp dữ liệu mới, khả năng giải thích dự đoán và kiểm thử tự động trên nhiều môi trường. Trong các hướng phát triển tiếp theo, hệ thống có thể bổ sung dashboard theo dõi, logging đầu vào, kiểm thử hồi quy mô hình, cơ chế versioning artifact và tài liệu API chi tiết hơn. Những cải tiến này sẽ giúp sản phẩm demo tiến gần hơn tới một hệ thống thông minh có khả năng vận hành lâu dài."))

    elements.extend(heading1("PHỤ LỤC A. LIÊN KẾT VÀ TÀI NGUYÊN NỘP BÀI", page_break=True))
    elements.append(body("Phụ lục này tổng hợp lại các tài nguyên chính dùng trong quá trình hoàn thiện báo cáo. Mục đích của phụ lục là giúp giảng viên hoặc người đọc nhanh chóng truy cập đúng mã nguồn, notebook và thư mục artifact khi cần kiểm tra lại kết quả."))
    elements.append(caption("Bảng A.1. Danh sách liên kết và tài nguyên"))
    elements.extend(
        pseudo_table(
            [
                ["Tài nguyên", "Đường dẫn"],
                ["Repository", repo_url],
                ["Notebook Diabetes", "pipeline/diabetes_pipeline.ipynb"],
                ["Notebook House Price", "pipeline/house_price_pipeline.ipynb"],
                ["Notebook Customer Behavior", "pipeline/customer_behavior_pipeline.ipynb"],
                ["Backend", "backend/app.py"],
                ["Web frontend", "web/src"],
                ["Mobile app", "mobile"],
            ]
        )
    )
    elements.append(body("Khi nộp bài, cần đảm bảo các file notebook, mã nguồn backend, web, mobile và artifact mô hình vẫn nằm trong đúng cấu trúc thư mục. Điều này giúp quá trình chấm bài hoặc chạy lại demo không bị phụ thuộc vào đường dẫn tuyệt đối trên máy cá nhân."))

    elements.extend(build_more_appendices())
    return elements


def build_more_appendices():
    elements = []
    elements.extend(heading1("PHỤ LỤC B. ĐẶC TẢ NHÓM INPUT CHO WEB VÀ MOBILE", page_break=True))
    elements.append(body("Phụ lục B mô tả cách nhóm các trường đầu vào khi triển khai biểu mẫu dự đoán trên web và mobile. Nội dung này được bổ sung vì ba pipeline có số lượng feature khác nhau, trong đó Customer Behavior có nhiều biến nhất và dễ làm giao diện trở nên dài nếu trình bày toàn bộ trường ở cùng một mức."))
    elements.append(body("Nguyên tắc thiết kế chung là giữ key kỹ thuật theo schema, nhưng hiển thị label tiếng Việt có dấu để người dùng dễ hiểu. Mỗi nhóm input tương ứng với một khối logic nghiệp vụ, được đặt trong dropdown có trạng thái mở đóng rõ ràng. Khi một nhóm đang đóng, giao diện vẫn cần thể hiện được người dùng đã nhập bao nhiêu trường hoặc có trường bắt buộc nào còn thiếu."))

    elements.append(heading2("B.1. Nhóm input Diabetes Classification"))
    elements.append(body("Với bài toán Diabetes Classification, các biến đầu vào chủ yếu là dữ liệu sức khỏe cá nhân, bệnh nền và chỉ số xét nghiệm. Do số lượng trường không quá lớn, web có thể hiển thị hai cột trên desktop, nhưng mobile nên chia thành từng dropdown ngắn. Cách chia nhóm giúp người dùng hiểu rõ đâu là thông tin nhân khẩu học, đâu là tình trạng bệnh nền và đâu là chỉ số định lượng."))
    elements.append(body("Nhóm thông tin cá nhân gồm tuổi, giới tính và lịch sử hút thuốc. Nhóm bệnh nền gồm tăng huyết áp và bệnh tim mạch. Nhóm chỉ số xét nghiệm gồm BMI, HbA1c và blood glucose level. Nếu schema mở rộng thêm các biến sức khỏe khác, nhóm mới nên được thêm theo ý nghĩa y khoa thay vì chỉ xếp theo thứ tự cột trong dataset."))
    elements.append(body("Giao diện cần ưu tiên hạn chế nhập sai kiểu dữ liệu. Các giá trị phân loại như gender hoặc smoking_history nên dùng dropdown, còn các chỉ số định lượng cần có input số và mô tả đơn vị nếu có. Với bài toán sức khỏe, cách trình bày càng rõ thì người dùng càng ít hiểu nhầm kết quả dự đoán là kết luận y tế chính thức."))
    elements.append(caption("Bảng B.1. Nhóm input cho Diabetes Classification"))
    elements.extend(
        pseudo_table(
            [
                ["Nhóm", "Trường tiêu biểu", "Ghi chú thiết kế"],
                ["Thông tin cá nhân", "age, gender, smoking_history", "Dùng dropdown cho biến phân loại và input số cho tuổi"],
                ["Bệnh nền", "hypertension, heart_disease", "Dùng lựa chọn Có/Không để giảm lỗi nhập"],
                ["Chỉ số xét nghiệm", "bmi, HbA1c_level, blood_glucose_level", "Dùng input số, giữ khoảng giá trị hợp lý"],
                ["Kết quả", "prediction, probability, threshold", "Hiển thị nhãn rủi ro kèm xác suất tham khảo"],
            ]
        )
    )

    elements.append(page_break_para())
    elements.append(heading2("B.2. Nhóm input Vietnam House Price Regression"))
    elements.append(body("Với bài toán Vietnam House Price Regression, dữ liệu có nhiều yếu tố định tính hơn so với Diabetes. Những trường như thành phố, quận huyện, loại nhà, pháp lý hoặc nội thất có ảnh hưởng mạnh tới giá dự đoán. Nếu người dùng phải gõ tự do, khả năng sai chính tả hoặc nhập giá trị ngoài tập huấn luyện sẽ cao, vì vậy các trường này cần ưu tiên dạng dropdown."))
    elements.append(body("Nhóm diện tích và cấu trúc nhà gồm diện tích, số phòng ngủ, số phòng vệ sinh, số tầng và mặt tiền. Nhóm vị trí gồm tỉnh thành, quận huyện và phường xã nếu dữ liệu có. Nhóm pháp lý và trạng thái gồm loại bất động sản, giấy tờ pháp lý, nội thất và hướng nhà. Mỗi nhóm nên được đặt trong một dropdown để người dùng có thể rà soát từng phần trước khi dự đoán."))
    elements.append(body("Kết quả dự đoán cần định dạng theo đơn vị tỷ đồng hoặc đồng Việt Nam tùy cách backend trả về. Trong báo cáo, target được xử lý qua log transform để giảm lệch phân bố, nhưng giao diện không nên hiển thị giá trị log cho người dùng. Backend chịu trách nhiệm biến đổi ngược, còn frontend chỉ trình bày giá trị cuối cùng ở đơn vị dễ hiểu."))
    elements.append(body("Chức năng compare đặc biệt phù hợp với bài toán giá nhà. Người dùng có thể tạo hai hoặc ba kịch bản, ví dụ giữ nguyên diện tích nhưng thay đổi quận huyện, hoặc giữ nguyên vị trí nhưng thay đổi pháp lý và nội thất. Thiết kế này biến mô hình hồi quy thành công cụ phân tích kịch bản thay vì chỉ là một ô nhập và một kết quả đơn lẻ."))
    elements.append(caption("Bảng B.2. Nhóm input cho Vietnam House Price Regression"))
    elements.extend(
        pseudo_table(
            [
                ["Nhóm", "Trường tiêu biểu", "Ghi chú thiết kế"],
                ["Diện tích và cấu trúc", "area, bedrooms, bathrooms, floors, facade", "Input số, có thể đặt min và step phù hợp"],
                ["Vị trí", "city, district, ward", "Dropdown để giữ đúng tập category đã huấn luyện"],
                ["Pháp lý và trạng thái", "legal_status, furniture, house_type, direction", "Dropdown theo danh mục cố định"],
                ["Kịch bản so sánh", "scenario_name, changed_features", "Cho phép nhân bản hồ sơ và thay một vài biến"],
                ["Kết quả", "predicted_price", "Định dạng tiền tệ, tránh hiển thị target log"],
            ]
        )
    )

    elements.append(page_break_para())
    elements.append(heading2("B.3. Nhóm input Customer Behavior"))
    elements.append(body("Customer Behavior là phần có nhiều input nhất nên cần được thiết kế cẩn thận hơn hai bài toán còn lại. Nếu toàn bộ trường được đặt trên một màn hình, người dùng sẽ khó phân biệt đâu là thông tin cá nhân, đâu là hành vi mua hàng, đâu là kênh tương tác và đâu là sở thích. Vì vậy, việc gom nhóm input thành dropdown không chỉ làm giao diện gọn hơn mà còn giúp phản ánh cấu trúc dữ liệu của bài toán."))
    elements.append(body("Nhóm nhân khẩu học có thể bao gồm tuổi, giới tính, khu vực và mức thu nhập. Nhóm hành vi tiêu dùng gồm tần suất mua, giá trị đơn hàng, số lần truy cập hoặc thời gian gần nhất tương tác. Nhóm kênh và thiết bị gồm channel, device, platform hoặc nguồn traffic. Nhóm sở thích thể hiện các category, brand hoặc nội dung mà khách hàng quan tâm."))
    elements.append(body("Do nhiều trường trong Customer Behavior có tính phân loại hoặc mức độ, frontend cần tránh dùng input text tự do. Dropdown, segmented control hoặc lựa chọn Có/Không phù hợp hơn, vì chúng giữ giá trị đầu vào gần với tập dữ liệu huấn luyện. Với mobile, mỗi dropdown nên có tiêu đề ngắn và trạng thái thu gọn rõ ràng để người dùng không bị lạc trong biểu mẫu dài."))
    elements.append(body("Kết quả của bài toán Customer Behavior nên được diễn giải theo hướng hỗ trợ marketing hoặc phân khúc khách hàng. Thay vì chỉ trả về nhãn số, giao diện cần hiển thị tên nhóm hoặc mô tả ngắn như mức quan tâm, khả năng churn hoặc nhóm hành vi nổi bật. Cách trình bày này làm cho kết quả mô hình dễ hiểu hơn với người dùng không trực tiếp làm kỹ thuật."))
    elements.append(caption("Bảng B.3. Nhóm input cho Customer Behavior"))
    elements.extend(
        pseudo_table(
            [
                ["Nhóm", "Trường tiêu biểu", "Ghi chú thiết kế"],
                ["Nhân khẩu học", "age, gender, region, income_level", "Gom thông tin nền của khách hàng"],
                ["Hành vi tiêu dùng", "purchase_frequency, avg_order_value, recency", "Input số hoặc lựa chọn mức độ"],
                ["Kênh và thiết bị", "channel, device, platform", "Dropdown để tránh lệch category"],
                ["Sở thích", "category_interest, brand_interest, content_interest", "Có thể dùng nhóm checkbox hoặc dropdown nhiều lựa chọn"],
                ["Kết quả", "prediction, probability, segment_label", "Hiển thị nhãn hành vi kèm diễn giải ngắn"],
            ]
        )
    )

    elements.extend(heading1("PHỤ LỤC C. KỊCH BẢN KIỂM THỬ VÀ HƯỚNG DẪN CHẠY DEMO", page_break=True))
    elements.append(body("Phụ lục C trình bày các kịch bản kiểm thử cơ bản để đảm bảo hệ thống có thể chạy từ pipeline tới giao diện. Các kịch bản này không thay thế kiểm thử tự động đầy đủ, nhưng đủ để chứng minh rằng các phần chính của assignment liên kết với nhau: artifact mô hình tồn tại, backend nạp được mô hình, API trả kết quả và giao diện hiển thị đúng trạng thái."))
    elements.append(body("Quy trình kiểm thử nên bắt đầu từ backend. Người kiểm thử chạy Flask app, gọi /health để xác nhận dịch vụ sẵn sàng, sau đó gọi /api/models và /api/schemas để kiểm tra thông tin metadata. Nếu các endpoint này trả dữ liệu đúng, có thể tiếp tục gửi demo input tới từng endpoint dự đoán. Đây là bước quan trọng vì giao diện chỉ hoạt động ổn định khi backend và schema đã đúng."))
    elements.append(caption("Bảng C.1. Kịch bản kiểm thử API và giao diện"))
    elements.extend(
        pseudo_table(
            [
                ["Mã", "Kịch bản", "Kết quả mong đợi"],
                ["TC01", "Gọi /health sau khi backend khởi động", "Trả trạng thái healthy và danh sách pipeline đã nạp"],
                ["TC02", "Gọi /api/schemas", "Trả schema của ba bài toán, đủ nhóm input và demo input"],
                ["TC03", "Gửi demo input Diabetes", "Trả nhãn dự đoán và xác suất"],
                ["TC04", "Gửi demo input House Price", "Trả giá dự đoán ở thang tiền tệ"],
                ["TC05", "Gửi demo input Customer Behavior", "Trả nhóm hành vi hoặc nhãn quan tâm"],
                ["TC06", "Mở web trên desktop", "Dropdown hoạt động, không tràn chữ, kết quả hiển thị đúng"],
                ["TC07", "Mở mobile app", "Các nhóm input đóng mở mượt và thao tác được trên màn hình nhỏ"],
            ]
        )
    )

    elements.append(page_break_para())
    elements.append(heading2("C.1. Kiểm thử trạng thái lỗi"))
    elements.append(body("Ngoài luồng thành công, hệ thống cần được kiểm thử với các trạng thái lỗi phổ biến. Khi backend chưa chạy, web và mobile phải hiển thị thông báo lỗi kết nối thay vì im lặng hoặc giữ loading vô hạn. Khi người dùng nhập thiếu trường bắt buộc, giao diện cần chỉ ra nhóm input liên quan để người dùng sửa nhanh. Khi backend trả lỗi schema, thông báo cần đủ rõ để người phát triển biết trường nào đang sai."))
    elements.append(body("Một lỗi thường gặp trong các demo machine learning là schema frontend không còn khớp với artifact mới nhất. Điều này có thể xảy ra khi notebook được chạy lại và feature_schema thay đổi, nhưng giao diện chưa cập nhật danh sách input. Để kiểm soát, mỗi lần thay pipeline cần chạy lại kịch bản /api/schemas và đối chiếu với type request trong web, mobile."))
    elements.append(body("Trạng thái lỗi cũng cần được kiểm tra trên mobile vì màn hình nhỏ dễ che mất thông báo. Khi dropdown đang đóng mà bên trong có trường lỗi, tiêu đề nhóm nên thể hiện trạng thái cần chú ý. Cách xử lý này giúp người dùng không phải mở từng nhóm để tìm lỗi, đặc biệt với form Customer Behavior có nhiều trường."))

    elements.append(page_break_para())
    elements.append(heading2("C.2. Tiêu chí nghiệm thu bản demo"))
    elements.append(body("Tiêu chí nghiệm thu được dùng để xác định bản demo đã đáp ứng yêu cầu assignment hay chưa. Một bản demo đạt yêu cầu cần chạy được cả ba pipeline, có link mã nguồn và notebook rõ ràng, giao diện tiếng Việt có dấu, các nhóm input được gom hợp lý và kết quả dự đoán hiển thị nhất quán trên web cũng như mobile."))
    elements.append(caption("Bảng C.2. Tiêu chí nghiệm thu bản demo"))
    elements.extend(
        pseudo_table(
            [
                ["Tiêu chí", "Mức đạt yêu cầu"],
                ["Pipeline", "Ba notebook xuất đủ artifact và backend nạp được không lỗi"],
                ["API", "Các endpoint health, schemas, predict và compare hoạt động"],
                ["Web", "Form được gom nhóm, dropdown đóng mở mượt, tiếng Việt có dấu"],
                ["Mobile", "Bố cục phù hợp màn hình nhỏ, input và kết quả không bị tràn"],
                ["Báo cáo", "Có danh sách hình ảnh, danh sách bảng, link GitHub, link notebook và phần thiết kế hệ thống"],
                ["Tái lập", "Có thể chạy lại demo theo cấu trúc thư mục trong repository"],
            ]
        )
    )
    elements.append(body("Các tiêu chí trên giúp phần báo cáo gắn chặt với sản phẩm triển khai. Thay vì chỉ mô tả mô hình đạt chỉ số nào, báo cáo cho thấy hệ thống đã được chuẩn bị để người dùng nhập dữ liệu, gọi API và nhận kết quả trong một luồng hoàn chỉnh. Đây là điểm khác biệt giữa một notebook thử nghiệm và một hệ thống thông minh có khả năng trình diễn."))
    elements.append(body("Trong bối cảnh chấm bài, phụ lục này cũng đóng vai trò như checklist cho người đọc. Nếu cần kiểm tra nhanh, có thể bắt đầu từ repository, mở các notebook trong pipeline, chạy backend, sau đó mở web hoặc mobile để thử một vài input mẫu. Khi toàn bộ chuỗi này hoạt động, assignment chứng minh được cả năng lực mô hình hóa lẫn năng lực tích hợp hệ thống."))
    elements.append(page_break_para())
    elements.append(heading2("C.3. Ghi chú tái lập nhanh"))
    elements.append(body("Để tái lập nhanh bản demo, người kiểm tra nên bắt đầu bằng việc mở repository và xác nhận cấu trúc thư mục pipeline còn đầy đủ. Sau đó chạy backend để kiểm tra các artifact đã được nạp, rồi mở web hoặc mobile để gửi một input mẫu. Trình tự này giúp khoanh vùng lỗi dễ hơn, vì nếu backend chưa nạp được mô hình thì lỗi giao diện chỉ là hệ quả của lỗi tầng dịch vụ."))
    elements.append(body("Khi cần kiểm tra sâu hơn, có thể mở từng notebook để đối chiếu dữ liệu đầu vào, bước preprocessing, chỉ số đánh giá và artifact được xuất ra. Việc đối chiếu này đặc biệt quan trọng khi báo cáo được cập nhật sau khi chạy lại notebook, vì một thay đổi nhỏ trong schema cũng có thể làm payload của web hoặc mobile không còn khớp với backend."))
    elements.append(body("Trong phạm vi assignment, mục tiêu tái lập không phải là xây dựng quy trình production hoàn chỉnh mà là chứng minh rằng người đọc có thể đi từ báo cáo sang mã nguồn, từ mã nguồn sang notebook và từ notebook sang ứng dụng demo. Khi ba phần này liên kết nhất quán, báo cáo có tính kiểm chứng cao hơn và phản ánh đúng quy trình phát triển hệ thống thông minh.")) 

    return elements



def expand_docx(src, dst):
    src = Path(src)
    dst = Path(dst)
    temp_data = {}
    with ZipFile(src, "r") as zin:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename.startswith("word/") and info.filename.endswith(".xml"):
                data = normalize_float_attributes(data)
            temp_data[info.filename] = data

    document_root = ET.fromstring(temp_data["word/document.xml"])
    strip_change_nodes_inplace(document_root)
    body_el = document_root.find(W + "body")
    children = list(body_el)
    sect_pr = None
    if children and children[-1].tag == W + "sectPr":
        sect_pr = copy_without_change_nodes(children[-1])
        children = children[:-1]

    additional_tables = [
        "Bảng 6.1. Nhóm API chính của hệ thống",
        "Bảng A.1. Danh sách liên kết và tài nguyên",
        "Bảng B.1. Nhóm input cho Diabetes Classification",
        "Bảng B.2. Nhóm input cho Vietnam House Price Regression",
        "Bảng B.3. Nhóm input cho Customer Behavior",
        "Bảng C.1. Kịch bản kiểm thử API và giao diện",
        "Bảng C.2. Tiêu chí nghiệm thu bản demo",
    ]
    figure_titles, table_titles = collect_caption_titles(children, additional_tables)
    toc_idx, children = remove_old_blank_gap(children)
    if toc_idx is None:
        raise RuntimeError("Không tìm thấy đoạn Mục lục trong tài liệu.")

    converted_children = []
    table_index = 0
    for child in children:
        if child.tag == W + "tbl":
            expected_caption = ORIGINAL_TABLE_CAPTIONS[table_index] if table_index < len(ORIGINAL_TABLE_CAPTIONS) else ""
            if expected_caption and not previous_text(converted_children).startswith("Bảng "):
                converted_children.append(caption(expected_caption))
            rows = rows_from_table(child)
            converted_children.extend(pseudo_table(rows))
            table_index += 1
        else:
            converted_children.append(copy_without_change_nodes(child))
    children = remove_known_sparse_breaks(converted_children)

    toc_idx = None
    for idx, child in enumerate(children):
        if child.tag == W + "p" and collapse_space(text_of(child)) == "Mục lục":
            toc_idx = idx
            break

    front_lists = build_front_lists(figure_titles, table_titles)

    rels_path = "word/_rels/document.xml.rels"
    rels_root = ET.fromstring(temp_data[rels_path])
    urls = [
        "https://github.com/tuananhtrieu1305/ISD_Assignment01",
        "https://github.com/tuananhtrieu1305/ISD_Assignment01/blob/main/pipeline/diabetes_pipeline.ipynb",
        "https://github.com/tuananhtrieu1305/ISD_Assignment01/blob/main/pipeline/house_price_pipeline.ipynb",
        "https://github.com/tuananhtrieu1305/ISD_Assignment01/blob/main/pipeline/customer_behavior_pipeline.ipynb",
    ]
    url_to_rid = build_reference_links(rels_root, urls)
    added_sections = build_added_sections(url_to_rid)

    final_children = children[: toc_idx + 1] + front_lists + children[toc_idx + 1 :] + added_sections
    if sect_pr is not None:
        final_children.append(sect_pr)

    for child in list(body_el):
        body_el.remove(child)
    for child in final_children:
        body_el.append(child)

    temp_data["word/document.xml"] = ET.tostring(document_root, encoding="utf-8", xml_declaration=True)
    temp_data[rels_path] = ET.tostring(rels_root, encoding="utf-8", xml_declaration=True)

    with ZipFile(dst, "w", ZIP_DEFLATED) as zout:
        with ZipFile(src, "r") as zin:
            for info in zin.infolist():
                data = temp_data[info.filename]
                zout.writestr(info, data)


def main():
    if len(sys.argv) != 3:
        print("Usage: python expand_a03_report.py input.docx output.docx")
        raise SystemExit(2)
    expand_docx(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
