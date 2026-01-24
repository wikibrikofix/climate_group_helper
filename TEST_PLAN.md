# Test Plan

For complete test plan with 12 test cases, see:

📄 **[docs_ita/TEST_PLAN.md](docs_ita/TEST_PLAN.md)** (Italian, 400+ lines)

## Quick Test

### Basic Test
```
1. Open window → thermostat in same area turns off (15s delay)
2. Close window → thermostat in same area turns back on (30s delay)
```

### Verification
```bash
# Check logs
ha core logs | grep "WindowControl initialized"
# Expected: "Mode: area_based"

ha core logs | grep "turning off"
# Expected: Only area thermostat

ha core logs | grep "restoring"
# Expected: Only area thermostat
```

### Test Cases

See Italian docs for:
- Single window open/close
- Multiple windows same area
- Multiple windows different areas
- Entity without area
- Group target mode OFF
- And 7 more test cases

---

**Status**: ✅ Tested on 2026-01-24
