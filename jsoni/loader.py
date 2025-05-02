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
from luke_lib.dict_helpers import key_exists, override_merge, try_get

def RemoveComments(text):
    # Remove single-line comments
    text = re.sub(r"//.*", "", text)
    # Remove multi-line comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text

def ResolveItem(file, ref, config):
    print("attempting to resolve link to", file, "with ref", ref)
    if file.endswith('.json'):
        item = LoadConfig(file)
        if ref != None:
           return try_get(ref, item)
        return item
    if file.endswith('.py'):
        module = ImportModuleFromPath(file, "build_module")
        build_function = getattr(module, ref)
        return build_function(config)

def ResolvePath(source, path):

	# todo allow loading from a url or a configured path

    try:
        return normpath(path_join(dirname(source), path))
    except Exception as e:
        raise Exception(f"Error resolving path {path} from {source}") from e

def ResolveLinks(filename, config):
    print("ResolveLinks called with", filename, config)
    for key in list(config.keys()):
        val = config[key]

        # recursive resolve dictionaries
        if isinstance(val, dict):
            print("recurse into dict ", key)
            config[key] = ResolveLinks(filename, val)

        # resolve any references - denoted by strings starting with '*.'
        if isinstance(val, str) and val.startswith("*."):
            ref = None
            s = val.split('#')
            file = s[0][2:]
            if len(s) == 2:
                ref = s[1]
            config[key] = ResolveItem(file, ref, config)

    return config

def LinkInheritance(filename, config):
    for key in config:
        val = config[key]
        if type(val) == str and val.startswith("*."):
            ref = None
            s = val.split('#')
            file = s[0][2:]
            if (len(s) == 2):
                ref = s[1]
            newPath = ResolvePath(filename, file)
            newValue = f"*.{newPath}"
            if ref != None:
                newValue += f"#{ref}"
            config[key] = newValue

    return config

def LoadConfig(fileName):
    with open(fileName, 'r') as file :
        try:
            config = loadJson(file)
        except:
            raise Exception(f"Error loading config file {fileName}")

    config = LinkInheritance(fileName, config)

    # if there is a base to inherit from, load it and then merge over it.
    if key_exists("*", config):
        val = config['*']
        ref = None
        s = val.split('#')
        file = s[0][2:]
        if len(s) == 2:
            ref = s[1]

        # todo respect ref here
        if file.endswith('.json'):
            basePath = config['*']
            basePath = ResolvePath(fileName, basePath)
            base_config = LoadConfig(basePath)
            config = override_merge(config, base_config)
            del config['*']

    return config

def ImportModuleFromPath(file_path, module_name):
    # Load the module spec from the given file path
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def load(filename):
    if not filename.endswith('.json'):
        filename = filename + '.json'

    config = LoadConfig(filename)

    return ResolveLinks(filename, config)

if __name__ == "__main__":
    filename = normpath(sys.argv[1])
    print(dumps(load(filename), indent=2))
