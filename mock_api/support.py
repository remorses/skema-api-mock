import yaml
import ruamel.yaml

def _dot_lookup(thing, comp, import_path):
    try:
        return getattr(thing, comp)
    except AttributeError:
        __import__(import_path)
        return getattr(thing, comp)


def importer(target):
    components = target.split('.')
    import_path = components.pop(0)
    thing = __import__(import_path)

    for comp in components:
        import_path += ".%s" % comp
        thing = _dot_lookup(thing, comp, import_path)
    return thing

class Dumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(Dumper, self).increase_indent(flow, False)

def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    
yaml.add_representer(str, str_presenter)

def dumps_yaml_(data):
    return yaml.dump(data, Dumper=Dumper, default_flow_style=False, default_style='|', indent=4)

def dumps_yaml(data):
    res = ""
    for line in ruamel.yaml.round_trip_dump(data, indent=4, block_seq_indent=4, default_style='|').splitlines(True):
        res += line
    return res