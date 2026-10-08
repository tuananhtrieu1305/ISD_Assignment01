const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const diabetesFields = [
  ["HighBP",0,1],["HighChol",0,1],["CholCheck",0,1],["BMI",10,100],
  ["Smoker",0,1],["Stroke",0,1],["HeartDiseaseorAttack",0,1],["PhysActivity",0,1],
  ["Fruits",0,1],["Veggies",0,1],["HvyAlcoholConsump",0,1],["AnyHealthcare",0,1],
  ["NoDocbcCost",0,1],["GenHlth",1,5],["MentHlth",0,30],["PhysHlth",0,30],
  ["DiffWalk",0,1],["Sex",0,1],["Age",1,13],["Education",1,6],["Income",1,8]
];
let currentMode = "customer";
let imageBase64 = "";

function toast(message) {
  const node = $("#toast"); node.textContent = message; node.classList.add("show");
  window.setTimeout(() => node.classList.remove("show"), 3500);
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data?.error?.message || "Không thể xử lý yêu cầu.");
  return data;
}

function setBusy(node, busy) { node.classList.toggle("loading", busy); }
function pct(number) { return `${(number * 100).toFixed(1)}%`; }
function provenanceLine(data) { return `<p class="minor">${data.version} · SHA ${data.model_sha256.slice(0,12)}…</p>`; }

function switchTab(name) {
  $$(".tab").forEach(button => {
    const selected = button.dataset.tab === name;
    button.classList.toggle("active", selected); button.setAttribute("aria-selected", String(selected));
  });
  $$(".panel").forEach(panel => { const selected = panel.id === `panel-${name}`; panel.hidden = !selected; panel.classList.toggle("active", selected); });
}

function buildDiabetesForm() {
  $("#diabetes-fields").innerHTML = diabetesFields.map(([name,min,max]) =>
    `<div class="field"><label for="f-${name}">${name}</label><input id="f-${name}" name="${name}" type="number" min="${min}" max="${max}" step="1" required></div>`
  ).join("");
}

async function loadDemo(name) {
  const data = await api(`/api/demo/${name}`);
  if (name === "diabetes") {
    Object.entries(data.input).forEach(([key,value]) => { const input = $(`#f-${key}`); if (input) input.value = value; });
  } else if (name === "eurosat") {
    imageBase64 = data.input.image_base64; const preview = $("#image-preview");
    preview.src = `data:image/jpeg;base64,${imageBase64}`; preview.hidden = false;
    $$("#drop-zone > :not(input):not(img)").forEach(node => node.hidden = true);
  } else {
    $("#sequence-input").value = data.input.sequence.map(row => row.join(", ")).join("\n");
  }
  toast(`Đã nạp mẫu ${data.sample_key || name}.`); return data;
}

function renderDiabetes(result) {
  $("#diabetes-result").innerHTML = `<p class="result-label">XÁC SUẤT NGUY CƠ / MLP NUMPY</p>
    <div class="metric-big">${pct(result.probability)}</div><progress max="1" value="${result.probability}"></progress>
    <p class="minor">Ngưỡng quyết định: ${pct(result.threshold)}</p><p class="verdict">${result.label}</p>
    ${provenanceLine(result.provenance)}<p class="warning">${result.warning}</p>`;
}

function renderCnn(result) {
  $("#cnn-result").innerHTML = `<p class="result-label">TOP-3 / CNN NUMPY</p><p class="verdict">${result.predicted_class}</p>
    ${result.top_classes.map((item,index) => `<div class="rank-row"><div class="rank-head"><b>${String(index+1).padStart(2,"0")} · ${item.class_name}</b><span>${pct(item.confidence)}</span></div><progress max="1" value="${item.confidence}"></progress></div>`).join("")}
    ${provenanceLine(result.provenance)}<p class="warning">${result.warning}</p>`;
}

function parseSequence() {
  const text = $("#sequence-input").value.trim();
  if (!text) throw new Error("Hãy nhập hoặc nạp một chuỗi CSV.");
  return text.split(/\r?\n/).filter(Boolean).map((line,row) => {
    const values = line.split(",").map(value => Number(value.trim()));
    if (values.length !== 5 || values.some(value => !Number.isFinite(value))) throw new Error(`Hàng ${row+1} phải có đúng 5 số.`);
    return values;
  });
}

