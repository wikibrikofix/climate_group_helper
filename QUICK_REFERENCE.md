# Quick Reference - Area-Based Window Control

## 🎯 What This Modification Does

Adds granular area-based control: when a window opens, only thermostats **in the same area** are turned off, not the entire group.

## 📁 Modified Files (5)

### 1. const.py
```python
# Added 3 constants + 1 enum value
CONF_WINDOW_SENSORS = "window_sensors"
CONF_WINDOW_OPEN_DELAY = "window_open_delay"
DEFAULT_WINDOW_OPEN_DELAY = 15
WindowControlMode.AREA_BASED = "area_based"
```

### 2. window_control.py (CORE)
```python
# Area-based methods added:
_area_based_listener()          # Handles window events
_handle_window_opened()         # Turns off area thermostats
_handle_window_closed()         # Restores area thermostats
_get_entity_area()              # Detects area from registry
_get_thermostats_in_area()      # Finds thermostats by area

# v0.17.0 integration:
self.call_handler.call_immediate(entity_ids=[...])  # Instead of hass.services
self.target_state.hvac_mode                         # Instead of _group.hvac_mode
```

### 3. service_call.py
```python
# WindowControlCallHandler modified:
async def call_immediate(data=None, entity_ids=None):  # entity_ids NEW
    self._target_entity_ids = entity_ids
    # ...

def _get_call_entity_ids(attr):
    if self._target_entity_ids is not None:
        return self._target_entity_ids  # Use custom list
    return self._group.climate_entity_ids  # Default: all
```

### 4. config_flow.py
```python
# Dynamic UI based on window_mode:
if window_mode == WindowControlMode.AREA_BASED:
    # Show: window_sensors (multiple), window_open_delay
else:
    # Show: room_sensor, zone_sensor, room_delay, zone_delay
```

### 5. strings.json
```json
{
  "window_sensors": "Window Sensors (Area-based)",
  "window_open_delay": "Window Open Delay",
  "area_based": "Area-based – Automatic zone detection"
}
```

---

## 🔄 How to Reapply on New Version

### Step 1: Prepare Environment
```bash
cd /root/homeassistant/repos
# Download new version
git clone https://github.com/bjrnptrsn/climate_group_helper climate_group_helper_vX.X.X
```

### Step 2: Check Compatibility
```bash
# Check if these methods still exist:
grep "class WindowControlCallHandler" climate_group_helper_vX.X.X/.../service_call.py
grep "def call_immediate" climate_group_helper_vX.X.X/.../service_call.py
grep "@property" climate_group_helper_vX.X.X/.../window_control.py | grep -E "state_manager|call_handler"

# If they exist → Simple merge
# If not → Deep analysis needed
```

### Step 3: Apply Modifications

**const.py:**
```bash
# Add after other window constants:
CONF_WINDOW_SENSORS = "window_sensors"
CONF_WINDOW_OPEN_DELAY = "window_open_delay"
DEFAULT_WINDOW_OPEN_DELAY = 15

# In WindowControlMode enum:
AREA_BASED = "area_based"
```

**service_call.py:**
```bash
# In WindowControlCallHandler, modify call_immediate:
# BEFORE:
async def call_immediate(self, data: dict | None = None):

# AFTER:
async def call_immediate(self, data: dict | None = None, entity_ids: list[str] | None = None):
    self._target_entity_ids = entity_ids
    try:
        await self._execute_calls(data)
    finally:
        self._target_entity_ids = None

# Add override:
def _get_call_entity_ids(self, attr: str) -> list[str]:
    if self._target_entity_ids is not None:
        return self._target_entity_ids
    return self._group.climate_entity_ids
```

**window_control.py:**
```bash
# Copy ENTIRE implementation from:
/root/homeassistant/repos/climate_group_helper_fork/custom_components/climate_group_helper/window_control.py

# Verify it uses:
# - self._hass (not self._group.hass)
# - self.call_handler.call_immediate()
# - self.target_state
```

**config_flow.py:**
```bash
# In async_step_window_control, replace static schema with dynamic
# See: climate_group_helper_fork/.../config_flow.py lines 471-600
```

**strings.json:**
```bash
# Add translations as in:
# climate_group_helper_fork/.../strings.json
```

### Step 4: Test
```bash
# Copy files
cp -r climate_group_helper_vX.X.X/custom_components/climate_group_helper \
      /root/homeassistant/custom_components/

# Restart
ha core restart

# Verify
ha core logs | grep "WindowControl initialized"
# Should say: "Mode: area_based"

# Functional test
# 1. Open window → only area thermostat turns off
# 2. Close window → only area thermostat turns back on
```

