export const chapters = [
  {
    route: "/",
    chapter: 1,
    label: "Tổng quan",
    title: "Lịch sử phát triển AI",
    family: "history",
    datasets: ["ch1_iris_history", "ch1_mnist_history", "ch1_imagenet_history"],
    intro:
      "Từ các luật do con người viết đến mô hình học từ dữ liệu. Iris, MNIST và ImageNet minh họa ba bước chuyển; đây không phải chương huấn luyện.",
  },
  {
    route: "/ml",
    chapter: 2,
    label: "ML",
    title: "Machine Learning",
    family: "mlp",
    datasets: ["ch2_cdc_diabetes", "ch2_ames_housing", "ch2_bank_marketing"],
    intro:
      "Biến một bảng đặc trưng thành dự đoán. MLP học các tổ hợp từ đơn giản đến phức tạp; mô hình cổ điển là đối chứng trong kết quả đã lưu.",
  },
  {
    route: "/cnn",
    chapter: 3,
    label: "CNN",
    title: "Học từ hình ảnh",
    family: "cnn",
    datasets: ["ch3_idrid", "ch3_eurosat", "ch3_cifar10"],
    intro:
      "Bộ lọc trượt tìm các mẫu cục bộ. Qua nhiều lớp, đường nét trở thành đặc trưng giúp phân biệt ảnh. Mô hình này có 5 Conv và 2 Dense học được.",
  },
  {
    route: "/rnn",
    chapter: 4,
    label: "RNN–LSTM",
    title: "Học từ chuỗi thời gian",
    family: "rnn",
    datasets: [
      "ch4_gold_pink_sheet",
      "ch4_bis_house_prices",
      "ch4_household_power",
    ],
    intro:
      "Đọc dữ liệu theo thứ tự thời gian. RNN truyền trạng thái qua từng bước; LSTM thêm các cổng để giữ hoặc quên thông tin. Dự báo không được nhìn tương lai.",
  },
  {
    route: "/rag",
    chapter: 5,
    label: "KG–RAG",
    title: "Tri thức có nguồn dẫn",
    family: "kg_rag",
    datasets: ["ch5_medquad_diabetes", "ch5_finqa", "ch5_wikidata_subgraphs"],
    intro:
      "Tìm bằng chứng trước, trả lời sau. B0–B4 kết hợp truy hồi và liên kết đồ thị trên snapshot đã khóa; không gọi LLM hay API bên ngoài.",
  },
  {
    route: "/agents",
    chapter: 6,
    label: "Multi-Agent",
    title: "Phối hợp nhiều tác tử",
    family: "multi_agent",
    datasets: ["ch6_diabetes_tasks", "ch6_house_tasks", "ch6_gold_tasks"],
    intro:
      "Chia công việc thành định tuyến, chuyên gia, kiểm chứng và báo cáo. So A0 trực tiếp, A1 thêm router và A2 thêm verifier/reporter trên cùng yêu cầu ID-bound.",
  },
] as const;
export const datasetNames: Record<string, string> = {
  ch1_iris_history: "Iris",
  ch1_mnist_history: "MNIST",
  ch1_imagenet_history: "ImageNet",
  ch2_cdc_diabetes: "Tiểu đường · CDC",
  ch2_ames_housing: "Giá nhà · Ames",
  ch2_bank_marketing: "Tiếp thị · Bank",
  ch3_idrid: "Võng mạc · IDRiD",
  ch3_eurosat: "Viễn thám · EuroSAT",
  ch3_cifar10: "Vật thể · CIFAR-10",
  ch4_gold_pink_sheet: "Giá vàng · World Bank",
  ch4_bis_house_prices: "Giá nhà · BIS",
  ch4_household_power: "Điện năng · Household",
  ch5_medquad_diabetes: "Y khoa · MedQuAD",
  ch5_finqa: "Tài chính · FinQA",
  ch5_wikidata_subgraphs: "Đồ thị · Wikidata",
  ch6_diabetes_tasks: "Tác vụ tiểu đường",
  ch6_house_tasks: "Tác vụ giá nhà",
  ch6_gold_tasks: "Tác vụ giá vàng",
};
