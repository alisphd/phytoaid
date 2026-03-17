from __future__ import annotations

import base64
import mimetypes
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".svg")
AUTO_FOCUS_PRESETS = (
    ("22% 28%", 1.16),
    ("78% 28%", 1.16),
    ("28% 72%", 1.18),
    ("72% 72%", 1.18),
    ("50% 50%", 1.24),
    ("50% 24%", 1.2),
    ("50% 76%", 1.2),
)

CATEGORY_STYLES = {
    "mild": {
        "accent": "#5f8b43",
        "panel": "#eef5e6",
        "panel_alt": "#dcecc8",
        "surface": "#a8c982",
        "stroke": "#36511d",
        "highlight": "#f5f9df",
    },
    "moderate": {
        "accent": "#b57612",
        "panel": "#fbf1d8",
        "panel_alt": "#f4d9a2",
        "surface": "#ddbe70",
        "stroke": "#744c11",
        "highlight": "#fff4cf",
    },
    "severe": {
        "accent": "#b54d38",
        "panel": "#f9e6e1",
        "panel_alt": "#f0c0b3",
        "surface": "#d48b72",
        "stroke": "#762b1f",
        "highlight": "#ffd6ca",
    },
}


def slugify_symptom_name(name: str) -> str:
    slug = []
    last_was_dash = False

    for character in name.lower():
        if character.isalnum():
            slug.append(character)
            last_was_dash = False
        elif not last_was_dash:
            slug.append("-")
            last_was_dash = True

    return "".join(slug).strip("-")


def find_local_symptom_image(symptom_name: str, assets_dir: str | Path, image_file: str | None = None) -> Path | None:
    asset_root = Path(assets_dir)

    if image_file:
        explicit_candidate = asset_root / image_file
        if explicit_candidate.exists():
            return explicit_candidate

    slug = slugify_symptom_name(symptom_name)
    for extension in SUPPORTED_IMAGE_EXTENSIONS:
        slug_candidate = asset_root / f"{slug}{extension}"
        if slug_candidate.exists():
            return slug_candidate
    return None


def get_symptom_cards(
    symptom_names: list[str],
    symptom_db: list[dict[str, Any]],
    assets_dir: str | Path,
    selected_crop: str | None = None,
) -> list[dict[str, Any]]:
    lookup = {item["name"]: item for item in symptom_db}
    cards: list[dict[str, Any]] = []

    for name in symptom_names:
        symptom = dict(lookup.get(name, {}))
        symptom.setdefault("name", name)
        symptom.setdefault("slug", slugify_symptom_name(name))
        symptom.setdefault("category", "moderate")
        symptom.setdefault("description", "Illustrative symptom reference.")
        symptom.setdefault("focus_area", "leaf")
        symptom.setdefault("visual", "spots")
        symptom.update(resolve_image_reference(symptom, selected_crop, assets_dir))
        cards.append(symptom)

    apply_duplicate_photo_focus(cards)
    return cards


def build_symptom_card_html(symptom: dict[str, Any], selected: bool = False) -> str:
    style = CATEGORY_STYLES.get(symptom.get("category", "moderate"), CATEGORY_STYLES["moderate"])
    visual = build_visual_markup(symptom, style)
    badge_text = "Selected symptom" if selected else f"{symptom.get('category', 'moderate').title()} symptom"
    selected_class = " symptom-card--selected" if selected else ""
    credit_markup = build_credit_markup(symptom)
    if symptom.get("has_real_photo"):
        media_label = "Focused local photo" if symptom.get("focused_photo") else "Local crop photo"
    else:
        media_label = "Illustration"

    return f"""
    <div class="symptom-card{selected_class}">
        <div class="symptom-card__visual">
            {visual}
        </div>
        <div class="symptom-card__body">
            <span class="symptom-card__badge" style="background:{style['highlight']}; color:{style['accent']};">
                {escape(badge_text)}
            </span>
            <span class="symptom-card__meta">{escape(media_label)}</span>
            <h4>{escape(symptom["name"])}</h4>
            <p>{escape(symptom.get("description", "Illustrative symptom reference."))}</p>
            {credit_markup}
        </div>
    </div>
    """


