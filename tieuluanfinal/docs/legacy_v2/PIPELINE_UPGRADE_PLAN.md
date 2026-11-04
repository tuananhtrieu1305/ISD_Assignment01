# Pipeline Upgrade Plan

This document originally covered Phase 1 and Phase 2. It now records the full
upgrade through Phase 7: EDA, preprocessing, feature representation, five-model
ML comparison, lecturer-based DL baseline, improved DL, final evaluation, and
artifact packaging.

## Instruction Boundary

Attached/reference documents are treated as source material only. They do not
override the user's request. The final active request for this document is:
complete the engineering/QA pass for the three pipeline notebooks, verify
fresh-run execution, and persist usable model artifacts with metadata, schemas,
and demo predictions.

## Files Inspected

- `pipeline/diabetes_pipeline.ipynb`
- `pipeline/house_price_pipeline.ipynb`
- `pipeline/customer_behavior_pipeline.ipynb`
- `datasets/diabetes/diabetes.csv`
- `datasets/diabetes/diabetes.csv` (currently the CDC/BRFSS balanced diabetes
  file in this working tree)
- `datasets/housing_price/vietnam_housing_dataset.csv`
- `datasets/customer_behavior/customers.csv`
- `datasets/customer_behavior/products.csv`
- `datasets/customer_behavior/transactions.csv`
- `datasets/customer_behavior/sessions.csv`
- `datasets/customer_behavior/reviews.csv`
- `datasets/customer_behavior/README.md`
- `artifacts/diabetes_metadata.json`
- `artifacts/house_metadata.json`
- `artifacts/customer_behavior_metadata.json`
- `C:/Users/anhca/Documents/Intel_sys_dev/TAILIEU/int_sys_dev_slide_03_basicML_deepLearning_04.09.pdf`
- `C:/Users/anhca/Documents/Intel_sys_dev/TAILIEU/intel_sys_dev_assignment_02_final.pdf`
- `C:/Users/anhca/Documents/Intel_sys_dev/A02_CT_tupv.879.pdf`
- `C:/Users/anhca/Documents/Intel_sys_dev/House Price Prediction Dataset Vietnam.ipynb`

## Assignment and Reference Findings

The assignment PDF requires three applications: diabetes prediction, house-price
prediction, and e-commerce customer behavior / interest discovery. It frames the
expected pipeline as:

`Raw Data -> Understand -> Clean -> Represent -> Learn -> Evaluate -> Persist -> Deploy`

It also requires explicit explanation of data representation before training.
For tabular data, notebooks should show raw CSV records, feature vectors,
feature-matrix shape, and model-ready numeric representations. For text data,
the customer notebook should show comment/review text transformed through
tokens, token IDs, and vector or embedding-style representations.

The local sample notebook `House Price Prediction Dataset Vietnam.ipynb` is only
a minimal two-cell notebook that imports NumPy/Pandas, reads
`vietnam_housing_dataset.csv`, and calls `info()` / `head()`.

The sample PDF `A02_CT_tupv.879.pdf` could be detected and partially inspected,
but its text extraction is poor because most meaningful content is compressed or
glyph-encoded. It should be used in a later run mainly as a visual/style
reference unless a better PDF/OCR tool is available.

## Teacher Deep Learning Baseline

Source:
`C:/Users/anhca/Documents/Intel_sys_dev/TAILIEU/int_sys_dev_slide_03_basicML_deepLearning_04.09.pdf`

Identified title and scope: "Deep Learning from Scratch with NumPy" for diabetes
prediction using a 3-layer neural network. The PDF explicitly states:

- No TensorFlow
- No PyTorch
- No Keras
- No Scikit-learn for the neural network
- Only NumPy is used for the neural network

Teacher baseline characteristics to preserve before any improvement:

- Imports: `import numpy as np`
- Original data assumption: `diabetes.csv`
- Original loading pattern: `np.loadtxt("diabetes.csv", delimiter=",", skiprows=1)`
- Original feature assumption: first 8 columns are numeric input features
- Original target assumption: column index 8 reshaped to `(-1, 1)`
- Original train/test split: random permutation with `np.random.seed(42)`,
  80 percent train and 20 percent test
- Original normalization: train-set mean and std only, with `std + 1e-8`;
  apply the same train statistics to test data
- Architecture: `8 -> 16 -> 8 -> 1`
- Hidden activations: ReLU for layer 1 and layer 2
- Output activation: sigmoid
- Weight initialization:
  - `W1 = np.random.randn(8, 16) * np.sqrt(2.0 / 8)`
  - `W2 = np.random.randn(16, 8) * np.sqrt(2.0 / 16)`
  - `W3 = np.random.randn(8, 1) * np.sqrt(2.0 / 8)`
  - biases initialized with zeros
- Loss: binary cross-entropy with clipping epsilon `1e-8`
- Optimizer: manual full-batch gradient descent, not Adam/SGD from a framework
- Learning rate: `0.01`
- Epochs: `1000`
- Batch size: no mini-batch; the code uses full training arrays each epoch
- Validation strategy: no separate validation set; only train/test split
- Prediction threshold: `y_prob >= 0.5`
- Metrics implemented manually: accuracy, TP/TN/FP/FN, precision, recall, F1
- Example predictions: print the first up to 10 test rows with probability,
  predicted class, and actual class

What must be preserved in the teacher baseline section:

