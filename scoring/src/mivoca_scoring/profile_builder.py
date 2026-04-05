"""Tier-weighted profile builder.

Merges self-report and observed scores using tier-based weighting:
  - Tier 1 (high SR reliability):    0.7 * SR + 0.3 * observed
  - Tier 2 (moderate):               0.5 * SR + 0.5 * observed
  - Tier 3 (weak SR):                0.3 * SR + 0.7 * observed
  - Tier 4 (SR not reliable):        0.0 * SR + 1.0 * observed

Distinctive-feature detection:
  - Compare each computational feature against population means.
  - Features > 1.5 SD from mean are "distinctive".

Voice stability map:
  - For dimensions measured in multiple modules, compute variance across contexts.
  - Low variance = stable_across_contexts; high variance = adapts_by_context.
"""

from __future__ import annotations

import math
from typing import Any


# ---------- Tier weights ----------

TIER_WEIGHTS: dict[int, tuple[float, float]] = {
    1: (0.7, 0.3),
    2: (0.5, 0.5),
    3: (0.3, 0.7),
    4: (0.0, 1.0),
}

# Default tier assignments for gold-standard dimensions.
# These can be overridden by calibration awareness levels.
DEFAULT_DIMENSION_TIERS: dict[str, int] = {
    "formality": 1,
    "emotional_tone": 1,
    "personality": 2,
    "complexity": 2,
    "audience_awareness": 2,
    "authority": 3,
    "narrativity": 3,
    "humor": 1,
}

# Default population estimates (mean, sd) for distinctive-feature detection.
# Overridable via config at interview.profile.population_means.
_DEFAULT_POPULATION_MEANS: dict[str, tuple[float, float]] = {
    "formality_f_score": (55.0, 10.0),
    "flesch_kincaid_grade": (10.0, 3.0),
    "liwc_clout": (55.0, 18.0),
    "liwc_analytical": (50.0, 20.0),
    "liwc_emotional_tone": (50.0, 20.0),
    "avg_sentence_length": (18.0, 5.0),
    "type_token_ratio": (0.65, 0.10),
    "hedge_word_rate": (0.02, 0.01),
    "passive_voice_rate": (0.08, 0.05),
    "contraction_rate": (0.04, 0.03),
}


def _load_population_means() -> dict[str, tuple[float, float]]:
    """Load population means from config, falling back to defaults."""
    means = dict(_DEFAULT_POPULATION_MEANS)
    try:
        from lib.config import get
        config_means = get("interview.profile.population_means", {})
        if isinstance(config_means, dict):
            for metric, vals in config_means.items():
                if isinstance(vals, dict) and "mean" in vals and "sd" in vals:
                    means[metric] = (float(vals["mean"]), float(vals["sd"]))
    except ImportError:
        pass
    return means


POPULATION_MEANS = _load_population_means()

# Stability threshold: variance below this is considered stable.
STABILITY_VARIANCE_THRESHOLD = 150.0  # On 0-100 scale, var < 150 ~ SD < ~12.


# ---------- Tier assignment ----------


def _tier_from_calibration(awareness: str | None) -> int | None:
    """Map calibration awareness level to tier number."""
    if awareness == "high":
        return 1
    if awareness == "moderate":
        return 2
    if awareness == "blind_spot":
        return 3
    return None


def _get_tier(
    dim: str,
    calibration: dict[str, Any] | None,
) -> int:
    """Determine the merging tier for a dimension."""
    if calibration:
        dim_cal = calibration.get("dimensions", {}).get(dim, {})
        tier = _tier_from_calibration(dim_cal.get("awareness"))
        if tier is not None:
            return tier
    return DEFAULT_DIMENSION_TIERS.get(dim, 2)


# ---------- Tier-weighted merging ----------


def _merge_scores(
    sr_score: float | None,
    obs_score: float | None,
    tier: int,
) -> dict[str, Any]:
    """Merge SR and observed scores using tier weights."""
    w_sr, w_obs = TIER_WEIGHTS.get(tier, (0.5, 0.5))

    if sr_score is not None and obs_score is not None:
        merged = w_sr * sr_score + w_obs * obs_score
    elif sr_score is not None:
        merged = sr_score
    elif obs_score is not None:
        merged = obs_score
    else:
        merged = None

    return {
        "merged_score": round(merged, 2) if merged is not None else None,
        "self_report_score": round(sr_score, 2) if sr_score is not None else None,
        "observed_score": round(obs_score, 2) if obs_score is not None else None,
        "tier": tier,
        "weight_sr": w_sr,
        "weight_obs": w_obs,
    }


