"""Integration test for the city-level backtest path (optional challenge tracks)."""
import numpy as np
import pytest

from imdc.config import DENGUE_TARGET_CITIES, QUANTILE_COLUMNS
from imdc.data.folds import get_folds
from imdc.evaluation.baselines import ClimatologicalQuantileModel
from imdc.evaluation.city import run_city_backtest, score_city_backtest
from imdc.evaluation.postprocess import enforce_monotonicity

CITIES = DENGUE_TARGET_CITIES[:3]


@pytest.fixture(scope="module")
def city_scored():
    folds = [get_folds("dengue")[0]]
    preds = run_city_backtest(ClimatologicalQuantileModel, folds, "dengue", CITIES)
    return score_city_backtest(preds, folds, "dengue", CITIES)


def test_covers_requested_cities(city_scored):
    assert set(city_scored["uf"].unique()) == set(str(c) for c in CITIES)


def test_predictions_valid(city_scored):
    vals = city_scored[QUANTILE_COLUMNS].to_numpy()
    assert (vals >= 0).all() and np.isfinite(vals).all()
    assert enforce_monotonicity(city_scored).attrs["frac_rows_needing_reordering"] == pytest.approx(0.0)


def test_wis_finite(city_scored):
    assert np.isfinite(city_scored["wis"]).all() and (city_scored["wis"] >= 0).all()
