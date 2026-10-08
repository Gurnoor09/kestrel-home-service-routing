"""Text and metadata preprocessing utilities for Kestrel service routing."""
import re

MOJIBAKE_MAP = {
    'Ã©': 'e',
    'Ã¨': 'e',
    'Ã¢â‚¬â€œ': '-',
    'Ã¢â‚¬Â¦': '...',
    'Ã¢â‚¬â„¢': "'",
    'Ã¢â‚¬Å“': '"',
    'Ã¢â‚¬': '"',
    'Ã': '',
    'Â': '',
}

CANONICAL_TEAM_MAP = {
    'Installations': 'Installs & Demo',
    'Consumables': 'Filters & Consumables'
}

VALID_TEAMS = [
    'Billing',
    'Filters & Consumables',
    'Installs & Demo',
    'Product Advice',
    'Repairs',
    'Returns & Replacement',
    'Warranty Claims'
]


def clean_text(text: str) -> str:
    """Repairs legacy Zoho mojibake, normalizes whitespace and casing."""
    if not isinstance(text, str):
        return ''
    for k, v in MOJIBAKE_MAP.items():
        text = text.replace(k, v)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def map_canonical_team(team_label: str) -> str:
    """Maps historical team labels to current canonical 7 teams."""
    return CANONICAL_TEAM_MAP.get(team_label, team_label)
