"""CNN architecture builders for Assignment 05.

The builders return uncompiled Keras models implemented from scratch. They are
small educational variants for controlled comparison, not historical replicas
at original scale.
"""

from __future__ import annotations

import math
from typing import Any

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


def _validate_common_inputs(input_shape: tuple[int, ...], num_classes: int, expected_rank: int) -> None:
    if len(input_shape) != expected_rank:
        raise ValueError(f"Expected input_shape rank {expected_rank}, got {input_shape}")
    if any(dimension <= 0 for dimension in input_shape):
        raise ValueError(f"All input dimensions must be positive, got {input_shape}")
    if num_classes <= 1:
        raise ValueError("num_classes must be greater than 1")


def _classification_head_2d(x: tf.Tensor, num_classes: int, dense_units: int, name: str) -> tf.Tensor:
    x = layers.GlobalAveragePooling2D(name=f"{name}_gap")(x)
    x = layers.Dense(dense_units, activation="relu", name=f"{name}_dense")(x)
    return layers.Dense(num_classes, activation="softmax", name=f"{name}_probabilities")(x)


def _classification_head_1d(x: tf.Tensor, num_classes: int, dense_units: int, name: str) -> tf.Tensor:
    x = layers.GlobalAveragePooling1D(name=f"{name}_gap")(x)
    x = layers.Dense(dense_units, activation="relu", name=f"{name}_dense")(x)
    return layers.Dense(num_classes, activation="softmax", name=f"{name}_probabilities")(x)


def _conv_relu_2d(x: tf.Tensor, filters: int, kernel_size: int, name: str) -> tf.Tensor:
    x = layers.Conv2D(filters, kernel_size, padding="same", activation=None, name=f"{name}_conv")(x)
    return layers.ReLU(name=f"{name}_relu")(x)


def _conv_relu_1d(x: tf.Tensor, filters: int, kernel_size: int, name: str) -> tf.Tensor:
    x = layers.Conv1D(filters, kernel_size, padding="same", activation=None, name=f"{name}_conv")(x)
    return layers.ReLU(name=f"{name}_relu")(x)


def _same_pool_length(length: int, stride: int = 2) -> int:
    return int(math.ceil(length / stride))


def _progression_step(name: str, length: int | None, channels: int) -> dict[str, int | str | None]:
    if length is not None and length <= 0:
        raise ValueError(f"Invalid sequence length after {name}: {length}")
    return {"stage": name, "length": length, "channels": channels}


def _attach_shape_progression(model: keras.Model, progression: list[dict[str, int | str | None]]) -> keras.Model:
    model.shape_progression = progression  # type: ignore[attr-defined]
    return model


def residual_block_2d(x: tf.Tensor, filters: int, *, name: str, stride: int = 1) -> tf.Tensor:
    """Two-convolution residual block with explicit projection when needed."""

    shortcut = x
    x = layers.Conv2D(filters, 3, strides=stride, padding="same", activation=None, name=f"{name}_conv1")(x)
    x = layers.ReLU(name=f"{name}_relu1")(x)
    x = layers.Conv2D(filters, 3, padding="same", activation=None, name=f"{name}_conv2")(x)

    input_channels = int(shortcut.shape[-1])
    if input_channels != filters or stride != 1:
        shortcut = layers.Conv2D(filters, 1, strides=stride, padding="same", activation=None, name=f"{name}_projection")(shortcut)

    x = layers.Add(name=f"{name}_add")([x, shortcut])
    return layers.ReLU(name=f"{name}_relu_out")(x)


def residual_block_1d(x: tf.Tensor, filters: int, *, name: str, stride: int = 1) -> tf.Tensor:
    """1D residual block with explicit 1x1 projection for channel changes."""

    shortcut = x
    x = layers.Conv1D(filters, 3, strides=stride, padding="same", activation=None, name=f"{name}_conv1")(x)
    x = layers.ReLU(name=f"{name}_relu1")(x)
    x = layers.Conv1D(filters, 3, padding="same", activation=None, name=f"{name}_conv2")(x)

    input_channels = int(shortcut.shape[-1])
    if input_channels != filters or stride != 1:
        shortcut = layers.Conv1D(filters, 1, strides=stride, padding="same", activation=None, name=f"{name}_projection")(shortcut)

    x = layers.Add(name=f"{name}_add")([x, shortcut])
    return layers.ReLU(name=f"{name}_relu_out")(x)


