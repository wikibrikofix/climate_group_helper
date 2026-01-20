"""Window control handler for automatic heating shutdown when windows open."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.climate import HVACMode
from homeassistant.const import STATE_ON, STATE_OPEN, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers import entity_registry as er

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


class WindowControlHandler:
    """Manages automatic thermostat control based on window states.
    
    Supports two modes:
    - Legacy: Single room/zone sensors with delays
    - Area-based: Multiple window sensors with per-area thermostat control
    
    In area-based mode, opening a window will turn off thermostats in the same
    area after a configurable delay. Closing the window will restore thermostats
    if no other windows in the area remain open.
    """

    def __init__(self, group: ClimateGroup) -> None:
        """Initialize the window control handler.
        
        Args:
            group: The climate group this handler belongs to
        """
        self._group = group
        self._unsub_listener = None

        self._window_control_mode = self._group.config.get(CONF_WINDOW_MODE, WindowControlMode.OFF)
        
        # Legacy configuration (backward compatibility with older versions)
        self._room_sensor = group.config.get(CONF_ROOM_SENSOR)
        self._zone_sensor = group.config.get(CONF_ZONE_SENSOR)
        self._room_delay = group.config.get(CONF_ROOM_OPEN_DELAY, DEFAULT_ROOM_OPEN_DELAY)
        self._zone_delay = group.config.get(CONF_ZONE_OPEN_DELAY, DEFAULT_ZONE_OPEN_DELAY)

        # Area-based configuration (new implementation)
        self._window_sensors = group.config.get(CONF_WINDOW_SENSORS, [])
        self._window_open_delay = group.config.get(CONF_WINDOW_OPEN_DELAY, DEFAULT_WINDOW_OPEN_DELAY)
        self._close_delay = group.config.get(CONF_CLOSE_DELAY, DEFAULT_CLOSE_DELAY)
        
        # Active timers for delayed actions (area-based mode only)
        self._timers: dict[str, Any] = {}  # window_id -> timer_cancel_function

        # Legacy state tracking (maintained for backward compatibility)
        self._control_state = "close"
        self._room_open = False
        self._zone_open = False
        self._room_last_changed = None
        self._zone_last_changed = None
        
        _LOGGER.debug(
            "[%s] WindowControl initialized. Mode: %s, Windows: %s, Open delay: %ss, Close delay: %ss",
            group.entity_id, self._window_control_mode, self._window_sensors, 
            self._window_open_delay, self._close_delay)

    @property
    def force_off(self) -> bool:
        """Check if window control should force HVAC off.
        
        Returns:
            True if any monitored windows are open and HVAC should be turned off
        """
        if self._window_control_mode != WindowControlMode.AREA_BASED:
            # Legacy mode compatibility
            return self._control_state == "open"
            
        # Area-based mode: check if any monitored windows are open
        for window_id in self._window_sensors:
            state = self._group.hass.states.get(window_id)
            if state and state.state in (STATE_ON, STATE_OPEN):
                return True
        return False

    def async_teardown(self) -> None:
        """Clean up resources when the handler is being removed."""
        # Cancel all active timers
        for cancel_func in self._timers.values():
            if cancel_func:
                cancel_func()
        self._timers.clear()
        
        # Unsubscribe from state change events
        if self._unsub_listener:
            self._unsub_listener()
            self._unsub_listener = None

    async def async_setup(self) -> None:
        """Set up window control by subscribing to sensor state changes."""
        if self._window_control_mode == WindowControlMode.OFF:
            _LOGGER.debug("[%s] Window control is disabled", self._group.entity_id)
            return

        # Area-based mode: monitor multiple window sensors
        if self._window_control_mode == WindowControlMode.AREA_BASED:
            if not self._window_sensors:
                _LOGGER.warning("[%s] Area-based window control enabled but no sensors configured", self._group.entity_id)
                return
            
            # Subscribe to state changes for all configured window sensors
            self._unsub_listener = async_track_state_change_event(
                self._group.hass, self._window_sensors, self._area_based_listener
            )
            _LOGGER.debug("[%s] Area-based window control subscribed to: %s", self._group.entity_id, self._window_sensors)
            return

        # Legacy mode: monitor single room/zone sensors (backward compatibility)
        sensors_to_track = []
        if self._room_sensor:
            sensors_to_track.append(self._room_sensor)
        if self._zone_sensor:
            sensors_to_track.append(self._zone_sensor)
        if not sensors_to_track:
            return

        self._unsub_listener = async_track_state_change_event(
            self._group.hass, sensors_to_track, self._state_change_listener,
        )

        _LOGGER.debug("[%s] Window control subscribed to: %s", self._group.entity_id, sensors_to_track)

        # Check initial state for legacy mode
        result = self._window_control_logic()
        if result:
            mode, delay = result
            if mode == "open":
                self._control_state = "open"
            if delay <= 0:
                self._group.hass.async_create_task(self._execute_action(mode))
            else:
                self._timers["legacy"] = async_call_later(self._group.hass, delay, self._timer_expired)

    @callback
    def _area_based_listener(self, event: Event[EventStateChangedData]) -> None:
        """Handle window sensor state changes in area-based mode.
        
        This is the main event handler for area-based window control.
        It schedules delayed actions based on window open/close events.
        
        Args:
            event: State change event from Home Assistant
        """
        window_id = event.data.get("entity_id")
        if not window_id:
            return
        
        new_state = event.data.get("new_state")
        if not new_state or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        is_open = new_state.state in (STATE_ON, STATE_OPEN)
        
        # Cancel any existing timer for this window to avoid conflicts
        if window_id in self._timers:
            self._timers[window_id]()
            del self._timers[window_id]
        
        if is_open:
            # Window opened: schedule thermostat turn-off after delay
            delay = self._window_open_delay
            _LOGGER.debug("[%s] Window %s opened, scheduling turn off in %ss", 
                         self._group.entity_id, window_id, delay)
            
            self._timers[window_id] = async_call_later(
                self._group.hass, delay,
                lambda _: self._group.hass.loop.call_soon_threadsafe(
                    self._group.hass.async_create_task, self._handle_window_opened(window_id)
                )
            )
        else:
            # Window closed: schedule thermostat restore check after delay
            delay = self._close_delay
            _LOGGER.debug("[%s] Window %s closed, scheduling restore check in %ss", 
                         self._group.entity_id, window_id, delay)
            
            self._timers[window_id] = async_call_later(
                self._group.hass, delay,
                lambda _: self._group.hass.loop.call_soon_threadsafe(
                    self._group.hass.async_create_task, self._handle_window_closed(window_id)
                )
            )

    def _get_thermostats_in_area(self, area_id: str, only_active: bool = False) -> list[str]:
        """Get list of thermostats in the specified area.
        
        Args:
            area_id: The area ID to search in
            only_active: If True, only return thermostats that are not OFF
            
        Returns:
            List of thermostat entity IDs in the area
        """
        thermostats = []
        for member_id in self._group.config.get("entities", []):
            member_area = self._get_entity_area(member_id)
            if member_area == area_id:
                if only_active:
                    state = self._group.hass.states.get(member_id)
                    if state and state.state != HVACMode.OFF:
                        thermostats.append(member_id)
                else:
                    thermostats.append(member_id)
        return thermostats

    async def _handle_window_opened(self, window_id: str) -> None:
        """Handle window opening after delay - verify state and turn off thermostats."""
        # Verify window is still open
        state = self._group.hass.states.get(window_id)
        if not state or state.state not in (STATE_ON, STATE_OPEN):
            _LOGGER.debug("[%s] Window %s no longer open, skipping turn off", 
                         self._group.entity_id, window_id)
            return
            
        window_area = self._get_entity_area(window_id)
        if not window_area:
            _LOGGER.warning("[%s] Cannot determine area for window %s", self._group.entity_id, window_id)
            return

        # Find active thermostats in same area
        thermostats_to_turn_off = self._get_thermostats_in_area(window_area, only_active=True)
        
        if not thermostats_to_turn_off:
            _LOGGER.debug("[%s] No active thermostats to turn off in area '%s'", 
                         self._group.entity_id, window_area)
            return

        _LOGGER.info("[%s] Window %s opened in area '%s', turning off: %s", 
                    self._group.entity_id, window_id, window_area, thermostats_to_turn_off)
        
        # Turn off thermostats
        for member_id in thermostats_to_turn_off:
            await self._group.hass.services.async_call(
                "climate", "set_hvac_mode",
                {"entity_id": member_id, "hvac_mode": HVACMode.OFF},
                blocking=False
            )

    async def _handle_window_closed(self, window_id: str) -> None:
        """Handle window closing after delay - verify state and restore thermostats."""
        # Verify window is still closed
        state = self._group.hass.states.get(window_id)
        if not state or state.state in (STATE_ON, STATE_OPEN):
            _LOGGER.debug("[%s] Window %s no longer closed, skipping restore", 
                         self._group.entity_id, window_id)
            return
            
        window_area = self._get_entity_area(window_id)
        if not window_area:
            return

        # Check if any other windows in same area are still open
        other_windows_open = []
        for other_window_id in self._window_sensors:
            if other_window_id == window_id:
                continue
            
            other_area = self._get_entity_area(other_window_id)
            if other_area == window_area:
                state = self._group.hass.states.get(other_window_id)
                if state and state.state in (STATE_ON, STATE_OPEN):
                    other_windows_open.append(other_window_id)
        
        if other_windows_open:
            _LOGGER.debug("[%s] Window %s closed but other windows still open in area '%s': %s", 
                         self._group.entity_id, window_id, window_area, other_windows_open)
            return

        # Find OFF thermostats in area that can be restored
        thermostats_to_restore = []
        for member_id in self._get_thermostats_in_area(window_area):
            state = self._group.hass.states.get(member_id)
            if state and state.state == HVACMode.OFF:
                thermostats_to_restore.append(member_id)
        
        if not thermostats_to_restore:
            _LOGGER.debug("[%s] No thermostats to restore in area '%s'", 
                         self._group.entity_id, window_area)
            return

        # Get target mode from group
        target_mode = self._group.hvac_mode
        if not target_mode or target_mode == HVACMode.OFF:
            _LOGGER.debug("[%s] Group target mode is %s, not restoring", 
                         self._group.entity_id, target_mode)
            return

        _LOGGER.info("[%s] Window %s closed, no other windows open in area '%s', restoring to %s: %s", 
                    self._group.entity_id, window_id, window_area, target_mode, thermostats_to_restore)
        
        # Restore thermostats
        for member_id in thermostats_to_restore:
            await self._group.hass.services.async_call(
                "climate", "set_hvac_mode",
                {"entity_id": member_id, "hvac_mode": target_mode},
                blocking=False
            )

    def _get_entity_area(self, entity_id: str) -> str | None:
        """Get the area ID for an entity."""
        ent_reg = er.async_get(self._group.hass)
        entity_entry = ent_reg.async_get(entity_id)
        
        if not entity_entry:
            return None
        
        # Try entity's area first
        if entity_entry.area_id:
            return entity_entry.area_id
        
        # Try device's area
        if entity_entry.device_id:
            from homeassistant.helpers import device_registry as dr
            dev_reg = dr.async_get(self._group.hass)
            device_entry = dev_reg.async_get(entity_entry.device_id)
            if device_entry and device_entry.area_id:
                return device_entry.area_id
        
        return None

    # Legacy methods below (for backward compatibility)

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
        if "legacy" in self._timer_cancel and self._timer_cancel["legacy"]:
            self._timer_cancel["legacy"]()
            del self._timer_cancel["legacy"]

        current_hvac = self._group.hvac_mode
        if mode == WINDOW_OPEN and current_hvac == HVACMode.OFF:
            _LOGGER.debug("[%s] HVAC is already OFF, skipping timer", self._group.entity_id)
            self._control_state = WINDOW_OPEN
            return
        elif mode == WINDOW_CLOSE and current_hvac != HVACMode.OFF:
            _LOGGER.debug("[%s] HVAC is already ON, skipping timer", self._group.entity_id)
            self._control_state = WINDOW_CLOSE
            return
        
        if delay > 0:
            _LOGGER.debug("[%s] Scheduling action in %.1fs", self._group.entity_id, delay)
            self._timer_cancel["legacy"] = async_call_later(self._group.hass, delay, self._timer_expired)
        else:
            self._group.hass.async_create_task(self._execute_action(mode))

    @callback
    def _timer_expired(self, now: Any) -> None:
        """Timer callback – recalculate and execute current action."""
        if "legacy" in self._timer_cancel:
            del self._timer_cancel["legacy"]
        mode, _ = self._window_control_logic()
        if mode:
            self._group.hass.async_create_task(self._execute_action(mode))

    async def _execute_action(self, mode: str) -> None:
        """Execute heating ON/OFF action (legacy mode)."""
        self._control_state = mode

        if mode == WINDOW_OPEN:
            if self._group.hvac_mode != HVACMode.OFF:
                _LOGGER.debug("[%s] Window opened, turning HVAC OFF", self._group.entity_id)
                await self._group.service_call_handler.call_hvac_off(context_id="window_control")
            else:
                _LOGGER.debug("[%s] Window opened, HVAC already OFF in target_state", self._group.entity_id)
        elif mode == WINDOW_CLOSE:
            _LOGGER.debug("[%s] Window closed, restoring target_state", self._group.entity_id)
            await self._group.service_call_handler.call_immediate(context_id="window_control")

    def _window_control_logic(self) -> tuple[str, float] | None:
        """Legacy window control logic."""
        self._room_open = None
        self._zone_open = None
        self._room_last_changed = None
        self._zone_last_changed = None

        if not self._room_sensor and not self._zone_sensor:
            return None

        if self._room_sensor and (state := self._group.hass.states.get(self._room_sensor)):
            self._room_open = state.state in (STATE_ON, STATE_OPEN)
            self._room_last_changed = time.time() - state.last_changed.timestamp()
        else:
            self._room_open = False
            self._room_last_changed = float("inf")

        if self._zone_sensor and (state := self._group.hass.states.get(self._zone_sensor)):
            self._zone_open = state.state in (STATE_ON, STATE_OPEN) or self._room_open
            self._zone_last_changed = time.time() - state.last_changed.timestamp()
        else:
            self._zone_open = self._room_open
            self._zone_last_changed = self._room_last_changed

        timer_room_open = max(self._room_delay - self._room_last_changed, 0) if self._room_open else self._room_delay
        timer_zone_open = max(self._zone_delay - self._zone_last_changed, 0) if self._zone_open else self._zone_delay
        timer_zone_close = max(self._close_delay - self._zone_last_changed, 0) if not self._zone_open else self._close_delay

        delay_room_open = min(timer_room_open, timer_zone_open) if self._room_open else None
        delay_zone_open = timer_zone_open if self._zone_open and not self._room_open else None
        delay_zone_close = timer_zone_close if not self._zone_open or not self._room_open else None

        mode = WINDOW_OPEN if self._zone_open or self._room_open else WINDOW_CLOSE
        delay = (delay_room_open or delay_zone_open or delay_zone_close) or 0

        _LOGGER.debug("[%s] Window control: mode=%s, delay=%.1fs (room_open=%s, zone_open=%s)",
            self._group.entity_id, mode, delay, self._room_open, self._zone_open)

        return mode, delay