- NumPy-only implementation
- Manual forward propagation
- Manual binary cross-entropy for binary classification tasks
- Manual backpropagation
- Manual gradient descent updates
- Same learning rate and epochs
- Same hidden-layer sizes `16` and `8`
- Same train-only normalization logic
- No early stopping, dropout, batch normalization, class weights, Adam, Keras,
  PyTorch, TensorFlow, or scikit-learn MLP in the teacher baseline

Strictly necessary adaptations:

- Input dimension must become the number of model-ready features for each
  dataset, so `W1` shape changes from `(8, 16)` to `(input_dim, 16)`.
- Diabetes target changes from `Outcome` to `Diabetes_binary` after dataset
  replacement.
- Customer target uses `is_churned`; the output remains binary sigmoid.
- House price is regression, so the adapted baseline must keep the NumPy
  feed-forward/backpropagation structure but replace sigmoid/BCE with a linear
  output and MSE/RMSE-style regression loss. This should be documented as a
  task-required adaptation, not as an optional improvement.
- For datasets with categorical/text preprocessing, the teacher baseline can
  receive a dense, already-preprocessed matrix. The preprocessing step must be
  outside and clearly separate from the NumPy neural-network code.

Optional improvements postponed to the Improved DL section:

- Larger architecture such as `input_dim -> 32 -> 16 -> 1`
- Validation split
- Loss history plots
- Early stopping
- Mini-batch training
- Class-weighted binary cross-entropy
- Learning-rate sweep
- L2 regularization
- Dropout
- Threshold tuning
- Adding selected TF-IDF/text features to the customer DL model
- Target log-transform or target standardization for house-price DL

## Dataset Sources

- Diabetes selected source: CDC Diabetes Health Indicators / BRFSS 2015, Kaggle
  dataset by Alex Teboul, CC0 Public Domain:
  `https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset/data`
- Diabetes metadata/reference: UCI CDC Diabetes Health Indicators:
  `https://archive.ics.uci.edu/dataset/891/cdc%2BDiabetes_012%2Bhealth%2Bindicators`
- Diabetes local acquisition mirror used in this run:
  `https://huggingface.co/datasets/thomask1018/diabetes/blob/main/diabetes_binary_5050split_health_indicators_BRFSS2015.csv`
- House selected source: House Price Prediction Dataset Vietnam - 2024,
  Kaggle by Nguyen Tien Nhan, CC0 Public Domain:
  `https://www.kaggle.com/datasets/nguyentiennhan/vietnam-housing-dataset-2024`
- House alternative not selected now: Vietnam Housing Dataset (Hanoi), Kaggle
  by Le Anh Duc, CC BY-NC-SA 4.0, `VN_housing_dataset.csv` about 18.1 MB:
  `https://www.kaggle.com/datasets/ladcva/vietnam-housing-dataset-hanoi`
- Customer selected source: Synthetic E-Commerce Customer Behavior Dataset,
  Kaggle by Lorenzo Scaturchio, GPL-3.0:
  `https://www.kaggle.com/datasets/lorenzoscaturchio/ecommerce-behavior`

## Global Later-Run Rules

- Each final notebook must contain 5 basic ML models plus one improved DL model
  in the final main comparison table.
- The teacher DL code must be shown first as a baseline, with only documented
  shape/task adaptations.
- The final comparison table must contain exactly these 6 main models:
  5 ML models + improved DL.
- The teacher baseline DL can appear in an auxiliary comparison table but should
  not replace the improved DL in the final 6-model comparison.
- All notebooks should keep relative paths and remain runnable from the project
  root.
- No generated model artifacts should be committed unless explicitly requested.

---

# 1. Diabetes Pipeline

## 1. Current State

- Notebook: `pipeline/diabetes_pipeline.ipynb`
- Current dataset: `datasets/diabetes/diabetes.csv`
- Current dataset shape: 768 rows, 9 columns
- Current target: `Outcome`
- Current selected features:
  - `Glucose`
  - `BMI`
  - `Age`
  - `Pregnancies`
  - `BloodPressure`
  - `DiabetesPedigreeFunction`
- Current excluded Pima features: `SkinThickness`, `Insulin`
- Current task: binary classification
- Current preprocessing:
  - replace invalid zero values in `Glucose`, `BloodPressure`, and `BMI` with
    missing values
  - median imputation in sklearn pipelines
  - standard scaling for Logistic Regression, KNN, and SVM
- Current ML models:
  - Logistic Regression
  - KNN
  - Decision Tree
  - Random Forest
  - SVM (RBF)
- Current metrics:
  - Accuracy
  - Precision
  - Recall
  - F1
- Current split/CV:
  - stratified 80/20 train/test split
  - `StratifiedKFold(n_splits=5)`
- Current deployment/model-saving logic:
  - saves `artifacts/diabetes_pipeline.joblib`
  - saves one artifact per ML model under `artifacts/diabetes_models/`
  - saves `artifacts/diabetes_metadata.json`
- Current obsolete/weak content:
  - dataset is too small for a convincing ML + DL comparison
  - no teacher DL baseline
  - no improved DL section
  - only 6 selected features, while the replacement dataset has 21 available
    health indicators

## 2. Dataset Decision

Decision: replace the final diabetes dataset.

Reason: the current Pima dataset has only 768 rows and 8 original predictors.
It can run the assignment, but it is too small for a strong 5 ML + neural
network comparison. This is a serious data-size limitation under the dataset
decision rules.

Selected local file for the upgraded notebook:

- `datasets/diabetes/diabetes.csv`

