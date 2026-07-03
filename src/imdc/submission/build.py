"""Build platform-compliant submission tables from model predictions.

A submission is one table per (disease, geography, season): weekly rows over the
full EW41-of-prior-year .. EW40-of-target-year range (Sunday-dated, no gaps),
with columns date, pred, lower_50/80/90/95, upper_50/80/90/95. Date-range logic
uses epiweeks.Week exactly as mosqlient.registry.schema does, so a table built
here matches the platform's own date validator bit-for-bit.
"""
import pandas as pd
from epiweeks import Week

from imdc.config import QUANTILE_COLUMNS, UF_TO_ADM1

SUBMISSION_COLUMNS = ["date"] + QUANTILE_COLUMNS


def season_date_range(season_year: int) -> pd.DatetimeIndex:
    """Sunday-dated weeks from EW41 of (season_year-1) through EW40 of season_year."""
    start = Week(season_year - 1, 41).startdate()
    end = Week(season_year, 40).startdate()
    return pd.date_range(start, end, freq="W-SUN")


def build_submission_frame(pred_wide: pd.DataFrame, uf: str, season_year: int) -> pd.DataFrame:
    """One state's submission table for one season, reindexed to the exact expected weeks.

    `pred_wide` must contain columns uf, date, and the 9 QUANTILE_COLUMNS. Missing
    weeks (if any) are surfaced as NaN rows so the validator catches them, rather
    than silently dropped.
    """
    expected = season_date_range(season_year)
    sub = pred_wide[pred_wide["uf"] == uf].copy()
    sub["date"] = pd.to_datetime(sub["date"])
    sub = sub.set_index("date").reindex(expected)
    sub.index.name = "date"
    out = sub[QUANTILE_COLUMNS].reset_index()
    return out


def adm1_for(uf: str) -> int:
    return UF_TO_ADM1[uf]
