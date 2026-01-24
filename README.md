# Climate Group Helper - Area-Based Window Control

## 📋 Overview

This repository contains a modified version of the **Climate Group Helper** module for Home Assistant with the addition of the **Area-Based Window Control** feature.

### What It Does

Enables granular thermostat control based on areas: when a window opens, only thermostats **in the same area** are turned off, not the entire group.

### Version

- **Base**: Climate Group Helper v0.17.0
- **Modification**: Area-Based Window Control
- **Date**: 2026-01-24
- **Status**: ✅ Tested and Working

---

## 📚 Documentation

### Getting Started

1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** ⭐ **START HERE**
   - Quick guide to understand modifications
   - Checklist to reapply on new versions
   - Quick troubleshooting
   - Log patterns to verify

### Technical Documentation

2. **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)**
   - Complete v0.17.0 architecture
   - Detailed explanation of each modification
   - Step-by-step re-merge guide
   - Complete test suite
   - In-depth troubleshooting

3. **[MODIFICATIONS_DIFF.md](MODIFICATIONS_DIFF.md)**
   - Exact diffs of all modifications
   - Line-by-line comparison
   - Complete code of new methods
   - Summary of changes per file

### User Documentation

4. **[AREA_BASED_WINDOW_CONTROL.md](custom_components/climate_group_helper/AREA_BASED_WINDOW_CONTROL.md)**
   - User guide for configuration
   - Usage examples
   - Requirements and setup
   - Debugging

### Merge Documentation

5. **[README_MERGE.md](README_MERGE.md)**
   - Installation instructions
   - Operation verification
   - Next steps

6. **[MERGE_SUMMARY.md](MERGE_SUMMARY.md)**
   - Technical merge summary
   - Details of changes per file
   - Testing checklist

7. **[COMPARISON.md](COMPARISON.md)**
   - Comparison fork v0.16.1 vs v0.17.0
   - Architectural differences
   - Advantages of new implementation

8. **[TEST_PLAN.md](TEST_PLAN.md)**
   - Complete test plan (12 test cases)
   - Performance tests
   - Rollback procedures
   - Success criteria

---

## 🚀 Quick Start

### Installation

```bash
# Backup
cp -r /root/homeassistant/custom_components/climate_group_helper \
      /root/climate_group_helper.backup

# Installation
cp -r custom_components/climate_group_helper \
      /root/homeassistant/custom_components/

# Restart
ha core restart
```

### Configuration

1. Go to **Settings > Devices & Services > Helpers**
2. Find your **Climate Group Helper**
3. Click **Configure > Window Control**
4. Select **Window Mode**: `Area-based`
5. Select **Window Sensors**: all windows to monitor
6. Configure **Window Open Delay**: 15s (default)
7. Configure **Close Delay**: 30s (default)
8. **Save**

**IMPORTANT**: Make sure windows and thermostats are assigned to areas in Home Assistant (Settings > Areas).

### Verification

```bash
# Verify loading
ha core logs | grep "WindowControl initialized"
# Expected output: "Mode: area_based"

# Functional test
# 1. Open window → only area thermostat turns off
# 2. Close window → only area thermostat turns back on
```

---

## 📁 Repository Structure

```
climate_group_helper/
├── README.md                           ← This file
├── INDEX.md                            ← Quick navigation
├── QUICK_REFERENCE.md                  ← ⭐ Quick guide
├── TECHNICAL_DOCUMENTATION.md          ← Complete documentation
├── MODIFICATIONS_DIFF.md               ← Code diffs
├── COMPARISON.md                       ← Version comparison
├── README_MERGE.md                     ← Installation instructions
├── MERGE_SUMMARY.md                    ← Merge summary
├── TEST_PLAN.md                        ← Test plan
├── docs_ita/                           ← Italian documentation
└── custom_components/
    └── climate_group_helper/
        ├── __init__.py                 (v0.17.0 base)
        ├── climate.py                  (v0.17.0 base)
        ├── const.py                    ⚙️ MODIFIED
        ├── window_control.py           ⚙️ MODIFIED
        ├── service_call.py             ⚙️ MODIFIED
        ├── config_flow.py              ⚙️ MODIFIED
        ├── strings.json                ⚙️ MODIFIED
        ├── state.py                    (v0.17.0 base)
        ├── sync_mode.py                (v0.17.0 base)
        ├── schedule.py                 (v0.17.0 base)
        ├── sensor.py                   (v0.17.0 base)
        ├── manifest.json               (v0.17.0)
        └── AREA_BASED_WINDOW_CONTROL.md ← User guide
```

---

## 🔧 Modified Files

### Core Modifications

| File | Changes | Description |
|------|---------|-------------|
| `const.py` | +4 lines | Area-based constants |
| `window_control.py` | +200 lines | Complete area-based logic |
| `service_call.py` | +18 lines | entity_ids support |
| `config_flow.py` | +70 lines | Dynamic UI |
| `strings.json` | +6 lines | Translations |

**Total**: ~300 lines of code

