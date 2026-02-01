# Technical Documentation

For complete technical documentation with architecture details, re-merge guide, and troubleshooting, see:

📄 **[docs_ita/TECHNICAL_DOCUMENTATION.md](docs_ita/TECHNICAL_DOCUMENTATION.md)** (Italian, 800+ lines)

## Quick Links

- **Architecture**: See Italian docs section "Architettura"
- **Re-merge Guide**: See Italian docs section "Guida al Re-Merge"
- **Test Suite**: See Italian docs section "Testing"
- **Troubleshooting**: See Italian docs section "Troubleshooting"

## English Summary

### v0.18.0 Architecture

The v0.18.0 version introduced a complete architectural redesign:

1. **State Management** (`state.py`): Immutable `TargetState` dataclass with metadata
2. **Service Call Handlers** (`service_call.py`): Specialized handlers with debouncing and retry logic
3. **Window Control** (`window_control.py`): Integrated with new architecture

### Area-Based Implementation

Key modifications:
- `window_control.py`: 5 new methods for area-based logic
- `service_call.py`: `entity_ids` parameter support
- `config_flow.py`: Dynamic UI based on mode
- `const.py`: Area-based constants
- `strings.json`: Translations

### Integration Points

```python
# Uses call_handler instead of direct service calls
await self.call_handler.call_immediate(entity_ids=[...])

# Uses target_state instead of _group attributes
if self.target_state.hvac_mode == HVACMode.OFF:

# Uses self._hass instead of self._group.hass
state = self._hass.states.get(entity_id)
```

---

For complete details, see the Italian documentation in `docs_ita/`.
