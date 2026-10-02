#!/usr/bin/env python3
"""reference-lookup: an MCP server (stdio) that checks whether references are real.

Standard library only. It asks two public, keyless services: OpenAlex (api.openalex.org) for
works by DOI or title, and arXiv (export.arxiv.org) for arXiv ids. Only the reference's own
identifiers and title leave the machine; nothing is stored anywhere.

Tools: verify_reference, verify_bibtex, lookup_reference, search_works, citation_neighbours.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

OPENALEX = "https://api.openalex.org/works"
ARXIV = "https://export.arxiv.org/api/query"
UA = "research-desk-reference-lookup/0.2 (Claude plugin; +https://github.com/najikay/claude-research-skills)"
FIELDS = "id,title,doi,publication_year,cited_by_count,authorships,primary_location,referenced_works"
PAUSE_S = 0.2  # polite spacing between calls
NS = {"a": "http://www.w3.org/2005/Atom"}
PROTOCOL_VERSION = "2025-06-18"
INFO = {"name": "reference-lookup", "version": "0.2.0"}
INSTRUCTIONS = (
    "Check references against OpenAlex and arXiv. verify_reference takes one reference "
    "(title, authors, year, doi, arxiv) and returns verified / mismatch / not_found / unchecked "
    "with the reasons; verify_bibtex does the same for a whole .bib text. lookup_reference turns "
    "a DOI, arXiv id or OpenAlex id into clean metadata; search_works finds candidate papers by "
    "words; citation_neighbours lists what a paper cites and what cites it."
)


# -- HTTP (replaceable in tests) ----------------------------------------------------------------
def fetch(url: str, params: dict[str, str] | None = None) -> tuple[int, str]:
    """GET → (status, body). Network errors come back as (0, message)."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, text/xml"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 - https to two known hosts
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return 0, str(e)[:160]


# -- matching ------------------------------------------------------------------------------------
def _norm_title(t: str) -> list[str]:
    return [w for w in re.sub(r"[^a-z0-9 ]+", " ", t.lower()).split() if len(w) > 1]


def title_similarity(a: str, b: str) -> float:
    """Token overlap of two titles in [0, 1]; letters-only similarity rescues hyphen/spelling variants."""
    la, lb = _norm_title(a), _norm_title(b)
    ta, tb = set(la), set(lb)
    if not ta or not tb:
        return 0.0
    joined = difflib.SequenceMatcher(None, "".join(la), "".join(lb), autojunk=False).ratio()
    return max(len(ta & tb) / len(ta | tb), joined if joined >= 0.9 else 0.0)


def author_list(v: Any) -> list[str]:
    """Authors as a list from a list, an 'A and B' string, 'A; B' or one name."""
    if isinstance(v, str):
        parts = re.split(r"\s+and\s+|;|\n", v) if (" and " in v or ";" in v or "\n" in v) else [v]
        return [p.strip() for p in parts if p.strip()]
    return [str(a).strip() for a in (v or []) if str(a).strip()]


def year_of(v: Any) -> int | None:
    """The four-digit year in 2021, '2021', '2021/22' or 'n.d.' (None when none)."""
    m = re.search(r"(?<!\d)(1[6-9]\d\d|20\d\d)(?!\d)", str(v or ""))
    return int(m.group(1)) if m else None


def surname(name: str) -> str:
    """Last word of a name, lowercased ('Vaswani, Ashish' and 'Ashish Vaswani' both give vaswani)."""
    if "," in name:
        return name.split(",")[0].strip().split()[-1].lower() if name.split(",")[0].strip() else ""
    parts = re.sub(r"[.]", " ", name).split()
    return parts[-1].lower() if parts else ""


def parse_arxiv(xml: str) -> list[dict]:
    """arXiv Atom feed → OpenAlex-shaped records."""
    try:
        root = ET.fromstring(xml)  # noqa: S314 - feed from export.arxiv.org over https
    except ET.ParseError:
        return []
    out = []
    for e in root.findall("a:entry", NS):
        title = " ".join((e.findtext("a:title", default="", namespaces=NS) or "").split())
        if not title or title == "Error":
            continue
        aid = (e.findtext("a:id", default="", namespaces=NS) or "").strip()
        published = (e.findtext("a:published", default="", namespaces=NS) or "")[:4]
        out.append(
            {
                "id": aid,
                "title": title,
                "publication_year": int(published) if published.isdigit() else None,
                "authorships": [
                    {"author": {"display_name": " ".join((n.text or "").split())}}
                    for n in e.findall("a:author/a:name", NS)
                ],
                "doi": None,
                "arxiv": re.sub(r"^https?://arxiv\.org/abs/", "", aid),
            }
        )
    return out


