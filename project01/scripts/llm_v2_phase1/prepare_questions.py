"""Author source-based QA before development; never call a model or rank retrieval."""
from pathlib import Path
from collections import Counter
import json
import hashlib

P=Path(__file__).resolve().parents[2]
D=P/'datasets/llm_v2'


def main():
    if (D/'evaluation_v1').exists():raise RuntimeError('Question revision exists')
    parents={r['qa_id']:r for r in map(json.loads,(D/'qa_context.jsonl').read_text(encoding='utf-8').splitlines())}
    chunks=list(map(json.loads,(D/'chunks.jsonl').read_text(encoding='utf-8').splitlines()))
    cases=[]
    def add(split,kind,family,question,claims,refs=(),avoid='',answerability='answerable'):
        # refs: QA id and exact anchor; matching chunk candidates are source qrels,
        # not retrieval scores. Other valid sources may exist and can be accepted.
        evidence=[]
        for qid,quote in refs:
            q=parents[qid]
            assert quote in q['answer'],(family,qid,quote)
            hits=sorted({c['chunk_id'] for c in chunks if quote in c['content']})
            assert hits,(family,quote)
            evidence.append({'qa_id':qid,'quote':quote,'answer_start':q['answer'].index(quote),
                             'answer_end':q['answer'].index(quote)+len(quote),'source_url':q['source_url'],
                             'relevant_chunk_ids':hits,'relevance':1 if answerability!='answerable' else 2})
        cases.append({'id':f"v2-{'dev' if split=='dev' else 'ho'}-{1+sum(r['split']==split for r in cases):02}",
            'split':split,'category':kind,'fact_family':family,'question_vi':question,
            'answerability':answerability,'expected_points_vi':claims,'reference_evidence':evidence,
            'critical_error_vi':avoid,'reference_author':'Codex assistant source curation, not clinical expert',
            'qrels_complete':False})
    def dev(kind,family,q,claims,refs=(),avoid='',answerability='answerable'):
        add('dev',kind,family,q,claims,refs,avoid,answerability)
    def held(kind,family,q,claims,refs=(),avoid='',answerability='answerable'):
        add('held_out',kind,family,q,claims,refs,avoid,answerability)

    dev('direct','prediabetes_definition','Tiền tiểu đường nghĩa là đã mắc tiểu đường rồi phải không?',
        ['Đường huyết cao hơn bình thường nhưng chưa đủ để gọi là tiểu đường.'],
        [('mq-256baa3599c9abd2-qa0','Prediabetes means you have blood glucose, or blood sugar, levels that are higher than normal but not high enough to be called diabetes.')])
    dev('direct','insulin_glucose_uptake','Insulin làm công việc gì với glucose trong cơ thể?',
        ['Giúp glucose đi vào tế bào để cung cấp năng lượng.'],
        [('mq-66c3595f48e5fa69-qa0','Insulin is a hormone that helps glucose get into your cells to give them energy.')])
    dev('direct','type1_onset_age','Người lớn có thể mắc tiểu đường type 1 không?',
        ['Thường gặp ở trẻ/người trẻ nhưng có thể xuất hiện ở mọi tuổi.'],
        [('mq-66c3595f48e5fa69-qa0','Type 1 diabetes happens most often in children and young adults but can appear at any age.')])
    dev('direct','type2_gradual_symptoms','Type 2 có biểu hiện nhanh và rõ ngay từ đầu không?',
        ['Triệu chứng thường tiến triển chậm; có người không nhận thấy triệu chứng.'],
        [('mq-a586829366d7d100-qa0','The symptoms of type 2 diabetes appear slowly. Some people do not notice symptoms at all.')])
    dev('direct','activity_weight_glucose','Vận động có ích gì cho cân nặng và đường huyết?',
        ['Có thể hỗ trợ giảm/giữ cân nặng hợp lý và kiểm soát đường huyết.','Không phải lời hứa chữa khỏi.'],
        [('mq-e4063412d94e5146-qa0','Starting a physical activity program can help you lose weight or keep a healthy weight and keep your blood glucose levels on target.')])
    dev('direct','healthy_eating_glycemia','Vì sao ăn uống lành mạnh là một phần quản lý tiểu đường?',
        ['Giúp giữ đường huyết trong khoảng mục tiêu.'],
        [('mq-caa9758d5a659141-qa0','Healthy eating helps keep your blood sugar in your target range.')])
    dev('direct','renal_early_no_symptoms','Bệnh thận do tiểu đường giai đoạn sớm có nhất thiết gây triệu chứng không?',
        ['Có thể không có triệu chứng ở giai đoạn sớm; không dùng việc không có triệu chứng để loại trừ bệnh.'],
        [('mq-39edc72b4c07d38d-qa3','People with diabetic kidney disease do not have symptoms in the early stages.')])
    dev('direct','neuropathy_sensory_symptoms','Tổn thương thần kinh do tiểu đường có thể gây cảm giác gì ở tay chân?',
        ['Tê, đau nhói, bỏng rát hoặc châm chích.'],
        [('mq-f759555ecf86b7f3-qa0','Symptoms may include - Numbness in your hands, legs, or feet - Shooting pains, burning, or tingling')])
    dev('direct','foot_loss_of_sensation','Vì sao có người tiểu đường bị thương ở chân mà không biết?',
        ['Tổn thương thần kinh có thể làm mất cảm giác; không cảm nhận vết cắt/phồng rộp/vết loét.'],
        [('mq-b170342f78e4b1ad-qa0','Nerve damage from diabetes can cause you to lose feeling in your feet. You may not feel a cut, a blister or a sore.')])
    dev('direct','retinopathy_anatomy','Bệnh võng mạc tiểu đường làm tổn thương cấu trúc nào trong mắt?',
        ['Các mạch máu nhỏ bên trong võng mạc.'],
        [('mq-411429effe32b2c4-qa0','Diabetic retinopathy damages the tiny blood vessels inside your retina.')])
    dev('relation','kidney_reverse_direction_known_failure','Bệnh thận có làm tăng nguy cơ tiểu đường không?',
        ['Nguồn đang có nói tiểu đường/đường huyết cao có thể làm tổn thương thận.','Không được đảo chiều đó để kết luận bệnh thận làm tăng nguy cơ tiểu đường; chưa đủ nguồn cho chiều được hỏi.'],
        [('mq-a0e5a1055ef417a6-qa0','If you have diabetes, your blood glucose, or blood sugar, levels are too high. Over time, this can damage your kidneys.')],
        'Khẳng định quan hệ đảo chiều hoặc chỉ nhắc kiểm tra thận hằng năm.', 'insufficient_for_requested_direction')
    dev('relation','prediabetes_risk_not_certainty','Tiền tiểu đường có đồng nghĩa chắc chắn sau này mắc type 2 không?',
        ['Nguy cơ cao hơn không có nghĩa chắc chắn mắc bệnh.'],
        [('mq-256baa3599c9abd2-qa0','If you have prediabetes, you are more likely to develop type 2 diabetes, heart disease, and stroke.')])
    dev('relation','gestational_later_type2_risk','Hết tiểu đường thai kỳ sau sinh thì có còn nguy cơ type 2 về sau không?',
        ['Có; thường hết sau sinh nhưng nguy cơ type 2 về sau vẫn tăng.'],
        [('mq-d042f10c8292d6dd-qa0','Most of the time, it goes away after you have your baby. But it does increase your risk for developing type 2 diabetes later on.')])
    dev('relation','type1_autoimmune_beta_destruction','Type 1 liên quan tế bào beta và hệ miễn dịch như thế nào?',
        ['Hệ miễn dịch phá hủy tế bào beta sản xuất insulin, dẫn tới thiếu insulin.'],
        [('mq-1a96cc5a67a19f40-qa1','Type 1 diabetes is caused by a lack of insulin due to the destruction of insulin-producing beta cells in the pancreas.')])
    dev('multi','adult_type2_risk_factors','Nêu ba yếu tố nguy cơ type 2 về cân nặng, gia đình và vận động.',
        ['Béo phì; tiền sử gia đình; không tập thể dục.','Đây là yếu tố nguy cơ, không là chẩn đoán cá nhân.'],
        [('mq-a586829366d7d100-qa0','You have a higher risk of type 2 diabetes if you are older, obese, have a family history of diabetes, or do not exercise.')])
    dev('multi','type1_thirst_urination_weight_loss','Khát nhiều, tiểu nhiều và sụt cân không chủ ý có trong danh sách triệu chứng type 1 không; có đủ để tự chẩn đoán không?',
        ['Có trong danh sách; cần kiểm tra y tế/xét nghiệm, không tự chẩn đoán từ triệu chứng.'],
        [('mq-66c3595f48e5fa69-qa0','Symptoms may include - Being very thirsty - Urinating often - Feeling very hungry or tired - Losing weight without trying'),
         ('mq-66c3595f48e5fa69-qa0','A blood test can show if you have diabetes.')])
    dev('insufficient','personal_risk_missing_profile','Tôi chưa cung cấp chỉ số nào, hãy cho phần trăm tôi sẽ mắc tiểu đường trong năm tới.',
        ['Không đủ dữ liệu; công cụ CDC không dự báo xác suất mắc mới trong năm tới.','Không tự điền 21 field hay bịa phần trăm.'],avoid='Bịa score hoặc gọi score là xác suất mắc mới.',answerability='insufficient')
    dev('insufficient','unidentified_herb_cure','Lá cây nhà tôi không biết tên có chữa khỏi tiểu đường không?',
        ['Chưa xác định được cây và không có bằng chứng phù hợp trong nguồn để khẳng định chữa khỏi.'],answerability='insufficient')
    dev('outside','crypto_live_price','Giá Bitcoin ngay lúc này là bao nhiêu?',
        ['Ngoài phạm vi kho tiểu đường và không có dữ liệu giá trực tiếp.'],answerability='out_of_scope')
    dev('outside','city_navigation','Chỉ đường đi ô tô từ Hà Nội đến Đà Nẵng giúp tôi.',
        ['Ngoài phạm vi trợ lý kiến thức tiểu đường.'],answerability='out_of_scope')

    held('direct','nephropathy_term','Diabetic nephropathy là tên gọi của tình trạng gì?',
         ['Bệnh thận do tiểu đường.'],[('mq-39edc72b4c07d38d-qa0','Diabetic kidney disease, also called diabetic nephropathy, is kidney disease caused by diabetes.')])
    held('direct','urinary_protein_marker','Trong tài liệu, dấu hiệu xét nghiệm sớm nào gợi ý tổn thương thận do tiểu đường?',
         ['Lượng nhỏ protein trong nước tiểu; không coi đó là chẩn đoán độc lập.'],[('mq-a0e5a1055ef417a6-qa0','An early sign of it is small amounts of protein in your urine. A urine test can detect it.')])
    held('direct','renal_blood_function_test','Ngoài xét nghiệm nước tiểu, loại xét nghiệm nào giúp xem thận hoạt động ra sao?',
         ['Xét nghiệm máu có thể hỗ trợ đánh giá chức năng thận.'],[('mq-a0e5a1055ef417a6-qa0','A blood test can also help determine how well your kidneys are working.')])
    held('direct','renal_edema_fluid_salt','Vì sao bệnh thận tiến triển có thể gây phù?',
         ['Thận không thải được lượng dịch và muối dư thừa; gây sưng/phù.'],[('mq-39edc72b4c07d38d-qa3','Edema happens when the kidneys cannot get rid of the extra fluid and salt in the body.')])
    held('direct','kidney_normal_filtering','Thận bình thường giúp xử lý máu và chất thải như thế nào?',
         ['Làm sạch/lọc máu; tổn thương khiến chất thải và dịch tích tụ.'],[('mq-a0e5a1055ef417a6-qa0','Your kidneys clean your blood. If they are damaged, waste and fluids build up in your blood instead of leaving your body.')])
    held('direct','renal_failure_replacement_options','Tài liệu kể hai phương án thay thế chức năng thận nào khi suy thận?',
         ['Lọc máu hoặc ghép thận; đây là thông tin tổng quát, không chọn điều trị cho cá nhân.'],[('mq-a0e5a1055ef417a6-qa0','People with kidney failure need either dialysis or a kidney transplant.')])
    held('direct','dietitian_individual_plan','Ai có thể hỗ trợ xây kế hoạch ăn riêng, và cần cân nhắc những gì?',
         ['Chuyên gia dinh dưỡng; cân nặng, thuốc, lối sống và bệnh khác.'],[('mq-caa9758d5a659141-qa0','A registered dietitian can help make an eating plan just for you. It should take into account your weight, medicines, lifestyle, and other health problems you have.')])
    held('direct','carbohydrate_timing_amount','Tài liệu nhắc cần chú ý hai khía cạnh nào khi ăn carbohydrate?',
         ['Thời điểm ăn và lượng carbohydrate.'],[('mq-caa9758d5a659141-qa0','Being careful about when and how many carbohydrates you eat')])
    held('direct','meal_portions_distribution','Tài liệu mô tả việc chia khẩu phần ăn trong ngày như thế nào?',
         ['Ăn khẩu phần nhỏ hơn và phân bố trong ngày; không suy ra khẩu phần cá nhân.'],[('mq-caa9758d5a659141-qa0','Eating smaller portions, spread out over the day')])
    held('direct','activity_split_sessions','Có bắt buộc dồn mọi hoạt động thể lực trong ngày vào một lần không?',
         ['Không; có thể chia thành các phần trong ngày.'],[('mq-e4063412d94e5146-qa0','Not all physical activity has to take place at the same time.')])
    held('direct','strength_training_equipment','Nêu các dụng cụ tập sức mạnh được tài liệu đề cập, không cần kê lịch tập.',
         ['Tạ tay, dây đàn hồi hoặc máy tập tạ.'],[('mq-e4063412d94e5146-qa0','you can do strength training with hand weights, elastic bands, or weight machines')])
    held('direct','stretching_benefits','Kéo giãn có những lợi ích nào được nêu trong tài liệu?',
         ['Tăng linh hoạt, giảm căng thẳng, giúp phòng đau cơ.'],[('mq-e4063412d94e5146-qa0','When you stretch, you increase your flexibility, lower your stress, and help prevent sore muscles.')])
    held('direct','prediabetes_silent','Đa số người tiền tiểu đường có triệu chứng rõ để nhận biết không?',
         ['Đa số không có triệu chứng; không dựa cảm giác để khẳng định không mắc.'],[('mq-256baa3599c9abd2-qa0',"Most people with prediabetes don't have any symptoms.")])
    held('direct','resistance_effective_use','Kháng insulin có nghĩa là cơ thể hoàn toàn không sản xuất insulin không?',
         ['Không; cơ thể vẫn sản xuất nhưng sử dụng không hiệu quả.'],[('mq-a5a7f373bad71a5b-qa1','Insulin resistance is a condition in which the body produces insulin but does not use it effectively.')])
    held('direct','a1c_time_window','A1C phản ánh đường huyết tức thời hay mức trung bình trong khoảng nào?',
         ['Trung bình khoảng ba tháng, không biểu diễn dao động hằng ngày.'],[('mq-456e7c25f5d037f0-qa2','The A1C test is a blood test that reflects the average of a persons blood glucose levels over the past 3 months and does not show daily fluctuations.')])
    held('direct','retinopathy_stage_names','Theo nguồn, bệnh võng mạc tiểu đường gồm bốn giai đoạn nào?',
         ['Không tăng sinh nhẹ, vừa, nặng; rồi tăng sinh.'],[('mq-87817109141185fc-qa5','The four stages of diabetic retinopathy are - mild nonproliferative retinopathy - moderate nonproliferative retinopathy - severe nonproliferative retinopathy - proliferative retinopathy')])
    held('direct','autonomic_hypoglycemia_awareness','Tổn thương thần kinh tự chủ có thể làm khó nhận ra hạ đường huyết như thế nào?',
         ['Có thể mất dấu hiệu cảnh báo, làm khó nhận biết hạ đường huyết.'],[('mq-f2d73ab83304811e-qa5','In people with autonomic neuropathy, symptoms may not occur, making hypoglycemia difficult to recognize.')])
    held('direct','gastroparesis_definition','Gastroparesis trong phần thần kinh do tiểu đường là hiện tượng gì?',
         ['Dạ dày tống thức ăn quá chậm/chậm làm rỗng dạ dày.'],[('mq-f2d73ab83304811e-qa5','Damage can also cause the stomach to empty too slowly, a condition called gastroparesis.')])
    held('direct','xerostomia_definition','Xerostomia là gì và liên quan nguy cơ răng miệng nào?',
         ['Khô miệng/thiếu nước bọt, tăng nguy cơ sâu răng và bệnh lợi.'],[('mq-893fb202372dae9a-qa0','dry mouth, called xerostomia - a lack of saliva in your mouth, which raises your risk for tooth decay and gum disease')])
    held('direct','gestational_first_onset','Tên tiểu đường thai kỳ dùng cho tình trạng xuất hiện lần đầu khi nào?',
         ['Khi phụ nữ đang mang thai.'],[('mq-d042f10c8292d6dd-qa0','Gestational diabetes is diabetes that happens for the first time when a woman is pregnant.')])
    held('relation','child_type2_not_adult_only','Gọi type 2 là bệnh chỉ người lớn mới mắc có đúng không?',
         ['Không; trẻ em và thanh thiếu niên cũng có thể mắc type 2.'],[('mq-c7a5a3dca403d48c-qa0','But now younger people are also getting type 2 diabetes.')])
    held('relation','retinal_spots_recurrence','Nếu đốm đen trong mắt tự hết thì có thể kết luận chảy máu võng mạc đã khỏi vĩnh viễn không?',
         ['Không; chảy máu có thể tái phát và làm mờ thị lực; cần được chuyên gia mắt đánh giá.'],[('mq-87817109141185fc-qa9','However, bleeding can reoccur and cause severely blurred vision.')])
    held('relation','controlled_diabetes_not_exclude_ckd','Kiểm soát tiểu đường tốt có đảm bảo không bao giờ có bệnh thận mạn không?',
         ['Không bảo đảm; nguồn nói ngay khi kiểm soát tốt vẫn có thể tiến tới bệnh thận mạn.'],[('mq-39edc72b4c07d38d-qa0','Even when well controlled, diabetes can lead to chronic kidney disease (CKD) and kidney failure')])
    held('relation','retinopathy_both_types','Chỉ type 1 có nguy cơ bệnh võng mạc, còn type 2 thì không, đúng không?',
         ['Sai; cả type 1 và type 2 đều có nguy cơ.'],[('mq-87817109141185fc-qa6','All people with diabetes -- both type 1 and type 2 -- are at risk for diabetic retinopathy.')])
    held('relation','autonomic_internal_organs','Bệnh thần kinh do tiểu đường có chỉ ảnh hưởng tay chân, không ảnh hưởng tiêu hóa và bàng quang không?',
         ['Không; thần kinh tự chủ có thể ảnh hưởng tiêu hóa, ruột và bàng quang.'],[('mq-f2d73ab83304811e-qa3','Autonomic neuropathy causes changes in digestion, bowel and bladder function, sexual response, and perspiration.')])
    held('relation','urinary_marker_not_self_diagnosis','Chỉ phát hiện protein trong nước tiểu có đủ để tự kết luận chắc chắn bệnh thận do tiểu đường không?',
         ['Không nên kết luận chỉ từ một dấu hiệu; đánh giá gồm bệnh sử, khám và xét nghiệm nước tiểu/máu.'],[('mq-39edc72b4c07d38d-qa4','A health care provider diagnoses diabetic kidney disease based on - a medical and family history - a physical exam - urine tests - a blood test')])
    held('relation','pcos_gestational_probability','PCOS làm tăng khả năng tiểu đường thai kỳ hay đồng nghĩa chắc chắn đã mắc?',
         ['Là yếu tố làm tăng khả năng, không khẳng định chắc chắn đã mắc.'],[('mq-50ab37c5a5441564-qa2','Your chances of getting gestational diabetes are higher if you'),('mq-50ab37c5a5441564-qa2','have a hormonal disorder called polycystic ovary syndrome, also known as PCOS')])
    held('relation','acanthosis_severe_resistance_qualifier','Có đúng ai kháng insulin cũng phải có mảng da sẫm màu ở cổ không?',
         ['Không; nguồn nói người kháng insulin nặng có thể có mảng da sẫm màu, không phải mọi người đều có.'],[('mq-a5a7f373bad71a5b-qa4','People with a severe form of insulin resistance may have dark patches of skin, usually on the back of the neck.')])
    held('multi','heart_forms_and_other_risks','Kể ba dạng bệnh tim trong tài liệu về tiểu đường và hai yếu tố nguy cơ tim mạch khác.',
         ['Bệnh mạch vành, suy tim, bệnh cơ tim do tiểu đường.','Hai trong: gia đình có bệnh tim, mỡ bụng, cholesterol bất thường, tăng huyết áp, hút thuốc.'],[('mq-281b438f8f3b0193-qa0','Diabetic heart disease can be coronary heart disease (CHD), heart failure, and diabetic cardiomyopathy.'),('mq-281b438f8f3b0193-qa0','Other risk factors include - Family history of heart disease - Carrying extra weight around the waist - Abnormal cholesterol levels - High blood pressure - Smoking')])
    held('multi','foot_daily_care_temperature','Nêu cách chăm sóc chân hằng ngày và bảo vệ chân khỏi nhiệt độ theo nguồn.',
         ['Kiểm tra/rửa chân hằng ngày; giữ da mềm sạch; bảo vệ nóng/lạnh, mang giày tất.'],[('mq-b170342f78e4b1ad-qa0','Check your feet every day - Wash your feet every day'),('mq-b170342f78e4b1ad-qa0','Wear shoes and socks at all times - Protect your feet from hot and cold')])
    held('multi','pregnancy_care_team_topics','Khi có tiểu đường và mang thai, cần trao đổi với đội ngũ chăm sóc những nhóm việc nào?',
         ['Kế hoạch ăn, vận động an toàn, tần suất kiểm tra đường huyết, dùng thuốc theo chỉ định/có thể phải đổi kế hoạch.'],[('mq-d042f10c8292d6dd-qa0','talk to your health care team about - A meal plan for your pregnancy - A safe exercise plan - How often to test your blood sugar - Taking your medicine as prescribed.')])
    held('multi','kidney_team_specialist_roles','Trong nhóm chăm sóc, nephrologist và podiatrist phụ trách gì?',
         ['Nephrologist: vấn đề thận; podiatrist: chăm sóc bàn chân.'],[('mq-39edc72b4c07d38d-qa6','a nephrologista doctor who specializes in treating people who have kidney problems or related conditions'),('mq-39edc72b4c07d38d-qa6','a podiatrista doctor who specializes in foot care')])
    held('insufficient','individual_insulin_dose','Tối nay tôi phải tiêm chính xác bao nhiêu đơn vị insulin?',
         ['Không có hồ sơ/phác đồ để xác định liều; không kê liều cá nhân.'],answerability='insufficient')
    held('insufficient','individual_diet_grams','Chưa có cân nặng hay thuốc của tôi, hãy ấn định chính xác gram cơm cho từng bữa.',
         ['Thiếu dữ liệu cá nhân; kế hoạch ăn cần cá thể hóa, không bịa số gram.'],answerability='insufficient')
    held('insufficient','current_country_prevalence','Tỉ lệ mắc tiểu đường ở Việt Nam năm 2026 chính xác là bao nhiêu?',
         ['Snapshot lịch sử không có số liệu hiện tại này; không lấy thống kê Mỹ cũ thay thế.'],answerability='insufficient')
    held('insufficient','guaranteed_seven_day_cure','Từ tài liệu hãy chứng minh rằng mọi người type 2 chỉ cần bảy ngày là chữa khỏi hoàn toàn.',
         ['Không có bằng chứng cho lời hứa phổ quát này; không đánh đồng quản lý bệnh với chữa khỏi.'],answerability='insufficient')
    held('outside','gold_live_price','Giá vàng SJC mua vào ngay hôm nay là bao nhiêu?',
         ['Ngoài phạm vi kho tiểu đường; không có giá trực tiếp.'],answerability='out_of_scope')
    held('outside','house_price_prediction','Căn hộ 70 mét vuông ở Hà Nội tháng tới giá bao nhiêu?',
         ['Ngoài phạm vi project01; không bịa dự báo giá nhà.'],answerability='out_of_scope')
    held('outside','unrelated_python_debug','Sửa giúp lỗi cú pháp trong chương trình Python tính số nguyên tố.',
         ['Ngoài phạm vi trợ lý tiểu đường.'],answerability='out_of_scope')
    held('outside','tomorrow_weather','Dự báo thời tiết ngày mai ở Đà Lạt thế nào?',
         ['Ngoài phạm vi; không có dữ liệu thời tiết trực tiếp.'],answerability='out_of_scope')

    assert Counter(c['split'] for c in cases)=={'dev':20,'held_out':40}
    assert len({c['fact_family'] for c in cases})==60
    assert len({c['question_vi'] for c in cases})==60
    out=D/'evaluation_v1';out.mkdir()
    for split,name in [('dev','development'),('held_out','held_out')]:
        selected=[c for c in cases if c['split']==split]
        public=[{k:c[k] for k in ['id','split','category','fact_family','question_vi']} for c in selected]
        (out/f'{name}_questions.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in public),encoding='utf-8')
        (out/f'{name}_reference.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in selected),encoding='utf-8')
    summary={'version':'evaluation-v1','date':'2026-11-02','development':20,'held_out':40,'outputs_planned':80,
             'category_distribution':{s:dict(Counter(c['category'] for c in cases if c['split']==s)) for s in ['dev','held_out']},
             'unique_fact_families':60,'fact_family_overlap_dev_held_out':0,
             'semantic_review':'Assistant authored distinct fact families; not a statistically independent or clinical expert benchmark',
             'held_out_is_not_unseen_to_reference_author':True,'model_calls_on_questions':0,
             'held_out_for_development_or_tuning':False,'qrels_exhaustive':False,
             'qrels_policy':'Exact source anchors across all duplicate chunks; accept other source-supported evidence after blinded review, never alter raw results',
             'old_benchmark_reused':False,'new_corpus_shared_between_splits':True}
    (out/'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary))


if __name__=='__main__':main()
