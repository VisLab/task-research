"""
parse_citation_string_tests.py

Unit tests for parse_citation_string.parse().

All test strings are taken verbatim from task_details.json or are minimal
synthetic variants.  Run with:
    python outputs\\parse_citation_string_tests.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from parse_citation_string import parse

PASS = 0
FAIL = 0


def check(label: str, got, expected, *, contains: bool = False):
    global PASS, FAIL
    ok = (got == expected) if not contains else (expected in (got or ""))
    if ok:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL [{label}]")
        print(f"       expected: {expected!r}")
        print(f"       got:      {got!r}")


def test(description: str, citation: str, **expectations):
    result = parse(citation)
    print(f"TEST: {description}")
    for field, expected_val in expectations.items():
        contains = field.endswith("__contains")
        fname = field.replace("__contains", "")
        got = getattr(result, fname, None)
        check(f"{description} | {fname}", got, expected_val, contains=contains)


# ===========================================================================
# 1. Standard journal article — volume(issue), pages, hyphen in pages
# ===========================================================================
test(
    "Journal: Fazio 1986",
    "Fazio, R. H., Sanbonmatsu, D. M., Powell, M. C., & Kardes, F. R. (1986). "
    "On the automatic activation of attitudes. "
    "*Journal of Personality and Social Psychology*, 50(2), 229-238.",
    authors="Fazio, R. H., Sanbonmatsu, D. M., Powell, M. C., & Kardes, F. R.",
    year=1986,
    title="On the automatic activation of attitudes",
    venue="Journal of Personality and Social Psychology",
    venue_type="journal",
    volume="50",
    issue="2",
    pages="229-238",
    parse_quality="clean_journal",
)

# ===========================================================================
# 2. Journal with en-dash in pages
# ===========================================================================
test(
    "Journal: Reber 1967 en-dash pages",
    "Reber, A. S. (1967). Implicit learning of artificial grammars. "
    "*Journal of Verbal Learning and Verbal Behavior*, 6(6), 855\u2013863.",
    authors="Reber, A. S.",
    year=1967,
    title="Implicit learning of artificial grammars",
    venue="Journal of Verbal Learning and Verbal Behavior",
    venue_type="journal",
    volume="6",
    issue="6",
    pages="855\u2013863",
    parse_quality="clean_journal",
)

# ===========================================================================
# 3. Journal with volume only (no issue in parentheses)
# ===========================================================================
test(
    "Journal: volume-only (no issue)",
    "Rohrmeier, M. A., & Cross, I. (2014). Modelling unsupervised online-learning "
    "of artificial grammars: Linking implicit and statistical learning. "
    "*Consciousness and Cognition*, 27, 155\u2013167.",
    authors="Rohrmeier, M. A., & Cross, I.",
    year=2014,
    venue_type="journal",
    volume="27",
    pages="155\u2013167",
    parse_quality="clean_journal",
)

# ===========================================================================
# 4. Book (italicised title)
# ===========================================================================
test(
    "Book: IAPS manual",
    "Lang, P. J., Bradley, M. M., & Cuthbert, B. N. (1997). "
    "*International Affective Picture System (IAPS): Technical Manual and Affective Ratings*. "
    "NIMH Center for the Study of Emotion and Attention.",
    authors="Lang, P. J., Bradley, M. M., & Cuthbert, B. N.",
    year=1997,
    title="International Affective Picture System (IAPS): Technical Manual and Affective Ratings",
    venue_type="report",   # NIMH = report
    parse_quality="clean_report",
)

# ===========================================================================
# 5. Book chapter with "In *Title* (pp. X–Y). Publisher."
# ===========================================================================
test(
    "Chapter: Bradley & Lang 2007",
    "Bradley, M. M., & Lang, P. J. (2007). "
    "The International Affective Picture System (IAPS) in the study of emotion and attention. "
    "In *Handbook of Emotion Elicitation and Assessment* (pp. 29\u201346). Oxford University Press.",
    authors="Bradley, M. M., & Lang, P. J.",
    year=2007,
    title="The International Affective Picture System (IAPS) in the study of emotion and attention",
    venue="Handbook of Emotion Elicitation and Assessment",
    venue_type="book_chapter",
    pages="29\u201346",
    parse_quality="clean_chapter",
)

# ===========================================================================
# 6. Another book chapter
# ===========================================================================
test(
    "Chapter: Klauer & Musch 2003",
    "Klauer, K. C., & Musch, J. (2003). Affective priming: Findings and theories. "
    "In *The Psychology of Evaluation* (pp. 7\u201349). Lawrence Erlbaum.",
    venue_type="book_chapter",
    venue="The Psychology of Evaluation",
    pages="7\u201349",
    parse_quality="clean_chapter",
)

# ===========================================================================
# 7. Compound citation with [Updated: ...]  — parse first citation only
# ===========================================================================
test(
    "Compound: Hutton & Ettinger 2006 with [Updated: ...]",
    "Hutton, S. B., & Ettinger, U. (2006). The antisaccade task as a research tool "
    "in psychopathology: A critical review. *Psychophysiology*, 43(3), 302\u2013313. "
    "[Updated: Amador, S. C., Hood, A. J., Schiess, M. C., Izor, R., & Sereno, A. B. "
    "(2006). Dissociating cognitive deficits involved in voluntary eye movement "
    "dysfunctions in Parkinson's disease patients. *Neuropsychologia*, 44(8), "
    "1475\u20131482.]",
    authors="Hutton, S. B., & Ettinger, U.",
    year=2006,
    title="The antisaccade task as a research tool in psychopathology: A critical review",
    venue="Psychophysiology",
    venue_type="journal",
    volume="43",
    issue="3",
    pages="302\u2013313",
    parse_quality="clean_journal",
)

# ===========================================================================
# 8. et al. in authors
# ===========================================================================
test(
    "et al. authors",
    "Antoniades, C. A., Ettinger, U., Gaymard, B., et al. (2013). "
    "An internationally standardised antisaccade protocol. "
    "*Vision Research*, 84, 1\u20135.",
    year=2013,
    venue_type="journal",
    venue="Vision Research",
    volume="84",
    parse_quality="clean_journal",
)

# ===========================================================================
# 9. Journal with colon in title
# ===========================================================================
test(
    "Journal: colon in title",
    "Knowlton, B. J., & Squire, L. R. (1996). Artificial grammar learning depends on "
    "implicit acquisition of both abstract and exemplar-specific information. "
    "*Journal of Experimental Psychology: Learning, Memory, and Cognition*, 22(1), 169\u2013181.",
    venue="Journal of Experimental Psychology: Learning, Memory, and Cognition",
    venue_type="journal",
    volume="22",
    issue="1",
    parse_quality="clean_journal",
)

# ===========================================================================
# 10. Journal with ampersand in name
# ===========================================================================
test(
    "Journal: & in name",
    "Vadillo, M. A., Konstantinidis, E., & Shanks, D. R. (2022). "
    "Underpowered samples, false negatives, and unconscious learning. "
    "*Psychonomic Bulletin & Review*, 29, 307\u2013337.",
    venue="Psychonomic Bulletin & Review",
    venue_type="journal",
    volume="29",
    parse_quality="clean_journal",
)

# ===========================================================================
# 11. Year with disambiguator letter
# ===========================================================================
test(
    "Year with letter suffix",
    "Smith, J. (2001a). Title here. *Some Journal*, 10(1), 1-10.",
    year=2001,
    venue_type="journal",
    parse_quality="clean_journal",
)

# ===========================================================================
# 12. Graceful degradation: no year
# ===========================================================================
test(
    "Malformed: no year",
    "Smith, J. Some Book. Publisher.",
    parse_quality="malformed",
    year=None,
)

# ===========================================================================
# 13. DOI already in string
# ===========================================================================
test(
    "Has DOI",
    "Braver, T. S., et al. (2021). The Dual Mechanisms of Cognitive Control Project. "
    "*Journal of Cognitive Neuroscience*. doi:10.1162/jocn_a_01768",
    doi="10.1162/jocn_a_01768",
    parse_quality="has_doi",
    venue_type="journal",
)

# ===========================================================================
# 14. Book — non-report (no report keywords)
# ===========================================================================
test(
    "Book: plain publisher",
    "Reber, A. S. (1993). *Implicit Learning and Tacit Knowledge: An Essay on the "
    "Cognitive Unconscious*. Oxford University Press.",
    year=1993,
    title="Implicit Learning and Tacit Knowledge: An Essay on the Cognitive Unconscious",
    venue_type="book",
    parse_quality="clean_book",
)

# ===========================================================================
# 15. Single-author, colon in journal name
# ===========================================================================
test(
    "Single author, journal with colon",
    "Braver, T. S. (2012). The variable nature of cognitive control: a dual mechanisms "
    "framework. *Trends in Cognitive Sciences*, 16(2), 106-113.",
    authors="Braver, T. S.",
    year=2012,
    venue="Trends in Cognitive Sciences",
    venue_type="journal",
    volume="16",
    issue="2",
    pages="106-113",
    parse_quality="clean_journal",
)

# ===========================================================================
# 16. Journal article without pages (e-pub style)
# ===========================================================================
test(
    "Journal: e-pub no pages",
    "Deng, Y., Wang, S., Fuhrmann, A., et al. (2023). A systematic review of IAPS "
    "around the world. *Brain and Behavior*, 13(7), e3027.",
    year=2023,
    venue_type="journal",
    volume="13",
    issue="7",
    parse_quality="clean_journal",
)

# ===========================================================================
# 17. Saccade paper — simple check
# ===========================================================================
test(
    "Journal: Hallett 1978",
    "Hallett, P. E. (1978). Primary and secondary saccades to goals defined by "
    "instructions. *Vision Research*, 18(11), 1279-1296.",
    authors="Hallett, P. E.",
    year=1978,
    venue="Vision Research",
    volume="18",
    issue="11",
    pages="1279-1296",
)

# ===========================================================================
# 18. Chapter with parenthetical editors "In A. Smith (Ed.), *Title* (pp. x–y)."
# ===========================================================================
test(
    "Chapter: with (Ed.) before book title",
    "Cohen, J. D., & Servan-Schreiber, D. (1992). Context, cortex, and dopamine: "
    "A connectionist approach to behavior and biology in schizophrenia. "
    "In A. Collins & E. Smith (Eds.), *Readings in Cognitive Science* (pp. 100-120). "
    "Morgan Kaufmann.",
    year=1992,
    venue_type="book_chapter",
    pages="100-120",
    parse_quality="clean_chapter",
)

# ===========================================================================
# 19. Highly abbreviated title-only entry (sparse but not malformed)
# ===========================================================================
test(
    "Sparse: book no publisher",
    "Skinner, B. F. (1938). *The Behavior of Organisms: An Experimental Analysis*.",
    year=1938,
    title="The Behavior of Organisms: An Experimental Analysis",
    venue_type="book",
)

# ===========================================================================
# 20. PLoS journal with article-number-style pages
# ===========================================================================
test(
    "Journal: PLoS article number",
    "Wager, T. D., Kang, J., Johnson, T. D., Nichols, T. E., Satpute, A. B., & "
    "Barrett, L. F. (2015). A Bayesian model of category-specific emotional brain "
    "responses. *PLoS Computational Biology*, 11(4), e1004066.",
    year=2015,
    venue="PLoS Computational Biology",
    venue_type="journal",
    volume="11",
    issue="4",
    parse_quality="clean_journal",
)

# ===========================================================================
# Summary
# ===========================================================================
print()
print("=" * 50)
total = PASS + FAIL
print(f"Results: {PASS}/{total} passed, {FAIL} failed")
if FAIL:
    print("SOME TESTS FAILED — fix the parser before continuing.")
    sys.exit(1)
else:
    print("All tests passed.")