def judge(ref: dict, work: dict, how: str) -> dict | None:
    """Compare a reference with one record; None when the titles are unrelated."""
    score = title_similarity(str(ref.get("title") or ""), str(work.get("title") or ""))
    if score < 0.6:
        return None
    problems: list[str] = []
    notes: list[str] = []
    if score < 0.9:
        problems.append(f"title differs: found “{work.get('title')}”")
    year, found_year = year_of(ref.get("year")), year_of(work.get("publication_year"))
    mine = surname((author_list(ref.get("authors")) or [""])[0])
    theirs = [surname((a.get("author") or {}).get("display_name") or "") for a in work.get("authorships") or []]
    if mine and theirs and mine not in theirs:
        problems.append(f"first author “{author_list(ref.get('authors'))[0]}” is not among the authors found")
    if year and found_year and abs(year - found_year) > 1:
        # a year alone is weak evidence (preprint, proceedings and journal records differ; indexes date reposts)
        (problems if problems else notes).append(f"year {year} here, {found_year} there")
    return {
        "status": "mismatch" if problems else "verified",
        "by": how,
        "score": round(score, 2),
        "matched_title": work.get("title"),
        "matched_year": found_year,
        "matched_id": work.get("id"),
        "matched_doi": (work.get("doi") or "").replace("https://doi.org/", "") or None,
        "problems": problems,
        "notes": notes,
    }


def _rank(v: dict) -> tuple[int, int, float]:
    return (-len(v["problems"]), -len(v["notes"]), v["score"])


def verify_reference(ref: dict) -> dict:
    """Look one reference up: by DOI, then arXiv id, then title; every candidate is judged."""
    steps: list[tuple[str, str, dict]] = []
    if ref.get("doi"):
        doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", str(ref["doi"]).strip())
        steps.append(("doi", f"{OPENALEX}/https://doi.org/{doi}", {"select": FIELDS}))
    if ref.get("arxiv"):
        aid = re.sub(r"v\d+$", "", re.sub(r"^(arxiv:|https?://arxiv\.org/abs/)", "", str(ref["arxiv"]).strip(), flags=re.I))
        steps.append(("arxiv", ARXIV, {"id_list": aid, "max_results": "1"}))
    if ref.get("title"):
        steps.append(("title", OPENALEX, {"search": str(ref["title"]), "select": FIELDS, "per-page": "10"}))
    if not steps:
        return {"status": "unchecked", "problems": ["nothing to look up: give a title, a DOI or an arXiv id"]}
    best: dict | None = None
    failures: list[str] = []
    for i, (how, url, params) in enumerate(steps):
        if i:
            time.sleep(PAUSE_S)
        status, body = fetch(url, params)
        if status == 404:
            continue  # unknown identifier there: try the next way
        if status == 0 or status >= 400:
            failures.append(f"{'arXiv' if how == 'arxiv' else 'OpenAlex'}: {'HTTP ' + str(status) if status else body}")
            continue
        if how == "arxiv":
            cands = parse_arxiv(body)
        else:
            try:
                data = json.loads(body)
            except ValueError:
                failures.append("OpenAlex: unreadable answer")
                continue
            cands = data.get("results") or ([data] if data.get("title") else [])
        for c in cands:
            v = judge(ref, c, how)
            if v is not None and (best is None or _rank(v) > _rank(best)):
                best = v
        if best is not None and best["status"] == "verified":
            break
    if best is None:
        if failures:
            return {"status": "unchecked", "problems": failures}
        return {"status": "not_found", "by": ", then ".join(h for h, _, _ in steps), "problems": ["no work with a similar title was found"]}
    return best


# -- bibtex ----------------------------------------------------------------------------------------
def _split_entries(text: str) -> list[tuple[str, str, str]]:
    """(kind, citekey, body) for every @entry{key, ...} with balanced braces (one line or many)."""
    out = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        if depth == 0:
            out.append((m.group(1), m.group(2), text[m.end() : i - 1]))
    return out


