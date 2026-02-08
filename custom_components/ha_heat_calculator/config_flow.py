"""Config flow for HA Heat Calculator."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.selector import SelectSelectorConfig
from homeassistant.loader import IntegrationNotFound, async_get_integration

from .const import (
    CALCULATION_METHODS,
    CONF_CALCULATION_METHOD,
    CONF_GAS_METER_ENTITY,
    CONF_GAS_PRICE,
    CONF_HEATERS,
    CONF_INCLUDE_WARM_WATER,
    CONF_WARM_WATER_PERCENT,
    DEFAULT_CALCULATION_METHOD,
    DEFAULT_GAS_PRICE,
    DEFAULT_INCLUDE_WARM_WATER,
    DEFAULT_WARM_WATER_PERCENT,
    DOMAIN,
)


class HeatCalculatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Heat Calculator."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_HEATERS):
                errors[CONF_HEATERS] = "at_least_one_heater"
            else:
                return self.async_create_entry(title="Heat Calculator", data=user_input)

        defaults = user_input or {}
        if CONF_GAS_PRICE not in defaults:
            energy_price = await _async_get_energy_gas_price(self.hass)
            if energy_price is not None:
                defaults = {**defaults, CONF_GAS_PRICE: energy_price}

        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(defaults),
            errors=errors,
        )

    @staticmethod
    def _build_schema(defaults: dict | None = None) -> vol.Schema:
        """Build a reusable schema for create/options flow."""
        defaults = defaults or {}

        def _required_key(key: str, fallback=vol.UNDEFINED) -> vol.Required:
            """Return a required key with an optional default if available."""
            if key in defaults:
                return vol.Required(key, default=defaults[key])
            if fallback is not vol.UNDEFINED:
                return vol.Required(key, default=fallback)
            return vol.Required(key)

        return vol.Schema(
            {
                _required_key(CONF_GAS_METER_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"], multiple=False)
                ),
                _required_key(CONF_HEATERS, []): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["climate"], multiple=True)
                ),
                _required_key(
                    CONF_INCLUDE_WARM_WATER, DEFAULT_INCLUDE_WARM_WATER
                ): selector.BooleanSelector(),
                _required_key(
                    CONF_WARM_WATER_PERCENT, DEFAULT_WARM_WATER_PERCENT
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=1)
                ),
                _required_key(
                    CONF_CALCULATION_METHOD, DEFAULT_CALCULATION_METHOD
                ): selector.SelectSelector(
                    SelectSelectorConfig(
                        options=list(CALCULATION_METHODS.keys()),
                        mode="dropdown",
                        translation_key=CONF_CALCULATION_METHOD,
                    )
                ),
                _required_key(CONF_GAS_PRICE, DEFAULT_GAS_PRICE): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=0.01)
                ),
            }
        )


    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return HeatCalculatorOptionsFlow(config_entry)


class HeatCalculatorOptionsFlow(config_entries.OptionsFlow):
    """Handle integration options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_HEATERS):
                errors[CONF_HEATERS] = "at_least_one_heater"
            else:
                return self.async_create_entry(title="", data=user_input)

        defaults = user_input or {**self.config_entry.data, **self.config_entry.options}
        if CONF_GAS_PRICE not in defaults:
            energy_price = await _async_get_energy_gas_price(self.hass)
            if energy_price is not None:
                defaults = {**defaults, CONF_GAS_PRICE: energy_price}
        return self.async_show_form(
            step_id="init",
            data_schema=HeatCalculatorConfigFlow._build_schema(defaults),
            errors=errors,
        )


async def _async_get_energy_gas_price(hass) -> float | None:
    """Return the fixed gas price from the Energy dashboard if configured."""
    try:
        await async_get_integration(hass, "energy")
        from homeassistant.components.energy.data import async_get_manager
    except (ImportError, IntegrationNotFound, ValueError):
        return None

    manager = await async_get_manager(hass)
    preferences = await manager.async_get_energy_preferences()
    energy_sources = preferences.get("energy_sources") if preferences else None
    if not energy_sources:
        return None

    for source in energy_sources:
        if source.get("type") != "gas":
            continue
        cost = source.get("cost")
        if not cost or cost.get("type") != "fixed":
            continue
        value = cost.get("value")
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    return None
