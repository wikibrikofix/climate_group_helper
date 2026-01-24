# Comparison v0.16.1 vs v0.17.0

For detailed architectural comparison, see:

📄 **[docs_ita/COMPARISON.md](docs_ita/COMPARISON.md)** (Italian, 500+ lines)

## Quick Summary

### Main Differences

| Aspect | v0.16.1 | v0.17.0 |
|--------|---------|---------|
| Service calls | `hass.services.async_call()` | `call_handler.call_immediate()` |
| State | `_group.hvac_mode` | `target_state.hvac_mode` |
| Hass access | `_group.hass` | `_hass` |
| Targeting | Manual loop | `entity_ids` parameter |
| Context tracking | Manual | Automatic |
| Retry logic | None | Automatic |

### Advantages v0.17.0

- ✅ Better integration with Schedule and Sync Mode
- ✅ Conflict prevention via source-aware state management
- ✅ Automatic retry logic and debouncing
- ✅ Context tracking for echo detection
- ✅ More maintainable and testable code

See Italian docs for detailed code examples.
