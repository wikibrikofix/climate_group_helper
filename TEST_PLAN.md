# Test Plan - Area-Based Window Control

## Pre-Test Setup

### 1. Backup
```bash
# Backup della configurazione attuale
cp -r /config/custom_components/climate_group_helper \
     /config/custom_components/climate_group_helper.backup
```

### 2. Installazione
```bash
# Copia i nuovi file
cp -r /root/homeassistant/repos/climate_group_helper_source/custom_components/climate_group_helper \
     /config/custom_components/
```

### 3. Configurazione Aree
Verifica che tutte le entità siano assegnate ad aree:
- Settings > Areas > Verifica finestre e termostati
- Se mancano, assegna le aree prima di procedere

### 4. Debug Logging
Aggiungi in `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.climate_group_helper: debug
    custom_components.climate_group_helper.window_control: debug
    custom_components.climate_group_helper.service_call: debug
```

### 5. Riavvio
```bash
# Riavvia Home Assistant
# Settings > System > Restart
```

---

## Test Suite

### Test 1: Verifica Installazione ✓

**Obiettivo:** Verificare che l'integrazione si carichi correttamente

**Steps:**
1. Vai su Settings > Devices & Services > Helpers
2. Trova il tuo Climate Group Helper
3. Click su Configure
4. Naviga fino a Window Control

**Expected:**
- ✅ Nessun errore nei log
- ✅ Opzione "Area-based" disponibile nel dropdown
- ✅ Configurazione esistente preservata

**Log Check:**
```
grep "climate_group_helper" /config/home-assistant.log | grep -i error
# Dovrebbe essere vuoto
```

---

### Test 2: Configurazione Area-Based ✓

**Obiettivo:** Configurare la modalità area-based

**Steps:**
1. Settings > Devices & Services > Helpers > Climate Group Helper
2. Configure > Window Control
3. Seleziona Window Mode: "Area-based"
4. Seleziona Window Sensors: [tutte le finestre da monitorare]
5. Window Open Delay: 15s
6. Close Delay: 30s
7. Save

**Expected:**
- ✅ Configurazione salvata senza errori
- ✅ Campi legacy (room_sensor, zone_sensor) non visibili
- ✅ Campo window_sensors visibile con selector multiplo

**Log Check:**
```
[climate_group_helper] WindowControl initialized. Mode: area_based
```

---

### Test 3: Area Detection ✓

**Obiettivo:** Verificare che le aree vengano rilevate correttamente

**Steps:**
1. Apri una finestra
2. Attendi il delay configurato (15s)
3. Controlla i log

**Expected:**
```
[climate.group_name] Window binary_sensor.window_1 opened in area 'Living Room', turning off: ['climate.thermostat_1']
```

**Se vedi:**
```
[climate.group_name] Cannot determine area for window binary_sensor.window_1
```
→ Assegna l'area alla finestra o al suo device

---

### Test 4: Single Window Open/Close ✓

**Obiettivo:** Test base con una singola finestra

**Setup:**
- Area "Living Room": window_1, thermostat_1
- Area "Bedroom": window_2, thermostat_2

**Test Steps:**
1. Apri window_1
2. Attendi 15s (window_open_delay)
3. Verifica che thermostat_1 si spenga
4. Verifica che thermostat_2 rimanga acceso
5. Chiudi window_1
6. Attendi 30s (close_delay)
7. Verifica che thermostat_1 si riaccenda

**Expected:**
- ✅ Solo thermostat_1 spento quando window_1 aperta
- ✅ thermostat_2 non influenzato
- ✅ thermostat_1 ripristinato quando window_1 chiusa

**Log Check:**
```
# Open
[climate.group_name] Window binary_sensor.window_1 opened, scheduling turn off in 15s
[climate.group_name] Window binary_sensor.window_1 opened in area 'Living Room', turning off: ['climate.thermostat_1']

# Close
[climate.group_name] Window binary_sensor.window_1 closed, scheduling restore check in 30s
[climate.group_name] Window binary_sensor.window_1 closed, restoring area 'Living Room': ['climate.thermostat_1']
```

---

### Test 5: Multiple Windows Same Area ✓

**Obiettivo:** Verificare gestione finestre multiple nella stessa area

**Setup:**
- Area "Living Room": window_1, window_2, thermostat_1

**Test Steps:**
1. Apri window_1 → thermostat_1 si spegne
2. Apri window_2 (mentre window_1 ancora aperta)
3. Chiudi window_1 → thermostat_1 NON si riaccende
4. Chiudi window_2 → thermostat_1 si riaccende

**Expected:**
- ✅ thermostat_1 spento quando prima finestra aperta
- ✅ thermostat_1 NON ripristinato se altre finestre aperte
- ✅ thermostat_1 ripristinato solo quando tutte finestre chiuse

**Log Check:**
```
# window_1 chiusa ma window_2 ancora aperta
[climate.group_name] Window binary_sensor.window_1 closed but other windows still open in area 'Living Room'
```

---

### Test 6: Multiple Windows Different Areas ✓

