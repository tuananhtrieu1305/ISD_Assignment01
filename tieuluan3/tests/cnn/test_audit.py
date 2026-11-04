"""Read-only audit of already-saved validation predictions, no TEST forward."""

import numpy as np
import pytest

from scripts.verify_phase27 import verify_prediction
from src.ch03_cnn.image_cache import development_cache
from src.ch03_cnn.protocol import BASE
from src.common.contracts import read_json


@pytest.mark.parametrize("run", ["ch3_idrid_cnn_scratch_s17", "ch3_idrid_majority_s17"])
def test_saved_validation_metric_recomputes_exactly(run):
    selected = read_json(BASE / "runs" / run / "selection.json")
    cache, view = development_cache("ch3_idrid")
    ids = view.ids("validation")
    labels = np.asarray([cache.labels[cache.positions[key]] for key in ids])
    assert (
        verify_prediction(selected["validation_metrics"], selected["details"], ids, labels, run_id=run) == 64
    )
    with pytest.raises(ValueError, match="ID/order"):
        verify_prediction(selected["validation_metrics"], selected["details"], ids[::-1], labels, run_id=run)
