"""Static extraction of semantic link annotations from Python source.

Parses Python source files using the ``ast`` module to collect
``md_ref``, ``md_block``, and ``md_anchor`` declarations without
executing the code.

Each extracted record is a dictionary with the following keys:

    type : str
        One of ``"md_ref"``, ``"md_block"``, or ``"md_anchor"``.
    label : str
        The TP requirement or equation label.
    note : str or None
        Optional descriptive note.
    qualname : str
        Qualified name of the enclosing function or method
        (e.g. ``"Calibrator.correct"``).
    line : int
        Source line number.
    end_line : int
        Last line of the block (``md_block`` records only).
    file : str
        Source file path.
"""

import ast
from pathlib import Path

#----------------------------------------------------------------------------
class Extractor(ast.NodeVisitor):
    """Extract md_ref, md_block, and md_anchor from Python source."""

    def __init__(self, filepath):
        self.filepath = str(filepath)
        self.scope_stack = []  # tracks class/function nesting
        self.records = []

    # --- scope tracking ---

    def _qualname(self, name):
        parts = self.scope_stack + [name]
        return ".".join(parts)

    # --- label extraction helpers ---

    @staticmethod
    def _is_call_to(node, name):
        """True if node is a Call whose function name matches."""
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == name
        )

    @staticmethod
    def _extract_label_and_note(call_node):
        """Return (label, note) from positional args of a Call."""
        args = call_node.args
        label = ast.literal_eval(args[0]) if len(args) >= 1 else None
        note = ast.literal_eval(args[1]) if len(args) >= 2 else None
        return label, note

    # --- visitors ---

    def visit_ClassDef(self, node):
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_FunctionDef(self, node):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node)

    def _visit_function(self, node):
        qualname = self._qualname(node.name)

        # check decorators for @md_ref(...)
        for dec in node.decorator_list:
            if self._is_call_to(dec, "md_ref"):
                label, note = self._extract_label_and_note(dec)
                self.records.append({
                    "type": "md_ref",
                    "label": label,
                    "note": note,
                    "qualname": qualname,
                    "line": dec.lineno,
                    "file": self.filepath,
                })

        # descend into the function body
        self.scope_stack.append(node.name)
        for child in ast.iter_child_nodes(node):
            self._visit_body_node(child, qualname)
        self.scope_stack.pop()

    def _visit_body_node(self, node, enclosing_qualname):
        """Walk statements inside a function looking for anchors and blocks."""

        # md_anchor("label", "note")
        if (
            isinstance(node, ast.Expr)
            and self._is_call_to(node.value, "md_anchor")
        ):
            label, note = self._extract_label_and_note(node.value)
            self.records.append({
                "type": "md_anchor",
                "label": label,
                "note": note,
                "qualname": enclosing_qualname,
                "line": node.lineno,
                "file": self.filepath,
            })

        # with md_block("label", "note"):
        elif isinstance(node, ast.With):
            for item in node.items:
                if self._is_call_to(item.context_expr, "md_block"):
                    label, note = self._extract_label_and_note(
                        item.context_expr
                    )
                    self.records.append({
                        "type": "md_block",
                        "label": label,
                        "note": note,
                        "qualname": enclosing_qualname,
                        "line": node.lineno,
                        "end_line": node.end_lineno,
                        "file": self.filepath,
                    })

        # recurse into nested structures (if, for, with, try, etc.)
        for child in ast.iter_child_nodes(node):
            self._visit_body_node(child, enclosing_qualname)

#----------------------------------------------------------------------------
def extract(source_path):
    """Extract all records from a single Python file.

    Parameters
    ----------
    source_path : str or Path
        Path to a Python source file.

    Returns
    -------
    list of dict
        Extracted records.
    """
    path = Path(source_path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    extractor = Extractor(path)
    extractor.visit(tree)
    return extractor.records

#----------------------------------------------------------------------------
def extract_from(root_dir, pattern="**/*.py"):
    """Extract records from all Python files under a directory.

    Parameters
    ----------
    root_dir : str or Path
        Root directory to search.
    pattern : str
        Glob pattern for matching files.

    Returns
    -------
    list of dict
        Extracted records from all matched files.
    """
    records = []
    for path in Path(root_dir).glob(pattern):
        records.extend(extract(path))
    return records