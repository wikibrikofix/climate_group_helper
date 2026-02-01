# Confronto: Fork v0.16.1 vs Nuovo v0.18.0 con Area-Based

## Architettura Window Control

### Fork v0.16.1
```python
# Chiamata diretta ai servizi
await self._group.hass.services.async_call(
    "climate", "set_hvac_mode",
    {"entity_id": member_id, "hvac_mode": HVACMode.OFF},
    blocking=False
)
```

### Nuovo v0.18.0
```python
# Usa il call handler con entity_ids opzionale
await self.call_handler.call_immediate(
    {"hvac_mode": HVACMode.OFF}, 
    entity_ids=thermostats_to_turn_off
)
```

**Vantaggi:**
- ✅ Retry logic automatico
- ✅ Context tracking per echo detection
- ✅ Integrazione con state management
- ✅ Debouncing quando necessario

---

## Gestione dello Stato

### Fork v0.16.1
```python
# Stato semplice
self._control_state = "open"  # o "close"
```

### Nuovo v0.18.0
```python
# Stato immutabile con metadata
@property
def target_state(self):
    return self.state_manager.target_state

# TargetState include:
# - hvac_mode, temperature, etc.
# - last_source, last_entity, last_timestamp
```

**Vantaggi:**
- ✅ Source-aware (distingue user/schedule/window)
- ✅ Immutabile (thread-safe)
- ✅ Metadata per tracking
- ✅ Prevenzione conflitti

---

## Proprietà e Accesso

### Fork v0.16.1
```python
# Accesso diretto
self._group.hass
self._group.config
self._group.hvac_mode
```

### Nuovo v0.18.0
```python
# Accesso tramite proprietà
self._hass
self.state_manager
self.call_handler
self.target_state
```

**Vantaggi:**
- ✅ Separazione delle responsabilità
- ✅ Testabilità migliorata
- ✅ Dependency injection

---

## Timer Management

### Fork v0.16.1
```python
# Timer multipli in dict
self._timers: dict[str, Any] = {}

# Cancellazione manuale
if window_id in self._timers:
    self._timers[window_id]()
    del self._timers[window_id]
```

### Nuovo v0.18.0
```python
# Stesso approccio per area-based
self._timers: dict[str, Any] = {}

# Timer singolo per legacy
self._timer_cancel: Any = None

# Cleanup in async_teardown()
for cancel_func in self._timers.values():
    if cancel_func:
        cancel_func()
```

**Nota:** Timer management è simile, ma con cleanup più robusto

---

## Area Detection

### Fork v0.16.1
```python
def _get_entity_area(self, entity_id: str) -> str | None:
    ent_reg = er.async_get(self._group.hass)
    entity_entry = ent_reg.async_get(entity_id)
    
    if not entity_entry:
        return None
    
    if entity_entry.area_id:
        return entity_entry.area_id
    
    if entity_entry.device_id:
        from homeassistant.helpers import device_registry as dr
        dev_reg = dr.async_get(self._group.hass)
        device_entry = dev_reg.async_get(entity_entry.device_id)
        if device_entry and device_entry.area_id:
            return device_entry.area_id
    
    return None
```

### Nuovo v0.18.0
```python
def _get_entity_area(self, entity_id: str) -> str | None:
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

**Nota:** Logica identica, solo `self._hass` invece di `self._group.hass`

---

## Window Open Handler

### Fork v0.16.1
```python
async def _handle_window_opened(self, window_id: str) -> None:
    # Verifica stato
    state = self._group.hass.states.get(window_id)
    if not state or state.state not in (STATE_ON, STATE_OPEN):
        return
    
    # Trova termostati
    thermostats = self._get_thermostats_in_area(window_area, only_active=True)
    
    # Spegni direttamente
    for member_id in thermostats:
        await self._group.hass.services.async_call(
            "climate", "set_hvac_mode",
            {"entity_id": member_id, "hvac_mode": HVACMode.OFF},
            blocking=False
        )
