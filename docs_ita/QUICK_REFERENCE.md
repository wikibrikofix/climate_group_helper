# Quick Reference - Area-Based Window Control

## 🎯 Cosa Fa Questa Modifica

Aggiunge controllo granulare per area: quando una finestra si apre, vengono spenti **solo i termostati nella stessa area**, non tutto il gruppo.

## 📁 File Modificati (5)

### 1. const.py
```python
# Aggiunte 3 costanti + 1 enum value
CONF_WINDOW_SENSORS = "window_sensors"
CONF_WINDOW_OPEN_DELAY = "window_open_delay"
DEFAULT_WINDOW_OPEN_DELAY = 15
WindowControlMode.AREA_BASED = "area_based"
```

### 2. window_control.py (CORE)
```python
# Metodi area-based aggiunti:
_area_based_listener()          # Gestisce eventi finestre
_handle_window_opened()         # Spegne termostati area
_handle_window_closed()         # Ripristina termostati area
_get_entity_area()              # Rileva area da registry
_get_thermostats_in_area()      # Trova termostati per area

# Integrazione v0.18.0:
self.call_handler.call_immediate(entity_ids=[...])  # Invece di hass.services
self.target_state.hvac_mode                         # Invece di _group.hvac_mode
```

### 3. service_call.py
```python
# WindowControlCallHandler modificato:
async def call_immediate(data=None, entity_ids=None):  # entity_ids NUOVO
    self._target_entity_ids = entity_ids
    # ...

def _get_call_entity_ids(attr):
    if self._target_entity_ids is not None:
        return self._target_entity_ids  # Usa lista custom
    return self._group.climate_entity_ids  # Default: tutti
```

### 4. config_flow.py
```python
# UI dinamica basata su window_mode:
if window_mode == WindowControlMode.AREA_BASED:
    # Mostra: window_sensors (multiple), window_open_delay
else:
    # Mostra: room_sensor, zone_sensor, room_delay, zone_delay
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

## 🔄 Come Riapplicare su Nuova Versione

### Step 1: Prepara Ambiente
```bash
cd /root/homeassistant/repos
# Scarica nuova versione
git clone https://github.com/bjrnptrsn/climate_group_helper climate_group_helper_vX.X.X
```

### Step 2: Verifica Compatibilità
```bash
# Controlla se questi metodi esistono ancora:
grep "class WindowControlCallHandler" climate_group_helper_vX.X.X/.../service_call.py
grep "def call_immediate" climate_group_helper_vX.X.X/.../service_call.py
grep "@property" climate_group_helper_vX.X.X/.../window_control.py | grep -E "state_manager|call_handler"

# Se esistono → Merge semplice
# Se non esistono → Analisi approfondita necessaria
```

### Step 3: Applica Modifiche

**const.py:**
```bash
# Aggiungi dopo le altre costanti window:
CONF_WINDOW_SENSORS = "window_sensors"
CONF_WINDOW_OPEN_DELAY = "window_open_delay"
DEFAULT_WINDOW_OPEN_DELAY = 15

# In WindowControlMode enum:
AREA_BASED = "area_based"
```

**service_call.py:**
```bash
# In WindowControlCallHandler, modifica call_immediate:
# PRIMA:
async def call_immediate(self, data: dict | None = None):

# DOPO:
async def call_immediate(self, data: dict | None = None, entity_ids: list[str] | None = None):
    self._target_entity_ids = entity_ids
    try:
        await self._execute_calls(data)
    finally:
        self._target_entity_ids = None

# Aggiungi override:
def _get_call_entity_ids(self, attr: str) -> list[str]:
    if self._target_entity_ids is not None:
        return self._target_entity_ids
    return self._group.climate_entity_ids
```

**window_control.py:**
```bash
# Copia INTERA implementazione da:
/root/homeassistant/repos/climate_group_helper_source/custom_components/climate_group_helper/window_control.py

# Verifica che usi:
# - self._hass (non self._group.hass)
# - self.call_handler.call_immediate()
# - self.target_state
```

**config_flow.py:**
```bash
# In async_step_window_control, sostituisci schema statico con dinamico
# Vedi: climate_group_helper_source/.../config_flow.py linee 471-600
```

**strings.json:**
```bash
# Aggiungi traduzioni come in:
# climate_group_helper_source/.../strings.json
```

### Step 4: Test
```bash
# Copia file
cp -r climate_group_helper_vX.X.X/custom_components/climate_group_helper \
      /root/homeassistant/custom_components/

# Riavvia
ha core restart

