# Climate Group Helper - Area-Based Window Control

## 📋 Panoramica

Questo repository contiene la versione modificata del modulo **Climate Group Helper** per Home Assistant con l'aggiunta della feature **Area-Based Window Control**.

### Cosa Fa

Permette il controllo granulare dei termostati basato sulle aree: quando una finestra si apre, vengono spenti **solo i termostati nella stessa area**, non tutto il gruppo.

### Versione

- **Base**: Climate Group Helper v0.17.0
- **Modifica**: Area-Based Window Control
- **Data**: 2026-01-24
- **Status**: ✅ Testato e Funzionante

---

## 📚 Documentazione

### Per Iniziare

1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** ⭐ **INIZIA QUI**
   - Guida rapida per capire le modifiche
   - Checklist per riapplicare su nuove versioni
   - Troubleshooting rapido
   - Log patterns da verificare

### Documentazione Tecnica

2. **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)**
   - Architettura completa v0.17.0
   - Spiegazione dettagliata di ogni modifica
   - Guida al re-merge passo-passo
   - Test suite completo
   - Troubleshooting approfondito

3. **[MODIFICATIONS_DIFF.md](MODIFICATIONS_DIFF.md)**
   - Diff esatti di tutte le modifiche
   - Confronto linea per linea
   - Codice completo dei nuovi metodi
   - Riepilogo modifiche per file

### Documentazione Utente

4. **[AREA_BASED_WINDOW_CONTROL.md](custom_components/climate_group_helper/AREA_BASED_WINDOW_CONTROL.md)**
   - Guida utente per configurazione
   - Esempi d'uso
   - Requisiti e setup
   - Debugging

### Documentazione Merge

5. **[README_MERGE.md](README_MERGE.md)**
   - Istruzioni installazione
   - Verifica funzionamento
   - Prossimi passi

6. **[MERGE_SUMMARY.md](MERGE_SUMMARY.md)**
   - Riepilogo tecnico del merge
   - Dettagli modifiche per file
   - Testing checklist

7. **[COMPARISON.md](COMPARISON.md)**
   - Confronto fork v0.16.1 vs v0.17.0
   - Differenze architetturali
   - Vantaggi nuova implementazione

8. **[TEST_PLAN.md](TEST_PLAN.md)**
   - Piano di test completo (12 test case)
   - Procedure di rollback
   - Success criteria

---

## 🚀 Quick Start

### Installazione

```bash
# Backup
cp -r /root/homeassistant/custom_components/climate_group_helper \
      /root/climate_group_helper.backup

# Installazione
cp -r custom_components/climate_group_helper \
      /root/homeassistant/custom_components/

# Riavvio
ha core restart
```

### Configurazione

1. Vai su **Settings > Devices & Services > Helpers**
2. Trova il tuo **Climate Group Helper**
3. Click **Configure > Window Control**
4. Seleziona **Window Mode**: `Area-based`
5. Seleziona **Window Sensors**: tutte le finestre da monitorare
6. Configura **Window Open Delay**: 15s (default)
7. Configura **Close Delay**: 30s (default)
8. **Save**

**IMPORTANTE**: Assicurati che finestre e termostati siano assegnati alle aree in Home Assistant (Settings > Areas).

### Verifica

```bash
# Verifica caricamento
ha core logs | grep "WindowControl initialized"
# Output atteso: "Mode: area_based"

# Test funzionale
# 1. Apri finestra → solo termostato area si spegne
# 2. Chiudi finestra → solo termostato area si riaccende
```

---

## 📁 Struttura Repository

```
climate_group_helper_source/
├── README.md                           ← Questo file
├── QUICK_REFERENCE.md                  ← ⭐ Guida rapida
├── TECHNICAL_DOCUMENTATION.md          ← Documentazione completa
├── MODIFICATIONS_DIFF.md               ← Diff delle modifiche
├── README_MERGE.md                     ← Istruzioni installazione
├── MERGE_SUMMARY.md                    ← Riepilogo merge
├── COMPARISON.md                       ← Confronto versioni
├── TEST_PLAN.md                        ← Piano di test
├── MERGE_COMPLETE.txt                  ← Riepilogo visuale
└── custom_components/
    └── climate_group_helper/
        ├── __init__.py                 (v0.17.0 base)
        ├── climate.py                  (v0.17.0 base)
        ├── const.py                    ⚙️ MODIFICATO
        ├── window_control.py           ⚙️ MODIFICATO
        ├── service_call.py             ⚙️ MODIFICATO
        ├── config_flow.py              ⚙️ MODIFICATO
        ├── strings.json                ⚙️ MODIFICATO
        ├── state.py                    (v0.17.0 base)
        ├── sync_mode.py                (v0.17.0 base)
        ├── schedule.py                 (v0.17.0 base)
        ├── sensor.py                   (v0.17.0 base)
        ├── manifest.json               (v0.17.0)
        └── AREA_BASED_WINDOW_CONTROL.md ← Guida utente
```

---

## 🔧 File Modificati

### Core Modifications

| File | Modifiche | Descrizione |
|------|-----------|-------------|
| `const.py` | +4 linee | Costanti area-based |
| `window_control.py` | +200 linee | Logica area-based completa |
| `service_call.py` | +18 linee | Supporto entity_ids |
| `config_flow.py` | +70 linee | UI dinamica |
| `strings.json` | +6 linee | Traduzioni |

