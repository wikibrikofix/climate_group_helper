# Documentation Index - Area-Based Window Control

## 🚀 Quick Start

**Are you a developer who needs to understand/modify the code?**
→ Start here: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (10 minutes)

**Need to reapply modifications to a new version?**
→ Follow: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) section "How to Reapply" + [MODIFICATIONS_DIFF.md](MODIFICATIONS_DIFF.md)

**Are you an end user who needs to configure?**
→ Read: [AREA_BASED_WINDOW_CONTROL.md](custom_components/climate_group_helper/AREA_BASED_WINDOW_CONTROL.md)

---

## 📚 Complete Documentation

### For Developers

| File | Purpose | Reading Time |
|------|---------|--------------|
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) ⭐⭐⭐ | Quick guide, checklist, troubleshooting | 10 min |
| [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) | Architecture, re-merge guide, test suite | 60 min |
| [MODIFICATIONS_DIFF.md](MODIFICATIONS_DIFF.md) | Exact diffs, complete code | 30 min |
| [COMPARISON.md](COMPARISON.md) | Comparison v0.16.1 vs v0.18.0 | 20 min |

### For Users

| File | Purpose | Reading Time |
|------|---------|--------------|
| [AREA_BASED_WINDOW_CONTROL.md](custom_components/climate_group_helper/AREA_BASED_WINDOW_CONTROL.md) | Configuration, examples, debugging | 10 min |
| [README_MERGE.md](README_MERGE.md) | Installation instructions | 5 min |

### Supporting Documentation

| File | Purpose |
|------|---------|
| [README.md](README.md) | General project overview |
| [MERGE_SUMMARY.md](MERGE_SUMMARY.md) | Technical merge summary |
| [TEST_PLAN.md](TEST_PLAN.md) | Complete test plan (12 test cases) |

---

## 🎯 Use Case Scenarios

### Scenario 1: First Time - Understanding the Project
```
1. Read README.md (5 min)
2. Read QUICK_REFERENCE.md (10 min)
3. Check MODIFICATIONS_DIFF.md for code (15 min)
Total: 30 minutes
```

### Scenario 2: Need to Re-Merge
```
1. Download new upstream version
2. Follow QUICK_REFERENCE.md section "How to Reapply" (20 min)
3. Use MODIFICATIONS_DIFF.md for exact code (30 min)
4. Test with TEST_PLAN.md (30 min)
Total: 80 minutes
```

### Scenario 3: Having a Problem
```
1. Check QUICK_REFERENCE.md section "Troubleshooting" (5 min)
2. If more details needed: TECHNICAL_DOCUMENTATION.md (10 min)
Total: 15 minutes
```

### Scenario 4: Want to Understand Architecture
```
1. Read TECHNICAL_DOCUMENTATION.md section "Architecture" (30 min)
2. Read COMPARISON.md for differences (20 min)
3. Study MODIFICATIONS_DIFF.md for implementation (30 min)
Total: 80 minutes
```

---

## 📊 Statistics

- **Total Documentation Files**: 9 files
- **Total Documentation Lines**: ~4,000 lines
- **Total Modified Code Lines**: ~300 lines
- **Modified Code Files**: 5 files
- **Complete Reading Time**: ~3 hours
- **Quick Start Time**: ~10 minutes

---

## 🗂️ Repository Structure

```
climate_group_helper/
├── INDEX.md                            ← This file
├── README.md                           ← General overview
├── QUICK_REFERENCE.md                  ← ⭐ Start here
├── TECHNICAL_DOCUMENTATION.md          ← Complete documentation
├── MODIFICATIONS_DIFF.md               ← Code diffs
├── COMPARISON.md                       ← Version comparison
├── README_MERGE.md                     ← Installation instructions
├── MERGE_SUMMARY.md                    ← Merge summary
├── TEST_PLAN.md                        ← Test plan
├── docs_ita/                           ← Italian documentation
└── custom_components/
    └── climate_group_helper/
        ├── window_control.py           ← ⚙️ Modified
        ├── service_call.py             ← ⚙️ Modified
        ├── config_flow.py              ← ⚙️ Modified
        ├── const.py                    ← ⚙️ Modified
        ├── strings.json                ← ⚙️ Modified
        ├── AREA_BASED_WINDOW_CONTROL.md ← User guide
        └── [other v0.18.0 base files]
```

---

## 🔍 Quick Search

### Search Information

```bash
# Search all documentation
cd /root/homeassistant/repos/climate_group_helper_fork
grep -r "search_term" *.md

# Examples:
grep -r "area-based" *.md
grep -r "call_handler" *.md
grep -r "troubleshooting" *.md
```

### Useful Commands

```bash
# List all markdown files
ls -lh *.md

# Count documentation lines
wc -l *.md

# View specific file
cat QUICK_REFERENCE.md | less
```

---

## 📞 Quick References

### Versions
- **Base**: Climate Group Helper v0.18.0
- **Modification**: Area-Based Window Control
- **Date**: 2026-02-01

### Important Paths
- **Documentation**: `/root/homeassistant/repos/climate_group_helper_fork/`
- **Installed Code**: `/root/homeassistant/custom_components/climate_group_helper/`
- **Backup**: `/root/climate_group_helper.backup`

### Useful Links
- **Upstream Repository**: https://github.com/bjrnptrsn/climate_group_helper
- **Complete Summary**: `/root/DOCUMENTAZIONE_COMPLETA.txt`

---

**Last Modified**: 2026-02-01  
**Status**: ✅ Complete and Tested

---

## 🌍 Languages

- **English**: Current documentation (root directory)
- **Italian**: [docs_ita/](docs_ita/) directory
