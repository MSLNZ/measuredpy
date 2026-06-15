"""
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
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List, Tuple, Union

class TermKind(Enum):
    """Epistemic classification of a quantity term."""
    KNOWN = auto()
    UNKNOWN = auto()
    RESIDUAL = auto()

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
        "=", "+", "-", "/", 
        "\\cdot", "\\times", "\\div",
    )
 
    classification_rules: list = None

    def __post_init__(self):
        if self.classification_rules is None:
            # Default: case-based with E as residual
            self.classification_rules = [
                (r"^E$",    TermKind.RESIDUAL),
                (r"^[a-z]", TermKind.KNOWN),
                (r"^[A-Z]", TermKind.UNKNOWN),
            ]
           
        # # A different set of rules           
        # classification_rules=[
            # (r"^\\Delta$",        TermKind.RESIDUAL),
            # (r"^\\hat\{.*\}$",    TermKind.KNOWN),
            # (r".*",               TermKind.UNKNOWN),
        # ]

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
    kind: Optional[TermKind] = None
    namespace: Optional[List[str]] = None
    qualifier: Optional[List[str]] = None
    association: Optional[List[str]] = None

Token = Union[MdTerm, str]

# ── Helpers ──────────────────────────────────────────────────────
#
def classify_body(body: str, config: MdTermConfig) -> Optional[TermKind]:
    """Classify a term body by epistemic status.

    Applies config.classification_rules in order; returns the
    TermKind for the first matching rule, or None if no rule
    matches."""
    for pattern, kind in config.classification_rules:
        if re.match(pattern, body):
            return kind
    return None

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
            results.append(MdTerm(
                body=t,
                kind=classify_body(t, config),
            ))
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
    """Split an argument string by separator, respecting brace
    grouping.  Separators inside {...} are ignored."""
    if separator is None:
        return [text.strip()]
    parts = []
    depth = 0
    start = 0
    for i, ch in enumerate(text):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        elif ch == separator and depth == 0:
            parts.append(text[start:i].strip())
            start = i + 1
    parts.append(text[start:].strip())
    return parts

# ── Parser ──────────────────────────────────────────────────────
#
def parse_mdterms(text: str, 
                    config: MdTermConfig = None) -> List[Token]:
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
            kind=classify_body(body, config),
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