import props.props as props

old_index = 8
new_index = 10

for key in props.header:
    values = props.header[key]
    print(f"{key}: {values[old_index]} -> {values[new_index]}")
