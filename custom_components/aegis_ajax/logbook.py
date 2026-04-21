"""Logbook descriptions for Aegis for Ajax security events."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.logbook import LOGBOOK_ENTRY_MESSAGE, LOGBOOK_ENTRY_NAME
from homeassistant.core import Event, callback

from custom_components.aegis_ajax.const import DOMAIN

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

_EVENT_DESCRIPTIONS: dict[str, str] = {
    "alarm": "Alarm triggered: {device_name}",
    "arm": "Armed by {device_name}",
    "arm_night": "Night mode armed by {device_name}",
    "battery_low": "Battery low: {device_name}",
    "co_alarm": "CO alarm: {device_name}",
    "connection_lost": "Connection lost: {device_name}",
    "disarm": "Disarmed by {device_name}",
    "disarm_night": "Night mode disarmed by {device_name}",
    "door_open": "Door opened: {device_name}",
    "fire": "Fire detected: {device_name}",
    "flood": "Flood detected: {device_name}",
    "glass_break": "Glass break: {device_name}",
    "malfunction": "Malfunction: {device_name}",
    "motion": "Motion detected: {device_name}",
    "panic": "Panic: {device_name}",
    "tamper": "Tamper: {device_name}",
}


@callback
def async_describe_events(
    hass: HomeAssistant,  # noqa: ARG001
    async_describe_event: Callable[[str, str, Callable[[Event], dict[str, str]]], None],
) -> None:
    """Register logbook event descriptions for Aegis security events."""

    @callback
    def async_describe_aegis_event(event: Event) -> dict[str, str]:
        data: dict[str, Any] = event.data
        event_type = data.get("event_type", "unknown")
        device_name = data.get("device_name", "Unknown device")
        room_name = data.get("room_name")

        template = _EVENT_DESCRIPTIONS.get(event_type, "Security event: {device_name}")
        message = template.format(device_name=device_name)
        if room_name:
            message += f" ({room_name})"

        return {
            LOGBOOK_ENTRY_NAME: "Aegis",
            LOGBOOK_ENTRY_MESSAGE: message,
        }

    async_describe_event(DOMAIN, f"{DOMAIN}_event", async_describe_aegis_event)
