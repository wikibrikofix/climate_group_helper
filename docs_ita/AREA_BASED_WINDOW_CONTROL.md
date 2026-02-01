# Area-Based Window Control

## Overview

Area-based window control is an advanced feature that automatically turns off thermostats in specific areas when windows are opened in those areas, and restores them when windows are closed.

## Key Features

- **Granular Control**: Only thermostats in the same area as an opened window are affected
- **Multi-Window Support**: Handles multiple windows in different areas simultaneously
- **Area Detection**: Uses Home Assistant's area registry to automatically associate windows with thermostats
- **Backward Compatible**: Legacy room/zone sensor mode continues to work

## How It Works

1. When a window opens → identifies its area via entity/device registry
2. Finds all group members (thermostats) in the same area
3. Turns off only those members after configured delay
4. When window closes → restores only members that were turned off by that window
5. If multiple windows are open in the same area, restoration happens only when all are closed

## Configuration

### Requirements

- **Areas configured**: Windows and thermostats must be assigned to areas in Home Assistant
- **Same area name**: Window and thermostat must be in the same area to be associated
- If an entity has no assigned area, the system tries to use the device's area

### Setup Steps

1. Go to **Settings** > **Devices & Services** > **Helpers**
2. Find your Climate Group Helper
3. Click **Configure** > **Window Control**
4. Select **Window Mode**: `area_based`
5. Select all windows to monitor in **Window Sensors**
6. Configure **Window Open Delay** (default: 15s)
7. Configure **Close Delay** (default: 30s)

## Example

**Setup:**
- Area "Living Room": `binary_sensor.living_room_window`, `climate.living_room_thermostat`
- Area "Bedroom": `binary_sensor.bedroom_window`, `climate.bedroom_thermostat`
- Group: includes both thermostats

**Behavior:**
1. Open `living_room_window` → only `living_room_thermostat` turns off
2. Open `bedroom_window` → only `bedroom_thermostat` turns off
3. Close `living_room_window` → only `living_room_thermostat` turns back on
4. Close `bedroom_window` → only `bedroom_thermostat` turns back on

## Architecture Integration

The area-based feature is fully integrated with the v0.18.0 architecture:

- Uses `WindowControlCallHandler` with optional `entity_ids` parameter
- Respects the central `TargetState` for restoration
- Works with the new source-aware state management system
- Compatible with Schedule and Sync Mode features

## Debugging

Enable debug logging to see area detection and control decisions:

```yaml
logger:
  default: info
  logs:
    custom_components.climate_group_helper: debug
```

Look for log messages like:
- `Window X opened in area 'Y', turning off: [entities]`
- `Window X closed, restoring area 'Y': [entities]`
- `Cannot determine area for window X` (indicates missing area assignment)

## Migration from Legacy Mode

If you're currently using the legacy room/zone sensor mode:

1. The legacy mode continues to work - no action required
2. To migrate to area-based:
   - Ensure all windows and thermostats are assigned to areas
   - Change **Window Mode** to `area_based`
   - Select all window sensors
   - Legacy configuration will be automatically removed

## Notes

- If an entity has no area assignment, it's ignored by area-based control
- If `window_mode = area_based` but no sensors configured, control is disabled
- The group's target state is never modified - only member states are controlled
- Restoration only happens if the group's target mode is not OFF
