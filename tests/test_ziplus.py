from unittest.mock import patch

import pytest

import ziplus

from ziplus import (
    StateException,
    abbr_to_state,
    dataset_version,
    format_state,
    get_state,
    is_state,
    is_state_abbr,
    is_state_full,
    is_valid,
    norm_to_abbr,
    norm_to_state,
    state_to_abbr,
)

# -- meta ------------------------------------------------------------------


def test_version():
    assert isinstance(ziplus.__version__, str)


# -- dataset ---------------------------------------------------------------


def test_dataset_version():
    assert dataset_version() != 'unknown'
    assert 'GeoNames' in dataset_version()


# -- validation ------------------------------------------------------------


def test_is_valid():
    assert is_valid('60614') is True
    assert is_valid('60614-7890') is True
    assert is_valid('606147890') is True
    assert is_valid('606') is False
    assert is_valid('hello') is False
    assert is_valid('') is False


# -- ZIP lookup ------------------------------------------------------------


def test_get_state_zip5():
    assert get_state('78701') == 'TX'
    assert get_state('02134') == 'MA'


def test_get_state_zip_plus4():
    assert get_state('60614-2803') == 'IL'
    assert get_state('331391234') == 'FL'


def test_get_state_full_name():
    assert get_state('80202', abbr=False) == 'Colorado'


def test_get_state_not_found():
    assert get_state('00000') is None


def test_get_state_invalid():
    with pytest.raises(ValueError, match='not a valid'):
        get_state('123')


# -- conversion ------------------------------------------------------------


def test_state_to_abbr():
    assert state_to_abbr('texas') == 'TX'
    assert state_to_abbr('ny') is None
    assert state_to_abbr('missing', 'ZZ') == 'ZZ'
    with pytest.raises(StateException):
        state_to_abbr('pluto', raise_exception=True)


def test_abbr_to_state():
    assert abbr_to_state('texas') is None
    assert abbr_to_state('hi') == 'Hawaii'
    assert abbr_to_state('missing', 'nope') == 'nope'
    # Regression: default must not leak into internal dict lookup
    assert abbr_to_state('QQ', 'TEXAS') == 'TEXAS'
    with pytest.raises(StateException):
        abbr_to_state('qq', raise_exception=True)


# -- normalization ---------------------------------------------------------


def test_norm_to_abbr():
    assert norm_to_abbr('tX') == 'TX'
    assert norm_to_abbr('fLoRiDa') == 'FL'
    assert norm_to_abbr('zz') is None
    assert norm_to_abbr('zz', 'QQ') == 'QQ'
    with pytest.raises(StateException):
        norm_to_abbr('zz', raise_exception=True)


def test_norm_to_state():
    assert norm_to_state('tx') == 'Texas'
    assert norm_to_state('FlOrIdA') == 'Florida'
    assert norm_to_state('qq') is None
    assert norm_to_state('qq', 'nope') == 'nope'
    with pytest.raises(StateException):
        norm_to_state('qq', raise_exception=True)


# -- formatting ------------------------------------------------------------


def test_format_state():
    assert format_state('tx') == 'TX'
    assert format_state('fLorIda') == 'Florida'
    assert format_state('qQq') == 'qQq'
    with pytest.raises(StateException):
        format_state('Nope', raise_exception=True)


# -- predicates ------------------------------------------------------------


def test_is_state():
    assert is_state('tx') is True
    assert is_state('zz') is False
    assert is_state('HI') is True
    assert is_state('fL') is True
    assert is_state('Oregon') is True
    assert is_state('OREGON') is True
    assert is_state('QQ') is False
    assert is_state('') is False


def test_is_state_full():
    assert is_state_full('TeXas') is True
    assert is_state_full('tX') is False
    assert is_state_full('Texass') is False


def test_is_state_abbr():
    assert is_state_abbr('TXX') is False
    assert is_state_abbr('hI') is True
    assert is_state_abbr('Oregon') is False


# -- internals -------------------------------------------------------------


def test_load_idempotent():
    ziplus._load()
    first_zipcodes = ziplus._zipcodes
    ziplus._load()
    assert ziplus._zipcodes is first_zipcodes


def test_version_fallback():
    import importlib

    from importlib.metadata import PackageNotFoundError

    try:
        with patch('importlib.metadata.version', side_effect=PackageNotFoundError):
            importlib.reload(ziplus)
            assert ziplus.__version__ == '0.0.0-dev'
    finally:
        importlib.reload(ziplus)


def test_states_immutable():
    with pytest.raises(TypeError):
        ziplus.STATES['Foo'] = 'XX'  # type: ignore[index]
