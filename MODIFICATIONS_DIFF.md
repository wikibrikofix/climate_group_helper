# Diff delle Modifiche - Area-Based Window Control

Questo file contiene i diff esatti delle modifiche apportate per implementare
la feature area-based window control sulla versione 0.17.0.

## const.py

```diff
--- a/const.py (v0.17.0 base)
+++ b/const.py (v0.17.0 + area-based)
@@ -68,9 +68,12 @@
 CONF_ROOM_OPEN_DELAY = "room_open_delay"
 CONF_ZONE_OPEN_DELAY = "zone_open_delay"
 CONF_CLOSE_DELAY = "close_delay"
+CONF_WINDOW_SENSORS = "window_sensors"
+CONF_WINDOW_OPEN_DELAY = "window_open_delay"
 DEFAULT_ROOM_OPEN_DELAY = 15
 DEFAULT_ZONE_OPEN_DELAY = 300
 DEFAULT_CLOSE_DELAY = 30
+DEFAULT_WINDOW_OPEN_DELAY = 15
 
 # Schedule options
 CONF_SCHEDULE_ENTITY = "schedule_entity"
@@ -111,6 +114,7 @@
 
     OFF = "off"
     ON = "on"
+    AREA_BASED = "area_based"
```

## service_call.py - WindowControlCallHandler

```diff
--- a/service_call.py (v0.17.0 base)
+++ b/service_call.py (v0.17.0 + area-based)
@@ -395,10 +395,28 @@
 class WindowControlCallHandler(BaseServiceCallHandler):
-    """Call handler for Window Control operations."""
+    """Call handler for Window Control operations.
+    
+    Supports optional entity_ids parameter for area-based control.
+    """
 
     CONTEXT_ID = "window_control"
 
     def __init__(self, group: ClimateGroup):
         """Initialize the window control call handler."""
         super().__init__(group)
+        self._target_entity_ids: list[str] | None = None
+
+    async def call_immediate(self, data: dict[str, Any] | None = None, entity_ids: list[str] | None = None) -> None:
+        """Execute a service call immediately, optionally targeting specific entities.
+        
+        Args:
+            data: Optional data dict with attributes to set
+            entity_ids: Optional list of entity IDs to target (for area-based control)
+        """
+        self._target_entity_ids = entity_ids
+        try:
+            await self._execute_calls(data)
+        finally:
+            self._target_entity_ids = None
+
+    def _get_call_entity_ids(self, attr: str) -> list[str]:
+        """Return target entity IDs if set, otherwise all members."""
+        if self._target_entity_ids is not None:
+            return self._target_entity_ids
+        return self._group.climate_entity_ids
```

## window_control.py - Struttura Principale

