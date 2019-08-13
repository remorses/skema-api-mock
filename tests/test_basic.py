import yaml
from mock_api import mock_api

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
        