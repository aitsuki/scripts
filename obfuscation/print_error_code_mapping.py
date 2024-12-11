import props.props as props

old_index = 8
new_index = 10

errcode_filter = [
    "0000",
    "Z1005",
    "Z1003",
    "Z1004",
    "Z1019",
    "Z1013",
]

for key in props.errcode:
    if key in errcode_filter:
        values = props.errcode[key]
        print(f"{key}: {values[old_index]} -> {values[new_index]}")
