from extractor.title_matcher import TitleMatcher


def test_title_matcher_prefers_longer_specific_titles():

    matches = TitleMatcher().find(
        "Jane Sharma is the Managing Director and a member of the board."
    )

    assert matches[0].title == "Managing Director"
    assert all(match.title != "Director" for match in matches)


def test_title_matcher_normalizes_hyphenated_titles():

    matches = TitleMatcher().find("Rajiv Mehta, Non Executive Director")

    assert matches[0].title == "Non-Executive Director"
