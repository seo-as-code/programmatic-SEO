# Programmatic SEO Toolkit

> **Idiomas:** [English](README.md) | [Español](README.es.md)

**Descripción para GitHub (corta):**  
Planificador pSEO basado en reglas — datos GSC + crawl → oportunidades de URL priorizadas (CSV/YAML). Funciona solo o con [SEO-as-Code](https://github.com/seo-as-code/SEO-as-Code-Toolkit) y [AI-SEO-Toolkit](https://github.com/seo-as-code/AI-SEO-Toolkit).

---

## Prueba rápida (sin credenciales ni repo padre)

```bash
git clone https://github.com/seo-as-code/Programmatic-SEO.git
cd Programmatic-SEO
pip install -r requirements.txt
copy config\project.local.yaml.example config\project.local.yaml
python scripts/planner/pseo_planner.py
```

O:

```powershell
.\reports\code\run_planner.ps1
```

**Salida esperada** en `reports/pseo/`:

- `pseo_queries_*.csv`
- `pseo_opportunities_*.csv`
- `pseo_opportunities_*.yaml`
- `pseo_summary_*.md`

### Configura tu sitio

1. `config/project.local.yaml.example` → `config/project.local.yaml`
2. `config/patterns.local.yaml.example` → `config/patterns.local.yaml` (recomendado)
3. Edita **solo** los `*.local.yaml` (gitignored)

| Archivo | Para qué |
|---------|----------|
| `project.local.yaml` | URL del sitio, rutas a CSV GSC/SF |
| `patterns.local.yaml` | Servicios, ciudades, reglas de patrones |

---

## 1. Qué hace este repositorio

Capa de **arquitectura programática**:

- Lee queries de **GSC** + inventario **Screaming Frog**
- Aplica **reglas YAML** (servicios, ubicaciones, intención)
- Genera **oportunidades de URL** con acciones: `create_new`, `optimize_existing`, `consolidate`, `ignore`

Sin IA obligatoria. Sin Ahrefs. Reproducible.

---

## 2. Los tres repos juntos

```text
SEO-as-Code (Datos)     →  GSC, GA4, SF en data/raw/
Programmatic-SEO (Arq.) →  patrones + specs YAML   ← este repo
AI-SEO (Decisión)       →  informes, blog, ejecutivo
```

---

## 3. Comandos

```powershell
# Demo con samples
.\reports\code\run_planner.ps1

# Dentro del monorepo proyecto_seo
.\reports\code\run_with_seo_as_code.ps1
```

---

## 4. Patrones principales

| Patrón | Dispara | URL sugerida |
|--------|---------|--------------|
| `service_location` | servicio + ciudad | `/services/{servicio}-{ciudad}/` |
| `blog_informational` | how/what/guía | `/blog/{slug}/` |
| `brand_navigational` | marca | `ignore` |

Guía completa: [docs/PLAYBOOK.md](docs/PLAYBOOK.md)

---

## 5. No subir a Git

- `config/*.local.yaml`
- `reports/pseo/*` generados
- `.venv/`

---

## Repos relacionados

- [SEO-as-Code-Toolkit](https://github.com/seo-as-code/SEO-as-Code-Toolkit)
- [AI-SEO-Toolkit](https://github.com/seo-as-code/AI-SEO-Toolkit)
