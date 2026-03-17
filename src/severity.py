from __future__ import annotations

from typing import Any


def calculate_severity(selected_symptoms: list[str], symptom_db: list[dict[str, Any]]) -> tuple[str, int]:
    symptom_weights = {item["name"]: item["weight"] for item in symptom_db}
    total = sum(symptom_weights.get(symptom, 0) for symptom in selected_symptoms)

    if total <= 3:
        return "Low", total
    if total <= 6:
        return "Moderate", total
    return "High", total


def build_severity_breakdown(selected_symptoms: list[str], symptom_db: list[dict[str, Any]]) -> list[dict[str, Any]]:
    symptom_lookup = {item["name"]: item for item in symptom_db}
    return [symptom_lookup[symptom] for symptom in selected_symptoms if symptom in symptom_lookup]
