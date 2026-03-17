from __future__ import annotations

import json
import shutil
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

BASE_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = BASE_DIR / "assets" / "symptoms"
SOURCE_DIR = ASSETS_DIR / "sources"
GENERATED_DIR = ASSETS_DIR / "generated"
SYMPTOMS_FILE = BASE_DIR / "data" / "symptoms.json"
ATTRIBUTION_FILE = ASSETS_DIR / "ATTRIBUTION.md"
OUTPUT_SIZE = (960, 600)


@dataclass(frozen=True)
class SourceSpec:
    filename: str
    credit: str
    source_url: str
    download_url: str | None = None
    local_source: str | None = None


SOURCE_SPECS: dict[str, SourceSpec] = {
    "citrus_canker_foliage": SourceSpec(
        filename="citrus-canker-foliage.jpg",
        local_source="citrus-canker-foliage.jpg",
        credit="USDA Agricultural Research Service / Public domain",
        source_url="https://commons.wikimedia.org/wiki/File:Citrus_canker_on_foliage.jpg",
    ),
    "citrus_canker_fruit": SourceSpec(
        filename="citrus-canker-fruit.jpg",
        local_source="citrus-canker-fruit.jpg",
        credit="USDA Agricultural Research Service / Public domain",
        source_url="https://commons.wikimedia.org/wiki/File:Citrus_canker_on_fruit.jpg",
    ),
    "citrus_chlorosis": SourceSpec(
        filename="chlorotic-lemon-leaf.jpg",
        local_source="chlorotic-lemon-leaf.jpg",
        credit="AKA MBG Archive / CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Chlorotic_lemon_tree_leaf_01.jpg",
    ),
    "citrus_black_spot": SourceSpec(
        filename="citrus-black-spot.jpg",
        credit="polaternez/citrus-diseases-detection",
        source_url="https://raw.githubusercontent.com/polaternez/citrus-diseases-detection/master/flask_api/sample_images/black_spot0.jpg",
        download_url="https://raw.githubusercontent.com/polaternez/citrus-diseases-detection/master/flask_api/sample_images/black_spot0.jpg",
    ),
    "citrus_greening": SourceSpec(
        filename="citrus-greening.jpg",
        credit="polaternez/citrus-diseases-detection",
        source_url="https://raw.githubusercontent.com/polaternez/citrus-diseases-detection/master/flask_api/sample_images/greening0.jpg",
        download_url="https://raw.githubusercontent.com/polaternez/citrus-diseases-detection/master/flask_api/sample_images/greening0.jpg",
    ),
    "citrus_canker_alt": SourceSpec(
        filename="citrus-canker-alt.jpg",
        credit="polaternez/citrus-diseases-detection",
        source_url="https://raw.githubusercontent.com/polaternez/citrus-diseases-detection/master/flask_api/sample_images/canker0.jpg",
        download_url="https://raw.githubusercontent.com/polaternez/citrus-diseases-detection/master/flask_api/sample_images/canker0.jpg",
    ),
    "tomato_bacterial_spot": SourceSpec(
        filename="tomato-bacterial-spot.jpg",
        credit="spMohanty/PlantVillage-Dataset",
        source_url="https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Bacterial_spot/00416648-be6e-4bd4-bc8d-82f43f8a7240___GCREC_Bact.Sp%203110.JPG",
        download_url="https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Bacterial_spot/00416648-be6e-4bd4-bc8d-82f43f8a7240___GCREC_Bact.Sp%203110.JPG",
    ),
    "tomato_early_blight": SourceSpec(
        filename="tomato-early-blight.jpg",
        credit="spMohanty/PlantVillage-Dataset",
        source_url="https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Early_blight/0012b9d2-2130-4a06-a834-b1f3af34f57e___RS_Erly.B%208389.JPG",
        download_url="https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Early_blight/0012b9d2-2130-4a06-a834-b1f3af34f57e___RS_Erly.B%208389.JPG",
    ),
    "tomato_late_blight": SourceSpec(
        filename="tomato-late-blight.jpg",
        credit="spMohanty/PlantVillage-Dataset",
        source_url="https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Late_blight/0003faa8-4b27-4c65-bf42-6d9e352ca1a5___RS_Late.B%204946.JPG",
        download_url="https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Late_blight/0003faa8-4b27-4c65-bf42-6d9e352ca1a5___RS_Late.B%204946.JPG",
    ),
    "tomato_leaf_mold": SourceSpec(
        filename="tomato-leaf-mold.jpg",
        credit="spMohanty/PlantVillage-Dataset",
        source_url="https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Leaf_Mold/00694db7-3327-45e0-b4da-a8bb7ab6a4b7___Crnl_L.Mold%206923.JPG",
        download_url="https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Leaf_Mold/00694db7-3327-45e0-b4da-a8bb7ab6a4b7___Crnl_L.Mold%206923.JPG",
    ),
    "tomato_yellow_leaf_curl": SourceSpec(
        filename="tomato-yellow-leaf-curl.jpg",
        credit="spMohanty/PlantVillage-Dataset",
        source_url="https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Tomato_Yellow_Leaf_Curl_Virus/00139ae8-d881-4edb-925f-46584b0bd68c___YLCV_NREC%202944.JPG",
        download_url="https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Tomato_Yellow_Leaf_Curl_Virus/00139ae8-d881-4edb-925f-46584b0bd68c___YLCV_NREC%202944.JPG",
    ),
    "wheat_brown_rust": SourceSpec(
        filename="wheat-brown-rust.jpg",
        credit="SWIN-SHARP/SWIN-SHARP",
        source_url="https://raw.githubusercontent.com/SWIN-SHARP/SWIN-SHARP/main/WheatDiseases/test/2_Brown_Rust/2.jpg",
        download_url="https://raw.githubusercontent.com/SWIN-SHARP/SWIN-SHARP/main/WheatDiseases/test/2_Brown_Rust/2.jpg",
    ),
    "wheat_yellow_rust": SourceSpec(
        filename="wheat-yellow-rust.jpg",
        credit="SWIN-SHARP/SWIN-SHARP",
        source_url="https://raw.githubusercontent.com/SWIN-SHARP/SWIN-SHARP/main/WheatDiseases/test/3_Yellow_Rust/147.jpg",
        download_url="https://raw.githubusercontent.com/SWIN-SHARP/SWIN-SHARP/main/WheatDiseases/test/3_Yellow_Rust/147.jpg",
    ),
    "wheat_powdery_mildew": SourceSpec(
        filename="wheat-powdery-mildew.jpg",
        credit="SWIN-SHARP/SWIN-SHARP",
        source_url="https://raw.githubusercontent.com/SWIN-SHARP/SWIN-SHARP/main/WheatDiseases/test/4_Powdery_Mildew/1999.jpg",
        download_url="https://raw.githubusercontent.com/SWIN-SHARP/SWIN-SHARP/main/WheatDiseases/test/4_Powdery_Mildew/1999.jpg",
    ),
    "wheat_loose_smut": SourceSpec(
        filename="wheat-loose-smut.jpg",
        credit="SWIN-SHARP/SWIN-SHARP",
        source_url="https://raw.githubusercontent.com/SWIN-SHARP/SWIN-SHARP/main/WheatDiseases/test/5_Loose_Smut/17.jpg",
        download_url="https://raw.githubusercontent.com/SWIN-SHARP/SWIN-SHARP/main/WheatDiseases/test/5_Loose_Smut/17.jpg",
    ),
    "wheat_root_rot": SourceSpec(
        filename="wheat-root-rot.jpg",
        credit="aadium/wheat-disease-detection",
        source_url="https://raw.githubusercontent.com/aadium/wheat-disease-detection/main/testCDD/crr_1.jpg",
        download_url="https://raw.githubusercontent.com/aadium/wheat-disease-detection/main/testCDD/crr_1.jpg",
    ),
    "wheat_leaf_spot": SourceSpec(
        filename="wheat-leaf-spot.jpg",
        credit="aadium/wheat-disease-detection",
        source_url="https://raw.githubusercontent.com/aadium/wheat-disease-detection/main/testCDD/ls_1.jpg",
        download_url="https://raw.githubusercontent.com/aadium/wheat-disease-detection/main/testCDD/ls_1.jpg",
    ),
}

