import pytest
import os.path
import yaml
from xxx import Klass
from funcy import silent
from mock_api import mock_function, mock_method, track_function, track_method, same_url, aggregate_same_urls, schema_difference_coefficent, group_equal, parametrize_urls

urlmap = {
    '/': 'Root: Str',
    '/ciao/': """
        Root:
            x: Int
            y: Str
    """,
    '/ciao/{}/': """
        Root:
            r: Int
    """
}
def test_0():
    with mock_function('yaml.load', urlmap, arg=0) as m:
        res = yaml.load('http://instagram.com/')
        print(res)
        with pytest.raises(Exception):
            res = yaml.load('http://instagram.com/ciao/8/8')
        res = yaml.load('http://instagram.com/ciao/8')
        assert 'r' in res
    assert yaml.load('9') == 9

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
        yaml.load('a/5/b')
        yaml.load('a/9/b')
        yaml.load('a/3/b')
    assert os.path.exists(path)
    with open(path) as f:
        print()
        print(f.read())
    silent(os.remove)(path)

def test_4():
    path = 'urls_.yml'
    silent(os.remove)(path)
    with track_function('yaml.load', path, ):
        yaml.load('xx/5/b')
        yaml.load('a/9/b')
        yaml.load('a/3/b')
        yaml.load('a/3/b')
        yaml.load('a/89/8')
    assert os.path.exists(path)
    with open(path) as f:
        print()
        print(f.read())
    silent(os.remove)(path)



def test_track_class():
    path = 'urls_.yml'
    silent(os.remove)(path)
    with track_method('xxx.Klass', 'ciao', path,):
        x = Klass()
        x.ciao('a/1/b')
        x.ciao('a/2/b')
        x.ciao('a/8/b')
    assert os.path.exists(path)
    with open(path) as f:
        print()
        print(f.read())
    silent(os.remove)(path)


def test_mock_method():
    with mock_method('xxx.Klass', 'ciao', urlmap, arg=1):
        k = Klass()
        res = k.ciao('http://instagram.com/ciao/')
        print(res)
        with pytest.raises(Exception):
            res = k.ciao('http://instagram.com/xxx/')

@pytest.mark.parametrize(
    'a, b, expected',
    [
        ('/ciao/x', 'ciao/x', True),
        ('/ciao/34', 'ciao/12', True),
        ('/ciao/34/xxx', '/ciao/4/xxx', True),
        ('http://instagram.com/ciao/34/xxx', 'http://instagram.com/ciao/4/xxx', True),
        ('a/b/x/s', 'a/b/1/k', False)
    ]
)
def test_same_url(a, b, expected):
    res = same_url(a, b)
    print(res)
    assert res == expected


def test_aggregate_same_urls():
    data = {
        '/xxx/1': [0, ],
        '/xxx/2': [1, ],
        '/xxx/3': [2, ],
    }
    aggregate_same_urls(data)

def test_schema_difference_coefficent():
    a = {
        'properties': {
            'x': 1,
            'y': 1,
            'a': 1,
        }
    }
    b = {
        'properties': {
            'x': 1,
            'y': 1,
            'a': 9
        }
    }
    y = schema_difference_coefficent(a, b)
    print(y)

def test_group_by():
    equal = lambda a, b: a+b == 3
    groups = group_equal([1, 2, 3, 2, 3, 4, 1, 2 ], equal=equal)
    print(groups)


def test_parametrize_urls():
    x = parametrize_urls([
        'xxx/ciao/8/x',
        'xxx/ciao/9/x',
        'xxx/ciao/2/x',
    ])
    print(x)
    assert x == 'xxx/ciao/{}/x'