**Obiettivo:** Verificare indipendenza tra aree diverse

**Setup:**
- Area "Living Room": window_1, thermostat_1
- Area "Bedroom": window_2, thermostat_2

**Test Steps:**
1. Apri window_1 → solo thermostat_1 si spegne
2. Apri window_2 → solo thermostat_2 si spegne
3. Chiudi window_1 → solo thermostat_1 si riaccende
4. Chiudi window_2 → solo thermostat_2 si riaccende

**Expected:**
- ✅ Controllo completamente indipendente per area
- ✅ Nessuna interferenza tra aree

---

### Test 7: Group Target Mode OFF ✓

**Obiettivo:** Verificare che non ripristini se gruppo è OFF

**Test Steps:**
1. Apri window_1 → thermostat_1 si spegne
2. Spegni manualmente il gruppo (set HVAC mode = OFF)
3. Chiudi window_1
4. Attendi close_delay

**Expected:**
- ✅ thermostat_1 NON si riaccende
- ✅ Log: "Target mode is OFF, not restoring"

**Log Check:**
```
[climate.group_name] Target mode is OFF, not restoring
```

---

### Test 8: Entity Without Area ✓

**Obiettivo:** Verificare comportamento con entità senza area

**Test Steps:**
1. Rimuovi l'area da una finestra
2. Apri quella finestra
3. Controlla i log

**Expected:**
- ✅ Log: "Cannot determine area for window X"
- ✅ Nessun termostato spento
- ✅ Nessun errore/crash

---

### Test 9: Legacy Mode Compatibility ✓

**Obiettivo:** Verificare che la modalità legacy funzioni ancora

**Test Steps:**
1. Configure > Window Control
2. Seleziona Window Mode: "On"
3. Configura room_sensor e zone_sensor
4. Save
5. Testa apertura/chiusura

**Expected:**
- ✅ Campi legacy visibili (room_sensor, zone_sensor, delays)
- ✅ Campo window_sensors NON visibile
- ✅ Funzionamento legacy preservato

---

### Test 10: Mode Switching ✓

**Obiettivo:** Verificare pulizia config quando si cambia modalità

**Test Steps:**
1. Configura area-based con window_sensors
2. Cambia a legacy mode (ON)
3. Verifica che window_sensors sia rimosso
4. Cambia a area-based
5. Verifica che room_sensor/zone_sensor siano rimossi

**Expected:**
- ✅ Config pulita automaticamente
- ✅ Nessun campo residuo

---

### Test 11: Integration with Schedule ✓

**Obiettivo:** Verificare compatibilità con Schedule feature

**Test Steps:**
1. Configura uno Schedule
2. Apri finestra → termostato si spegne
3. Schedule cambia temperatura
4. Chiudi finestra → termostato ripristinato con nuova temperatura

**Expected:**
- ✅ Nessun conflitto tra window control e schedule
- ✅ Ripristino usa target_state aggiornato

---

### Test 12: Rapid Open/Close ✓

**Obiettivo:** Test stress con aperture/chiusure rapide

**Test Steps:**
1. Apri finestra
2. Chiudi immediatamente (prima del delay)
3. Apri di nuovo
4. Chiudi di nuovo
5. Ripeti 5 volte

**Expected:**
- ✅ Timer cancellati correttamente
- ✅ Nessun comportamento anomalo
- ✅ Stato finale consistente

---

## Performance Tests

### Test P1: Memory Leak Check
```bash
# Prima del test
ps aux | grep home-assistant | awk '{print $6}'

# Dopo 100 aperture/chiusure
ps aux | grep home-assistant | awk '{print $6}'

# Memoria non dovrebbe crescere significativamente
```

### Test P2: Timer Cleanup
```bash
# Verifica che i timer vengano puliti
# Apri 10 finestre, chiudi tutte
# Controlla che self._timers sia vuoto
```

---

## Rollback Procedure

Se qualcosa va storto:

```bash
# 1. Stop Home Assistant
systemctl stop home-assistant

# 2. Restore backup
rm -rf /config/custom_components/climate_group_helper
cp -r /config/custom_components/climate_group_helper.backup \
     /config/custom_components/climate_group_helper

# 3. Start Home Assistant
systemctl start home-assistant
```

---

## Success Criteria

Il merge è considerato riuscito se:

- ✅ Tutti i test 1-12 passano
- ✅ Nessun errore nei log
- ✅ Performance accettabili (P1, P2)
- ✅ Legacy mode funziona
- ✅ Area-based mode funziona
- ✅ Nessun conflitto con altre feature

---

## Reporting Issues

Se trovi problemi:

1. Raccogli i log:
```bash
grep "climate_group_helper" /config/home-assistant.log > debug.log
```

2. Documenta:
   - Test che fallisce
   - Expected vs Actual behavior
   - Log rilevanti
   - Configurazione (aree, sensori, etc.)

3. Verifica:
   - Aree configurate correttamente
   - Entità esistenti e disponibili
   - Delay configurati correttamente
