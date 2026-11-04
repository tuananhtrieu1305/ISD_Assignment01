"""Schema checks use tiny synthetic fixtures, never substitute them for real data."""

import pandas as pd
import pytest

from src.common.acquisition import AcquisitionError
from src.common.source_inspection import column_contracts, normalize_column, require


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("SalePrice", "sale_price"),
        ("Sale_Price", "sale_price"),
        ("HighBP", "high_bp"),
        ("1st Flr SF", "v_1st_flr_sf"),
    ],
)
def test_column_aliases_are_explicit(raw, expected):
    assert normalize_column(raw) == expected


def test_ids_and_target_not_features():
    frame = pd.DataFrame({"ID": [1], "SalePrice": [123.0], "Street": ["Pave"]})
    columns = column_contracts(frame, target="sale_price", ids={"id"})
    assert [column["role"] for column in columns] == ["id", "target", "feature"]


def test_malformed_source_is_rejected():
    with pytest.raises(AcquisitionError):
        require(False, "wrong source")


def test_normalized_column_collision_is_rejected():
    with pytest.raises(AcquisitionError):
        column_contracts(pd.DataFrame({"SalePrice": [1], "Sale_Price": [2]}), "sale_price")
