# Area-Based Window Control - Documentazione Tecnica Completa

## Indice
1. [Panoramica](#panoramica)
2. [Architettura](#architettura)
3. [Modifiche Implementate](#modifiche-implementate)
4. [Guida al Re-Merge](#guida-al-re-merge)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## Panoramica

### Contesto
Il modulo **Climate Group Helper** per Home Assistant permette di raggruppare più termostati in un'unica entità virtuale. La feature **Area-Based Window Control** estende il window control esistente permettendo il controllo granulare per area: quando una finestra si apre, vengono spenti solo i termostati nella stessa area.

### Versioni
- **Versione Base**: 0.16.1 (con window control legacy room/zone)
- **Fork Custom**: 0.16.1 + Area-Based Window Control
- **Versione Target**: 0.17.0 (redesign architetturale completo)
- **Versione Finale**: 0.17.0 + Area-Based Window Control (questo merge)

### Data Merge
- **Prima implementazione**: 2026-01-24
- **Test completato**: 2026-01-24 19:58
- **Ambiente**: Home Assistant 2026.1.2

---

## Architettura

### Redesign v0.17.0

La versione 0.17.0 ha introdotto un redesign architetturale completo:

#### 1. State Management (state.py)
```python
@dataclass(frozen=True)
class TargetState:
    """Stato immutabile con metadata per tracking."""
    hvac_mode: str | None = None
    temperature: float | None = None
    # ... altri attributi
    
    # Metadata per Optimistic Concurrency Control
    last_source: str | None = None
    last_entity: str | None = None
    last_timestamp: float | None = None
```

**Caratteristiche:**
- Immutabile (thread-safe)
- Source-aware (distingue user/schedule/window)
- Metadata per conflict prevention

#### 2. Service Call Handlers (service_call.py)
```python
class BaseServiceCallHandler(ABC):
    """Base class con debouncing, retry logic, context tracking."""
    CONTEXT_ID: str = "service_call"
    
    async def call_immediate(self, data: dict | None = None) -> None:
        """Esegue chiamata immediata senza debouncing."""
        
    async def call_debounced(self, data: dict | None = None) -> None:
        """Esegue chiamata con debouncing."""
```

**Handler Specializzati:**
- `ClimateCallHandler` - Comandi utente
- `SyncCallHandler` - Sync mode (Lock/Mirror)
- `WindowControlCallHandler` - Window control
- `ScheduleCallHandler` - Schedule automation

#### 3. Window Control (window_control.py)

**Proprietà chiave:**
```python
@property
def state_manager(self):
    """Accesso al state manager (read-only)."""
    return self._group.window_control_state_manager

@property
def call_handler(self):
    """Accesso al call handler specializzato."""
    return self._group.window_control_call_handler

@property
def target_state(self):
    """Stato target corrente."""
    return self.state_manager.target_state
```

---

## Modifiche Implementate

### File Modificati

#### 1. const.py
```python
# Aggiunte costanti area-based
CONF_WINDOW_SENSORS = "window_sensors"
CONF_WINDOW_OPEN_DELAY = "window_open_delay"
DEFAULT_WINDOW_OPEN_DELAY = 15

# Aggiunto nuovo mode
class WindowControlMode(StrEnum):
    OFF = "off"
    ON = "on"
    AREA_BASED = "area_based"  # NUOVO
```

**Rationale:** Separare la configurazione area-based da quella legacy.

---

#### 2. window_control.py

**Struttura Duale:**
```python
class WindowControlHandler:
    def __init__(self, group: ClimateGroup) -> None:
        # Legacy configuration
        self._room_sensor = group.config.get(CONF_ROOM_SENSOR)
        self._zone_sensor = group.config.get(CONF_ZONE_SENSOR)
        
        # Area-based configuration
        self._window_sensors = group.config.get(CONF_WINDOW_SENSORS, [])
        self._window_open_delay = group.config.get(CONF_WINDOW_OPEN_DELAY, 15)
        
        # Area-based state
        self._timers: dict[str, Any] = {}  # window_id -> cancel_func
```

**Setup Dinamico:**
```python
async def async_setup(self) -> None:
    if self._window_control_mode == WindowControlMode.AREA_BASED:
        # Modalità area-based
        self._unsub_listener = async_track_state_change_event(
            self._hass, self._window_sensors, self._area_based_listener
        )
    else:
        # Modalità legacy
        sensors_to_track = [self._room_sensor, self._zone_sensor]
        self._unsub_listener = async_track_state_change_event(
            self._hass, sensors_to_track, self._state_change_listener
        )
```

**Logica Area-Based:**

1. **Listener Eventi:**
```python
@callback
def _area_based_listener(self, event: Event[EventStateChangedData]) -> None:
    """Gestisce cambio stato finestra."""
    window_id = event.data.get("entity_id")
    is_open = new_state.state in (STATE_ON, STATE_OPEN)
    
    # Cancella timer esistente
    if window_id in self._timers:
        self._timers[window_id]()
        del self._timers[window_id]
    
    if is_open:
        # Schedula spegnimento
        self._timers[window_id] = async_call_later(
            self._hass, self._window_open_delay,
            lambda _: self._hass.async_create_task(
                self._handle_window_opened(window_id)
            )
        )
    else:
        # Schedula ripristino
        self._timers[window_id] = async_call_later(
            self._hass, self._close_delay,
            lambda _: self._hass.async_create_task(
                self._handle_window_closed(window_id)
            )
        )
```

2. **Gestione Apertura:**
```python
async def _handle_window_opened(self, window_id: str) -> None:
    # Verifica stato ancora aperto
    state = self._hass.states.get(window_id)
    if not state or state.state not in (STATE_ON, STATE_OPEN):
        return
    
    # Identifica area
    window_area = self._get_entity_area(window_id)
    if not window_area:
        _LOGGER.warning("Cannot determine area for window %s", window_id)
        return
    
    # Trova termostati attivi nell'area
    thermostats = self._get_thermostats_in_area(window_area, only_active=True)
    
    # Spegni via call handler (CHIAVE: usa entity_ids)
    await self.call_handler.call_immediate(
        {"hvac_mode": HVACMode.OFF}, 
        entity_ids=thermostats
    )
```

3. **Gestione Chiusura:**
```python
async def _handle_window_closed(self, window_id: str) -> None:
    # Verifica altre finestre aperte nella stessa area
    for other_window_id in self._window_sensors:
        if other_window_id == window_id:
            continue
        if self._get_entity_area(other_window_id) == window_area:
            state = self._hass.states.get(other_window_id)
            if state and state.state in (STATE_ON, STATE_OPEN):
                _LOGGER.debug("Other windows still open in area")
                return
    
    # Trova termostati OFF da ripristinare
    thermostats = [
        m for m in self._get_thermostats_in_area(window_area)
        if self._hass.states.get(m).state == HVACMode.OFF
    ]
    
    # Verifica target state
    if self.target_state.hvac_mode == HVACMode.OFF:
        return
    
    # Ripristina via call handler (usa target_state automaticamente)
    await self.call_handler.call_immediate(entity_ids=thermostats)
```

4. **Rilevamento Area:**
```python
def _get_entity_area(self, entity_id: str) -> str | None:
    """Ottiene area da entity o device registry."""
    ent_reg = er.async_get(self._hass)
    entity_entry = ent_reg.async_get(entity_id)
    
    if not entity_entry:
        return None
    
    # Prova area entità
    if entity_entry.area_id:
        return entity_entry.area_id
    
    # Fallback: area device
    if entity_entry.device_id:
        dev_reg = dr.async_get(self._hass)
        device_entry = dev_reg.async_get(entity_entry.device_id)
        if device_entry and device_entry.area_id:
            return device_entry.area_id
    
    return None
```

**Differenze Chiave vs Fork v0.16.1:**

| Aspetto | Fork v0.16.1 | Merge v0.17.0 |
|---------|--------------|---------------|
| Chiamate servizi | `hass.services.async_call()` diretto | `call_handler.call_immediate()` |
| Accesso stato | `self._group.hvac_mode` | `self.target_state.hvac_mode` |
| Accesso hass | `self._group.hass` | `self._hass` |
| Targeting | Loop manuale su membri | `entity_ids` parameter |
| Context tracking | Nessuno | Automatico via `CONTEXT_ID` |

---

#### 3. service_call.py

**Modifica WindowControlCallHandler:**
```python
class WindowControlCallHandler(BaseServiceCallHandler):
    """Handler per window control con supporto entity_ids."""
    
    CONTEXT_ID = "window_control"
    
    def __init__(self, group: ClimateGroup):
        super().__init__(group)
        self._target_entity_ids: list[str] | None = None
    
    async def call_immediate(
        self, 
        data: dict[str, Any] | None = None, 
        entity_ids: list[str] | None = None  # NUOVO PARAMETRO
    ) -> None:
        """Esegue chiamata con targeting opzionale."""
        self._target_entity_ids = entity_ids
        try:
            await self._execute_calls(data)
        finally:
            self._target_entity_ids = None
    
    def _get_call_entity_ids(self, attr: str) -> list[str]:
        """Override per usare entity_ids se specificato."""
        if self._target_entity_ids is not None:
            return self._target_entity_ids
        return self._group.climate_entity_ids
```

**Rationale:** Permette al window control di targetizzare specifici termostati invece di tutto il gruppo.

---

#### 4. config_flow.py

**UI Dinamica:**
```python
async def async_step_window_control(self, user_input: dict | None = None) -> ConfigFlowResult:
    if user_input is not None:
        window_mode = user_input.get(CONF_WINDOW_MODE)
        
        if window_mode == WindowControlMode.AREA_BASED:
            # Rimuovi config legacy
            for key in [CONF_ROOM_SENSOR, CONF_ZONE_SENSOR, ...]:
                current_config.pop(key, None)
        else:
            # Rimuovi config area-based
            for key in [CONF_WINDOW_SENSORS, CONF_WINDOW_OPEN_DELAY]:
                current_config.pop(key, None)
    
    # Schema dinamico basato su mode
    window_mode = current_config.get(CONF_WINDOW_MODE, WindowControlMode.OFF)
    schema_dict = {...}
    
    if window_mode == WindowControlMode.AREA_BASED:
        schema_dict[vol.Optional(CONF_WINDOW_SENSORS)] = selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="binary_sensor",
                multiple=True,  # CHIAVE: selector multiplo
            )
        )
    elif window_mode == WindowControlMode.ON:
        # Campi legacy
        schema_dict[vol.Optional(CONF_ROOM_SENSOR)] = ...
```

**Rationale:** Mostra solo i campi rilevanti per la modalità selezionata, evitando confusione.

---

#### 5. strings.json

**Traduzioni Aggiunte:**
```json
{
  "config": {
    "step": {
      "window_control": {
        "data": {
          "window_sensors": "Window Sensors (Area-based)",
          "window_open_delay": "Window Open Delay (seconds)"
        },
        "data_description": {
          "window_sensors": "Select all window sensors to monitor. When a window opens, only climate devices in the same area will be turned off.",
          "window_open_delay": "Time to wait before turning off heating after a window opens."
        }
      }
    }
  },
  "selector": {
    "window_mode": {
      "options": {
        "area_based": "Area-based – Automatic zone detection"
      }
    }
  }
}
```

---

## Guida al Re-Merge

### Quando Serve un Re-Merge

Un re-merge è necessario quando:
1. Lo sviluppatore upstream rilascia una nuova versione (es. 0.18.0)
2. Ci sono bugfix critici da integrare
3. Nuove feature upstream che vogliamo mantenere

### Processo di Re-Merge

#### Step 1: Analisi Differenze

```bash
# Scarica nuova versione upstream
cd /root/homeassistant/repos
git clone https://github.com/bjrnptrsn/climate_group_helper climate_group_helper_new

# Confronta file chiave
diff -u climate_group_helper_source/custom_components/climate_group_helper/window_control.py \
        climate_group_helper_new/custom_components/climate_group_helper/window_control.py

diff -u climate_group_helper_source/custom_components/climate_group_helper/service_call.py \
        climate_group_helper_new/custom_components/climate_group_helper/service_call.py
```

#### Step 2: Identificare Modifiche Critiche

Cerca modifiche in:
1. **Architettura base** (state.py, climate.py, __init__.py)
2. **Handler system** (service_call.py)
3. **Window control** (window_control.py)

**Domande chiave:**
- La struttura di `WindowControlHandler` è cambiata?
- `WindowControlCallHandler` esiste ancora?
- Il metodo `call_immediate()` ha la stessa firma?
- Le proprietà `state_manager`, `call_handler`, `target_state` esistono ancora?

#### Step 3: Strategia di Merge

**Scenario A: Modifiche Minori (bugfix, ottimizzazioni)**
```bash
# Copia nuova versione base
cp climate_group_helper_new/custom_components/climate_group_helper/*.py \
   climate_group_helper_source/custom_components/climate_group_helper/

# Riapplica modifiche custom
# 1. const.py - aggiungi costanti area-based
# 2. window_control.py - integra logica area-based
# 3. service_call.py - modifica WindowControlCallHandler
# 4. config_flow.py - UI dinamica
# 5. strings.json - traduzioni
```

**Scenario B: Redesign Architetturale**
```bash
# Analisi approfondita necessaria
# 1. Studia nuova architettura
# 2. Identifica equivalenti delle nostre modifiche
# 3. Riadatta logica area-based alla nuova struttura
# 4. Test estensivi
```

#### Step 4: Checklist Modifiche

**const.py:**
```python
# [ ] CONF_WINDOW_SENSORS aggiunto
# [ ] CONF_WINDOW_OPEN_DELAY aggiunto
# [ ] DEFAULT_WINDOW_OPEN_DELAY = 15
# [ ] WindowControlMode.AREA_BASED aggiunto
```

**window_control.py:**
```python
# [ ] Proprietà state_manager, call_handler, target_state presenti
# [ ] __init__ include configurazione area-based
# [ ] async_setup gestisce AREA_BASED mode
# [ ] _area_based_listener implementato
# [ ] _handle_window_opened usa call_handler.call_immediate(entity_ids=...)
# [ ] _handle_window_closed verifica altre finestre aperte
# [ ] _get_entity_area implementato
# [ ] _get_thermostats_in_area implementato
# [ ] Modalità legacy preservata
```

**service_call.py:**
```python
# [ ] WindowControlCallHandler esiste
# [ ] call_immediate accetta entity_ids opzionale
# [ ] _target_entity_ids gestito correttamente
# [ ] _get_call_entity_ids override presente
```

**config_flow.py:**
```python
# [ ] Import CONF_WINDOW_SENSORS, CONF_WINDOW_OPEN_DELAY
# [ ] async_step_window_control ha logica dinamica
# [ ] Schema mostra campi corretti per mode
# [ ] Cleanup config quando si cambia mode
```

**strings.json:**
```python
# [ ] window_sensors tradotto
# [ ] window_open_delay tradotto
# [ ] area_based option aggiunta
```

#### Step 5: Testing

```bash
# Copia file
cp -r climate_group_helper_source/custom_components/climate_group_helper \
      /root/homeassistant/custom_components/

# Riavvia
ha core restart

# Verifica log
ha core logs | grep -i "WindowControl initialized"
ha core logs | grep -i "Area-based window control"

# Test funzionale
# 1. Apri finestra → termostato area si spegne
# 2. Chiudi finestra → termostato area si riaccende
# 3. Apri 2 finestre stessa area → termostato si spegne
# 4. Chiudi 1 finestra → termostato resta spento
# 5. Chiudi 2a finestra → termostato si riaccende
```

---

## Testing

### Test Suite Completo

#### Test 1: Single Window Open/Close
```
Setup: Area "Studio" con finestra_studio e termostato_studio

1. Apri finestra_studio
   Expected: Dopo 15s, termostato_studio OFF
   Log: "Window ... opened in area 'studio', turning off: ['climate.termostato_studio']"

2. Chiudi finestra_studio
   Expected: Dopo 30s, termostato_studio ripristinato
   Log: "Window ... closed, restoring area 'studio': ['climate.termostato_studio']"
```

#### Test 2: Multiple Windows Same Area
```
Setup: Area "Living" con finestra_1, finestra_2, termostato_living

1. Apri finestra_1 → termostato_living OFF
2. Apri finestra_2 (finestra_1 ancora aperta)
3. Chiudi finestra_1
   Expected: termostato_living resta OFF
   Log: "Other windows still open in area 'living'"
4. Chiudi finestra_2
   Expected: termostato_living ripristinato
```

#### Test 3: Multiple Windows Different Areas
```
Setup: 
- Area "Studio": finestra_studio, termostato_studio
- Area "Camera": finestra_camera, termostato_camera

1. Apri finestra_studio → solo termostato_studio OFF
2. Apri finestra_camera → solo termostato_camera OFF
3. Chiudi finestra_studio → solo termostato_studio ripristinato
4. Chiudi finestra_camera → solo termostato_camera ripristinato

Expected: Controllo completamente indipendente per area
```

#### Test 4: Entity Without Area
```
1. Rimuovi area da una finestra
2. Apri quella finestra
   Expected: Log "Cannot determine area for window X"
   Expected: Nessun termostato spento
   Expected: Nessun crash
```

#### Test 5: Group Target Mode OFF
```
1. Apri finestra → termostato si spegne
2. Spegni manualmente il gruppo (HVAC mode = OFF)
3. Chiudi finestra
   Expected: Termostato NON si riaccende
   Log: "Target mode is OFF, not restoring"
```

### Log Patterns da Verificare

**Inizializzazione:**
```
INFO [homeassistant.components.sensor] Setting up climate_group_helper.sensor
DEBUG [custom_components.climate_group_helper.window_control] [climate.globale] WindowControl initialized. Mode: area_based
```

**Apertura Finestra:**
```
DEBUG [custom_components.climate_group_helper.window_control] [climate.globale] Window binary_sensor.finestra_X_contact opened, scheduling turn off in 15.0s
INFO [custom_components.climate_group_helper.window_control] [climate.globale] Window binary_sensor.finestra_X_contact opened in area 'Y', turning off: ['climate.termostato_Y']
```

**Chiusura Finestra:**
```
DEBUG [custom_components.climate_group_helper.window_control] [climate.globale] Window binary_sensor.finestra_X_contact closed, scheduling restore check in 30.0s
INFO [custom_components.climate_group_helper.window_control] [climate.globale] Window binary_sensor.finestra_X_contact closed, restoring area 'Y': ['climate.termostato_Y']
```

**Errori da NON vedere:**
```
ERROR [custom_components.climate_group_helper]
Cannot determine area for window (se aree configurate)
```

---

## Troubleshooting

### Problema: Climate Group Non Si Carica

**Sintomi:**
```bash
ha core logs | grep climate_group_helper
# Output vuoto
```

**Cause Possibili:**
1. File non copiati correttamente
2. Errori di sintassi Python
3. Dipendenze mancanti

**Soluzione:**
```bash
# Verifica file
ls -lh /root/homeassistant/custom_components/climate_group_helper/*.py

# Verifica sintassi
python3 -m py_compile /root/homeassistant/custom_components/climate_group_helper/*.py

# Cerca errori
ha core logs | grep -i error | grep climate

# Riavvia
ha core restart
```

---

### Problema: WindowControl Non Inizializza

**Sintomi:**
```bash
ha core logs | grep "WindowControl initialized"
# Output vuoto
```

**Cause:**
1. Window control disabilitato (mode = OFF)
2. Nessun sensore configurato
3. Climate group non configurato

**Soluzione:**
```bash
# Verifica configurazione
# Settings > Devices & Services > Helpers > Climate Group Helper > Configure > Window Control
# - Window Mode deve essere "Area-based"
# - Window Sensors deve avere almeno un sensore
```

---

### Problema: Finestra Aperta Ma Termostato Non Si Spegne

**Sintomi:**
```bash
# Apri finestra ma nessun log
ha core logs | grep "finestra_X"
# Output vuoto
```

**Diagnosi:**
```bash
# 1. Verifica sensore funziona
# Controlla in Home Assistant se binary_sensor.finestra_X cambia stato

# 2. Verifica area configurata
ha core logs | grep "Cannot determine area"

# 3. Verifica termostato nell'area
ha core logs | grep "No active thermostats"
```

**Soluzioni:**
1. **Sensore non cambia stato**: Problema hardware/zigbee
2. **Area non trovata**: Assegna area a finestra o device in Settings > Areas
3. **Nessun termostato**: Assegna termostato alla stessa area della finestra

---

### Problema: Termostato Non Si Riaccende

**Sintomi:**
```bash
# Chiudi finestra ma termostato resta OFF
```

**Diagnosi:**
```bash
# Cerca log
ha core logs | grep "finestra_X.*closed"

# Verifica altre finestre
ha core logs | grep "Other windows still open"

# Verifica target mode
ha core logs | grep "Target mode is OFF"
```

**Soluzioni:**
1. **Altre finestre aperte**: Normale, chiudi tutte le finestre dell'area
2. **Target mode OFF**: Riaccendi manualmente il gruppo
3. **Nessun log**: Verifica che close_delay sia passato (default 30s)

---

### Problema: Tutti i Termostati Si Spengono (Non Solo Area)

**Sintomi:**
```bash
# Log mostra tutti i termostati invece di uno solo
INFO [...] turning off: ['climate.termo1', 'climate.termo2', 'climate.termo3']
```

**Causa:**
Modalità legacy attiva invece di area-based

**Soluzione:**
```bash
# Verifica mode
ha core logs | grep "WindowControl initialized"
# Deve dire "Mode: area_based"

# Se dice "Mode: on", riconfigura:
# Settings > Devices & Services > Helpers > Climate Group Helper > Configure
# Window Control > Window Mode > Seleziona "Area-based"
```

---

## Appendice: File Structure

```
/root/homeassistant/
├── custom_components/
│   └── climate_group_helper/
│       ├── __init__.py                    (v0.17.0 base)
│       ├── climate.py                     (v0.17.0 base)
│       ├── const.py                       (MODIFICATO - area-based)
│       ├── window_control.py              (MODIFICATO - area-based)
│       ├── service_call.py                (MODIFICATO - entity_ids)
│       ├── config_flow.py                 (MODIFICATO - UI dinamica)
│       ├── strings.json                   (MODIFICATO - traduzioni)
│       ├── state.py                       (v0.17.0 base)
│       ├── sync_mode.py                   (v0.17.0 base)
│       ├── schedule.py                    (v0.17.0 base)
│       ├── sensor.py                      (v0.17.0 base)
│       ├── manifest.json                  (v0.17.0)
│       └── AREA_BASED_WINDOW_CONTROL.md   (Documentazione)
│
└── repos/
    ├── climate_group_helper_1.61.1/       (Versione originale)
    ├── climate_group_helper_fork/         (Fork v0.16.1 + area-based)
    └── climate_group_helper_source/       (v0.17.0 + area-based - MASTER)
        └── custom_components/
            └── climate_group_helper/
                └── [file modificati]
```

---

## Appendice: Comandi Utili

### Backup e Restore
```bash
# Backup
cp -r /root/homeassistant/custom_components/climate_group_helper \
      /root/climate_group_helper.backup.$(date +%Y%m%d)

# Restore
rm -rf /root/homeassistant/custom_components/climate_group_helper
cp -r /root/climate_group_helper.backup.YYYYMMDD \
      /root/homeassistant/custom_components/climate_group_helper
ha core restart
```

### Monitoring
```bash
# Log in tempo reale
ha core logs --follow | grep climate_group_helper

# Log finestra specifica
ha core logs | grep "finestra_studio"

# Log area-based
ha core logs | grep "area\|turning off\|restoring"

# Errori
ha core logs | grep -i error | grep climate
```

### Debug
```bash
# Abilita debug in configuration.yaml
logger:
  default: info
  logs:
    custom_components.climate_group_helper: debug
    custom_components.climate_group_helper.window_control: debug

# Riavvia
ha core restart

# Verifica debug attivo
ha core logs | grep DEBUG | grep climate_group_helper
```

---

## Changelog

### 2026-01-24 - v0.17.0 + Area-Based
- ✅ Merge completato su architettura v0.17.0
- ✅ Area-based window control integrato
- ✅ Backward compatibility con modalità legacy
- ✅ Test completati con successo
- ✅ Documentazione completa creata

---

## Contatti e Riferimenti

- **Repository Upstream**: https://github.com/bjrnptrsn/climate_group_helper
- **Versione Base**: 0.17.0
- **Custom Feature**: Area-Based Window Control
- **Ambiente**: Home Assistant 2026.1.2
- **Data Implementazione**: 2026-01-24
