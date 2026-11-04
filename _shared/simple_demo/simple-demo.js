'use strict';

const data = window.ASSIGN_DATA;
const $ = (id) => document.getElementById(id);
const make = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};

const LABELS = {
  Glucose: 'Đường huyết', BMI: 'BMI', Age: 'Tuổi', Pregnancies: 'Số lần mang thai',
  BloodPressure: 'Huyết áp', DiabetesPedigreeFunction: 'Chỉ số di truyền tiểu đường',
  Area: 'Diện tích (m²)', Frontage: 'Mặt tiền (m)', 'Access Road': 'Đường vào (m)',
  Floors: 'Số tầng', Bedrooms: 'Phòng ngủ', Bathrooms: 'Phòng tắm', age: 'Tuổi',
  transaction_count: 'Số giao dịch', total_transactions: 'Số giao dịch', total_spent: 'Tổng chi tiêu',
  avg_order_value: 'Giá trị đơn trung bình', session_count: 'Số phiên truy cập',
  conversion_rate: 'Tỷ lệ chuyển đổi', avg_rating: 'Đánh giá trung bình',
  HighBP: 'Cao huyết áp', HighChol: 'Cholesterol cao', Smoker: 'Hút thuốc',
  PhysActivity: 'Có vận động', GenHlth: 'Sức khỏe tổng quát (1–5)', Income: 'Nhóm thu nhập (1–8)',
  Area_m2: 'Diện tích (m²)', Frontage_m: 'Mặt tiền (m)', Access_Road_m: 'Đường vào (m)',
  city: 'Tỉnh/thành phố', district: 'Quận/huyện'
};

const BINARY = new Set([
  'email_opt_in', 'has_app', 'HighBP', 'HighChol', 'CholCheck', 'Smoker', 'Stroke',
  'HeartDiseaseorAttack', 'PhysActivity', 'Fruits', 'Veggies', 'HvyAlcoholConsump',
  'AnyHealthcare', 'NoDocbcCost', 'DiffWalk', 'Sex'
]);

// A few preserved demo fixtures intentionally use null to represent missing
// values.  The live HTTP endpoint expects a concrete number, so the form uses
// neutral, easy-to-understand defaults instead of sending invalid JSON input.
const FORM_DEFAULTS = {
  Frontage_m: 5,
  Access_Road_m: 5,
  Bedrooms: 3,
  Bathrooms: 2
};

const EDITABLE = {
  A01: {
    diabetes: ['Glucose', 'BMI', 'Age', 'Pregnancies', 'BloodPressure', 'DiabetesPedigreeFunction'],
    house: ['Area', 'Frontage', 'Access Road', 'Floors', 'Bedrooms', 'Bathrooms']
  },
  A02: {
    diabetes: ['Glucose', 'BMI', 'Age', 'Pregnancies', 'BloodPressure', 'DiabetesPedigreeFunction'],
    house: ['Area', 'Frontage', 'Access Road', 'Floors', 'Bedrooms', 'Bathrooms'],
    customer_behavior: ['age', 'transaction_count', 'total_spent', 'avg_order_value', 'session_count', 'conversion_rate', 'avg_rating', 'customer_tenure_days']
  },
  A03: {
    diabetes: ['HighBP', 'HighChol', 'BMI', 'Smoker', 'PhysActivity', 'GenHlth', 'Age', 'Income'],
    house_price: ['Area_m2', 'Frontage_m', 'Access_Road_m', 'Floors', 'Bedrooms', 'Bathrooms', 'city', 'district'],
    customer_behavior: ['age', 'total_transactions', 'total_spent', 'avg_order_value', 'session_count', 'conversion_rate', 'avg_rating', 'days_since_last_transaction']
  }
};

let task = data.tasks[0];
let mode = 'live';

function format(value) {
  if (typeof value === 'number') return value.toLocaleString('vi-VN', { maximumFractionDigits: 4 });
  return String(value ?? '—');
}

