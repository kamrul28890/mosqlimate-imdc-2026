"""City-level backtesting (optional challenge tracks).

The state harness aggregates municipalities to UF; the city tracks instead
forecast a fixed set of target municipalities directly. We relabel each city's
geocode into the `uf` column so the geography-agnostic models (the baselines and
climatological-quantile) run unchanged. Feature-heavy models (LGBM/GRU) key
their covariates on state geography and would need municipal features, so the
city tracks use the baseline/climatological models here.
"""
import numpy as np
import pandas as pd

from imdc.config import QUANTILE_LEVEL_TO_COLUMN
from imdc.data.folds import cutoff_filter
from imdc.data.loaders import load_cases
from imdc.data.validate import assert_no_leakage
from imdc.evaluation.metrics import wis_decomposition, wis_from_intervals


def _city_cases(fold, disease: str, geocodes: list) -> pd.DataFrame:
    """Leakage-safe city case series (geocode relabeled to `uf`), date <= train_cutoff."""
    cases = cutoff_filter(load_cases(disease), fold.train_cutoff)
    assert_no_leakage(cases, fold.train_cutoff, name=f"fold{fold.id} city cases")
    sub = cases[cases["geocode"].isin(geocodes)][["geocode", "date", "casos"]].copy()
    sub = sub.rename(columns={"geocode": "uf"})
    sub["uf"] = sub["uf"].astype(str)
    return sub.sort_values(["uf", "date"]).reset_index(drop=True)


def _city_target_grid(fold, geocodes: list) -> pd.DataFrame:
    dates = pd.date_range(fold.target_start, fold.target_end, freq="W-SUN")
    hz = ((dates - fold.train_cutoff).days // 7).astype(int)
    frames = [pd.DataFrame({"uf": str(g), "date": dates, "horizon_weeks": hz}) for g in geocodes]
    return pd.concat(frames, ignore_index=True)


def run_city_backtest(model_factory, folds, disease: str, geocodes: list) -> pd.DataFrame:
    all_preds = []
    for fold in folds:
        train = _city_cases(fold, disease, geocodes)
        model = model_factory()
        model.fit(train, fold)
        grid = _city_target_grid(fold, geocodes)
        preds = model.predict(grid).merge(grid, on=["uf", "date"], how="left")
        preds["model"] = getattr(model, "name", model.__class__.__name__)
        preds["disease"] = disease
        preds["fold_id"] = fold.id
        all_preds.append(preds)
    return pd.concat(all_preds, ignore_index=True)


def score_city_backtest(preds_long: pd.DataFrame, folds, disease: str, geocodes: list) -> pd.DataFrame:
    fold_by_id = {f.id: f for f in folds}
    idx = ["model", "disease", "fold_id", "uf", "date", "horizon_weeks"]
    wide = preds_long.pivot_table(index=idx, columns="quantile_level", values="predicted_value")
    wide = wide.rename(columns=QUANTILE_LEVEL_TO_COLUMN).reset_index()

    obs_frames = []
    cases = load_cases(disease)
    for fid in wide["fold_id"].unique():
        f = fold_by_id[fid]
        w = cases[(cases["date"] >= f.target_start) & (cases["date"] <= f.target_end)
                  & (cases["geocode"].isin(geocodes))][["geocode", "date", "casos"]].copy()
        w = w.rename(columns={"geocode": "uf", "casos": "observed_value"})
        w["uf"] = w["uf"].astype(str)
        w["fold_id"] = fid
        obs_frames.append(w)
    observed = pd.concat(obs_frames, ignore_index=True)

    scored = wide.merge(observed, on=["fold_id", "uf", "date"], how="inner")
    y = scored["observed_value"].to_numpy()
    scored["wis"] = wis_from_intervals(scored, y)
    scored = pd.concat([scored, wis_decomposition(scored, y)], axis=1)
    scored["ae_median"] = np.abs(y - scored["pred"].to_numpy())
    for level in [50, 80, 90, 95]:
        scored[f"coverage_{level}"] = (y >= scored[f"lower_{level}"].to_numpy()) & (y <= scored[f"upper_{level}"].to_numpy())
    return scored