Phase 3 correction: in the current working tree, `datasets/diabetes/diabetes.csv`
already contains the CDC/BRFSS balanced health-indicators dataset. The longer
planned filename
`datasets/diabetes/diabetes_binary_5050split_health_indicators_BRFSS2015.csv`
is not present. The original small Pima file is no longer present under
`datasets/diabetes/`, so later runs must not assume it is available locally.

New dataset audit:

- Rows: 70,692
- Columns: 22
- Target: `Diabetes_binary`
- Task type: binary classification
- Class balance: exactly 35,346 class `0.0` and 35,346 class `1.0`
- Missing values: 0
- Duplicate rows: 1,635 exact duplicate rows
- Rows after duplicate removal in Phase 3 notebook: 69,057
- Class balance after duplicate removal: 33,960 class `0` and 35,097 class `1`
- ID-only columns: none
- Field types: all numeric-coded binary/ordinal/integer health indicators
- Enough data for ML + DL: yes
- Reproducible processing: yes, local CSV file with relative path

## 3. Final Target

- `Diabetes_binary`
- Class `0`: no diabetes
- Class `1`: prediabetes or diabetes

## 4. Planned Preprocessing

- Load `datasets/diabetes/diabetes.csv`, which is currently the CDC/BRFSS
  balanced diabetes file.
- Convert target values from float-like strings to integers.
- Drop exact duplicate rows before splitting to avoid duplicate leakage across
  train/test.
- Use all 21 non-target columns initially.
- Treat binary-coded columns as numeric indicators.
- Treat ordinal-coded columns such as `GenHlth`, `Age`, `Education`, and
  `Income` carefully; start numeric, then discuss ordinal meaning.
- Use stratified train/test split.
- For ML pipelines:
  - impute only if needed, but document that source has no missing values
  - scale for Logistic Regression, KNN, and SVM
  - no scaling required for tree models
- For teacher DL:
  - use dense numeric matrix
  - normalize with train mean/std only

## 5. Planned EDA

- Dataset overview and data dictionary.
- Class balance table and plot.
- Duplicate-row analysis and decision to drop duplicates.
- Distribution of major risk factors:
  - BMI
  - HighBP
  - HighChol
  - GenHlth
  - Age
  - PhysHlth
  - MentHlth
- Target-rate by key binary/ordinal features.
- Correlation or mutual information with `Diabetes_binary`.
- Short fairness/sensitivity note for `Sex`, `Education`, and `Income`.
- One raw record -> feature vector -> feature matrix shape -> final DL matrix.

## 6. Planned 5 ML Models

- Logistic Regression
- KNN
- Decision Tree
- Random Forest
- SVM

## 7. Teacher DL Baseline Adaptation

- Preserve NumPy-only implementation.
- Preserve manual forward/backward/BCE/gradient-descent logic.
- Adapt input dimension from 8 to 21 after duplicate removal and target split.
- Keep hidden sizes `16` and `8`.
- Keep sigmoid output.
- Keep `learning_rate = 0.01`.
- Keep `epochs = 1000`.
- Keep full-batch training.
- Keep threshold `0.5`.
- Add clear markdown stating these are shape/target-name adaptations only.

## 8. Planned DL Improvements

- Add validation split from training data.
- Track and plot loss history.
- Try architecture `21 -> 32 -> 16 -> 1`.
- Add mini-batch option only in improved section.
- Tune learning rate from a small candidate list.
- Add threshold tuning to optimize F1 or recall/F1 trade-off.
- Optionally add L2 regularization if overfitting appears.

## 9. Evaluation Metrics

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC
- PR-AUC if class balance changes after duplicate removal
- Confusion matrix
- Optional threshold curve for precision/recall

## 10. Final Artifacts to Save

- Best sklearn ML pipeline if best model is ML
- DL weights as `.npz` if improved DL is best or included for deployment
- Preprocessing metadata and feature schema
- `artifacts/diabetes_metadata.json`
- Updated selectable model artifacts under `artifacts/diabetes_models/`
- Demo input rows compatible with the new CDC schema

## 11. Risks / Potential Leakage

- Exact duplicate rows could leak into train/test if not removed before split.
- Demographic variables (`Sex`, `Education`, `Income`) may raise fairness and
  sensitivity concerns; keep but discuss clearly unless instructed otherwise.
- Replacing Pima means current backend/web/mobile diabetes form fields are no
  longer sufficient if deployment must stay in scope.

## 12. Exact Files Modified in Later Runs

- `pipeline/diabetes_pipeline.ipynb`
- `artifacts/diabetes_pipeline.joblib`
- `artifacts/diabetes_metadata.json`
- `artifacts/diabetes_models/*.joblib`
- `backend/app.py` if deployment schema must support CDC features
- `web/src/pages/DiabetesPage.tsx` if the web form must support CDC features
- `mobile/src/screens/DiabetesScreen.tsx` if the mobile form must support CDC
  features

---

# 2. House Price Pipeline

## 1. Current State

- Notebook: `pipeline/house_price_pipeline.ipynb`
- Current dataset: `datasets/housing_price/vietnam_housing_dataset.csv`
- Current dataset shape: 30,229 rows, 12 columns
- Current target: `Price`
- Current target meaning: price in billions of VND
- Current selected features:
  - `Area`
  - `Frontage`
  - `Access Road`
  - `Floors`
  - `Bedrooms`
  - `Bathrooms`
- Current available but mostly unused fields:
  - `Address`
  - `House direction`
  - `Balcony direction`
  - `Legal status`
  - `Furniture state`
- Current task: regression
- Current preprocessing:
  - numeric features selected directly
  - median imputation in sklearn pipelines
  - standard scaling for Linear Regression and KNN