def build_visual_markup(symptom: dict[str, Any], style: dict[str, str]) -> str:
    asset_path = symptom.get("asset_path")
    if asset_path:
        return wrap_visual_markup(build_local_asset_markup(asset_path, symptom))

    fallback_uri = build_symptom_svg_data_uri(symptom, style)
    return wrap_visual_markup(build_data_uri_img_markup(fallback_uri, symptom["name"], "illustration"))


def wrap_visual_markup(inner_markup: str) -> str:
    return f'<div class="symptom-card__frame">{inner_markup}</div>'


def build_local_asset_markup(asset_path: str | Path, symptom: dict[str, Any]) -> str:
    path = Path(asset_path)
    mime_type, _ = mimetypes.guess_type(path.name)
    mime_type = mime_type or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    safe_alt = escape(symptom["name"])
    image_style = build_image_style(symptom)
    return (
        f'<img class="symptom-card__img" src="data:{mime_type};base64,{encoded}" '
        f'alt="{safe_alt} reference image"{image_style} />'
    )


def build_data_uri_img_markup(data_uri: str, alt_text: str, suffix: str) -> str:
    safe_uri = escape(data_uri, quote=True)
    safe_alt = escape(alt_text)
    return f'<img class="symptom-card__img" src="{safe_uri}" alt="{safe_alt} {suffix}" />'


def build_remote_asset_markup(image_url: str, symptom: dict[str, Any], fallback_uri: str) -> str:
    safe_url = escape(image_url, quote=True)
    safe_alt = escape(symptom["name"])
    safe_fallback = escape(fallback_uri, quote=True)
    image_style = build_image_style(symptom)
    onerror = (
        "this.onerror=null;"
        f"this.src='{safe_fallback}';"
        "var card=this.closest('.symptom-card');"
        "if(card){"
        "var meta=card.querySelector('.symptom-card__meta');"
        "if(meta){meta.textContent='Illustration';}"
        "var credit=card.querySelector('.symptom-card__credit');"
        "if(credit){credit.style.display='none';}"
        "}"
    )
    return (
        f'<img class="symptom-card__img" src="{safe_url}" '
        f'alt="{safe_alt} reference image" loading="lazy" referrerpolicy="no-referrer" '
        f'onerror="{onerror}"{image_style} />'
    )


