# Merge Summary: Area-Based Window Control on v0.17.0

## Changes Made

### 1. `const.py`
Added constants for area-based window control:
- `CONF_WINDOW_SENSORS` - list of window sensors
- `CONF_WINDOW_OPEN_DELAY` - delay before turning off
- `DEFAULT_WINDOW_OPEN_DELAY = 15`
- `WindowControlMode.AREA_BASED` - new mode enum

### 2. `window_control.py`
Complete rewrite integrating area-based feature with v0.17.0 architecture:
- **Dual mode support**: Legacy (room/zone sensors) and Area-based
- **Area-based logic**:
  - `_area_based_listener()` - handles window state changes
  - `_handle_window_opened()` - turns off thermostats in same area
  - `_handle_window_closed()` - restores thermostats when all windows closed
  - `_get_thermostats_in_area()` - finds members by area
  - `_get_entity_area()` - resolves entity/device area
- **Architecture integration**:
  - Uses `self.call_handler.call_immediate()` with optional `entity_ids`
  - Respects `self.target_state` for restoration
  - Compatible with new state management system
- **Backward compatibility**: Legacy mode unchanged

### 3. `service_call.py`
Modified `WindowControlCallHandler` to support targeted entity control:
- Added `_target_entity_ids` instance variable
- Modified `call_immediate()` to accept optional `entity_ids` parameter
- Override `_get_call_entity_ids()` to return targeted entities when set

### 4. `config_flow.py`
Dynamic configuration UI based on selected mode:
- Added imports for `CONF_WINDOW_SENSORS`, `CONF_WINDOW_OPEN_DELAY`, `DEFAULT_WINDOW_OPEN_DELAY`
- Modified `async_step_window_control()`:
  - Shows different fields based on `window_mode` selection
  - Area-based mode: shows `window_sensors` (multiple selector) and `window_open_delay`
  - Legacy mode: shows `room_sensor`, `zone_sensor`, `room_open_delay`, `zone_open_delay`
  - Automatic cleanup of unused config keys when switching modes

### 5. `strings.json`
Added translations for new configuration options:
- `window_sensors` - description for area-based sensor selection
- `window_open_delay` - description for open delay
- `area_based` option in `window_mode` selector

### 6. Documentation
Created `AREA_BASED_WINDOW_CONTROL.md` with:
- Feature overview and key features
- How it works (step-by-step)
- Configuration requirements and setup
- Example scenario
- Architecture integration details
- Debugging tips
- Migration guide from legacy mode

## Testing Checklist

### Area-Based Mode
- [ ] Configure area-based mode with multiple window sensors
- [ ] Verify window open triggers only thermostats in same area
- [ ] Verify window close restores only affected thermostats
- [ ] Test multiple windows in same area (restoration only when all closed)
- [ ] Test multiple windows in different areas (independent control)
- [ ] Verify entities without area assignment are ignored
- [ ] Test with group target mode = OFF (should not restore)

### Legacy Mode
- [ ] Verify legacy room/zone sensor mode still works
- [ ] Test room sensor with short delay
- [ ] Test zone sensor with long delay
- [ ] Test close delay restoration

### Configuration UI
- [ ] Switch between OFF/ON/AREA_BASED modes
- [ ] Verify correct fields shown for each mode
- [ ] Verify config cleanup when switching modes
- [ ] Test with empty sensor selections

### Integration
- [ ] Verify compatibility with Schedule feature
- [ ] Verify compatibility with Sync Mode
- [ ] Check debug logs for proper context_id="window_control"
- [ ] Verify no conflicts with user commands

## Migration Notes

### From v0.16.1 Fork to v0.17.0 with Area-Based

**Breaking Changes in v0.17.0:**
- New state management architecture (TargetState dataclass)
- New service call handler system
- Window control redesigned to use call handlers

**Your Custom Feature:**
- Fully integrated with new architecture
- No breaking changes for end users
- Legacy mode preserved for backward compatibility

**Recommended Steps:**
1. Backup current configuration
2. Test in development environment first
3. Verify all areas are properly configured in Home Assistant
4. Enable debug logging during initial testing
5. Monitor logs for any area detection issues

## Known Limitations

1. Entities without area assignment are ignored in area-based mode
2. Area detection relies on entity_registry and device_registry
3. If device has no area, entity area is used (fallback)
4. No support for dynamic area changes (requires restart)

## Future Enhancements

Possible improvements for future versions:
- Support for area groups/hierarchies
- Configurable fallback behavior for entities without areas
- Per-window delay configuration
- Window open duration tracking
- Integration with presence detection
