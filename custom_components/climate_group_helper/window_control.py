"""Window control handler for automatic heating shutdown when windows open.

CUSTOM MODIFICATION: Area-Based Window Control
===============================================
This file has been modified to support area-based window control in addition to
the legacy room/zone sensor mode.

Key Changes from v0.18.1 base:
1. Added area-based configuration (CONF_WINDOW_SENSORS, CONF_WINDOW_OPEN_DELAY)
2. Implemented _area_based_listener for per-window event handling
3. Added _handle_window_opened/_handle_window_closed for area-specific control
4. Added _get_entity_area for automatic area detection via registry
5. Added _get_thermostats_in_area for finding members by area
6. Integrated with v0.18.1 architecture (call_handler, target_state)

Architecture Integration:
- Uses self.call_handler.call_immediate(entity_ids=...) for targeted control
- Respects self.target_state for restoration
- Compatible with new state management system

Backward Compatibility:
- Legacy mode (room/zone sensors) fully preserved
- Automatic config cleanup when switching modes

Date: 2026-02-04
Version: 0.18.1 + Area-Based Window Control
"""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from homeassistant.components.climate import HVACMode
from homeassistant.const import STATE_ON, STATE_OPEN, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers import entity_registry as er, device_registry as dr

from .const import (
    CONF_CLOSE_DELAY,
    CONF_ROOM_OPEN_DELAY,
    CONF_ROOM_SENSOR,
    CONF_WINDOW_MODE,
    CONF_WINDOW_SENSORS,
    CONF_WINDOW_OPEN_DELAY,
    CONF_ZONE_OPEN_DELAY,
    CONF_ZONE_SENSOR,
    DEFAULT_CLOSE_DELAY,
    DEFAULT_ROOM_OPEN_DELAY,
    DEFAULT_ZONE_OPEN_DELAY,
    DEFAULT_WINDOW_OPEN_DELAY,
    WindowControlMode,
)

if TYPE_CHECKING:
    from .climate import ClimateGroup

_LOGGER = logging.getLogger(__name__)

# Constants
WINDOW_CLOSE = "close"
WINDOW_OPEN = "open"


