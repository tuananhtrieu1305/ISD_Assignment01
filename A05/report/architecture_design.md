# Architecture Design

This document summarizes the CNN architecture families implemented in `models/architectures.py`. All models are implemented from scratch with Keras layers. No pretrained weights, transfer learning, or `keras.applications` architectures are used.

The image variants use Conv2D layers for RGB image data. The diabetes variants use Conv1D layers as assignment-driven experimental adaptations for the 21 predictor features. For the tabular case, the original feature order is preserved, but this order is not a natural spatial structure like neighboring image pixels.

## Design Comparison

Representative parameter counts were measured with:

- image input: `(64, 64, 3)`, `num_classes=10`
- tabular input: `(21, 1)`, `num_classes=3`

| Variant | Model family | Main architectural idea | Input assumptions | Convolution depth | Pooling strategy | Residual connection | Representative parameters | Major CPU-related design constraint |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| Conv2D | Basic CNN | Simple convolutional baseline | RGB image tensor with 3 channels | 2 Conv2D layers | Two 2x2 max-pooling stages, then global average pooling | No | 24,202 | Uses global average pooling instead of a large Flatten-Dense head |
| Conv2D | AlexNet-inspired CNN | Deeper feature extraction and increased representational capacity | RGB image tensor with 3 channels | 4 Conv2D layers | Three 2x2 max-pooling stages, then global average pooling | No | 260,170 | Uses modest filters and compact dense head instead of original-scale AlexNet dense layers |
| Conv2D | VGG-inspired CNN | Systematic repeated small-kernel convolution blocks | RGB image tensor with 3 channels | 6 Conv2D layers | Pool after each repeated-convolution block, then global average pooling | No | 304,810 | Limits the number of repeated blocks for CPU execution |
| Conv2D | ResNet-inspired CNN | Residual learning using `y = F(x) + x` | RGB image tensor with 3 channels | Stem Conv2D plus 3 residual blocks | Two 2x2 max-pooling stages, then global average pooling | Yes | 324,490 | Uses compact residual blocks and projection shortcuts only when channel dimensions differ |
| Conv1D | Basic CNN | Simple tabular convolution baseline | 21-feature sequence with 1 channel | 2 Conv1D layers | One same-padded max-pooling stage, then global average pooling | No | 2,787 | Minimal depth because the sequence has only 21 positions |
| Conv1D | AlexNet-inspired CNN | More representational capacity over the short feature sequence | 21-feature sequence with 1 channel | 4 Conv1D layers | Two same-padded max-pooling stages, then global average pooling | No | 29,635 | Uses only two pooling stages so sequence length remains valid |
| Conv1D | VGG-inspired CNN | Repeated small-kernel Conv1D blocks | 21-feature sequence with 1 channel | 6 Conv1D layers | Two same-padded pooling stages, then global average pooling | No | 38,299 | Preserves the repeated-kernel idea without excessive pooling depth |
| Conv1D | ResNet-inspired CNN | Residual learning using `y = F(x) + shortcut(x)` | 21-feature sequence with 1 channel | Stem Conv1D plus 3 residual blocks | Two same-padded pooling stages, then global average pooling | Yes | 44,387 | Uses projection shortcuts for channel changes and avoids length collapse |

## Parameter-Choice Rationale

- Input channels and output classes are data-determined.
- Residual projection shortcuts are architecture-determined because tensors must have compatible channel dimensions before addition.
- Repeated small kernels in the VGG-inspired models are architecture-determined by the conceptual VGG progression.
- The smaller filter counts and compact dense heads are operational bounds for CPU-only execution; they are not claims of optimality.
- Learning rate, batch size, dropout, and optimizer are intentionally not selected in this task.

## Conv1D Shape Progression

The Conv1D diabetes adaptations preserve length with `padding="same"` in convolution layers and use only limited same-padded pooling. No sequence length becomes zero or invalid.

| Model | Shape progression |
| --- | --- |
| Basic CNN 1D | input `21x1` -> conv `21x16` -> pool `11x16` -> conv `11x32` -> global average pooling |
| AlexNet-inspired CNN 1D | input `21x1` -> conv `21x24` -> pool `11x24` -> conv `11x48` -> pool `6x48` -> conv `6x64` -> conv `6x64` -> global average pooling |
| VGG-inspired CNN 1D | input `21x1` -> conv `21x24` -> conv `21x24` -> pool `11x24` -> conv `11x48` -> conv `11x48` -> pool `6x48` -> conv `6x64` -> conv `6x64` -> global average pooling |
| ResNet-inspired CNN 1D | input `21x1` -> stem `21x24` -> residual `21x24` -> pool `11x24` -> residual projection `11x48` -> pool `6x48` -> residual projection `6x64` -> global average pooling |

## Residual Connections

The ResNet-inspired variants implement residual blocks explicitly:

```text
y = F(x) + shortcut(x)
```

When channel dimensions differ, the shortcut path uses a 1x1 convolution projection. This avoids accidental broadcasting and makes the tensor addition structurally valid.

## Tabular CNN Limitation

The CDC diabetes predictors are tabular features, not pixels. Adjacent feature positions do not automatically carry the same kind of local spatial meaning as adjacent image pixels. The Conv1D models are therefore experimental adaptations required for the assignment, not a claim that CNNs are naturally optimal for this dataset.

No architecture is declared superior here. Model quality must be evaluated later using validation-driven hyperparameter selection and final isolated test evaluation.
