# Dataset Audit

Scope: read-only audit of local files under `A05/datasets/`. No raw dataset files were modified and no neural networks were trained.

Generated: 2026-09-21T11:32:24

## Summary

| Dataset | Exists | Status | Discrepancies |
| --- | --- | --- | --- |
| eurosat | yes | ok | none |
| oxford_pets | yes | ok | none |
| diabetes | yes | ok | none |

## Warnings

- Oxford Pets has 41 unreferenced raw files under images/ that are outside the official classification sample set

## EuroSAT

### Expected Properties

- Path: `datasets/eurosat/EuroSAT_RGB/`
- 10 class folders
- Approximately 27,000 JPEG images

### Properties Actually Observed

- Exists: True
- Class folders: 10
- JPEG images: 27000
- Non-JPEG files in class folders: 0
- Duplicate filenames: 0
- Readability check retained from previous audit: deterministic seed-42 sample; structural JPEG header parser; no full pixel decode
- Readability sample: 1000 of 27000
- Unreadable files in sample: 0
- Image shapes in sample: 64x64x3: 1000

| Class | JPEG Count |
| --- | --- |
| AnnualCrop | 3000 |
| Forest | 3000 |
| HerbaceousVegetation | 3000 |
| Highway | 2500 |
| Industrial | 2500 |
| Pasture | 2000 |
| PermanentCrop | 2500 |
| Residential | 3000 |
| River | 2500 |
| SeaLake | 3000 |

### Discrepancies

- None observed.

## Oxford Pets

### Expected Properties

- Path: `datasets/oxford_pets/`
- Canonical classification samples come from `annotations/trainval.txt` and `annotations/test.txt`.
- `images/` may contain raw files not referenced by the official classification annotations.
- File extension is not assumed to identify encoded image content.

### Properties Actually Observed

- Exists: True
- Required official annotation paths present: True
- Train/validation records: 3680
- Test records: 3669
- Total official records: 7349
- Total unique official annotated samples: 7349
- Number of classes: 37
- Trainval/test overlap count: 0
- Missing official image files: 0
- Official samples decoded with Pillow: 7349 of 7349
- Dataset usability: usable; all official annotated samples decode and convert to RGB with Pillow without warnings or workarounds

### Official Image Integrity Categories

| Category | Count | Meaning |
| --- | --- | --- |
| A_valid_standard_jpeg | 7345 | valid standard JPEG |
| B_valid_image_extension_content_mismatch | 4 | valid image but file extension/content-format mismatch |
| C_decodable_with_warnings_or_minor_corruption | 0 | decodable image with warnings/minor corruption |
| D_truly_undecodable | 0 | truly undecodable image |

### Detected Formats For Official Samples

| Format | Count |
| --- | --- |
| JPEG | 7345 |
| PNG | 4 |

### Official Sample Image Shapes

| Width | Height | Count |
| --- | --- | --- |
| 500 | 375 | 1424 |
| 500 | 333 | 1069 |
| 375 | 500 | 511 |
| 333 | 500 | 509 |
| 300 | 225 | 261 |
| 500 | 334 | 250 |
| 500 | 332 | 185 |
| 334 | 500 | 151 |
| 500 | 335 | 97 |
| 332 | 500 | 91 |
| 500 | 500 | 88 |
| 335 | 500 | 53 |
| 225 | 300 | 49 |
| 500 | 400 | 39 |
| 500 | 281 | 29 |
| 500 | 330 | 28 |
| 400 | 500 | 27 |
| 500 | 374 | 27 |
| 500 | 376 | 27 |
| 357 | 500 | 26 |
| 500 | 357 | 25 |
| 500 | 331 | 22 |
| 281 | 500 | 18 |
| 300 | 224 | 18 |
| 300 | 200 | 17 |
| 374 | 500 | 17 |
| 500 | 336 | 16 |
| 500 | 379 | 16 |
| 300 | 199 | 14 |
| 500 | 354 | 14 |
| ... | ... | 987 additional shape rows in JSON |

