from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class OrtSearchInput(BaseModel):
    """Input for GET /reiseloesung/orte."""

    query: str = Field(min_length=1)
    typ: Literal["ALL", "BAHNHOF", "ORT", "POI"] = "ALL"
    limit: int = Field(default=5, ge=1, le=50)


class FahrplanSearchInput(BaseModel):
    """Input for POST /angebote/fahrplan."""

    origin: str = Field(min_length=2)
    destination: str = Field(min_length=2)
    departure_at: datetime
    travel_class: Literal[1, 2] = 2
    passenger_age: int | None = Field(default=None, ge=0, le=120)
    bahn_card: Literal[25, 50, 100] | None = None
    has_deutschland_ticket: bool = False
    deutschland_ticket_only: bool = False
    max_transfers: int = Field(default=5, ge=0, le=10)

    @field_validator("bahn_card", mode="before")
    @classmethod
    def _normalize_bahn_card(cls, value: object) -> int | None:
        if value is None or value == "none" or value == "":
            return None
        return int(value)  # type: ignore[arg-type]

    @classmethod
    def from_actor_input(cls, raw: dict[str, Any]) -> FahrplanSearchInput:
        departure_raw = raw.get("departureDateTime")
        if departure_raw:
            departure_at = datetime.fromisoformat(str(departure_raw))
        else:
            travel_date = date.fromisoformat(str(raw["travelDate"]))
            hour = int(raw.get("departureHour", 8))
            minute = int(raw.get("departureMinute", 0))
            departure_at = datetime.combine(travel_date, time(hour, minute))
        return cls(
            origin=str(raw["origin"]).strip(),
            destination=str(raw["destination"]).strip(),
            departure_at=departure_at,
            travel_class=raw.get("travelClass", 2),  # type: ignore[arg-type]
            passenger_age=raw.get("passengerAge"),
            bahn_card=raw.get("bahnCard"),  # type: ignore[arg-type]
            has_deutschland_ticket=bool(raw.get("hasDeutschlandTicket", False)),
            deutschland_ticket_only=bool(raw.get("deutschlandTicketOnly", False)),
            max_transfers=int(raw.get("maxTransfers", 5)),
        )
