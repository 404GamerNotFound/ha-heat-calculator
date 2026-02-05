"""Constants for the HA Heat Calculator integration."""

from __future__ import annotations

DOMAIN = "ha_heat_calculator"

CONF_GAS_METER_ENTITY = "gas_meter_entity"
CONF_HEATERS = "heaters"
CONF_INCLUDE_WARM_WATER = "include_warm_water"
CONF_WARM_WATER_PERCENT = "warm_water_percent"
CONF_CALCULATION_METHOD = "calculation_method"

DEFAULT_INCLUDE_WARM_WATER = False
DEFAULT_WARM_WATER_PERCENT = 20.0
DEFAULT_CALCULATION_METHOD = "runtime_temp_weighted"

CALCULATION_METHODS = {
    "runtime_only": "Runtime only",
    "runtime_temp_weighted": "Runtime with temperature delta weighting",
}

UPDATE_INTERVAL_SECONDS = 300
