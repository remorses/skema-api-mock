import pytest
import os.path
import yaml
from xxx import Klass
from funcy import silent
from mock_api import mock_function, mock_method, track_function, track_method

urlmap = {
    '/ciao/': """
        Root:
            x: Int
            y: Str
    """
}
def test_1():
    with mock_function('yaml.load', urlmap, arg=0) as m:
        res = yaml.load('http://instagram.com/ciao/')
        print(res)
        assert 'x' in res
        assert 'y' in res
    assert yaml.load('9') == 9

def test_2():
    m = mock_function('yaml.load', urlmap, arg=0)
    m.start()
    with pytest.raises(Exception):
        res = yaml.load('http://instagram.com/xxx/')
    m.stop()
    assert yaml.load('9') == 9

def test_3():
    path = 'urls_.yml'
    silent(os.remove)(path)
    with track_function('yaml.load', path, ):
        yaml.load('9')
        yaml.load('{ciao: []}')
        yaml.load('ciao')
    assert os.path.exists(path)
    with open(path) as f:
        print(f.read())
    silent(os.remove)(path)



def test_track_class():
    path = 'urls_.yml'
    silent(os.remove)(path)
    with track_method('xxx.Klass', 'ciao', path,):
        x = Klass()
        x.ciao('asdasd')
        x.ciao('sdfsd')
        x.ciao('asdasd')
    assert os.path.exists(path)
    with open(path) as f:
        print(f.read())
    silent(os.remove)(path)


def test_mock_method():
    with mock_method('xxx.Klass', 'ciao', urlmap, arg=1):
        k = Klass()
        res = k.ciao('http://instagram.com/ciao/')
        print(res)
        with pytest.raises(Exception):
            res = k.ciao('http://instagram.com/xxx/')
