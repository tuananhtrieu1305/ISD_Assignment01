# Experiment Protocol

This protocol applies to all Assignment 05 experiments. The raw datasets stay unchanged, and all generated artifacts must be written under `results/`, `report/`, or `models/`.

## 1. Train, Validation, and Test Responsibilities

Training data is used to fit model weights and any fitted preprocessing objects. Validation data is used to choose model and hyperparameter settings. Test data is held aside until final evaluation of a selected configuration.

For Oxford-IIIT Pet, the official `annotations/trainval.txt` split may be subdivided into training and validation records. The official `annotations/test.txt` split remains isolated for final evaluation.

## 2. Why Test Cannot Tune Hyperparameters

Using test performance to choose learning rate, architecture details, regularization, image size, batch size, epoch count, or preprocessing choices leaks final-evaluation information into model selection. That makes the test metric an optimistic selection metric rather than an estimate of generalization. Test results are reported only after validation-driven choices are fixed.

## 3. Reproducibility Rules

Use seed `42` unless a concrete reason is documented. Seed Python `random`, NumPy, and TensorFlow/Keras when TensorFlow is present. Request deterministic TensorFlow behavior where reasonably possible, while documenting that some hardware kernels and library versions may still introduce nondeterminism.

All paths must resolve relative to the A05 project root. Code must not depend on the notebook current working directory and must not use machine-specific absolute paths.

## 4. Fair CNN Architecture Comparison

The four model families are Basic CNN, AlexNet-inspired CNN, VGG-inspired CNN, and ResNet-inspired CNN. They must be implemented from scratch with no pretrained weights and no transfer learning.

Comparisons should use the same dataset split, preprocessing policy, metric definitions, stopping rules, and final test protocol. Differences should be limited to the architecture family and explicitly selected hyperparameters.

## 5. Hyperparameter-Selection Rules

Every meaningful parameter decision must be classified as data-determined, architecture-determined, experimentally selected, or operational bound.

If a parameter cannot be justified mathematically from the data or architecture, select it using validation-set evidence. Learning rate, regularization strength, batch size, and similar optimization choices must not be justified by popularity, habit, or intuition.

## 6. Image Decoding Strategy

Image loaders must decode image content rather than infer format from the filename extension. Oxford-IIIT Pet includes valid PNG images with `.jpg` filenames, so JPEG-only decoding based on suffix is unsafe.

The training pipeline should open images with a format-aware decoder such as Pillow `Image.open(...)` or TensorFlow `tf.io.decode_image`, convert the decoded image to RGB/3 channels in memory, resize to the selected input shape, and leave the raw source file unchanged.

## 7. Oxford Official-Sample Policy

Only samples referenced by `datasets/oxford_pets/annotations/trainval.txt` and `datasets/oxford_pets/annotations/test.txt` may enter Oxford classification experiments.

Do not glob every file under `datasets/oxford_pets/images/` and treat all raw files as samples. The 41 raw images absent from the official trainval/test annotation set are unreferenced raw images and must not be used for classification experiments.

The four `.jpg`-named PNG files are valid official samples and must not be silently excluded:

- `Abyssinian_5.jpg`
- `Egyptian_Mau_14.jpg`
- `Egyptian_Mau_156.jpg`
- `Egyptian_Mau_186.jpg`

## 8. Raw Dataset Preservation

Raw dataset files are read-only experiment inputs. Do not delete, rename, overwrite, repair, convert, or normalize raw files in place. Any derived manifests, resized caches, metrics, figures, histories, or model checkpoints must be written to assignment output directories.
