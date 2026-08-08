from verifier.designation_validator import DesignationValidator


def test_designation_validator_rejects_officer_only_titles():

    validator = DesignationValidator()

    assert not validator.is_valid("Chief Executive Officer")
    assert not validator.is_valid("Company Secretary")
    assert not validator.is_valid("Chief Financial Officer")


def test_designation_validator_allows_explicit_director_officer_combo():

    validator = DesignationValidator()

    assert validator.is_valid("Managing Director and CEO")
    assert validator.is_valid("Director and Company Secretary")