function friendlyModelName(value) {
  return String(value || 'Mô hình').replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function setTaskText() {
  $('task-title').textContent = task.title;
  const live = Boolean(task.endpoint && task.fixture && Object.keys(task.fixture).length);
  $('task-help').textContent = live
    ? data.project === 'A03' ? 'Nhập thông tin, sau đó bấm Kiểm tra để xem dự đoán của Improved DNN.' : 'Nhập thông tin, sau đó bấm Kiểm tra để so sánh kết quả các mô hình.'
    : task.samples?.length
      ? 'Chọn một mẫu đã lưu để xem các mô hình đã dự đoán như thế nào.'
      : 'Chọn chỉ số để so sánh các mô hình trên kết quả đã lưu.';
  $('mode-pill').textContent = live ? 'Inference CPU' : 'Kết quả đã lưu';
}

function addField(key, value) {
  const formValue = value ?? FORM_DEFAULTS[key] ?? value;
  const label = make('label', undefined, 'field');
  label.append(make('span', key === 'Age' && data.project === 'A03' ? 'Nhóm tuổi CDC (1–13)' : LABELS[key] || key));
  let control;
  if (BINARY.has(key)) {
    control = document.createElement('select');
    for (const [raw, text] of [['0', 'Không'], ['1', 'Có']]) {
      const option = make('option', text);
      option.value = raw;
      option.selected = Number(formValue) === Number(raw);
      control.append(option);
    }
    control.dataset.type = 'number';
  } else {
    control = document.createElement('input');
    const numeric = typeof formValue === 'number' || formValue === null;
    control.type = numeric ? 'number' : 'text';
    if (numeric) control.step = 'any';
    control.value = formValue ?? '';
    control.dataset.type = numeric ? 'number' : 'string';
  }
  control.name = key;
  control.id = `field-${key.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`;
  label.htmlFor = control.id;
  label.append(control);
  $('input-fields').append(label);
}

function renderInputForm() {
  $('input-fields').replaceChildren();
  $('defaults-note').textContent = '';
  const fixture = task.fixture || {};
  if (task.endpoint && Object.keys(fixture).length) {
    mode = 'live';
    const keys = EDITABLE[data.project]?.[task.id] || Object.keys(fixture).slice(0, 10);
    keys.filter((key) => Object.hasOwn(fixture, key)).forEach((key) => addField(key, fixture[key]));
    const hidden = Object.keys(fixture).length - keys.length;
    if (hidden > 0) $('defaults-note').textContent = `${hidden} trường kỹ thuật còn lại dùng giá trị mẫu cố định.`;
    const hasComparison = Boolean(task.models?.length > 1 || data.project === 'A01' || data.project === 'A02');
    $('submit').textContent = hasComparison ? 'Kiểm tra và so sánh' : 'Kiểm tra';
    return;
  }
  renderReplayForm();
}

function addSelect(name, labelText, options) {
  const label = make('label', undefined, 'field full');
  label.append(make('span', labelText));
  const select = document.createElement('select');
  select.name = name;
  select.id = `field-${name}`;
  for (const optionData of options) {
    const option = make('option', optionData.label);
    option.value = optionData.value;
    select.append(option);
  }
  label.htmlFor = select.id;
  label.append(select);
  $('input-fields').append(label);
}

function replayKey(row) {
  return String(row.relative_path ?? row.image_id ?? row.row_index ?? row.CustomerID ?? row.target_date ?? 'mẫu');
}

function renderReplayForm() {
  mode = 'replay';
  const curated = window.ASSIGN_DEMO_PREDICTIONS?.[task.id];
  if (curated?.length) {
    addSelect('sample', 'Chọn mẫu kiểm tra', curated.map((row, index) => ({ value: String(index), label: `${index + 1}. ${row.key.split('/').pop()}` })));
  } else if (task.samples?.length && task.samples[0].rows?.length) {
    addSelect('sample', 'Chọn mẫu kiểm tra', task.samples[0].rows.map((row, index) => ({ value: String(index), label: `${index + 1}. ${replayKey(row)}` })));
  } else {
    const rows = task.tables?.[0]?.rows || [];
    const metrics = Object.keys(rows[0] || {}).filter((key) => rows.some((row) => typeof row[key] === 'number'));
    addSelect('metric', 'Chọn chỉ số so sánh', metrics.map((key) => ({ value: key, label: key })));
  }
  $('submit').textContent = 'Xem kết quả';
}

function readPayload() {
  const payload = { ...(task.fixture || {}) };
  for (const [key, value] of Object.entries(payload)) {
    if (value === null && Object.hasOwn(FORM_DEFAULTS, key)) payload[key] = FORM_DEFAULTS[key];
  }
  for (const control of $('input-fields').querySelectorAll('input, select')) {
    if (control.name === 'sample' || control.name === 'metric') continue;
    if (control.dataset.type === 'number') {
      if (control.value === '') payload[control.name] = null;
      else {
        const value = Number(control.value);
        if (!Number.isFinite(value)) throw new Error(`${LABELS[control.name] || control.name} phải là số hợp lệ.`);
        payload[control.name] = value;
      }
    } else payload[control.name] = control.value.trim();
  }
  return payload;
}

function addResultCard(title, pairs, recommended = false) {
  const card = make('article', undefined, `result-card${recommended ? ' recommended' : ''}`);
  const heading = make('h3', title);
  if (recommended) heading.append(make('span', 'Khuyến nghị', 'badge'));
  card.append(heading);
  const list = document.createElement('dl');
  for (const [key, value] of pairs) list.append(make('dt', key), make('dd', format(value)));
  card.append(list);
  $('results').append(card);
}

function predictionLabel(item) {
  const value = item.prediction ?? item.predicted_label;
  if (task.id.includes('customer')) return Number(value) === 1 ? 'Có nguy cơ rời bỏ' : 'Đang gắn bó';
  if (task.id.includes('diabetes')) return Number(value) === 0 ? 'Âm tính (lớp 0)' : 'Dương tính (lớp 1)';
  return item.predicted_class ?? value;
}

function renderResults(response) {
  $('results').replaceChildren();
  const rows = response.results || [response];
  for (const item of rows) {
    const pairs = [];
    if (item.predicted_price !== undefined) pairs.push(['Giá dự đoán', `${format(item.predicted_price)} tỷ đồng`]);
    else pairs.push(['Kết quả', predictionLabel(item)]);
    const probability = item.probability ?? item.churn_score;
    if (typeof probability === 'number') pairs.push(['Điểm/xác suất mô hình', `${(probability * 100).toFixed(2)}%`]);
    addResultCard(item.model_name || item.model?.name || friendlyModelName(item.model_id), pairs, Boolean(item.recommended));
  }
  if (response.consensus) {
    const ratio = Number(response.consensus.agreement_ratio || 0) * 100;
    $('results').append(make('div', `${response.consensus.agreeing_models}/${response.consensus.total_models} mô hình đồng thuận (${ratio.toFixed(0)}%).`, 'summary-card'));
  }
  if (response.spread) {
    $('results').append(make('div', `Khoảng dự đoán: ${format(response.spread.min)} – ${format(response.spread.max)} tỷ đồng.`, 'summary-card'));
  }
}

function renderReplayResults() {
  $('results').replaceChildren();
  const curated = window.ASSIGN_DEMO_PREDICTIONS?.[task.id];
  const sampleIndex = Number($('input-fields').querySelector('[name="sample"]')?.value || 0);
  if (curated?.length) {
    const sample = curated[sampleIndex];
    $('results').append(make('div', `Nhãn thật: ${sample.true_label}`, 'summary-card'));
    const classLabels = ['Không tiểu đường', 'Tiền tiểu đường', 'Tiểu đường'];
    for (const row of sample.models) addResultCard(friendlyModelName(row.model), [['Dự đoán', task.id === 'diabetes' ? classLabels[Number(row.predicted)] : row.predicted], ['Độ tự tin đã lưu', `${(row.probability * 100).toFixed(2)}%`]]);
    return;
  }
  if (task.samples?.length && task.samples[0].rows?.length) {
    const selected = task.samples[0].rows[sampleIndex];
    const key = replayKey(selected);
    for (const source of task.samples) {
      const row = source.rows.find((candidate) => replayKey(candidate) === key);
      if (!row) continue;
      const name = source.source.toLowerCase().includes('keras') ? 'Keras RNN' : source.source.toLowerCase().includes('pytorch') ? 'PyTorch RNN' : source.source.split('/').pop();
      const pairs = [];
      if (row.predicted_close !== undefined) pairs.push(['Giá dự đoán', row.predicted_close], ['Giá thực tế', row.actual_close]);
      else pairs.push(['Kết quả', Number(row.predicted_label) === 1 ? 'Có nguy cơ rời bỏ' : 'Đang gắn bó'], ['Điểm nguy cơ rời bỏ', `${(Number(row.probability) * 100).toFixed(2)}%`]);
      addResultCard(name, pairs);
      if (row.naive_close !== undefined && !$('results').querySelector('[data-baseline]')) {
        const baseline = make('article', undefined, 'result-card');
        baseline.dataset.baseline = 'true';
        baseline.append(make('h3', 'Baseline giá gần nhất'));
        const dl = document.createElement('dl');
        dl.append(make('dt', 'Dự đoán'), make('dd', format(row.naive_close)));
        baseline.append(dl);
        $('results').append(baseline);
      }
    }
    return;
  }
  const metric = $('input-fields').querySelector('[name="metric"]')?.value;
  const rows = [...(task.tables?.[0]?.rows || [])].filter((row) => typeof row[metric] === 'number');
  const lowerIsBetter = /loss|error|rmse|mae|time|params/i.test(metric || '');
  rows.sort((a, b) => lowerIsBetter ? a[metric] - b[metric] : b[metric] - a[metric]);
  rows.forEach((row, index) => addResultCard(row.Model || row.model || row.model_family || `Mô hình ${index + 1}`, [[metric, row[metric]]], index === 0));
}

async function submit(event) {
  event.preventDefault();
  $('submit').disabled = true;
  $('status').className = '';
  $('status').textContent = mode === 'live' ? 'Đang chạy các mô hình…' : 'Đang đọc kết quả đã lưu…';
  try {
    if (mode === 'replay') renderReplayResults();
    else {
      const response = await fetch(task.endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(readPayload()) });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || `API trả về ${response.status}`);
      renderResults(body);
    }
    $('status').textContent = mode === 'live' ? 'Đã hoàn tất.' : 'Kết quả này được đọc từ output đã lưu, không chạy lại TEST.';
  } catch (error) {
    $('status').className = 'error';
    $('status').textContent = `Không thể xử lý: ${error.message}`;
  } finally {
    $('submit').disabled = false;
  }
}

