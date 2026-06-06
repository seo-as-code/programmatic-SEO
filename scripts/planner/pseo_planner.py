"""
Programmatic SEO Planner — rule-based URL opportunities from GSC + crawl data.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.common import (  # noqa: E402
    BASE_DIR,
    latest_file,
    load_patterns_config,
    load_project_config,
    site_origin,
)
from lib.pattern_rules import (  # noqa: E402
    QueryContext,
    apply_decision_rules,
    build_url,
    classify_intent,
    classify_landing_kind,
    coverage_for_query,
    extract_service_location,
    match_pattern,
    score_priority,
    url_path,
)


def _resolve_input_path(project: dict[str, Any], key: str, fallback: str) -> str | None:
    rel = project.get("data_sources", {}).get(key, fallback)
    full = str(BASE_DIR / rel)
    if "*" in rel:
        return latest_file(full)
    return full


def _load_sf(sf_path: str | None, project: dict[str, Any]) -> tuple[set[str], dict[str, str]]:
    path = sf_path or _resolve_input_path(project, "sf_glob", "data/samples/sf_sample.csv")
    if not path or not Path(path).exists():
        return set(), {}
    df = pd.read_csv(path)
    addr_col = "Address" if "Address" in df.columns else df.columns[0]
    title_col = "Title 1" if "Title 1" in df.columns else None
    urls: set[str] = set()
    titles: dict[str, str] = {}
    for _, row in df.iterrows():
        raw = str(row.get(addr_col, "")).strip()
        if not raw:
            continue
        p = url_path(raw)
        urls.add(p)
        if title_col:
            titles[p] = str(row.get(title_col, ""))
    return urls, titles


def _aggregate_gsc(gsc: pd.DataFrame, min_impressions: int) -> list[QueryContext]:
    for col in ("impressions", "clicks", "position"):
        if col in gsc.columns:
            gsc[col] = pd.to_numeric(gsc[col], errors="coerce").fillna(0)

    grouped = (
        gsc.groupby("query", dropna=False)
        .agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            avg_position=("position", "mean"),
            pages=("page", lambda s: sorted({url_path(str(x)) for x in s if str(x).strip()})),
        )
        .reset_index()
    )
    grouped = grouped[grouped["impressions"] >= min_impressions].sort_values("impressions", ascending=False)

    contexts: list[QueryContext] = []
    for _, row in grouped.iterrows():
        query = str(row["query"])
        pages = list(row["pages"]) if isinstance(row["pages"], list) else []
        contexts.append(
            QueryContext(
                query=query,
                impressions=int(row["impressions"]),
                clicks=int(row["clicks"]),
                avg_position=round(float(row["avg_position"]), 2),
                pages=pages,
                intent=classify_intent(query),
            )
        )
    return contexts


def _enrich_context(ctx: QueryContext, cfg: dict[str, Any], sf_urls: set[str], page_titles: dict[str, str]) -> None:
    ctx.service, ctx.location = extract_service_location(ctx.query, cfg)
    ctx.best_page = ctx.pages[0] if ctx.pages else ""
    if not ctx.best_page and ctx.service and ctx.service.hub_path:
        ctx.best_page = ctx.service.hub_path
    ctx.coverage = coverage_for_query(ctx.query, ctx.best_page, page_titles)
    ctx.landing_kind = classify_landing_kind(ctx.best_page, cfg)


def _cluster_key(row: dict[str, Any]) -> str:
    return "|".join([str(row.get("pattern_id", "")), str(row.get("suggested_url", "")), str(row.get("action", ""))])


def run(gsc_path: str | None = None, sf_path: str | None = None) -> dict[str, Any]:
    project = load_project_config()
    cfg = load_patterns_config()
    thresholds = cfg.get("thresholds", {})
    min_impressions = int(thresholds.get("min_impressions", 50))

    gsc_file = gsc_path or _resolve_input_path(project, "gsc_glob", "data/samples/gsc_sample.csv")
    if not gsc_file or not Path(gsc_file).exists():
        raise FileNotFoundError(
            "GSC CSV not found. Use --gsc, place data in data/samples/, "
            "or point data_sources.gsc_glob to SEO-as-Code exports."
        )

    gsc = pd.read_csv(gsc_file)
    if "query" not in gsc.columns:
        raise ValueError("GSC CSV must include column: query")

    sf_urls, page_titles = _load_sf(sf_path, project)
    origin = site_origin(project)
    reports_dir = BASE_DIR / project.get("output", {}).get("reports_dir", "reports/pseo")

    rows: list[dict[str, Any]] = []
    for ctx in _aggregate_gsc(gsc, min_impressions):
        _enrich_context(ctx, cfg, sf_urls, page_titles)
        pattern = match_pattern(ctx, cfg)
        if not pattern:
            continue

        action, note, forced = apply_decision_rules(ctx, pattern, cfg)
        if forced:
            pattern = forced

        suggested_url = build_url(pattern, ctx)
        if suggested_url and not suggested_url.startswith("/"):
            suggested_url = "/" + suggested_url.lstrip("/")
        full_url = f"{origin}{suggested_url}" if suggested_url else ""

        existing_url = ""
        if ctx.pages:
            existing_url = f"{origin}{ctx.pages[0]}"
        elif ctx.best_page:
            existing_url = f"{origin}{ctx.best_page}"

        priority = score_priority(action, ctx, pattern, cfg)

        rows.append(
            {
                "query": ctx.query,
                "impressions": ctx.impressions,
                "clicks": ctx.clicks,
                "avg_position": ctx.avg_position,
                "intent": ctx.intent,
                "pattern_id": pattern.get("id", ""),
                "pattern_name": pattern.get("name", ""),
                "service_slug": ctx.service.slug if ctx.service else "",
                "location_slug": ctx.location.slug if ctx.location else "",
                "action": action,
                "priority": priority,
                "suggested_url": suggested_url,
                "full_url": full_url,
                "existing_url": existing_url,
                "landing_kind": ctx.landing_kind,
                "coverage": round(ctx.coverage, 2),
                "gsc_page_count": len(ctx.pages),
                "content_template": pattern.get("content_template", ""),
                "schema_types": ",".join(pattern.get("schema_types", []) or []),
                "decision_note": note,
            }
        )

    if not rows:
        print("[pSEO] No opportunities with current rules. Adjust patterns.local.yaml or thresholds.")
        return {"rows": 0}

    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in rows:
        clusters[_cluster_key(record)].append(record)

    opportunities = []
    for key, items in clusters.items():
        if not key.strip("|"):
            continue
        head = items[0]
        opportunities.append(
            {
                "cluster_key": key,
                "pattern_id": head["pattern_id"],
                "pattern_name": head["pattern_name"],
                "action": head["action"],
                "priority": head["priority"],
                "suggested_url": head["suggested_url"],
                "full_url": head["full_url"],
                "content_template": head["content_template"],
                "schema_types": head["schema_types"].split(",") if head["schema_types"] else [],
                "total_impressions": sum(i["impressions"] for i in items),
                "queries": [i["query"] for i in items],
                "query_count": len(items),
                "avg_position": round(sum(i["avg_position"] for i in items) / len(items), 2),
                "decision_note": head["decision_note"],
                "internal_links_from": _suggest_internal_links(head, cfg),
            }
        )

    opportunities.sort(
        key=lambda x: ({"high": 0, "medium": 1, "low": 2}.get(x["priority"], 3), -x["total_impressions"])
    )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir.mkdir(parents=True, exist_ok=True)

    detail_path = reports_dir / f"pseo_queries_{stamp}.csv"
    opp_csv = reports_dir / f"pseo_opportunities_{stamp}.csv"
    opp_yaml = reports_dir / f"pseo_opportunities_{stamp}.yaml"
    summary_md = reports_dir / f"pseo_summary_{stamp}.md"

    pd.DataFrame(rows).to_csv(detail_path, index=False, encoding="utf-8")
    pd.DataFrame(opportunities).to_csv(opp_csv, index=False, encoding="utf-8")
    with opp_yaml.open("w", encoding="utf-8") as f:
        yaml.safe_dump({"opportunities": opportunities}, f, allow_unicode=True, sort_keys=False)
    _write_summary(summary_md, opportunities, gsc_file, project)

    print(f"[pSEO] Queries analyzed: {len(rows)}")
    print(f"[pSEO] Opportunity clusters: {len(opportunities)}")
    print(f"[pSEO] Detail CSV: {detail_path}")
    print(f"[pSEO] Opportunities CSV: {opp_csv}")
    print(f"[pSEO] Spec YAML: {opp_yaml}")
    print(f"[pSEO] Summary MD: {summary_md}")

    return {"queries": len(rows), "opportunities": len(opportunities), "yaml": str(opp_yaml)}


def _suggest_internal_links(row: dict[str, Any], cfg: dict[str, Any]) -> list[str]:
    kinds = cfg.get("url_kinds", {})
    links = list(kinds.get("hub_paths", ["/"]))
    if row.get("service_slug"):
        for svc in cfg.get("variables", {}).get("services", []):
            if svc.get("slug") == row["service_slug"] and svc.get("hub_path"):
                links.insert(0, svc["hub_path"])
    return list(dict.fromkeys(links))[:4]


def _write_summary(path: Path, opportunities: list[dict[str, Any]], gsc_file: str, project: dict[str, Any]) -> None:
    domain = project.get("project", {}).get("domain", "")
    by_action: dict[str, int] = defaultdict(int)
    by_priority: dict[str, int] = defaultdict(int)
    for opp in opportunities:
        by_action[opp["action"]] += 1
        by_priority[opp["priority"]] += 1

    lines = [
        "# Programmatic SEO — summary",
        "",
        f"Site: **{domain}**",
        f"GSC input: `{gsc_file}`",
        f"Opportunities: **{len(opportunities)}**",
        "",
        "## By action",
        "",
    ]
    for action, count in sorted(by_action.items(), key=lambda x: -x[1]):
        lines.append(f"- **{action}**: {count}")

    lines.extend(["", "## By priority", ""])
    for prio in ("high", "medium", "low"):
        lines.append(f"- **{prio}**: {by_priority.get(prio, 0)}")

    lines.extend(["", "## Top opportunities", ""])
    for opp in opportunities[:10]:
        if opp["action"] == "ignore":
            continue
        lines.append(f"### {opp['priority'].upper()} — {opp['pattern_name']} ({opp['action']})")
        lines.append(f"- URL: `{opp['full_url'] or '(n/a)'}`")
        lines.append(f"- Impressions: {opp['total_impressions']} | Queries: {opp['query_count']}")
        lines.append(f"- Template: `{opp['content_template']}`")
        if opp.get("decision_note"):
            lines.append(f"- Note: {opp['decision_note']}")
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Programmatic SEO Planner")
    parser.add_argument("--gsc", help="Path to GSC CSV (page, query, impressions, …)")
    parser.add_argument("--sf", help="Path to crawl CSV (Address, Title 1, …)")
    args = parser.parse_args()
    run(gsc_path=args.gsc, sf_path=args.sf)


if __name__ == "__main__":
    main()
