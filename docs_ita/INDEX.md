# Indice Documentazione - Area-Based Window Control

## 🚀 Inizio Rapido

**Sei uno sviluppatore che deve capire/modificare il codice?**
→ Inizia da: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (10 minuti)

**Devi riapplicare le modifiche su una nuova versione?**
→ Segui: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) sezione "Come Riapplicare" + [MODIFICATIONS_DIFF.md](MODIFICATIONS_DIFF.md)

**Sei un utente finale che deve configurare?**
→ Leggi: [AREA_BASED_WINDOW_CONTROL.md](custom_components/climate_group_helper/AREA_BASED_WINDOW_CONTROL.md)

---

## 📚 Documentazione Completa

### Per Sviluppatori

| File | Scopo | Tempo Lettura |
|------|-------|---------------|
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) ⭐⭐⭐ | Guida rapida, checklist, troubleshooting | 10 min |
| [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) | Architettura, guida re-merge, test suite | 60 min |
| [MODIFICATIONS_DIFF.md](MODIFICATIONS_DIFF.md) | Diff esatti, codice completo | 30 min |
| [COMPARISON.md](COMPARISON.md) | Confronto v0.16.1 vs v0.18.0 | 20 min |

### Per Utenti

| File | Scopo | Tempo Lettura |
|------|-------|---------------|
| [AREA_BASED_WINDOW_CONTROL.md](custom_components/climate_group_helper/AREA_BASED_WINDOW_CONTROL.md) | Configurazione, esempi, debugging | 10 min |
| [README_MERGE.md](README_MERGE.md) | Istruzioni installazione | 5 min |

### Documentazione di Supporto

| File | Scopo |
|------|-------|
| [README.md](README.md) | Panoramica generale progetto |
| [MERGE_SUMMARY.md](MERGE_SUMMARY.md) | Riepilogo tecnico merge |
| [TEST_PLAN.md](TEST_PLAN.md) | Piano test completo (12 test case) |

---

## 🎯 Scenari d'Uso

### Scenario 1: Prima Volta - Capire il Progetto
```
1. Leggi README.md (5 min)
2. Leggi QUICK_REFERENCE.md (10 min)
3. Guarda MODIFICATIONS_DIFF.md per vedere il codice (15 min)
Totale: 30 minuti
```

### Scenario 2: Devo Fare un Re-Merge
```
1. Scarica nuova versione upstream
2. Segui QUICK_REFERENCE.md sezione "Come Riapplicare" (20 min)
3. Usa MODIFICATIONS_DIFF.md per codice esatto (30 min)
4. Testa con TEST_PLAN.md (30 min)
Totale: 80 minuti
```

### Scenario 3: Ho un Problema
```
1. Consulta QUICK_REFERENCE.md sezione "Troubleshooting" (5 min)
2. Se serve più dettagli: TECHNICAL_DOCUMENTATION.md (10 min)
Totale: 15 minuti
```

### Scenario 4: Voglio Capire l'Architettura
```
1. Leggi TECHNICAL_DOCUMENTATION.md sezione "Architettura" (30 min)
2. Leggi COMPARISON.md per differenze (20 min)
3. Studia MODIFICATIONS_DIFF.md per implementazione (30 min)
Totale: 80 minuti
```

---

## 📊 Statistiche

- **Totale File Documentazione**: 9 file
- **Totale Righe Documentazione**: ~4,000 righe
- **Totale Righe Codice Modificato**: ~300 righe
- **File Codice Modificati**: 5 file
- **Tempo Lettura Completa**: ~3 ore
- **Tempo Quick Start**: ~10 minuti

---

## 🗂️ Struttura Repository

```
climate_group_helper_source/
├── INDEX.md                            ← Questo file
├── README.md                           ← Panoramica generale
├── QUICK_REFERENCE.md                  ← ⭐ Inizia qui
├── TECHNICAL_DOCUMENTATION.md          ← Documentazione completa
├── MODIFICATIONS_DIFF.md               ← Diff del codice
├── COMPARISON.md                       ← Confronto versioni
├── README_MERGE.md                     ← Istruzioni installazione
├── MERGE_SUMMARY.md                    ← Riepilogo merge
├── TEST_PLAN.md                        ← Piano test
└── custom_components/
    └── climate_group_helper/
        ├── window_control.py           ← ⚙️ Modificato
        ├── service_call.py             ← ⚙️ Modificato
        ├── config_flow.py              ← ⚙️ Modificato
        ├── const.py                    ← ⚙️ Modificato
        ├── strings.json                ← ⚙️ Modificato
        ├── AREA_BASED_WINDOW_CONTROL.md ← Guida utente
        └── [altri file v0.18.0 base]
```

---

## 🔍 Ricerca Rapida

### Cercare Informazioni

```bash
# Cerca in tutta la documentazione
cd /root/homeassistant/repos/climate_group_helper_source
grep -r "termine_da_cercare" *.md

# Esempi:
grep -r "area-based" *.md
grep -r "call_handler" *.md
grep -r "troubleshooting" *.md
```

### Comandi Utili

```bash
# Lista tutti i file markdown
ls -lh *.md

# Conta righe documentazione
wc -l *.md

# Visualizza file specifico
cat QUICK_REFERENCE.md | less
```

---

## 📞 Riferimenti Rapidi

### Versioni
- **Base**: Climate Group Helper v0.18.0
- **Modifica**: Area-Based Window Control
- **Data**: 2026-02-01

### Percorsi Importanti
- **Documentazione**: `/root/homeassistant/repos/climate_group_helper_source/`
- **Codice Installato**: `/root/homeassistant/custom_components/climate_group_helper/`
- **Backup**: `/root/climate_group_helper.backup`

### Link Utili
- **Repository Upstream**: https://github.com/bjrnptrsn/climate_group_helper
- **Riepilogo Completo**: `/root/DOCUMENTAZIONE_COMPLETA.txt`

---

**Ultima Modifica**: 2026-02-01  
**Status**: ✅ Completo e Testato
