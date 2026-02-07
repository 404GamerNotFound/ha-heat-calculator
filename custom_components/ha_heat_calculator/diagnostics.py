"""Diagnostics for HA Heat Calculator."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import HeatCalculatorCoordinator


def _snapshot_heater_state(
    coordinator: HeatCalculatorCoordinator, entity_id: str
) -> dict[str, Any]:
    """Capture key heater state details for diagnostics."""
    state = coordinator.hass.states.get(entity_id)
    if state is None:
        return {
            "entity_id": entity_id,
            "state": None,
            "is_heating": False,
            "hvac_action": None,
            "current_temperature": None,
            "target_temperature": None,
        }

    return {
        "entity_id": entity_id,
        "state": state.state,
        "is_heating": coordinator._is_heating_active(state.state, state.attributes),
        "hvac_action": state.attributes.get("hvac_action"),
        "current_temperature": state.attributes.get("current_temperature"),
        "target_temperature": state.attributes.get("temperature"),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: HeatCalculatorCoordinator = hass.data[DOMAIN][entry.entry_id]
    gas_state = hass.states.get(coordinator.gas_meter_entity_id)

    return {
        "config_entry": {
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "runtime": {
            "gas_meter_entity_id": coordinator.gas_meter_entity_id,
            "gas_meter_state": gas_state.state if gas_state else None,
            "gas_meter_attributes": gas_state.attributes if gas_state else None,
            "heaters": [
                _snapshot_heater_state(coordinator, entity_id)
                for entity_id in coordinator.heaters
            ],
            "calculation_method": coordinator.calculation_method,
            "include_warm_water": coordinator.include_warm_water,
            "warm_water_percent": coordinator.warm_water_percent,
            "gas_price": coordinator.gas_price,
            "last_delta_gas": coordinator.last_delta_gas,
            "last_distributable_gas": coordinator.last_distributable_gas,
            "last_warm_water_deducted": coordinator.last_warm_water_deducted,
            "last_distribution_time": coordinator.last_distribution_time.isoformat()
            if coordinator.last_distribution_time
            else None,
        },
        "allocation": {
            "effort_window": {
                entity_id: stats.effort_window
                for entity_id, stats in coordinator.data.items()
            },
            "total_allocated": {
                entity_id: stats.total_allocated
                for entity_id, stats in coordinator.data.items()
            },
        },
    }