```

### Nuovo v0.18.0
```python
async def _handle_window_opened(self, window_id: str) -> None:
    # Verifica stato
    state = self._hass.states.get(window_id)
    if not state or state.state not in (STATE_ON, STATE_OPEN):
        return
    
    # Trova termostati
    thermostats = self._get_thermostats_in_area(window_area, only_active=True)
    
    # Usa call handler
    await self.call_handler.call_immediate(
        {"hvac_mode": HVACMode.OFF}, 
        entity_ids=thermostats
    )
```

**Differenza chiave:** Usa `call_handler` invece di chiamata diretta

---

## Window Close Handler

### Fork v0.16.1
```python
async def _handle_window_closed(self, window_id: str) -> None:
    # Verifica altre finestre aperte
    if other_windows_open:
        return
    
    # Ottieni target mode dal gruppo
    target_mode = self._group.hvac_mode
    if not target_mode or target_mode == HVACMode.OFF:
        return
    
    # Ripristina direttamente
    for member_id in thermostats_to_restore:
        await self._group.hass.services.async_call(
            "climate", "set_hvac_mode",
            {"entity_id": member_id, "hvac_mode": target_mode},
            blocking=False
        )
```

### Nuovo v0.18.0
```python
async def _handle_window_closed(self, window_id: str) -> None:
    # Verifica altre finestre aperte
    if other_windows_open:
        return
    
    # Ottieni target mode da target_state
    if self.target_state.hvac_mode == HVACMode.OFF:
        return
    
    # Ripristina via call handler (usa target_state automaticamente)
    await self.call_handler.call_immediate(
        entity_ids=thermostats_to_restore
    )
```

**Differenze:**
- ✅ Usa `target_state` invece di `_group.hvac_mode`
- ✅ `call_immediate()` senza data usa automaticamente `target_state`
- ✅ Più pulito e consistente

---

## Legacy Mode

### Fork v0.16.1
```python
async def _execute_action(self, mode: str) -> None:
    self._control_state = mode

    if mode == WINDOW_OPEN:
        if self._group.hvac_mode != HVACMode.OFF:
            await self._group.service_call_handler.call_hvac_off(
                context_id="window_control"
            )
    elif mode == WINDOW_CLOSE:
        await self._group.service_call_handler.call_immediate(
            context_id="window_control"
        )
```

### Nuovo v0.18.0
```python
async def _execute_action(self, mode: str) -> None:
    self._control_state = mode

    if mode == WINDOW_OPEN:
        if self._group.hvac_mode != HVACMode.OFF:
            await self.call_handler.call_immediate(
                {"hvac_mode": HVACMode.OFF}
            )
    elif mode == WINDOW_CLOSE:
        await self.call_handler.call_immediate()
```

**Differenze:**
- ✅ Usa `self.call_handler` (property)
- ✅ Non serve `context_id` (automatico)
- ✅ API più semplice

---

## Riepilogo Vantaggi v0.18.0

| Aspetto | Fork v0.16.1 | Nuovo v0.18.0 |
|---------|--------------|---------------|
| **Chiamate servizi** | Dirette | Via CallHandler |
| **Retry logic** | ❌ No | ✅ Automatico |
| **Context tracking** | ⚠️ Manuale | ✅ Automatico |
| **State management** | ⚠️ Semplice | ✅ Immutabile + metadata |
| **Source awareness** | ❌ No | ✅ Sì (user/schedule/window) |
| **Conflict prevention** | ⚠️ Limitata | ✅ Completa |
| **Testabilità** | ⚠️ Media | ✅ Alta |
| **Manutenibilità** | ⚠️ Media | ✅ Alta |
| **Backward compat** | ✅ Sì | ✅ Sì |

---

## Conclusione

La nuova implementazione v0.18.0:
- ✅ Mantiene tutta la funzionalità area-based
- ✅ Migliora robustezza e affidabilità
- ✅ Integra perfettamente con nuova architettura
- ✅ Preserva backward compatibility
- ✅ Codice più pulito e manutenibile

**Raccomandazione:** Usa la nuova versione v0.18.0 per tutti i nuovi deployment.
