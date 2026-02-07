"""Device helpers for HA Heat Calculator."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOCUMENTATION_URL, DOMAIN


def build_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Build the DeviceInfo used by all platform entities."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="HA Heat Calculator",
        model="Heat Allocation",
        configuration_url=DOCUMENTATION_URL,
        entry_type=DeviceEntryType.SERVICE,
    )