def build_basic_cnn_2d(input_shape: tuple[int, int, int], num_classes: int) -> keras.Model:
    """Simple Conv2D baseline with two feature-extraction stages.

    Purpose: establish the smallest image-CNN baseline in the comparison.
    Blocks: Conv-ReLU-Pool, Conv-ReLU-Pool, global pooling, dense classifier.
    Difference: later families add depth, repeated blocks, or residual paths.
    """

    _validate_common_inputs(input_shape, num_classes, expected_rank=3)
    inputs = keras.Input(shape=input_shape, name="image")
    x = _conv_relu_2d(inputs, 32, 3, "basic_block1")
    x = layers.MaxPooling2D(pool_size=2, name="basic_pool1")(x)
    x = _conv_relu_2d(x, 64, 3, "basic_block2")
    x = layers.MaxPooling2D(pool_size=2, name="basic_pool2")(x)
    outputs = _classification_head_2d(x, num_classes, dense_units=64, name="basic_head")
    return keras.Model(inputs, outputs, name="basic_cnn_2d")


def build_alexnet_inspired_2d(input_shape: tuple[int, int, int], num_classes: int) -> keras.Model:
    """Deeper Conv2D model with increased representational capacity.

    Purpose: progress beyond the basic baseline by adding more convolutional
    extraction before the classifier.
    Blocks: wider early convolution, two middle convolutions, three pooling
    points, and a compact dense head.
    Difference: deeper than Basic CNN, but CPU-bounded and not a 227x227
    historical AlexNet replica.
    """

    _validate_common_inputs(input_shape, num_classes, expected_rank=3)
    inputs = keras.Input(shape=input_shape, name="image")
    x = _conv_relu_2d(inputs, 32, 5, "alex_block1")
    x = layers.MaxPooling2D(pool_size=2, name="alex_pool1")(x)
    x = _conv_relu_2d(x, 64, 3, "alex_block2")
    x = layers.MaxPooling2D(pool_size=2, name="alex_pool2")(x)
    x = _conv_relu_2d(x, 128, 3, "alex_block3")
    x = _conv_relu_2d(x, 128, 3, "alex_block4")
    x = layers.MaxPooling2D(pool_size=2, name="alex_pool3")(x)
    outputs = _classification_head_2d(x, num_classes, dense_units=128, name="alex_head")
    return keras.Model(inputs, outputs, name="alexnet_inspired_2d")


def build_vgg_inspired_2d(input_shape: tuple[int, int, int], num_classes: int) -> keras.Model:
    """VGG-inspired Conv2D model using repeated small-kernel blocks.

    Purpose: demonstrate systematic stacking of small 3x3 convolutions.
    Blocks: three repeated-convolution blocks with pooling between blocks.
    Difference: more regular block structure than the AlexNet-inspired model.
    """

    _validate_common_inputs(input_shape, num_classes, expected_rank=3)
    inputs = keras.Input(shape=input_shape, name="image")
    x = inputs
    for block_index, filters in enumerate((32, 64, 128), start=1):
        x = _conv_relu_2d(x, filters, 3, f"vgg_block{block_index}_conv1")
        x = _conv_relu_2d(x, filters, 3, f"vgg_block{block_index}_conv2")
        x = layers.MaxPooling2D(pool_size=2, name=f"vgg_block{block_index}_pool")(x)
    outputs = _classification_head_2d(x, num_classes, dense_units=128, name="vgg_head")
    return keras.Model(inputs, outputs, name="vgg_inspired_2d")


