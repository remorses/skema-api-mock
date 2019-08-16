from functools import reduce
import operator
import mock
import os
import yaml
import json
import skema.infer

from collections import defaultdict
from typing import Dict, Union
from urllib.parse import urlparse
from funcy import contextmanager, concat

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
    return hostname, '/' + '/'.join(list(paths))

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
            schema = get_schema(url, url_map)
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
            schema = get_schema(url, url_map)
            return skema.fake_data(schema, amount=1)[-1]
        except IndexError:
            raise Exception(f'{url} not found')
    setattr(klass, method, mocked)
    return mock.patch(class_path, new_callable=lambda: klass)

def get_schema(target_url, url_map):
    for url, schema in url_map.items():
        if same_url(target_url, url):
            return schema
    raise Exception(f'url {target_url} not found')

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

def contains(group, x, equal=operator.eq):
    return any(equal(a, x) for a in group)

def group_equal(iter, equal=operator.eq):
    groups = []
    for x in iter:
        if not contains(list(concat(*groups)), x, equal=equal):
            groups += [[x]]
        else:
            i = [i for i, g in enumerate(groups) if contains(g, x, equal=equal)][0]
            groups[i] += [x]
    return groups

def parametrize_urls(urls):
    assert urls
    assert len(set([len(url.split('/')) for url in urls])) == 1
    parts = urls[0].split('/')
    def reducer(acc, url):
        parts = url.split('/')
        return [x if x == p else False for x, p in zip(acc, parts)]
    difference = reduce(reducer, urls, parts)
    if False in difference:
        parts[difference.index(False)] = '{}'
    return '/'.join(parts)

def ungroup_small_groups(groups, small=3):
    for group in groups:
        if len(group) <= small:
            for elem in group:
                yield [elem]
        else:
            yield group


def make_url_map(data_per_url):
    # data_per_url = aggregate_same_urls(data_per_url)
    def equal(a, b):
        url1, schema1 = a
        url2, schema2 = b
        return same_url(url1, url2) # and schema_difference_coefficent(schema1, schema2) < 0.5
    data_per_url = {k:replace_special_types(array) for k, array in data_per_url.items()}
    url_map = {url: skema.infer.infer_schema(array,) for url, array in data_per_url.items()}
    same_urls_schemas = group_equal(url_map.items(), equal=equal)
    same_urls_schemas = ungroup_small_groups(same_urls_schemas, small=2)
    url_map = {parametrize_urls([x[0] for x in group]): longer_schema([x[1] for x in group]) for group in same_urls_schemas}
    url_map = {url: skema.infer.from_jsonschema(schema, ref_name='Root') for url, schema in url_map.items()}
    return url_map

def same_url(url_a, url_b):
    """
    urls are equal if same hostname, same path len, only 1 path part is different
    """
    a = urlparse(url_a)
    b = urlparse(url_b)
    if (a.hostname and b.hostname) and a.hostname != b.hostname:
        return False
    pa = [x for x in a.path.split('/') if x]
    pb = [x for x in b.path.split('/') if x]
    if len(pa) != len(pb):
        return False
    same = [x == y for x, y in zip(pa, pb)]
    hits = len([x for x in same if bool(x)])
    if len(same) <= 1:
        return pa == pb
    if hits >= len(same) - 1:
        return True
    return False

def longer_schema(schemas):
    def reducer(acc, schema):
        if len(schema) > len(acc):
            return schema
        else:
            return acc
    return reduce(reducer, schemas, '')

def aggregate_same_urls(data_per_url):
    # print(data_per_url)
    visited = []
    result = {}
    for url, array in data_per_url.items():
        same_urls = [(u, arr) for u, arr in visited if same_url(url, u)]
        if len(same_urls):
            matched_url, matched_array = same_urls[0]
            parametrized_url = same_url(matched_url, url)
            array = array + matched_array
            result.update({parametrized_url: array})
            visited = [(u, a) for u, a in visited if u != matched_url]
            if matched_url in result:
                del result[matched_url]
        else:
            result.update({url: array})
        visited += [(url, array)]
    # print(result)
    return result

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


def get_schema_root_properties(schema):
    properties = schema.get('properties', {})
    return list(properties.keys())

def get_schema_common_properties(a, b):
    aprops = get_schema_root_properties(a)
    bprops = get_schema_root_properties(b)
    common = set(aprops) & set(bprops)
    return len(common)

def schema_difference_coefficent(a, b):
    aprops = get_schema_root_properties(a)
    bprops = get_schema_root_properties(b)
    unique = set(aprops + bprops)
    common = set(aprops) & set(bprops)
    coeff = len(common) / (len(unique) or 0.1)
    return 1 - coeff