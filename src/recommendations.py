from __future__ import annotations

from typing import Any

MANAGEMENT_SECTIONS = (
    ("Cultural", "cultural"),
    ("Chemical", "chemical"),
    ("Preventive", "preventive"),
)


def format_management_sections(management: dict[str, list[str]]) -> list[dict[str, Any]]:
    return [{"label": label, "items": management.get(key, [])} for label, key in MANAGEMENT_SECTIONS]


def build_report_text(
    crop: str,
    plant_part: str,
    selected_symptoms: list[str],
    field_notes: str,
    severity_label: str,
    severity_score: int,
    results: list[dict[str, Any]],
) -> str:
    lines = [
        "PhytoAid Diagnosis Summary",
        "=========================",
        f"Crop: {crop}",
        f"Affected plant part: {plant_part}",
        f"Selected symptoms: {', '.join(selected_symptoms)}",
        f"Estimated severity: {severity_label} ({severity_score})",
    ]

    if field_notes.strip():
        lines.append(f"Field notes: {field_notes.strip()}")

    lines.append("")
    lines.append("Top disease suggestions")
    lines.append("-----------------------")

    for index, result in enumerate(results, start=1):
        lines.append(f"{index}. {result['disease_name']} ({result['confidence']}% confidence)")
        lines.append(f"   Pathogen type: {result['pathogen_type']}")
        lines.append(f"   Description: {result['short_description']}")
        if result["matched_key"]:
            lines.append(f"   Matched key symptoms: {', '.join(result['matched_key'])}")
        if result["matched_secondary"]:
            lines.append(f"   Matched secondary symptoms: {', '.join(result['matched_secondary'])}")
        for section in format_management_sections(result["management"]):
            items = "; ".join(section["items"]) if section["items"] else "None listed"
            lines.append(f"   {section['label']}: {items}")
        lines.append("")

    lines.append(
        "Disclaimer: This tool provides preliminary disease suggestions and should not replace laboratory diagnosis or expert consultation."
    )
    return "\n".join(lines)
