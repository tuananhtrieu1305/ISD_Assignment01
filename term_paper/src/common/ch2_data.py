"""Rebuild the three Chapter 2 model matrices under the locked protocol."""

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .ch2_protocol import split_key_digest, validate_split_keys


SEED = 42


@dataclass
class PreparedDataset:
    dataset_id: str
    task: str
    x: dict
    y_model: dict
    y_true: dict
    keys: dict
    preprocessor: object
    raw_feature_names: list
    transformed_feature_names: list
    class_weight: dict | None
    target_transform: dict | None
    source_paths: list

    @property
    def split_sha256(self):
        return split_key_digest(self.keys)

    def inverse_target(self, values):
        values = np.asarray(values, dtype=float)
        if self.target_transform is None:
            return values
        if self.target_transform.get("name") != "standardized_log1p":
            raise ValueError("Unsupported target transform")
        mean = float(self.target_transform["mean"])
        std = float(self.target_transform["std"])
        return np.expm1(values * std + mean)


def _one_hot(min_frequency):
    return OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=True,
        min_frequency=min_frequency,
    )


def _dense(matrix):
    if hasattr(matrix, "toarray"):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def _split_positions(y, task):
    positions = np.arange(len(y))
    stratify = y if task == "binary" else None
    dev, test = train_test_split(
        positions,
        test_size=0.20,
        random_state=SEED,
        stratify=stratify,
    )
    dev_stratify = np.asarray(y)[dev] if task == "binary" else None
    train, val = train_test_split(
        dev,
        test_size=0.20,
        random_state=SEED,
        stratify=dev_stratify,
    )
    return {"train": train, "val": val, "test": test}


def _finalize(
    dataset_id,
    task,
    x_frame,
    y,
    keys,
    preprocessor,
    raw_feature_names,
    source_paths,
    class_weight=False,
    transform_target=False,
):
    x_frame = x_frame.reset_index(drop=True)
    y = np.asarray(y)
    keys = np.asarray(keys).astype(str)
    split_positions = _split_positions(y, task)
    preprocessor.fit(x_frame.iloc[split_positions["train"]])
    x = {
        name: _dense(preprocessor.transform(x_frame.iloc[positions]))
        for name, positions in split_positions.items()
    }
    split_keys = {
        name: keys[positions] for name, positions in split_positions.items()
    }
    validate_split_keys(split_keys, expected_total=len(keys))
    y_true = {
        name: np.asarray(y[positions], dtype=np.float32).reshape(-1)
        for name, positions in split_positions.items()
    }
    target_transform = None
    if transform_target:
        log_train = np.log1p(y_true["train"].astype(float))
        target_mean = float(log_train.mean())
        target_std = float(log_train.std())
        if target_std <= 0:
            raise ValueError("Target standard deviation must be positive")
        target_transform = {
            "name": "standardized_log1p",
            "mean": target_mean,
            "std": target_std,
        }
        y_model = {
            name: ((np.log1p(values.astype(float)) - target_mean) / target_std).astype(
                np.float32
            )
            for name, values in y_true.items()
        }
    else:
        y_model = {name: values.copy() for name, values in y_true.items()}
    weights = None
    if class_weight:
        counts = np.bincount(y_true["train"].astype(int), minlength=2)
        weights = {
            0: float(len(y_true["train"]) / (2.0 * counts[0])),
            1: float(len(y_true["train"]) / (2.0 * counts[1])),
        }
    try:
        transformed_feature_names = preprocessor.get_feature_names_out().tolist()
    except (AttributeError, ValueError):
        transformed_feature_names = [f"feature_{index}" for index in range(x["train"].shape[1])]
    return PreparedDataset(
        dataset_id=dataset_id,
        task=task,
        x=x,
        y_model=y_model,
        y_true=y_true,
        keys=split_keys,
        preprocessor=preprocessor,
        raw_feature_names=list(raw_feature_names),
        transformed_feature_names=transformed_feature_names,
        class_weight=weights,
        target_transform=target_transform,
        source_paths=[str(Path(path)) for path in source_paths],
    )


