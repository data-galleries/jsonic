#!python

# build complete json dictionaries using an inheritance structure.
# the key '#base' is used to denote inheritance.
# resulting object contains a '#tree' key with inheritance structure.

# values inherit as follows:
# dict - override merge
# list - full merge

# todo: add loop detection

from json import load as loadJson, dumps
from os.path import join as path_join, dirname, normpath
import re
import sys
import importlib.util
from luke_lib.dict_helpers import override_merge, try_get
import requests
from jsonic.util import GetRefAndKey
import types

def RemoveComments(text):
    # Remove single-line comments
    text = re.sub(r"//.*", "", text)
    # Remove multi-line comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text

def ResolveJsonLink(link, source):
    ref, key = GetRefAndKey(link)
    if ref.startswith("http://") or ref.startswith("https://"):
        result = requests.get(ref).json()
        item = LoadConfig(None, result)
    else:
        path = ResolveLocalPath(source, ref)
        item = LoadConfigFromFile(path, link=True)

    if key is None : return item
    else : return try_get(key, item)

def ResolvePythonLink(link, config):
    ref, key = GetRefAndKey(link)
    if ref.startswith("http://") or ref.startswith("https://"):
        result = requests.get(ref).text
        module = types.ModuleType("build_module")
        exec(result, module.__dict__)
    else:
        module = ImportModuleFromPath(ref, "build_module")

    build_function = getattr(module, key)
    return build_function(config)

def ResolveLocalPath(source, path):
    try:
        return normpath(path_join(dirname(source), path))
    except Exception as e:
        raise Exception(f"Error resolving path {path} from {source}") from e

def ResolveLinks(filename, config):
    for key in list(config.keys()):
        val = config[key]

        # recursive resolve dictionaries
        if isinstance(val, dict):
            config[key] = ResolveLinks(filename, val)

        # resolve any json links - denoted by strings starting with '*.'
        if isinstance(val, str) and val.startswith("*."):
            config[key] = ResolveJsonLink(val, filename)

        # resolve any python links - denoted by strings starting with '!.'
        if isinstance(val, str) and val.startswith("!."):
            config[key] = ResolvePythonLink(val, config)

    if "!" in config:
        config = ResolvePythonLink(config["!"], config)
        del config["!"]

    return config

def LinkInheritance(filename, config):
    diff = {}
    for key in config:
        val = config[key]
        if type(val) == str and val.startswith("*."):
            ref, key = GetRefAndKey(val)
            newPath = ResolveLocalPath(filename, ref)
            newValue = f"*.{newPath}"
            if key != None:
                newValue += f"#{key}"
            diff[key] = newValue

    config = override_merge(config, diff)
    return config

def LoadConfig(source, config):
    # if there is a base to inherit from, load it and then merge over it.
    if "*" in config:
        val = config['*']
        base_config = ResolveJsonLink(val, source)
        config = override_merge(config, base_config)
        del config['*']

    return config

def LoadConfigFromFile(source, link=False):
    with open(source, 'r') as file :
        try:
            config = loadJson(file)
        except:
            raise Exception(f"Error loading config file {source}")

    if link:
        config = LinkInheritance(source, config)

    return LoadConfig(source, config)

def ImportModuleFromPath(file_path, module_name):
    # Load the module spec from the given file path
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def Load(source):
    if not source.endswith('.json'):
        source = source + '.json'

    config = LoadConfigFromFile(source)
    return ResolveLinks(source, config)

if __name__ == "__main__":
    filename = normpath(sys.argv[1])
    print(dumps(Load(filename), indent=2))
