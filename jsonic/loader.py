#!python

# build complete json dictionaries using an inheritance structure.
# the key '*' is used to denote inheritance.
# resulting object contains a '*' key with inheritance structure.

# values inherit as follows:
# dict - override merge
# list - full merge

# todo: add loop detection

from json import load as loadJson, dumps
from os.path import join as path_join, dirname, normpath
import re
import sys
import importlib.util
from .utils import override_merge, try_get, key_exists
import requests

def RemoveComments(text):
    # Remove single-line comments
    text = re.sub(r"//.*", "", text)
    # Remove multi-line comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text

def ResolveItem(file, ref, config):
    if file.endswith('.json'):
        item = LoadConfigFromFile(file)
        if ref != None:
           return try_get(item, ref)
        return item
    if file.endswith('.py'):
        module = ImportModuleFromPath(file, "build_module")
        build_function = getattr(module, ref)
        return build_function(config)

def ResolvePath(source, path):
    try:
        return normpath(path_join(dirname(source), path))
    except Exception as e:
        raise Exception(f"Error resolving path {path} from {source}") from e

def ResolveLinks(filename, config):
    for key in list(config.keys()):
        val = config[key]

        # recurse into dicts first
        if isinstance(val, dict):
            config[key] = ResolveLinks(filename, val)

        # resolve references like "*.path#ref"
        if isinstance(val, str) and val.startswith("*."):
            ref = None
            s = val.split('#')
            file = s[0][2:]
            if len(s) == 2:
                ref = s[1]

            file_path = ResolvePath(filename, file)
            config[key] = ResolveItem(file_path, ref, config)
    return config

def LoadConfig(source, config):
    # if there is a base to inherit from, load it and then merge over it.
    if '*' in config:
        val = config['*']

        if val.startswith("http://") or val.startswith("https://"):
            result = requests.get(val).json()
            base_config = LoadConfig("", result)
            config = override_merge(config, base_config)
            del config['*']

        elif val.endswith('.json'):
            basePath = config['*']
            basePath = ResolvePath(source, basePath)
            base_config = LoadConfigFromFile(basePath)
            config = override_merge(config, base_config)
            del config['*']

    return config

def LoadConfigFromFile(fileName):
    with open(fileName, 'r') as file:
        try:
            config = loadJson(file)
        except:
            raise Exception(f"Error loading config file {fileName}")

    return LoadConfig(fileName, config)

def ImportModuleFromPath(file_path, module_name):
    # Load the module spec from the given file path
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def Load(filename):
    if not filename.endswith('.json'):
        filename = filename + '.json'

    config = LoadConfigFromFile(filename)

    return ResolveLinks(filename, config)

if __name__ == "__main__":
    filename = normpath(sys.argv[1])
    print(dumps(Load(filename), indent=2))