- Current ML models:
  - Linear Regression
  - KNN Regressor
  - Decision Tree Regressor
  - Random Forest Regressor
  - Gradient Boosting Regressor
- Current metrics:
  - MAE
  - MSE
  - RMSE
  - R2
  - MAPE
- Current split/CV:
  - 80/20 train/test split
  - `KFold(n_splits=3)`
- Current deployment/model-saving logic:
  - saves `artifacts/house_pipeline.joblib`
  - saves one artifact per ML model under `artifacts/house_models/`
  - saves `artifacts/house_metadata.json`
- Current obsolete/weak content:
  - no teacher DL baseline
  - no improved DL section
  - high-cardinality `Address` is excluded instead of used to derive location
  - categorical fields are not yet used in the main model

## 2. Dataset Decision

Decision: keep the current dataset for now.

Reason: the current dataset is already a Vietnam house-price dataset, has 30k+
rows, a sensible continuous price target, and meaningful real-estate fields.
It is smaller than the alternative Hanoi Kaggle dataset, but it does not have a
serious issue that justifies replacement under the decision rules.

Current dataset audit:

- Rows: 30,229
- Columns: 12
- Target: `Price`
- Task type: regression
- Missing values:
  - `Balcony direction`: 82.65 percent
  - `House direction`: 70.26 percent
  - `Furniture state`: 46.71 percent
  - `Access Road`: 43.99 percent
  - `Frontage`: 38.25 percent
  - `Bathrooms`: 23.40 percent
  - `Bedrooms`: 17.08 percent
  - `Legal status`: 14.91 percent
  - `Floors`: 11.92 percent
- Duplicate rows: 0
- ID-only columns: none
- High-cardinality text/location field: `Address`
- Enough data for ML + DL: yes
- Reproducible processing: yes, local CSV file with relative path

Alternative not selected now:

- Kaggle `ladcva/vietnam-housing-dataset-hanoi`
- About 82,497 rows and 13 columns according to public references
- Better explicit location fields (`Quận`, `Huyện`) and property type
- Requires Kaggle login/terms and has non-commercial share-alike license
- Can be revisited only if the user supplies the CSV or explicitly wants the
  Hanoi-only dataset

## 3. Final Target

- `Price`
- Unit: billions of VND
- Regression target

## 4. Planned Preprocessing

- Keep `Price` as numeric; audit outliers before modeling.
- Derive location features from `Address` where possible:
  - province/city
  - district-like token
  - project flag if address starts with a project phrase
- Include both numeric and categorical features:
  - numeric: `Area`, `Frontage`, `Access Road`, `Floors`, `Bedrooms`,
    `Bathrooms`
  - categorical: derived location, `Legal status`, `Furniture state`,
    `House direction`, maybe `Balcony direction` if useful despite missingness
- Use median imputation for numeric columns.
- Use explicit `"Unknown"` category for categorical missing values.
- Use one-hot encoding with unknown handling.
- Consider `log1p(Price)` as a planned modeling experiment, not as default
  baseline preprocessing.
- Use the same preprocessing object for ML and DL comparisons where possible.

## 5. Planned EDA

- Dataset overview and data dictionary.
- Missingness table/heatmap.
- Price distribution and log-price distribution.
- Area, bedrooms, bathrooms, floors distributions.
- Price vs area scatter and residual/outlier comments.
- Price by legal status, furniture state, direction, and derived location.
- Correlation and mutual information for numeric features.
- One raw record -> feature vector -> feature matrix shape.

## 6. Planned 5 ML Models

- Linear Regression
- KNN Regressor
- Decision Tree Regressor
- Random Forest Regressor
- Gradient Boosting Regressor

## 7. Teacher DL Baseline Adaptation

- Preserve NumPy-only feed-forward/backpropagation structure.
- Preserve two hidden layers with sizes `16` and `8`.
- Preserve train-only normalization for numeric model matrix.
- Adapt input dimension to the final dense feature matrix.
- Required regression adaptation:
  - use linear output instead of sigmoid
  - use MSE loss instead of binary cross-entropy
  - evaluate regression metrics instead of TP/TN/precision/recall/F1
- Keep `learning_rate = 0.01` and `epochs = 1000` initially unless numerical
  instability makes the baseline impossible; if changed, document as a required
  stability adaptation, not an improvement.
- No target log-transform, early stopping, Adam, dropout, or architecture tuning
  in teacher baseline.

## 8. Planned DL Improvements

- Use validation split and early stopping.
- Track train/validation loss.
- Compare raw target vs log-transformed target.
- Optionally standardize target for DL training stability.
- Try architecture such as `input_dim -> 64 -> 32 -> 1`.
- Add mini-batch training only in improved section.
- Tune learning rate if baseline is unstable.

## 9. Evaluation Metrics

- MAE
- MSE
- RMSE
- R2
- MAPE
- Residual plots
- Actual-vs-predicted plot

## 10. Final Artifacts to Save

- Best sklearn ML pipeline if best model is ML
- DL weights `.npz` plus preprocessing transformer if improved DL is selected
  or included for demo
- `artifacts/house_pipeline.joblib`
- `artifacts/house_metadata.json`
- Updated selectable model artifacts under `artifacts/house_models/`
- Demo input rows with area, location-derived fields, legal/furniture status,
  and numeric house attributes

## 11. Risks / Potential Leakage

- `Address` is not ID-only, but it is high-cardinality and may overfit if used
  naively.
