"""Synthetic observations exercise source transformations without raw edits."""

import numpy as np
import pandas as pd
import pytest

from src.common.eda_sources import gold_features, hourly_power, parse_cifar_classes, select_bis_panel


def test_cifar_metadata_allows_terminal_blank_line_but_keeps_ten_unique_classes():
    names = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
    assert parse_cifar_classes("\n".join(names) + "\n\n") == names


def test_cifar_metadata_rejects_missing_or_duplicate_class_names():
    with pytest.raises(ValueError):
        parse_cifar_classes("cat\ndog\n")
    with pytest.raises(ValueError):
        parse_cifar_classes("cat\n" * 10)


def test_gold_explanatory_prices_have_one_period_publication_lag():
    raw = pd.DataFrame(
        {
            "time": pd.date_range("2000-01-01", periods=3, freq="MS"),
            "gold": [100, 110, 120],
            "silver": [1, 2, 3],
            "platinum": [5, 6, 7],
            "crude_oil": [20, 30, 40],
        }
    )
    frame, features = gold_features(raw)
    assert frame.target.tolist() == [100, 110, 120]
    assert frame.gold.tolist() == [100, 110, 120]
    assert frame.silver_lag1.iloc[1] == 1
    assert "silver" not in features


def minute_fixture():
    times = pd.date_range("2007-01-01", periods=120, freq="min")
    frame = pd.DataFrame({"Date": times.strftime("%d/%m/%Y"), "Time": times.strftime("%H:%M:%S")})
    for name in (
        "Global_active_power",
        "Global_reactive_power",
        "Voltage",
        "Global_intensity",
        "Sub_metering_1",
        "Sub_metering_2",
        "Sub_metering_3",
    ):
        frame[name] = 1.0
    return frame


def test_power_hourly_requires_45_observed_minutes_and_never_fills_target():
    raw = minute_fixture()
    raw.loc[:15, "Global_active_power"] = np.nan
    result, features = hourly_power(raw)
    assert np.isnan(result.target.iloc[0])
    assert result.target.iloc[1] == 1.0
    assert "Global_active_power_missing" in features
    assert result.Global_active_power_missing.iloc[0] == 1


def test_power_45_minutes_is_valid_boundary():
    raw = minute_fixture()
    raw.loc[:14, "Global_active_power"] = np.nan
    result, _ = hourly_power(raw)
    assert result.target.iloc[0] == 1.0


def test_bis_only_nominal_index_not_real_or_yoy_and_80_observations():
    quarters = pd.period_range("2000Q1", periods=90, freq="Q")
    rows = []
    for economy, value, unit in [
        ("US", "N", "628"),
        ("US", "R", "628"),
        ("US", "N", "771"),
        ("XM", "N", "628"),
        ("VN", "N", "628"),
    ]:
        row = {"FREQ": "Q", "REF_AREA": economy, "VALUE": value, "UNIT_MEASURE": unit}
        row.update({str(q).replace("Q", "-Q"): float(i + 1) for i, q in enumerate(quarters)})
        if economy == "VN":
            for q in quarters[:20]:
                row[str(q).replace("Q", "-Q")] = np.nan
        rows.append(row)
    panel, features, audit = select_bis_panel(pd.DataFrame(rows))
    assert set(panel.series) == {"Q.US.N.628"}
    assert panel.target.notna().sum() == 90
    assert audit["retained_series"] == ["Q.US.N.628"]
    assert "country_US" in features


def test_bis_duplicate_economy_series_fails_closed():
    row = {"FREQ": "Q", "REF_AREA": "US", "VALUE": "N", "UNIT_MEASURE": "628"}
    row.update({f"{2000 + i // 4}-Q{i % 4 + 1}": i for i in range(80)})
    with pytest.raises(ValueError):
        select_bis_panel(pd.DataFrame([row, row]))
