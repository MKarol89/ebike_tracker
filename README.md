# E-bike Tracker

Custom Home Assistant integration for tracking an e-bike mileage, charging energy and riding cost locally.

## Features

- HACS-ready custom integration under `custom_components/ebike_tracker`.
- UI-only setup through Home Assistant config flow. No `configuration.yaml` is required.
- Each configured bike is created as a separate Home Assistant device.
- Editable odometer number with protection against accidental backward changes.
- Administrator-only correction action for confirmed backward odometer fixes.
- Persistent odometer and energy history using Home Assistant storage.
- Reset-aware cumulative energy tracking for smart plugs that reset or are replaced.
- Polish and English translations.

## Setup

1. Install the repository through HACS as a custom integration.
2. Restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration**.
4. Search for **E-bike Tracker**.
5. Provide:
   - bike name,
   - current mileage in km,
   - cumulative energy entity in kWh,
   - optional charging power entity in W,
   - energy price in PLN/kWh,
   - optional battery capacity in Wh.

The charging state uses a configurable power threshold. The default threshold is **5 W** and can be changed in integration options.

## Entities

The integration creates:

- odometer number,
- total mileage,
- distance since monitoring started,
- daily, weekly and monthly mileage increase,
- 7-day and 30-day average daily distance,
- total, weekly and monthly energy,
- average energy consumption in kWh/100 km,
- energy consumption in Wh/km,
- cost per 100 km,
- total energy cost,
- current charging power,
- charging binary sensor,
- last mileage update timestamp.

## Odometer correction

Normal odometer edits cannot lower the current mileage. To correct mileage backwards, call the `ebike_tracker.correct_odometer` action with:

- `config_entry_id`,
- corrected `mileage`,
- `confirm: true`.

The action requires a Home Assistant administrator user context.

## Energy meter resets

The configured energy entity should be a cumulative kWh sensor. When the raw value drops, E-bike Tracker treats it as a meter reset and keeps previously tracked energy. The new raw value is added as energy consumed after the reset, so previously tracked energy does not disappear.

## Development

Run unit tests:

```bash
pytest
```

The repository includes GitHub workflows for HACS validation and Hassfest.

## License

MIT
