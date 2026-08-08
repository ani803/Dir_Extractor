from extractor.candidate_finder import CandidateFinder
from models import PersonCard


def test_candidate_finder_does_not_let_board_heading_swallow_name():

    card = PersonCard(
        text="Board of Directors Jane Sharma is the Managing Director.",
        html="",
        source_url="https://example.com/board",
    )

    candidates = CandidateFinder().find([card])

    assert [candidate.name for candidate in candidates] == ["Jane Sharma"]
    assert candidates[0].designation == "Managing Director"


def test_candidate_finder_finds_name_after_designation():

    card = PersonCard(
        text="Managing Director Jane Sharma leads the company.",
        html="",
        source_url="https://example.com/team",
    )

    candidates = CandidateFinder().find([card])

    assert any(candidate.name == "Jane Sharma" for candidate in candidates)


def test_candidate_finder_cleans_honorifics_from_director_names():

    card = PersonCard(
        text="Dr. Rajiv Mehta - Independent Director DIN 01234567 Profile Details",
        html="",
        source_url="https://example.com/directors",
    )

    candidates = CandidateFinder().find([card])

    assert [candidate.name for candidate in candidates] == ["Rajiv Mehta"]


def test_candidate_finder_ignores_unrelated_capitalized_details():

    card = PersonCard(
        text=(
            "Board of Directors Registered Office Mumbai Compliance Committee "
            "Jane Sharma serves as the Managing Director."
        ),
        html="",
        source_url="https://example.com/governance",
    )

    candidates = CandidateFinder().find([card])

    assert [candidate.name for candidate in candidates] == ["Jane Sharma"]


def test_candidate_finder_attaches_only_one_name_per_title_occurrence():
    """
    A single title match's +/-120 char window can contain more than one
    capitalized phrase that superficially "relates" to it (e.g. two names
    sitting close together in flattened table text). Only the single
    best-ranked name should become a candidate for that title -- not every
    name in the window -- or the same title gets attached to several
    different (mostly wrong) people.
    """

    card = PersonCard(
        text="Rakesh Kumar Sunita Rao is the Director of the company.",
        html="",
        source_url="https://example.com/board",
    )

    candidates = CandidateFinder().find([card])

    assert len(candidates) == 1
    assert candidates[0].designation == "Director"
