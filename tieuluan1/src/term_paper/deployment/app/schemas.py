"""Strict, allow-list input validation for deployment endpoints."""

import base64
import binascii
import io
import math
import warnings

import numpy as np
from PIL import Image, UnidentifiedImageError


MAX_IMAGE_BYTES = 5 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 20_000_000

DIABETES_FEATURES = [
    "HighBP", "HighChol", "CholCheck", "BMI", "Smoker", "Stroke",
    "HeartDiseaseorAttack", "PhysActivity", "Fruits", "Veggies",
    "HvyAlcoholConsump", "AnyHealthcare", "NoDocbcCost", "GenHlth",
    "MentHlth", "PhysHlth", "DiffWalk", "Sex", "Age", "Education", "Income",
]
BINARY_FEATURES = {
    "HighBP", "HighChol", "CholCheck", "Smoker", "Stroke",
    "HeartDiseaseorAttack", "PhysActivity", "Fruits", "Veggies",
    "HvyAlcoholConsump", "AnyHealthcare", "NoDocbcCost", "DiffWalk", "Sex",
}
DIABETES_RANGES = {
    "BMI": (10, 100), "GenHlth": (1, 5), "MentHlth": (0, 30),
    "PhysHlth": (0, 30), "Age": (1, 13), "Education": (1, 6), "Income": (1, 8),
}


class ValidationError(ValueError):
    """A safe validation error whose message may be returned to the user."""


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
        raise ValidationError(f"{label} phải là một số.")
    number = float(value)
    if not math.isfinite(number):
        raise ValidationError(f"{label} phải là số hữu hạn.")
    return number


def validate_diabetes(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Dữ liệu diabetes phải là một JSON object.")
    expected, received = set(DIABETES_FEATURES), set(payload)
    missing, extra = sorted(expected - received), sorted(received - expected)
    if missing:
        raise ValidationError(f"Thiếu trường bắt buộc: {', '.join(missing)}.")
    if extra:
        raise ValidationError(f"Trường không được hỗ trợ: {', '.join(extra)}.")
    result = {}
    for name in DIABETES_FEATURES:
        value = _finite_number(payload[name], name)
        if name in BINARY_FEATURES and value not in {0.0, 1.0}:
            raise ValidationError(f"{name} chỉ nhận 0 hoặc 1.")
        if name in DIABETES_RANGES:
            lower, upper = DIABETES_RANGES[name]
            if value < lower or value > upper:
                raise ValidationError(f"{name} phải nằm trong [{lower}, {upper}].")
        result[name] = value
    return result


def validate_sequence(sequence, kind):
    if kind not in {"customer", "aapl"}:
        raise ValidationError("Loại sequence không được hỗ trợ.")
    expected_rows = 8 if kind == "customer" else 30
    if not isinstance(sequence, list) or len(sequence) != expected_rows:
        raise ValidationError(f"Sequence {kind} phải có đúng {expected_rows} hàng.")
    rows = []
    for row_index, row in enumerate(sequence):
        if not isinstance(row, list) or len(row) != 5:
            raise ValidationError(f"Hàng {row_index + 1} phải có đúng 5 giá trị.")
        rows.append([_finite_number(value, f"hàng {row_index + 1}, cột {column + 1}")
                     for column, value in enumerate(row)])
    array = np.asarray(rows, dtype=np.float32)
    if kind == "customer":
        if np.any(array[:, :4] < 0) or np.any(array[:, :4] > 1e9):
            raise ValidationError("Feature giao dịch phải nằm trong [0, 1e9].")
        if not np.isin(array[:, 4], [0.0, 1.0]).all():
            raise ValidationError("active_flag chỉ nhận 0 hoặc 1.")
    else:
        if np.any(array[:, :4] <= 0) or np.any(array[:, 4] < 0):
            raise ValidationError("OHLC phải dương và Volume không được âm.")
        open_price, high, low, close = (array[:, index] for index in range(4))
        if np.any(high < np.maximum(open_price, close)) or np.any(low > np.minimum(open_price, close)):
            raise ValidationError("Mỗi hàng phải thỏa Low ≤ Open/Close ≤ High.")
    return array


def validate_image_base64(encoded):
    if not isinstance(encoded, str) or not encoded:
        raise ValidationError("Ảnh phải được gửi dưới dạng base64.")
    if encoded.startswith("data:"):
        try:
            encoded = encoded.split(",", 1)[1]
        except IndexError as error:
            raise ValidationError("Data URI ảnh không hợp lệ.") from error
    if len(encoded) > (MAX_IMAGE_BYTES * 4 // 3) + 16:
        raise ValidationError("Ảnh vượt quá giới hạn 5 MB.")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValidationError("Chuỗi base64 không hợp lệ.") from error
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise ValidationError("Ảnh rỗng hoặc vượt quá giới hạn 5 MB.")
    try:
        with warnings.catch_warnings():
            # We enforce the same pixel ceiling explicitly and return a safe
            # validation error instead of emitting a process-level warning.
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as probe:
                if probe.format not in {"PNG", "JPEG"}:
                    raise ValidationError("Chỉ chấp nhận ảnh PNG hoặc JPEG.")
                if probe.width * probe.height > Image.MAX_IMAGE_PIXELS:
                    raise ValidationError("Ảnh vượt quá giới hạn 20 triệu pixel.")
                probe.verify()
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            return image.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValidationError("Nội dung upload không phải ảnh PNG/JPEG hợp lệ.") from error
