# Programmatic SEO Toolkit

> **Languages:** [English](README.md) | [Español](README.es.md)

**GitHub description (short):**  
Rule-based programmatic SEO planner — GSC + crawl data → prioritized URL opportunities (CSV/YAML). Works standalone or with [SEO-as-Code](https://github.com/seo-as-code/SEO-as-Code-Toolkit) and [AI-SEO-Toolkit](https://github.com/seo-as-code/AI-SEO-Toolkit).

---

## Quick test (no credentials, no parent repo)

Anyone can test in under 2 minutes with bundled sample data:

```bash
git clone https://github.com/seo-as-code/programmatic-SEO.git
cd programmatic-SEO
pip install -r requirements.txt
copy config\project.local.yaml.example config\project.local.yaml   # Windows
# cp config/project.local.yaml.example config/project.local.yaml   # macOS/Linux
python scripts/planner/pseo_planner.py
```

Or:

```powershell
.\reports\code\run_planner.ps1
```

**Expected output** in `reports/pseo/`:

- `pseo_queries_*.csv` — one row per GSC query
- `pseo_opportunities_*.csv` — clustered URL opportunities
- `pseo_opportunities_*.yaml` — machine-readable page specs
- `pseo_summary_*.md` — human-readable summary

### Configure your site

1. Copy `config/project.local.yaml.example` → `config/project.local.yaml`
2. Copy `config/patterns.local.yaml.example` → `config/patterns.local.yaml` (optional but recommended)
3. Edit **only** `*.local.yaml` files (gitignored, never pushed)

| File | Purpose |
|------|---------|
| `project.local.yaml` | Site URL, locale, paths to GSC/SF CSV |
| `patterns.local.yaml` | Your services, cities, custom pattern rules |

`config/project.yaml` and `config/patterns.yaml` on GitHub stay generic.

---

## 1. What this repository does

**Programmatic SEO Toolkit** is the **architecture layer** of the SEO-as-Code stack:

- Reads **GSC queries** + **crawl inventory** (Screaming Frog)
- Applies **YAML pattern rules** (services, locations, intents)
- Outputs **prioritized URL opportunities** with actions: `create_new`, `optimize_existing`, `consolidate`, `ignore`

No AI required. No Ahrefs. Deterministic and reproducible.

---

## 2. How the three repositories work together

```text
SEO-as-Code-Toolkit (Data)
  ├─ GSC, GA4, CrUX, Screaming Frog → data/raw/*.csv
  └─ Index monitor (separate folder in monorepo)

Programmatic-SEO (Architecture)  ← this repo
  ├─ GSC + SF + pattern rules
  └─ reports/pseo/*.yaml → URL specs for devs/CMS

AI-SEO-Toolkit (Decision)
  ├─ Semantic map, gaps, blog strategy, executive report
  └─ Optional copy briefs on top of pSEO specs
```

| Handoff | File | From → To |
|---------|------|-----------|
| GSC export | `../data/raw/gsc_*.csv` | SEO-as-Code → pSEO Planner |
| Crawl export | `../data/raw/internos_html.csv` | SEO-as-Code → pSEO Planner |
| Opportunities | `reports/pseo/pseo_opportunities_*.yaml` | pSEO → dev/CMS or AI module 12 |

---

## 3. Repository structure

```text
programmatic-seo/
  config/
    project.yaml              # generic site placeholders
    patterns.yaml             # generic pattern rules
    project.local.yaml.example
    patterns.local.yaml.example
  data/samples/               # demo GSC + SF (committed)
  scripts/
    lib/                      # config loader + rule engine
    planner/pseo_planner.py   # main CLI
    orchestrator/pseo_master.py
  reports/
    pseo/                     # generated (gitignored)
    code/                     # run_planner.ps1, run_with_seo_as_code.ps1
  templates/                  # page spec examples for CMS
  docs/PLAYBOOK.md
```

---

## 4. Commands

### Standalone (samples)

```powershell
cd programmatic-seo
.\reports\code\run_planner.ps1
```

### Inside SEO-as-Code monorepo

```powershell
cd C:\path\to\proyecto_seo\programmatic-seo
.\reports\code\run_with_seo_as_code.ps1
```

### Manual paths

```powershell
py .\scripts\planner\pseo_planner.py --gsc ..\data\raw\gsc_oauth_2026-01-01_2026-02-01.csv --sf ..\data\raw\internos_html.csv
```

---

## 5. Pattern rules (summary)

Defined in `config/patterns.yaml` + `patterns.local.yaml`:

| Pattern | Triggers | Suggested URL |
|---------|----------|---------------|
| `service_location` | service + city tokens | `/services/{service}-{city}/` |
| `service_national` | service, no geo | `/services/{service}/` |
| `blog_informational` | how/what/guide queries | `/blog/{query-slug}/` |
| `brand_navigational` | brand intent | `ignore` |

**Decision rules** override patterns: hub weakness, cannibalization, low volume, etc.

Full guide: [docs/PLAYBOOK.md](docs/PLAYBOOK.md)

---

## 6. Actions explained

| Action | When |
|--------|------|
| `create_new` | Demand exists, no dedicated URL |
| `optimize_existing` | URL exists but underperforms |
| `consolidate` | Same query split across multiple URLs |
| `ignore` | Low volume or out of scope |

---

## 7. What NOT to commit

See `.gitignore`:

- `config/project.local.yaml`
- `config/patterns.local.yaml`
- `reports/pseo/*.csv`, `*.yaml`, `*.md`
- `.venv/`

---

## 8. Related repositories

- [SEO-as-Code-Toolkit](https://github.com/seo-as-code/SEO-as-Code-Toolkit) — data extraction
- [AI-SEO-Toolkit](https://github.com/seo-as-code/AI-SEO-Toolkit) — analysis & executive reports
- Org: [github.com/seo-as-code](https://github.com/seo-as-code)

---

## License

MIT — use freely in client and personal projects.
