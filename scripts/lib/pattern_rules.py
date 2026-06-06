from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

INTENT_RULES: dict[str, list[str]] = {
    "transactional": [r"\bbuy\b", r"\bbook\b", r"\breserv", r"\bprice\b", r"\bprecio\b", r"\bhire\b"],
    "commercial": [r"\bbest\b", r"\btop\b", r"\bvs\b", r"\bcompany\b", r"\bstudio\b", r"\bagency\b", r"\bservicio"],
    "navigational": [r"\blogin\b", r"\bcontact\b", r"\babout\b", r"\bbrand\b"],
    "local": [r"\bnear me\b", r"\blocal\b", r"\bin [a-z]+\b"],
    "informational": [r"\bwhat\b", r"\bhow\b", r"\bguide\b", r"\bguia\b", r"\bcomo\b", r"\bideas\b", r"\bcost\b"],
}


def classify_intent(text: str) -> str:
    value = text.lower()
    scores: dict[str, int] = {}
    for intent, patterns in INTENT_RULES.items():
        score = sum(1 for p in patterns if re.search(p, value))
        if score:
            scores[intent] = score
    if not scores:
        return "mixed"
    return max(scores, key=scores.get)


def normalize_terms(value: str) -> set[str]:
    tokens = []
    for part in str(value).lower().replace("-", " ").replace("/", " ").split():
        token = "".join(ch for ch in part if ch.isalnum())
        if len(token) > 3:
            tokens.append(token)
    return set(tokens)


def slugify(text: str, max_len: int = 60) -> str:
    import unicodedata

    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len].rstrip("-")


def url_path(url: str) -> str:
    path = urlparse(str(url)).path or "/"
    return path if path.endswith("/") else path + "/"


def classify_landing_kind(path: str, cfg: dict[str, Any]) -> str:
    kinds = cfg.get("url_kinds", {})
    p = path.lower()
    for fragment in kinds.get("ignore_path_contains", []):
        if fragment.lower() in p:
            return "ignore"
    blog_prefix = kinds.get("blog_prefix", "/blog/").lower()
    if blog_prefix in p:
        return "blog"
    for prefix in kinds.get("service_prefixes", []):
        if prefix.lower() in p:
            return "service"
    for hub in kinds.get("hub_paths", []):
        if p.rstrip("/") == hub.lower().rstrip("/"):
            return "hub"
    if p in {"/", ""}:
        return "hub"
    return "other"


@dataclass
class ServiceMatch:
    slug: str
    labels: list[str]
    hub_path: str = "/services/"
    prefer_dedicated_page: bool = True


@dataclass
class LocationMatch:
    slug: str
    labels: list[str]


@dataclass
class QueryContext:
    query: str
    impressions: int
    clicks: int
    avg_position: float
    pages: list[str] = field(default_factory=list)
    intent: str = "mixed"
    service: ServiceMatch | None = None
    location: LocationMatch | None = None
    coverage: float = 0.0
    landing_kind: str = "other"
    best_page: str = ""


def _match_tokens(query: str, token_lists: list[list[str]]) -> bool:
    q = query.lower()
    for tokens in token_lists:
        if any(t.lower() in q for t in tokens):
            return True
    return False


def extract_service_location(query: str, cfg: dict[str, Any]) -> tuple[ServiceMatch | None, LocationMatch | None]:
    variables = cfg.get("variables", {})
    service_hit: ServiceMatch | None = None
    location_hit: LocationMatch | None = None

    for loc in variables.get("locations", []):
        tokens = loc.get("tokens", []) + loc.get("labels", [])
        if _match_tokens(query, [tokens]):
            location_hit = LocationMatch(slug=loc["slug"], labels=loc.get("labels", []))
            break

    for svc in variables.get("services", []):
        tokens = svc.get("tokens", []) + svc.get("labels", [])
        if _match_tokens(query, [tokens]):
            service_hit = ServiceMatch(
                slug=svc["slug"],
                labels=svc.get("labels", []),
                hub_path=svc.get("hub_path", "/services/"),
                prefer_dedicated_page=bool(svc.get("prefer_dedicated_page", True)),
            )
            break

    return service_hit, location_hit