function renderTask() {
  for (const button of $('datasets').children) button.setAttribute('aria-pressed', String(button.dataset.id === task.id));
  setTaskText();
  renderInputForm();
  $('results').replaceChildren(make('p', 'Kết quả sẽ xuất hiện ở đây sau khi bạn bấm nút.', 'empty'));
  $('status').textContent = '';
  $('notebooks').replaceChildren(...(task.notebooks || []).map((notebook) => {
    const link = make('a', `Mở ${notebook.title} ↗`);
    link.href = notebook.href;
    link.download = '';
    return link;
  }));
}

$('brand').textContent = `${data.project} · MODEL DEMO`;
$('title').textContent = data.title;
$('summary').textContent = data.tasks.some((row) => row.endpoint) ? 'Nhập thông tin và bấm kiểm tra để xem dự đoán.' : 'Chọn dữ liệu minh họa để đối chiếu kết quả các mô hình đã lưu.';
for (const row of data.tasks) {
  const button = make('button', row.title);
  button.type = 'button';
  button.dataset.id = row.id;
  button.addEventListener('click', () => { task = row; renderTask(); });
  $('datasets').append(button);
}
$('demo-form').addEventListener('submit', submit);
renderTask();
fetch('/health').then((response) => response.ok ? response.json() : null).then(() => {
  $('connection').textContent = 'Demo sẵn sàng';
  $('connection').classList.add('ready');
}).catch(() => { $('connection').textContent = 'Không kết nối được backend'; });
