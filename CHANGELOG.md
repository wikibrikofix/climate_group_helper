# Changelog

All notable changes to this fork will be documented in this file.

## [0.18.0-area-based] - 2026-02-01

### ✅ Tested and Working
- Area-based window control fully functional
- Automatic area detection working correctly
- Independent timer management per window
- Smart restore when all windows in area are closed

### 🔄 Merged from Upstream v0.18.0

#### 🚀 Scheduler & Timers
- **Resync Interval**: Periodically enforce the scheduled state to fix drifting devices
- **Override Duration**: Manual changes are temporary. The group automatically returns to the schedule after a configured duration (e.g. 60 min)
- **Sticky Override**: Manual changes persist until the override expires, ignoring background schedule updates

#### 🌡️ Advanced Calibration
- **New Modes**: Added `Offset` and `Scaled` (x100) support for better TRV compatibility
- **Heartbeat**: Periodically re-syncs calibration values to prevent timeouts (e.g. Aqara/Sonoff)

### 🎯 Area-Based Window Control (Custom Feature)

#### Added
- `AREA_BASED` mode to `WindowControlMode` enum
- `CONF_WINDOW_SENSORS` and `CONF_WINDOW_OPEN_DELAY` configuration options
- Area detection via entity/device registry
- Independent timer management for multiple windows
- Smart restore logic (checks all windows in area before restoring)

#### Modified Files
- `const.py`: Added area-based constants and enum value
- `window_control.py`: Added 160+ lines for area-based logic
  - `_area_based_listener()`: Handles window sensor events
  - `_handle_window_opened()`: Turns off thermostats in area
  - `_handle_window_closed()`: Restores thermostats when safe
  - `_get_thermostats_in_area()`: Finds thermostats by area
  - `_get_entity_area()`: Determines entity area from registry
- `service_call.py`: Extended `WindowControlCallHandler` with `entity_ids` parameter
- `config_flow.py`: Dynamic UI based on selected window mode
- `strings.json`: Added translations for area_based mode
- `translations/it.json`: Italian translations
- `translations/en.json`: English translations

### 🔧 Technical Details

#### Architecture
- Modular integration: Area-based code isolated in dedicated sections
- Backward compatible: Legacy mode (ON) fully preserved
- No invasive changes to core logic

#### Future Merge Strategy
- All area-based code is clearly marked and isolated
- Easy to re-apply on future upstream versions
- Configuration cleanup logic prevents conflicts

### 📝 Documentation
- Updated README.md with v0.18.0 information
- Created MERGE_v0.18.0_SUMMARY.md with detailed merge notes
- Maintained all existing documentation

---

## [0.17.0-area-based] - 2026-02-01

### Added
- Initial implementation of area-based window control
- Merged from upstream v0.17.0
- Complete bilingual documentation (EN/IT)

### Features
- Area-based window control mode
- Automatic area detection
- Independent window timers
- Smart thermostat restore logic

---

## Upstream Changelog

For changes in the original Climate Group Helper, see:
https://github.com/bjrnptrsn/climate_group_helper/blob/main/CHANGELOG.md