function renderRnn(result) {
  if (currentMode === "aapl") {
    $("#rnn-result").innerHTML = `<p class="result-label">RNN SO VỚI BASELINE</p><div class="comparison"><div><span>RNN dự đoán</span><b>$${result.rnn_prediction_usd.toFixed(2)}</b></div><div><span>Naive last-Close</span><b>$${result.naive_last_close_usd.toFixed(2)}</b></div></div><p class="verdict">Chênh lệch ${result.delta_rnn_vs_naive_usd >= 0 ? "+" : ""}${result.delta_rnn_vs_naive_usd.toFixed(2)} USD</p>${provenanceLine(result.provenance)}<p class="warning">${result.warning}</p>`;
  } else {
    $("#rnn-result").innerHTML = `<p class="result-label">XÁC SUẤT / RNN NUMPY</p><div class="metric-big">${pct(result.probability)}</div><progress max="1" value="${result.probability}"></progress><p class="minor">Ngưỡng quyết định: ${pct(result.threshold)}</p><p class="verdict">${result.label}</p>${provenanceLine(result.provenance)}<p class="warning">${result.warning}</p>`;
  }
}

async function boot() {
  buildDiabetesForm();
  $$(".tab").forEach(button => button.addEventListener("click", () => switchTab(button.dataset.tab)));
  $$('[data-demo]').forEach(button => button.addEventListener("click", () => loadDemo(button.dataset.demo).catch(error => toast(error.message))));
  $$(".mode").forEach(button => button.addEventListener("click", () => {
    currentMode = button.dataset.mode; $$(".mode").forEach(item => item.classList.toggle("active", item === button));
    $("#sequence-title").textContent = currentMode === "aapl" ? "Chuỗi AAPL" : "Chuỗi khách hàng"; $("#sequence-input").value = "";
  }));
  $("#sequence-demo").addEventListener("click", () => loadDemo(currentMode).catch(error => toast(error.message)));
  $("#diabetes-form").addEventListener("submit", async event => {
    event.preventDefault(); const form = event.currentTarget; setBusy(form,true);
    try { const payload = Object.fromEntries(diabetesFields.map(([name]) => [name,Number(form.elements[name].value)])); renderDiabetes(await api("/api/predict/diabetes",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)})); }
    catch(error){toast(error.message);} finally {setBusy(form,false);}
  });
  $("#image-input").addEventListener("change", event => {
    const file=event.target.files[0]; if(!file)return; if(file.size>5*1024*1024){toast("Ảnh vượt quá giới hạn 5 MB.");return;}
    const reader=new FileReader(); reader.onload=()=>{imageBase64=reader.result.split(",")[1]; const preview=$("#image-preview");preview.src=reader.result;preview.hidden=false; $$("#drop-zone > :not(input):not(img)").forEach(node=>node.hidden=true);}; reader.readAsDataURL(file);
  });
  $("#cnn-submit").addEventListener("click", async () => { if(!imageBase64){toast("Hãy chọn hoặc nạp ảnh mẫu.");return;} const card=$("#panel-cnn .control-card");setBusy(card,true);try{renderCnn(await api("/api/predict/eurosat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({image_base64:imageBase64})}));}catch(error){toast(error.message);}finally{setBusy(card,false);}});
  $("#csv-input").addEventListener("change", event => {const file=event.target.files[0];if(!file)return;const reader=new FileReader();reader.onload=()=>{$("#sequence-input").value=reader.result;};reader.readAsText(file);});
  $("#rnn-submit").addEventListener("click", async () => {const card=$("#panel-rnn .control-card");setBusy(card,true);try{renderRnn(await api(`/api/predict/${currentMode}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sequence:parseSequence()})}));}catch(error){toast(error.message);}finally{setBusy(card,false);}});
  try {
    const [health, registry] = await Promise.all([api("/health"), api("/api/models")]);
    $("#health").classList.add("ready"); $("#health span:last-child").textContent = `${Object.keys(health.models).length} mô hình sẵn sàng`;
    $("#model-registry").innerHTML = Object.entries(registry.models).map(([id,item]) => `<div class="registry-row"><b>${id}</b><code title="${item.model_sha256}">${item.version} · ${item.model_sha256.slice(0,12)}…</code><span class="badge">✓ VERIFIED</span></div>`).join("");
  } catch(error) { toast(`Health check lỗi: ${error.message}`); }
  const params = new URLSearchParams(location.search); const tab=params.get("tab"), demo=params.get("demo");
  if(tab) switchTab(tab); if(demo){ if(demo==="aapl"){currentMode="aapl";$(".mode[data-mode='aapl']").click();} await loadDemo(demo); await new Promise(resolve=>setTimeout(resolve,100)); if(demo==="diabetes")$("#diabetes-form").requestSubmit(); if(demo==="eurosat")$("#cnn-submit").click(); if(["customer","aapl"].includes(demo))$("#rnn-submit").click(); }
}
document.addEventListener("DOMContentLoaded", () => boot().catch(error => toast(error.message)));
