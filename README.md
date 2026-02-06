# HA Heat Calculator (HACS Integration)

A Home Assistant custom integration that distributes total gas usage from one gas meter across multiple heater entities and exposes fully managed integration entities (no helper entities required).

## Features

- Select one gas meter entity (`sensor.*`).
- Select multiple heater entities (`climate.*`).
- Optional warm-water correction, managed directly by integration entities:
  - Switch entity to toggle whether warm water uses the same gas boiler.
  - Number entity to set a warm-water percentage subtracted before heater distribution.
- Per-heater output sensor with allocated gas consumption.
- Two allocation methods via integration select entity:
  - **Runtime only**
  - **Runtime with temperature weighting** (higher demand gets more weight)
- Built-in diagnostics panel with runtime state and last allocation details.

## How calculation works

1. The integration checks all configured climate entities every 5 minutes.
2. It estimates whether each heater is actively heating (`hvac_action == heating` or fallback logic).
3. It accumulates a heater-specific effort value.
4. On each increase of the gas meter value, it distributes the delta:
   - Warm-water share is removed first (if enabled).
   - Remaining gas is distributed proportionally by heater effort.

## Installation via HACS

1. Open HACS → Integrations → Custom repositories.
2. Add your repository URL and select **Integration**.
3. Install **HA Heat Calculator**.
4. Restart Home Assistant.
5. Add integration via **Settings → Devices & Services**.

## Notes

- Gas meter should be a monotonically increasing value.
- On meter resets/decreases, the baseline is re-synced automatically.
- Sensors represent allocated cumulative consumption since integration startup.
