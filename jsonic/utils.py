def key_exists(d: dict, dotted_key: str) -> bool:
    try:
        for k in dotted_key.split("."):
            d = d[k]
        return True
    except (KeyError, TypeError):
        return False

def override_merge(config, base_config) :
    for key in config :
        t = type(config[key])
        if t == dict :
            if key not in base_config:
                base_config[key] = config[key]
            else:
                base_config[key] = override_merge(config[key], base_config[key])
            continue

        if type(config[key]) == list :
            if key not in base_config:
                base_config[key] = config[key]
            else:
                base_config[key] = config[key] + base_config[key]
            continue

        base_config[key] = config[key]
    return base_config

def try_get(d: dict, dotted_key: str):
    keys = dotted_key.split('.')
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d
