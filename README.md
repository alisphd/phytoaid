# PhytoAid

PhytoAid is a rule-based Streamlit application for preliminary plant disease diagnosis. Users choose a crop, affected plant part, and visible symptoms, and the app returns likely diseases with confidence scores, severity estimates, and management guidance.

## Features

- Crop selection for citrus, tomato, wheat, rice, maize, sugarcane, and cotton
- Plant-part-aware symptom filtering
- Transparent rule-based disease ranking
- Confidence scoring and severity estimation
- Management recommendations grouped by cultural, chemical, and preventive actions
- Searchable disease library
- Local symptom reference gallery with cited crop photos
- Downloadable text summary report

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
|   `-- severity.py
|-- assets/
|   |-- screenshots/
|   `-- symptoms/
|       `-- ATTRIBUTION.md
`-- docs/
    `-- notes.md
```

## How It Works

1. The app filters disease profiles by crop.
2. It compares the selected plant part and symptoms with each disease profile.
3. The scoring engine assigns:
   - `+20` for a plant part match
   - `+20` for each matched key symptom
   - `+10` for each matched secondary symptom
   - `-5` for each selected symptom not found in the disease profile
4. Confidence is normalized as a percentage of the maximum possible score for that disease.
5. Severity is estimated from symptom weights defined in `data/symptoms.json`.

## Example Use Case

- Crop: `Citrus`
- Plant part: `Leaf`
- Symptoms: `Raised lesions`, `Yellow halo`, `Corky spots`

Expected outcome:

- Top suggestion: `Citrus canker`
- Confidence: high match
- Severity: moderate to high depending on the full symptom set

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publish And Deploy

GitHub Pages cannot host this project because PhytoAid is a Python Streamlit app rather than a static website. The clean deployment flow is:

1. Push this folder to its own GitHub repository.
2. Deploy that repository on Streamlit Community Cloud.
3. Streamlit will rebuild the app automatically whenever you push updates to GitHub.

### Push To GitHub

From the project folder:

```bash
git init -b main
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<your-username>/phytoaid.git
git push -u origin main
```

### Deploy On Streamlit Community Cloud

1. Open [share.streamlit.io](https://share.streamlit.io/)
2. Sign in with your GitHub account.
3. Choose the repository you pushed.
4. Set the main file path to `app.py`.
5. Deploy the app.

Recommended settings:

- Repository: `phytoaid`
- Branch: `main`
- Main file path: `app.py`

Once deployed, Streamlit will give you a public app URL that you can add to your CV and GitHub profile.

## Adding Real Symptom Images

PhytoAid now ships with a fully local symptom image pack. Every symptom card resolves to a bundled local file under `assets/symptoms/`, and each card shows its photo credit and source link directly under the image.

To rebuild the local image pack after changing symptom sources, run:

```bash
python tools/build_symptom_assets.py
```

This script:

- downloads the curated source photos into `assets/symptoms/sources/`
- generates crop-specific local symptom cards in `assets/symptoms/generated/`
- rewrites `data/symptoms.json` so the app uses only local files
- refreshes `assets/symptoms/ATTRIBUTION.md`

The current local source list is tracked in `assets/symptoms/ATTRIBUTION.md`.

## Disclaimer

This tool provides preliminary disease suggestions based on user-selected symptoms and should not replace laboratory diagnosis, expert consultation, or official agricultural advisory services.

## Future Improvements

- Add image upload for visual assistance
- Expand the dataset with more crops and local disease notes
- Add bilingual English and Urdu support
- Add weather-based disease risk alerts
- Export PDF reports

## CV Description

**PhytoAid - Plant Disease Diagnosis Helper Web App**  
Developed a rule-based web application in Python and Streamlit for preliminary diagnosis of crop diseases using crop type, affected plant part, and visible symptom selection. Implemented symptom-based disease ranking, confidence scoring, severity estimation, and management recommendation modules for agricultural decision support.
