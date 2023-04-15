from buggy_script import calculate

def test_subtract():
    assert calculate("subtract", 20, 3) == 17

def test_multiply():
    assert calculate("multiply", 2, 5) == 10

# chatgpt-3.5 had a really hard time getting this test to pass
# if you want to confirm that the tool works, try commenting this one out
def test_bad_input():
    assert calculate("multiiiply", 2, 5) == None