- Missingness is high in directions, frontage, access road, and furniture state.
- Price outliers could dominate RMSE and DL training.
- Derived location parsing from free text may be noisy.
- If the user later chooses the Hanoi dataset, target may change from total
  price to price per square meter, requiring a different interpretation.

## 12. Exact Files Modified in Later Runs

- `pipeline/house_price_pipeline.ipynb`
- `artifacts/house_pipeline.joblib`
- `artifacts/house_metadata.json`
- `artifacts/house_models/*.joblib`
- `backend/app.py` if the prediction schema changes
- `web/src/pages/HousePricePage.tsx` if the web form adds categorical/location
  fields
- `mobile/src/screens/HousePriceScreen.tsx` if the mobile form adds
  categorical/location fields

---

# 3. Customer Behavior / Interest Discovery Pipeline

## 1. Current State

- Notebook: `pipeline/customer_behavior_pipeline.ipynb`
- Current dataset folder: `datasets/customer_behavior/`
- Current local files:
  - `customers.csv`
  - `products.csv`
  - `transactions.csv`
  - `sessions.csv`
  - `reviews.csv`
- Current actual table sizes:
  - `customers.csv`: 10,000 rows, 10 columns
  - `products.csv`: 1,000 rows, 11 columns
  - `transactions.csv`: 120,000 rows, 11 columns
  - `sessions.csv`: 80,000 rows, 10 columns
  - `reviews.csv`: 25,000 rows, 8 columns
- Current target: `is_churned`
- Current task: binary classification with interest-discovery interpretation
- Current target balance:
  - class `0`: 8,306 rows, 83.06 percent
  - class `1`: 1,694 rows, 16.94 percent
- Current engineered features:
  - customer profile features
  - transaction aggregates
  - session aggregates
  - review aggregates
  - top category / brand
  - review text cleaned into one text field
- Current feature counts in metadata:
  - 29 numeric features
  - 8 categorical features
  - 1 text feature
- Current preprocessing:
  - fill numeric missing values with 0 after aggregation
  - fill categorical missing values with `"Unknown"`
  - use sklearn `ColumnTransformer`
  - scale numeric features
  - one-hot encode categorical features
  - TF-IDF for text model variant
- Current ML models:
  - Logistic Regression (tabular)
  - Decision Tree (tabular)
  - Random Forest (tabular)
  - Linear SVM (tabular)
  - Gradient Boosting (tabular)
  - Text + Tabular Logistic Regression
- Current metrics:
  - Accuracy
  - Precision
  - Recall
  - F1
  - ROC-AUC for final model where available
- Current split/CV:
  - stratified train/test split
  - `StratifiedKFold(n_splits=3)`
- Current deployment/model-saving logic:
  - saves `artifacts/customer_churn_pipeline.joblib`
  - saves one artifact per model under `artifacts/customer_behavior_models/`
  - saves `artifacts/customer_behavior_metadata.json`
- Current obsolete/weak content:
  - no teacher DL baseline
  - no improved DL section
  - current README row counts are stale compared with actual files
  - current aggregation uses the full observed time span and needs a leakage
    discussion or time-aware cutoff

## 2. Dataset Decision

Decision: keep the current dataset.

Reason: the current dataset is genuinely suitable. It is relational, joins on
customer/product keys, contains profile, transaction, session, product, and
review text tables, has enough rows for ML + DL, and includes an explicit churn
label. Replacing it only because another dataset exists would violate the
dataset decision rules.

Current dataset audit:

- Missing values: 0 across all five CSV files
- Duplicate rows: 0 across all five CSV files
- ID-only columns:
  - `customer_id`
  - `product_id`
  - `transaction_id`
  - `session_id`
  - `review_id`
- Text field: `review_text`
- Categorical fields:
  - customer: `gender`, `country`, `segment`
  - product: `category`, `brand`
  - transaction: `status`, `payment_method`
  - session: `device`, `channel`
- Numerical fields:
  - customer: `age`, `lifetime_value`, `email_opt_in`, `has_app`
  - product: price/rating/stock/discount fields
  - transaction: quantity, price, amount, discount, shipping
  - session: duration, pages, converted, bounced, cart additions
  - review: rating, helpful votes, verified purchase
- Enough data for ML + DL: yes
- Reproducible processing: yes, all files are local relative paths

README issue:

- `datasets/customer_behavior/README.md` appears stale. It says some tables have
  5,000 rows, but actual files have 10,000 customers, 120,000 transactions,
  80,000 sessions, and 25,000 reviews.

## 3. Final Target

Primary supervised target:

- `is_churned`

Reason:

- It is an explicit customer-level label and supports fair 5 ML + DL binary
  classification.
- It is semantically meaningful for customer behavior.
- The interest-discovery requirement should be handled as an interpretation and
  representation section using `top_category`, `top_brand`, session behavior,
  and review text.

Rejected as primary target for now:

- `top_category` / `top_brand`: these are derived from transaction/product
  history and would create target leakage if the same history is also used as
  input features.
- `converted`: this is session-level, not customer-level, and would shift the
  problem away from customer behavior/interest discovery.
- `rating`: review-level target, not customer-level, and does not directly match
  the current pipeline structure.

## 4. Planned Preprocessing

- Keep relational joins at customer level.
- Exclude ID-only columns from model features.
- Continue excluding raw `lifetime_value` unless the prediction horizon is
  explicitly defined.
- Add a time-aware feature cutoff if feasible:
  - compute features using activity before a cutoff date
  - define churn label as post-cutoff behavior if the dataset supports it
