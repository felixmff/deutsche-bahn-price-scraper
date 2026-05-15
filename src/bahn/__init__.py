"""Unofficial client for bahn.de web API (reiseloesung/orte, angebote/fahrplan)."""

from .client import BahnWebClient
from .models import FahrplanSearchInput, OrtSearchInput

__all__ = ["BahnWebClient", "FahrplanSearchInput", "OrtSearchInput"]
