"""Lightweight US ZIP code lookup library."""

import gzip
import json
import re

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from types import MappingProxyType

try:
    __version__ = version('ziplus')
except PackageNotFoundError:
    __version__ = '0.0.0-dev'

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

STATES_LIST = (
    'AK',
    'AL',
    'AR',
    'AZ',
    'CA',
    'CO',
    'CT',
    'DC',
    'DE',
    'FL',
    'GA',
    'HI',
    'IA',
    'ID',
    'IL',
    'IN',
    'KS',
    'KY',
    'LA',
    'MA',
    'MD',
    'ME',
    'MI',
    'MN',
    'MO',
    'MS',
    'MT',
    'NC',
    'ND',
    'NE',
    'NH',
    'NJ',
    'NM',
    'NV',
    'NY',
    'OH',
    'OK',
    'OR',
    'PA',
    'RI',
    'SC',
    'SD',
    'TN',
    'TX',
    'UT',
    'VA',
    'VT',
    'WA',
    'WI',
    'WV',
    'WY',
)

STATES = MappingProxyType(
    {
        'Alabama': 'AL',
        'Alaska': 'AK',
        'Arizona': 'AZ',
        'Arkansas': 'AR',
        'California': 'CA',
        'Colorado': 'CO',
        'Connecticut': 'CT',
        'Delaware': 'DE',
        'District of Columbia': 'DC',
        'Florida': 'FL',
        'Georgia': 'GA',
        'Hawaii': 'HI',
        'Idaho': 'ID',
        'Illinois': 'IL',
        'Indiana': 'IN',
        'Iowa': 'IA',
        'Kansas': 'KS',
        'Kentucky': 'KY',
        'Louisiana': 'LA',
        'Maine': 'ME',
        'Maryland': 'MD',
        'Massachusetts': 'MA',
        'Michigan': 'MI',
        'Minnesota': 'MN',
        'Mississippi': 'MS',
        'Missouri': 'MO',
        'Montana': 'MT',
        'Nebraska': 'NE',
        'Nevada': 'NV',
        'New Hampshire': 'NH',
        'New Jersey': 'NJ',
        'New Mexico': 'NM',
        'New York': 'NY',
        'North Carolina': 'NC',
        'North Dakota': 'ND',
        'Ohio': 'OH',
        'Oklahoma': 'OK',
        'Oregon': 'OR',
        'Pennsylvania': 'PA',
        'Rhode Island': 'RI',
        'South Carolina': 'SC',
        'South Dakota': 'SD',
        'Tennessee': 'TN',
        'Texas': 'TX',
        'Utah': 'UT',
        'Vermont': 'VT',
        'Virginia': 'VA',
        'Washington': 'WA',
        'West Virginia': 'WV',
        'Wisconsin': 'WI',
        'Wyoming': 'WY',
    }
)

_NAME_TO_ABBR: dict[str, str] = {name.upper(): abbr for name, abbr in STATES.items()}
_ABBR_TO_NAME: dict[str, str] = {abbr: name for name, abbr in STATES.items()}

RE_ZIP_PLUS4 = re.compile(r'^(\d{5})-?(\d{4})?$')

# Lazy-loaded dataset singleton
_zipcodes: dict[str, int] | None = None
_dataset_version: str | None = None

# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class StateException(Exception):  # noqa: N818
    """Raised when a state name/abbreviation cannot be resolved."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load() -> None:
    global _zipcodes, _dataset_version  # noqa: PLW0603
    if _zipcodes is not None:
        return
    with gzip.open(Path(__file__).resolve().parent / 'zipcodes.json.gz', 'rb') as gz:
        dataset = json.loads(gz.read().decode('ascii'))
        _dataset_version = dataset.get('version', 'unknown')
        _zipcodes = dataset.get('zipcodes', {})


def _resolve(value: str) -> tuple[str, str] | None:
    """Resolve any state representation to (abbreviation, full_name) or None."""
    upper = value.upper()
    if upper in _ABBR_TO_NAME:
        return upper, _ABBR_TO_NAME[upper]
    if upper in _NAME_TO_ABBR:
        abbr = _NAME_TO_ABBR[upper]
        return abbr, _ABBR_TO_NAME[abbr]
    return None


# ---------------------------------------------------------------------------
# Public API — dataset
# ---------------------------------------------------------------------------


def dataset_version() -> str:
    """Return the dataset version string."""
    _load()
    return _dataset_version  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Public API — validation
# ---------------------------------------------------------------------------


def is_valid(zipcode: str) -> bool:
    """Return True if zipcode matches 5-digit or ZIP+4 format."""
    return bool(RE_ZIP_PLUS4.match(zipcode))


# ---------------------------------------------------------------------------
# Public API — ZIP lookup
# ---------------------------------------------------------------------------


def get_state(zipcode: str, *, abbr: bool = True) -> str | None:
    """Look up state for a US ZIP code. Returns abbreviation or full name."""
    _load()
    if not is_valid(zipcode):
        msg = f'{zipcode} is not a valid US ZIP code'
        raise ValueError(msg)
    st_idx = _zipcodes.get(zipcode[:5])
    if st_idx is None:
        return None
    state_abbr = STATES_LIST[st_idx]
    return state_abbr if abbr else _ABBR_TO_NAME[state_abbr]


# ---------------------------------------------------------------------------
# Public API — conversion
# ---------------------------------------------------------------------------


def state_to_abbr(state: str, default: str | None = None, *, raise_exception: bool = False) -> str | None:
    """Convert full state name to abbreviation."""
    upper = state.upper()
    if upper in _NAME_TO_ABBR:
        return _NAME_TO_ABBR[upper]
    if raise_exception:
        msg = f'Unknown state name: {state}'
        raise StateException(msg)
    return default


def abbr_to_state(abbr: str, default: str | None = None, *, raise_exception: bool = False) -> str | None:
    """Convert state abbreviation to full name."""
    upper = abbr.upper()
    if upper in _ABBR_TO_NAME:
        return _ABBR_TO_NAME[upper]
    if raise_exception:
        msg = f'Unknown state abbreviation: {abbr}'
        raise StateException(msg)
    return default


# ---------------------------------------------------------------------------
# Public API — normalization
# ---------------------------------------------------------------------------


def norm_to_abbr(value: str, default: str | None = None, *, raise_exception: bool = False) -> str | None:
    """Normalize any state representation to its abbreviation."""
    resolved = _resolve(value)
    if resolved is not None:
        return resolved[0]
    if raise_exception:
        msg = f'Unknown state: {value}'
        raise StateException(msg)
    return default


def norm_to_state(value: str, default: str | None = None, *, raise_exception: bool = False) -> str | None:
    """Normalize any state representation to its full name."""
    resolved = _resolve(value)
    if resolved is not None:
        return resolved[1]
    if raise_exception:
        msg = f'Unknown state: {value}'
        raise StateException(msg)
    return default


# ---------------------------------------------------------------------------
# Public API — formatting
# ---------------------------------------------------------------------------


def format_state(value: str, *, raise_exception: bool = False) -> str:
    """Return properly cased state: abbreviation stays uppercase, full name gets title case."""
    upper = value.upper()
    if upper in _NAME_TO_ABBR:
        return _ABBR_TO_NAME[_NAME_TO_ABBR[upper]]
    if upper in _ABBR_TO_NAME:
        return upper
    if raise_exception:
        msg = f'Unknown state: {value}'
        raise StateException(msg)
    return value


# ---------------------------------------------------------------------------
# Public API — predicates
# ---------------------------------------------------------------------------


def is_state(value: str) -> bool:
    """Return True if value is any valid state representation."""
    return _resolve(value) is not None


def is_state_full(state: str) -> bool:
    """Return True if value is a full state name."""
    return state.upper() in _NAME_TO_ABBR


def is_state_abbr(abbr: str) -> bool:
    """Return True if value is a state abbreviation."""
    return abbr.upper() in _ABBR_TO_NAME
