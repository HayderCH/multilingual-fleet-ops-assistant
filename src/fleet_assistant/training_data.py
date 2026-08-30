from __future__ import annotations

from itertools import product

TEMPLATES: dict[str, dict[str, list[str]]] = {
    "vehicle_location": {
        "fr": ["où est {vehicle}", "position actuelle {vehicle}", "localisation de {vehicle}"],
        "tn_latn": ["win {vehicle} tawa", "position mta3 {vehicle}", "a3tini blaset {vehicle}"],
        "tn_ar": ["وين {vehicle} توا", "موقع {vehicle}", "اعطيني بلاصة {vehicle}"],
        "en": ["where is {vehicle}", "current location of {vehicle}", "locate {vehicle}"],
    },
    "vehicle_speed": {
        "fr": ["vitesse de {vehicle}", "à quelle vitesse roule {vehicle}", "km h {vehicle}"],
        "tn_latn": ["vitesse mta3 {vehicle}", "9addech temchi {vehicle}", "sor3a {vehicle}"],
        "tn_ar": ["سرعة {vehicle}", "قداش ماشية {vehicle}", "السرعة متاع {vehicle}"],
        "en": ["speed of {vehicle}", "how fast is {vehicle}", "vehicle speed {vehicle}"],
    },
    "vehicle_status": {
        "fr": ["état de {vehicle}", "statut {vehicle}", "est-ce que {vehicle} roule"],
        "tn_latn": ["status mta3 {vehicle}", "{vehicle} temchi wala we9fa", "etat {vehicle}"],
        "tn_ar": ["حالة {vehicle}", "{vehicle} ماشية ولا واقفة", "وضعية {vehicle}"],
        "en": ["status of {vehicle}", "is {vehicle} moving", "vehicle state {vehicle}"],
    },
    "vehicle_history": {
        "fr": ["historique de {vehicle}", "trajet de {vehicle} hier", "où est allée {vehicle}"],
        "tn_latn": ["historique {vehicle}", "win mchet {vehicle} lbarah", "trajet mta3 {vehicle}"],
        "tn_ar": ["تاريخ {vehicle}", "وين مشات {vehicle} البارح", "مسار {vehicle}"],
        "en": ["history of {vehicle}", "where did {vehicle} go yesterday", "trip of {vehicle}"],
    },
    "vehicle_engine_time": {
        "fr": ["temps moteur {vehicle}", "durée moteur de {vehicle}", "combien moteur {vehicle}"],
        "tn_latn": [
            "9addech khdem moteur {vehicle}",
            "temps moteur {vehicle}",
            "wa9t moteur {vehicle}",
        ],
        "tn_ar": ["قداش خدم موتور {vehicle}", "وقت المحرك {vehicle}", "مدة تشغيل موتور {vehicle}"],
        "en": ["engine time {vehicle}", "engine duration {vehicle}", "how long engine {vehicle}"],
    },
    "create_ticket": {
        "fr": [
            "réclamation pour {vehicle}",
            "signaler problème {vehicle}",
            "créer ticket {vehicle}",
        ],
        "tn_latn": ["reclamation {vehicle}", "nheb nechki ala {vehicle}", "mochkel fi {vehicle}"],
        "tn_ar": ["شكوى على {vehicle}", "نحب نشكي على {vehicle}", "مشكلة في {vehicle}"],
        "en": ["complaint for {vehicle}", "report issue with {vehicle}", "create ticket {vehicle}"],
    },
    "fleet_list": {
        "fr": ["mes véhicules", "liste de la flotte", "afficher toutes les voitures"],
        "tn_latn": ["warrini krahebi", "liste flotte", "chneya l kraheb mte3i"],
        "tn_ar": ["وريني سياراتي", "قائمة العربات", "شنية الكراهب متاعي"],
        "en": ["my vehicles", "list the fleet", "show all cars"],
    },
}

VEHICLES = {
    "fr": ["voiture 2", "véhicule 4", "camion 7"],
    "tn_latn": ["karhba 2", "voiture 4", "camion 7"],
    "tn_ar": ["الكرهبة ٢", "السيارة 4", "الشاحنة ٧"],
    "en": ["vehicle 2", "car 4", "truck 7"],
}

WRAPPERS = ("{}", "svp {}", "{} maintenant", "brabi {}")


def generate_training_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for intent, by_language in TEMPLATES.items():
        for language, templates in by_language.items():
            vehicles = [""] if intent == "fleet_list" else VEHICLES[language]
            for template, vehicle, wrapper in product(templates, vehicles, WRAPPERS):
                query = wrapper.format(template.format(vehicle=vehicle)).strip()
                rows.append({"query": query, "intent": intent, "language": language})
    return rows