def _prepare_diabetes(workspace):
    path = workspace / "datasets" / "diabetes" / "diabetes.csv"
    raw = pd.read_csv(path)
    target = "Diabetes_binary"
    numeric = raw.apply(pd.to_numeric, errors="coerce")
    keep = ~numeric.duplicated()
    cleaned = numeric.loc[keep].copy()
    keys = np.array([f"diabetes:{index}" for index in cleaned.index])
    cleaned = cleaned.reset_index(drop=True)
    cleaned[target] = cleaned[target].astype(int)
    features = [column for column in cleaned.columns if column != target]
    preprocessor = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                features,
            )
        ],
        remainder="drop",
    )
    return _finalize(
        "ch2_diabetes_binary",
        "binary",
        cleaned[features],
        cleaned[target],
        keys,
        preprocessor,
        features,
        [path],
    )


def _normalize_text_value(value):
    if pd.isna(value):
        return "Unknown"
    text = re.sub(r"\s+", " ", str(value).strip()).strip(".")
    return text if text else "Unknown"


def _parse_number(value):
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)
    match = re.search(r"[-+]?\d*\.?\d+", str(value).lower().strip().replace(",", "."))
    return float(match.group(0)) if match else np.nan


def _parse_price(value, area):
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)
    text = str(value).lower().strip().replace(",", ".")
    number = _parse_number(text)
    if np.isnan(number):
        return np.nan
    if "triệu/m" in text or "tr/m" in text:
        return number * area / 1000.0 if area is not None and area > 0 else np.nan
    if "triệu" in text:
        return number / 1000.0
    return number


def _split_address(address):
    parts = [
        _normalize_text_value(part)
        for part in str(address).split(",")
        if _normalize_text_value(part) != "Unknown"
    ]
    city = parts[-1] if len(parts) >= 1 else "Unknown"
    district = parts[-2] if len(parts) >= 2 else "Unknown"
    ward_or_street = parts[-3] if len(parts) >= 3 else "Unknown"
    city = {
        "Hà Nội.": "Hà Nội",
        "TP. Hồ Chí Minh": "Hồ Chí Minh",
        "Tp Hồ Chí Minh": "Hồ Chí Minh",
    }.get(city, city)
    return pd.Series(
        {"city": city, "district": district, "ward_or_street": ward_or_street}
    )


def _prepare_housing(workspace):
    path = workspace / "datasets" / "housing_price" / "vietnam_housing_dataset.csv"
    raw = pd.read_csv(path)
    frame = raw.copy()
    frame["Area_m2"] = frame["Area"].apply(_parse_number)
    frame["Price_BillionVND"] = [
        _parse_price(price, area) for price, area in zip(frame["Price"], frame["Area_m2"])
    ]
    frame["Frontage_m"] = frame["Frontage"].apply(_parse_number)
    frame["Access_Road_m"] = frame["Access Road"].apply(_parse_number)
    for column in ["Floors", "Bedrooms", "Bathrooms"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    locations = frame["Address"].apply(_split_address)
    frame = pd.concat([frame, locations], axis=1)
    categorical = [
        "Legal status",
        "Furniture state",
        "House direction",
        "Balcony direction",
        "city",
        "district",
        "ward_or_street",
    ]
    for column in categorical:
        frame[column] = frame[column].apply(_normalize_text_value)
    valid = (
        frame["Price_BillionVND"].notna()
        & frame["Area_m2"].notna()
        & (frame["Price_BillionVND"] > 0)
        & (frame["Area_m2"] >= 10)
        & (frame["Area_m2"] <= 1000)
    )
    cleaned = frame.loc[valid].copy()
    keys = np.array([f"housing:{index}" for index in cleaned.index])
    cleaned = cleaned.reset_index(drop=True)
    numeric_features = [
        "Area_m2",
        "Frontage_m",
        "Access_Road_m",
        "Floors",
        "Bedrooms",
        "Bathrooms",
    ]
    categorical_features = [
        "city",
        "district",
        "Legal status",
        "Furniture state",
        "House direction",
        "Balcony direction",
    ]
    features = numeric_features + categorical_features
    preprocessor = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        (
                            "imputer",
                            SimpleImputer(strategy="constant", fill_value="Unknown"),
                        ),
                        ("onehot", _one_hot(min_frequency=20)),
                    ]
                ),
                categorical_features,
            ),
        ],
        remainder="drop",
    )
    return _finalize(
        "ch2_vietnam_housing",
        "regression",
        cleaned[features],
        cleaned["Price_BillionVND"],
        keys,
        preprocessor,
        features,
        [path],
        transform_target=True,
    )


