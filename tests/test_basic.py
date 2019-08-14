import pytest
import os.path
import yaml
from funcy import silent
from mock_api import mock_api, track_function_call

urlmap = {
    '/ciao/': """
        Root:
            x: Int
            y: Str
    """
}
def test_1():
    with mock_api('yaml.load', urlmap, arg=0) as m:
        res = yaml.load('http://instagram.com/ciao/')
        print(res)
        assert 'x' in res
        assert 'y' in res
    assert yaml.load('9') == 9

def test_2():
    m = mock_api('yaml.load', urlmap, arg=0)
    m.start()
    with pytest.raises(Exception):
        res = yaml.load('http://instagram.com/xxx/')
    m.stop()
    assert yaml.load('9') == 9

def test_3():
    path = 'urls_.yml'
    silent(os.remove)(path)
    with track_function_call('yaml.load', path, ):
        yaml.load('9')
        yaml.load('{ciao: []}')
        yaml.load('ciao')
    assert os.path.exists(path)
    with open(path) as f:
        print(f.read())
