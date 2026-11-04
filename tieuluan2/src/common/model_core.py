"""One architecture plan supplies all backends, contracts and explanations.

Canonical activations: NHWC images, NTF sequences, dense IO, conv HWIO,
recurrent (input, gates*hidden)/(hidden, gates*hidden), LSTM i/f/g/o.
"""

from __future__ import annotations

import copy

import numpy as np

from src.common.contracts import PROTOCOL, canonical_sha256, read_json, validate_document

BACKENDS = {"scratch": "numpy", "keras": "tensorflow", "pytorch": "torch"}
LEARNED = {"dense", "conv2d", "rnn", "lstm"}


def build_plan(family, input_shape, outputs, *, tiny=False):
    protocol = read_json(PROTOCOL)
    if (
        family not in protocol["families"]
        or not input_shape
        or outputs < 1
        or any(not isinstance(v, int) or v < 1 for v in input_shape)
    ):
        raise ValueError("Invalid family/input/output dimensions")
    if len(input_shape) != {"mlp": 1, "cnn": 3, "rnn": 2, "lstm": 2}[family]:
        raise ValueError("Input rank mismatch")
    shape = list(input_shape)
    steps = []

    def add(kind, output, **options):
        nonlocal shape
        step = {
            "id": f"{kind}_{len(steps) + 1}",
            "kind": kind,
            "input_shape": shape,
            "output_shape": list(output),
            **options,
        }
        steps.append(step)
        shape = list(output)

    policy = protocol["families"][family]
    if family == "mlp":
        for units in [2] * 5 if tiny else policy["hidden_units"]:
            add("dense", [units])
            add("activation", shape, activation="relu")
    elif family == "cnn":
        for i, channels in enumerate([2] * 5 if tiny else policy["channels"]):
            add("conv2d", [*shape[:2], channels], kernel_size=3, padding="same")
            add("activation", shape, activation="relu")
            if i in policy["pool_after_convolutions"]:
                if min(shape[:2]) < 2:
                    raise ValueError("Image too small for two pooling stages")
                add("pooling", [shape[0] // 2, shape[1] // 2, shape[2]], pool="max2")
        add("pooling", [shape[-1]], pool="global_average")
        add("dense", [2 if tiny else policy["dense_hidden"]])
        add("activation", shape, activation="relu")
    else:
        for i, units in enumerate([2] * 3 if tiny else policy["hidden_units"]):
            add(family, [shape[0], units] if i < 2 else [units], return_sequences=i < 2)
        for units in [2, 2] if tiny else policy["dense_hidden"]:
            add("dense", [units])
            add("activation", shape, activation="relu")
    add("dense", [outputs])
    return {
        "plan_version": "phase25.1",
        "family": family,
        "input_shape": list(input_shape),
        "output_shape": shape,
        "steps": steps,
        "tiny_synthetic_only": tiny,
    }


def parameter_shapes(step):
    kind = step["kind"]
    width = step["input_shape"][-1]
    units = step["output_shape"][-1]
    if kind == "dense":
        return {"w": (width, units), "b": (units,)}
    if kind == "conv2d":
        return {"w": (step["kernel_size"], step["kernel_size"], width, units), "b": (units,)}
    if kind in {"rnn", "lstm"}:
        gates = 4 if kind == "lstm" else 1
        return {"w": (width, gates * units), "u": (units, gates * units), "b": (gates * units,)}
    return {}


def canonical_weights(plan, seed, dtype="float32"):
    rng = np.random.default_rng(seed)
    result = {}
    for step in plan["steps"]:
        for name, shape in parameter_shapes(step).items():
            value = (
                np.zeros(shape, dtype=dtype)
                if name == "b"
                else rng.normal(0, np.sqrt(1 / np.prod(shape[:-1])), shape).astype(dtype)
            )
            if step["kind"] == "lstm" and name == "b":
                units = step["output_shape"][-1]
                value[units : 2 * units] = 1
            result[f"{step['id']}/{name}"] = value
    return result


def formula_for(step):
    kind = step["kind"]
    expressions = {
        "dense": "y = xW + b",
        "conv2d": "y = conv_same(x, W) + b",
        "rnn": "h_t = tanh(x_t W + h_previous U + b)",
        "lstm": "(i,f,g,o) = (sigmoid,sigmoid,tanh,sigmoid)(x_t W + h_previous U + b); c_t = f*c_previous + i*g; h_t = o*tanh(c_t)",
    }
    if kind not in expressions:
        return None
    meanings = {
        "x": "tensor đầu vào (x_t: tại bước t)",
        "y": "tensor đầu ra",
        "W": "trọng số đầu vào",
        "b": "bias học được",
    }
    if kind in {"rnn", "lstm"}:
        meanings.update(
            {
                "h_t": "trạng thái ở bước t",
                "h_previous": "trạng thái bước trước, bắt đầu bằng 0",
                "U": "trọng số trạng thái",
                "t": "chỉ số bước thời gian",
            }
        )
    if kind == "rnn":
        meanings["tanh"] = "hàm ép giá trị vào khoảng -1 đến 1"
    if kind == "conv2d":
        meanings["conv_same"] = "trượt bộ lọc 3×3, đệm 0 để giữ kích thước ảnh"
    if kind == "lstm":
        meanings.update(
            {
                "i,f,o": "cổng nhận, quên, xuất trong 0..1",
                "g": "ứng viên bộ nhớ",
                "c_t": "bộ nhớ mới",
                "c_previous": "bộ nhớ bước trước, bắt đầu bằng 0",
                "sigmoid": "hàm ép vào khoảng 0 đến 1",
                "tanh": "hàm ép vào khoảng -1 đến 1",
                "*": "nhân từng phần tử",
            }
        )
    return {
        "expression": expressions[kind],
        "symbols": [{"symbol": k, "meaning": v} for k, v in meanings.items()],
        "why_needed": "Đối chiếu phép tính forward trong code scratch.",
        "plain_explanation": {
            "dense": "Kết hợp các giá trị đầu vào bằng trọng số rồi cộng bias.",
            "conv2d": "Tìm đặc trưng cục bộ bằng bộ lọc trượt trên ảnh.",
            "rnn": "Kết hợp dữ liệu hiện tại và thông tin nhớ từ bước trước.",
            "lstm": "Chọn thông tin cần giữ, bổ sung và xuất qua các cổng.",
        }[kind],
        "example": f"Shape {step['input_shape']} → {step['output_shape']} cho một mẫu; batch được giữ nguyên.",
    }


def make_contract(plan, implementation, evidence_kind, provenance=None):
    if implementation not in BACKENDS:
        raise ValueError("Unknown implementation")
    if evidence_kind != "synthetic_fixture" and provenance is None:
        raise ValueError("Measured contracts require provenance")
    if plan["tiny_synthetic_only"] and evidence_kind != "synthetic_fixture":
        raise ValueError("Tiny plan is not a production model")
    family = plan["family"]
    dataset = {
        "mlp": "ch2_cdc_diabetes",
        "cnn": "ch3_cifar10",
        "rnn": "ch4_gold_pink_sheet",
        "lstm": "ch4_gold_pink_sheet",
    }[family]
    digest = canonical_sha256(plan)
    provenance = provenance or {
        "dataset_id": dataset,
        "config_sha256": digest,
        "dataset_sha256": digest,
        "comparison_group_sha256": digest,
        "preprocessing": {
            "path": "artifacts/manifests/phase25/synthetic_preprocessing.json",
            "sha256": digest,
        },
    }
    layers = []
    functions = []
    keras_names = {
        "dense": "Dense",
        "conv2d": "Conv2D",
        "rnn": "SimpleRNN",
        "lstm": "LSTM",
        "activation": "ReLU",
        "pooling": "MaxPooling2D/GlobalAveragePooling2D",
    }
    torch_names = {
        "dense": "Linear",
        "conv2d": "Conv2d",
        "rnn": "RNN",
        "lstm": "LSTM",
        "activation": "ReLU",
        "pooling": "MaxPool2d/AdaptiveAvgPool2d",
    }
    roles = {
        "dense": "Kết hợp các đặc trưng",
        "conv2d": "Tìm đặc trưng trong vùng ảnh",
        "rnn": "Nhớ thông tin theo thời gian",
        "lstm": "Giữ/quên thông tin bằng bộ nhớ và cổng",
        "activation": "Giữ tín hiệu dương, tạo khả năng học phi tuyến",
        "pooling": "Rút gọn vùng ảnh",
    }
    for step in plan["steps"]:
        count = int(sum(np.prod(shape) for shape in parameter_shapes(step).values()))
        inp = ["batch", *step["input_shape"]]
        out = ["batch", *step["output_shape"]]
        layers.append(
            {
                "id": step["id"],
                "kind": step["kind"],
                "parameter_count": count,
                "input_shape": inp,
                "output_shape": out,
                "function_id": step["id"],
            }
        )
        functions.append(
            {
                "id": step["id"],
                "signature": f"{step['kind']}(x, weights) -> y",
                "role": roles[step["kind"]],
                "input_shape": inp,
                "output_shape": out,
                "parameters": count,
                "corner_case": "Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.",
                "formula": formula_for(step),
                "mapping": {
                    "scratch": f"src.common.numpy_engine.NumpyNetwork.forward[{step['kind']}]",
                    "keras": f"keras.layers.{keras_names[step['kind']]}",
                    "pytorch": f"torch.nn.{torch_names[step['kind']]}",
                },
            }
        )
    contract = {
        "schema_version": "3.0.0",
        "evidence_kind": evidence_kind,
        "model_id": f"{provenance['dataset_id']}_{family}_{implementation}",
        "dataset_id": provenance["dataset_id"],
        "family": family,
        "implementation": implementation,
        "backend": BACKENDS[implementation],
        "parameter_count": sum(x["parameter_count"] for x in layers),
        "input_shape": ["batch", *plan["input_shape"]],
        "output_shape": ["batch", *plan["output_shape"]],
        "layers": layers,
        "functions": functions,
        "composition": [x["id"] for x in functions],
        "composition_plain": "đầu vào → "
        + " → ".join(f"{roles[x['kind']]} {x['output_shape']}" for x in plan["steps"])
        + " → đầu ra (logit/giá trị chuẩn hóa)",
        "recurrent_unroll": "Ở mỗi tầng l=1..3, lặp t=1..T theo thứ tự; khởi tạo h (và c) bằng 0 cho mỗi window. Tầng 1–2 trả toàn chuỗi, tầng 3 trả bước cuối → 3 Dense."
        if family in {"rnn", "lstm"}
        else None,
        **{
            key: provenance[key]
            for key in ("config_sha256", "dataset_sha256", "comparison_group_sha256", "preprocessing")
        },
    }
    validate_model(contract)
    return contract


def validate_model(contract):
    validate_document("model", contract)
    functions = {row["id"]: row for row in contract["functions"]}
    if contract["composition"] != [row["function_id"] for row in contract["layers"]]:
        raise ValueError("Composition order differs from execution")
    previous = contract["input_shape"]
    for layer in contract["layers"]:
        function = functions[layer["function_id"]]
        if (
            layer["input_shape"] != previous
            or any(function[k] != layer[k] for k in ("input_shape", "output_shape"))
            or function["parameters"] != layer["parameter_count"]
        ):
            raise ValueError("Shape/function/parameter trace mismatch")
        kind = layer["kind"]
        width = layer["input_shape"][-1]
        units = layer["output_shape"][-1]
        expected = 0
        if kind == "dense":
            expected = (width + 1) * units
        elif kind == "conv2d":
            expected = (9 * width + 1) * units
        elif kind in {"rnn", "lstm"}:
            expected = (width + units + 1) * units * (4 if kind == "lstm" else 1)
        if layer["parameter_count"] != expected:
            raise ValueError("Parameter count does not match tensor dimensions")
        previous = layer["output_shape"]
    if previous != contract["output_shape"]:
        raise ValueError("Final output shape mismatch")


def render_functions(contract):
    validate_model(contract)
    functions = copy.deepcopy(contract["functions"])
    technical = "F = " + " ∘ ".join(reversed(contract["composition"]))
    table = "| Hàm | Vai trò | Input → Output | Tham số |\n|---|---|---|---:|\n"
    table += "".join(
        f"| {f['id']} | {f['role']} | {f['input_shape']} → {f['output_shape']} | {f['parameters']} |\n"
        for f in functions
    )
    markdown = f"# {contract['model_id']}\n\n{contract['composition_plain']}\n\n`{technical}`\n\n{contract['recurrent_unroll'] or ''}\n\n{table}"
    for function in functions:
        markdown += f"\n## {function['id']}\n\n`{function['signature']}` — {function['role']}.\n\n{function['corner_case']}\n\nMapping: {function['mapping']}\n"
        formula = function["formula"]
        if formula:
            markdown += (
                f"\n{formula['plain_explanation']}\n\n`{formula['expression']}`\n\n"
                + "; ".join(f"{s['symbol']}: {s['meaning']}" for s in formula["symbols"])
                + f".\n\n{formula['example']}\n"
            )
    return {
        "technical": technical,
        "plain": contract["composition_plain"],
        "functions": functions,
        "markdown": markdown,
    }


class ModelRegistry:
    def __init__(self):
        self._models = {}

    def register(self, contract):
        validate_model(contract)
        if contract["model_id"] in self._models:
            raise ValueError("Duplicate model ID")
        self._models[contract["model_id"]] = copy.deepcopy(contract)

    def get(self, model_id):
        return copy.deepcopy(self._models[model_id])
