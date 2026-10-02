#!/usr/bin/env python3
"""reference-lookup: an MCP server (stdio) that checks whether references are real.

Standard library only. It asks two public, keyless services: OpenAlex (api.openalex.org) for
works by DOI or title, and arXiv (export.arxiv.org) for arXiv ids. What leaves the machine is the
reference's identifiers and title, or the search words Claude composes for search_works; the two
services see the request like any web request (address, user agent). Nothing is stored anywhere.

Tools: verify_reference, verify_bibtex, lookup_reference, search_works, citation_neighbours.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

OPENALEX = "https://api.openalex.org/works"
ARXIV = "https://export.arxiv.org/api/query"
UA = "research-desk-reference-lookup/0.2 (Claude plugin; +https://github.com/najikay/claude-research-skills)"
FIELDS = "id,title,doi,publication_year,cited_by_count,authorships,primary_location,referenced_works"
PAUSE_S = 0.25  # polite spacing between OpenAlex calls
ARXIV_PAUSE_S = 3.0  # arXiv asks for one request every three seconds
REQUEST_TIMEOUT_S = 10
BATCH_DEADLINE_S = 150  # verify_bibtex returns what it has by then
_last_arxiv_call = 0.0
NS = {"a": "http://www.w3.org/2005/Atom"}
PROTOCOL_VERSION = "2025-06-18"
INFO = {"name": "reference-lookup", "version": "0.2.1"}
INSTRUCTIONS = (
    "Check references against OpenAlex and arXiv. verify_reference takes one reference "
    "(title, authors, year, doi, arxiv) and returns verified / mismatch / not_found / unchecked "
    "with the reasons; verify_bibtex does the same for a whole .bib text. lookup_reference turns "
    "a DOI, arXiv id or OpenAlex id into clean metadata; search_works finds candidate papers by "
    "words; citation_neighbours lists what a paper cites and what cites it."
)


# -- HTTP (replaceable in tests) ----------------------------------------------------------------
def fetch(url: str, params: dict[str, str] | None = None) -> tuple[int, str]:
    """GET → (status, body). Network errors come back as (0, message); never raises.

    arXiv calls are spaced three seconds apart (its API terms); a 429 or 503 from either
    service is retried once after the Retry-After it names (default 5 s).
    """
    global _last_arxiv_call
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    if url.startswith(ARXIV):
        wait = ARXIV_PAUSE_S - (time.monotonic() - _last_arxiv_call)
        if wait > 0:
            time.sleep(wait)
        _last_arxiv_call = time.monotonic()
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, text/xml"})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as r:  # noqa: S310 - https to two known hosts
                return r.status, r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt == 1:
                try:
                    delay = float(e.headers.get("Retry-After") or 5)
                except ValueError:
                    delay = 5.0
                time.sleep(min(max(delay, 1.0), 30.0))
                continue
            return e.code, ""
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            return 0, str(e)[:160]
    return 0, "retry failed"


def doi_path(doi: str) -> str:
    """A DOI as it goes into the OpenAlex URL: prefix stripped, spaces removed, reserved characters escaped."""
    d = re.sub(r"^\s*(https?://(dx\.)?doi\.org/|doi:)\s*", "", doi.strip(), flags=re.I).replace(" ", "")
    return urllib.parse.quote(d, safe="/")


# -- matching ------------------------------------------------------------------------------------
LATEX_ACCENTS = {
    r"\\\"": "\u0308", r"\\'": "\u0301", r"\\`": "\u0300", r"\\^": "\u0302", r"\\~": "\u0303",
    r"\\c": "\u0327", r"\\v": "\u030c", r"\\=": "\u0304", r"\\.": "\u0307", r"\\u": "\u0306", r"\\H": "\u030b",
}


def delatex(t: str) -> str:
    """Turn LaTeX accents ({\\"u}, \\'e, {\\ss}) into plain characters and drop stray braces."""
    out = t
    for cmd, mark in LATEX_ACCENTS.items():
        out = re.sub(r"\{?" + cmd + r"\{?([A-Za-z])\}?\}?", lambda m, mark=mark: m.group(1) + mark, out)
    out = out.replace("{\\ss}", "ß").replace("\\ss", "ß").replace("{\\o}", "ø").replace("{\\O}", "Ø").replace("{\\ae}", "æ").replace("{\\l}", "ł")
    return re.sub(r"[{}]", "", unicodedata.normalize("NFC", out))


def fold(t: str) -> str:
    """Lowercase, accents stripped (NFKD minus combining marks), so Müller == Muller."""
    t = unicodedata.normalize("NFKD", delatex(t)).lower()
    return "".join(c for c in t if not unicodedata.combining(c))


def _norm_title(t: str) -> list[str]:
    return [w for w in re.sub(r"[^\w ]+", " ", fold(t), flags=re.UNICODE).replace("_", " ").split() if len(w) > 1]


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


SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "phd", "md"}


def surname(name: str) -> str:
    """Family name, folded: 'Vaswani, Ashish', 'Ashish Vaswani', 'King Jr., Martin' → vaswani / king."""
    name = fold(name)
    if "," in name:
        family = name.split(",")[0]
        parts = [w for w in re.sub(r"[.]", " ", family).split() if w not in SUFFIXES]
        return parts[-1] if parts else ""
    parts = [w for w in re.sub(r"[.]", " ", name).split() if w not in SUFFIXES]
    return parts[-1] if parts else ""


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
        doi = (e.findtext("arxiv:doi", default="", namespaces={"arxiv": "http://arxiv.org/schemas/atom"}) or "").strip()
        out.append(
            {
                "id": aid,
                "title": title,
                "publication_year": int(published) if published.isdigit() else None,
                "authorships": [
                    {"author": {"display_name": " ".join((n.text or "").split())}}
                    for n in e.findall("a:author/a:name", NS)
                ],
                "doi": f"https://doi.org/{doi}" if doi else None,
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
        # a year alone is weak evidence (preprint, proceedings and journal records differ; indexes date
        # reposts), so with the title and first author agreeing it makes the verdict partial, not wrong
        (problems if problems else notes).append(f"year {year} here, {found_year} there")
    if not mine:
        notes.append("no authors given, so only the title was compared")
    status = "mismatch" if problems else ("partial" if notes else "verified")
    return {
        "status": status,
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


STATUS_ORDER = {"verified": 3, "partial": 2, "mismatch": 1}


def verify_reference(ref: dict) -> dict:
    """Look one reference up: by DOI, then arXiv id, then title; every candidate is judged."""
    steps: list[tuple[str, str, dict]] = []
    if ref.get("doi"):
        steps.append(("doi", f"{OPENALEX}/https://doi.org/{doi_path(str(ref['doi']))}", {"select": FIELDS}))
    if ref.get("arxiv"):
        aid = re.sub(r"v\d+$", "", re.sub(r"^(arxiv:|https?://arxiv\.org/abs/)", "", str(ref["arxiv"]).strip(), flags=re.I))
        steps.append(("arxiv", ARXIV, {"id_list": aid, "max_results": "1"}))
    if ref.get("title"):
        steps.append(("title", OPENALEX, {"search": str(ref["title"]), "select": FIELDS, "per-page": "10"}))
    if not steps:
        return {"status": "unchecked", "problems": ["nothing to look up: give a title, a DOI or an arXiv id"]}
    best: dict | None = None
    failures: list[str] = []
    identifier_problem: str | None = None  # a DOI or arXiv id that resolves to some other paper
    identifier_note: str | None = None  # a DOI or arXiv id the service does not know
    for i, (how, url, params) in enumerate(steps):
        if i:
            time.sleep(PAUSE_S)
        status, body = fetch(url, params)
        if status == 404:
            if how in ("doi", "arxiv"):  # not proof the identifier is wrong (coverage gaps), so a note
                identifier_note = f"the {'DOI' if how == 'doi' else 'arXiv id'} given is unknown to {'OpenAlex' if how == 'doi' else 'arXiv'}; matched by title instead"
            continue  # try the next way
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
        if how in ("doi", "arxiv") and cands and ref.get("title") and all(judge(ref, c, how) is None for c in cands):
            other = str(cands[0].get("title") or "?")
            identifier_problem = f"the {'DOI' if how == 'doi' else 'arXiv id'} given points to another paper: \u201c{other}\u201d"
        for c in cands:
            v = judge(ref, c, how)
            if v is not None and (best is None or _rank(v) > _rank(best)):
                best = v
        if best is not None and best["status"] == "verified":
            break
    if best is None:
        if failures:
            return {"status": "unchecked", "problems": failures + ([identifier_problem] if identifier_problem else [])}
        return {"status": "not_found", "by": ", then ".join(h for h, _, _ in steps), "problems": ([identifier_problem] if identifier_problem else []) + ["no work with a similar title was found"]}
    if identifier_problem:  # the paper exists, but the identifier in the reference is wrong: never 'verified'
        best = {**best, "status": "mismatch", "problems": [identifier_problem, *best["problems"]]}
    elif identifier_note and best["status"] == "verified":
        best = {**best, "status": "partial", "notes": [identifier_note, *best["notes"]]}
    return best


# -- bibtex ----------------------------------------------------------------------------------------
def _balanced(text: str, start: int) -> int:
    """Index just past the brace block that opens at ``start`` (text[start] == '{'), or -1."""
    depth, i = 0, start
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def _split_entries(text: str) -> list[tuple[str, str, str]]:
    """(kind, citekey, body) for every @entry{key, ...}; @comment and @preamble are skipped, @string collected."""
    out = []
    pos = 0
    head = re.compile(r"@(\w+)\s*(?=[{(])")
    while True:
        m = head.search(text, pos)
        if not m:
            break
        kind = m.group(1).lower()
        open_at = m.end()
        end = _balanced(text, open_at) if text[open_at] == "{" else text.find(")", open_at) + 1
        if end <= 0:
            pos = open_at + 1
            continue
        pos = end  # whatever sits inside this block (an @entry inside an @comment) is not an entry
        inner = text[open_at + 1 : end - 1]
        if kind in ("comment", "preamble"):
            continue
        if kind == "string":
            out.append((kind, "", inner))
            continue
        km = re.match(r"\s*([^,\s]+)\s*,", inner)
        if not km:
            continue
        out.append((kind, km.group(1), inner[km.end() :]))
    return out


def _fields(body: str, strings: dict[str, str]) -> dict[str, str]:
    """name = {value} | "value" | bare, with nested braces kept whole and @string names expanded."""
    fields: dict[str, str] = {}
    i = 0
    while i < len(body):
        m = re.compile(r"\s*(\w+)\s*=\s*").match(body, i)
        if not m:
            nxt = body.find(",", i)
            if nxt < 0:
                break
            i = nxt + 1
            continue
        name, i = m.group(1).lower(), m.end()
        parts: list[str] = []
        while i < len(body):
            if body[i] == "{":
                end = _balanced(body, i)
                if end < 0:
                    end = len(body)
                parts.append(body[i + 1 : end - 1])
                i = end
            elif body[i] == '"':
                j = i + 1
                while j < len(body) and body[j] != '"':
                    j += 2 if body[j] == "\\" else 1
                parts.append(body[i + 1 : j])
                i = j + 1
            else:
                bm = re.compile(r"\s*([^,#{}\"]+)").match(body, i)
                raw = (bm.group(1).strip() if bm else "")
                parts.append(strings.get(raw.lower(), raw))
                i = bm.end() if bm else len(body)
            tail = re.compile(r"\s*#\s*").match(body, i)
            if tail:  # "a" # "b" concatenation
                i = tail.end()
                continue
            break
        value = "".join(parts)
        fields[name] = delatex(value).strip()
        nxt = body.find(",", i)
        if nxt < 0:
            break
        i = nxt + 1
    return fields


def parse_bibtex(text: str) -> list[dict]:
    """A small .bib parser: braces, quotes, nesting, @string macros; @comment and @preamble are ignored.

    Duplicate citekeys are kept (each gets a ``duplicate_of`` note) so the caller can report them.
    """
    strings: dict[str, str] = {}
    out: list[dict] = []
    seen: dict[str, int] = {}
    for kind, key, body in _split_entries(text):
        if kind == "string":
            for sm in re.finditer(r"(\w+)\s*=\s*(\{[^{}]*\}|\"[^\"]*\")", body):
                strings[sm.group(1).lower()] = sm.group(2)[1:-1]
            continue
        fields = _fields(body, strings)
        eprint = fields.get("eprint", "")
        is_arxiv = "arxiv" in fields.get("archiveprefix", "").lower() or bool(re.match(r"^\d{4}\.\d{4,5}", eprint))
        ref = {
            "citekey": key,
            "kind": kind,
            "title": fields.get("title"),
            "authors": author_list(fields.get("author", "")),
            "year": fields.get("year"),
            "doi": fields.get("doi"),
            "arxiv": eprint if (eprint and is_arxiv) else None,
            "venue": fields.get("journal") or fields.get("booktitle"),
        }
        if key in seen:
            ref["duplicate_of"] = key
        seen[key] = seen.get(key, 0) + 1
        out.append(ref)
    return out


def verify_bibtex(text: str, limit: int = 60) -> dict:
    """Every entry (up to ``limit``) gets its own verdict; one bad entry never spoils the batch.

    The batch stops at ``BATCH_DEADLINE_S`` and says how many entries it did not reach.
    """
    refs = parse_bibtex(text)
    skipped = max(0, len(refs) - limit)
    refs = refs[:limit]
    rows = []
    t0 = time.monotonic()
    stopped = None
    for i, ref in enumerate(refs):
        if time.monotonic() - t0 > BATCH_DEADLINE_S:
            stopped = f"stopped after {i} entries: time limit; call again with the rest"
            break
        if i:
            time.sleep(PAUSE_S)
        try:
            v = verify_reference(ref)
        except Exception as e:  # noqa: BLE001 - one odd entry is reported, the others go on
            v = {"status": "unchecked", "problems": [f"could not check: {type(e).__name__}: {str(e)[:120]}"]}
        if ref.get("duplicate_of"):
            v = {**v, "problems": [f"duplicate citekey {ref['citekey']}", *v.get("problems", [])]}
        rows.append({"citekey": ref["citekey"], "title": ref.get("title"), **v})
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    out = {"entries": len(refs), "counts": counts, "results": rows}
    if stopped:
        out["stopped"] = stopped
    if skipped:
        out["skipped"] = f"{skipped} entries beyond the first {limit} were not checked"
    return out


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
        status, body = fetch(f"{OPENALEX}/https://doi.org/{doi_path(doi)}", {"select": FIELDS})
    elif re.fullmatch(r"(?:https://openalex\.org/)?W\d+", ident):
        status, body = fetch(f"{OPENALEX}/{ident.rsplit('/', 1)[-1]}", {"select": FIELDS})
    elif re.search(r"\d{4}\.\d{4,5}", ident):
        aid = re.search(r"(\d{4}\.\d{4,5})", ident).group(1)
        status, body = fetch(ARXIV, {"id_list": aid, "max_results": "1"})
        recs = parse_arxiv(body) if status == 200 else []
        if not recs:
            return {"found": False, "ident": ident, "problem": "arXiv has no such id" if status == 200 else f"arXiv: {body or 'HTTP ' + str(status)}"}
        r = recs[0]
        return {"found": True, "ident": ident, "title": r["title"], "authors": [a["author"]["display_name"] for a in r["authorships"]], "year": r["publication_year"], "venue": "arXiv", "arxiv": r["arxiv"], "doi": (r.get("doi") or "").replace("https://doi.org/", "") or None, "url": r["id"]}
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
        "Check one reference against OpenAlex (by DOI, then title) and arXiv (by arXiv id). Returns status verified (title, first author and year agree) | partial (title agrees; the year is off or no authors were given) | mismatch (wrong first author or title, or a DOI/arXiv id that points elsewhere) | not_found | unchecked (the services could not be asked), with the matched record and the reasons. Give as much as you have; a generic title alone is weak evidence.",
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
        limit = args.get("limit", 8)
        return json.dumps(search_works(str(args.get("query") or ""), int(8 if limit is None else limit)), ensure_ascii=False, indent=1)
    if name == "citation_neighbours":
        refs = args.get("refs", 10)
        cites = args.get("cites", 8)
        return json.dumps(citation_neighbours(str(args.get("ident") or ""), int(10 if refs is None else refs), int(8 if cites is None else cites)), ensure_ascii=False, indent=1)
    raise ValueError(f"unknown tool: {name}")


def handle(msg: Any) -> dict | None:
    """One JSON-RPC message → a response, or None for a notification. Never raises."""
    if not isinstance(msg, dict):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "a request must be a JSON object"}}
    rid, method, params = msg.get("id"), msg.get("method", ""), msg.get("params")
    if params is None:
        params = {}
    if rid is None:
        return None  # a notification (initialized, cancelled, progress): nothing to answer
    if not isinstance(params, dict):
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "params must be an object"}}
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": INFO, "instructions": INSTRUCTIONS}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = str(params.get("name", ""))
        if name not in {t["name"] for t in TOOLS}:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": f"unknown tool: {name}"}}
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "arguments must be an object"}}
        try:
            text = call(name, dict(arguments))
        except Exception as e:  # noqa: BLE001 - a tool error is an answer, not a crash
            return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}], "isError": True}}
        return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": text}], "isError": False}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"method not found: {method}"}}


def main() -> None:
    """Newline-delimited JSON-RPC over stdin/stdout, as the MCP stdio transport specifies.

    UTF-8 on both pipes whatever the platform's default (Windows consoles default to a code page),
    and no input can stop the loop: bad JSON gets -32700, anything else an error answer.
    """
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
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
        try:
            out = handle(msg)
        except Exception as e:  # noqa: BLE001 - the loop must survive anything
            rid = msg.get("id") if isinstance(msg, dict) else None
            out = {"jsonrpc": "2.0", "id": rid, "error": {"code": -32603, "message": f"internal error: {type(e).__name__}"}}
        if out is not None:
            sys.stdout.write(json.dumps(out, ensure_ascii=True) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
