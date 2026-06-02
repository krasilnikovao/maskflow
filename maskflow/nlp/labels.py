PERSON = "person"
ORGANIZATION = "organization"
LOCATION = "location"
ADDRESS = "address"
DOCUMENT = "document"
BANK_ACCOUNT = "bank_account"

DEFAULT_ENTITY_TYPES: tuple[str, ...] = (
    PERSON,
    ORGANIZATION,
    LOCATION,
    ADDRESS,
)

DEFAULT_DETECTION_LABELS: tuple[str, ...] = (
    PERSON,
    "full name",
    ORGANIZATION,
    "company",
    "bank",
    "legal entity",
    "individual entrepreneur",
    LOCATION,
    ADDRESS,
)

PROVIDER_PRIORITIES: dict[str, int] = {
    "spacy": 30,
    "natasha": 20,
    "qwen": 15,
    "gliner": 10,
}

LABEL_ALIASES: dict[str, str] = {
    "PER": PERSON,
    "PERSON": PERSON,
    "FULL_NAME": PERSON,
    "NAME": PERSON,
    "ORG": ORGANIZATION,
    "ORGANIZATION": ORGANIZATION,
    "COMPANY": ORGANIZATION,
    "BANK": ORGANIZATION,
    "BANK_BRANCH": ORGANIZATION,
    "LEGAL_ENTITY": ORGANIZATION,
    "INDIVIDUAL_ENTREPRENEUR": ORGANIZATION,
    "LOC": LOCATION,
    "LOCATION": LOCATION,
    "GPE": LOCATION,
    "ADDRESS": ADDRESS,
    "DOCUMENT": DOCUMENT,
    "BANK_ACCOUNT": BANK_ACCOUNT,
}


def normalize_entity_type(label: str) -> str:
    normalized = label.strip().replace("-", "_").replace(" ", "_").upper()
    return LABEL_ALIASES.get(normalized, normalized.lower())
