import json


class Json:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Json({self.value!r})"


class JsonString:
    def __init__(self, value):
        self.value = json.loads(value)

    def __repr__(self):
        return f"JsonString({self.value!r})"


class JsonNumber:
    def __init__(self, value):
        self.value = float(value)

    def __repr__(self):
        return f"JsonNumber({self.value!r})"


class JsonBool:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"JsonBool({self.value!r})"


class JsonNull:
    def __repr__(self):
        return "JsonNull()"


class JsonObject:
    def __init__(self, members):
        self.members = members or []

    def __repr__(self):
        return f"JsonObject({self.members!r})"


class JsonMember:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return f"JsonMember({self.key!r}, {self.value!r})"


class JsonArray:
    def __init__(self, values):
        self.values = values or []

    def __repr__(self):
        return f"JsonArray({self.values!r})"