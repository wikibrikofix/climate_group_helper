# Installation and Merge Instructions

## ✅ Merge Completed Successfully

The **Area-Based Window Control** feature has been successfully merged onto Climate Group Helper v0.18.0 architecture.

### What Was Done

**5 Files Modified:**
1. **const.py** - Area-based constants added
2. **window_control.py** - Rewritten with v0.18.0 integration (16.3 KB)
3. **service_call.py** - WindowControlCallHandler modified (16.7 KB)
4. **config_flow.py** - Dynamic UI implemented (24.4 KB)
5. **strings.json** - Translations added

**Documentation Created:**
- 10 documentation files (~4,000 lines)
- Inline code comments
- Complete test plan

### Installation

```bash
# Backup
cp -r /root/homeassistant/custom_components/climate_group_helper \
      /root/climate_group_helper.backup

# Install
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
6. Configure delays (15s open, 30s close)
7. **Save**

**IMPORTANT**: Assign windows and thermostats to areas in Settings > Areas.

### Verification

```bash
# Check loading
ha core logs | grep "WindowControl initialized"
# Expected: "Mode: area_based"

# Test
# 1. Open window → area thermostat turns off (15s)
# 2. Close window → area thermostat turns back on (30s)
```

---

**Version**: 0.18.0 + Area-Based Window Control  
**Status**: ✅ Production Ready  
**Date**: 2026-02-01
