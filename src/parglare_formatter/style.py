from dataclasses import dataclass

@dataclass
class Style:
    indent_width: int = 2
    array_break_threshold: int = 3
    space_around_binary_ops: bool = True
    newline_between_top_level_exprs: bool = True