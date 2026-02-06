"""Config flow for HA Heat Calculator."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.selector import SelectSelectorConfig

from .const import (
    CALCULATION_METHODS,
    CONF_CALCULATION_METHOD,
    CONF_GAS_METER_ENTITY,
    CONF_HEATERS,
    CONF_INCLUDE_WARM_WATER,
    CONF_WARM_WATER_PERCENT,
    DEFAULT_CALCULATION_METHOD,
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

        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(user_input),
            errors=errors,
        )

    @staticmethod
    def _build_schema(defaults: dict | None = None) -> vol.Schema:
        """Build a reusable schema for create/options flow."""
        defaults = defaults or {}

        return vol.Schema(
            {
                vol.Required(
                    CONF_GAS_METER_ENTITY,
                    default=defaults.get(CONF_GAS_METER_ENTITY),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"], multiple=False)
                ),
                vol.Required(
                    CONF_HEATERS,
                    default=defaults.get(CONF_HEATERS, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["climate"], multiple=True)
                ),
                vol.Required(
                    CONF_INCLUDE_WARM_WATER,
                    default=defaults.get(
                        CONF_INCLUDE_WARM_WATER, DEFAULT_INCLUDE_WARM_WATER
                    ),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_WARM_WATER_PERCENT,
                    default=defaults.get(
                        CONF_WARM_WATER_PERCENT, DEFAULT_WARM_WATER_PERCENT
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=1)
                ),
                vol.Required(
                    CONF_CALCULATION_METHOD,
                    default=defaults.get(
                        CONF_CALCULATION_METHOD, DEFAULT_CALCULATION_METHOD
                    ),
                ): selector.SelectSelector(
                    SelectSelectorConfig(
                        options=list(CALCULATION_METHODS.keys()),
                        mode="dropdown",
                        translation_key=CONF_CALCULATION_METHOD,
                    )
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
        return self.async_show_form(
            step_id="init",
            data_schema=HeatCalculatorConfigFlow._build_schema(defaults),
            errors=errors,
        )

