# nested_property.py

def _match(document, query):
    if not isinstance(query, dict):
        return False

    for key, value in query.items():
        if key == "$and":
            if not all(_match(document, subquery) for subquery in value):
                return False
        elif key == "$or":
            if not any(_match(document, subquery) for subquery in value):
                return False
        elif key == "$not":
            if _match(document, value):
                return False
        elif isinstance(value, dict):
            doc_value = get(document, key)
            for op, v in value.items():
                if op == "$eq" and not doc_value == v:
                    return False
                elif op == "$ne" and not doc_value != v:
                    return False
                elif op == "$gt" and not (doc_value is not None and doc_value > v):
                    return False
                elif op == "$gte" and not (doc_value is not None and doc_value >= v):
                    return False
                elif op == "$lt" and not (doc_value is not None and doc_value < v):
                    return False
                elif op == "$lte" and not (doc_value is not None and doc_value <= v):
                    return False
                elif op == "$in" and not doc_value in v:
                    return False
                elif op == "$nin" and doc_value in v:
                    return False
                else:
                    if op not in ["$eq","$ne","$gt","$gte","$lt","$lte","$in","$nin"]:
                        raise ValueError(f"Unsupported operator: {op}")
        else:
            if get(document, key) != value:
                return False
    return True

def _parse_key(key, index_prefix):
    """Determine if the key is a list index or dict key.
    Supports multi-character index prefixes.
    """
    if index_prefix is not None and key.startswith(index_prefix):
        return True, int(key[len(index_prefix):])
    elif index_prefix is None and key.isdigit():
        return True, int(key)
    return False, key

def _traverse(obj, keys, create_missing=False, index_prefix=None):
    for key in keys:
        is_index, k = _parse_key(key, index_prefix)
        if is_index:
            if not isinstance(obj, list):
                if create_missing:
                    obj.clear() if isinstance(obj, dict) else None
                    obj = []
                else:
                    return None
            while create_missing and k >= len(obj):
                obj.append({})
            try:
                obj = obj[k]
            except (IndexError, TypeError):
                return None
        else:
            if not isinstance(obj, dict):
                if create_missing:
                    obj.clear() if isinstance(obj, list) else None
                    obj = {}
                else:
                    return None
            if create_missing and k not in obj:
                obj[k] = {}
            obj = obj.get(k)
        if obj is None:
            return None
    return obj

def get(obj, path, default=None, index_prefix=None):
    keys = path.split(".")
    result = _traverse(obj, keys, index_prefix=index_prefix)
    return default if result is None else result

def set(obj, path, value, index_prefix=None):
    keys = path.split(".")
    current = obj
    for key in keys[:-1]:
        is_index, k = _parse_key(key, index_prefix)
        if is_index:
            if not isinstance(current, list):
                current.clear() if isinstance(current, dict) else None
                current = []
            while k >= len(current):
                current.append({})
            current = current[k]
        else:
            if not isinstance(current, dict):
                current.clear() if isinstance(current, list) else None
                current = {}
            if k not in current or not isinstance(current[k], (dict, list)):
                current[k] = {}
            current = current[k]

    last_is_index, last_key = _parse_key(keys[-1], index_prefix)
    if last_is_index:
        if not isinstance(current, list):
            current.clear() if isinstance(current, dict) else None
            current = []
        while last_key >= len(current):
            current.append(None)
        current[last_key] = value
    else:
        if not isinstance(current, dict):
            current.clear() if isinstance(current, list) else None
            current = {}
        current[last_key] = value

def delete(obj, path, index_prefix=None):
    keys = path.split(".")
    parent = _traverse(obj, keys[:-1], index_prefix=index_prefix)
    if parent is None:
        return
    last_is_index, last_key = _parse_key(keys[-1], index_prefix)
    if last_is_index and isinstance(parent, list) and 0 <= last_key < len(parent):
        parent.pop(last_key)
    elif not last_is_index and isinstance(parent, dict):
        parent.pop(last_key, None)

def unset(obj, path, index_prefix=None):
    delete(obj, path, index_prefix)

def push(obj, path, value, index_prefix=None):
    target = _traverse(obj, path.split("."), create_missing=True, index_prefix=index_prefix)
    if isinstance(target, list):
        target.append(value)
    else:
        set(obj, path, [value], index_prefix=index_prefix)

def pull(obj, path, value=None, index=None, index_prefix=None):
    keys = path.split(".")
    parent = _traverse(obj, keys[:-1], index_prefix=index_prefix)
    if parent is None:
        return
    last_is_index, last_key = _parse_key(keys[-1], index_prefix)
    target_list = None

    if last_is_index and isinstance(parent, list) and 0 <= last_key < len(parent) and isinstance(parent[last_key], list):
        target_list = parent[last_key]
    elif not last_is_index and isinstance(parent, dict) and last_key in parent and isinstance(parent[last_key], list):
        target_list = parent[last_key]

    if target_list is None:
        return

    if index is not None and isinstance(index, int) and 0 <= index < len(target_list):
        target_list.pop(index)
    elif value is not None:
        if isinstance(value, dict):
            q_indexes = []
            for idx, doc in enumerate(target_list):
                if not isinstance(doc, dict):
                    continue
                if _match(doc, value):
                    q_indexes.append(idx)
            for idx in q_indexes[::-1]:
                target_list.pop(idx)
        else:
            parent[last_key if not last_is_index else last_key] = [v for v in target_list if v != value]

def has(obj, path, index_prefix=None):
    keys = path.split(".")
    current = obj
    for key in keys:
        is_index, k = _parse_key(key, index_prefix)
        if is_index:
            if not isinstance(current, list):
                return False
            try:
                current = current[k]
            except (IndexError, TypeError):
                return False
        else:
            if not isinstance(current, dict) or k not in current:
                return False
            current = current[k]
    return True