- If a true temporal label cannot be reconstructed, document the synthetic label
  limitation and avoid using obviously label-derived fields.
- Numeric preprocessing:
  - impute missing aggregate values with 0 when absence means no activity
  - otherwise median imputation
  - scale for LR, KNN, SVM, and DL
- Categorical preprocessing:
  - fill `"Unknown"`
  - one-hot encode with unknown handling
- Text preprocessing:
  - lowercase/clean review text
  - tokenize and show token IDs for assignment representation
  - TF-IDF for text-inclusive ML
  - dense selected TF-IDF or embedding-like representation for improved DL

## 5. Planned EDA

- Table-level row/column/missing/duplicate overview.
- Customer churn distribution.
- Profile analysis by churn:
  - segment
  - country
  - email opt-in
  - app usage
- Behavioral analysis by churn:
  - recency
  - frequency
  - monetary value
  - completed/cancelled/refunded rates
  - session conversion/bounce/cart additions
- Interest-discovery analysis:
  - top categories and brands
  - category distribution by churn
  - review text frequent terms
  - example customer profile -> top category/brand -> review terms
- Text representation demo:
  - raw review
  - tokens
  - token IDs
  - TF-IDF/vector or embedding-style tensor shape

## 6. Planned 5 ML Models

Use exactly five ML models in the final main comparison:

- Logistic Regression
- KNN
- Decision Tree
- Random Forest
- Gradient Boosting

Linear SVM can remain as an auxiliary experiment if useful, but the final main
comparison should stay at 5 ML models plus improved DL.

## 7. Teacher DL Baseline Adaptation

- Preserve NumPy-only implementation.
- Preserve two hidden layers with sizes `16` and `8`.
- Preserve sigmoid output and binary cross-entropy.
- Preserve manual gradient descent.
- Preserve `learning_rate = 0.01`.
- Preserve `epochs = 1000`.
- Preserve full-batch training.
- Adapt input dimension to the dense customer feature matrix.
- Use tabular dense representation for the teacher baseline to avoid silently
  redesigning the teacher network for sparse/high-dimensional text.
- Add markdown saying text-enhanced DL is postponed to the Improved DL section.

## 8. Planned DL Improvements

- Add validation split and loss curves.
- Add class-weighted BCE because churn is imbalanced.
- Add mini-batch training.
- Tune decision threshold for F1 or recall.
- Include a compact text representation:
  - selected top TF-IDF terms, or
  - low-dimensional dense text representation
- Try architecture such as `input_dim -> 64 -> 32 -> 1`.
- Compare teacher baseline DL vs improved DL in an auxiliary table.

## 9. Evaluation Metrics

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC
- PR-AUC due churn imbalance
- Confusion matrix
- Threshold trade-off table

## 10. Final Artifacts to Save

- Best sklearn ML pipeline if best model is ML
- DL weights `.npz` plus preprocessing transformer if improved DL is selected
  or included for demo
- `artifacts/customer_churn_pipeline.joblib`
- `artifacts/customer_behavior_metadata.json`
- Updated selectable model artifacts under `artifacts/customer_behavior_models/`
- Demo customer cases and interest explanation fields

## 11. Risks / Potential Leakage

- `lifetime_value` is a likely leakage/reference column and should remain
  excluded unless the prediction time window is explicitly defined.
- Full-period transaction/session/review aggregates may leak future behavior
  into churn prediction if `is_churned` is intended as a future label.
- `top_category` and `top_brand` are derived from completed transactions; they
  are useful for interpretation but risky as targets without a temporal split.
- The dataset is synthetic; note that patterns are educational simulations, not
  real customer causality.
- Class imbalance requires PR-AUC and threshold tuning, not accuracy alone.

## 12. Exact Files Modified in Later Runs

- `pipeline/customer_behavior_pipeline.ipynb`
- `datasets/customer_behavior/README.md` to correct stale row counts, if desired
- `artifacts/customer_churn_pipeline.joblib`
- `artifacts/customer_behavior_metadata.json`
- `artifacts/customer_behavior_models/*.joblib`
- `backend/app.py` if prediction schema or best model changes
- `web/src/pages/CustomerBehaviorPage.tsx` if the web form changes
- `mobile/src/screens/CustomerBehaviorScreen.tsx` if the mobile form changes

---

## Phase 1 and Phase 2 Decisions Locked Before Phase 3

- Diabetes dataset: replace Pima in the final notebook with
  the local CDC/BRFSS diabetes file. Phase 3 uses
  `datasets/diabetes/diabetes.csv` because that is the actual selected file
  currently present.
- House dataset: keep `datasets/housing_price/vietnam_housing_dataset.csv`.
- Customer dataset: keep `datasets/customer_behavior/`.
- Diabetes target: `Diabetes_binary`.
- House target: `Price`.
- Customer target: `is_churned`.
- Future final main comparison: 5 ML models + improved DL model for each
  notebook.
- Teacher DL baseline must be shown before improvements and must not be silently
  optimized.

## Phase 3 Update: EDA, Preprocessing, and Representation

Files updated in Phase 3:

- `pipeline/diabetes_pipeline.ipynb`
- `pipeline/house_price_pipeline.ipynb`
- `pipeline/customer_behavior_pipeline.ipynb`
- `PIPELINE_UPGRADE_PLAN.md`

Scope completed:

- Replaced active full-modeling sections with Phase 3 EDA, data-quality,
  representation, preprocessing architecture, and validation cells.
- Added end-of-notebook checks for X/y definition, target exclusion from X,
  split creation, preprocessing transform shape, and NaN/Inf absence.
