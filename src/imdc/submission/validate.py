"""Local pre-flight validation of a submission table.

Replicates the checks in mosqlient.registry.schema.PredictionDataRow /
Prediction so failures are caught for free, before any network round-trip:
  - required columns present
  - dates are the exact expected EW41..EW40 Sunday-dated weeks, no gaps
  - all values finite and >= 0
  - nested bounds: lower_95 <= lower_90 <= lower_80 <= lower_50 <= pred
                   <= upper_50 <= upper_80 <= upper_90 <= upper_95
"""
import numpy as np
import pandas as pd

from imdc.config import QUANTILE_COLUMNS
from imdc.submission.build import SUBMISSION_COLUMNS, season_date_range

_NEST_ORDER = ["lower_95", "lower_90", "lower_80", "lower_50", "pred",
               "upper_50", "upper_80", "upper_90", "upper_95"]


class SubmissionError(ValueError):
    pass


def validate_submission(frame: pd.DataFrame, season_year: int, name: str = "submission") -> None:
    """Raise SubmissionError on the first problem found; return None if the table is valid."""
    missing_cols = set(SUBMISSION_COLUMNS) - set(frame.columns)
    if missing_cols:
        raise SubmissionError(f"{name}: missing columns {sorted(missing_cols)}")

    dates = pd.to_datetime(frame["date"])
    expected = season_date_range(season_year)
    if len(frame) != len(expected) or not (dates.to_numpy() == expected.to_numpy()).all():
        raise SubmissionError(
            f"{name}: dates do not match the expected EW41..EW40 weekly range "
            f"({len(frame)} rows vs {len(expected)} expected)"
        )

    vals = frame[QUANTILE_COLUMNS].to_numpy(dtype=float)
    if not np.isfinite(vals).all():
        n = int((~np.isfinite(vals)).sum())
        raise SubmissionError(f"{name}: {n} non-finite / missing prediction values")
    if (vals < 0).any():
        raise SubmissionError(f"{name}: negative prediction values present")

    ordered = frame[_NEST_ORDER].to_numpy(dtype=float)
    diffs = np.diff(ordered, axis=1)
    if (diffs < -1e-6).any():
        bad = int((diffs < -1e-6).any(axis=1).sum())
        raise SubmissionError(f"{name}: nested-bound order violated in {bad} row(s)")


def is_valid(frame: pd.DataFrame, season_year: int) -> bool:
    try:
        validate_submission(frame, season_year)
        return True
    except SubmissionError:
        return False
