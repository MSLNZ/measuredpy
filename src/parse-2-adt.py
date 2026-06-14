"""mdterm — Parse \\mdterm invocations into structured objects.

Parses the body of a LaTeX equation environment (assumed to have
been pre-cleaned of formatting markup) and returns a list of
Token objects: MdTerm instances for semantic terms and plain
strings for mathematical operators.

The \\mdterm LaTeX command has the form:

    \\mdterm[namespaces]{body}[qualifiers](associations)

where only {body} is mandatory.  Arguments may contain \\tv{...}
to indicate template parameters (preserved as-is in the output).

Parsing behaviour is configured via MdTermConfig, which controls
argument separators and the set of recognised operator tokens.

Usage:
    from mdterm import MdTermConfig, MdTerm, parse_mdterms

    config = MdTermConfig(namespace_sep="-")
    tokens = parse_mdterms(equation_body, config)
"""
import re
from dataclasses import dataclass
from typing import Optional, List, Tuple
from typing import Union

# ── Argument separators ─────────────────────────────────────────
# Character used to separate multiple values within an argument.
# Set to None to treat the whole argument as a single value.

@dataclass
class MdTermConfig:
    """Configuration for parsing \\mdterm invocations,
    reflecting conventions adopted by the LaTeX user.

    Attributes:
        namespace_sep:   Separator for multiple namespaces,
                         e.g. "," for [ns1,ns2] or "-" for [ns1-ns2].
                         None means the whole argument is one value.
        qualifier_sep:   Separator for multiple qualifiers.
        association_sep: Separator for multiple associations.
        operator_tokens: Tokens recognised as mathematical operators.
                         These are kept in the output as plain strings
                         rather than being promoted to MdTerm objects.
    """


    namespace_sep: Optional[str] = ","
    qualifier_sep: Optional[str] = ","
    association_sep: Optional[str] = ","
    
    operator_tokens: tuple = (
        "=", "+", "-", "\\cdot", "\\times", "\\leq", "\\geq",
        "\\neq", "\\approx", "\\equiv", "\\pm", "\\mp",
        "\\sum", "\\prod", "\\int", "\\infty",
    )
  
@dataclass
class MdTerm:
    """A semantic term parsed from an \\mdterm invocation, or a
    plain mathematical symbol not wrapped in \\mdterm.

    For a plain symbol, only body is set; the other fields are None.

    Attributes:
        body:        The mandatory argument (symbol or expression).
        namespace:   Optional list of namespace labels, or None.
        qualifier:   Optional list of qualifier labels, or None.
        association: Optional list of association labels, or None.
                     May contain raw \\tv{...} strings indicating
                     template parameters.
    """
    body: str

    namespace: Optional[List[str]] = None
    qualifier: Optional[List[str]] = None
    association: Optional[List[str]] = None

Token = Union[MdTerm, str]

# ── Helpers ──────────────────────────────────────────────────────
#
def _tokenise_plain(text: str, config: MdTermConfig) -> list:
    """Tokenise a gap between \\mdterm invocations.
    Maths symbols become MdTerm objects; operators and relations
    remain as plain strings."""
    results = []
    for tok in re.finditer(r"\\[a-zA-Z]+|[^\s{}]", text):
        t = tok.group()
        if t in config.operator_tokens:
            results.append(t)
        else:
            results.append(MdTerm(body=t))
    return results


def _skip_whitespace(text: str, pos: int) -> int:
    """Advance past whitespace."""
    while pos < len(text) and text[pos] in " \t\n\r":
        pos += 1
    return pos


def _extract_braced(text: str, pos: int) -> Tuple[str, int]:
    """Extract content of {…}, handling nested braces.
    pos must point at the opening '{'.
    Returns (content, position after closing '}')."""
    assert text[pos] == "{"
    depth = 1
    start = pos + 1
    pos = start
    while pos < len(text) and depth > 0:
        if text[pos] == "{":
            depth += 1
        elif text[pos] == "}":
            depth -= 1
        pos += 1
    return text[start:pos - 1], pos


