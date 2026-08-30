import pytest

from fleet_assistant.router import detect_language, route


@pytest.mark.parametrize(
    ("query", "intent", "vehicle_id"),
    [
        ("Où est la voiture 4 ?", "vehicle_location", 4),
        ("quelle est la vitesse du véhicule 2", "vehicle_speed", 2),
        ("historique voiture 4 hier", "vehicle_history", 4),
        ("9addech khdem moteur karhba 2", "vehicle_engine_time", 2),
        ("win karhba 4 tawa", "vehicle_location", 4),
        ("وين الكرهبة 4؟", "vehicle_location", 4),
        ("قداش خدم الموتور متاع السيارة ٢", "vehicle_engine_time", 2),
        ("je veux signaler une réclamation voiture 4", "create_ticket", 4),
        ("montre mes véhicules", "fleet_list", None),
    ],
)
def test_routes(query: str, intent: str, vehicle_id: int | None) -> None:
    decision = route(query)
    assert decision.intent == intent
    assert decision.vehicle_id == vehicle_id


def test_language_detection() -> None:
    assert detect_language("Où est la voiture 4 ?") == "fr"
    assert detect_language("win karhba 4 tawa") == "tn_latn"
    assert detect_language("وين الكرهبة 4؟") == "tn_ar"
    assert detect_language("where is vehicle 4") == "en"
