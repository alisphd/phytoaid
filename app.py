from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_json
from src.diagnosis import diagnose
from src.helpers import (
    filter_selected_symptoms,
    get_crop_record,
    get_symptoms_for_crop_part,
    render_markdown_list,
)
from src.recommendations import build_report_text, format_management_sections
from src.severity import build_severity_breakdown, calculate_severity
from src.symptom_visuals import build_symptom_card_html, get_symptom_cards

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SYMPTOM_ASSETS_DIR = BASE_DIR / "assets" / "symptoms"


def load_app_data() -> tuple[list[dict], list[dict], list[dict]]:
    crops = load_json(DATA_DIR / "crops.json")
    symptoms = load_json(DATA_DIR / "symptoms.json")
    diseases = load_json(DATA_DIR / "diseases.json")
    return crops, symptoms, diseases


def initialize_state(crops: list[dict]) -> None:
    default_crop = crops[0]["name"]
    default_parts = crops[0]["plant_parts"]

    st.session_state.setdefault("selected_crop", default_crop)
    st.session_state.setdefault("selected_part", default_parts[0])
    st.session_state.setdefault("selected_symptoms", [])
    st.session_state.setdefault("field_notes", "")
    st.session_state.setdefault("diagnosis_requested", False)


def handle_crop_change(crops: list[dict]) -> None:
    crop_record = get_crop_record(st.session_state.selected_crop, crops)
    st.session_state.selected_part = crop_record["plant_parts"][0]
    st.session_state.selected_symptoms = []
    st.session_state.diagnosis_requested = False


def handle_part_change() -> None:
    st.session_state.selected_symptoms = []
    st.session_state.diagnosis_requested = False


