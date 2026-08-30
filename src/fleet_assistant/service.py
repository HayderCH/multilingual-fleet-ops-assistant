from __future__ import annotations

from uuid import uuid4

from .catalog import list_vehicles, vehicle
from .models import ChatResponse, RouteDecision, SessionState
from .router import extract_vehicle_id, requires_vehicle, route
from .sessions import SessionStore

YES = {"yes", "oui", "ok", "confirm", "confirmer", "نعم", "اي", "ey", "ena موافق"}
NO = {"no", "non", "cancel", "annuler", "لا", "le", "لا شكرا"}


def _reply(language: str, key: str, **values: object) -> str:
    templates = {
        "vehicle_prompt": {
            "fr": "Quel véhicule souhaitez-vous consulter ? Indiquez son numéro.",
            "en": "Which vehicle should I use? Send its number.",
            "tn_ar": "شنية الكرهبة اللي تقصدها؟ ابعث رقمها.",
            "tn_latn": "Anahi karhba ta9sed? Ab3ath ra9mha.",
        },
        "unknown_vehicle": {
            "fr": "Le véhicule {vehicle_id} n'existe pas dans cette flotte de démonstration.",
            "en": "Vehicle {vehicle_id} is not present in this demo fleet.",
            "tn_ar": "الكرهبة رقم {vehicle_id} موش موجودة في flotte التجريبية.",
            "tn_latn": "Karhba {vehicle_id} mch mawjouda fel flotte demo.",
        },
        "unknown": {
            "fr": (
                "Je peux aider avec la position, la vitesse, l'état, "
                "l'historique ou le temps moteur."
            ),
            "en": "I can help with location, speed, status, history, or engine time.",
            "tn_ar": "نجم نعاونك في الموقع، السرعة، الحالة، التاريخ ولا وقت المحرك.",
            "tn_latn": "Najem n3awnek fel position, vitesse, status, historique wala temps moteur.",
        },
        "confirm": {
            "fr": "Confirmez-vous la création d'un ticket pour le véhicule {vehicle_id} ?",
            "en": "Confirm ticket creation for vehicle {vehicle_id}?",
            "tn_ar": "تأكد إنشاء شكوى للكرهبة {vehicle_id}؟",
            "tn_latn": "Tconfirmi creation reclamation lel karhba {vehicle_id}?",
        },
        "cancelled": {
            "fr": "Action annulée. Aucun ticket n'a été créé.",
            "en": "Cancelled. No ticket was created.",
            "tn_ar": "تلغات العملية وما تعمل حتى ticket.",
            "tn_latn": "Telghat l operation, ma tsna3 hata ticket.",
        },
        "ticket_created": {
            "fr": "Ticket {ticket_id} créé pour le véhicule de démonstration {vehicle_id}.",
            "en": "Ticket {ticket_id} created for demo vehicle {vehicle_id}.",
            "tn_ar": "تعمل ticket {ticket_id} للكرهبة التجريبية {vehicle_id}.",
            "tn_latn": "Tsana3 ticket {ticket_id} lel karhba demo {vehicle_id}.",
        },
    }
    language_templates = templates[key]
    return language_templates.get(language, language_templates["fr"]).format(**values)