def build_symptom_svg_data_uri(symptom: dict[str, Any], style: dict[str, str]) -> str:
    slug = symptom.get("slug", slugify_symptom_name(symptom["name"]))
    focus_area = symptom.get("focus_area", "leaf")
    visual = symptom.get("visual", "spots")
    surface_markup = build_surface_markup(focus_area, style)
    overlay_markup = build_overlay_markup(visual, focus_area, style)
    svg_markup = f"""
    <svg viewBox="0 0 320 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{escape(symptom['name'])} illustration">
        <defs>
            <linearGradient id="panel-{slug}" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="{style['panel']}" />
                <stop offset="100%" stop-color="{style['panel_alt']}" />
            </linearGradient>
        </defs>
        <rect x="12" y="12" width="296" height="186" rx="28" fill="url(#panel-{slug})" />
        <circle cx="258" cy="48" r="30" fill="{style['highlight']}" opacity="0.85" />
        {surface_markup}
        {overlay_markup}
    </svg>
    """
    encoded = base64.b64encode(svg_markup.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def build_credit_markup(symptom: dict[str, Any]) -> str:
    if not symptom.get("has_real_photo"):
        return ""

    credit_text = symptom.get("image_credit")
    source_url = symptom.get("image_source_url")
    if not credit_text:
        return ""

    if source_url:
        safe_url = escape(source_url, quote=True)
        return (
            f'<p class="symptom-card__credit">Photo: '
            f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">{escape(credit_text)}</a></p>'
        )

    return f'<p class="symptom-card__credit">Photo: {escape(credit_text)}</p>'


def build_image_style(symptom: dict[str, Any]) -> str:
    style_rules: list[str] = []

    position = symptom.get("image_position")
    if position:
        style_rules.append(f"object-position:{position}")

    scale = symptom.get("image_scale")
    if scale and scale != 1:
        style_rules.append(f"transform:scale({scale})")
        style_rules.append("transform-origin:center center")

    if not style_rules:
        return ""

    style = "; ".join(style_rules)
    return f' style="{escape(style, quote=True)}"'


def resolve_image_reference(symptom: dict[str, Any], selected_crop: str | None, assets_dir: str | Path) -> dict[str, Any]:
    image_data = dict(symptom)
    variant = select_image_variant(symptom, selected_crop)

    if variant:
        image_data.update(variant)

    crop_targets = image_data.get("image_crops", [])
    crop_matches = selected_crop is None or not crop_targets or selected_crop in crop_targets
    asset_path = find_local_symptom_image(symptom["name"], assets_dir, image_data.get("image_file")) if crop_matches else None
    image_source_url = resolve_source_url(image_data)

    return {
        "asset_path": asset_path,
        "image_url": None,
        "image_credit": image_data.get("image_credit"),
        "image_source_url": image_source_url,
        "has_real_photo": bool(asset_path),
    }


def select_image_variant(symptom: dict[str, Any], selected_crop: str | None) -> dict[str, Any] | None:
    variants = symptom.get("image_variants", [])
    if not variants:
        return None

    if selected_crop:
        for variant in variants:
            if variant.get("crop") == selected_crop:
                return dict(variant)

    for variant in variants:
        if variant.get("crop") in {None, "", "All", "*"}:
            return dict(variant)

    if selected_crop is None:
        return dict(variants[0])

    return None


def resolve_image_url(image_data: dict[str, Any]) -> str | None:
    image_url = image_data.get("image_url")
    if image_url:
        return image_url

    commons_file = image_data.get("commons_file")
    if not commons_file:
        return None

    width = image_data.get("image_width", 640)
    encoded_name = quote(commons_file, safe="")
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{encoded_name}?width={width}"


def resolve_source_url(image_data: dict[str, Any]) -> str | None:
    source_url = image_data.get("image_source_url")
    if source_url:
        return source_url

    commons_file = image_data.get("commons_file")
    if not commons_file:
        return None

    encoded_name = quote(commons_file.replace(" ", "_"), safe="")
    return f"https://commons.wikimedia.org/wiki/File:{encoded_name}"


def apply_duplicate_photo_focus(cards: list[dict[str, Any]]) -> None:
    grouped_cards: dict[str, list[dict[str, Any]]] = {}

    for card in cards:
        if not card.get("has_real_photo"):
            continue

        source_key = get_photo_source_key(card)
        if not source_key:
            continue

        grouped_cards.setdefault(source_key, []).append(card)

    for grouped in grouped_cards.values():
        if len(grouped) < 2:
            continue

        ordered_cards = sorted(grouped, key=lambda item: item["name"])
        for index, card in enumerate(ordered_cards):
            if not card.get("image_position"):
                card["image_position"] = AUTO_FOCUS_PRESETS[index % len(AUTO_FOCUS_PRESETS)][0]
            if not card.get("image_scale"):
                card["image_scale"] = AUTO_FOCUS_PRESETS[index % len(AUTO_FOCUS_PRESETS)][1]
            card["focused_photo"] = True


def get_photo_source_key(card: dict[str, Any]) -> str | None:
    asset_path = card.get("asset_path")
    if asset_path:
        return str(asset_path)

    image_url = card.get("image_url")
    if image_url:
        return image_url

    source_url = card.get("image_source_url")
    if source_url:
        return source_url

    return None


def build_surface_markup(focus_area: str, style: dict[str, str]) -> str:
    stroke = style["stroke"]
    surface = style["surface"]

    if focus_area == "fruit":
        return f"""
        <ellipse cx="160" cy="112" rx="72" ry="66" fill="{surface}" stroke="{stroke}" stroke-width="5" />
        <path d="M160 48 C170 30, 185 24, 200 26" fill="none" stroke="{stroke}" stroke-width="5" stroke-linecap="round" />
        <path d="M176 34 C207 30, 220 54, 214 72 C193 66, 182 55, 176 34 Z" fill="{style['highlight']}" opacity="0.85" />
        """
    if focus_area == "root":
        return f"""
        <path d="M160 42 L160 86" stroke="{stroke}" stroke-width="8" stroke-linecap="round" />
        <path d="M160 86 C150 126, 138 148, 118 180" stroke="{stroke}" stroke-width="6" fill="none" stroke-linecap="round" />
        <path d="M160 92 C170 124, 182 152, 206 182" stroke="{stroke}" stroke-width="6" fill="none" stroke-linecap="round" />
        <path d="M160 108 C155 136, 156 160, 156 186" stroke="{stroke}" stroke-width="5" fill="none" stroke-linecap="round" />
        <path d="M126 160 C118 166, 112 176, 104 184" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" />
        <path d="M196 160 C204 168, 214 178, 224 186" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" />
        """
    if focus_area == "stem":
        return f"""
        <rect x="138" y="38" width="44" height="138" rx="22" fill="{surface}" stroke="{stroke}" stroke-width="5" />
        <path d="M182 74 C212 60, 232 72, 238 102 C206 102, 190 94, 182 74 Z" fill="{style['highlight']}" stroke="{stroke}" stroke-width="4" />
        <path d="M138 100 C112 88, 96 98, 88 124 C118 126, 132 118, 138 100 Z" fill="{style['highlight']}" stroke="{stroke}" stroke-width="4" />
        """
    if focus_area == "seed":
        return f"""
        <ellipse cx="160" cy="112" rx="54" ry="74" fill="{surface}" stroke="{stroke}" stroke-width="5" transform="rotate(12 160 112)" />
        <path d="M154 54 C166 88, 170 124, 166 164" fill="none" stroke="{stroke}" stroke-width="4" opacity="0.7" />
        """
    if focus_area == "whole_plant":
        return f"""
        <path d="M160 44 L160 158" stroke="{stroke}" stroke-width="7" stroke-linecap="round" />
        <path d="M158 84 C132 60, 98 70, 90 104 C120 106, 142 100, 158 84 Z" fill="{surface}" stroke="{stroke}" stroke-width="4" />
        <path d="M162 98 C190 70, 228 80, 236 118 C202 118, 178 112, 162 98 Z" fill="{surface}" stroke="{stroke}" stroke-width="4" />
        <path d="M160 158 C144 176, 136 190, 132 198" stroke="{stroke}" stroke-width="6" stroke-linecap="round" />
        <path d="M160 158 C176 176, 184 190, 188 198" stroke="{stroke}" stroke-width="6" stroke-linecap="round" />
        """
    return f"""
    <path d="M66 166 C84 92, 140 44, 246 62 C234 150, 186 194, 108 194 C86 186, 76 178, 66 166 Z" fill="{surface}" stroke="{stroke}" stroke-width="5" />
    <path d="M112 186 C132 136, 160 108, 208 74" fill="none" stroke="{stroke}" stroke-width="5" stroke-linecap="round" />
    """


def build_overlay_markup(visual: str, focus_area: str, style: dict[str, str]) -> str:
    accent = style["accent"]
    stroke = style["stroke"]
    highlight = style["highlight"]

    if visual == "halo":
        return f"""
        <circle cx="150" cy="112" r="34" fill="none" stroke="{accent}" stroke-width="10" opacity="0.9" />
        <circle cx="150" cy="112" r="16" fill="{stroke}" opacity="0.75" />
        <circle cx="202" cy="92" r="18" fill="none" stroke="{accent}" stroke-width="7" opacity="0.8" />
        """
    if visual == "lesions":
        return f"""
        <circle cx="134" cy="96" r="18" fill="{stroke}" opacity="0.78" />
        <circle cx="170" cy="130" r="20" fill="{accent}" opacity="0.72" />
        <circle cx="204" cy="88" r="13" fill="{stroke}" opacity="0.7" />
        <circle cx="136" cy="96" r="7" fill="{highlight}" opacity="0.6" />
        """
    if visual == "spots":
        return f"""
        <circle cx="128" cy="92" r="10" fill="{accent}" opacity="0.72" />
        <circle cx="178" cy="106" r="14" fill="{stroke}" opacity="0.72" />
        <circle cx="210" cy="128" r="12" fill="{accent}" opacity="0.72" />
        <circle cx="154" cy="142" r="10" fill="{stroke}" opacity="0.65" />
        """
    if visual == "corky":
        return f"""
        <circle cx="136" cy="96" r="18" fill="{stroke}" opacity="0.78" />
        <circle cx="188" cy="122" r="20" fill="{accent}" opacity="0.74" />
        <path d="M122 96 L148 96 M136 82 L136 110" stroke="{highlight}" stroke-width="3" />
        <path d="M176 122 L200 122 M188 108 L188 136" stroke="{highlight}" stroke-width="3" />
        """
    if visual == "rings":
        return f"""
        <circle cx="138" cy="98" r="20" fill="none" stroke="{accent}" stroke-width="4" opacity="0.9" />
        <circle cx="138" cy="98" r="11" fill="none" stroke="{stroke}" stroke-width="3" opacity="0.8" />
        <circle cx="186" cy="126" r="24" fill="none" stroke="{stroke}" stroke-width="4" opacity="0.88" />
        <circle cx="186" cy="126" r="13" fill="none" stroke="{accent}" stroke-width="3" opacity="0.82" />
        """
    if visual == "defoliation":
        return f"""
        <path d="M214 68 C234 88, 236 118, 214 144" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" />
        <path d="M94 154 C100 166, 112 176, 122 188" fill="none" stroke="{stroke}" stroke-width="5" stroke-linecap="round" />
        <path d="M220 156 C228 166, 238 176, 248 184" fill="none" stroke="{stroke}" stroke-width="5" stroke-linecap="round" />
        <path d="M110 150 C124 150, 132 166, 126 178 C110 178, 104 164, 110 150 Z" fill="{highlight}" opacity="0.9" />
        <path d="M224 146 C238 148, 244 162, 238 176 C222 176, 218 160, 224 146 Z" fill="{highlight}" opacity="0.9" />
        """
    if visual == "wilting":
        return f"""
        <path d="M120 82 C102 96, 98 122, 116 138 C144 130, 154 112, 154 92" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" />
        <path d="M198 92 C222 104, 228 132, 210 150 C182 148, 170 126, 170 100" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" />
        <path d="M160 84 L160 156" stroke="{stroke}" stroke-width="5" stroke-linecap="round" opacity="0.8" />
        """
    if visual == "decay":
        return f"""
        <path d="M126 138 C118 156, 118 170, 112 186" stroke="{accent}" stroke-width="7" stroke-linecap="round" />
        <path d="M160 128 C156 154, 154 172, 154 192" stroke="{stroke}" stroke-width="7" stroke-linecap="round" />
        <path d="M200 138 C208 158, 214 172, 224 186" stroke="{accent}" stroke-width="7" stroke-linecap="round" />
        <circle cx="152" cy="154" r="12" fill="{stroke}" opacity="0.5" />
        """
    if visual == "gum":
        return f"""
        <path d="M160 86 L160 148" stroke="{stroke}" stroke-width="10" stroke-linecap="round" />
        <path d="M160 118 C174 128, 174 146, 160 160 C146 146, 146 128, 160 118 Z" fill="{accent}" opacity="0.92" />
        <path d="M160 150 C168 156, 168 168, 160 176 C152 168, 152 156, 160 150 Z" fill="{highlight}" opacity="0.9" />
        """
    if visual == "powder":
        return f"""
        <circle cx="126" cy="96" r="18" fill="#fffdf7" opacity="0.95" />
        <circle cx="160" cy="110" r="24" fill="#fffdf7" opacity="0.92" />
        <circle cx="194" cy="132" r="18" fill="#fffdf7" opacity="0.95" />
        <circle cx="144" cy="136" r="12" fill="#f9f6ee" opacity="0.9" />
        """
    if visual == "chlorosis":
        return f"""
        <ellipse cx="146" cy="112" rx="32" ry="44" fill="#f6db72" opacity="0.78" />
        <ellipse cx="194" cy="100" rx="24" ry="36" fill="#f1c852" opacity="0.72" />
        """
    if visual == "necrosis":
        return f"""
        <path d="M126 88 C154 72, 184 86, 188 112 C192 144, 158 156, 128 146 C114 126, 114 100, 126 88 Z" fill="{stroke}" opacity="0.8" />
        <path d="M186 98 C206 100, 216 118, 208 138 C190 146, 174 134, 172 118 C172 108, 178 100, 186 98 Z" fill="{accent}" opacity="0.75" />
        """
    if visual == "blight":
        return f"""
        <path d="M104 76 C140 82, 158 116, 140 154 C112 156, 92 128, 104 76 Z" fill="{stroke}" opacity="0.74" />
        <path d="M188 84 C224 96, 232 132, 206 160 C176 154, 170 114, 188 84 Z" fill="{accent}" opacity="0.72" />
        """
    if visual == "water-soaked":
        return f"""
        <ellipse cx="140" cy="102" rx="24" ry="18" fill="#cfe0ea" opacity="0.88" stroke="{accent}" stroke-width="3" />
        <ellipse cx="188" cy="126" rx="30" ry="20" fill="#dbe9f2" opacity="0.9" stroke="{accent}" stroke-width="3" />
        """
    if visual == "canker":
        return f"""
        <ellipse cx="160" cy="112" rx="28" ry="38" fill="{accent}" opacity="0.76" />
        <path d="M146 92 L176 132 M176 92 L146 132" stroke="{highlight}" stroke-width="4" stroke-linecap="round" />
        <ellipse cx="160" cy="112" rx="36" ry="46" fill="none" stroke="{stroke}" stroke-width="5" opacity="0.85" />
        """
    if visual == "rot":
        return f"""
        <path d="M128 108 C144 84, 194 88, 212 122 C210 158, 164 170, 136 150 C126 138, 122 124, 128 108 Z" fill="{stroke}" opacity="0.82" />
        <circle cx="188" cy="118" r="10" fill="{accent}" opacity="0.7" />
        """
    if visual == "mold":
        return f"""
        <circle cx="128" cy="96" r="16" fill="#f6f4ee" opacity="0.9" />
        <circle cx="150" cy="118" r="20" fill="#efefe9" opacity="0.9" />
        <circle cx="178" cy="104" r="18" fill="#f8f8f2" opacity="0.9" />
        <circle cx="198" cy="130" r="14" fill="#f1eee7" opacity="0.92" />
        <path d="M120 96 C132 88, 142 88, 154 96" fill="none" stroke="{accent}" stroke-width="3" opacity="0.5" />
        """
    if visual == "rust":
        return f"""
        <circle cx="126" cy="94" r="8" fill="#c45d1b" />
        <circle cx="148" cy="114" r="10" fill="#b94a16" />
        <circle cx="174" cy="100" r="8" fill="#cf6a1f" />
        <circle cx="196" cy="126" r="10" fill="#b14a1b" />
        <circle cx="154" cy="142" r="8" fill="#cc6b20" />
        """
    if visual == "patch":
        return f"""
        <path d="M116 90 C142 72, 170 74, 180 96 C178 120, 144 128, 118 120 C108 110, 108 98, 116 90 Z" fill="#fcfbf4" opacity="0.96" />
        <path d="M180 110 C198 96, 220 102, 224 122 C218 144, 192 148, 176 136 C170 126, 172 116, 180 110 Z" fill="#f7f5ef" opacity="0.96" />
        """
    if visual == "curl":
        return f"""
        <path d="M114 114 C114 78, 150 58, 186 70 C178 100, 154 120, 120 126" fill="none" stroke="{accent}" stroke-width="7" stroke-linecap="round" />
        <path d="M184 92 C212 92, 226 124, 210 146 C188 146, 174 130, 176 108" fill="none" stroke="{stroke}" stroke-width="7" stroke-linecap="round" />
        <circle cx="146" cy="108" r="10" fill="{highlight}" opacity="0.7" />
        """
    if visual == "stunting":
        return f"""
        <path d="M130 140 L130 90" stroke="{stroke}" stroke-width="6" stroke-linecap="round" />
        <path d="M190 156 L190 68" stroke="{accent}" stroke-width="6" stroke-linecap="round" opacity="0.55" stroke-dasharray="8 8" />
        <path d="M130 104 C112 88, 96 96, 92 114 C112 116, 124 112, 130 104 Z" fill="{highlight}" stroke="{stroke}" stroke-width="3" />
        <path d="M130 118 C148 102, 164 108, 170 126 C148 128, 138 124, 130 118 Z" fill="{highlight}" stroke="{stroke}" stroke-width="3" />
        """
    if visual == "seed-discoloration":
        return f"""
        <path d="M122 132 C120 94, 146 70, 176 74 C198 82, 212 110, 202 146 C174 164, 138 158, 122 132 Z" fill="{accent}" opacity="0.75" />
        <path d="M150 72 C164 96, 168 122, 162 156" fill="none" stroke="{stroke}" stroke-width="4" opacity="0.7" />
        """
    if visual == "fruit-lesion":
        return f"""
        <circle cx="146" cy="110" r="16" fill="{stroke}" opacity="0.8" />
        <circle cx="186" cy="128" r="22" fill="{accent}" opacity="0.74" />
        <circle cx="146" cy="110" r="6" fill="{highlight}" opacity="0.65" />
        """

    return f"""
    <circle cx="138" cy="100" r="14" fill="{accent}" opacity="0.72" />
    <circle cx="182" cy="126" r="18" fill="{stroke}" opacity="0.72" />
    """
