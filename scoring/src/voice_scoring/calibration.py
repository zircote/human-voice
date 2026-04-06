"""Calibration: compare self-report dimension scores against observed values.

Cross-reference mapping (self-report dimension -> computational metric):
  - formality        -> formality_f_score  (normalized to 0-100)
  - complexity       -> flesch_kincaid_grade (normalized)
  - authority        -> liwc_clout
  - narrativity      -> liwc_analytical     (inverted)
  - emotional_tone   -> liwc_emotional_tone

For each dimension with both scores:
  - delta = self_report - observed
  - |delta| <= 10  -> "high" awareness
  - |delta| <= 25  -> "moderate" awareness
  - |delta| > 25   -> "blind_spot"

Compute overall_self_awareness as mean of per-dimension awareness scores.
"""

from __future__ import annotations

from typing import Any


# Mapping from self-report dimension to observed metric key.
CROSS_REFERENCE_MAP: dict[str, str] = {
    "formality": "formality_f_score",
    "complexity": "flesch_kincaid_grade",
    "authority": "liwc_clout",
    "narrativity": "liwc_analytical",
    "emotional_tone": "liwc_emotional_tone",
}

# Dimensions where the observed metric is inverted (higher observed = lower dimension).
INVERTED_METRICS: set[str] = {"narrativity"}

# Normalization ranges for observed metrics to map to 0-100.
# (metric_key, min_raw, max_raw)
OBSERVED_NORMALIZATION: dict[str, tuple[float, float]] = {
    "formality_f_score": (0.0, 100.0),      # Heylighen-Dewaele F-score: (pos-neg+100)/2 → ~30-70 range.
    "flesch_kincaid_grade": (0.0, 20.0),    # Grade 0-20 -> 0-100.
    "liwc_clout": (0.0, 100.0),             # Already 0-100.
    "liwc_analytical": (0.0, 100.0),        # Already 0-100.
    "liwc_emotional_tone": (0.0, 100.0),    # Already 0-100.
}

# Awareness thresholds.
HIGH_THRESHOLD = 10.0
MODERATE_THRESHOLD = 25.0

# Numeric score for each awareness level (for computing overall mean).
AWARENESS_SCORES: dict[str, float] = {
    "high": 100.0,
    "moderate": 60.0,
    "blind_spot": 20.0,
}


def _normalize_observed(metric_key: str, raw_value: float) -> float:
    """Normalize an observed metric value to 0-100."""
    lo, hi = OBSERVED_NORMALIZATION.get(metric_key, (0.0, 100.0))
    if hi == lo:
        return 50.0
    normalized = ((raw_value - lo) / (hi - lo)) * 100.0
    return max(0.0, min(100.0, normalized))


def _classify_awareness(abs_delta: float) -> str:
    """Classify delta into awareness level."""
    if abs_delta <= HIGH_THRESHOLD:
        return "high"
    if abs_delta <= MODERATE_THRESHOLD:
        return "moderate"
    return "blind_spot"


def calibrate(
    sr_scores: dict[str, Any],
    observed: dict[str, Any],
) -> dict[str, Any]:
    """Compare self-report scores against observed computational scores.

    Parameters
    ----------
    sr_scores:
        Output of ``score_self_report``.  Expects ``sr_scores["dimensions"]``
        dict mapping dimension names to score dicts with a ``"score"`` key.
    observed:
        Dict of observed metric values keyed by metric name
        (e.g. ``{"formality_f_score": 0.72, "flesch_kincaid_grade": 12.3, ...}``).

    Returns
    -------
    Calibration report dict with per-dimension entries and overall_self_awareness.
    """
    dimensions_sr = sr_scores.get("dimensions", {})
    per_dim: dict[str, Any] = {}
    awareness_scores: list[float] = []

    for dim, obs_key in CROSS_REFERENCE_MAP.items():
        sr_entry = dimensions_sr.get(dim, {})
        sr_score = sr_entry.get("score") if isinstance(sr_entry, dict) else None
        obs_raw = observed.get(obs_key)

        if sr_score is None or obs_raw is None:
            per_dim[dim] = {
                "self_report": sr_score,
                "observed_raw": obs_raw,
                "observed_normalized": None,
                "delta": None,
                "awareness": None,
                "direction": None,
            }
            continue

        obs_norm = _normalize_observed(obs_key, float(obs_raw))

        # Invert if needed (higher observed = lower dimension score).
        if dim in INVERTED_METRICS:
            obs_norm = 100.0 - obs_norm

        delta = sr_score - obs_norm
        abs_delta = abs(delta)
        awareness = _classify_awareness(abs_delta)

        direction: str | None = None
        if delta > HIGH_THRESHOLD:
            direction = "overestimate"
        elif delta < -HIGH_THRESHOLD:
            direction = "underestimate"

        per_dim[dim] = {
            "self_report": round(sr_score, 2),
            "observed_raw": obs_raw,
            "observed_normalized": round(obs_norm, 2),
            "delta": round(delta, 2),
            "awareness": awareness,
            "direction": direction,
        }
        awareness_scores.append(AWARENESS_SCORES[awareness])

    overall = round(sum(awareness_scores) / len(awareness_scores), 2) if awareness_scores else None

    return {
        "dimensions": per_dim,
        "overall_self_awareness": overall,
    }