def build_resnet_inspired_2d(input_shape: tuple[int, int, int], num_classes: int) -> keras.Model:
    """ResNet-inspired Conv2D model with explicit residual mappings.

    Purpose: demonstrate y = F(x) + x residual learning for image CNNs.
    Blocks: compact stem, residual blocks, explicit projection shortcuts when
    channel counts change, global pooling classifier.
    Difference: introduces additive shortcut paths absent from prior families.
    """

    _validate_common_inputs(input_shape, num_classes, expected_rank=3)
    inputs = keras.Input(shape=input_shape, name="image")
    x = _conv_relu_2d(inputs, 32, 3, "res2d_stem")
    x = residual_block_2d(x, 32, name="res2d_block1")
    x = layers.MaxPooling2D(pool_size=2, name="res2d_pool1")(x)
    x = residual_block_2d(x, 64, name="res2d_block2")
    x = layers.MaxPooling2D(pool_size=2, name="res2d_pool2")(x)
    x = residual_block_2d(x, 128, name="res2d_block3")
    outputs = _classification_head_2d(x, num_classes, dense_units=128, name="res2d_head")
    return keras.Model(inputs, outputs, name="resnet_inspired_2d")


def build_basic_cnn_1d(input_shape: tuple[int, int], num_classes: int) -> keras.Model:
    """Basic Conv1D adaptation for the 21 diabetes predictor features.

    The feature order is preserved. This is an assignment-driven experiment,
    not a claim that tabular features have natural spatial adjacency.
    """

    _validate_common_inputs(input_shape, num_classes, expected_rank=2)
    length, channels = input_shape
    progression = [_progression_step("input", length, channels)]

    inputs = keras.Input(shape=input_shape, name="tabular_sequence")
    x = _conv_relu_1d(inputs, 16, 3, "basic1d_block1")
    progression.append(_progression_step("conv1_same", length, 16))
    x = layers.MaxPooling1D(pool_size=2, padding="same", name="basic1d_pool1")(x)
    length = _same_pool_length(length)
    progression.append(_progression_step("pool1_same", length, 16))
    x = _conv_relu_1d(x, 32, 3, "basic1d_block2")
    progression.append(_progression_step("conv2_same", length, 32))
    outputs = _classification_head_1d(x, num_classes, dense_units=32, name="basic1d_head")
    progression.append(_progression_step("global_average_pool", None, 32))
    model = keras.Model(inputs, outputs, name="basic_cnn_1d")
    return _attach_shape_progression(model, progression)


def build_alexnet_inspired_1d(input_shape: tuple[int, int], num_classes: int) -> keras.Model:
    """AlexNet-inspired Conv1D adaptation with more feature-extraction capacity.

    The larger first kernel expands the receptive field over the short feature
    sequence, while only two pooling stages are used so length 21 remains valid.
    """

    _validate_common_inputs(input_shape, num_classes, expected_rank=2)
    length, channels = input_shape
    progression = [_progression_step("input", length, channels)]

    inputs = keras.Input(shape=input_shape, name="tabular_sequence")
    x = _conv_relu_1d(inputs, 24, 5, "alex1d_block1")
    progression.append(_progression_step("conv1_same", length, 24))
    x = layers.MaxPooling1D(pool_size=2, padding="same", name="alex1d_pool1")(x)
    length = _same_pool_length(length)
    progression.append(_progression_step("pool1_same", length, 24))
    x = _conv_relu_1d(x, 48, 3, "alex1d_block2")
    progression.append(_progression_step("conv2_same", length, 48))
    x = layers.MaxPooling1D(pool_size=2, padding="same", name="alex1d_pool2")(x)
    length = _same_pool_length(length)
    progression.append(_progression_step("pool2_same", length, 48))
    x = _conv_relu_1d(x, 64, 3, "alex1d_block3")
    progression.append(_progression_step("conv3_same", length, 64))
    x = _conv_relu_1d(x, 64, 3, "alex1d_block4")
    progression.append(_progression_step("conv4_same", length, 64))
    outputs = _classification_head_1d(x, num_classes, dense_units=64, name="alex1d_head")
    progression.append(_progression_step("global_average_pool", None, 64))
    model = keras.Model(inputs, outputs, name="alexnet_inspired_1d")
    return _attach_shape_progression(model, progression)