```diff
--- a/window_control.py (v0.17.0 base)
+++ b/window_control.py (v0.17.0 + area-based)
@@ -1,4 +1,28 @@
-"""Window control handler for automatic heating shutdown when windows open."""
+"""Window control handler for automatic heating shutdown when windows open.
+
+CUSTOM MODIFICATION: Area-Based Window Control
+===============================================
+This file has been modified to support area-based window control in addition to
+the legacy room/zone sensor mode.
+
+Key Changes from v0.17.0 base:
+1. Added area-based configuration (CONF_WINDOW_SENSORS, CONF_WINDOW_OPEN_DELAY)
+2. Implemented _area_based_listener for per-window event handling
+3. Added _handle_window_opened/_handle_window_closed for area-specific control
+4. Added _get_entity_area for automatic area detection via registry
+5. Added _get_thermostats_in_area for finding members by area
+6. Integrated with v0.17.0 architecture (call_handler, target_state)
+
+Architecture Integration:
+- Uses self.call_handler.call_immediate(entity_ids=...) for targeted control
+- Respects self.target_state for restoration
+- Compatible with new state management system
+
+Backward Compatibility:
+- Legacy mode (room/zone sensors) fully preserved
+- Automatic config cleanup when switching modes
+
+Date: 2026-01-24
+Version: 0.17.0 + Area-Based Window Control
+"""
 from __future__ import annotations
 
 import logging
@@ -10,6 +34,7 @@
 from homeassistant.const import STATE_ON, STATE_OPEN
 from homeassistant.core import Event, EventStateChangedData, callback
 from homeassistant.helpers.event import async_call_later, async_track_state_change_event
+from homeassistant.helpers import entity_registry as er, device_registry as dr
 
 from .const import (
     CONF_CLOSE_DELAY,
@@ -17,6 +42,8 @@
     CONF_ROOM_SENSOR,
     CONF_WINDOW_MODE,
+    CONF_WINDOW_SENSORS,
+    CONF_WINDOW_OPEN_DELAY,
     CONF_ZONE_OPEN_DELAY,
     CONF_ZONE_SENSOR,
     DEFAULT_CLOSE_DELAY,
     DEFAULT_ROOM_OPEN_DELAY,
+    DEFAULT_WINDOW_OPEN_DELAY,
     DEFAULT_ZONE_OPEN_DELAY,
     WindowControlMode,
 )
@@ -48,6 +75,12 @@
         self._room_delay = group.config.get(CONF_ROOM_OPEN_DELAY, DEFAULT_ROOM_OPEN_DELAY)
         self._zone_delay = group.config.get(CONF_ZONE_OPEN_DELAY, DEFAULT_ZONE_OPEN_DELAY)
+
+        # Area-based configuration
+        self._window_sensors = group.config.get(CONF_WINDOW_SENSORS, [])
+        self._window_open_delay = group.config.get(CONF_WINDOW_OPEN_DELAY, DEFAULT_WINDOW_OPEN_DELAY)
         self._close_delay = group.config.get(CONF_CLOSE_DELAY, DEFAULT_CLOSE_DELAY)
+
+        # Area-based state tracking
+        self._timers: dict[str, Any] = {}
 
         # Legacy state tracking
         self._room_open = False
@@ -95,6 +128,15 @@
             _LOGGER.debug("[%s] Window control is disabled", self._group.entity_id)
             return
 
+        # Area-based mode
+        if self._window_control_mode == WindowControlMode.AREA_BASED:
+            if not self._window_sensors:
+                _LOGGER.warning("[%s] Area-based window control enabled but no sensors configured", self._group.entity_id)
+                return
+            
+            self._unsub_listener = async_track_state_change_event(
+                self._hass, self._window_sensors, self._area_based_listener
+            )
+            _LOGGER.debug("[%s] Area-based window control subscribed to: %s", self._group.entity_id, self._window_sensors)
+            return
+
         # Legacy mode
         sensors_to_track = []
```

## window_control.py - Metodi Area-Based (NUOVI)