### Category B Files: Valid Image, Extension/Content Mismatch

- `datasets/oxford_pets/images/Abyssinian_5.jpg`: detected format PNG, size 200x150
- `datasets/oxford_pets/images/Egyptian_Mau_14.jpg`: detected format PNG, size 582x800
- `datasets/oxford_pets/images/Egyptian_Mau_156.jpg`: detected format PNG, size 400x265
- `datasets/oxford_pets/images/Egyptian_Mau_186.jpg`: detected format PNG, size 183x275

### Category C Files: Decodable With Warnings/Minor Corruption

- None.

### Category D Files: Truly Undecodable

- None.

### Unreferenced Raw Images

- Count: 41
- These files are present under `images/` but absent from the official `trainval.txt`/`test.txt` classification sample set. They are not treated as corrupted data and were not deleted.
- `datasets/oxford_pets/images/Abyssinian_34.jpg`
- `datasets/oxford_pets/images/Abyssinian_82.jpg`
- `datasets/oxford_pets/images/Bombay_11.jpg`
- `datasets/oxford_pets/images/Bombay_189.jpg`
- `datasets/oxford_pets/images/Bombay_190.jpg`
- `datasets/oxford_pets/images/Bombay_192.jpg`
- `datasets/oxford_pets/images/Bombay_203.jpg`
- `datasets/oxford_pets/images/Bombay_206.jpg`
- `datasets/oxford_pets/images/Bombay_209.jpg`
- `datasets/oxford_pets/images/Bombay_210.jpg`
- `datasets/oxford_pets/images/Bombay_217.jpg`
- `datasets/oxford_pets/images/Bombay_22.jpg`
- `datasets/oxford_pets/images/Bombay_220.jpg`
- `datasets/oxford_pets/images/Bombay_32.jpg`
- `datasets/oxford_pets/images/Bombay_69.jpg`
- `datasets/oxford_pets/images/Bombay_85.jpg`
- `datasets/oxford_pets/images/Bombay_92.jpg`
- `datasets/oxford_pets/images/Bombay_99.jpg`
- `datasets/oxford_pets/images/boxer_82.jpg`
- `datasets/oxford_pets/images/Egyptian_Mau_129.jpg`
- `datasets/oxford_pets/images/Egyptian_Mau_139.jpg`
- `datasets/oxford_pets/images/Egyptian_Mau_145.jpg`
- `datasets/oxford_pets/images/Egyptian_Mau_167.jpg`
- `datasets/oxford_pets/images/Egyptian_Mau_177.jpg`
- `datasets/oxford_pets/images/Egyptian_Mau_183.jpg`
- `datasets/oxford_pets/images/Egyptian_Mau_191.jpg`
- `datasets/oxford_pets/images/Egyptian_Mau_202.jpg`
- `datasets/oxford_pets/images/Egyptian_Mau_41.jpg`
- `datasets/oxford_pets/images/Egyptian_Mau_71.jpg`
- `datasets/oxford_pets/images/english_cocker_spaniel_162.jpg`
- `datasets/oxford_pets/images/english_cocker_spaniel_163.jpg`
- `datasets/oxford_pets/images/english_cocker_spaniel_164.jpg`
- `datasets/oxford_pets/images/english_cocker_spaniel_179.jpg`
- `datasets/oxford_pets/images/keeshond_59.jpg`
- `datasets/oxford_pets/images/newfoundland_152.jpg`
- `datasets/oxford_pets/images/newfoundland_153.jpg`
- `datasets/oxford_pets/images/newfoundland_154.jpg`
- `datasets/oxford_pets/images/newfoundland_155.jpg`
- `datasets/oxford_pets/images/Siamese_203.jpg`
- `datasets/oxford_pets/images/staffordshire_bull_terrier_2.jpg`
- `datasets/oxford_pets/images/staffordshire_bull_terrier_22.jpg`

### Class Distribution