def _regex_any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def match_pattern(ctx: QueryContext, cfg: dict[str, Any]) -> dict[str, Any] | None:
    for pattern in cfg.get("patterns", []):
        if not pattern.get("enabled", True):
            continue
        match_cfg = pattern.get("match", {})
        intents = match_cfg.get("intents")
        if intents and ctx.intent not in intents:
            continue
        if match_cfg.get("requires_service") and not ctx.service:
            continue
        if match_cfg.get("requires_location") and not ctx.location:
            continue
        if match_cfg.get("requires_service") is False and ctx.service:
            continue
        exclude = match_cfg.get("query_exclude_regex", [])
        if exclude and _regex_any(exclude, ctx.query):
            continue
        include = match_cfg.get("query_include_regex", [])
        if include and not _regex_any(include, ctx.query):
            continue
        return pattern
    return None


def build_url(pattern: dict[str, Any], ctx: QueryContext) -> str:
    template = pattern.get("url_template")
    if not template:
        return ""
    url = template
    if ctx.service:
        url = url.replace("{service_slug}", ctx.service.slug)
    if ctx.location:
        url = url.replace("{location_slug}", ctx.location.slug)
    url = url.replace("{query_slug}", slugify(ctx.query))
    return url


def coverage_for_query(query: str, page_url: str, page_titles: dict[str, str]) -> float:
    if not page_url:
        return 0.0
    page_terms = normalize_terms(page_url)
    page_terms.update(normalize_terms(page_titles.get(page_url, "")))
    q_terms = normalize_terms(query)
    if not q_terms:
        return 0.0
    return len(q_terms & page_terms) / len(q_terms)


def apply_decision_rules(
    ctx: QueryContext,
    pattern: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[str, str, dict[str, Any] | None]:
    action = pattern.get("default_action", "create_new")
    note = ""
    forced_pattern: dict[str, Any] | None = None
    thresholds = cfg.get("thresholds", {})

    for rule in cfg.get("decision_rules", []):
        when = rule.get("when", {})
        then = rule.get("then", {})
        ok = True

        if "intents" in when and ctx.intent not in when["intents"]:
            ok = False
        if when.get("matched_service") and not ctx.service:
            ok = False
        if "content_template" in when and pattern.get("content_template") != when["content_template"]:
            ok = False
        if "coverage_gte" in when and ctx.coverage < float(when["coverage_gte"]):
            ok = False
        if "coverage_lt" in when and ctx.coverage >= float(when["coverage_lt"]):
            ok = False
        if "landing_kind" in when and ctx.landing_kind != when["landing_kind"]:
            ok = False
        if "landing_kind_in" in when and ctx.landing_kind not in when["landing_kind_in"]:
            ok = False
        if "impressions_gte" in when and ctx.impressions < int(when["impressions_gte"]):
            ok = False
        if "impressions_lt" in when and ctx.impressions >= int(when["impressions_lt"]):
            ok = False
        if "gsc_pages_gte" in when and len(ctx.pages) < int(when["gsc_pages_gte"]):
            ok = False

        if not ok:
            continue

        if "action" in then:
            action = then["action"]
        if "note" in then:
            note = then["note"]
        if "force_pattern" in then:
            forced_id = then["force_pattern"]
            forced_pattern = next((p for p in cfg.get("patterns", []) if p.get("id") == forced_id), None)

    if len(ctx.pages) >= int(thresholds.get("cannibalization_min_pages", 2)) and action == "create_new":
        action = "consolidate"
        note = note or "Multiple URLs compete for the same query in GSC"

    return action, note, forced_pattern


def score_priority(action: str, ctx: QueryContext, pattern: dict[str, Any], cfg: dict[str, Any]) -> str:
    if action == "ignore":
        return "low"
    scoring = cfg.get("scoring", {})
    boost = int(pattern.get("priority_boost", 0))
    effective_impressions = ctx.impressions + boost * 5

    for level in ("high", "medium", "low"):
        block = scoring.get(level, {})
        if action not in block.get("actions", [action]):
            continue
        if effective_impressions < int(block.get("min_impressions", 0)):
            continue
        if "max_avg_position" in block and ctx.avg_position > float(block["max_avg_position"]):
            continue
        return level
    return "low"