**Totale**: ~300 linee di codice

### File Non Modificati

Tutti gli altri file sono identici alla versione v0.17.0 base:
- `__init__.py`, `climate.py`, `state.py`, `sync_mode.py`, `schedule.py`, `sensor.py`

---

## 🎯 Funzionalità

### Area-Based Mode

- ✅ Controllo granulare per area
- ✅ Rilevamento automatico aree via registry
- ✅ Gestione finestre multiple per area
- ✅ Gestione finestre multiple in aree diverse
- ✅ Delay configurabili (apertura/chiusura)
- ✅ Ripristino intelligente

### Legacy Mode

- ✅ Modalità room/zone preservata
- ✅ Backward compatibility completa
- ✅ Nessuna breaking change

### Integrazione v0.17.0

- ✅ Usa nuovo sistema TargetState
- ✅ Compatibile con CallHandler architecture
- ✅ Source-aware state management
- ✅ Context tracking automatico
- ✅ Retry logic e debouncing

---

## 🧪 Testing

### Test Completato

**Data**: 2026-01-24 19:58  
**Ambiente**: Home Assistant 2026.1.2

**Timeline Test:**
```
19:57:02 - Finestra studio aperta
19:57:17 - Termostato studio spento (dopo 15s)
19:58:25 - Finestra studio chiusa
19:58:56 - Termostato studio ripristinato (dopo 30s)
```

**Risultato**: ✅ Funzionamento perfetto

### Test Suite

Vedi [TEST_PLAN.md](TEST_PLAN.md) per:
- 12 test case completi
- Performance tests
- Rollback procedure
- Success criteria

---

## 🐛 Troubleshooting

### Problemi Comuni

| Problema | Soluzione |
|----------|-----------|
| Climate group non si carica | Verifica sintassi Python, controlla log errori |
| WindowControl non inizializza | Verifica mode = "area_based" e sensori configurati |
| Finestra aperta ma niente succede | Verifica sensore funziona e area configurata |
| Termostato non si riaccende | Verifica altre finestre chiuse e target mode |
| Tutti termostati si spengono | Verifica mode = "area_based" (non "on") |

Vedi [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-troubleshooting-rapido) per dettagli.

---

## 🔄 Re-Merge su Nuova Versione

### Quando Necessario

- Nuova versione upstream (es. v0.18.0)
- Bugfix critici da integrare
- Nuove feature da mantenere

### Processo

1. **Analisi**: Confronta file chiave con nuova versione
2. **Verifica**: Controlla compatibilità architetturale
3. **Applica**: Riapplica modifiche (vedi QUICK_REFERENCE.md)
4. **Test**: Verifica funzionamento completo

Vedi [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#guida-al-re-merge) per guida completa.

---

## 📊 Log Patterns

### Funzionamento Corretto

```
DEBUG [...] WindowControl initialized. Mode: area_based
DEBUG [...] Window binary_sensor.finestra_X opened, scheduling turn off in 15.0s
INFO  [...] Window ... opened in area 'Y', turning off: ['climate.termo_Y']
DEBUG [...] Window ... closed, scheduling restore check in 30.0s
INFO  [...] Window ... closed, restoring area 'Y': ['climate.termo_Y']
```

### Debug

```bash
# Abilita debug logging in configuration.yaml
logger:
  default: info
  logs:
    custom_components.climate_group_helper: debug

# Monitora log
ha core logs --follow | grep climate_group_helper
```

---

## 🔑 Punti Chiave

### Differenze Architetturali v0.16.1 → v0.17.0

| Aspetto | v0.16.1 | v0.17.0 |
|---------|---------|---------|
| Chiamate servizi | `hass.services.async_call()` | `call_handler.call_immediate()` |
| Stato | `_group.hvac_mode` | `target_state.hvac_mode` |
| Accesso hass | `_group.hass` | `_hass` |
| Targeting | Loop manuale | `entity_ids` parameter |

### Codice Chiave

```python
# ✅ CORRETTO (v0.17.0)
await self.call_handler.call_immediate(
    {"hvac_mode": HVACMode.OFF}, 
    entity_ids=["climate.termo1"]
)

if self.target_state.hvac_mode == HVACMode.OFF:
    return

state = self._hass.states.get(entity_id)
```

---

## 📞 Supporto

### Documentazione

- **Quick Start**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Tecnica**: [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)
- **Diff**: [MODIFICATIONS_DIFF.md](MODIFICATIONS_DIFF.md)

### Repository

- **Upstream**: https://github.com/bjrnptrsn/climate_group_helper
- **Versione Base**: 0.17.0
- **Custom Feature**: Area-Based Window Control

---

## 📝 Changelog

### 2026-01-24 - v0.17.0 + Area-Based

- ✅ Merge completato su architettura v0.17.0
- ✅ Area-based window control integrato
- ✅ Backward compatibility preservata
- ✅ Test completati con successo
- ✅ Documentazione completa creata
- ✅ Codice commentato inline

---

## 📄 Licenza

Stesso della versione upstream (Climate Group Helper).

---

## 🙏 Credits

- **Climate Group Helper**: bjrnptrsn
- **Area-Based Feature**: Custom modification
- **Merge v0.17.0**: 2026-01-24

---

**Ultima Modifica**: 2026-01-24  
**Versione**: 0.17.0 + Area-Based Window Control  
**Status**: ✅ Produzione
