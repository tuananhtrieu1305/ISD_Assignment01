import numpy as np
import pytest

from src.ch02_ml.baselines import PortableBaseline, fit_baseline


@pytest.mark.parametrize(
    "name,task",
    [
        ("majority", "binary"),
        ("logistic_regression", "binary"),
        ("random_forest", "binary"),
        ("median", "mse"),
        ("ridge", "mse"),
        ("random_forest", "mse"),
    ],
)
def test_portable_models_match_sklearn_without_pickle(name, task):
    x = np.random.default_rng(42).normal(size=(60, 3)).astype("float32")
    y = (x[:, 0] > 0).astype("float32") if task == "binary" else x[:, 0] * 2 + x[:, 1]
    fitted, portable = fit_baseline(
        name,
        x,
        y,
        task,
        seed=17,
        settings={"n_estimators": 5, "max_depth": 4, "min_samples_leaf": 2, "n_jobs": 1},
    )
    clone = PortableBaseline(portable.metadata, portable.arrays)
    expected = fitted.predict_proba(x) if task == "binary" else fitted.predict(x).reshape(-1, 1)
    np.testing.assert_allclose(clone.predict(x), expected, atol=1e-6, rtol=1e-6)
    with pytest.raises(ValueError):
        clone.predict(x[:, :2])
