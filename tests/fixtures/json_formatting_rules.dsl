rule Json(node) = format(node.value);

rule JsonObject(node) =
    text("{") ++
    nest(2,
        softline() ++
        list(node.members, item, text(",") ++ softline())
    ) ++
    softline() ++
    text("}");

rule JsonMember(node) =
    format(node.key) ++ text(": ") ++ format(node.value);

rule JsonArray(node) =
    group(
        text("[") ++
        nest(2,
            softline() ++
            list(node.values, item, text(",") ++ softline())
        ) ++
        softline() ++
        text("]")
    );

rule JsonString(node) =
    text("\"") ++ escaped(node.value) ++ text("\"");

rule JsonNumber(node) =
    node.value;

rule JsonBool(node) =
    lower(node.value);

rule JsonNull(node) =
    text("null");