from fastapi.testclient import TestClient

from fleet_assistant.api import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json() == {"status": "ok", "data": "synthetic"}


def test_location_response_is_traceable_and_synthetic() -> None:
    response = client.post("/chat", json={"text": "Où est la voiture 4 ?"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "complete"
    assert body["route"]["intent"] == "vehicle_location"
    assert body["data"]["synthetic"] is True


def test_public_classifier_endpoint() -> None:
    response = client.post("/classify", json={"text": "win karhba 4 tawa"})
    assert response.status_code == 200
    body = response.json()
    assert body["training_data"] == "synthetic"
    assert body["candidates"][0]["intent"] == "vehicle_location"


def test_clarification_keeps_conversation_state() -> None:
    conversation_id = "clarification-test"
    first = client.post(
        "/chat", json={"text": "où est la voiture ?", "conversation_id": conversation_id}
    ).json()
    assert first["status"] == "awaiting_clarification"

    second = client.post("/chat", json={"text": "4", "conversation_id": conversation_id}).json()
    assert second["status"] == "complete"
    assert second["route"]["vehicle_id"] == 4


def test_mutation_requires_confirmation() -> None:
    conversation_id = "confirmation-test"
    first = client.post(
        "/chat",
        json={"text": "signaler une réclamation voiture 2", "conversation_id": conversation_id},
    ).json()
    assert first["status"] == "awaiting_confirmation"
    assert first["data"] is None

    second = client.post("/chat", json={"text": "oui", "conversation_id": conversation_id}).json()
    assert second["status"] == "complete"
    assert second["data"]["synthetic"] is True
    assert second["data"]["ticket_id"].startswith("DEMO-")