# ---------- Distinctive-feature detection ----------


def detect_distinctive_features(
    observed: dict[str, Any] | None,
    population_means: dict[str, Any] | None = None,
    z_threshold: float = 1.5,
) -> list[dict[str, Any]]:
    """Identify features > z_threshold SDs from population mean.

    Parameters
    ----------
    observed:
        Dict of observed computational metric values.
    population_means:
        Optional override for population stats.
        Format: ``{"metric_key": {"mean": float, "sd": float}, ...}``
        or ``{"metric_key": [mean, sd], ...}``.
        Falls back to POPULATION_MEANS.

    Returns
    -------
    List of distinctive-feature dicts with metric, value, z_score, direction.
    """
    if not observed:
        return []

    pop = POPULATION_MEANS.copy()
    if population_means:
        for k, v in population_means.items():
            if isinstance(v, dict):
                pop[k] = (v.get("mean", 50.0), v.get("sd", 20.0))
            elif isinstance(v, (list, tuple)) and len(v) >= 2:
                pop[k] = (float(v[0]), float(v[1]))

    distinctive: list[dict[str, Any]] = []
    for metric, raw_val in observed.items():
        if not isinstance(raw_val, (int, float)):
            continue
        stats = pop.get(metric)
        if stats is None:
            continue
        mean, sd = stats
        if sd <= 0:
            continue
        z = (float(raw_val) - mean) / sd
        if abs(z) >= z_threshold:
            distinctive.append({
                "metric": metric,
                "value": raw_val,
                "population_mean": mean,
                "population_sd": sd,
                "z_score": round(z, 2),
                "direction": "above" if z > 0 else "below",
            })

    # Sort by absolute z-score descending.
    distinctive.sort(key=lambda d: abs(d["z_score"]), reverse=True)
    return distinctive


# ---------- Voice stability map ----------


def compute_voice_stability(
    responses: list[dict[str, Any]],
    dimension_mapping: dict[str, Any],
) -> dict[str, Any]:
    """Compute per-dimension stability across modules.

    For each dimension, collect responses grouped by module, normalize,
    compute per-module means, then compute variance of module means.

    Returns a dict mapping dimension to stability classification and stats.
    """
    from mivoca_scoring.self_report import normalize_response, _infer_question_type

    # Group items by dimension and module.
    dim_module_scores: dict[str, dict[str, list[float]]] = {}

    resp_lookup: dict[str, dict[str, Any]] = {}
    for r in responses:
        qid = r.get("question_id")
        if qid:
            resp_lookup[qid] = r

    for dim, item_ids in dimension_mapping.items():
        if not isinstance(item_ids, list):
            continue
        for qid in item_ids:
            resp = resp_lookup.get(qid)
            if resp is None:
                continue
            # Extract module from question_id (e.g. "M03-Q06" -> "M03").
            module = qid.split("-")[0] if "-" in qid else "unknown"
            qtype = _infer_question_type(resp)
            raw = resp.get("scale_value") or resp.get("semantic_differential_value") or resp.get("value")
            norm = normalize_response(raw, qtype)
            if norm is None:
                continue
            dim_module_scores.setdefault(dim, {}).setdefault(module, []).append(norm)

    stability: dict[str, Any] = {}
    for dim, modules in dim_module_scores.items():
        if len(modules) < 2:
            stability[dim] = {
                "classification": "insufficient_data",
                "module_count": len(modules),
                "variance": None,
            }
            continue

        # Compute per-module mean.
        module_means = [sum(vals) / len(vals) for vals in modules.values()]
        n = len(module_means)
        overall_mean = sum(module_means) / n
        variance = sum((m - overall_mean) ** 2 for m in module_means) / (n - 1) if n > 1 else 0.0

        classification = (
            "stable_across_contexts" if variance < STABILITY_VARIANCE_THRESHOLD
            else "adapts_by_context"
        )

        stability[dim] = {
            "classification": classification,
            "module_count": n,
            "module_means": {mod: round(sum(v) / len(v), 2) for mod, v in modules.items()},
            "variance": round(variance, 2),
            "sd": round(math.sqrt(variance), 2) if variance > 0 else 0.0,
        }

    return stability


# ---------- Main entry point ----------


