# test_parameterized_fixture.py
import pytest

class MyTester:
    def __init__(self, x):
        self.x = x

    def dothis(self):
        # assert self.x
        print(f"self.x {self.x}")

@pytest.fixture
def tester(request):
    """Create tester object"""
    print(f"===== request.param {request.param}")
    try:
        print(f"===== request.param {request.param}")
        return MyTester(request.param)
    except Exception as e:
        print(f"+++++++++++{e}")
    return MyTester(29382)


class TestIt:
    @pytest.mark.parametrize('tester', [True, False], indirect=['tester'])
    def test_tc1(self, tester):
       tester.dothis()
       assert 1

    @pytest.mark.parametrize('tester', [143343], indirect=['tester'])
    def test_tc2(self, tester):
        tester.dothis()
        assert 1


    def test_tc3(self, tester):
       tester.dothis()
       assert 1
