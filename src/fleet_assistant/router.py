from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .models import Language, RouteDecision

ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
VEHICLE_RE = re.compile(
    r"(?:vehicle|voiture|vehicule|car|van|karhba|kraheb|كرهبة|الكرهبة|سيارة|السيارة|عربية|العربية)\s*#?\s*([0-9٠-٩]+)",
    re.IGNORECASE,
)
NUMBER_ONLY_RE = re.compile(r"^\s*([0-9٠-٩]+)\s*$")


@dataclass(frozen=True)
class IntentRule:
    name: str
    terms: tuple[str, ...]
    requires_vehicle: bool = True
    priority: int = 0


RULES = (
    IntentRule(
        "create_ticket",
        (
            "reclamation",
            "réclamation",
            "complaint",
            "signaler",
            "شكوى",
            "مشكلة",
            "mochkel",
            "mouchkla",
        ),
        priority=60,
    ),
    IntentRule(
        "vehicle_engine_time",
        (
            "engine time",
            "temps moteur",
            "moteur combien",
            "moteur 9addech",
            "9addech khdem moteur",
            "9adeh khdem moteur",
            "وقت المحرك",
            "قداش خدم الموتور",
            "مدة تشغيل المحرك",
        ),
        priority=55,
    ),
    IntentRule(
        "vehicle_history",
        (
            "historique",
            "history",
            "hier",
            "yesterday",
            "lbarah",
            "bareh",
            "emes",
            "البارح",
            "أمس",
            "وين مشات",
            "win mchet",
            "route today",
            "trajet",
        ),
        priority=45,
    ),
    IntentRule(
        "vehicle_speed",
        ("vitesse", "speed", "sor3a", "سرعة", "السرعة", "9addech temchi"),
        priority=40,
    ),
    IntentRule(
        "vehicle_status",
        (
            "status",
            "statut",
            "état",
            "etat",
            "moving",
            "stopped",
            "moteur khadem tawa",
            "حالة",
            "واقفة",
            "ماشية",
        ),
        priority=35,
    ),
    IntentRule(
        "vehicle_location",
        (
            "where",
            "position",
            "location",
            "localisation",
            "où",
            "ou est",
            "win",
            "وين",
            "موقع",
            "الموقع",
            "بلاصة",
        ),
        priority=30,
    ),
    IntentRule(
        "fleet_list",
        (
            "mes véhicules",
            "mes vehicules",
            "my vehicles",
            "fleet",
            "flotte",
            "krahebi",
            "سياراتي",
            "العربات",
        ),
        requires_vehicle=False,
        priority=20,
    ),
)


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text).lower().strip()
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = unicodedata.normalize("NFKC", value)
    value = value.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    value = re.sub(r"[^\w\u0600-\u06ff]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def detect_language(text: str) -> Language:
    if ARABIC_RE.search(text):
        return "tn_ar"
    lowered = normalize(text)
    arabizi_markers = {
        "win",
        "karhba",
        "lkarhba",
        "krahebi",
        "9addech",
        "9adeh",
        "mchet",
        "tawa",
        "lbarah",
        "bareh",
        "moteur",
        "mochkel",
    }
    if any(token in lowered.split() for token in arabizi_markers) or re.search(r"[3579]", lowered):
        return "tn_latn"
    english_markers = {"where", "speed", "history", "vehicle", "fleet", "engine", "complaint"}
    if any(token in lowered.split() for token in english_markers):
        return "en"
    return "fr"


def extract_vehicle_id(text: str) -> int | None:
    normalized = normalize(text)
    match = VEHICLE_RE.search(normalized)
    if match:
        return int(match.group(1))
    match = NUMBER_ONLY_RE.match(normalized)
    return int(match.group(1)) if match else None


def route(text: str) -> RouteDecision:
    normalized = normalize(text)
    language = detect_language(text)
    vehicle_id = extract_vehicle_id(text)

    ranked: list[tuple[int, IntentRule, list[str]]] = []
    for rule in RULES:
        hits = [term for term in rule.terms if normalize(term) in normalized]
        if hits:
            ranked.append((rule.priority + 8 * len(hits), rule, hits))

    if not ranked:
        return RouteDecision(
            intent="unknown",
            confidence=0.0,
            language=language,
            vehicle_id=vehicle_id,
        )

    ranked.sort(key=lambda item: item[0], reverse=True)
    score, winner, hits = ranked[0]
    margin = score - ranked[1][0] if len(ranked) > 1 else 20
    confidence = min(0.98, 0.62 + 0.06 * len(hits) + 0.01 * max(0, margin))
    return RouteDecision(
        intent=winner.name,
        confidence=round(confidence, 3),
        language=language,
        vehicle_id=vehicle_id,
        evidence=hits[:3],
    )


def requires_vehicle(intent: str) -> bool:
    rule = next((item for item in RULES if item.name == intent), None)
    return bool(rule and rule.requires_vehicle)