---

## 🐛 Quick Troubleshooting

### Climate Group Not Loading
```bash
ha core logs | grep -i error | grep climate
python3 -m py_compile /root/homeassistant/custom_components/climate_group_helper/*.py
```

### WindowControl Not Initializing
```bash
# Check configuration:
# Settings > Helpers > Climate Group > Configure > Window Control
# - Mode must be "Area-based"
# - Window Sensors must have at least 1 sensor
```

### Window Opens But Nothing Happens
```bash
# 1. Check sensor changes state in Home Assistant
# 2. Check area configured:
ha core logs | grep "Cannot determine area"
# 3. Check thermostat in area:
ha core logs | grep "No active thermostats"
```

### Thermostat Doesn't Turn Back On
```bash
# Check other windows open:
ha core logs | grep "Other windows still open"
# Check target mode:
ha core logs | grep "Target mode is OFF"
```

### All Thermostats Turn Off (Not Just Area)
```bash
# Check mode
ha core logs | grep "WindowControl initialized"
# Must say "Mode: area_based"

# If says "Mode: on", reconfigure:
# Settings > Devices & Services > Helpers > Climate Group Helper > Configure
# Window Control > Window Mode > Select "Area-based"
```

---

## 📊 Log Patterns

### ✅ Correct Operation
```
DEBUG [...] WindowControl initialized. Mode: area_based
DEBUG [...] Window binary_sensor.window_X opened, scheduling turn off in 15.0s
INFO  [...] Window binary_sensor.window_X opened in area 'Y', turning off: ['climate.thermo_Y']
DEBUG [...] Window binary_sensor.window_X closed, scheduling restore check in 30.0s
INFO  [...] Window binary_sensor.window_X closed, restoring area 'Y': ['climate.thermo_Y']
```

### ❌ Problems
```
ERROR [...] Cannot determine area for window X          → Assign area
DEBUG [...] No active thermostats in area 'Y'          → Normal if all OFF
DEBUG [...] Other windows still open in area 'Y'       → Normal, close others
DEBUG [...] Target mode is OFF, not restoring          → Normal if group OFF
```

---

## 🔑 Key Points to Remember

1. **Use call_handler, not hass.services**
   ```python
   # ❌ WRONG (v0.16.1)
   await self._group.hass.services.async_call(...)
   
   # ✅ CORRECT (v0.17.0)
   await self.call_handler.call_immediate(entity_ids=[...])
   ```

2. **Use target_state, not _group.hvac_mode**
   ```python
   # ❌ WRONG
   if self._group.hvac_mode == HVACMode.OFF:
   
   # ✅ CORRECT
   if self.target_state.hvac_mode == HVACMode.OFF:
   ```

3. **Use self._hass, not self._group.hass**
   ```python
   # ❌ WRONG
   state = self._group.hass.states.get(entity_id)
   
   # ✅ CORRECT
   state = self._hass.states.get(entity_id)
   ```

4. **entity_ids is optional in call_immediate**
   ```python
   # All members
   await self.call_handler.call_immediate({"hvac_mode": HVACMode.OFF})
   
   # Only some members
   await self.call_handler.call_immediate(
       {"hvac_mode": HVACMode.OFF}, 
       entity_ids=["climate.thermo1", "climate.thermo2"]
   )
   ```

5. **Check other windows before restoring**
   ```python
   # Check if other windows in area are open
   for other_window in self._window_sensors:
       if self._get_entity_area(other_window) == window_area:
           if is_open(other_window):
               return  # Don't restore yet
   ```

---

## 📚 Complete Documentation

See: [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)

---

## 📝 Merge Checklist

- [ ] const.py: 3 constants + 1 enum
- [ ] service_call.py: entity_ids parameter + override
- [ ] window_control.py: 5 area-based methods + v0.17.0 integration
- [ ] config_flow.py: Dynamic UI
- [ ] strings.json: 3 translations
- [ ] Test: open/close window
- [ ] Log: "Mode: area_based"
- [ ] Functional: only area thermostat controlled

---

**Last Modified**: 2026-01-24  
**Version**: 0.17.0 + Area-Based Window Control  
**Status**: ✅ Tested and Working

---

## 🌍 Languages

- **English**: This file
- **Italian**: [docs_ita/QUICK_REFERENCE.md](docs_ita/QUICK_REFERENCE.md)
