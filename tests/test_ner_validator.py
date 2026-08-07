from extractor.ner_validator import NamedEntityValidator


def test_named_entity_validator_accepts_person_like_name():

    validator = NamedEntityValidator()

    assert validator.is_person_name(
        "Jane Sharma",
        "Jane Sharma is the Managing Director.",
    )


def test_named_entity_validator_rejects_company_like_phrase():

    validator = NamedEntityValidator()

    assert not validator.is_person_name(
        "Acme Finance",
        "Acme Finance is a company with a board of directors.",
    )


def test_named_entity_validator_rejects_detail_labels():

    validator = NamedEntityValidator()

    assert not validator.is_person_name(
        "Registered Office",
        "Registered Office Mumbai",
    )