```python
# QUESTI METODI SONO COMPLETAMENTE NUOVI - NON ESISTONO IN v0.17.0 BASE

@callback
def _area_based_listener(self, event: Event[EventStateChangedData]) -> None:
    """Handle window sensor state changes in area-based mode."""
    window_id = event.data.get("entity_id")
    if not window_id:
        return
    
    new_state = event.data.get("new_state")
    if not new_state or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        return

    is_open = new_state.state in (STATE_ON, STATE_OPEN)
    
    if window_id in self._timers:
        self._timers[window_id]()
        del self._timers[window_id]
    
    if is_open:
        delay = self._window_open_delay
        _LOGGER.debug("[%s] Window %s opened, scheduling turn off in %ss", 
                     self._group.entity_id, window_id, delay)
        
        self._timers[window_id] = async_call_later(
            self._hass, delay,
            lambda _: self._hass.loop.call_soon_threadsafe(
                self._hass.async_create_task, self._handle_window_opened(window_id)
            )
        )
    else:
        delay = self._close_delay
        _LOGGER.debug("[%s] Window %s closed, scheduling restore check in %ss", 
                     self._group.entity_id, window_id, delay)
        
        self._timers[window_id] = async_call_later(
            self._hass, delay,
            lambda _: self._hass.loop.call_soon_threadsafe(
                self._hass.async_create_task, self._handle_window_closed(window_id)
            )
        )

async def _handle_window_opened(self, window_id: str) -> None:
    """Handle window opening after delay."""
    state = self._hass.states.get(window_id)
    if not state or state.state not in (STATE_ON, STATE_OPEN):
        _LOGGER.debug("[%s] Window %s no longer open, skipping", self._group.entity_id, window_id)
        return
        
    window_area = self._get_entity_area(window_id)
    if not window_area:
        _LOGGER.warning("[%s] Cannot determine area for window %s", self._group.entity_id, window_id)
        return

    thermostats_to_turn_off = self._get_thermostats_in_area(window_area, only_active=True)
    
    if not thermostats_to_turn_off:
        _LOGGER.debug("[%s] No active thermostats in area '%s'", self._group.entity_id, window_area)
        return

    _LOGGER.info("[%s] Window %s opened in area '%s', turning off: %s", 
                self._group.entity_id, window_id, window_area, thermostats_to_turn_off)
    
    # CHIAVE: Usa call_handler con entity_ids
    await self.call_handler.call_immediate({"hvac_mode": HVACMode.OFF}, entity_ids=thermostats_to_turn_off)

async def _handle_window_closed(self, window_id: str) -> None:
    """Handle window closing after delay."""
    state = self._hass.states.get(window_id)
    if not state or state.state in (STATE_ON, STATE_OPEN):
        _LOGGER.debug("[%s] Window %s no longer closed, skipping", self._group.entity_id, window_id)
        return
        
    window_area = self._get_entity_area(window_id)
    if not window_area:
        return

    # Check if any other windows in same area are still open
    for other_window_id in self._window_sensors:
        if other_window_id == window_id:
            continue
        
        if self._get_entity_area(other_window_id) == window_area:
            state = self._hass.states.get(other_window_id)
            if state and state.state in (STATE_ON, STATE_OPEN):
                _LOGGER.debug("[%s] Window %s closed but other windows still open in area '%s'", 
                             self._group.entity_id, window_id, window_area)
                return

    thermostats_to_restore = []
    for member_id in self._get_thermostats_in_area(window_area):
        state = self._hass.states.get(member_id)
        if state and state.state == HVACMode.OFF:
            thermostats_to_restore.append(member_id)
    
    if not thermostats_to_restore:
        _LOGGER.debug("[%s] No thermostats to restore in area '%s'", self._group.entity_id, window_area)
        return

    # CHIAVE: Usa target_state invece di _group.hvac_mode
    if self.target_state.hvac_mode == HVACMode.OFF:
        _LOGGER.debug("[%s] Target mode is OFF, not restoring", self._group.entity_id)
        return

    _LOGGER.info("[%s] Window %s closed, restoring area '%s': %s", 
                self._group.entity_id, window_id, window_area, thermostats_to_restore)
    
    # CHIAVE: call_immediate senza data usa target_state automaticamente
    await self.call_handler.call_immediate(entity_ids=thermostats_to_restore)

def _get_thermostats_in_area(self, area_id: str, only_active: bool = False) -> list[str]:
    """Get list of thermostats in the specified area."""
    thermostats = []
    for member_id in self._group.climate_entity_ids:
        if self._get_entity_area(member_id) == area_id:
            if only_active:
                state = self._hass.states.get(member_id)
                if state and state.state != HVACMode.OFF:
                    thermostats.append(member_id)
            else:
                thermostats.append(member_id)
    return thermostats

def _get_entity_area(self, entity_id: str) -> str | None:
    """Get the area ID for an entity."""
    ent_reg = er.async_get(self._hass)
    entity_entry = ent_reg.async_get(entity_id)
    
    if not entity_entry:
        return None
    
    if entity_entry.area_id:
        return entity_entry.area_id
    
    if entity_entry.device_id:
        dev_reg = dr.async_get(self._hass)
        device_entry = dev_reg.async_get(entity_entry.device_id)
        if device_entry and device_entry.area_id:
            return device_entry.area_id
    
    return None
```

