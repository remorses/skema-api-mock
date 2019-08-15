# mock_api
mocks api function returning fake data with specified shape.
Every url can have different shape, these are represented in skema format in a yaml file,
```yaml
/posts/: |
    Response:
        ok: Bool
        data: [
            postName: Str
            date: Str
            id: Int
        ]
/post/: |
    Response:
        ok: Bool
        data:
            author:
                name: Str
                id: Int
            description: Str
```
The shape of the data can change based on url hostname or path.
an example:
```python
from mock_api import mock_api
from api import api_call

with mock_api('api.api_call', 'api_shape.yml', arg=0):
    data = api_call('/posts/')
    print(data) # {'ok': True, 'data': {'postName': 'sdfsdgx', 'date': 'sdfg4'}}
```

## genrating the api shapes

You can generating the shapes calling many times the api
```python
from mock_api import mock_api
from api import api_call

with track_function_call('api.api_call', 'api_shape.yaml', ):
    api_call('/posts/')
    api_call('/post/34')
    api_call('/post/14')
    api_call('/data/')

# a file api_shape.yaml is created
assert os.path.exists('api_shape)
```

## todo:
- change shape based on POST, GET ...
- change shape based on parameters
- add url parameters, like posts/:id/
- remove Response root key maybe (but i can't use root arrays, Root: [...])
- add possible codes, like 200, 400, then change shape based on them
- 
