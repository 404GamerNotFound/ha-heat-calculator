"""Data update coordinator for HA Heat Calculator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CALCULATION_METHOD,
    CONF_GAS_METER_ENTITY,
    CONF_HEATERS,
    CONF_INCLUDE_WARM_WATER,
    CONF_WARM_WATER_PERCENT,
    DEFAULT_CALCULATION_METHOD,
    DEFAULT_INCLUDE_WARM_WATER,
    DEFAULT_WARM_WATER_PERCENT,
    DOMAIN,
    UPDATE_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)
MIN_WARM_WATER_PERCENT = 0.0
MAX_WARM_WATER_PERCENT = 100.0


@dataclass
class HeaterStats:
    """Track effort and allocated gas for one heater."""

    effort_window: float = 0.0
    total_allocated: float = 0.0


class HeatCalculatorCoordinator(DataUpdateCoordinator[dict[str, HeaterStats]]):
    """Coordinate gas distribution updates."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.config_entry = entry

        self._last_sample_time: datetime | None = None
        self._last_gas_value: float | None = None
        self.last_delta_gas: float = 0.0
        self.last_distributable_gas: float = 0.0
        self.last_warm_water_deducted: float = 0.0
        self.last_distribution_time: datetime | None = None

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )

        self._apply_config()

    def _apply_config(self) -> None:
        """Load and apply current config/option values."""
        entry = self.config_entry
        self.gas_meter_entity_id = entry.options.get(
            CONF_GAS_METER_ENTITY, entry.data[CONF_GAS_METER_ENTITY]
        )
        self.heaters = entry.options.get(CONF_HEATERS, entry.data[CONF_HEATERS])
        self.include_warm_water = bool(
            entry.options.get(
                CONF_INCLUDE_WARM_WATER,
                entry.data.get(CONF_INCLUDE_WARM_WATER, DEFAULT_INCLUDE_WARM_WATER),
            )
        )
        self.warm_water_percent = self._sanitize_warm_water_percent(
            entry.options.get(
                CONF_WARM_WATER_PERCENT,
                entry.data.get(CONF_WARM_WATER_PERCENT, DEFAULT_WARM_WATER_PERCENT),
            )
        )
        self.calculation_method = entry.options.get(
            CONF_CALCULATION_METHOD,
            entry.data.get(CONF_CALCULATION_METHOD, DEFAULT_CALCULATION_METHOD),
        )

        existing = self.data or {}
        self.data = {
            entity_id: HeaterStats(total_allocated=existing.get(entity_id, HeaterStats()).total_allocated)
            for entity_id in self.heaters
        }

    async def async_update_options(self, updates: dict) -> None:
        """Persist updated options and refresh runtime configuration."""
        new_options = {**self.config_entry.options, **updates}
        self.hass.config_entries.async_update_entry(self.config_entry, options=new_options)
        self._apply_config()
        self.async_update_listeners()
        await self.async_request_refresh()

    @staticmethod
    def _sanitize_warm_water_percent(value: Any) -> float:
        """Convert and clamp the warm-water share to a safe percentage range."""
        try:
            percent = float(value)
        except (TypeError, ValueError):
            return DEFAULT_WARM_WATER_PERCENT

        return min(MAX_WARM_WATER_PERCENT, max(MIN_WARM_WATER_PERCENT, percent))

    async def _async_update_data(self) -> dict[str, HeaterStats]:
        """Collect heating effort and distribute gas increments."""
        now = dt_util.utcnow()

        if self._last_sample_time is None:
            self._last_sample_time = now
            self._last_gas_value = self._read_gas_meter()
            return self.data

        elapsed_seconds = (now - self._last_sample_time).total_seconds()
        self._last_sample_time = now

        if elapsed_seconds > 0:
            self._add_heating_effort(elapsed_seconds)

        current_gas = self._read_gas_meter()
        if current_gas is None:
            return self.data

        if self._last_gas_value is None:
            self._last_gas_value = current_gas
            return self.data

        delta = current_gas - self._last_gas_value
        if delta > 0:
            self._distribute_gas(delta)
            self._last_gas_value = current_gas
        elif delta < 0:
            # Meter resets are handled by syncing the baseline to the new value.
            self._last_gas_value = current_gas

        return self.data

    def _read_gas_meter(self) -> float | None:
        """Read the current gas meter state as float."""
        state = self.hass.states.get(self.gas_meter_entity_id)
        if state is None:
            return None

        try:
            return float(state.state)
        except (TypeError, ValueError):
            return None

    def _add_heating_effort(self, elapsed_seconds: float) -> None:
        """Update each heater's effort based on current runtime and method."""
        for heater_entity_id, heater_stats in self.data.items():
            state = self.hass.states.get(heater_entity_id)
            if state is None:
                continue

            if not self._is_heating_active(state.state, state.attributes):
                continue

            effort_factor = 1.0
            if self.calculation_method == "runtime_temp_weighted":
                effort_factor = self._temperature_weight(state.attributes)

            heater_stats.effort_window += elapsed_seconds * effort_factor

    @staticmethod
    def _is_heating_active(state_value: str, attributes: dict) -> bool:
        """Estimate whether a thermostat is currently heating."""
        hvac_action = attributes.get("hvac_action")
        if hvac_action == "heating":
            return True

        if state_value != "heat":
            return False

        current_temperature = attributes.get("current_temperature")
        target_temperature = attributes.get("temperature")
        if current_temperature is None or target_temperature is None:
            return False

        try:
            return float(current_temperature) < float(target_temperature)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _temperature_weight(attributes: dict[str, Any]) -> float:
        """Return a weighting factor derived from target/current temperature."""
        current_temperature = attributes.get("current_temperature")
        target_temperature = attributes.get("temperature")
        if current_temperature is None or target_temperature is None:
            return 1.0

        try:
            delta = float(target_temperature) - float(current_temperature)
        except (TypeError, ValueError):
            return 1.0

        return max(0.5, min(3.0, 1.0 + max(delta, 0.0) * 0.25))

    def _distribute_gas(self, delta_gas: float) -> None:
        """Distribute a gas meter delta to all configured heaters."""
        if not self.data:
            self.last_delta_gas = delta_gas
            self.last_distributable_gas = 0.0
            self.last_warm_water_deducted = 0.0
            self.last_distribution_time = dt_util.utcnow()
            return

        distributable = delta_gas
        self.last_delta_gas = delta_gas
        if self.include_warm_water:
            distributable = delta_gas * (1 - (self.warm_water_percent / 100.0))
        self.last_distributable_gas = distributable
        self.last_warm_water_deducted = max(delta_gas - distributable, 0.0)
        self.last_distribution_time = dt_util.utcnow()

        if distributable <= 0:
            self._reset_effort_window()
            return

        total_effort = sum(stats.effort_window for stats in self.data.values())

        if total_effort <= 0:
            # If no heating runtime was seen, distribute equally as a fallback.
            equal_share = distributable / len(self.data)
            for stats in self.data.values():
                stats.total_allocated += equal_share
            self._reset_effort_window()
            return

        for stats in self.data.values():
            ratio = stats.effort_window / total_effort
            stats.total_allocated += distributable * ratio

        self._reset_effort_window()

    def _reset_effort_window(self) -> None:
        """Clear temporary effort values after a gas allocation round."""
        for stats in self.data.values():
            stats.effort_window = 0.0