def _extract_delimited(text: str, pos: int,
                        open_ch: str, close_ch: str
                        ) -> Tuple[str, int]:
    """Extract content between open_ch and close_ch.
    Respects brace grouping: close_ch inside {…} is hidden.
    pos must point at open_ch.
    Returns (content, position after close_ch)."""
    assert text[pos] == open_ch
    start = pos + 1
    pos = start
    brace_depth = 0
    while pos < len(text):
        ch = text[pos]
        if ch == "{":
            brace_depth += 1
        elif ch == "}":
            brace_depth -= 1
        elif ch == close_ch and brace_depth == 0:
            return text[start:pos], pos + 1
        pos += 1
    raise ValueError(
        f"Unmatched '{open_ch}' at position {start - 1}")

def _split_argument(text: str, separator: str = None) -> list:
    """Split an argument string by separator, stripping whitespace
    from each part.  If separator is None, return a single-element
    list."""
    if separator is None:
        return [text.strip()]
    return [part.strip() for part in text.split(separator)]

# ── Parser ──────────────────────────────────────────────────────
#
def parse_mdterms(text: str, config: MdTermConfig = None) -> List:
    """Parse a cleaned equation body into a list of Tokens.

    Pass 1: find all \\mdterm invocations and record their
            positions and parsed MdTerm objects.
    Pass 2: tokenise the gaps between invocations, promoting
            plain symbols to MdTerm and keeping operators as
            strings.

    Args:
        text:   The body of a LaTeX equation environment, after
                formatting markup has been removed.
        config: Parsing configuration.  If None, defaults are used.

    Returns:
        A list of Token (Union[MdTerm, str]) in order of
        appearance.  Strings represent mathematical operators;
        MdTerm objects represent semantic terms.
    """
    if config is None:
        config = MdTermConfig()

    # Pass 1: collect \mdterm invocations and their spans
    spans = []  # (start, end, MdTerm)
    pattern = re.compile(r"\\mdterm(?![a-zA-Z])")

    for match in pattern.finditer(text):
        start = match.start()
        pos = match.end()

        namespace = None
        pos = _skip_whitespace(text, pos)
        if pos < len(text) and text[pos] == "[":
            namespace, pos = _extract_delimited(
                text, pos, "[", "]")
            namespace = _split_argument(
                namespace, config.namespace_sep)

        pos = _skip_whitespace(text, pos)
        if pos < len(text) and text[pos] == "{":
            body, pos = _extract_braced(text, pos)
        else:
            continue

        qualifier = None
        pos = _skip_whitespace(text, pos)
        if pos < len(text) and text[pos] == "[":
            qualifier, pos = _extract_delimited(
                text, pos, "[", "]")
            qualifier = _split_argument(
                qualifier, config.qualifier_sep)

        association = None
        pos = _skip_whitespace(text, pos)
        if pos < len(text) and text[pos] == "(":
            association, pos = _extract_delimited(
                text, pos, "(", ")")
            association = _split_argument(
                association, config.association_sep)

        spans.append((start, pos, MdTerm(
            body=body,
            namespace=namespace,
            qualifier=qualifier,
            association=association,
        )))

    # Pass 2: interleave plain terms from gaps
    results = []
    prev_end = 0

    for start, end, term in spans:
        gap = text[prev_end:start]
        results.extend(_tokenise_plain(gap, config))
        results.append(term)
        prev_end = end

    gap = text[prev_end:]
    results.extend(_tokenise_plain(gap, config))

    return results
  
# ===========================================================================  
if __name__ == "__main__":

    cfg = MdTermConfig(namespace_sep="-")
    
    eq = r'''\mdterm{f}  
	+ \mdterm[gen-msl]{O}[fix](\tv{f}) 
	+ \mdterm[gen]{E}[rnd](\tv{f,i})
	+ \mdterm[gen]{E}[res](\tv{f})
	- \mdterm[MSL]{E}[ref]
    - x'''
    
    for i in parse_mdterms(eq,cfg):
        print(i)