def build_vgg_inspired_1d(input_shape: tuple[int, int], num_classes: int) -> keras.Model:
    """VGG-inspired Conv1D adaptation with repeated small-kernel blocks.

    Pooling is limited to two stages because the diabetes sequence has only 21
    features. The concept is repeated 3-wide convolutions, not aggressive depth.
    """

    _validate_common_inputs(input_shape, num_classes, expected_rank=2)
    length, channels = input_shape
    progression = [_progression_step("input", length, channels)]

    inputs = keras.Input(shape=input_shape, name="tabular_sequence")
    x = inputs
    for block_index, filters in enumerate((24, 48), start=1):
        x = _conv_relu_1d(x, filters, 3, f"vgg1d_block{block_index}_conv1")
        progression.append(_progression_step(f"block{block_index}_conv1_same", length, filters))
        x = _conv_relu_1d(x, filters, 3, f"vgg1d_block{block_index}_conv2")
        progression.append(_progression_step(f"block{block_index}_conv2_same", length, filters))
        x = layers.MaxPooling1D(pool_size=2, padding="same", name=f"vgg1d_block{block_index}_pool")(x)
        length = _same_pool_length(length)
        progression.append(_progression_step(f"block{block_index}_pool_same", length, filters))
    x = _conv_relu_1d(x, 64, 3, "vgg1d_block3_conv1")
    progression.append(_progression_step("block3_conv1_same", length, 64))
    x = _conv_relu_1d(x, 64, 3, "vgg1d_block3_conv2")
    progression.append(_progression_step("block3_conv2_same", length, 64))
    outputs = _classification_head_1d(x, num_classes, dense_units=64, name="vgg1d_head")
    progression.append(_progression_step("global_average_pool", None, 64))
    model = keras.Model(inputs, outputs, name="vgg_inspired_1d")
    return _attach_shape_progression(model, progression)


def build_resnet_inspired_1d(input_shape: tuple[int, int], num_classes: int) -> keras.Model:
    """ResNet-inspired Conv1D adaptation with explicit residual additions.

    The model preserves y = F(x) + shortcut(x) while using only two pooling
    stages to keep the short 21-feature sequence valid.
    """

    _validate_common_inputs(input_shape, num_classes, expected_rank=2)
    length, channels = input_shape
    progression = [_progression_step("input", length, channels)]

    inputs = keras.Input(shape=input_shape, name="tabular_sequence")
    x = _conv_relu_1d(inputs, 24, 3, "res1d_stem")
    progression.append(_progression_step("stem_conv_same", length, 24))
    x = residual_block_1d(x, 24, name="res1d_block1")
    progression.append(_progression_step("residual_block1", length, 24))
    x = layers.MaxPooling1D(pool_size=2, padding="same", name="res1d_pool1")(x)
    length = _same_pool_length(length)
    progression.append(_progression_step("pool1_same", length, 24))
    x = residual_block_1d(x, 48, name="res1d_block2")
    progression.append(_progression_step("residual_block2_projection", length, 48))
    x = layers.MaxPooling1D(pool_size=2, padding="same", name="res1d_pool2")(x)
    length = _same_pool_length(length)
    progression.append(_progression_step("pool2_same", length, 48))
    x = residual_block_1d(x, 64, name="res1d_block3")
    progression.append(_progression_step("residual_block3_projection", length, 64))
    outputs = _classification_head_1d(x, num_classes, dense_units=64, name="res1d_head")
    progression.append(_progression_step("global_average_pool", None, 64))
    model = keras.Model(inputs, outputs, name="resnet_inspired_1d")
    return _attach_shape_progression(model, progression)


IMAGE_2D_BUILDERS: dict[str, Any] = {
    "Basic CNN": build_basic_cnn_2d,
    "AlexNet-inspired CNN": build_alexnet_inspired_2d,
    "VGG-inspired CNN": build_vgg_inspired_2d,
    "ResNet-inspired CNN": build_resnet_inspired_2d,
}

TABULAR_1D_BUILDERS: dict[str, Any] = {
    "Basic CNN": build_basic_cnn_1d,
    "AlexNet-inspired CNN": build_alexnet_inspired_1d,
    "VGG-inspired CNN": build_vgg_inspired_1d,
    "ResNet-inspired CNN": build_resnet_inspired_1d,
}
