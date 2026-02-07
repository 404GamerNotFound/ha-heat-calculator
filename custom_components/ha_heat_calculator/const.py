"""Constants for the HA Heat Calculator integration."""

from __future__ import annotations

DOMAIN = "ha_heat_calculator"
DOCUMENTATION_URL = "https://github.com/404GamerNotFound/ha-heat-calculator"

CONF_GAS_METER_ENTITY = "gas_meter_entity"
CONF_HEATERS = "heaters"
CONF_INCLUDE_WARM_WATER = "include_warm_water"
CONF_WARM_WATER_PERCENT = "warm_water_percent"
CONF_CALCULATION_METHOD = "calculation_method"
CONF_GAS_PRICE = "gas_price"
CONF_HEATER_AREAS = "heater_areas"
CONF_HEATER_OUTPUTS = "heater_outputs"

DEFAULT_INCLUDE_WARM_WATER = False
DEFAULT_WARM_WATER_PERCENT = 20.0
DEFAULT_CALCULATION_METHOD = "runtime_temp_weighted"
DEFAULT_GAS_PRICE = 0.0

CALCULATION_METHODS = {
    "runtime_only": "Runtime only",
    "runtime_temp_weighted": "Runtime with temperature delta weighting",
}

UPDATE_INTERVAL_SECONDS = 300
