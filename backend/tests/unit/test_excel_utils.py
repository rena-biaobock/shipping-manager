"""
Unit tests for excel_serial_to_dt.

Excel stores dates as floats: integer part = days since 1899-12-30,
fractional part = fraction of 24 hours.

Excel has a known bug treating 1900 as a leap year (serial 60 = 1900-02-29).
Using epoch 1899-12-30 sidesteps this without special-casing.
"""

import pytest
from datetime import datetime

from app.utils.excel import excel_serial_to_dt


# ---------------------------------------------------------------------------
# Epoch and known dates
# ---------------------------------------------------------------------------

def test_serial_zero_returns_epoch():
    assert excel_serial_to_dt(0) == datetime(1899, 12, 30, 0, 0, 0)


def test_serial_two_is_excel_january_1_1900():
    # Excel serial 1 = 1900-01-00 (the phantom leap day bug),
    # serial 2 = 1900-01-01 in real-world terms.
    assert excel_serial_to_dt(2) == datetime(1900, 1, 1, 0, 0, 0)


def test_known_date_serial_44927_is_2023_01_01():
    assert excel_serial_to_dt(44927) == datetime(2023, 1, 1, 0, 0, 0)


def test_known_date_serial_45292_is_2024_01_01():
    assert excel_serial_to_dt(45292) == datetime(2024, 1, 1, 0, 0, 0)


# ---------------------------------------------------------------------------
# Fractional part → time of day
# ---------------------------------------------------------------------------

def test_fractional_half_is_noon():
    result = excel_serial_to_dt(44927.5)
    assert result == datetime(2023, 1, 1, 12, 0, 0)


def test_fractional_quarter_is_six_am():
    result = excel_serial_to_dt(44927.25)
    assert result == datetime(2023, 1, 1, 6, 0, 0)


def test_fractional_three_quarters_is_six_pm():
    result = excel_serial_to_dt(44927.75)
    assert result == datetime(2023, 1, 1, 18, 0, 0)


def test_integer_serial_has_midnight_time():
    result = excel_serial_to_dt(44927)
    assert result.hour == 0
    assert result.minute == 0
    assert result.second == 0


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

def test_returns_datetime_instance():
    assert isinstance(excel_serial_to_dt(44927), datetime)
