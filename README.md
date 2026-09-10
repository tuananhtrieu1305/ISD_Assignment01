# Intelligent Systems Development Pipelines

This project contains three independent ML notebooks under `pipeline/`:

- `diabetes_pipeline.ipynb`: binary diabetes classification with CDC/BRFSS health indicators.
- `house_price_pipeline.ipynb`: Vietnam house-price regression in billion VND.
- `customer_behavior_pipeline.ipynb`: customer churn classification with behavior and interest-discovery features.

Each notebook follows the assignment flow:

`Raw Data -> Understand -> Clean -> Represent -> Learn -> Evaluate -> Persist`

The final comparison in each notebook contains exactly six main models: five classical ML models plus the improved NumPy Deep Learning model. The lecturer-based NumPy Deep Learning baseline is shown and evaluated separately first, then improved deliberately.

## Datasets

- Diabetes: `datasets/diabetes/diabetes.csv`
- House Price: `datasets/housing_price/vietnam_housing_dataset.csv`
- Customer Behavior: `datasets/customer_behavior/`

All normal notebook paths are relative to the project root.

## How To Run

Open the notebooks in Jupyter from the project root with a Python environment that has:

- `numpy`
- `pandas`
- `scikit-learn`
- `matplotlib`
- `joblib`

Run each notebook top-to-bottom from a fresh kernel:

- `pipeline/diabetes_pipeline.ipynb`
- `pipeline/house_price_pipeline.ipynb`
- `pipeline/customer_behavior_pipeline.ipynb`

## Saved Artifacts

Final pipeline artifacts are saved inside:

- `pipeline/diabetes/`
- `pipeline/house_price/`
- `pipeline/customer_behavior/`

Each artifact folder contains the selected model, preprocessor, metadata JSON, feature schema JSON, demo input JSON, demo prediction JSON, and final comparison CSV files.
