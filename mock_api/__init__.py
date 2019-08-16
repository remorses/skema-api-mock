import mock
import os
import yaml
import json
import skema.infer

from collections import defaultdict
from typing import Dict, Union
from urllib.parse import urlparse
from funcy import contextmanager

from .support import importer, dumps_yaml

def load(path):
    if path.endswith('.yml') or path.endswith('.yaml'):
        with open(path,) as f:
            data = yaml.load(f, )
            return data
    else:
        raise NotImplementedError()

def hostname_and_path(url: str):
    a = urlparse(url)
    hostnames =  a.hostname.split('.')[-2:] if a.hostname else []
    hostname = '.'.join(hostnames)
    paths = filter(bool, a.path.split('/'))
    paths = list(paths)
    if not hostname and not url.startswith('/'):
        if '.' in paths[0]:
            hostname = paths.pop(0)
    return hostname, list(paths)

def fuzzy_compare_urls(a, b):
    a_name, a_paths = hostname_and_path(a)
    b_name, b_paths = hostname_and_path(b)
    if a_name and b_name:
        return a_name == b_name and a_paths == b_paths
    else:
        return a_paths == b_paths

    

def mock_function(function_path, url_map: Union[str, dict], arg=0, kwarg=None):
    """
    name.com/path1/path2
    www.name.com/path1/path2
    /path/ciao/
    path/ciao
    """
    if isinstance(url_map, str):
        url_map: Dict[str, dict] = load(url_map)

    def mocked(*args, **kwargs):
        if kwarg is not None:
            url = kwargs[kwarg]
        else:
            url = args[arg]
        try:
            key = [x for x in url_map if fuzzy_compare_urls(url, x)][0]
            schema = url_map[key]
            return skema.fake_data(schema, amount=1)[-1]
        except IndexError:
            raise Exception(f'{url} not found')

    return mock.patch(function_path, new_callable=lambda: mocked)
    

def mock_method(class_path, method, url_map: Union[str, dict], arg=1, kwarg=None):
    klass = importer(class_path)
    if isinstance(url_map, str):
        url_map: Dict[str, dict] = load(url_map)
    def mocked(*args, **kwargs):
        if kwarg is not None:
            url = kwargs[kwarg]
        else:
            url = args[arg]
        try:
            key = [x for x in url_map if fuzzy_compare_urls(url, x)][0]
            schema = url_map[key]
            return skema.fake_data(schema, amount=1)[-1]
        except IndexError:
            raise Exception(f'{url} not found')
    setattr(klass, method, mocked)
    return mock.patch(class_path, new_callable=lambda: klass)

def replace_special_types(array):
    result = []
    inferrable_types = (dict, str, bool, int, float, list,)
    for obj in array:
        if isinstance(obj, dict):
            data = json.dumps(obj, default=str)
            result.append(json.loads(data))
        elif any([isinstance(obj, x) for x in inferrable_types]):
            result.append(obj)
    return result

@contextmanager
def track_function(function_path, url_map_path, arg=0, kwarg=None):
    function = importer(function_path)
    data_per_url = defaultdict(list)
    def mocked(*args, **kwargs):
        if kwarg is not None:
            url = kwargs[kwarg]
        else:
            url = args[arg]
        parsed = urlparse(url)
        url = parsed.hostname or '' + parsed.path or ''
        result = function(*args, **kwargs)
        data_per_url[url] += [result]
        return result
    m = mock.patch(function_path, new_callable=lambda: mocked)
    m.start()
    try:
        yield m
    finally:
        m.stop()
        url_map = make_url_map(data_per_url)
        if os.path.exists(url_map_path):
            with open(url_map_path, 'r') as f:
                data = yaml.load(f)
                url_map = {**data, **url_map}
        with open(url_map_path, 'w') as f:
            data = dumps_yaml(url_map)
            f.write(data)

def make_url_map(data_per_url):
    data_per_url = {k:replace_special_types(array) for k, array in data_per_url.items()}
    return {url: skema.infer.infer_skema(array, ) for url, array in data_per_url.items()}


@contextmanager
def track_method(class_path, method, url_map_path, arg=1, kwarg=None):
    klass = importer(class_path)
    function = getattr(klass, method)
    data_per_url = defaultdict(list)
    def mocked(*args, **kwargs):
        # print(args)
        if kwarg is not None:
            url = kwargs[kwarg]
        else:
            url = args[arg]
        parsed = urlparse(url)
        url = parsed.hostname or '' + parsed.path or ''
        result = function(*args, **kwargs)
        data_per_url[url] += [result]
        return result
    setattr(klass, method, mocked)
    m = mock.patch(class_path, new_callable=lambda: klass)
    m.start()
    try:
        yield m
    finally:
        m.stop()
        url_map = make_url_map(data_per_url)
        if os.path.exists(url_map_path):
            with open(url_map_path, 'r') as f:
                data = yaml.load(f)
                url_map = {**data, **url_map}
        with open(url_map_path, 'w') as f:
            data = dumps_yaml(url_map)
            f.write(data)