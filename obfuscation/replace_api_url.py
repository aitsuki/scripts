import os
import re

import props.props as props

dart_api_file = "c:/Users/as/dev/flutter/nga-gen-credit/lib/api.dart"

old_index = 8
new_index = 10

mapping = {}
for key in props.url:
    values = props.url[key]
    mapping[values[old_index]] = values[new_index]

with open(dart_api_file, "r+", encoding="utf-8") as f:
    code = f.read()

    def replace_match(match):
        old_url = match.group(1)
        new_url = mapping.get(old_url, old_url)
        print(f"{old_url} => {new_url}")
        return f'post("{new_url}"'

    pattern = re.compile(r"post\s*\(\s*[\'\"]([^\'\"]+)[\'\"]")
    updated_code = pattern.sub(replace_match, code)

    f.seek(0)
    f.truncate(0)
    f.write(updated_code)