class FleetAssistant:
    def __init__(self, sessions: SessionStore) -> None:
        self.sessions = sessions

    async def process(self, text: str, conversation_id: str | None = None) -> ChatResponse:
        conversation_id = conversation_id or str(uuid4())
        state = await self.sessions.get(conversation_id)
        normalized_answer = text.lower().strip()

        if state.pending_confirmation:
            decision = RouteDecision(
                intent="create_ticket",
                confidence=1.0,
                language=route(text).language,
                vehicle_id=state.pending_vehicle_id,
                evidence=["session_confirmation"],
            )
            if normalized_answer in YES:
                ticket_id = f"DEMO-{uuid4().hex[:8].upper()}"
                vehicle_id = state.pending_vehicle_id
                await self.sessions.set(conversation_id, SessionState(last_vehicle_id=vehicle_id))
                return ChatResponse(
                    conversation_id=conversation_id,
                    status="complete",
                    reply=_reply(
                        decision.language,
                        "ticket_created",
                        ticket_id=ticket_id,
                        vehicle_id=vehicle_id,
                    ),
                    route=decision,
                    data={"ticket_id": ticket_id, "vehicle_id": vehicle_id, "synthetic": True},
                )
            if normalized_answer in NO:
                await self.sessions.set(
                    conversation_id, SessionState(last_vehicle_id=state.pending_vehicle_id)
                )
                return ChatResponse(
                    conversation_id=conversation_id,
                    status="cancelled",
                    reply=_reply(decision.language, "cancelled"),
                    route=decision,
                )

        decision = route(text)
        if state.pending_intent:
            followup_vehicle = extract_vehicle_id(text)
            if followup_vehicle is not None:
                decision = RouteDecision(
                    intent=state.pending_intent,
                    confidence=1.0,
                    language=decision.language,
                    vehicle_id=followup_vehicle,
                    evidence=["session_clarification"],
                )

        if decision.intent == "unknown":
            return ChatResponse(
                conversation_id=conversation_id,
                status="unsupported",
                reply=_reply(decision.language, "unknown"),
                route=decision,
            )

        if requires_vehicle(decision.intent) and decision.vehicle_id is None:
            await self.sessions.set(
                conversation_id,
                SessionState(pending_intent=decision.intent, last_vehicle_id=state.last_vehicle_id),
            )
            return ChatResponse(
                conversation_id=conversation_id,
                status="awaiting_clarification",
                reply=_reply(decision.language, "vehicle_prompt"),
                route=decision,
            )

        if decision.intent == "fleet_list":
            rows = list_vehicles()
            await self.sessions.set(conversation_id, SessionState())
            return ChatResponse(
                conversation_id=conversation_id,
                status="complete",
                reply=f"{len(rows)} demo vehicles are available.",
                route=decision,
                data=rows,
            )

        vehicle_id = decision.vehicle_id
        row = vehicle(vehicle_id or -1)
        if row is None:
            return ChatResponse(
                conversation_id=conversation_id,
                status="unsupported",
                reply=_reply(decision.language, "unknown_vehicle", vehicle_id=vehicle_id),
                route=decision,
            )

        if decision.intent == "create_ticket":
            await self.sessions.set(
                conversation_id,
                SessionState(
                    pending_vehicle_id=vehicle_id,
                    pending_confirmation=True,
                    last_vehicle_id=vehicle_id,
                ),
            )
            return ChatResponse(
                conversation_id=conversation_id,
                status="awaiting_confirmation",
                reply=_reply(decision.language, "confirm", vehicle_id=vehicle_id),
                route=decision,
            )

        reply, data = self._execute_read(decision.intent, row, decision.language)
        await self.sessions.set(conversation_id, SessionState(last_vehicle_id=vehicle_id))
        return ChatResponse(
            conversation_id=conversation_id,
            status="complete",
            reply=reply,
            route=decision,
            data=data,
        )

    @staticmethod
    def _execute_read(
        intent: str, row: dict[str, object], language: str
    ) -> tuple[str, dict[str, object]]:
        label = str(row["label"])
        if intent == "vehicle_location":
            data = {
                "vehicle_id": row["vehicle_id"],
                "city": row["city"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "synthetic": True,
            }
            replies = {
                "fr": f"{label} se trouve actuellement à {row['city']}.",
                "en": f"{label} is currently in {row['city']}.",
                "tn_ar": f"{label} موجودة توا في {row['city']}.",
                "tn_latn": f"{label} mawjouda tawa fi {row['city']}.",
            }
            return replies.get(language, replies["fr"]), data
        if intent == "vehicle_speed":
            data = {
                "vehicle_id": row["vehicle_id"],
                "speed_kmh": row["speed_kmh"],
                "synthetic": True,
            }
            replies = {
                "fr": f"La vitesse de {label} est de {row['speed_kmh']} km/h.",
                "en": f"{label} is travelling at {row['speed_kmh']} km/h.",
                "tn_ar": f"سرعة {label} هي {row['speed_kmh']} كم/س.",
                "tn_latn": f"Vitesse mta3 {label} hiya {row['speed_kmh']} km/h.",
            }
            return replies.get(language, replies["fr"]), data
        if intent == "vehicle_status":
            data = {
                "vehicle_id": row["vehicle_id"],
                "status": row["status"],
                "synthetic": True,
            }
            replies = {
                "fr": f"L'état de {label} est {row['status']}.",
                "en": f"{label} is {row['status']}.",
                "tn_ar": f"حالة {label}: {row['status']}.",
                "tn_latn": f"Status mta3 {label}: {row['status']}.",
            }
            return replies.get(language, replies["fr"]), data
        if intent == "vehicle_engine_time":
            data = {
                "vehicle_id": row["vehicle_id"],
                "engine_minutes_today": row["engine_minutes_today"],
                "synthetic": True,
            }
            minutes = row["engine_minutes_today"]
            replies = {
                "fr": f"Le moteur de {label} a fonctionné {minutes} minutes aujourd'hui.",
                "en": f"{label}'s engine has run for {minutes} minutes today.",
                "tn_ar": f"موتور {label} خدم {minutes} دقيقة اليوم.",
                "tn_latn": f"Moteur mta3 {label} khdem {minutes} minutes lyoum.",
            }
            return replies.get(language, replies["fr"]), data
        data = {
            "vehicle_id": row["vehicle_id"],
            "period": "today",
            "distance_km": row["distance_km_today"],
            "synthetic": True,
        }
        distance = row["distance_km_today"]
        replies = {
            "fr": f"{label} a parcouru {distance} km aujourd'hui.",
            "en": f"{label} travelled {distance} km today.",
            "tn_ar": f"{label} مشات {distance} كم اليوم.",
            "tn_latn": f"{label} mchet {distance} km lyoum.",
        }
        return replies.get(language, replies["fr"]), data
