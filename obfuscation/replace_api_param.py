import os
import re
import props.props as props


dart_model_dir = "c:/Users/as\dev/flutter/nga-gen-credit/lib/model"

old_index = 8
new_index = 10

mapping = {}
for key in props.param:
    values = props.param[key]
    mapping[values[old_index]] = values[new_index]

# 正则表达式匹配 @JsonKey(name: 'xxx')
jsonkey_pattern = re.compile(r"@JsonKey\(name:\s*[\'\"]([^\'\"]+)[\'\"]\)")

for dart_file in os.listdir(dart_model_dir):
    if dart_file.endswith(".g.dart"):
        continue
    print(f"{dart_file}:")
    with open(os.path.join(dart_model_dir, dart_file), "r+", encoding="utf-8") as f:
        new_content = ""
        for line in f:
            match = jsonkey_pattern.search(line)
            if match:
                old_name = match.group(1)
                new_name = mapping.get(old_name, old_name)
                print(f"{old_name} => {new_name}")
                new_line = line[: match.start(1)] + new_name + line[match.end(1) :]
                new_content += new_line
            else:
                new_content += line
        print("=============================")
        f.seek(0)
        f.truncate(0)
        f.write(new_content)
