"""Configurable lead scoring with derived underwriting signals."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import get_settings


@dataclass
class ScoreResult:
    score: int
    tier: str
    breakdown: dict[str, int]


def _income_range_from_amount(amount: int) -> str:
    if amount >= 500_000:
        return "500k_plus"
    if amount >= 350_000:
        return "350_500k"
    if amount >= 200_000:
        return "200_350k"
    if amount >= 100_000:
        return "100_200k"
    return "under_100k"


def _bmi_category(height_feet: int, height_inches: int, weight_lbs: int) -> str:
    total_inches = height_feet * 12 + height_inches
    if total_inches <= 0:
        return "unknown"
    bmi = (weight_lbs / (total_inches**2)) * 703
    if bmi < 18.5:
        return "underweight"
    if bmi < 25:
        return "normal"
    if bmi < 30:
        return "overweight"
    return "obese"


def _medical_complexity(conditions: list[str] | str) -> str:
    if isinstance(conditions, str):
        text = conditions.lower()
        if not text or "none reported" in text:
            return "none"
        parts = [p.strip() for p in conditions.split(";") if p.strip()]
        count = len(parts)
    else:
        items = [c for c in conditions if c and c.lower() != "none reported"]
        count = len(items)
    if count == 0:
        return "none"
    if count <= 2:
        return "low"
    return "high"


def _affordability_signal(income: int, expenses_range: str) -> str:
    if income <= 0:
        return "unknown"
    ratio_map = {
        "under_3k": 0.05,
        "3k_8k": 0.10,
        "8k_15k": 0.18,
        "15k_plus": 0.28,
        "not_sure": 0.12,
    }
    est_ratio = ratio_map.get(expenses_range, 0.12)
    # Premium target 1-3% of income — lower expense load = easier fit
    if est_ratio <= 0.08:
        return "strong"
    if est_ratio <= 0.15:
        return "moderate"
    return "weak"


def enrich_score_data(lead_data: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(lead_data)
    income = int(lead_data.get("annual_income_amount") or 0)
    enriched["annual_income_range"] = _income_range_from_amount(income)
    enriched["income_tier"] = enriched["annual_income_range"]
    enriched["bmi_category"] = _bmi_category(
        int(lead_data.get("height_feet") or 0),
        int(lead_data.get("height_inches") or 0),
        int(lead_data.get("weight_lbs") or 0),
    )
    conditions = lead_data.get("medical_conditions")
    if conditions is None and lead_data.get("medical_conditions_text"):
        conditions = lead_data["medical_conditions_text"]
    enriched["medical_complexity"] = _medical_complexity(conditions or [])
    enriched["affordability_signal"] = _affordability_signal(
        income, str(lead_data.get("monthly_expenses_range", "not_sure"))
    )
    return enriched


def load_scoring_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or get_settings().scoring_config_path
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def calculate_score(lead_data: dict[str, Any], config: dict[str, Any] | None = None) -> ScoreResult:
    cfg = config or load_scoring_config()
    enriched = enrich_score_data(lead_data)
    breakdown: dict[str, int] = {}
    total = 0

    for criterion in cfg.get("criteria", []):
        field = criterion["field"]
        weights = criterion.get("weights", {})
        raw = enriched.get(field, "")
        if isinstance(raw, bool):
            value = str(raw)
        else:
            value = str(raw)
        points = int(weights.get(value, weights.get(value.lower(), 0)))
        breakdown[field] = points
        total += points

    tiers = cfg.get("tiers", {"hot": 80, "warm": 50, "cold": 0})
    if total >= tiers.get("hot", 80):
        tier = "hot"
    elif total >= tiers.get("warm", 50):
        tier = "warm"
    else:
        tier = "cold"

    return ScoreResult(score=total, tier=tier, breakdown=breakdown)


def get_scoring_criteria_for_display() -> list[dict[str, Any]]:
    cfg = load_scoring_config()
    return [
        {
            "field": c["field"],
            "label": c.get("label", c["field"]),
            "weights": c.get("weights", {}),
        }
        for c in cfg.get("criteria", [])
    ]