# Merge Summary - Area-Based Window Control on v0.18.0

## Changes Made

### 1. const.py
- Added `CONF_WINDOW_SENSORS` - list of window sensors
- Added `CONF_WINDOW_OPEN_DELAY` - delay before turning off
- Added `DEFAULT_WINDOW_OPEN_DELAY = 15`
- Added `WindowControlMode.AREA_BASED` - new mode enum

### 2. window_control.py
Complete rewrite integrating area-based feature with v0.18.0 architecture:
- Dual mode support: Legacy (room/zone sensors) and Area-based
- Area-based logic with automatic zone detection
- Integration with v0.18.0 state management
- Uses `call_handler.call_immediate()` with optional `entity_ids`

### 3. service_call.py
Modified `WindowControlCallHandler` to support targeted entity control:
- Added `_target_entity_ids` instance variable
- Modified `call_immediate()` to accept optional `entity_ids` parameter
- Override `_get_call_entity_ids()` to return targeted entities

### 4. config_flow.py
Dynamic configuration UI based on selected mode:
- Shows different fields based on `window_mode` selection
- Area-based mode: shows `window_sensors` (multiple) and `window_open_delay`
- Legacy mode: shows `room_sensor`, `zone_sensor`, delays
- Automatic cleanup of unused config keys

### 5. strings.json
Added translations for new configuration options

## Testing

✅ Tested on 2026-02-01 19:58
✅ Environment: Home Assistant 2026.1.2
✅ Result: Perfect operation

---

**Version**: 0.18.0 + Area-Based Window Control  
**Status**: ✅ Production Ready
