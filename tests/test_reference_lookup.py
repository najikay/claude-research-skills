"""Offline tests for the reference-lookup server: every HTTP call is replaced by a fake."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SERVER = Path(__file__).resolve().parents[1] / "servers" / "reference_lookup" / "server.py"
spec = importlib.util.spec_from_file_location("reference_lookup", SERVER)
rl = importlib.util.module_from_spec(spec)
sys.modules["reference_lookup"] = rl
spec.loader.exec_module(rl)


def work(wid, title, year, authors, doi=None, cited=5, refs=()):
    return {
        "id": f"https://openalex.org/{wid}",
        "title": title,
        "publication_year": year,
        "cited_by_count": cited,
        "doi": f"https://doi.org/{doi}" if doi else None,
        "authorships": [{"author": {"display_name": a}} for a in authors],
        "primary_location": {"landing_page_url": f"https://x/{wid}", "source": {"display_name": "J"}},
        "referenced_works": [f"https://openalex.org/{r}" for r in refs],
    }


ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><entry>
<id>http://arxiv.org/abs/2007.11898v2</id><published>2020-07-23T10:00:00Z</published>
<title>ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM</title>
<author><name>Carlos Campos</name></author><author><name>Richard Elvira</name></author></entry></feed>"""


@pytest.fixture
def fake(monkeypatch):
    calls = []
    works = {
        "W1": work("W1", "Attention Is All You Need", 2025, ["Ashish Vaswani", "Noam Shazeer"], "10.65215/2q58a426", 26678),
        "W2": work("W2", "Attention Is All You Need", 2017, ["Ashish Vaswani", "Noam Shazeer"], None, 100),
        "W3": work("W3", "Deep Residual Learning for Image Recognition", 2016, ["Kaiming He", "Xiangyu Zhang"], "10.1109/cvpr.2016.90", 200000, refs=["W1", "W2"]),
        "W4": work("W4", "Attention Is All You Need In Speech Separation", 2021, ["Cem Subakan"], None, 600),
    }

    def fetch(url, params=None):
        calls.append((url, params or {}))
        monkeypatch.setattr(rl.time, "sleep", lambda s: None)
        if "doi.org/10.1109/cvpr.2016.90" in url.lower():  # OpenAlex matches DOIs case-insensitively
            return 200, json.dumps(works["W3"])
        if "doi.org/10.9999/dead" in url:
            return 404, ""
        if "doi.org/10.9999/down" in url:
            return 503, ""
        if url.endswith("/W3"):
            return 200, json.dumps(works["W3"])
        if url == rl.ARXIV:
            return (200, ATOM) if params.get("id_list") == "2007.11898" else (200, "<feed xmlns='http://www.w3.org/2005/Atom'></feed>")
        f = params.get("filter", "")
        if f.startswith("openalex:"):
            return 200, json.dumps({"results": [works[i] for i in f.split(":", 1)[1].split("|") if i in works]})
        if f.startswith("cites:"):
            return 200, json.dumps({"results": [works["W4"]]})
        q = params.get("search", "").lower()
        if "attention" in q:
            return 200, json.dumps({"results": [works["W1"], works["W4"], works["W2"]]})
        if "residual" in q:
            return 200, json.dumps({"results": [works["W3"]]})
        return 200, json.dumps({"results": []})

    monkeypatch.setattr(rl, "fetch", fetch)
    monkeypatch.setattr(rl.time, "sleep", lambda s: None)
    return calls


def test_verify_picks_the_agreeing_record_and_explains_mismatches(fake):
    v = rl.verify_reference({"title": "Attention Is All You Need", "authors": ["Ashish Vaswani"], "year": 2017})
    assert v["status"] == "verified" and v["matched_year"] == 2017 and v["notes"] == []  # not the 2025 repost
    v = rl.verify_reference({"title": "Deep Residual Learning for Image Recognition", "authors": ["Yann LeCun"], "year": 2009})
    assert v["status"] == "mismatch" and len(v["problems"]) == 2  # wrong first author, then the year counts too
    assert "LeCun" in v["problems"][0] and "2009" in v["problems"][1]
    v = rl.verify_reference({"title": "Attention Is All You Need", "authors": "Ashish Vaswani and Noam Shazeer", "year": "2025"})
    assert v["status"] == "verified" and v["matched_year"] == 2025
    v = rl.verify_reference({"title": "Telepathic Consensus Among Quantum Drone Swarms", "authors": ["Nobody Real"], "year": 2024})
    assert v["status"] == "not_found" and "title" in v["by"]
    # DOI first; a dead DOI falls back to the title; a failing service is 'unchecked', never 'not found'
    v = rl.verify_reference({"doi": "https://doi.org/10.1109/CVPR.2016.90", "title": "Deep Residual Learning for Image Recognition", "authors": ["Kaiming He"], "year": 2016})
    assert v["status"] == "verified" and v["by"] == "doi" and v["matched_doi"] == "10.1109/cvpr.2016.90"
    v = rl.verify_reference({"doi": "10.9999/dead", "title": "Deep Residual Learning for Image Recognition", "authors": ["Kaiming He"], "year": 2016})
    assert v["status"] == "verified" and v["by"] == "title"
    v = rl.verify_reference({"doi": "10.9999/down"})
    assert v["status"] == "unchecked" and "HTTP 503" in v["problems"][0]
    v = rl.verify_reference({"arxiv": "arXiv:2007.11898v2", "title": "ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual–Inertial, and Multimap SLAM", "authors": ["Carlos Campos"], "year": 2021})
    assert v["status"] == "verified" and v["by"] == "arxiv"
    assert rl.verify_reference({})["status"] == "unchecked"


