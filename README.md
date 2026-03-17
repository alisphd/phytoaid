# PhytoAid

[![Live App](https://img.shields.io/badge/Live_App-PhytoAid-red?logo=streamlit&logoColor=white)](https://phytoaid.streamlit.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-alisphd%2Fphytoaid-181717?logo=github)](https://github.com/alisphd/phytoaid)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)

PhytoAid is a rule-based Streamlit web application for preliminary plant disease diagnosis. Users select a crop, affected plant part, and visible symptoms, and the app returns likely diseases with confidence scores, severity estimates, symptom references, and management guidance.

This project is designed as a decision-support tool for students, researchers, extension workers, and growers. It does not replace laboratory diagnosis or expert agronomic advice.

## Live Demo

- Live app: [https://phytoaid.streamlit.app/](https://phytoaid.streamlit.app/)
- Repository: [https://github.com/alisphd/phytoaid](https://github.com/alisphd/phytoaid)

## Why This Project

PhytoAid was built to combine plant pathology knowledge with practical software development in a way that is useful, explainable, and portfolio-ready. Instead of relying on a black-box model, the app uses transparent rules so users can understand why a disease was suggested.

## Current Crop Coverage

PhytoAid currently supports symptom-based diagnosis for:

- Citrus
- Tomato
- Wheat
- Rice
- Maize
- Sugarcane
- Cotton

## Key Features

- Crop-specific diagnosis workflow
- Plant-part-aware symptom filtering
- Rule-based disease ranking with transparent scoring
- Confidence score and severity estimation
- Management recommendations grouped by cultural, chemical, and preventive actions
- Searchable disease library
- Local symptom reference gallery with cited crop images
- Downloadable text summary report

## How It Works

1. The user selects a crop and affected plant part.
2. The app filters symptom options relevant to that crop and plant part.
3. Candidate diseases are matched against the selected symptoms.
4. Each disease is scored using plant-part matches, key symptom matches, secondary symptom matches, and mismatch penalties.
5. The system ranks the top likely diseases and shows a confidence score.
6. Severity is estimated from the combined weight of the selected symptoms.

## Example Diagnosis

Example input:

- Crop: `Citrus`
- Plant part: `Leaf`
- Symptoms: `Raised lesions`, `Yellow halo`, `Corky spots`

Expected outcome:

- Top suggestion: `Citrus canker`
- Match confidence: high
- Severity: moderate to high depending on the full symptom set

## Tech Stack

- Python
- Streamlit
- pandas
- Plotly
- JSON knowledge base

## Project Structure

```text
phytoaid/
|-- app.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- data/
|   |-- crops.json
|   |-- diseases.json
|   `-- symptoms.json
|-- src/
|   |-- __init__.py
|   |-- data_loader.py
|   |-- diagnosis.py
|   |-- helpers.py
|   |-- recommendations.py
|   |-- scoring.py
|   |-- severity.py
|   `-- symptom_visuals.py
|-- assets/
|   |-- screenshots/
|   `-- symptoms/
|       |-- generated/
|       |-- sources/
|       `-- ATTRIBUTION.md
|-- tools/
|   `-- build_symptom_assets.py
`-- docs/
    `-- notes.md
```

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Symptom Image System

PhytoAid includes a fully local symptom image pack. Each symptom card uses bundled local files under `assets/symptoms/` and shows a source credit directly in the app.

To rebuild the local symptom image pack after changing image sources, run:

```bash
python tools/build_symptom_assets.py
```

This script:

- downloads curated source images into `assets/symptoms/sources/`
- generates local crop-specific symptom cards in `assets/symptoms/generated/`
- updates `data/symptoms.json` to point to local image files
- refreshes `assets/symptoms/ATTRIBUTION.md`

## Deployment

PhytoAid is deployed on Streamlit Community Cloud:

- Live app: [https://phytoaid.streamlit.app/](https://phytoaid.streamlit.app/)

GitHub Pages is not suitable for this project because Streamlit apps require a Python backend rather than static site hosting.

## Future Improvements

- Add more crops and disease profiles relevant to Pakistan
- Add real symptom photo packs for the newly added crops
- Add image upload for visual assistance
- Add bilingual English and Urdu support
- Add weather-based disease risk alerts
- Export PDF reports

## Disclaimer

This tool provides preliminary disease suggestions based on user-selected symptoms and should not replace laboratory diagnosis, expert consultation, or official agricultural advisory services.

## CV Description

**PhytoAid - Plant Disease Diagnosis Helper Web App**  
Developed and deployed a rule-based web application in Python and Streamlit for preliminary diagnosis of crop diseases using crop type, plant part, and visible symptom selection. Implemented symptom-based disease ranking, confidence scoring, severity estimation, management recommendation modules, and a cited local symptom image library for agricultural decision support.
