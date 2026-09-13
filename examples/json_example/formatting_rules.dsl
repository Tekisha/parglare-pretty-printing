rule Json(node) = format(node.value);

rule JsonObject(node) =
    text("{") ++
    nest(2, softline() ++ list(node.members, item, text(",") ++ line())) ++
    softline() ++
    text("}");

rule JsonMember(node) =
    format(node.key) ++ text(": ") ++ format(node.value);

rule JsonArray(node) =
    text("[") ++
    nest(2, softline() ++ list(node.values, item, text(",") ++ line())) ++
    softline() ++
    text("]");

rule JsonString(node) =
    text("\"") ++ node.value ++ text("\"");

rule JsonNumber(node) =
    node.value;

rule JsonBool(node) =
    node.value;

rule JsonNull(node) =
    text("null");