| Class ID | Class Label | Trainval | Test | Total |
| --- | --- | --- | --- | --- |
| 1 | Abyssinian | 100 | 98 | 198 |
| 2 | american_bulldog | 100 | 100 | 200 |
| 3 | american_pit_bull_terrier | 100 | 100 | 200 |
| 4 | basset_hound | 100 | 100 | 200 |
| 5 | beagle | 100 | 100 | 200 |
| 6 | Bengal | 100 | 100 | 200 |
| 7 | Birman | 100 | 100 | 200 |
| 8 | Bombay | 96 | 88 | 184 |
| 9 | boxer | 100 | 99 | 199 |
| 10 | British_Shorthair | 100 | 100 | 200 |
| 11 | chihuahua | 100 | 100 | 200 |
| 12 | Egyptian_Mau | 93 | 97 | 190 |
| 13 | english_cocker_spaniel | 96 | 100 | 196 |
| 14 | english_setter | 100 | 100 | 200 |
| 15 | german_shorthaired | 100 | 100 | 200 |
| 16 | great_pyrenees | 100 | 100 | 200 |
| 17 | havanese | 100 | 100 | 200 |
| 18 | japanese_chin | 100 | 100 | 200 |
| 19 | keeshond | 100 | 99 | 199 |
| 20 | leonberger | 100 | 100 | 200 |
| 21 | Maine_Coon | 100 | 100 | 200 |
| 22 | miniature_pinscher | 100 | 100 | 200 |
| 23 | newfoundland | 96 | 100 | 196 |
| 24 | Persian | 100 | 100 | 200 |
| 25 | pomeranian | 100 | 100 | 200 |
| 26 | pug | 100 | 100 | 200 |
| 27 | Ragdoll | 100 | 100 | 200 |
| 28 | Russian_Blue | 100 | 100 | 200 |
| 29 | saint_bernard | 100 | 100 | 200 |
| 30 | samoyed | 100 | 100 | 200 |
| 31 | scottish_terrier | 100 | 99 | 199 |
| 32 | shiba_inu | 100 | 100 | 200 |
| 33 | Siamese | 99 | 100 | 199 |
| 34 | Sphynx | 100 | 100 | 200 |
| 35 | staffordshire_bull_terrier | 100 | 89 | 189 |
| 36 | wheaten_terrier | 100 | 100 | 200 |
| 37 | yorkshire_terrier | 100 | 100 | 200 |

### Discrepancies

- None observed for the official annotated classification sample set.

### Recommended Robust Decoding Strategy For Later Training

- Build the classification manifest from `annotations/trainval.txt` and `annotations/test.txt`, not from a directory glob.
- Open images with Pillow and inspect decoded content (`Image.open(...).format`) instead of assuming the `.jpg` extension means JPEG bytes.
- Convert decoded images to RGB in memory before resizing/tensor conversion.
- Keep a deterministic exception list for any category C files that require a documented Pillow workaround, such as `ImageFile.LOAD_TRUNCATED_IMAGES=True`; do not overwrite raw files.
- Fail clearly on category D files because they cannot be decoded into training tensors.

## Diabetes

### Expected Properties

- Path: `datasets/diabetes/diabetes_012_health_indicators_BRFSS2015.csv`
- Target column: `Diabetes_012`
- Approximately 253,680 rows
- 21 predictor features

### Properties Actually Observed

- Exists: True
- Rows: 253680
- Columns: 22
- Target column present: True
- Predictor features: 21
- Total missing values: 0
- Duplicate rows: 23899
- Malformed rows: 0

| Target Value | Count |
| --- | --- |
| 0.0 | 213703 |
| 1.0 | 4631 |
| 2.0 | 35346 |

### Discrepancies

- None observed.

## Notes

- This update corrects the Oxford Pets interpretation: unreferenced raw files under `images/` are not official classification samples and are not treated as dataset corruption.
- The Oxford Pets integrity audit decoded every official annotated sample with Pillow and converted it to RGB in memory without modifying raw files.
- EuroSAT and Diabetes audit results were preserved from the existing audit because no factual correction was requested for them.