- Did not run or add final 5-ML + DL comparison.
- Did not add final DL training or final model/artifact export.

Diabetes Phase 3 decisions:

- Use all 21 CDC/BRFSS non-target features initially.
- Treat binary survey columns as numeric indicators.
- Treat `GenHlth`, `Age`, `Education`, and `Income` as ordinal-coded survey
  features.
- Treat `BMI` as continuous and `MentHlth` / `PhysHlth` as 0-30 day counts.
- Drop 1,635 exact duplicates before train/test split.
- Use median imputation plus `StandardScaler` in a sklearn `ColumnTransformer`.
- No target leakage columns or ID-only columns found.

House Price Phase 3 decisions:

- Parse/normalize units robustly for possible values containing `m²`,
  `triệu/m²`, `tỷ`, or `triệu`, while preserving the current numeric CSV.
- Derive `city`, `district`, and `ward_or_street` from `Address`.
- Use `Price_BillionVND` as target and prepare `Log_Price_BillionVND` only as a
  Run 3 experiment.
- Remove impossible records with invalid price/area and area under 10 m²;
  current notebook removes 6 area-under-10 records.
- Use numeric features `Area_m2`, `Frontage_m`, `Access_Road_m`, `Floors`,
  `Bedrooms`, `Bathrooms`.
- Use categorical features `city`, `district`, `Legal status`,
  `Furniture state`, `House direction`, `Balcony direction`.
- Keep `price_per_m2_million` for EDA only; exclude it from X because it is
  mathematically derived from target price.

Customer Phase 3 decisions:

- Define prediction time as 90 days before the latest observed event:
  `2024-10-01 23:59:05`.
- Build customer-level features only from pre-cutoff activity:
  105,502 transactions, 70,139 sessions, and 21,848 reviews.
- Exclude `lifetime_value`, ID columns, and raw date columns from X.
- Engineer RFM/spending, transaction-status, session/funnel,
  category/brand preference, review/rating, recency, and compact text features.
- Use `is_churned` as the supervised target.
- Keep interest discovery as representation/interpretation through
  `top_category`, `top_brand`, category spend features, channel/device, and
  review text.
- Remaining limitation: the dataset provides `is_churned` without a churn date,
  so the exact outcome window cannot be reconstructed.

## Phase 4-6 Update: Modeling, Deep Learning, and Evaluation

Files updated in Phase 4-6:

- `pipeline/diabetes_pipeline.ipynb`
- `pipeline/house_price_pipeline.ipynb`
- `pipeline/customer_behavior_pipeline.ipynb`
- `PIPELINE_UPGRADE_PLAN.md`

Global modeling structure now implemented:

- One simple reference baseline per notebook.
- Exactly five main classical ML models per notebook.
- A separate "Deep Learning Baseline Based on Lecturer Code" section.
- A separate "Improved Deep Learning Model" section.
- A separate teacher-DL-vs-improved-DL table.
- A final main comparison table with exactly 6 rows:
  five ML models plus `Improved DNN`.
- The teacher DL baseline is excluded from the final main table by assertion.

Execution environment:

- Full notebook code execution was performed with
  `backend/.venv/Scripts/python.exe`.
- `matplotlib` was installed into the local backend venv for plot-path
  verification after the first run showed it was missing.
- Final verification used the non-GUI Matplotlib `Agg` backend.
- All three notebooks executed end-to-end after the compatibility fix for
  Matplotlib 3.11 `boxplot(tick_labels=...)`.

Diabetes Phase 4-6 results:

- Main ML models:
  - Logistic Regression
  - KNN
  - Decision Tree
  - Random Forest
  - SVM implemented with `LinearSVC` for runtime stability on the larger CDC
    dataset
- Teacher DL baseline:
  - NumPy only
  - architecture `input_dim -> 16 -> 8 -> 1`
  - ReLU/ReLU/Sigmoid
  - binary cross-entropy
  - full-batch gradient descent
  - `learning_rate = 0.01`
  - `epochs = 1000`
  - threshold `0.5`
- Improved DL:
  - NumPy only
  - architecture `input_dim -> 32 -> 16 -> 1`
  - validation split from training data
  - mini-batch training
  - L2 regularization
  - early stopping
  - validation-threshold tuning
- Best final model by F1 in verification run: `Improved DNN`
- Improved DNN verification metrics:
  - Accuracy: 0.7208
  - Precision: 0.6609
  - Recall: 0.9256
  - F1: 0.7712
  - ROC-AUC: 0.8192
- Strongest classical model by F1: Random Forest, F1 0.7602
- Teacher DL baseline F1: 0.7310

House Price Phase 4-6 results:

- Main ML models:
  - Linear Regression
  - KNN Regressor
  - Decision Tree Regressor
  - Random Forest Regressor
  - Gradient Boosting Regressor
- Classical ML target handling:
  - models are wrapped with `TransformedTargetRegressor`
  - training target uses `log1p(Price_BillionVND)`
  - predictions are inverse-transformed with `expm1`
  - final metrics remain in original billion-VND units
- Teacher DL baseline:
  - NumPy only
  - architecture `input_dim -> 16 -> 8 -> 1`
  - ReLU/ReLU/linear output
  - MSE loss as required regression adaptation
  - full-batch gradient descent
  - `learning_rate = 0.01`
  - `epochs = 1000`
- Improved DL:
  - NumPy only
  - architecture `input_dim -> 64 -> 32 -> 1`
  - standardized log target
  - validation split
  - mini-batch training
  - L2 regularization
  - early stopping
  - inverse transform to original units for final metrics
