from buggy_script import calculate
from termcolor import cprint

def test_subtract():
    assert calculate("subtract", 20, 3) == 17

def test_multiply():
    assert calculate("multiply", 2, 5) == 10

def test_bad_input():
    assert calculate("multiiiply", 2, 5) == None