def build_profile(
    sr_scores: dict[str, Any],
    observed: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    population_means: dict[str, Any] | None = None,
    responses: list[dict[str, Any]] | None = None,
    dimension_mapping: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the merged voice profile.

    Parameters
    ----------
    sr_scores:
        Output of ``score_self_report``.
    observed:
        Observed computational metric scores (optional).
    calibration:
        Output of ``calibrate`` (optional).
    population_means:
        Population statistics for distinctive-feature detection (optional).
    responses:
        Full response list for stability computation (optional).
    dimension_mapping:
        Dimension-to-item mapping for stability computation (optional).

    Returns
    -------
    Complete voice profile dict.
    """
    from mivoca_scoring.calibration import CROSS_REFERENCE_MAP, _normalize_observed, INVERTED_METRICS

    dimensions_sr = sr_scores.get("dimensions", {})
    merged_dimensions: dict[str, Any] = {}

    for dim in dimensions_sr:
        sr_entry = dimensions_sr[dim]
        sr_val = sr_entry.get("score") if isinstance(sr_entry, dict) else None

        # Get observed normalized value for this dimension if available.
        obs_val: float | None = None
        obs_key = CROSS_REFERENCE_MAP.get(dim)
        if observed and obs_key and obs_key in observed:
            obs_val = _normalize_observed(obs_key, float(observed[obs_key]))
            if dim in INVERTED_METRICS and obs_val is not None:
                obs_val = 100.0 - obs_val

        tier = _get_tier(dim, calibration)
        merged_dimensions[dim] = _merge_scores(sr_val, obs_val, tier)

    # Gap dimensions pass through unmerged.
    gap_dims = sr_scores.get("gap_dimensions", {})

    # Distinctive features from observed.
    distinctive = detect_distinctive_features(observed, population_means)

    # Voice stability.
    stability: dict[str, Any] = {}
    if responses and dimension_mapping:
        stability = compute_voice_stability(responses, dimension_mapping)

    return {
        "merged_dimensions": merged_dimensions,
        "gap_dimensions": gap_dims,
        "distinctive_features": distinctive,
        "voice_stability": stability,
    }


def assemble_voice_profile(
    build_result: dict[str, Any],
    session_id: str,
    writer_type: str,
    identity_summary: str,
    calibration_report: dict[str, Any] | None = None,
    semantic_differential: dict[str, float] | None = None,
    writing_sample_analysis: dict[str, Any] | None = None,
    session_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble a schema-compliant voice profile from build_profile output.

    Transforms the internal build_profile result into the structure required
    by voice-profile.schema.json, adding session metadata, identity summary,
    calibration, and writing sample analysis.
    """
    import uuid
    from datetime import datetime, timezone

    merged = build_result.get("merged_dimensions", {})
    gap = build_result.get("gap_dimensions", {})
    distinctive_raw = build_result.get("distinctive_features", [])
    stability = build_result.get("voice_stability", {})

    # Convert gold standard dimensions to schema format
    gold_standard: dict[str, Any] = {}
    for dim, data in merged.items():
        if isinstance(data, dict):
            gold_standard[dim] = {
                "score": data.get("composite", data.get("score", 0)),
                "self_report": data.get("self_report", 0),
                "observed": data.get("observed", 0),
                "confidence": data.get("confidence", 0.5),
            }

    # Convert gap dimensions to schema format
    gap_dims: dict[str, Any] = {}
    for dim, data in gap.items():
        if isinstance(data, dict):
            gap_dims[dim] = {
                "score": data.get("score", 0),
                "source": data.get("source", "self_report"),
            }

    # Convert distinctive features to strings
    distinctive_strings: list[str] = []
    for feat in distinctive_raw:
        if isinstance(feat, dict):
            desc = feat.get("description", feat.get("feature", ""))
            if not desc:
                desc = f"{feat.get('metric', 'unknown')}: {feat.get('value', '?')} (z={feat.get('z_score', '?')})"
            distinctive_strings.append(desc)
        elif isinstance(feat, str):
            distinctive_strings.append(feat)

    return {
        "$schema": "voice-profile/v1",
        "profile_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "session_id": session_id,
        "identity_summary": identity_summary,
        "writer_type": writer_type,
        "gold_standard_dimensions": gold_standard,
        "gap_dimensions": gap_dims,
        "semantic_differential": semantic_differential or {},
        "calibration": calibration_report or {},
        "distinctive_features": distinctive_strings,
        "voice_stability_map": {
            "stable_across_contexts": stability.get("stable_across_contexts", []),
            "adapts_by_context": stability.get("adapts_by_context", []),
        },
        "writing_sample_analysis": writing_sample_analysis or {},
        "metadata": session_metadata or {},
    }