def _top_value(series):
    values = series.dropna().astype(str)
    return "Unknown" if values.empty else values.value_counts().idxmax()


def _prepare_customer(workspace):
    directory = workspace / "datasets" / "customer_behavior"
    paths = {
        name: directory / f"{name}.csv"
        for name in ("customers", "products", "transactions", "sessions", "reviews")
    }
    customers = pd.read_csv(paths["customers"])
    products = pd.read_csv(paths["products"])
    transactions = pd.read_csv(paths["transactions"])
    sessions = pd.read_csv(paths["sessions"])
    reviews = pd.read_csv(paths["reviews"])
    customers["signup_date"] = pd.to_datetime(customers["signup_date"], errors="coerce")
    transactions["transaction_date"] = pd.to_datetime(
        transactions["transaction_date"], errors="coerce"
    )
    sessions["session_date"] = pd.to_datetime(sessions["session_date"], errors="coerce")
    reviews["review_date"] = pd.to_datetime(reviews["review_date"], errors="coerce")
    latest = max(
        transactions["transaction_date"].max(),
        sessions["session_date"].max(),
        reviews["review_date"].max(),
    )
    cutoff = latest - pd.Timedelta(days=90)
    observation_start = min(
        transactions["transaction_date"].min(),
        sessions["session_date"].min(),
        reviews["review_date"].min(),
    )
    no_activity_days = int((cutoff - observation_start).days) + 31
    transactions = transactions[transactions["transaction_date"] <= cutoff].copy()
    sessions = sessions[sessions["session_date"] <= cutoff].copy()
    reviews = reviews[reviews["review_date"] <= cutoff].copy()
    customers["is_churned"] = customers["is_churned"].astype(int)

    tx_prod = transactions.merge(
        products[["product_id", "category", "brand"]], on="product_id", how="left"
    )
    completed = tx_prod[tx_prod["status"] == "completed"].copy()
    tx_basic = tx_prod.groupby("customer_id").agg(
        total_transactions=("transaction_id", "count"),
        total_quantity=("quantity", "sum"),
        avg_discount=("discount_applied", "mean"),
        avg_shipping_cost=("shipping_cost", "mean"),
        last_transaction_date=("transaction_date", "max"),
    )
    status_counts = tx_prod.pivot_table(
        index="customer_id",
        columns="status",
        values="transaction_id",
        aggfunc="count",
        fill_value=0,
    ).rename(columns=lambda value: f"{value}_transactions")
    tx_completed = completed.groupby("customer_id").agg(
        completed_orders=("transaction_id", "count"),
        total_spent=("total_amount", "sum"),
        avg_order_value=("total_amount", "mean"),
        category_diversity=("category", "nunique"),
        brand_diversity=("brand", "nunique"),
        top_category=("category", _top_value),
        top_brand=("brand", _top_value),
    )
    top_categories = completed["category"].value_counts().head(8).index.tolist()
    category_spend = (
        completed[completed["category"].isin(top_categories)]
        .pivot_table(
            index="customer_id",
            columns="category",
            values="total_amount",
            aggfunc="sum",
            fill_value=0,
        )
        .rename(
            columns=lambda value: "spend_category_"
            + re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_").lower()
        )
    )
    tx_features = (
        tx_basic.join(status_counts, how="outer")
        .join(tx_completed, how="outer")
        .join(category_spend, how="outer")
    )
    session_features = sessions.groupby("customer_id").agg(
        session_count=("session_id", "count"),
        avg_session_duration=("duration_seconds", "mean"),
        total_pages_viewed=("pages_viewed", "sum"),
        avg_pages_viewed=("pages_viewed", "mean"),
        conversion_rate=("converted", "mean"),
        bounce_rate=("bounced", "mean"),
        cart_additions_total=("cart_additions", "sum"),
        cart_additions_avg=("cart_additions", "mean"),
        device_diversity=("device", "nunique"),
        channel_diversity=("channel", "nunique"),
        top_device=("device", _top_value),
        top_channel=("channel", _top_value),
        last_session_date=("session_date", "max"),
    )
    reviews["review_text_clean"] = reviews["review_text"].fillna("").astype(str).str.lower()
    review_features = reviews.groupby("customer_id").agg(
        review_count=("review_id", "count"),
        avg_rating=("rating", "mean"),
        low_rating_share=("rating", lambda values: (values <= 2).mean()),
        verified_review_share=("verified_purchase", "mean"),
        helpful_votes_total=("helpful_votes", "sum"),
        review_text_all=("review_text_clean", lambda values: " ".join(values.astype(str))),
        last_review_date=("review_date", "max"),
    )
    features = (
        customers.drop(columns=["lifetime_value"])
        .set_index("customer_id")
        .join([tx_features, session_features, review_features], how="left")
    )
    features["customer_tenure_days"] = (cutoff - features["signup_date"]).dt.days.clip(
        lower=0
    )
    features["days_since_last_transaction"] = (
        cutoff - features["last_transaction_date"]
    ).dt.days
    features["days_since_last_session"] = (cutoff - features["last_session_date"]).dt.days
    features["days_since_last_review"] = (cutoff - features["last_review_date"]).dt.days
    features = features.reset_index()
    category_features = [
        column for column in features.columns if column.startswith("spend_category_")
    ]
    numeric_features = [
        "age",
        "email_opt_in",
        "has_app",
        "customer_tenure_days",
        "total_transactions",
        "total_quantity",
        "avg_discount",
        "avg_shipping_cost",
        "completed_orders",
        "total_spent",
        "avg_order_value",
        "category_diversity",
        "brand_diversity",
        "cancelled_transactions",
        "completed_transactions",
        "pending_transactions",
        "refunded_transactions",
        "session_count",
        "avg_session_duration",
        "total_pages_viewed",
        "avg_pages_viewed",
        "conversion_rate",
        "bounce_rate",
        "cart_additions_total",
        "cart_additions_avg",
        "device_diversity",
        "channel_diversity",
        "review_count",
        "avg_rating",
        "low_rating_share",
        "verified_review_share",
        "helpful_votes_total",
        "days_since_last_transaction",
        "days_since_last_session",
        "days_since_last_review",
    ] + category_features
    categorical_features = [
        "gender",
        "country",
        "segment",
        "top_category",
        "top_brand",
        "top_device",
        "top_channel",
    ]
    text_feature = "review_text_all"
    all_features = numeric_features + categorical_features + [text_feature]
    for column in numeric_features:
        if column not in features:
            features[column] = 0
    zero_fill = [
        column
        for column in numeric_features
        if any(
            token in column
            for token in (
                "count",
                "total",
                "orders",
                "transactions",
                "quantity",
                "spent",
                "votes",
                "spend_category",
            )
        )
        or column.endswith("_rate")
        or column.endswith("_share")
        or column.endswith("_diversity")
    ]
    zero_fill += [
        "avg_discount",
        "avg_shipping_cost",
        "avg_order_value",
        "avg_session_duration",
        "avg_pages_viewed",
        "cart_additions_avg",
        "avg_rating",
    ]
    features[sorted(set(zero_fill))] = features[sorted(set(zero_fill))].fillna(0)
    recency = [
        "days_since_last_transaction",
        "days_since_last_session",
        "days_since_last_review",
    ]
    features[recency] = features[recency].fillna(no_activity_days)
    for column in categorical_features:
        features[column] = features[column].fillna("Unknown").astype(str)
    features[text_feature] = features[text_feature].fillna("").astype(str)
    preprocessor = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        (
                            "imputer",
                            SimpleImputer(strategy="constant", fill_value="Unknown"),
                        ),
                        ("onehot", _one_hot(min_frequency=10)),
                    ]
                ),
                categorical_features,
            ),
            (
                "text",
                TfidfVectorizer(
                    max_features=300,
                    min_df=3,
                    ngram_range=(1, 2),
                    stop_words="english",
                ),
                text_feature,
            ),
        ],
        remainder="drop",
    )
    return _finalize(
        "ch2_ecommerce_behavior",
        "binary",
        features[all_features],
        features["is_churned"],
        features["customer_id"],
        preprocessor,
        all_features,
        list(paths.values()),
        class_weight=True,
    )


def prepare_dataset(workspace, dataset_id):
    workspace = Path(workspace).resolve()
    loaders = {
        "ch2_diabetes_binary": _prepare_diabetes,
        "ch2_vietnam_housing": _prepare_housing,
        "ch2_ecommerce_behavior": _prepare_customer,
    }
    if dataset_id not in loaders:
        raise ValueError(f"Unknown Chapter 2 dataset: {dataset_id}")
    return loaders[dataset_id](workspace)
