import pytest

from src.parglare_formatter.document_model import (
    Text, Line, Concat, Nest, Group, Align, Empty,
    text, line, softline, concat, nest, group, align, empty, concat_all,
)


class TestDataclassConstruction:
    def test_text_construction(self):
        t = Text("hello")
        assert t.s == "hello"

    def test_line_default_is_soft(self):
        l = Line()
        assert l.soft is True

    def test_line_hard(self):
        l = Line(soft=False)
        assert l.soft is False

    def test_concat_construction(self):
        c = Concat(Text("a"), Text("b"))
        assert isinstance(c.left, Text)
        assert isinstance(c.right, Text)
        assert c.left.s == "a"
        assert c.right.s == "b"

    def test_nest_construction(self):
        n = Nest(2, Text("x"))
        assert n.indent == 2
        assert isinstance(n.doc, Text)

    def test_group_construction(self):
        g = Group(Text("x"))
        assert isinstance(g.doc, Text)

    def test_align_construction(self):
        a = Align(Text("x"))
        assert isinstance(a.doc, Text)

    def test_empty_construction(self):
        e = Empty()
        assert isinstance(e, Empty)

    def test_dataclasses_are_frozen(self):
        t = Text("hello")
        with pytest.raises(Exception):
            t.s = "changed"

    def test_dataclasses_support_equality(self):
        assert Text("a") == Text("a")
        assert Text("a") != Text("b")
        assert Line(soft=True) == Line(soft=True)
        assert Nest(2, Text("a")) == Nest(2, Text("a"))


class TestCombinators:
    def test_text_combinator_returns_text_instance(self):
        d = text("foo")
        assert isinstance(d, Text)
        assert d.s == "foo"

    def test_text_combinator_rejects_non_str(self):
        with pytest.raises(TypeError):
            text(123)  # type: ignore[arg-type]

    def test_line_combinator_is_hard_line(self):
        d = line()
        assert isinstance(d, Line)
        assert d.soft is False

    def test_softline_combinator_is_soft_line(self):
        d = softline()
        assert isinstance(d, Line)
        assert d.soft is True

    def test_concat_combinator_returns_concat_instance(self):
        d = concat(text("a"), text("b"))
        assert isinstance(d, Concat)
        assert d.left == Text("a")
        assert d.right == Text("b")

    def test_nest_combinator_returns_nest_instance(self):
        d = nest(4, text("body"))
        assert isinstance(d, Nest)
        assert d.indent == 4
        assert d.doc == Text("body")

    def test_group_combinator_returns_group_instance(self):
        d = group(text("x"))
        assert isinstance(d, Group)
        assert d.doc == Text("x")

    def test_align_combinator_returns_align_instance(self):
        d = align(text("x"))
        assert isinstance(d, Align)
        assert d.doc == Text("x")

    def test_empty_combinator_returns_empty_instance(self):
        d = empty()
        assert isinstance(d, Empty)


class TestCombinatorComposition:
    def test_nested_group_and_nest(self):
        doc = group(nest(2, concat(text("a"), concat(softline(), text("b")))))
        assert isinstance(doc, Group)
        assert isinstance(doc.doc, Nest)
        assert doc.doc.indent == 2
        inner = doc.doc.doc
        assert isinstance(inner, Concat)
        assert inner.left == Text("a")
        assert isinstance(inner.right, Concat)
        assert inner.right.left == Line(soft=True)
        assert inner.right.right == Text("b")

    def test_concat_all_builds_left_associative_chain(self):
        doc = concat_all(text("a"), text("b"), text("c"))
        # concat_all(a, b, c) == concat(concat(concat(empty(), a), b), c)
        assert isinstance(doc, Concat)
        assert doc.right == Text("c")
        assert isinstance(doc.left, Concat)
        assert doc.left.right == Text("b")
        assert isinstance(doc.left.left, Concat)
        assert doc.left.left.right == Text("a")
        assert doc.left.left.left == Empty()

    def test_concat_all_empty_args_returns_empty(self):
        doc = concat_all()
        assert isinstance(doc, Empty)

    def test_align_wrapping_group(self):
        doc = align(group(concat(text("x"), softline())))
        assert isinstance(doc, Align)
        assert isinstance(doc.doc, Group)


class TestUnionTypeCoverage:
    """Provera da Doc union pokriva svih 7 varijanti tipa."""

    def test_all_variants_are_valid_doc_instances(self):
        docs = [
            text("t"),
            line(),
            softline(),
            concat(text("a"), text("b")),
            nest(1, text("a")),
            group(text("a")),
            align(text("a")),
            empty(),
        ]
        expected_types = (Text, Line, Line, Concat, Nest, Group, Align, Empty)
        for d, expected in zip(docs, expected_types):
            assert isinstance(d, expected)