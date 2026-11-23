rule Json = format(node.value);

rule JsonObject =
    text("{") ++
    nest(2,
        softline() ++
        list(node.members, item)
    ) ++
    softline() ++
    text("}");

rule JsonMember =
    format(node.key) ++ text(": ") ++ format(node.value);

rule JsonArray =
    group(
        text("[") ++
        nest(2,
            softline() ++
            list(node.values, item)
        ) ++
        softline() ++
        text("]")
    );

rule JsonString =
    text("\"") ++ escaped(node.value) ++ text("\"");

rule JsonNumber =
    node.value;

rule JsonBool =
    lower(node.value);

rule JsonNull =
    text("null");