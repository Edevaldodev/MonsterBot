import pytest
from app.calculator import safe_calculate

def test_calculator_basic():
    assert safe_calculate("(25 * 4) / 2") == 50

def test_calculator_power():
    assert safe_calculate("2 ** 3") == 8

def test_calculator_blocks_code():
    with pytest.raises(ValueError):
        safe_calculate("__import__('os').system('echo no')")

def test_calculator_blocks_large_exponent():
    with pytest.raises(ValueError):
        safe_calculate("2 ** 20")
