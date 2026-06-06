# Playbook — Programmatic SEO Toolkit

## Visión en una frase

**Datos GSC + crawl + reglas YAML → lista priorizada de URLs programáticas** listas para implementar en CMS, Next.js o WordPress.

---

## 1. Dónde vive el proyecto

Puedes clonar **solo este repo** o integrarlo en el workspace SEO-as-Code (cada persona elige su ruta local):

```text
your-workspace/              # ejemplo: D:\dev\proyecto_seo — NO subir rutas personales a Git
├── scripts/                 ← SEO-as-Code (Etapa 1-2) — repo SEO-as-Code-Toolkit
├── programmatic-seo/        ← este repo (Etapa 2.5)
├── ai-seo-toolkit/          ← AI-as-Code (Etapa 3)
└── proyecto_seo-index/      ← Index Monitor (opcional, suele ser local)
```

`programmatic-seo`, `ai-seo-toolkit` y el toolkit de datos son **repos Git separados**; la carpeta padre es solo tu workspace local.

---

## 2. Flujo recomendado

```text
1. SEO-as-Code:  gsc_oauth.py + leer_sf.py
2. pSEO:         run_with_seo_as_code.ps1
3. Revisar:      reports/pseo/pseo_summary_*.md
4. Implementar:  templates/ + CMS
5. (Opcional) AI: módulo 12 blog / informe ejecutivo
6. Monitor:      proyecto_seo-index (indexación)
```

---

## 3. Archivos de configuración

| Archivo | Git | Contenido |
|---------|-----|-----------|
| `config/project.yaml` | Sí | Placeholders genéricos |
| `config/patterns.yaml` | Sí | Patrones y reglas base |
| `config/project.local.yaml` | **No** | Tu dominio y rutas CSV |
| `config/patterns.local.yaml` | **No** | Tus servicios y ciudades |

### project.local.yaml — campos clave

```yaml
project:
  origin: "https://example.com"
data_sources:
  gsc_glob: "../data/raw/gsc_*.csv"
  sf_glob: "../data/raw/internos_html.csv"
```

### patterns.local.yaml — personaliza

```yaml
variables:
  locations:
    - slug: ibiza
      tokens: [ibiza]
  services:
    - slug: eco-friendly-renovations
      tokens: [eco, sustainable, renovation]
      hub_path: /our-services/
```

---

## 4. Patrones (orden de evaluación)

1. `service_location` — servicio + ubicación
2. `service_national` — solo servicio
3. `blog_informational` — contenido educativo
4. `brand_navigational` — ignorar

El **primer patrón que encaja** gana.

---

## 5. Reglas de decisión

| ID | Efecto |
|----|--------|
| `transactional_no_blog` | Servicio → landing, no blog |
| `hub_only_weak` | Hub genérico + demanda → URL dedicada |
| `strong_existing_coverage` | Ya cubierto → optimizar |
| `cannibalization` | Varias URLs → consolidar |
| `low_volume` | Pocas impresiones → ignorar |

---

## 6. Salidas

| Archivo | Uso |
|---------|-----|
| `pseo_queries_*.csv` | Auditoría query a query |
| `pseo_opportunities_*.yaml` | Spec para devs |
| `pseo_summary_*.md` | Revisión humana |

---

## 7. Integración con AI-SEO-Toolkit

- **No duplica** módulos 05 (gaps) ni 12 (blog).
- pSEO responde: **qué URL crear y con qué plantilla**.
- AI responde: **cómo escribir el contenido** (brief, tono, FAQ).

Pipeline sugerido: `pSEO YAML` → revisión humana → módulo 12 solo para posts blog.

---

## 8. Publicar en GitHub

```powershell
cd programmatic-seo
git init
git add .
git commit -m "Initial Programmatic SEO Toolkit"
git remote add origin https://github.com/seo-as-code/programmatic-SEO.git
git push -u origin main
```

**About del repo:**

> Rule-based programmatic SEO planner: GSC + crawl → prioritized URL specs (YAML/CSV). Works with SEO-as-Code and AI-SEO-Toolkit.

**Topics:** `seo`, `programmatic-seo`, `google-search-console`, `python`, `yaml`, `seo-as-code`

---

## 9. Checklist antes de compartir

- [ ] `project.local.yaml` no está en el commit
- [ ] `patterns.local.yaml` no está en el commit
- [ ] `reports/pseo/*.csv` generados ignorados
- [ ] README quick test funciona con `data/samples/`
