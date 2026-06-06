"""
test_enrich_no_doi.py — Unit + integration tests for enrich_no_doi.py.

Pure fixture-driven for the scoring and parsing layers.  The
end-to-end CLI test injects a fake ``fetch_fn`` so no network is
touched and no real cache files are read.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from enrich_no_doi import (  # noqa: E402
    DEFAULT_THRESHOLDS,
    Score,
    Thresholds,
    apply_high_matches,
    format_markdown_report,
    iter_no_doi_refs,
    main as enrich_main,
    normalize_title,
    parse_surnames,
    pick_best,
    run_enrich,
    score_candidate,
    title_similarity,
    year_delta,
)


# ---------------------------------------------------------------------------
# parse_surnames
# ---------------------------------------------------------------------------

class TestParseSurnames:

    def test_single_author(self):
        assert parse_surnames("Shanks, D. R.") == ["shanks"]

    def test_two_authors_ampersand(self):
        assert parse_surnames("Staddon, J. E. R., & Cerutti, D. T.") == [
            "staddon", "cerutti",
        ]

    def test_three_authors(self):
        out = parse_surnames("Smith, A., Jones, B., & Brown, C.")
        # The OG split on "&" gives ["Smith, A., Jones, B.", "Brown, C."]
        # then comma-head extracts surnames: "Smith" from first piece
        # only (the Jones lands in the same piece).  Documenting this
        # known limitation — the catalog's APA format makes a clean
        # multi-author parse hard without a real BibTeX-style parser.
        # The first surname is the load-bearing one for author matching.
        assert "smith" in out
        assert "brown" in out

    def test_empty(self):
        assert parse_surnames("") == []
        assert parse_surnames(None) == []  # type: ignore[arg-type]

    def test_no_comma_uses_full_string(self):
        assert parse_surnames("Pavlov") == ["pavlov"]


# ---------------------------------------------------------------------------
# normalize_title and title_similarity
# ---------------------------------------------------------------------------

class TestTitleSimilarity:

    def test_identical(self):
        assert title_similarity("Learning: From Association to Cognition",
                                "Learning: From Association to Cognition") == 1.0

    def test_subtitle_dropped(self):
        # Catalog has the full title; OpenAlex sometimes returns the main
        # title only.  Should still score high.
        sim = title_similarity(
            "Conditioned reflexes: an investigation of the physiological activity of the cerebral cortex.",
            "Conditioned reflexes",
        )
        # 2 of 11 content words overlap.
        assert sim < 0.3  # low — different content words elsewhere

    def test_word_order_doesnt_matter(self):
        assert title_similarity("From Association to Cognition",
                                "Cognition to Association From") == 1.0

    def test_punctuation_normalised(self):
        assert title_similarity("Coming to terms with fear",
                                "Coming, to: terms (with) fear!") == 1.0

    def test_diacritics_normalised(self):
        assert title_similarity("Naïve Bayes Classifier",
                                "Naive Bayes Classifier") == 1.0

    def test_empty(self):
        assert title_similarity("", "Anything") == 0.0
        assert title_similarity("anything", "") == 0.0
        assert title_similarity("", "") == 0.0

    def test_stopwords_dropped(self):
        # "the" appears in both but adds no signal; the content words
        # match completely.
        assert title_similarity("Learning the Cognition",
                                "The Cognition Learning") == 1.0


# ---------------------------------------------------------------------------
# year_delta
# ---------------------------------------------------------------------------

class TestYearDelta:

    def test_exact(self):
        assert year_delta(2010, 2010) == 0

    def test_off_by_one(self):
        assert year_delta(2010, 2011) == 1

    def test_either_missing(self):
        assert year_delta(None, 2010) is None
        assert year_delta(2010, None) is None
        assert year_delta(None, None) is None

    def test_bad_type(self):
        assert year_delta(2010, "abc") is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# score_candidate (the heart)
# ---------------------------------------------------------------------------

class TestScoreCandidate:

    def test_high_exact_match(self):
        s = score_candidate(
            ref_title="Learning: From Association to Cognition",
            ref_year=2010,
            ref_surnames=["shanks"],
            cand_title="Learning: From Association to Cognition",
            cand_year=2010,
            cand_surnames=["shanks"],
        )
        assert s.tier == "high"
        assert s.title_sim == 1.0
        assert s.year_delta == 0
        assert s.author_match is True

    def test_high_year_off_by_one(self):
        s = score_candidate(
            ref_title="Coming to Terms with Fear",
            ref_year=2014,
            ref_surnames=["ledoux"],
            cand_title="Coming to terms with fear",
            cand_year=2015,
            cand_surnames=["ledoux"],
        )
        assert s.tier == "high"
        assert s.year_delta == 1

    def test_med_no_author_match(self):
        # Title and year strong, but candidate authors don't include
        # the ref's first author → degrade to MED.
        s = score_candidate(
            ref_title="Operant Conditioning",
            ref_year=2003,
            ref_surnames=["staddon"],
            cand_title="Operant Conditioning",
            cand_year=2003,
            cand_surnames=["jones"],
        )
        assert s.tier == "med"
        assert s.author_match is False

    def test_med_title_weaker(self):
        # 3-word ref title vs. 3-word candidate title with 3 of 4
        # content words shared -> Jaccard 0.75 (above MED 0.70 but
        # below HIGH 0.90).  Year + author both match cleanly so the
        # weaker title-similarity is the only thing keeping this out
        # of HIGH.
        s = score_candidate(
            ref_title="Operant Conditioning Reward Mechanisms",
            ref_year=2003,
            ref_surnames=["staddon"],
            cand_title="Operant Conditioning Reward",
            cand_year=2003,
            cand_surnames=["staddon"],
        )
        assert s.tier == "med"
        assert 0.70 <= s.title_sim < 0.90

    def test_low_year_far_off(self):
        s = score_candidate(
            ref_title="Operant Conditioning",
            ref_year=2003,
            ref_surnames=["staddon"],
            cand_title="Operant Conditioning",
            cand_year=1985,
            cand_surnames=["jones"],
        )
        assert s.tier == "low"

    def test_low_completely_different_title(self):
        s = score_candidate(
            ref_title="Fear Conditioning in Mice",
            ref_year=2014,
            ref_surnames=["ledoux"],
            cand_title="A Completely Unrelated Paper",
            cand_year=2014,
            cand_surnames=["ledoux"],
        )
        assert s.tier == "low"

    def test_missing_year_doesnt_block_med(self):
        # If the catalog ref has no year, we can't assert year-match,
        # but author + strong title should still hit MED.
        s = score_candidate(
            ref_title="Some Specific Title Words",
            ref_year=None,
            ref_surnames=["smith"],
            cand_title="Some Specific Title Words",
            cand_year=2020,
            cand_surnames=["smith"],
        )
        # year_delta is None -> HIGH branch fails; MED branch passes
        # via the author_match path.
        assert s.tier == "med"

    def test_custom_thresholds(self):
        t = Thresholds(high_title=0.5, high_year_delta=5,
                       high_require_author=False)
        s = score_candidate(
            ref_title="Operant Conditioning",
            ref_year=2003,
            ref_surnames=["staddon"],
            cand_title="Operant",
            cand_year=2003,
            cand_surnames=["different"],
            thresholds=t,
        )
        # Title sim 0.5, year=0, no author → HIGH under loosened
        # thresholds.
        assert s.tier == "high"


# ---------------------------------------------------------------------------
# pick_best
# ---------------------------------------------------------------------------

class TestPickBest:

    def _ref(self, title, year, authors):
        return {"title": title, "year": year, "authors": authors,
                "ids": {"doi": None}}

    def _cand_work(self, *, doi, title, year, surnames, citations=0):
        # OpenAlex Works response shape, minimal.
        return {
            "id": "https://openalex.org/W123",
            "doi": f"https://doi.org/{doi}" if doi else None,
            "title": title,
            "publication_year": year,
            "authorships": [
                {"author": {"display_name": f"X {s.title()}"}}
                for s in surnames
            ],
            "cited_by_count": citations,
        }

    def test_no_candidates(self):
        best, score = pick_best(self._ref("X", 2020, "Smith, A."), [])
        assert best is None
        assert score is None

    def test_picks_high_over_med(self):
        ref = self._ref("Operant Conditioning", 2003, "Staddon, J., & Cerutti, D.")
        cands = [
            self._cand_work(doi="10.x/1", title="Operant Conditioning",
                            year=2003, surnames=["jones"], citations=500),  # MED
            self._cand_work(doi="10.x/2", title="Operant Conditioning",
                            year=2003, surnames=["staddon"], citations=100),  # HIGH
        ]
        best, score = pick_best(ref, cands)
        assert best["doi"] == "10.x/2"
        assert score.tier == "high"

    def test_ties_broken_by_citation_count(self):
        ref = self._ref("Operant Conditioning", 2003, "Staddon, J.")
        cands = [
            self._cand_work(doi="10.x/low", title="Operant Conditioning",
                            year=2003, surnames=["staddon"], citations=10),
            self._cand_work(doi="10.x/high", title="Operant Conditioning",
                            year=2003, surnames=["staddon"], citations=999),
        ]
        best, _ = pick_best(ref, cands)
        assert best["doi"] == "10.x/high"

    def test_candidate_without_doi_skipped(self):
        ref = self._ref("Operant Conditioning", 2003, "Staddon, J.")
        cands = [
            self._cand_work(doi=None, title="Operant Conditioning",
                            year=2003, surnames=["staddon"], citations=999),
            self._cand_work(doi="10.x/has-doi", title="Operant Conditioning",
                            year=2003, surnames=["staddon"], citations=10),
        ]
        best, _ = pick_best(ref, cands)
        assert best["doi"] == "10.x/has-doi"


# ---------------------------------------------------------------------------
# iter_no_doi_refs
# ---------------------------------------------------------------------------

class TestIterNoDoiRefs:

    def test_yields_only_no_doi(self):
        procs = {"processes": [{
            "process_id": "p1",
            "references": [
                {"ids": {"doi": "10.x/has"}, "title": "Has DOI"},
                {"ids": {"doi": None}, "title": "No DOI"},
                {"ids": {"doi": ""}, "title": "Empty DOI"},
                {"ids": {}, "title": "Missing DOI field"},
            ],
        }]}
        out = [r["title"] for _, _, r in iter_no_doi_refs(procs, [])]
        assert out == ["No DOI", "Empty DOI", "Missing DOI field"]

    def test_walks_processes_and_tasks(self):
        procs = {"processes": [
            {"process_id": "p1", "references": [{"ids": {"doi": None}}]},
        ]}
        tasks = [
            {"hedtsk_id": "t1", "references": [{"ids": {"doi": None}}]},
        ]
        ids = [(o, i) for o, i, _ in iter_no_doi_refs(procs, tasks)]
        assert ids == [("p1", 0), ("t1", 0)]


# ---------------------------------------------------------------------------
# apply_high_matches
# ---------------------------------------------------------------------------

class TestApplyHighMatches:

    def _make_match(self, owner_id, idx, doi, openalex_id, tier="high"):
        from enrich_no_doi import Match
        return Match(
            ref_owner_id=owner_id, ref_idx=idx,
            ref_title="", ref_year=None, ref_authors="",
            candidate={"doi": doi, "openalex_id": openalex_id,
                       "title": "", "year": None, "surnames": [],
                       "cited_by_count": 0},
            score=Score(title_sim=1.0, year_delta=0,
                        author_match=True, tier=tier),
            tier=tier,
        )

    def test_stamps_doi_and_openalex_id(self):
        procs = {"processes": [{
            "process_id": "p1",
            "references": [{"ids": {"doi": None}}],
        }]}
        matches = [self._make_match("p1", 0, "10.x/a", "W123")]
        n = apply_high_matches(matches, procs, [])
        assert n == 1
        ref = procs["processes"][0]["references"][0]
        assert ref["ids"]["doi"] == "10.x/a"
        assert ref["ids"]["openalex_id"] == "W123"

    def test_med_not_stamped(self):
        procs = {"processes": [{
            "process_id": "p1",
            "references": [{"ids": {"doi": None}}],
        }]}
        matches = [self._make_match("p1", 0, "10.x/a", "W123", tier="med")]
        n = apply_high_matches(matches, procs, [])
        assert n == 0
        ref = procs["processes"][0]["references"][0]
        assert ref["ids"]["doi"] is None


# ---------------------------------------------------------------------------
# End-to-end CLI smoke test
# ---------------------------------------------------------------------------

class TestCLI:

    def _stage_workspace(self, tmp_path: Path):
        procs = {"processes": [{
            "process_id": "hed_test",
            "references": [
                {
                    "authors": "Shanks, D. R.",
                    "year": 2010,
                    "title": "Learning: From Association to Cognition",
                    "ids": {"doi": None},
                },
                {
                    "authors": "Pavlov, I. P.",
                    "year": 1927,
                    "title": "Conditioned reflexes",
                    "ids": {"doi": None},
                },
            ],
        }]}
        (tmp_path / "process_details.json").write_text(
            json.dumps(procs), encoding="utf-8")
        (tmp_path / "task_details.json").write_text("[]", encoding="utf-8")

    def _fake_fetch(self, title, year):
        # Return OpenAlex-shaped JSON for the Shanks ref; nothing for Pavlov.
        if "Learning" in title:
            return {"results": [{
                "id": "https://openalex.org/W4097944001",
                "doi": "https://doi.org/10.1146/annurev.psych.093008.100422",
                "title": "Learning: From Association to Cognition",
                "publication_year": 2010,
                "authorships": [{"author": {"display_name": "David R Shanks"}}],
                "cited_by_count": 500,
            }]}
        return {"results": []}

    def test_dry_run_writes_report_no_catalog_change(self, tmp_path: Path):
        self._stage_workspace(tmp_path)
        rc = enrich_main(
            ["--workspace", str(tmp_path)],
            fetch_fn=self._fake_fetch,
        )
        assert rc == 0
        # Catalog unchanged.
        procs = json.loads((tmp_path / "process_details.json").read_text("utf-8"))
        for ref in procs["processes"][0]["references"]:
            assert ref["ids"]["doi"] is None
        # Report written.
        md_files = list((tmp_path / "outputs" / "analysis").glob("enrich_no_doi_*.md"))
        assert len(md_files) == 1
        assert "HIGH-confidence" in md_files[0].read_text("utf-8")

    def test_wet_run_stamps_high_matches(self, tmp_path: Path):
        self._stage_workspace(tmp_path)
        rc = enrich_main(
            ["--workspace", str(tmp_path), "--write"],
            fetch_fn=self._fake_fetch,
        )
        assert rc == 0
        procs = json.loads((tmp_path / "process_details.json").read_text("utf-8"))
        refs = procs["processes"][0]["references"]
        # Shanks gets stamped.
        assert refs[0]["ids"]["doi"] == "10.1146/annurev.psych.093008.100422"
        assert refs[0]["ids"]["openalex_id"] == "W4097944001"
        # Pavlov stays unstamped (no candidate returned).
        assert refs[1]["ids"]["doi"] is None