def parse_bibtex(text: str) -> list[dict]:
    """A small .bib parser: entries with braces or quotes; good enough for the common cases."""
    out = []
    for kind, key, body in _split_entries(text):
        fields: dict[str, str] = {}
        for fm in re.finditer(r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|[^,\n]+)", body):
            val = fm.group(2).strip().strip(",").strip()
            if (val.startswith("{") and val.endswith("}")) or (val.startswith('"') and val.endswith('"')):
                val = val[1:-1]
            fields[fm.group(1).lower()] = re.sub(r"[{}]", "", val).strip()
        eprint = fields.get("eprint", "")
        is_arxiv = "arxiv" in fields.get("archiveprefix", "").lower() or bool(re.match(r"^\d{4}\.\d{4,5}", eprint))
        out.append(
            {
                "citekey": key,
                "kind": kind.lower(),
                "title": fields.get("title"),
                "authors": author_list(fields.get("author", "")),
                "year": fields.get("year"),
                "doi": fields.get("doi"),
                "arxiv": eprint if (eprint and is_arxiv) else None,
                "venue": fields.get("journal") or fields.get("booktitle"),
            }
        )
    return out


def verify_bibtex(text: str, limit: int = 60) -> dict:
    refs = parse_bibtex(text)[:limit]
    rows = []
    for i, ref in enumerate(refs):
        if i:
            time.sleep(PAUSE_S)
        v = verify_reference(ref)
        rows.append({"citekey": ref["citekey"], "title": ref.get("title"), **v})
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"entries": len(refs), "counts": counts, "results": rows}


# -- lookups --------------------------------------------------------------------------------------
def _work_record(w: dict) -> dict:
    loc = w.get("primary_location") or {}
    return {
        "openalex_id": str(w.get("id") or "").rsplit("/", 1)[-1],
        "title": w.get("title") or "",
        "authors": [((a.get("author") or {}).get("display_name") or "") for a in (w.get("authorships") or [])],
        "year": w.get("publication_year"),
        "venue": (loc.get("source") or {}).get("display_name"),
        "doi": (w.get("doi") or "").replace("https://doi.org/", "") or None,
        "cited_by": w.get("cited_by_count") or 0,
        "url": loc.get("landing_page_url") or w.get("id"),
    }


def lookup_reference(ident: str) -> dict:
    ident = ident.strip()
    if re.search(r"10\.\d{4,9}/\S+", ident):
        doi = re.search(r"(10\.\d{4,9}/\S+)", ident).group(1)
        status, body = fetch(f"{OPENALEX}/https://doi.org/{doi}", {"select": FIELDS})
    elif re.fullmatch(r"(?:https://openalex\.org/)?W\d+", ident):
        status, body = fetch(f"{OPENALEX}/{ident.rsplit('/', 1)[-1]}", {"select": FIELDS})
    elif re.search(r"\d{4}\.\d{4,5}", ident):
        aid = re.search(r"(\d{4}\.\d{4,5})", ident).group(1)
        status, body = fetch(ARXIV, {"id_list": aid, "max_results": "1"})
        recs = parse_arxiv(body) if status == 200 else []
        if not recs:
            return {"found": False, "ident": ident, "problem": "arXiv has no such id" if status == 200 else f"arXiv: {body or 'HTTP ' + str(status)}"}
        r = recs[0]
        return {"found": True, "ident": ident, "title": r["title"], "authors": [a["author"]["display_name"] for a in r["authorships"]], "year": r["publication_year"], "venue": "arXiv", "arxiv": r["arxiv"], "url": r["id"]}
    else:
        return {"found": False, "ident": ident, "problem": "give a DOI (10.xxxx/...), an arXiv id (2504.20339) or an OpenAlex id (W...)"}
    if status == 404:
        return {"found": False, "ident": ident, "problem": "OpenAlex has no such work"}
    if status != 200:
        return {"found": False, "ident": ident, "problem": f"OpenAlex: {'HTTP ' + str(status) if status else body}"}
    return {"found": True, "ident": ident, **_work_record(json.loads(body))}


def search_works(query: str, limit: int = 8) -> dict:
    status, body = fetch(OPENALEX, {"search": query, "select": FIELDS, "per-page": str(max(1, min(limit, 25)))})
    if status != 200:
        return {"query": query, "results": [], "problem": f"OpenAlex: {'HTTP ' + str(status) if status else body}"}
    return {"query": query, "results": [_work_record(w) for w in json.loads(body).get("results") or []]}