## config_flow.py - async_step_window_control

```diff
--- a/config_flow.py (v0.17.0 base)
+++ b/config_flow.py (v0.17.0 + area-based)
@@ -18,6 +18,8 @@
     CONF_ROOM_SENSOR,
     CONF_SCHEDULE_ENTITY,
+    CONF_WINDOW_SENSORS,
+    CONF_WINDOW_OPEN_DELAY,
     CONF_ZONE_OPEN_DELAY,
     CONF_ZONE_SENSOR,
     DEFAULT_CLOSE_DELAY,
     DEFAULT_ROOM_OPEN_DELAY,
+    DEFAULT_WINDOW_OPEN_DELAY,
     DEFAULT_ZONE_OPEN_DELAY,
@@ -471,50 +473,120 @@
     async def async_step_window_control(
         self, user_input: dict[str, Any] | None = None
     ) -> ConfigFlowResult:
         """Manage window control settings."""
         current_config = {**self._config_entry.options, **(user_input or {})}

         if user_input is not None:
-            # If user clears a sensor field, remove it from config
-            for key in [CONF_ROOM_SENSOR, CONF_ZONE_SENSOR]:
-                if key not in user_input or not user_input.get(key):
-                    current_config.pop(key, None)
-            # Auto-disable window control if no sensors configured
-            if CONF_ROOM_SENSOR not in current_config and CONF_ZONE_SENSOR not in current_config:
-                current_config[CONF_WINDOW_MODE] = WindowControlMode.OFF
+            # Clean up based on mode
+            window_mode = user_input.get(CONF_WINDOW_MODE, WindowControlMode.OFF)
+            
+            if window_mode == WindowControlMode.AREA_BASED:
+                # Remove legacy config
+                for key in [CONF_ROOM_SENSOR, CONF_ZONE_SENSOR, CONF_ROOM_OPEN_DELAY, CONF_ZONE_OPEN_DELAY]:
+                    current_config.pop(key, None)
+                # Clear window_sensors if empty
+                if not user_input.get(CONF_WINDOW_SENSORS):
+                    current_config.pop(CONF_WINDOW_SENSORS, None)
+                    current_config[CONF_WINDOW_MODE] = WindowControlMode.OFF
+            else:
+                # Remove area-based config
+                for key in [CONF_WINDOW_SENSORS, CONF_WINDOW_OPEN_DELAY]:
+                    current_config.pop(key, None)
+                # Clear legacy sensors if empty
+                if CONF_ROOM_SENSOR not in user_input or not user_input.get(CONF_ROOM_SENSOR):
+                    current_config.pop(CONF_ROOM_SENSOR, None)
+                if CONF_ZONE_SENSOR not in user_input or not user_input.get(CONF_ZONE_SENSOR):
+                    current_config.pop(CONF_ZONE_SENSOR, None)
+                # Auto-disable if no sensors
+                if CONF_ROOM_SENSOR not in current_config and CONF_ZONE_SENSOR not in current_config:
+                    current_config[CONF_WINDOW_MODE] = WindowControlMode.OFF
             
             self._update_config_if_changed(current_config)
             return await self.async_step_schedule()

-        schema = vol.Schema(
-            {
-                vol.Required(
-                    CONF_WINDOW_MODE,
-                    default=current_config.get(CONF_WINDOW_MODE, WindowControlMode.OFF),
-                ): selector.SelectSelector(
-                    selector.SelectSelectorConfig(
-                        options=[opt.value for opt in WindowControlMode],
-                        mode=selector.SelectSelectorMode.DROPDOWN,
-                        translation_key="window_mode",
-                    )
-                ),
-                # ... campi statici legacy ...
-            }
-        )
+        # Build dynamic schema based on current mode
+        window_mode = current_config.get(CONF_WINDOW_MODE, WindowControlMode.OFF)
+        
+        schema_dict = {
+            vol.Required(
+                CONF_WINDOW_MODE,
+                default=window_mode,
+            ): selector.SelectSelector(
+                selector.SelectSelectorConfig(
+                    options=[opt.value for opt in WindowControlMode],
+                    mode=selector.SelectSelectorMode.DROPDOWN,
+                    translation_key="window_mode",
+                )
+            ),
+        }
+
+        # Area-based mode fields
+        if window_mode == WindowControlMode.AREA_BASED:
+            schema_dict[vol.Optional(
+                CONF_WINDOW_SENSORS,
+                description={"suggested_value": current_config.get(CONF_WINDOW_SENSORS, [])},
+            )] = selector.EntitySelector(
+                selector.EntitySelectorConfig(
+                    domain="binary_sensor",
+                    multiple=True,
+                )
+            )
+            schema_dict[vol.Optional(
+                CONF_WINDOW_OPEN_DELAY,
+                default=current_config.get(CONF_WINDOW_OPEN_DELAY, DEFAULT_WINDOW_OPEN_DELAY),
+            )] = selector.NumberSelector(
+                selector.NumberSelectorConfig(
+                    min=0,
+                    max=120,
+                    step=1,
+                    unit_of_measurement="s",
+                    mode=selector.NumberSelectorMode.SLIDER,
+                )
+            )
+        # Legacy mode fields
+        elif window_mode == WindowControlMode.ON:
+            # ... campi legacy ...
+
+        # Close delay (common to both modes)
+        if window_mode != WindowControlMode.OFF:
+            schema_dict[vol.Optional(
+                CONF_CLOSE_DELAY,
+                default=current_config.get(CONF_CLOSE_DELAY, DEFAULT_CLOSE_DELAY),
+            )] = selector.NumberSelector(...)

         return self.async_show_form(
             step_id="window_control",
-            data_schema=schema,
+            data_schema=vol.Schema(schema_dict),
         )
```