def reset_inputs(crops: list[dict]) -> None:
    default_crop = crops[0]["name"]
    crop_record = get_crop_record(default_crop, crops)
    st.session_state.selected_crop = default_crop
    st.session_state.selected_part = crop_record["plant_parts"][0]
    st.session_state.selected_symptoms = []
    st.session_state.field_notes = ""
    st.session_state.diagnosis_requested = False


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(224, 206, 153, 0.22), transparent 32%),
                    linear-gradient(180deg, #f7f3ea 0%, #fdfcf7 100%);
            }
            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
            }
            .hero-card {
                background: linear-gradient(135deg, #304b23 0%, #637d3b 55%, #d2b165 100%);
                border-radius: 24px;
                color: #fffaf0;
                padding: 1.8rem;
                box-shadow: 0 14px 40px rgba(48, 75, 35, 0.18);
                margin-bottom: 1rem;
            }
            .hero-card h1 {
                margin: 0;
                font-size: 2.4rem;
                letter-spacing: 0.02em;
            }
            .hero-card p {
                margin: 0.65rem 0 0;
                max-width: 48rem;
                line-height: 1.6;
                color: rgba(255, 250, 240, 0.92);
            }
            .section-note {
                color: #59614e;
                font-size: 0.95rem;
            }
            .symptom-card {
                background: rgba(255, 252, 244, 0.94);
                border: 1px solid rgba(99, 125, 59, 0.16);
                border-radius: 22px;
                overflow: hidden;
                box-shadow: 0 12px 30px rgba(48, 75, 35, 0.08);
                margin-bottom: 1rem;
            }
            .symptom-card--selected {
                border-color: rgba(48, 75, 35, 0.42);
                box-shadow: 0 16px 34px rgba(48, 75, 35, 0.15);
                transform: translateY(-2px);
            }
            .symptom-card__visual {
                padding: 0.7rem 0.7rem 0 0.7rem;
            }
            .symptom-card__frame {
                aspect-ratio: 16 / 10;
                border-radius: 18px;
                overflow: hidden;
                background: #f6f2e7;
            }
            .symptom-card__svg,
            .symptom-card__img {
                width: 100%;
                height: 100%;
                display: block;
            }
            .symptom-card__img {
                object-fit: cover;
                background: #f6f2e7;
                transition: transform 180ms ease-out;
            }
            .symptom-card__body {
                padding: 0.85rem 1rem 1rem 1rem;
            }
            .symptom-card__badge {
                display: inline-block;
                padding: 0.2rem 0.55rem;
                border-radius: 999px;
                font-size: 0.74rem;
                font-weight: 700;
                letter-spacing: 0.03em;
                margin-bottom: 0.5rem;
            }
            .symptom-card__meta {
                float: right;
                margin-top: 0.12rem;
                color: #7c7f74;
                font-size: 0.76rem;
                font-weight: 600;
            }
            .symptom-card__body h4 {
                margin: 0 0 0.35rem 0;
                color: #304b23;
                font-size: 1rem;
            }
            .symptom-card__body p {
                margin: 0;
                color: #5e6654;
                font-size: 0.93rem;
                line-height: 1.5;
            }
            .symptom-card__credit {
                margin-top: 0.6rem;
                font-size: 0.78rem;
                color: #7a806f;
                line-height: 1.4;
            }
            .symptom-card__credit a {
                color: #4d6a34;
                text-decoration: none;
                border-bottom: 1px solid rgba(77, 106, 52, 0.28);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_overview_metrics(diseases: list[dict], symptoms: list[dict], crops: list[dict]) -> None:
    metric_cols = st.columns(3)
    metric_cols[0].metric("Crops", len(crops))
    metric_cols[1].metric("Disease profiles", len(diseases))
    metric_cols[2].metric("Tracked symptoms", len(symptoms))


def render_symptom_card_grid(
    symptom_names: list[str],
    symptoms: list[dict],
    selected_symptoms: list[str],
    crop: str,
) -> None:
    symptom_cards = get_symptom_cards(symptom_names, symptoms, SYMPTOM_ASSETS_DIR, selected_crop=crop)
    selected_set = set(selected_symptoms)
    columns = st.columns(3)

    for index, card in enumerate(symptom_cards):
        with columns[index % 3]:
            st.markdown(
                build_symptom_card_html(card, selected=card["name"] in selected_set),
                unsafe_allow_html=True,
            )


def render_symptom_reference(crop: str, symptom_names: list[str], selected_symptoms: list[str], symptoms: list[dict]) -> None:
    if not symptom_names:
        st.info("No symptom reference cards are available for the current crop and plant part.")
        return

    st.subheader("Symptom Reference")
    st.caption(
        "Cards below use local crop-specific photos bundled with this project, and each card includes a source link under the image."
    )

    if selected_symptoms:
        st.markdown("**Selected symptoms**")
        render_symptom_card_grid(selected_symptoms, symptoms, selected_symptoms, crop)

    remaining_symptoms = [name for name in symptom_names if name not in set(selected_symptoms)]

    with st.expander("Browse all symptom references for this crop and plant part", expanded=not selected_symptoms):
        if selected_symptoms and not remaining_symptoms:
            st.caption("All available symptoms for this crop and plant part are already shown above.")
        else:
            render_symptom_card_grid(remaining_symptoms if selected_symptoms else symptom_names, symptoms, selected_symptoms, crop)


def render_results(
    crop: str,
    plant_part: str,
    selected_symptoms: list[str],
    field_notes: str,
    symptoms: list[dict],
    diseases: list[dict],
) -> None:
    if not selected_symptoms:
        st.warning("Select at least one visible symptom to run a diagnosis.")
        return

    severity_label, severity_score = calculate_severity(selected_symptoms, symptoms)
    severity_breakdown = build_severity_breakdown(selected_symptoms, symptoms)
    results = diagnose(crop, plant_part, selected_symptoms, diseases)

    st.subheader("Diagnosis Results")

    summary_col, context_col = st.columns([1.1, 1.4])
    with summary_col:
        if severity_label == "Low":
            st.success(f"Estimated severity: {severity_label} ({severity_score})")
        elif severity_label == "Moderate":
            st.warning(f"Estimated severity: {severity_label} ({severity_score})")
        else:
            st.error(f"Estimated severity: {severity_label} ({severity_score})")

        st.caption("Severity is based on the combined weight of the selected symptoms.")
        st.markdown("**Severity drivers**")
        st.markdown(
            render_markdown_list(
                [f"{item['name']} ({item['category']}, weight {item['weight']})" for item in severity_breakdown]
            )
        )

    with context_col:
        st.markdown(f"**Crop:** {crop}")
        st.markdown(f"**Affected plant part:** {plant_part}")
        st.markdown(f"**Selected symptoms:** {', '.join(selected_symptoms)}")
        if field_notes.strip():
            st.markdown(f"**Field notes:** {field_notes.strip()}")
        st.caption("Confidence scores represent symptom match strength, not certainty.")

    if not results:
        st.info("No disease profiles were available for this crop selection.")
        return

    chart_df = pd.DataFrame(
        {
            "Disease": [result["disease_name"] for result in results],
            "Confidence": [result["confidence"] for result in results],
        }
    )

    chart = px.bar(
        chart_df,
        x="Confidence",
        y="Disease",
        orientation="h",
        range_x=[0, 100],
        color="Confidence",
        color_continuous_scale=["#d9bf7a", "#7f9a44", "#304b23"],
    )
    chart.update_layout(
        height=320,
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Confidence (%)",
        yaxis_title="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    chart.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(chart, use_container_width=True)

    if results[0]["confidence"] < 40:
        st.info(
            "The current symptom combination produced only weak matches. Refine the symptom list or confirm with an expert."
        )

    report_text = build_report_text(
        crop=crop,
        plant_part=plant_part,
        selected_symptoms=selected_symptoms,
        field_notes=field_notes,
        severity_label=severity_label,
        severity_score=severity_score,
        results=results,
    )
    st.download_button(
        "Download summary report",
        data=report_text,
        file_name="phytoaid_diagnosis_report.txt",
        mime="text/plain",
        use_container_width=True,
    )

    for index, result in enumerate(results, start=1):
        st.markdown("---")
        header_cols = st.columns([1.8, 1, 1])
        header_cols[0].markdown(f"### {index}. {result['disease_name']}")
        header_cols[1].metric("Confidence", f"{result['confidence']}%")
        header_cols[2].metric("Match level", result["confidence_label"])

        st.progress(min(int(result["confidence"]), 100))
        st.markdown(f"**Pathogen type:** {result['pathogen_type']}")
        st.markdown(f"**Description:** {result['short_description']}")

        match_reasons: list[str] = []
        if result["part_match"]:
            match_reasons.append(f"Plant part matched the profile for {plant_part}.")
        if result["matched_key"]:
            match_reasons.append(f"Matched key symptoms: {', '.join(result['matched_key'])}.")
        if result["matched_secondary"]:
            match_reasons.append(f"Matched secondary symptoms: {', '.join(result['matched_secondary'])}.")
        if not match_reasons:
            match_reasons.append("This profile remained in the top suggestions, but strong symptom overlap was limited.")

        st.markdown("**Why it matched**")
        st.markdown(render_markdown_list(match_reasons))

        recommendation_cols = st.columns(3)
        for column, section in zip(recommendation_cols, format_management_sections(result["management"])):
            with column:
                st.markdown(f"**{section['label']}**")
                st.markdown(render_markdown_list(section["items"]))

        if result["unmatched"]:
            st.caption(f"Selected symptoms not matched by this profile: {', '.join(result['unmatched'])}")


def render_library(diseases: list[dict], crop_names: list[str]) -> None:
    st.subheader("Disease Library")
    filter_col, search_col = st.columns([1, 1.5])
    with filter_col:
        selected_filter = st.selectbox("Filter by crop", ["All"] + crop_names, key="library_crop_filter")
    with search_col:
        search_term = st.text_input(
            "Search disease or symptom",
            placeholder="Try rust, wilt, lesions, or canker",
            key="library_search_term",
        ).strip()

    filtered = diseases
    if selected_filter != "All":
        filtered = [disease for disease in filtered if disease["crop"] == selected_filter]

    if search_term:
        needle = search_term.lower()
        filtered = [
            disease
            for disease in filtered
            if needle in disease["disease_name"].lower()
            or needle in disease["short_description"].lower()
            or any(needle in symptom.lower() for symptom in disease["key_symptoms"] + disease["secondary_symptoms"])
        ]

    library_df = pd.DataFrame(
        [
            {
                "Crop": disease["crop"],
                "Disease": disease["disease_name"],
                "Pathogen type": disease["pathogen_type"],
                "Plant parts": ", ".join(disease["plant_parts"]),
            }
            for disease in filtered
        ]
    )

    if library_df.empty:
        st.info("No disease profiles matched the current library filter.")
        return

    st.dataframe(library_df, use_container_width=True, hide_index=True)

    for disease in filtered:
        with st.expander(f"{disease['crop']} - {disease['disease_name']}"):
            st.markdown(f"**Pathogen type:** {disease['pathogen_type']}")
            st.markdown(f"**Plant parts affected:** {', '.join(disease['plant_parts'])}")
            st.markdown("**Key symptoms**")
            st.markdown(render_markdown_list(disease["key_symptoms"]))
            st.markdown("**Secondary symptoms**")
            st.markdown(render_markdown_list(disease["secondary_symptoms"]))
            st.markdown("**Management**")
            for section in format_management_sections(disease["management"]):
                st.markdown(f"**{section['label']}**")
                st.markdown(render_markdown_list(section["items"]))
            st.caption(disease["short_description"])


def render_about() -> None:
    st.subheader("About PhytoAid")
    st.markdown(
        """
        PhytoAid is a rule-based decision-support app for preliminary plant disease diagnosis.
        It compares the selected crop, plant part, and visible symptoms against a curated disease
        knowledge base, then ranks likely matches with transparent scoring rules.
        """
    )
    st.markdown("**How the diagnosis engine works**")
    st.markdown(
        render_markdown_list(
            [
                "Crop match is mandatory before a profile is considered.",
                "Plant part match adds 20 points.",
                "Each matched key symptom adds 20 points.",
                "Each matched secondary symptom adds 10 points.",
                "Each unmatched selected symptom subtracts 5 points.",
            ]
        )
    )
    st.markdown("**Disclaimer**")
    st.warning(
        "This tool provides preliminary disease suggestions based on user-selected symptoms and should not replace laboratory diagnosis, expert consultation, or official agricultural advisory services."
    )
    st.markdown("**Suggested next upgrades**")
    st.markdown(
        render_markdown_list(
            [
                "Add image upload for symptom-assisted diagnosis.",
                "Expand the knowledge base with more crops and local disease notes.",
                "Support bilingual English and Urdu reporting.",
                "Add weather and location-based disease risk alerts.",
            ]
        )
    )


def main() -> None:
    st.set_page_config(page_title="PhytoAid", layout="wide")
    inject_styles()

    crops, symptoms, diseases = load_app_data()
    crop_names = [crop["name"] for crop in crops]

    initialize_state(crops)

    st.markdown(
        """
        <div class="hero-card">
            <h1>PhytoAid</h1>
            <p>
                Plant Disease Diagnosis Helper for rapid, transparent, symptom-based disease
                suggestions across citrus, tomato, and wheat.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='section-note'>Use the sidebar to choose a crop, plant part, and visible symptoms, then run the diagnosis to review the top likely disease matches.</p>",
        unsafe_allow_html=True,
    )

    render_overview_metrics(diseases, symptoms, crops)

    with st.sidebar:
        st.header("Diagnosis Inputs")
        st.selectbox(
            "Select crop",
            crop_names,
            key="selected_crop",
            on_change=handle_crop_change,
            args=(crops,),
        )

        crop_record = get_crop_record(st.session_state.selected_crop, crops)
        if st.session_state.selected_part not in crop_record["plant_parts"]:
            st.session_state.selected_part = crop_record["plant_parts"][0]

        st.selectbox(
            "Affected plant part",
            crop_record["plant_parts"],
            key="selected_part",
            on_change=handle_part_change,
        )

        symptom_options = get_symptoms_for_crop_part(
            st.session_state.selected_crop,
            st.session_state.selected_part,
            diseases,
            symptoms,
        )
        st.session_state.selected_symptoms = filter_selected_symptoms(
            st.session_state.selected_symptoms,
            symptom_options,
        )

        st.multiselect(
            "Visible symptoms",
            options=symptom_options,
            key="selected_symptoms",
            help="The list is narrowed to symptoms relevant to the selected crop and plant part.",
        )
        st.caption(f"{len(symptom_options)} symptom options available for the current selection.")
        st.caption("Scroll to the Symptom Reference section for visual examples of the available symptoms.")

        st.text_area(
            "Optional field notes",
            placeholder="Example: symptoms started after heavy rain and spread quickly.",
            key="field_notes",
            height=110,
        )

        diagnose_clicked = st.button("Run diagnosis", type="primary", use_container_width=True)
        st.button("Reset inputs", use_container_width=True, on_click=reset_inputs, args=(crops,))

    if diagnose_clicked:
        st.session_state.diagnosis_requested = True

    diagnosis_tab, library_tab, about_tab = st.tabs(["Diagnosis", "Disease Library", "About"])

    with diagnosis_tab:
        st.info(
            "This app is a preliminary advisory tool. Confidence reflects symptom match strength rather than confirmed diagnosis."
        )
        st.markdown("**Quick sample**: Citrus + Leaf + Raised lesions + Yellow halo + Corky spots should rank Citrus canker near the top.")
        render_symptom_reference(
            st.session_state.selected_crop,
            symptom_options,
            st.session_state.selected_symptoms,
            symptoms,
        )

        if st.session_state.diagnosis_requested:
            render_results(
                crop=st.session_state.selected_crop,
                plant_part=st.session_state.selected_part,
                selected_symptoms=st.session_state.selected_symptoms,
                field_notes=st.session_state.field_notes,
                symptoms=symptoms,
                diseases=diseases,
            )
        else:
            st.markdown("**Ready to diagnose**")
            st.markdown(
                render_markdown_list(
                    [
                        "Choose a crop and affected plant part from the sidebar.",
                        "Select one or more visible symptoms.",
                        "Run the diagnosis to view the top three likely diseases.",
                    ]
                )
            )

    with library_tab:
        render_library(diseases, crop_names)

    with about_tab:
        render_about()


if __name__ == "__main__":
    main()
