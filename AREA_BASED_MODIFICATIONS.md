# Area-Based Window Control - Modifiche Completate

## Data
2026-03-10

## Descrizione
Portate con successo le modifiche per la feature "Area-Based Window Control" dalla versione fork (climate_group_helper) alla versione ufficiale aggiornata (climate_group_helper_orig).

## File Modificati

### 1. const.py
✅ Aggiunte costanti:
- `CONF_WINDOW_SENSORS = "window_sensors"`
- `CONF_WINDOW_OPEN_DELAY = "window_open_delay"`
- `DEFAULT_WINDOW_OPEN_DELAY = 15`
- `WindowControlMode.AREA_BASED = "area_based"`

### 2. service_call.py
✅ Modificato `WindowControlCallHandler`:
- Aggiunta variabile `_target_entity_ids`
- Aggiunto metodo `call_immediate(data, entity_ids)`
- Override `_get_call_entity_ids()` per supporto entity_ids mirati

### 3. window_control.py
✅ Aggiunte funzionalità area-based:
- Header documentazione modifiche custom
- Import registry (entity_registry, device_registry)
- Variabili configurazione area-based
- Modificato `async_setup()` per gestire mode AREA_BASED
- 5 nuovi metodi:
  - `_area_based_listener()` - gestisce eventi sensori
  - `_handle_window_opened()` - gestisce apertura finestra
  - `_handle_window_closed()` - gestisce chiusura finestra
  - `_get_thermostats_in_area()` - trova termostati per area
  - `_get_entity_area()` - determina area entità

### 4. config_flow.py
✅ UI dinamica e cleanup automatico:
- Import nuove costanti
- Modificato `_normalize_options()` per cleanup basato su mode
- Riscritto `_section_factory_window_control()` per UI dinamica
  - Mostra campi area-based solo se mode = AREA_BASED
  - Mostra campi legacy solo se mode = ON

### 5. strings.json (inglese)
✅ Aggiunte traduzioni:
- `window_sensors`: "Window Sensors (Area-based)"
- `window_open_delay`: "Window Open Delay (seconds)"
- Descrizioni per i nuovi campi
- Opzione `area_based` nel selector window_mode

### 6. translations/it.json (italiano)
✅ Aggiunte traduzioni italiane:
- `window_sensors`: "Sensori Finestre (Area-based)"
- `window_open_delay`: "Ritardo Apertura Finestra (s)"
- Descrizioni complete in italiano
- Opzione `area_based`: "Basato su aree – Rilevamento automatico zone"

## Statistiche
- **File modificati:** 6
- **Linee di codice aggiunte:** ~300
- **Nuovi metodi:** 5
- **Nuove costanti:** 4
- **Lingue tradotte:** 2 (inglese, italiano)

## Funzionalità Area-Based

### Come Funziona
1. L'utente seleziona più sensori finestra da monitorare
2. Quando una finestra si apre:
   - Il sistema identifica l'area della finestra tramite registry
   - Trova tutti i termostati nella stessa area
   - Spegne solo quei termostati dopo il delay configurato
3. Quando la finestra si chiude:
   - Verifica che tutte le finestre dell'area siano chiuse
   - Ripristina i termostati dell'area allo stato target

### Vantaggi
- ✅ Controllo granulare per area
- ✅ Gestione multi-finestra simultanea
- ✅ Rilevamento automatico aree via registry
- ✅ Nessuna configurazione manuale zone richiesta

## Compatibilità
- ✅ Backward compatible con mode legacy (room/zone sensors)
- ✅ Cleanup automatico configurazione quando si cambia mode
- ✅ Integrato con architettura esistente (call_handler, target_state)
- ✅ Compatibile con tutte le altre feature (Schedule, Sync Mode, etc.)

## Configurazione

### Requisiti
- Finestre e termostati devono essere assegnati ad aree in Home Assistant
- Finestra e termostato devono essere nella stessa area per essere associati

### Setup
1. Vai su **Impostazioni** > **Dispositivi e Servizi** > **Helper**
2. Trova il tuo Climate Group Helper
3. Clicca **Configura** > **Window Control**
4. Seleziona **Window Mode**: `area_based`
5. Seleziona tutte le finestre da monitorare in **Window Sensors**
6. Configura **Window Open Delay** (default: 15s)
7. Configura **Close Delay** (default: 30s)

## Debug
Abilita debug logging per vedere le decisioni di controllo:

```yaml
logger:
  default: info
  logs:
    custom_components.climate_group_helper: debug
```

Messaggi log da cercare:
- `Window X opened in area 'Y', turning off: [entities]`
- `Window X closed, restoring area 'Y': [entities]`
- `Cannot determine area for window X` (indica mancanza assegnazione area)

## Test Consigliati
Prima dell'uso in produzione, testare:
1. ✅ Apertura/chiusura singola finestra
2. ✅ Apertura multipla finestre stessa area
3. ✅ Apertura finestre in aree diverse
4. ✅ Cambio mode da legacy ad area-based e viceversa
5. ✅ Entità senza area assegnata (devono essere ignorate)

## Note Importanti
- Se un'entità non ha area assegnata, viene ignorata dal controllo area-based
- Se `window_mode = area_based` ma nessun sensore configurato, il controllo è disabilitato
- Lo stato target del gruppo non viene mai modificato - solo gli stati dei membri
- Il ripristino avviene solo se il mode target del gruppo non è OFF

## Prossimi Passi
1. Testare le modifiche in ambiente di sviluppo
2. Verificare che tutte le feature esistenti funzionino correttamente
3. Testare il cambio dinamico tra i vari mode
4. Verificare i log per eventuali errori
5. Testare con configurazioni reali (finestre e termostati in aree)

---

**Versione Base:** Latest official version
**Versione Finale:** Latest + Area-Based Window Control
**Status:** ✅ Modifiche completate e pronte per test
