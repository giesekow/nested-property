# Nested Property Library for Python

A lightweight Python library for **accessing, modifying, and manipulating nested dictionaries and lists** using dot-separated paths. Inspired by JavaScript libraries like `nested-property`, with support for **multi-character list index prefixes**.

---

## Features

- **Get** nested values: `get(obj, path)`
- **Set** nested values: `set(obj, path, value)`
- **Delete** nested values: `delete(obj, path)`
- **Check existence**: `has(obj, path)`
- **Push** values to nested lists: `push(obj, path, value)`
- **Pull** values from nested lists: `pull(obj, path, value=None, index=None)`
- Supports **list indices with optional prefixes**, e.g., `"$0"` or `"idx_0"`
- Default behavior treats numeric keys as list indices automatically (`index_prefix=None`)

---

## Installation

```
pip install nested-property
```

## Usage

import the functions
```
from nested_property import get, set, delete, has, push, pull
```
Note that you can also import `unset` which is an alias for `delete`

Basic usage
```
data = {"a": {"b": {"c": 42}}}

# Get a value
print(get(data, "a.b.c"))  # 42

# Set a value
set(data, "a.b.d", 100)
print(data)  # {'a': {'b': {'c': 42, 'd': 100}}}

# Check existence
print(has(data, "a.b.c"))  # True

# Delete a value
delete(data, "a.b.c")
print(has(data, "a.b.c"))  # False
```

Working with lists
```
data = {"items": [1, 2, 3]}

# Push a value to a list
push(data, "items", 4)
print(get(data, "items"))  # [1, 2, 3, 4]

# Pull a value by value
pull(data, "items", value=2)
print(get(data, "items"))  # [1, 3, 4]

# Pull a value by index
pull(data, "items", index=0)
print(get(data, "items"))  # [3, 4]
```

Using index prefix
```
data = {}

# Use "@" as prefix
set(data, "a.b.@0.items", [1, 2, 3], index_prefix="@")
push(data, "a.b.@0.items", 4, index_prefix="@")
print(get(data, "a.b.@0.items", index_prefix="@"))  # [1, 2, 3, 4]

# Use multi-character prefix "idx_"
set(data, "x.y.idx_0.list", [10, 20], index_prefix="idx_")
pull(data, "x.y.idx_0.list", value=10, index_prefix="idx_")
print(get(data, "x.y.idx_0.list", index_prefix="idx_"))  # [20]
```

Mixed usage
```
data = {"a": [{"b": [1, 2, 3]}]}

# Numeric keys work without prefix
print(get(data, "a.0.b"))  # [1, 2, 3]

# Push to nested list
push(data, "a.0.b", 4)
print(get(data, "a.0.b"))  # [1, 2, 3, 4]
```

## API

| Function | Description | Parameters |
|----------|-------------|------------|
| `get(obj, path, default=None, index_prefix=None, query=None)` | Get nested value | `obj`: dict/list, `path`: str/list[str], `default`: any, `index_prefix`: str or None, `query`: dict or None |
| `set(obj, path, value, index_prefix=None)` | Set nested value | `obj`: dict/list, `path`: str/list[str], `value`: any, `index_prefix`: str or None |
| `delete(obj, path, index_prefix=None)` | Delete nested value | `obj`: dict/list, `path`: str/list[str], `index_prefix`: str or None |
| `unset(obj, path, index_prefix=None)` | Alias for Delete | `obj`: dict/list, `path`: str/list[str], `index_prefix`: str or None |
| `has(obj, path, index_prefix=None)` | Check if nested value exists | `obj`: dict/list, `path`: str/list[str], `index_prefix`: str or None |
| `push(obj, path, value, index_prefix=None)` | Append value to nested list | `obj`: dict/list, `path`: str/list[str], `value`: any, `index_prefix`: str or None |
| `pull(obj, path, value=None, index=None, index_prefix=None)` | Remove value from nested list by value or index | `obj`: dict/list, `path`: str[str], `value`: any, `index`: int, `index_prefix`: str or None |


## Notes
Dot-separated paths are used for nested keys, e.g., `"a.b.c"` or `"x.y.0.z"`.

Index prefixes allow you to distinguish numeric dictionary keys from list indices.

When `index_prefix=None` (default), any key that is a valid integer string is treated as a list index automatically.

Where `path` is a list the functions return a list or where its an editing functions (e.g. `set`, `pull`, `push`) the effect is applied to the paths one after the other.

When using the `pull` function, when `value` is a `dict` it is used as a query.

## License
MIT License

## Author
Created by Giles Tetteh. Inspired by JavaScript nested-property library.
