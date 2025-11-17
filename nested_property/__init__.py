# nested_property.py

import re
from typing import Any, Dict, List

def get_value(obj, key, default=None):
    """Retrieve value from dict or object attribute."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    if hasattr(obj, key):
        return getattr(obj, key)
    return default

def set_value(obj, key, value):
    """Set value on dict or object attribute."""
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)

def has_key(obj, key):
    """Check if key exists in dict or object attribute."""
    if isinstance(obj, dict):
        return key in obj
    return hasattr(obj, key)

def is_list_object(obj):
    return isinstance(obj, (list, tuple))

def is_dict_object(obj):
    return isinstance(obj, dict) or hasattr(obj, '__dict__')

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
                elif op == "$len":
                    _len = len(doc_value)
                    if isinstance(v, dict):
                        if not _match({"$len": _len}, v):
                            return False
                    elif not _len == v:
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
            if not is_list_object(obj):
                if create_missing:
                    obj.clear() if isinstance(obj, dict) else None
                    obj = []
                else:
                    return None
            while create_missing and k >= len(obj):
                obj.append({})
            try:
                obj = get_value(obj, k)
            except (IndexError, TypeError):
                return None
        else:
            if not is_dict_object(obj):
                if create_missing:
                    obj.clear() if isinstance(obj, list) else None
                    obj = {}
                else:
                    return None
            if create_missing and not has_key(obj, k):
                set_value(obj, k, {})
            obj = get_value(obj, k)
        if obj is None:
            return None
    return obj

def get(obj, path, default=None, index_prefix=None, query=None):
    
    if is_list_object(path):
        res = []
        for p in path:
            res.append(get(obj=obj, path=p, default=default, index_prefix=index_prefix, query=query))
            
        return res
    
    keys = path.split(".")
    result = _traverse(obj, keys, index_prefix=index_prefix)

    if (not result is None) and (not query is None):
        if is_list_object(result):
            result = list(( item for item in result if is_dict_object(item) and _match(item, query)))

    return default if result is None else result

def set(obj, path, value, index_prefix=None):
    if is_list_object(path):
        for p in path:
            set(obj=obj, path=p, value=value, index_prefix=index_prefix)
        return
    
    keys = path.split(".")
    current = obj
    for key in keys[:-1]:
        is_index, k = _parse_key(key, index_prefix)
        if is_index:
            if not is_list_object(current):
                current.clear() if isinstance(current, dict) else None
                current = []
            while k >= len(current):
                current.append({})
            current = get_value(current, k)
        else:
            if not is_dict_object(current):
                current.clear() if isinstance(current, list) else None
                current = {}
            if not has_key(current, k) or not (is_dict_object(get_value(current, k)) or is_list_object(get_value(current, k))):
                set_value(current, k, {})
            current = get_value(current, k)

    last_is_index, last_key = _parse_key(keys[-1], index_prefix)
    if last_is_index:
        if not is_list_object(current):
            current.clear() if isinstance(current, dict) else None
            current = []
        while last_key >= len(current):
            current.append(None)
        set_value(current, last_key, value)
    else:
        if not is_dict_object(dict):
            current.clear() if isinstance(current, list) else None
            current = {}
        set_value(current, last_key, value)

def delete(obj, path, index_prefix=None):

    if is_list_object(path):
        for p in path:
            delete(obj=obj, path=p, index_prefix=index_prefix)
        return

    keys = path.split(".")
    parent = _traverse(obj, keys[:-1], index_prefix=index_prefix)
    if parent is None:
        return
    last_is_index, last_key = _parse_key(keys[-1], index_prefix)
    if last_is_index and is_list_object(parent) and 0 <= last_key < len(parent):
        if hasattr(parent, 'pop'):
            parent.pop(last_key)
    elif not last_is_index and is_dict_object(parent):
        if hasattr(parent, 'pop'):
            parent.pop(last_key, None)

def unset(obj, path, index_prefix=None):
    delete(obj, path, index_prefix)

def push(obj, path, value, index_prefix=None):
    
    if is_list_object(path):
        for p in path:
            push(obj=obj, path=p, value=value, index_prefix=index_prefix)
        return
    
    target = _traverse(obj, path.split("."), create_missing=True, index_prefix=index_prefix)
    if is_list_object(target):
        if hasattr(target, 'append'):
            target.append(value)
    else:
        set(obj, path, [value], index_prefix=index_prefix)

def pull(obj, path, value=None, index=None, index_prefix=None):
    
    if is_list_object(path):
        for p in path:
            pull(obj=obj, path=p, value=value, index=index, index_prefix=index_prefix)
        return
    
    keys = path.split(".")
    parent = _traverse(obj, keys[:-1], index_prefix=index_prefix)
    if parent is None:
        return
    last_is_index, last_key = _parse_key(keys[-1], index_prefix)
    target_list = None

    if last_is_index and is_list_object(parent) and 0 <= last_key < len(parent) and is_list_object(get_value(parent, last_key)):
        target_list = get_value(parent, last_key)
    elif not last_is_index and is_dict_object(parent) and last_key in parent and is_list_object(get_value(parent, last_key)):
        target_list = get_value(parent, last_key)

    if target_list is None:
        return

    if index is not None and isinstance(index, int) and 0 <= index < len(target_list):
        target_list.pop(index)
    elif value is not None:
        if is_dict_object(value):
            q_indexes = []
            for idx, doc in enumerate(target_list):
                if not is_dict_object(doc):
                    continue
                if _match(doc, value):
                    q_indexes.append(idx)
            for idx in q_indexes[::-1]:
                target_list.pop(idx)
        else:
            parent[last_key if not last_is_index else last_key] = [v for v in target_list if v != value]

def has(obj, path, index_prefix=None):
    
    if is_list_object(path):
        res = []
        for p in path:
            res.append(has(obj=obj, path=p, index_prefix=index_prefix))

        return res
    
    keys = path.split(".")
    current = obj
    for key in keys:
        is_index, k = _parse_key(key, index_prefix)
        if is_index:
            if not is_list_object(current):
                return False
            try:
                current = current[k]
            except (IndexError, TypeError):
                return False
        else:
            if not is_dict_object(current) or not has_key(current, k):
                return False
            current = get_value(current, k)
    return True

def match_condition(item: Dict[str, Any], key: str, condition: Any) -> bool:
    """
    Checks if a single key in the item matches the condition.
    Supports $regex, $options, $lt, $lte, $gt, $gte, $in, $nin.
    """
    value = get(item, key)

    if isinstance(condition, dict):
        for op, op_val in condition.items():
            if op == '$regex':
                flags = 0
                if '$options' in condition:
                    options = condition['$options']
                    if 'i' in options: flags |= re.IGNORECASE
                    if 'm' in options: flags |= re.MULTILINE
                if not isinstance(value, str) or not re.search(op_val, value, flags):
                    return False
            elif op == '$lt':
                if not (value < op_val):
                    return False
            elif op == '$lte':
                if not (value <= op_val):
                    return False
            elif op == '$gt':
                if not (value > op_val):
                    return False
            elif op == '$gte':
                if not (value >= op_val):
                    return False
            elif op == '$in':
                if value not in op_val:
                    return False
            elif op == '$nin':
                if value in op_val:
                    return False
            elif op == '$options':
                continue  # already handled in $regex
            else:
                # Treat as exact match for unknown operator
                if value != condition:
                    return False
        return True
    else:
        return value == condition

def match_item(item: Dict[str, Any], query: Dict[str, Any]) -> bool:
    """
    Recursively checks if the item matches the MongoDB-style query.
    """
    if '$and' in query:
        return all(match_item(item, sub_query) for sub_query in query['$and'])
    if '$or' in query:
        return any(match_item(item, sub_query) for sub_query in query['$or'])

    return all(match_condition(item, k, v) for k, v in query.items())

def find_first(items: List[Dict[str, Any]], query: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Returns the first item in the list that matches the query.
    """
    for item in items:
        if match_item(item, query):
            return item
    return None

def find_all(items: List[Dict[str, Any]], query: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Returns all items in the list that match the query.
    """
    return [item for item in items if match_item(item, query)]
