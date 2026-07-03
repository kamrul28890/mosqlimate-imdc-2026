# Future Work — IMDC 2026 (Team Neural Earth)

The project's calendar-anchored roadmap: the competition **forecast phase**, the webinars, and the
**journal paper**, plus how improvements sequence against those milestones. This is the
higher-level companion to:
- `docs/IMPROVEMENTS.md` — the code/engineering/accuracy backlog (line-level, prioritized).
- `docs/PLAN.md` — the original phase 2–8 implementation plan (history).

## 0. Where we are

Validation phase **submitted and verified** (308/308 predictions across dengue/chikungunya ×
state/city; 64 tests passing; fully reproducible public repo). The next hard deadline is the
**forecast phase, 2026-09-10**. Everything below is oriented around that and the paper.

## 1. Key dates
*(Confirm against https://sprint.mosqlimate.org/calendar — dates shift.)*

| Date | Milestone |
|------|-----------|
| 2026-07-31 | Validation-round results webinar |
| **2026-09-10** | **Forecast-phase submission — true 2026–27 season** ← primary deadline |
| 2026-09-22 | Team methodology presentations |
| 2026-10-15 | Technical results webinar |
| 2026-10-30 | Public results webinar |
| (rolling) | Journal paper — PNAS-style, following Araujo et al. 2026 |

## 2. Workstream A — Forecast phase (the real 2026–27 forecast) · highest priority

The pipeline already generalizes — fold 4 was effectively a dry run for this. Steps:

1. **Data refresh.** Re-pull `data_imdc_2026` from the FTP / Mosqlimate API through **EW25 2026**
   (current data ends 2026-03-08); regenerate `data/raw/data_imdc_2026/CHECKSUMS.sha256`. Script it
   (IMPROVEMENTS §6.1) so it is one command.
2. **Population extrapolation** to 2026/2027 for incidence normalization and state aggregation
   (population data ends 2025; currently clipped to the last available year). Add a documented
   extrapolation (e.g. last-observed growth rate).
3. **Re-run** `make reproduce` with `train_cutoff = EW25 2026`; produce the full 2026–27 season
   forecast for all four tracks via `imdc/submission/forecast.py`.
4. **Validate + upload** to the *forecast* phase using the same tooling (`submission/validate.py`,
   `submission/upload.py`, `scripts/finish_upload.py`); reuse registered model **id 83**.
5. **Buffer.** Internal-complete by ~Sept 5, upload by Sept 8 — never the deadline day (the API was
   intermittently timing out during the validation upload).

## 3. Workstream B — Modeling improvements to land *before* the forecast phase

Prioritized for accuracy (details in IMPROVEMENTS.md §5):

- **ECMWF seasonal-climate features** (§5.1) — the one genuine *future* covariate signal for
  horizons ≤26 weeks; loaded nowhere today and likely the biggest untapped accuracy lever. **Do first.**
- **Hierarchical reconciliation** (state ↔ city ↔ national coherence, §5.2) — an accuracy gain and a
  clean methodological contribution for the paper.
- **Stacking / QRA ensemble** (§5.3) vs the current unweighted Vincentization, with the
  leave-one-fold-out weight-robustness check.
- **Sparse-series handling.** The degenerate zero-median fix (mean point estimate) already shipped
  for the city tracks — generalize it into a principled zero-inflated / hurdle option and unit-test it.
- **Deseasonalized climate-lag re-check** (§5.5) and **disease-specific chikungunya** features
  (§5.4, biennial dynamics) — chikungunya currently reuses the dengue recipe.

## 4. Workstream C — Engineering hardening (enables fast, safe iteration before September)

From IMPROVEMENTS.md, in order:
- **Loader caching** (§2.1) — ~3–5× faster everywhere; the single biggest speedup.
- **Model-weight persistence** (§2.4) — makes the forecast run seconds, not an hour.
- **EW53 season-week bug** (§1.1) — a real latent bug affecting 53-week years like 2026.
- **`Forecaster` protocol + remove dead params** (§3.1); **unify state/city + ensemble duplication**
  (§3.2); **one parametrized CLI** (§3.3); **fast synthetic-fixture tests + CI/ruff** (§4.1, §3.5).

## 5. Workstream D — The journal paper (PNAS-style)

Build on `paper/imdc_paper.tex`:
- **Main text:** finalize the 5-family + ensemble comparison; the headline **metric-disagreement**
  finding (raw-mean WIS vs scale-free relative-WIS pick different winners); calibration (CQR); the
  **hyperparameter-tuning negative result**; and the newly-discovered **degenerate-median /
  episodic-sparsity** finding as a methods note.
- **Figures:** keep `paper_wis_by_fold`, `paper_coverage`, `paper_relative_wis`; add a state-level
  **relative-WIS choropleth** (geopandas + `shape_muni.gpkg`) tied to the EDA's Köppen gradient.
- **SI appendix:** full WIS/CRPS math, feature list + frozen hyperparameters, DL architecture,
  mechanistic derivation, per-state/per-fold tables, ensemble-weight robustness, reproducibility
  statement (public repo + `RESULTS.md` provenance).
- **Sequencing:** draft Intro/Data/Methods now (data-independent); fill Results/Discussion after the
  forecast phase and once the 2025–26 season resolves enough to score fold 4; fold in comparanda
  from the July/October webinars; submit after the October results.

## 6. Workstream E — Evaluation & ops

- When organizers publish validation scores, compare our WIS/coverage to other teams and record it.
- **Re-score fold 4** when the 2025–26 season resolves (currently prospective/partial).
- Lightweight **experiment tracking** (IMPROVEMENTS §6.2) for the many upcoming model/feature variants.
- Keep the **EpiScanner** caveat visible: the API endpoint is still down (HTTP 500); the mechanistic
  model uses the local Richards reimplementation — revisit if the endpoint returns.

## 7. Suggested calendar

- **Now → ~Jul 25:** engineering hardening (Workstream C) + start ECMWF features; prep the Jul 31 webinar.
- **Late Jul → mid-Aug:** modeling improvements (ECMWF, reconciliation, stacking); write the data-refresh script.
- **Mid-Aug → Sep 5:** data refresh → re-run → generate/validate the 2026–27 forecast; freeze the model.
- **Sep 5–8:** upload the forecast phase (buffer before Sep 10). **Sep 22:** methodology presentation.
- **Sep → Oct:** paper Results/Discussion; **Oct 15 / Oct 30** webinars; finalize + submit the paper after.

## 8. Risks & dependencies

- Data-refresh availability (FTP/API) before the September run.
- API flakiness at upload time — mitigated by the idempotent `scripts/finish_upload.py`.
- Fold-4 resolution timing for the paper's headline numbers.
- EpiScanner endpoint still down.
- Population-extrapolation assumptions for 2026/2027.