# Verifica
ha core logs | grep "WindowControl initialized"
# Deve dire: "Mode: area_based"

# Test funzionale
# 1. Apri finestra → solo termostato area si spegne
# 2. Chiudi finestra → solo termostato area si riaccende
```

---

## 🐛 Troubleshooting Rapido

### Climate Group Non Si Carica
```bash
ha core logs | grep -i error | grep climate
python3 -m py_compile /root/homeassistant/custom_components/climate_group_helper/*.py
```

### WindowControl Non Inizializza
```bash
# Verifica configurazione:
# Settings > Helpers > Climate Group > Configure > Window Control
# - Mode deve essere "Area-based"
# - Window Sensors deve avere almeno 1 sensore
```

### Finestra Aperta Ma Niente Succede
```bash
# 1. Verifica sensore cambia stato in Home Assistant
# 2. Verifica area configurata:
ha core logs | grep "Cannot determine area"
# 3. Verifica termostato nell'area:
ha core logs | grep "No active thermostats"
```

### Termostato Non Si Riaccende
```bash
# Verifica altre finestre aperte:
ha core logs | grep "Other windows still open"
# Verifica target mode:
ha core logs | grep "Target mode is OFF"
```

---

## 📊 Log Patterns

### ✅ Funzionamento Corretto
```
DEBUG [...] WindowControl initialized. Mode: area_based
DEBUG [...] Window binary_sensor.finestra_X opened, scheduling turn off in 15.0s
INFO  [...] Window binary_sensor.finestra_X opened in area 'Y', turning off: ['climate.termo_Y']
DEBUG [...] Window binary_sensor.finestra_X closed, scheduling restore check in 30.0s
INFO  [...] Window binary_sensor.finestra_X closed, restoring area 'Y': ['climate.termo_Y']
```

### ❌ Problemi
```
ERROR [...] Cannot determine area for window X          → Assegna area
DEBUG [...] No active thermostats in area 'Y'          → Normale se tutti OFF
DEBUG [...] Other windows still open in area 'Y'       → Normale, chiudi altre
DEBUG [...] Target mode is OFF, not restoring          → Normale se gruppo OFF
```

---

## 🔑 Punti Chiave da Ricordare

1. **Usa call_handler, non hass.services**
   ```python
   # ❌ SBAGLIATO (v0.16.1)
   await self._group.hass.services.async_call(...)
   
   # ✅ CORRETTO (v0.18.0)
   await self.call_handler.call_immediate(entity_ids=[...])
   ```

2. **Usa target_state, non _group.hvac_mode**
   ```python
   # ❌ SBAGLIATO
   if self._group.hvac_mode == HVACMode.OFF:
   
   # ✅ CORRETTO
   if self.target_state.hvac_mode == HVACMode.OFF:
   ```

3. **Usa self._hass, non self._group.hass**
   ```python
   # ❌ SBAGLIATO
   state = self._group.hass.states.get(entity_id)
   
   # ✅ CORRETTO
   state = self._hass.states.get(entity_id)
   ```

4. **entity_ids è opzionale in call_immediate**
   ```python
   # Tutti i membri
   await self.call_handler.call_immediate({"hvac_mode": HVACMode.OFF})
   
   # Solo alcuni membri
   await self.call_handler.call_immediate(
       {"hvac_mode": HVACMode.OFF}, 
       entity_ids=["climate.termo1", "climate.termo2"]
   )
   ```

5. **Verifica altre finestre prima di ripristinare**
   ```python
   # Controlla se altre finestre nell'area sono aperte
   for other_window in self._window_sensors:
       if self._get_entity_area(other_window) == window_area:
           if is_open(other_window):
               return  # Non ripristinare ancora
   ```

---

## 📚 Documentazione Completa

Vedi: `/root/homeassistant/repos/climate_group_helper_source/TECHNICAL_DOCUMENTATION.md`

---

## 📝 Checklist Merge

- [ ] const.py: 3 costanti + 1 enum
- [ ] service_call.py: entity_ids parameter + override
- [ ] window_control.py: 5 metodi area-based + integrazione v0.18.0
- [ ] config_flow.py: UI dinamica
- [ ] strings.json: 3 traduzioni
- [ ] Test: apri/chiudi finestra
- [ ] Log: "Mode: area_based"
- [ ] Funzionale: solo termostato area controllato

---

**Ultima Modifica**: 2026-02-01  
**Versione**: 0.18.0 + Area-Based Window Control  
**Status**: ✅ Testato e Funzionante
