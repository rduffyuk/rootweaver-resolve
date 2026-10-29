"""Strict public JSON schema-location validation; no experiment adapters."""

def _failure(schema, value, path=""):
    types = {"object": dict, "array": list, "string": str, "null": type(None)}
    if schema.get("type") in types and not isinstance(value, types[schema["type"]]):
        return path or "/", "type:" + schema["type"]
    if "enum" in schema and value not in schema["enum"]:
        return path or "/", "enum"
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                return path + "/" + key, "required"
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            return path + "/<unknown>", "additionalProperties:false"
        for key, child in properties.items():
            if key in value:
                error = _failure(child, value[key], path + "/" + key)
                if error:
                    return error
    if isinstance(value, (list, str)):
        suffix = "Items" if isinstance(value, list) else "Length"
        for prefix, compare in [
            ("min", lambda a, b: a < b),
            ("max", lambda a, b: a > b),
        ]:
            constraint = prefix + suffix
            if constraint in schema and compare(len(value), schema[constraint]):
                return path or "/", constraint + ":" + str(schema[constraint])
    if isinstance(value, list):
        for index, item in enumerate(value):
            error = _failure(schema.get("items", {}), item, path + "/" + str(index))
            if error:
                return error
    return None