def citation_neighbours(ident: str, refs: int = 10, cites: int = 8) -> dict:
    base = lookup_reference(ident)
    if not base.get("found") or not base.get("openalex_id"):
        return {"ident": ident, "problem": base.get("problem") or "only DOIs and OpenAlex ids have a citation graph here"}
    wid = base["openalex_id"]
    status, body = fetch(f"{OPENALEX}/{wid}", {"select": FIELDS})
    work = json.loads(body) if status == 200 else {}
    ref_ids = [str(x).rsplit("/", 1)[-1] for x in (work.get("referenced_works") or [])][: max(0, min(refs, 50))]
    references: list[dict] = []
    if ref_ids:
        time.sleep(PAUSE_S)
        s2, b2 = fetch(OPENALEX, {"filter": "openalex:" + "|".join(ref_ids), "select": FIELDS, "per-page": "50"})
        if s2 == 200:
            references = [_work_record(w) for w in json.loads(b2).get("results") or []]
    citing: list[dict] = []
    if cites > 0:
        time.sleep(PAUSE_S)
        s3, b3 = fetch(OPENALEX, {"filter": f"cites:{wid}", "sort": "cited_by_count:desc", "select": FIELDS, "per-page": str(max(1, min(cites, 25)))})
        if s3 == 200:
            citing = [_work_record(w) for w in json.loads(b3).get("results") or []]
    return {"paper": base, "references": references, "cited_by": citing, "cited_by_total": work.get("cited_by_count")}


# -- MCP over stdio ---------------------------------------------------------------------------------
def _tool(name: str, desc: str, props: dict, required: list[str] | None = None) -> dict:
    schema: dict = {"type": "object", "properties": props, "additionalProperties": False}
    if required:
        schema["required"] = required
    return {"name": name, "description": desc, "inputSchema": schema}


TOOLS = [
    _tool(
        "verify_reference",
        "Check one reference against OpenAlex (by DOI, then title) and arXiv (by arXiv id). Returns status verified | mismatch | not_found | unchecked, the matched record, and the problems (wrong first author, title or year). Give as much as you have.",
        {
            "title": {"type": "string"},
            "authors": {"type": "array", "items": {"type": "string"}, "description": "author names, first author first"},
            "year": {"type": ["string", "integer"]},
            "doi": {"type": "string"},
            "arxiv": {"type": "string", "description": "arXiv id like 2504.20339"},
        },
    ),
    _tool("verify_bibtex", "Check every entry of a BibTeX text (up to 60) and return a verdict per citekey plus counts.", {"bibtex": {"type": "string"}}, ["bibtex"]),
    _tool("lookup_reference", "Clean metadata (title, authors, year, venue, DOI) for a DOI, arXiv id or OpenAlex id.", {"ident": {"type": "string"}}, ["ident"]),
    _tool("search_works", "Find candidate papers by words in the title (OpenAlex). Use to resolve a vague reference before verifying it.", {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 25}}, ["query"]),
    _tool("citation_neighbours", "What a paper cites (its first references) and the most-cited papers citing it, for a DOI or OpenAlex id.", {"ident": {"type": "string"}, "refs": {"type": "integer", "minimum": 0, "maximum": 50}, "cites": {"type": "integer", "minimum": 0, "maximum": 25}}, ["ident"]),
]


def call(name: str, args: dict) -> str:
    if name == "verify_reference":
        return json.dumps(verify_reference(args), ensure_ascii=False, indent=1)
    if name == "verify_bibtex":
        return json.dumps(verify_bibtex(str(args.get("bibtex") or "")), ensure_ascii=False, indent=1)
    if name == "lookup_reference":
        return json.dumps(lookup_reference(str(args.get("ident") or "")), ensure_ascii=False, indent=1)
    if name == "search_works":
        return json.dumps(search_works(str(args.get("query") or ""), int(args.get("limit") or 8)), ensure_ascii=False, indent=1)
    if name == "citation_neighbours":
        return json.dumps(citation_neighbours(str(args.get("ident") or ""), int(args.get("refs") or 10), int(args.get("cites") or 8)), ensure_ascii=False, indent=1)
    raise ValueError(f"unknown tool: {name}")


def handle(msg: dict) -> dict | None:
    """One JSON-RPC message → a response, or None for a notification."""
    rid, method, params = msg.get("id"), msg.get("method", ""), msg.get("params") or {}
    if rid is None:
        return None
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": params.get("protocolVersion") or PROTOCOL_VERSION, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": INFO, "instructions": INSTRUCTIONS}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        try:
            text = call(str(params.get("name", "")), dict(params.get("arguments") or {}))
        except Exception as e:  # noqa: BLE001 - a tool error is an answer, not a crash
            return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}], "isError": True}}
        return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": text}], "isError": False}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"method not found: {method}"}}


def main() -> None:
    """Newline-delimited JSON-RPC over stdin/stdout, as the MCP stdio transport specifies."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}) + "\n")
            sys.stdout.flush()
            continue
        out = handle(msg)
        if out is not None:
            sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