def test_bibtex_parsing_and_batch_verdicts(fake):
    bib = """
@inproceedings{vaswani2017attention,
  title = {Attention Is All You Need},
  author = {Vaswani, Ashish and Shazeer, Noam},
  booktitle = {NeurIPS},
  year = {2017}
}
@article{he2016deep, title="Deep Residual Learning for Image Recognition", author="He, Kaiming and Zhang, Xiangyu", journal="CVPR", year=2016, doi={10.1109/CVPR.2016.90}}
@misc{campos2021orbslam3, title={ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM}, author={Campos, Carlos}, year={2021}, eprint={2007.11898}, archivePrefix={arXiv}}
@article{fake2024, title={Telepathic Consensus Among Quantum Drone Swarms}, author={Real, Nobody}, journal={Nature}, year={2024}}
"""
    refs = rl.parse_bibtex(bib)
    assert [r["citekey"] for r in refs] == ["vaswani2017attention", "he2016deep", "campos2021orbslam3", "fake2024"]
    assert refs[0]["authors"] == ["Vaswani, Ashish", "Shazeer, Noam"] and refs[1]["doi"] == "10.1109/CVPR.2016.90"
    assert refs[2]["arxiv"] == "2007.11898" and refs[3]["venue"] == "Nature"
    out = rl.verify_bibtex(bib)
    assert out["entries"] == 4 and out["counts"] == {"verified": 3, "not_found": 1}
    assert [r["status"] for r in out["results"]] == ["verified", "verified", "verified", "not_found"]


def test_lookup_search_and_neighbours(fake):
    r = rl.lookup_reference("https://doi.org/10.1109/CVPR.2016.90")
    assert r["found"] and r["title"].startswith("Deep Residual") and r["authors"][0] == "Kaiming He" and r["venue"] == "J"
    assert rl.lookup_reference("10.9999/dead") == {"found": False, "ident": "10.9999/dead", "problem": "OpenAlex has no such work"}
    a = rl.lookup_reference("2007.11898")
    assert a["found"] and a["venue"] == "arXiv" and a["arxiv"] == "2007.11898v2"
    assert not rl.lookup_reference("hello")["found"]
    s = rl.search_works("attention is all you need", limit=3)
    assert [x["openalex_id"] for x in s["results"]] == ["W1", "W4", "W2"]
    n = rl.citation_neighbours("10.1109/CVPR.2016.90", refs=5, cites=3)
    assert n["paper"]["openalex_id"] == "W3" and [x["openalex_id"] for x in n["references"]] == ["W1", "W2"]
    assert n["cited_by"][0]["openalex_id"] == "W4" and n["cited_by_total"] == 200000


def test_jsonrpc_surface(fake):
    init = rl.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
    assert init["result"]["serverInfo"]["name"] == "reference-lookup" and init["result"]["capabilities"]["tools"] == {"listChanged": False}
    assert rl.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    tools = rl.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
    assert [t["name"] for t in tools] == ["verify_reference", "verify_bibtex", "lookup_reference", "search_works", "citation_neighbours"]
    assert all(t["inputSchema"]["type"] == "object" for t in tools)
    r = rl.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "verify_reference", "arguments": {"title": "Attention Is All You Need", "authors": ["Ashish Vaswani"], "year": 2017}}})
    assert r["result"]["isError"] is False and json.loads(r["result"]["content"][0]["text"])["status"] == "verified"
    bad = rl.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "nope", "arguments": {}}})
    assert bad["result"]["isError"] is True and "unknown tool" in bad["result"]["content"][0]["text"]
    assert rl.handle({"jsonrpc": "2.0", "id": 5, "method": "resources/list"})["error"]["code"] == -32601
    assert rl.handle({"jsonrpc": "2.0", "id": 6, "method": "ping"})["result"] == {}


def test_helpers():
    assert rl.surname("Vaswani, Ashish") == "vaswani" and rl.surname("Ashish Vaswani") == "vaswani" and rl.surname("") == ""
    assert rl.year_of("2021/22") == 2021 and rl.year_of("n.d.") is None and rl.year_of(1999) == 1999
    assert rl.author_list("A B and C D") == ["A B", "C D"] and rl.author_list(["x", " "]) == ["x"]
    assert rl.title_similarity("Multi-Map SLAM", "Multimap SLAM") >= 0.9 and rl.title_similarity("", "x") == 0.0
    assert rl.parse_arxiv("not xml") == [] and rl.parse_arxiv(ATOM)[0]["arxiv"] == "2007.11898v2"
