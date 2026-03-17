from __future__ import annotations

from typing import Any

PART_MATCH_SCORE = 20
KEY_SYMPTOM_SCORE = 20
SECONDARY_SYMPTOM_SCORE = 10
UNMATCHED_SYMPTOM_PENALTY = 5


def confidence_label(confidence: float) -> str:
    if confidence >= 80:
        return "High"
    if confidence >= 60:
        return "Moderate"
    if confidence >= 40:
        return "Low"
    return "Weak"


def score_disease(
    selected_part: str,
    selected_symptoms: list[str],
    disease: dict[str, Any],
) -> dict[str, Any]:
    score = 0
    matched_key: list[str] = []
    matched_secondary: list[str] = []
    unmatched: list[str] = []

    part_match = selected_part in disease["plant_parts"]
    if part_match:
        score += PART_MATCH_SCORE

    for symptom in selected_symptoms:
        if symptom in disease["key_symptoms"]:
            score += KEY_SYMPTOM_SCORE
            matched_key.append(symptom)
        elif symptom in disease["secondary_symptoms"]:
            score += SECONDARY_SYMPTOM_SCORE
            matched_secondary.append(symptom)
        else:
            score -= UNMATCHED_SYMPTOM_PENALTY
            unmatched.append(symptom)

    score = max(score, 0)
    max_possible = (
        PART_MATCH_SCORE
        + len(disease["key_symptoms"]) * KEY_SYMPTOM_SCORE
        + len(disease["secondary_symptoms"]) * SECONDARY_SYMPTOM_SCORE
    )
    confidence = round((score / max_possible) * 100, 1) if max_possible else 0.0

    return {
        "score": score,
        "confidence": min(confidence, 100.0),
        "confidence_label": confidence_label(confidence),
        "part_match": part_match,
        "matched_key": matched_key,
        "matched_secondary": matched_secondary,
        "unmatched": unmatched,
    }