class WindowControlHandler:
    """Manages window control logic with support for legacy and area-based modes."""

    def __init__(self, group: ClimateGroup) -> None:
        """Initialize the window control handler."""
        self._group = group
        self._hass = group.hass
        self._timer_cancel: Any = None
        self._unsub_listener = None

        self._window_control_mode = self._group.config.get(CONF_WINDOW_MODE, WindowControlMode.OFF)
        self._control_state = WINDOW_CLOSE

        # Legacy configuration
        self._room_sensor = group.config.get(CONF_ROOM_SENSOR)
        self._zone_sensor = group.config.get(CONF_ZONE_SENSOR)
        self._room_delay = group.config.get(CONF_ROOM_OPEN_DELAY, DEFAULT_ROOM_OPEN_DELAY)
        self._zone_delay = group.config.get(CONF_ZONE_OPEN_DELAY, DEFAULT_ZONE_OPEN_DELAY)

        # Area-based configuration
        self._window_sensors = group.config.get(CONF_WINDOW_SENSORS, [])
        self._window_open_delay = group.config.get(CONF_WINDOW_OPEN_DELAY, DEFAULT_WINDOW_OPEN_DELAY)
        self._close_delay = group.config.get(CONF_CLOSE_DELAY, DEFAULT_CLOSE_DELAY)

        # Area-based state tracking
        self._timers: dict[str, Any] = {}

        # Legacy state tracking
        self._room_open = False
        self._zone_open = False
        self._room_last_changed = None
        self._zone_last_changed = None

        _LOGGER.debug(
            "[%s] WindowControl initialized. Mode: %s",
            group.entity_id, self._window_control_mode)

    @property
    def state_manager(self):
        """Return the specialized state manager for window control (read-only)."""
        return self._group.window_control_state_manager

    @property
    def call_handler(self):
        """Return the specialized call handler for window control operations."""
        return self._group.window_control_call_handler

    @property
    def target_state(self):
        """Return the current target state (from central source)."""
        return self.state_manager.target_state

    @property
    def force_off(self) -> bool:
        """Return whether window control is active."""
        if self._window_control_mode == WindowControlMode.AREA_BASED:
            for window_id in self._window_sensors:
                state = self._hass.states.get(window_id)
                if state and state.state in (STATE_ON, STATE_OPEN):
                    return True
            return False
        return self._control_state == WINDOW_OPEN

    def async_teardown(self) -> None:
        """Unsubscribe from sensors and cancel timers."""
        self._cancel_timer()
        for cancel_func in self._timers.values():
            if cancel_func:
                cancel_func()
        self._timers.clear()
        if self._unsub_listener:
            self._unsub_listener()
            self._unsub_listener = None

    async def async_setup(self) -> None:
        """Subscribe to window sensor state changes."""

        if self._window_control_mode == WindowControlMode.OFF:
            _LOGGER.debug("[%s] Window control is disabled", self._group.entity_id)
            return

        # Area-based mode
        if self._window_control_mode == WindowControlMode.AREA_BASED:
            if not self._window_sensors:
                _LOGGER.warning("[%s] Area-based window control enabled but no sensors configured", self._group.entity_id)
                return
            
            self._unsub_listener = async_track_state_change_event(
                self._hass, self._window_sensors, self._area_based_listener
            )
            _LOGGER.debug("[%s] Area-based window control subscribed to: %s", self._group.entity_id, self._window_sensors)
            return

        # Legacy mode
        sensors_to_track = []
        if self._room_sensor:
            sensors_to_track.append(self._room_sensor)
        if self._zone_sensor:
            sensors_to_track.append(self._zone_sensor)
        if not sensors_to_track:
            return

        # Subscribe to window sensor state changes
        self._unsub_listener = async_track_state_change_event(
            self._hass, sensors_to_track, self._state_change_listener,
        )

        _LOGGER.debug("[%s] Window control subscribed to: %s", self._group.entity_id, sensors_to_track)

        # Check initial state
        result = self._window_control_logic()
        if result:
            mode, delay = result
            if mode == WINDOW_OPEN:
                self._control_state = WINDOW_OPEN
            if delay <= 0:
                self._hass.async_create_task(self._execute_action(mode))
            else:
                self._timer_cancel = async_call_later(self._hass, delay, self._timer_expired)

    @callback
    def _state_change_listener(self, event: Event[EventStateChangedData]) -> None:
        """Handle sensor event – recalculate and schedule action."""
        _LOGGER.debug("[%s] Sensor event: %s", self._group.entity_id, event.data.get("entity_id"))

        result = self._window_control_logic()
        if result is None:
            _LOGGER.debug("[%s] Window control sensors not available", self._group.entity_id)
            self._control_state = WINDOW_CLOSE
            return

        mode, delay = result
        self._cancel_timer()

        # Skip timer if no action needed (HVAC already in desired state)
        current_hvac = self._group.hvac_mode
        if mode == WINDOW_OPEN and current_hvac == HVACMode.OFF:
            _LOGGER.debug("[%s] HVAC is already OFF, skipping timer", self._group.entity_id)
            self._control_state = WINDOW_OPEN  # Clear blocking mode
            return

        elif mode == WINDOW_CLOSE and current_hvac != HVACMode.OFF:
            _LOGGER.debug("[%s] HVAC is already ON, skipping timer", self._group.entity_id)
            self._control_state = WINDOW_CLOSE  # Clear blocking mode
            return
        
        if delay > 0:
            _LOGGER.debug("[%s] Scheduling action in %.1fs", self._group.entity_id, delay)
            self._timer_cancel = async_call_later(self._hass, delay, self._timer_expired)
        else:
            self._hass.async_create_task(self._execute_action(mode))

    @callback
    def _timer_expired(self, now: Any) -> None:
        """Timer callback – recalculate and execute current action."""
        self._timer_cancel = None
        mode, _ = self._window_control_logic()
        if mode:
            self._hass.async_create_task(self._execute_action(mode))

    def _cancel_timer(self) -> None:
        """Cancel any pending timer."""
        if self._timer_cancel:
            self._timer_cancel()
            self._timer_cancel = None
            _LOGGER.debug("[%s] Timer cancelled", self._group.entity_id)

    async def _execute_action(self, mode: str) -> None:
        """Execute heating ON/OFF action.
        
        Window Control does NOT modify target_state:
        - OPEN: Forces members OFF via call_immediate
        - CLOSE: Restores members to target_state via call_immediate
        """
        # Update control state first
        self._control_state = mode

        if mode == WINDOW_OPEN:
            # Turn HVAC OFF via self.call_handler (WindowControlCallHandler)
            if self._group.hvac_mode != HVACMode.OFF:
                _LOGGER.debug("[%s] Window opened, turning HVAC OFF", self._group.entity_id)
                await self.call_handler.call_immediate({"hvac_mode": HVACMode.OFF})
            else:
                _LOGGER.debug("[%s] Window opened, HVAC already OFF in target_state", self._group.entity_id)

        elif mode == WINDOW_CLOSE:
            # Restore target_state via self.call_handler
            _LOGGER.debug("[%s] Window closed, restoring target_state", self._group.entity_id)
            await self.call_handler.call_immediate()

    def _window_control_logic(self) -> tuple[str, float] | None:
        """This method implements the core logic from the Window Heating Control blueprint.
        
        Return the control mode and the timer delay.
        Return None if no sensors are configured.
        """
        self._room_open = None
        self._zone_open = None
        self._room_last_changed = None
        self._zone_last_changed = None

        # If no sensors are configured, return None
        if not self._room_sensor and not self._zone_sensor:
            return None

        # If no room sensor is configured, room is always closed
        if self._room_sensor and (state := self._hass.states.get(self._room_sensor)):
            self._room_open = state.state in (STATE_ON, STATE_OPEN)
            self._room_last_changed = time.time() - state.last_changed.timestamp()
        else:
            self._room_open = False
            self._room_last_changed = float("inf")

        # If no zone sensor is configured, use room sensor state
        if self._zone_sensor and (state := self._hass.states.get(self._zone_sensor)):
            self._zone_open = state.state in (STATE_ON, STATE_OPEN) or self._room_open
            self._zone_last_changed = time.time() - state.last_changed.timestamp()
        else:
            self._zone_open = self._room_open
            self._zone_last_changed = self._room_last_changed

        # Calculate timers
        timer_room_open = max(self._room_delay - self._room_last_changed, 0) if self._room_open else self._room_delay
        timer_zone_open = max(self._zone_delay - self._zone_last_changed, 0) if self._zone_open else self._zone_delay
        timer_zone_close = max(self._close_delay - self._zone_last_changed, 0) if not self._zone_open else self._close_delay

        # Calculate delays
        delay_room_open = min(timer_room_open, timer_zone_open) if self._room_open else None
        delay_zone_open = timer_zone_open if self._zone_open and not self._room_open else None
        delay_zone_close = timer_zone_close if not self._zone_open or not self._room_open else None

        # Calculate mode and delay
        mode = WINDOW_OPEN if self._zone_open or self._room_open else WINDOW_CLOSE
        delay = (delay_room_open or delay_zone_open or delay_zone_close) or 0

        _LOGGER.debug("[%s] Window control: mode=%s, delay=%.1fs (room_open=%s, zone_open=%s)",
            self._group.entity_id, mode, delay, self._room_open, self._zone_open)

        return mode, delay

    # ============================================================================
    # AREA-BASED WINDOW CONTROL METHODS (CUSTOM MODIFICATION)
    # ============================================================================

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
        
        # Cancel existing timer for this window
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
        """Handle window opened event for area-based control."""
        try:
            # Clean up timer
            if window_id in self._timers:
                del self._timers[window_id]
            
            # Get area for this window
            area_id = self._get_entity_area(window_id)
            if not area_id:
                _LOGGER.warning("[%s] Could not determine area for window %s", 
                               self._group.entity_id, window_id)
                return
            
            # Get thermostats in this area
            target_entity_ids = self._get_thermostats_in_area(area_id)
            if not target_entity_ids:
                _LOGGER.debug("[%s] No thermostats found in area %s for window %s", 
                             self._group.entity_id, area_id, window_id)
                return
            
            _LOGGER.info("[%s] Window %s opened in area %s, turning off thermostats: %s", 
                        self._group.entity_id, window_id, area_id, target_entity_ids)
            
            # Turn off thermostats in this area
            await self.call_handler.call_immediate(
                data={"hvac_mode": HVACMode.OFF},
                entity_ids=target_entity_ids
            )
            
        except Exception as e:
            _LOGGER.error("[%s] Error handling window opened for %s: %s", 
                         self._group.entity_id, window_id, e)

    async def _handle_window_closed(self, window_id: str) -> None:
        """Handle window closed event for area-based control."""
        try:
            # Clean up timer
            if window_id in self._timers:
                del self._timers[window_id]
            
            # Check if any other windows in the same area are still open
            area_id = self._get_entity_area(window_id)
            if not area_id:
                return
            
            # Check if any other windows in this area are still open
            area_windows_open = False
            for sensor_id in self._window_sensors:
                if sensor_id == window_id:
                    continue
                    
                sensor_area = self._get_entity_area(sensor_id)
                if sensor_area == area_id:
                    state = self._hass.states.get(sensor_id)
                    if state and state.state in (STATE_ON, STATE_OPEN):
                        area_windows_open = True
                        break
            
            if area_windows_open:
                _LOGGER.debug("[%s] Window %s closed but other windows in area %s still open", 
                             self._group.entity_id, window_id, area_id)
                return
            
            # Get thermostats in this area
            target_entity_ids = self._get_thermostats_in_area(area_id)
            if not target_entity_ids:
                return
            
            # Check if group has a target state to restore
            if not self.target_state:
                _LOGGER.debug("[%s] No target state to restore for area %s", 
                             self._group.entity_id, area_id)
                return
            
            _LOGGER.info("[%s] All windows closed in area %s, restoring thermostats: %s", 
                        self._group.entity_id, area_id, target_entity_ids)
            
            # Restore target state for thermostats in this area
            restore_data = {}
            if hasattr(self.target_state, 'hvac_mode') and self.target_state.hvac_mode:
                restore_data["hvac_mode"] = self.target_state.hvac_mode
            if hasattr(self.target_state, 'temperature') and self.target_state.temperature:
                restore_data["temperature"] = self.target_state.temperature
            
            if restore_data:
                await self.call_handler.call_immediate(
                    data=restore_data,
                    entity_ids=target_entity_ids
                )
            
        except Exception as e:
            _LOGGER.error("[%s] Error handling window closed for %s: %s", 
                         self._group.entity_id, window_id, e)

    def _get_entity_area(self, entity_id: str) -> str | None:
        """Get the area ID for an entity."""
        try:
            entity_registry = er.async_get(self._hass)
            entity_entry = entity_registry.async_get(entity_id)
            
            if entity_entry and entity_entry.area_id:
                return entity_entry.area_id
            
            # If entity has no area, try to get it from device
            if entity_entry and entity_entry.device_id:
                device_registry = dr.async_get(self._hass)
                device_entry = device_registry.async_get(entity_entry.device_id)
                if device_entry and device_entry.area_id:
                    return device_entry.area_id
            
            return None
            
        except Exception as e:
            _LOGGER.error("[%s] Error getting area for entity %s: %s", 
                         self._group.entity_id, entity_id, e)
            return None

    def _get_thermostats_in_area(self, area_id: str) -> list[str]:
        """Get list of group member thermostats in the specified area."""
        thermostats_in_area = []
        
        try:
            entity_registry = er.async_get(self._hass)
            device_registry = dr.async_get(self._hass)
            
            for member_id in self._group.climate_entity_ids:
                entity_entry = entity_registry.async_get(member_id)
                if not entity_entry:
                    continue
                
                # Check if entity is directly in the area
                if entity_entry.area_id == area_id:
                    thermostats_in_area.append(member_id)
                    continue
                
                # Check if entity's device is in the area
                if entity_entry.device_id:
                    device_entry = device_registry.async_get(entity_entry.device_id)
                    if device_entry and device_entry.area_id == area_id:
                        thermostats_in_area.append(member_id)
            
            return thermostats_in_area
            
        except Exception as e:
            _LOGGER.error("[%s] Error getting thermostats in area %s: %s", 
                         self._group.entity_id, area_id, e)
            return []