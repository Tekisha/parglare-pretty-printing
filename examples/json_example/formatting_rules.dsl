rule Json(value) = format(value);

rule JsonObject(members) =
    text("{") ++
    nest(2, softline() ++ list(members, item, text(",") ++ line())) ++
    softline() ++
    text("}");

rule JsonMember(key, value) =
    format(key) ++ text(": ") ++ format(value);

rule JsonArray(values) =
    text("[") ++
    nest(2, softline() ++ list(values, item, text(",") ++ line())) ++
    softline() ++
    text("]");

rule JsonString(value) =
    text("\"") ++ value ++ text("\"");

rule JsonNumber(value) =
    value;

rule JsonBool(value) =
    value;

rule JsonNull() =
    text("null");