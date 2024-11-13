import pytest

from eocanvas.processes import ShearWaterProcess


def test_invalid_area():
    with pytest.raises(ValueError) as e:
        ShearWaterProcess(area="unknown", start_day="1970-01-01", end_day="1970-01-01")
        assert e.value.message.startswith("Invalid area unknown")


def test_invalid_start_day():
    with pytest.raises(ValueError) as e:
        ShearWaterProcess(area="Sindian", start_day="abc", end_day="1970-01-01")
        assert e.value.message.startswith("start_date 'abc'")


def test_invalid_end_day():
    with pytest.raises(ValueError) as e:
        ShearWaterProcess(area="Sindian", start_day="1970-01-01", end_day="abc")
        assert e.value.message.startswith("end_date 'abc'")