## strings.json

```diff
--- a/strings.json (v0.17.0 base)
+++ b/strings.json (v0.17.0 + area-based)
@@ -126,6 +126,8 @@
           "room_sensor": "Room Window Sensor",
           "zone_sensor": "Zone Window Sensor",
+          "window_sensors": "Window Sensors (Area-based)",
+          "window_open_delay": "Window Open Delay (seconds)",
           "close_delay": "Close Delay (seconds)"
         },
         "data_description": {
@@ -134,6 +136,8 @@
           "zone_sensor": "Binary sensor for other windows/doors in the zone/floor. Triggers the longer delay.",
+          "window_sensors": "Select all window sensors to monitor. When a window opens, only climate devices in the same area will be turned off.",
+          "window_open_delay": "Time to wait before turning off heating after a window opens.",
           "close_delay": "Time to wait after all windows close before restoring heating."
         }
       },
@@ -232,6 +236,7 @@
     "window_mode": {
       "options": {
         "off": "Off – Window control is disabled",
-        "on": "On – Window control is enabled"
+        "on": "On – Window control is enabled",
+        "area_based": "Area-based – Automatic zone detection"
       }
     },
```

---

## Riepilogo Modifiche

### Linee di Codice Aggiunte/Modificate

- **const.py**: +4 linee
- **service_call.py**: +18 linee
- **window_control.py**: +200 linee (5 nuovi metodi + documentazione)
- **config_flow.py**: +70 linee (logica dinamica)
- **strings.json**: +6 linee

**Totale**: ~300 linee di codice

### File NON Modificati

- `__init__.py` - Nessuna modifica necessaria
- `climate.py` - Nessuna modifica necessaria
- `state.py` - Nessuna modifica necessaria
- `sync_mode.py` - Nessuna modifica necessaria
- `schedule.py` - Nessuna modifica necessaria
- `sensor.py` - Nessuna modifica necessaria
- `manifest.json` - Solo versione aggiornata

---

**Data**: 2026-01-24  
**Versione Base**: 0.17.0  
**Versione Finale**: 0.17.0 + Area-Based Window Control
