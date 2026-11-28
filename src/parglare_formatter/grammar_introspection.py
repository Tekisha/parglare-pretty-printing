import re
from typing import Dict, Optional, Tuple
from parglare.grammar import NonTerminal, Terminal

SeparatorMap = Dict[Tuple[str, str], str]

#a_0, a_1, a_0_comma, a_1_comma, ...
_REPETITION_RULE = re.compile(r"_[01](_\w+)?$")
_LIST_MULTIPLICITIES = ("0..*", "1..*")


def _get(obj, key):
    return obj[key] if isinstance(obj, dict) else getattr(obj, key)


def _literal_of(symbol) -> Optional[str]:
    """Terminal's text if it is a string recognizer, otherwise None."""
    if not isinstance(symbol, Terminal):
        return None
    recognizer = symbol.recognizer
    if type(recognizer).__name__ != "StringRecognizer":
        return None
    return getattr(recognizer, "value", None)


def _separator_symbol(repetition_symbol):
    """Walks through the helper repetition rules and looks for a production
    of the form  R: R sep element  (left-recursive, three elements)."""
    seen, stack = set(), [repetition_symbol]
    while stack:
        sym = stack.pop()
        if (not isinstance(sym, NonTerminal)
                or sym.name in seen
                or not _REPETITION_RULE.search(sym.name)):
            continue
        seen.add(sym.name)
        for prod in sym.productions:
            rhs = prod.rhs
            if len(rhs) == 3 and rhs[0].name == sym.name:
                return rhs[1]
            if len(rhs) == 1:
                stack.append(rhs[0])
    return None


def extract_list_separators(grammar) -> SeparatorMap:
    """(rule_name, attribute_name) -> separator literal, for every
    named match of the form  attr=X*[sep]  or  attr=X+[sep]."""
    result: SeparatorMap = {}
    for prod in grammar.productions:
        assignments = getattr(prod, "assignments", None) or {}
        for attr_name, assignment in assignments.items():
            if _get(assignment, "multiplicity") not in _LIST_MULTIPLICITIES:
                continue
            repetition = prod.rhs[_get(assignment, "index")]
            sep = _separator_symbol(repetition)
            literal = _literal_of(sep) if sep is not None else None
            if literal is not None:
                result[(prod.symbol.name, attr_name)] = literal
    return result