- Best final model by RMSE in verification run: `Improved DNN`
- Improved DNN verification metrics:
  - MAE: 1.0648 billion VND
  - MSE: 2.0077
  - RMSE: 1.4169 billion VND
  - R2: 0.5799
  - MAPE: 21.2207 percent
- Strongest classical model by RMSE: Random Forest Regressor, RMSE 1.4399
- Teacher DL baseline RMSE: 1.4568

Customer Behavior Phase 4-6 results:

- Main ML models:
  - Logistic Regression
  - KNN
  - Decision Tree
  - Random Forest
  - Gradient Boosting
- All final models use the same customer-level numeric, categorical, and TF-IDF
  text information from the Phase 3 cutoff representation.
- Teacher DL baseline:
  - NumPy only
  - architecture `input_dim -> 16 -> 8 -> 1`
  - ReLU/ReLU/Sigmoid
  - binary cross-entropy
  - full-batch gradient descent
  - `learning_rate = 0.01`
  - `epochs = 1000`
  - threshold `0.5`
- Improved DL:
  - NumPy only
  - architecture `input_dim -> 64 -> 32 -> 1`
  - validation split
  - mini-batch training
  - L2 regularization
  - early stopping
  - class-weighted BCE for churn imbalance
  - validation-threshold tuning
- Best final model by F1 in verification run: `Improved DNN`
- Improved DNN verification metrics:
  - Accuracy: 0.6110
  - Precision: 0.2520
  - Recall: 0.6578
  - F1: 0.3644
  - ROC-AUC: 0.6655
- Strongest classical model by F1: Logistic Regression, F1 0.3580
- Random Forest had the strongest classical ROC-AUC in this run, 0.6792, but
  lower F1 than Logistic Regression.
- Teacher DL baseline predicted no churn cases at threshold 0.5, giving F1 0.0
  despite ROC-AUC 0.6597. This supports the improved section's use of class
  weighting and threshold tuning.

## Optional Next Actions After Final Notebook Packaging

1. Update backend prediction schemas only if API/UI deployment is required:
   - CDC diabetes features
   - house categorical/location fields
   - customer behavior aggregate features
2. Update web/mobile forms only after the backend schema is finalized.
3. Optionally re-run and save notebooks inside Jupyter if the submission must
   contain rich output cells.
4. Revisit `A02_CT_tupv.879.pdf` only if better OCR/PDF tooling is needed for
   exact visual/sample text extraction.

## Phase 7 Update: Final Pipeline Packaging and QA

Files updated in Phase 7:

- `pipeline/diabetes_pipeline.ipynb`
- `pipeline/house_price_pipeline.ipynb`
- `pipeline/customer_behavior_pipeline.ipynb`
- `PIPELINE_UPGRADE_PLAN.md`
- `README.md`

Final artifact folders created:

- `pipeline/diabetes/`
- `pipeline/house_price/`
- `pipeline/customer_behavior/`

Each artifact folder now contains:

- selected model
- fitted preprocessing object
- `metadata.json`
- `feature_schema.json`
- `demo_input.json`
- `demo_prediction.json`
- `final_comparison.csv`
- `dl_comparison.csv`

Artifact validation:

- All three notebooks executed top-to-bottom from fresh namespaces using
  `backend/.venv/Scripts/python.exe`.
- Artifacts were created by the notebooks, not hand-written independently.
- Each saved preprocessor/model pair was loaded back from disk and used for a
  demo prediction.
- Metadata, feature schema, demo input, and demo prediction JSON files were
  parsed successfully.
- Final comparison CSV files contain exactly six rows and exclude
  `Teacher DL Baseline`.
- No normal artifact JSON requires an absolute `C:/Users/...` path.

Final selected models:

- Diabetes: `Improved DNN`
  - F1: 0.7712
  - ROC-AUC: 0.8192
- House Price: `Improved DNN`
  - RMSE: 1.4169 billion VND
  - R2: 0.5799
- Customer Behavior: `Improved DNN`
  - F1: 0.3644
  - ROC-AUC: 0.6655

## Final Verification for This Run

- Diabetes selected dataset is resolvable locally.
- House selected dataset is resolvable locally.
- Customer selected dataset files are resolvable locally.
- Diabetes target `Diabetes_binary` is sensible for binary classification.
- House target `Price_BillionVND` is sensible for regression.
- Customer target `is_churned` is sensible as the primary supervised behavior
  prediction target; interest discovery remains an interpretation task.
- Final 6-model comparison is implemented and asserted for all three notebooks.
- Teacher DL baseline characteristics have been identified from the local slide
  PDF and preserved in notebook baseline sections.
- Phase 4-6 notebooks are valid `.ipynb` JSON files and all code cells compile
  syntactically.
- All three notebooks executed end-to-end with model fitting, DL training,
  metrics calculation, and Matplotlib plot code paths.

## Unresolved Issues

- `A02_CT_anhtt.053.ipynb` is currently absent from the project root, although
  the three split notebooks under `pipeline/` are present.
- `A02_CT_tupv.879.pdf` needs better OCR/PDF tooling if we need exact text
  extraction from the sample. Current extraction is too degraded to quote or
  analyze deeply.
- The final deployment UI/API may need schema updates after the diabetes dataset
  replacement.
- Current notebooks were executed through a script runner, not saved with rich
  output cells. If the instructor wants visible outputs inside `.ipynb`, rerun
  and save the notebooks in Jupyter before submission.
