from __future__ import annotations

from typing import Any


def get_crop_record(crop_name: str, crops: list[dict[str, Any]]) -> dict[str, Any]:
    return next(crop for crop in crops if crop["name"] == crop_name)


def get_symptoms_for_crop_part(
    crop: str,
    plant_part: str,
    disease_db: list[dict[str, Any]],
    symptom_db: list[dict[str, Any]],
) -> list[str]:
    crop_diseases = [disease for disease in disease_db if disease["crop"] == crop]
    part_specific = [disease for disease in crop_diseases if plant_part in disease["plant_parts"]]
    relevant_profiles = part_specific or crop_diseases

    relevant_symptoms = {
        symptom
        for disease in relevant_profiles
        for symptom in disease["key_symptoms"] + disease["secondary_symptoms"]
    }
    return [item["name"] for item in symptom_db if item["name"] in relevant_symptoms]


def filter_selected_symptoms(selected_symptoms: list[str], allowed_symptoms: list[str]) -> list[str]:
    allowed = set(allowed_symptoms)
    return [symptom for symptom in selected_symptoms if symptom in allowed]


def render_markdown_list(items: list[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)