PRESETS = {
    "full": (0.00, 0.00, 1.00, 1.00),
    "wide": (0.04, 0.06, 0.96, 0.88),
    "tight": (0.10, 0.12, 0.90, 0.88),
    "left": (0.00, 0.08, 0.76, 0.92),
    "right": (0.24, 0.08, 1.00, 0.92),
    "top": (0.08, 0.00, 0.92, 0.72),
    "bottom": (0.08, 0.28, 0.92, 1.00),
    "top_left": (0.00, 0.00, 0.72, 0.72),
    "top_right": (0.28, 0.00, 1.00, 0.72),
    "bottom_left": (0.00, 0.28, 0.72, 1.00),
    "bottom_right": (0.28, 0.28, 1.00, 1.00),
    "detail_left": (0.02, 0.12, 0.68, 0.86),
    "detail_right": (0.32, 0.12, 0.98, 0.86),
}

IMAGE_ASSIGNMENTS: dict[str, dict[str, tuple[str, str]]] = {
    "Yellow halo": {
        "Citrus": ("citrus_canker_foliage", "top_left"),
    },
    "Raised lesions": {
        "Citrus": ("citrus_canker_alt", "tight"),
    },
    "Leaf spots": {
        "Citrus": ("citrus_black_spot", "wide"),
        "Tomato": ("tomato_bacterial_spot", "wide"),
    },
    "Corky spots": {
        "Citrus": ("citrus_canker_fruit", "tight"),
    },
    "Defoliation": {
        "Citrus": ("citrus_greening", "wide"),
    },
    "Wilting": {
        "Citrus": ("citrus_greening", "bottom"),
        "Tomato": ("tomato_yellow_leaf_curl", "left"),
        "Wheat": ("wheat_root_rot", "wide"),
    },
    "Root decay": {
        "Citrus": ("citrus_chlorosis", "bottom"),
        "Wheat": ("wheat_root_rot", "tight"),
    },
    "Gum exudation": {
        "Citrus": ("citrus_canker_alt", "right"),
    },
    "Powdery growth": {
        "Wheat": ("wheat_powdery_mildew", "full"),
    },
    "Chlorosis": {
        "Citrus": ("citrus_chlorosis", "full"),
        "Tomato": ("tomato_leaf_mold", "left"),
        "Wheat": ("wheat_yellow_rust", "left"),
    },
    "Necrosis": {
        "Citrus": ("citrus_black_spot", "detail_right"),
        "Tomato": ("tomato_early_blight", "detail_right"),
        "Wheat": ("wheat_leaf_spot", "detail_right"),
    },
    "Blighting": {
        "Tomato": ("tomato_late_blight", "wide"),
    },
    "Water-soaked lesions": {
        "Tomato": ("tomato_late_blight", "detail_right"),
    },
    "Stem canker": {
        "Citrus": ("citrus_canker_alt", "detail_left"),
        "Tomato": ("tomato_early_blight", "bottom_left"),
    },
    "Fruit rot": {
        "Tomato": ("tomato_late_blight", "bottom"),
    },
    "Mold growth": {
        "Tomato": ("tomato_leaf_mold", "wide"),
        "Wheat": ("wheat_loose_smut", "left"),
    },
    "Rust pustules": {
        "Wheat": ("wheat_brown_rust", "tight"),
    },
    "White patches": {
        "Wheat": ("wheat_powdery_mildew", "detail_left"),
    },
    "Stunted growth": {
        "Citrus": ("citrus_greening", "top_left"),
        "Tomato": ("tomato_yellow_leaf_curl", "bottom_left"),
        "Wheat": ("wheat_root_rot", "top_left"),
    },
    "Seed discoloration": {
        "Wheat": ("wheat_loose_smut", "tight"),
    },
    "Fruit lesions": {
        "Citrus": ("citrus_canker_fruit", "left"),
        "Tomato": ("tomato_bacterial_spot", "bottom_right"),
    },
    "Greasy blotches": {
        "Citrus": ("citrus_black_spot", "right"),
    },
    "Bark cracking": {
        "Citrus": ("citrus_canker_alt", "top_right"),
    },
    "Collar rot": {
        "Citrus": ("citrus_canker_alt", "bottom_left"),
    },
    "Concentric rings": {
        "Tomato": ("tomato_early_blight", "detail_left"),
    },
    "One-sided wilting": {
        "Tomato": ("tomato_yellow_leaf_curl", "right"),
    },
    "Vascular browning": {
        "Tomato": ("tomato_yellow_leaf_curl", "tight"),
    },
    "Shot holes": {
        "Tomato": ("tomato_bacterial_spot", "top_right"),
    },
    "Leaf curling": {
        "Wheat": ("wheat_yellow_rust", "detail_left"),
    },
    "Rapid collapse": {
        "Tomato": ("tomato_late_blight", "top"),
    },
    "Shriveled grain": {
        "Wheat": ("wheat_loose_smut", "bottom_right"),
    },
    "Patchy growth": {
        "Citrus": ("citrus_greening", "top"),
        "Wheat": ("wheat_yellow_rust", "top"),
    },
}


