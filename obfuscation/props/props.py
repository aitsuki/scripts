def _read_props(filename):
    props_map = {}
    with open(filename) as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            value_list = value.split(",")
            props_map[key] = value_list
    return props_map


header = _read_props("props/mapping-header.properties")
errcode = _read_props("props/mapping-code.properties")
param = _read_props("props/mapping-param.properties")
url = _read_props("props/mapping-path-add.properties")
