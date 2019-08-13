# mock_api
mocks api function returning fake data with specified shape.
Every url can have different shape, these are represented in skema format in a yaml file,
```yaml
/posts/: |
    Response:
        ok: Boolù
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
```

## todo:
- change shape based on POST, GET ...
- change shape based on parameters
- add url parameters, like posts/:id/
- remove Response root key maybe (but i can't use root arrays, Root: [...])
- add possible codes, like 200, 400, then change shape based on them
- 