def ensure_directories() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def ensure_source_file(source_id: str) -> Path:
    spec = SOURCE_SPECS[source_id]
    if spec.local_source:
        local_path = ASSETS_DIR / spec.local_source
        if not local_path.exists():
            raise FileNotFoundError(f"Missing local source image: {local_path}")
        return local_path

    destination = SOURCE_DIR / spec.filename
    if destination.exists():
        return destination

    request = urllib.request.Request(spec.download_url, headers={"User-Agent": "Codex"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    return destination


def render_variant(source_path: Path, destination: Path, preset_name: str) -> None:
    left, top, right, bottom = PRESETS[preset_name]
    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        width, height = image.size
        crop_box = (
            int(width * left),
            int(height * top),
            int(width * right),
            int(height * bottom),
        )
        cropped = image.crop(crop_box)
        rendered = ImageOps.fit(cropped, OUTPUT_SIZE, method=Image.Resampling.LANCZOS)
        rendered.save(destination, quality=86, optimize=True)


def build_asset_pack() -> dict[str, list[dict[str, str]]]:
    generated_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)

    for symptom_name, crop_map in IMAGE_ASSIGNMENTS.items():
        for crop, (source_id, preset_name) in crop_map.items():
            source_path = ensure_source_file(source_id)
            slug = symptom_name.lower().replace(" ", "-")
            destination_name = f"{crop.lower()}-{slug}.jpg"
            destination = GENERATED_DIR / destination_name
            render_variant(source_path, destination, preset_name)
            generated_by_source[source_id].append(
                {
                    "crop": crop,
                    "symptom": symptom_name,
                    "image_file": f"generated/{destination_name}",
                }
            )

    return generated_by_source


def load_symptoms() -> list[dict]:
    return json.loads(SYMPTOMS_FILE.read_text(encoding="utf-8"))


def apply_local_mappings(symptoms: list[dict]) -> None:
    for item in symptoms:
        mapping = IMAGE_ASSIGNMENTS.get(item["name"])
        if not mapping:
            raise KeyError(f"No image mapping configured for symptom: {item['name']}")

        for key in (
            "image_file",
            "image_crops",
            "image_credit",
            "image_source_url",
            "image_url",
            "image_width",
            "commons_file",
        ):
            item.pop(key, None)

        item.pop("image_variants", None)

        variants: list[dict[str, object]] = []
        for index, (crop, (source_id, _preset_name)) in enumerate(mapping.items()):
            spec = SOURCE_SPECS[source_id]
            variant_payload = {
                "crop": crop,
                "image_file": f"generated/{crop.lower()}-{item['slug']}.jpg",
                "image_crops": [crop],
                "image_credit": spec.credit,
                "image_source_url": spec.source_url,
            }
            if index == 0:
                item["image_file"] = variant_payload["image_file"]
                item["image_crops"] = variant_payload["image_crops"]
                item["image_credit"] = variant_payload["image_credit"]
                item["image_source_url"] = variant_payload["image_source_url"]
            else:
                variants.append(variant_payload)

        if variants:
            item["image_variants"] = variants


def write_symptoms(symptoms: list[dict]) -> None:
    SYMPTOMS_FILE.write_text(json.dumps(symptoms, indent=2) + "\n", encoding="utf-8")


def write_attribution(generated_by_source: dict[str, list[dict[str, str]]]) -> None:
    lines = [
        "# Symptom Image Attribution",
        "",
        "All symptom cards use local image files stored under `assets/symptoms/`.",
        "Generated files in `assets/symptoms/generated/` are cropped local derivatives of the source photos listed below.",
        "",
    ]

    for source_id in sorted(generated_by_source):
        spec = SOURCE_SPECS[source_id]
        lines.append(f"## {source_id}")
        lines.append("")
        lines.append(f"- Credit: {spec.credit}")
        lines.append(f"- Source link: {spec.source_url}")
        source_location = spec.local_source or f"sources/{spec.filename}"
        lines.append(f"- Local source file: `{source_location}`")
        lines.append("- Derived symptom cards:")
        for record in sorted(generated_by_source[source_id], key=lambda item: (item["crop"], item["symptom"])):
            lines.append(f"  - `{record['image_file']}` for {record['crop']} - {record['symptom']}")
        lines.append("")

    ATTRIBUTION_FILE.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_directories()
    generated_by_source = build_asset_pack()
    symptoms = load_symptoms()
    apply_local_mappings(symptoms)
    write_symptoms(symptoms)
    write_attribution(generated_by_source)
    print(f"Generated {sum(len(items) for items in generated_by_source.values())} local symptom images.")


if __name__ == "__main__":
    main()
