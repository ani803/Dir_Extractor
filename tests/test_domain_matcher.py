from search.domain_matcher import DomainMatcher
from search.validators import WebsiteValidator


def test_domain_matcher_scores_correct_domain_higher_than_social_or_wiki():

    company = "SUNDARAM FINANCE LIMITED"

    correct = DomainMatcher.score(company, "https://www.sundaramfinance.in/about")
    linkedin = DomainMatcher.score(company, "https://www.linkedin.com/company/sundaram-finance")
    wikipedia = DomainMatcher.score(company, "https://en.wikipedia.org/wiki/Sundaram_Finance")

    assert correct > linkedin
    assert correct > wikipedia


def test_domain_matcher_handles_compound_domain_names():

    score = DomainMatcher.score("MUTHOOT FINCORP LIMITED", "https://www.muthootfincorp.com/")

    assert score > 0.4


def test_domain_matcher_returns_zero_for_unrelated_domain():

    score = DomainMatcher.score("ACME FINANCE LIMITED", "https://www.totallyunrelatedsite.org")

    assert score < 0.2


def test_website_validator_blocks_subdomains_of_bad_domains():

    validator = WebsiteValidator()

    assert validator.validate("https://in.linkedin.com/company/example") is False
    assert validator.validate("https://www.zaubacorp.com/company/EXAMPLE") is False
    assert validator.validate("https://www.moneycontrol.com/company/example") is False


def test_website_validator_does_not_false_positive_on_substring_domains():
    """
    A naive substring check ('linkedin.com' in domain) would incorrectly
    block a legitimate domain that merely contains a blocked name as a
    substring, e.g. a company actually named "notlinkedin.com".
    """

    validator = WebsiteValidator()

    assert validator.validate("https://www.notlinkedin.com") is True
    assert validator.validate("https://www.example.com") is True
