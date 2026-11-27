from parglare_formatter.formatter import Formatter


def test_clean_rules_have_no_problems():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, statement);
        rule statement_Value = format(node) ++ ";";
        rule Value = node.value;
        """
    )

    assert formatter.check() == []


def test_unknown_context_is_reported():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, statment);
        rule statement_Value = format(node) ++ ";";
        """
    )

    problems = formatter.check()

    assert any("'statment'" in p and "Container" in p for p in problems)


def test_unused_contextual_rule_is_reported():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, statment);
        rule statement_Value = format(node) ++ ";";
        """
    )

    problems = formatter.check()

    assert any("statement_Value" in p for p in problems)


def test_context_with_underscore_is_recognised():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, before_else);
        rule before_else_Value = format(node);
        """
    )

    assert formatter.check() == []


def test_check_does_not_change_formatting():
    source = """
        rule Container = format(node.child, statment);
        rule statement_Value = format(node) ++ ";";
    """
    formatter = Formatter.from_dsl_source(source)

    formatter.check()
    formatter.check()

    assert formatter.check() == formatter.check()