### Unmodified Files

All other files are identical to v0.17.0 base:
- `__init__.py`, `climate.py`, `state.py`, `sync_mode.py`, `schedule.py`, `sensor.py`

---

## 🎯 Features

### Area-Based Mode

- ✅ Granular control per area
- ✅ Automatic area detection via registry
- ✅ Multiple windows per area management
- ✅ Multiple windows in different areas management
- ✅ Configurable delays (open/close)
- ✅ Smart restoration

### Legacy Mode

- ✅ Room/zone mode preserved
- ✅ Complete backward compatibility
- ✅ No breaking changes

### v0.17.0 Integration

- ✅ Uses new TargetState system
- ✅ Compatible with CallHandler architecture
- ✅ Source-aware state management
- ✅ Automatic context tracking
- ✅ Retry logic and debouncing

---

## 🧪 Testing

### Test Completed

**Date**: 2026-01-24 19:58  
**Environment**: Home Assistant 2026.1.2

**Test Timeline:**
```
19:57:02 - Studio window opened
19:57:17 - Studio thermostat turned off (after 15s)
19:58:25 - Studio window closed
19:58:56 - Studio thermostat restored (after 30s)
```

**Result**: ✅ Perfect operation

### Test Suite

See [TEST_PLAN.md](TEST_PLAN.md) for:
- 12 complete test cases
- Performance tests
- Rollback procedures
- Success criteria

---

## 🐛 Troubleshooting

### Common Problems

| Problem | Solution |
|---------|----------|
| Climate group not loading | Check Python syntax, check error logs |
| WindowControl not initializing | Check mode = "area_based" and sensors configured |
| Window opens but nothing happens | Check sensor works and area configured |
| Thermostat doesn't turn back on | Check other windows closed and target mode |
| All thermostats turn off | Check mode = "area_based" (not "on") |

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-quick-troubleshooting) for details.

---

## 🔄 Re-Merge on New Version

### When Needed

- New upstream version (e.g. v0.18.0)
- Critical bugfixes to integrate
- New features to maintain

### Process

1. **Analysis**: Compare key files with new version
2. **Verification**: Check architectural compatibility
3. **Apply**: Reapply modifications (see QUICK_REFERENCE.md)
4. **Test**: Verify complete operation

See [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#guida-al-re-merge) for complete guide.

---

## 📊 Log Patterns

### Correct Operation

```
DEBUG [...] WindowControl initialized. Mode: area_based
DEBUG [...] Window binary_sensor.window_X opened, scheduling turn off in 15.0s
INFO  [...] Window ... opened in area 'Y', turning off: ['climate.thermo_Y']
DEBUG [...] Window ... closed, scheduling restore check in 30.0s
INFO  [...] Window ... closed, restoring area 'Y': ['climate.thermo_Y']
```

### Debug

```bash
# Enable debug logging in configuration.yaml
logger:
  default: info
  logs:
    custom_components.climate_group_helper: debug

# Monitor logs
ha core logs --follow | grep climate_group_helper
```

---

## 🔑 Key Points

### Architectural Differences v0.16.1 → v0.17.0

| Aspect | v0.16.1 | v0.17.0 |
|--------|---------|---------|
| Service calls | `hass.services.async_call()` | `call_handler.call_immediate()` |
| State | `_group.hvac_mode` | `target_state.hvac_mode` |
| Hass access | `_group.hass` | `_hass` |
| Targeting | Manual loop | `entity_ids` parameter |

### Key Code

```python
# ✅ CORRECT (v0.17.0)
await self.call_handler.call_immediate(
    {"hvac_mode": HVACMode.OFF}, 
    entity_ids=["climate.thermo1"]
)

if self.target_state.hvac_mode == HVACMode.OFF:
    return

state = self._hass.states.get(entity_id)
```

---

## 📞 Support

### Documentation

- **Quick Start**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Technical**: [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)
- **Diff**: [MODIFICATIONS_DIFF.md](MODIFICATIONS_DIFF.md)

### Repository

- **Upstream**: https://github.com/bjrnptrsn/climate_group_helper
- **Base Version**: 0.17.0
- **Custom Feature**: Area-Based Window Control

---

## 📝 Changelog

### 2026-01-24 - v0.17.0 + Area-Based

- ✅ Merge completed on v0.17.0 architecture
- ✅ Area-based window control integrated
- ✅ Backward compatibility preserved
- ✅ Tests completed successfully
- ✅ Complete documentation created
- ✅ Code commented inline

---

## 📄 License

Same as upstream version (Climate Group Helper).

---

## 🙏 Credits

- **Climate Group Helper**: bjrnptrsn
- **Area-Based Feature**: Custom modification
- **Merge v0.17.0**: 2026-01-24

---

## 🌍 Languages

- **English**: This documentation (root directory)
- **Italian**: [docs_ita/](docs_ita/) directory

---

**Last Modified**: 2026-01-24  
**Version**: 0.17.0 + Area-Based Window Control  
**Status**: ✅ Production
