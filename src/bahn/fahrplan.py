from __future__ import annotations

from typing import Any

from .models import FahrplanSearchInput

DEFAULT_PRODUCTS = [
    "ICE",
    "EC_IC",
    "IR",
    "REGIONAL",
    "SBAHN",
    "BUS",
    "SCHIFF",
    "UBAHN",
    "TRAM",
    "ANRUFPFLICHTIG",
]

_AGE_GROUP_LABELS = (
    (6, "KLEINKIND"),
    (15, "FAMILIENKIND"),
    (27, "JUGENDLICHER"),
    (65, "ERWACHSENER"),
    (120, "SENIOR"),
)


def passenger_type_for_age(age: int) -> str:
    for upper_bound, label in _AGE_GROUP_LABELS:
        if age < upper_bound:
            return label
    return "SENIOR"


def build_discount(search: FahrplanSearchInput) -> dict[str, str]:
    travel_class = "KLASSE_1" if search.travel_class == 1 else "KLASSE_2"
    if search.bahn_card is not None:
        return {"art": f"BAHNCARD{search.bahn_card}", "klasse": travel_class}
    return {"art": "KEINE_ERMAESSIGUNG", "klasse": "KLASSENLOS"}


def build_reisende(search: FahrplanSearchInput) -> list[dict[str, Any]]:
    passenger_type = (
        passenger_type_for_age(search.passenger_age)
        if search.passenger_age is not None
        else "ERWACHSENER"
    )
    alter: list[str] = []
    if search.passenger_age is not None:
        alter = [str(search.passenger_age)]

    return [
        {
            "typ": passenger_type,
            "anzahl": 1,
            "alter": alter,
            "ermaessigungen": [build_discount(search)],
        }
    ]


def build_fahrplan_body(
    from_id: str,
    to_id: str,
    search: FahrplanSearchInput,
) -> dict[str, Any]:
    return {
        "abfahrtsHalt": from_id,
        "ankunftsHalt": to_id,
        "anfrageZeitpunkt": search.departure_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "ankunftSuche": "ABFAHRT",
        "klasse": "KLASSE_1" if search.travel_class == 1 else "KLASSE_2",
        "maxUmstiege": search.max_transfers,
        "schnelleVerbindungen": True,
        "deutschlandTicketVorhanden": search.has_deutschland_ticket,
        "nurDeutschlandTicketVerbindungen": search.deutschland_ticket_only,
        "reservierungsKontingenteVorhanden": False,
        "sitzplatzOnly": False,
        "reisende": build_reisende(search),
        "produktgattungen": DEFAULT_PRODUCTS,
    }
