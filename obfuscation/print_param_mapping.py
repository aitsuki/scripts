import props.props as props

old_index = 8
new_index = 10

param_filter = [
    "vitellus",
    "password",
    "factoid",
]

for key in props.param:
    values = props.param[key]
    if values[old_index] in param_filter:
        print(f"{key}: {values[old_index]} -> {values[new_index]}")
