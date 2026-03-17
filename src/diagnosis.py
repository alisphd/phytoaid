from __future__ import annotations

from typing import Any

from src.scoring import score_disease


def filter_candidate_diseases(crop: str, disease_db: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [disease for disease in disease_db if disease["crop"] == crop]


def diagnose(
    crop: str,
    plant_part: str,
    selected_symptoms: list[str],
    disease_db: list[dict[str, Any]],
    limit: int = 3,
) -> list[dict[str, Any]]:
    candidates = filter_candidate_diseases(crop, disease_db)
    results: list[dict[str, Any]] = []

    for disease in candidates:
        score_result = score_disease(plant_part, selected_symptoms, disease)
        results.append(
            {
                "crop": disease["crop"],
                "disease_name": disease["disease_name"],
                "pathogen_type": disease["pathogen_type"],
                "plant_parts": disease["plant_parts"],
                "short_description": disease["short_description"],
                "management": disease["management"],
                "severity_clues": disease["severity_clues"],
                **score_result,
            }
        )

    results.sort(key=lambda item: (-item["score"], -item["confidence"], item["disease_name"].lower()))
    return results[:limit]
