
"""cleantex — Remove formatting markup from LaTeX equation bodies.

Reads sidecar files containing the body of LaTeX equation,
equation+split, or multline environments and strips formatting
commands, spacing adjustments, line breaks, and trailing
punctuation, leaving only the mathematical content (including
any \\label).

The sets of strings and patterns to remove are defined in
module-level constants and can be extended as needed.

Bodies containing \\left. or \\right. (unpaired delimiters)
are treated as invalid and skipped with a warning.

Usage:
    python cleantex.py FILE [FILE ...]
"""
import sys
import re

# ── Configurable removal lists ──────────────────────────────────
#
# REMOVE_STRINGS: exact strings to strip from the body.
#   • Put longer strings before shorter substrings
#     (e.g. \qquad before \quad).
#   • Add new entries as needed.
#
# TRAILING_PUNCTUATION: characters to strip from the very end
#   of the body (applied after all other cleaning).

REMOVE_STRINGS = [
    r"\nonumber",
    r"\notag",
    r"\qquad",
    r"\quad",
    r"\left",
    r"\right",
    r"\,",
    r"\;",
    r"\:",
    r"\!",
    "&",
]

TRAILING_PUNCTUATION = ".,;"


# Validate: \left. and \right. indicate an unpaired delimiter
INVALID_PATTERNS = [
    (r"\\left\s*\.",  r"\left."),
    (r"\\right\s*\.", r"\right."),
]

# ── End of configurable lists ───────────────────────────────────


def clean_body(text):
    """Remove formatting markup and trailing punctuation from a
    LaTeX math-environment body, keeping the mathematics and any
    \\label intact.

    Args:
        text:   Body content of an equation environment.
        source: Filename for warning messages.

    Returns:
        Cleaned text, or None if the body is invalid.
    """

    for pattern, label in INVALID_PATTERNS:
        if re.search(pattern, text):
            print(f"Warning: '{source}' contains {label} "
                  f"(unpaired delimiter); skipping.",
                  file=sys.stderr)
            return None

    # 1. Remove each exact string
    for s in REMOVE_STRINGS:
        text = text.replace(s, "")

    # 2. \big-family sizing commands
    text = re.sub(r"\\[Bb]igg?[lrm]?(?![a-zA-Z])", "", text)

    # 3. Line-break commands: \\ or \\[<length>]
    text = re.sub(r"\\\\(\[[^\]]*\])?", "", text)

    # 4. Strip trailing punctuation (after trimming whitespace)
    text = text.rstrip()
    text = text.rstrip(TRAILING_PUNCTUATION)

    # 4. Tidy whitespace: collapse runs, remove blank lines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


def main():
    """Process sidecar files given on the command line."""
    filenames = sys.argv[1:]

    if not filenames:
        print("Usage: python strip_markup.py FILE [FILE ...]",
              file=sys.stderr)
        sys.exit(1)

    for filename in filenames:
        try:
            with open(filename, encoding="utf-8") as f:
                content = f.read()
            print(clean_body(content))
        except FileNotFoundError:
            print(f"Error: '{filename}' not found.", file=sys.stderr)
        except PermissionError:
            print(f"Error: no read permission for '{filename}'.",
                  file=sys.stderr)


if __name__ == "__main__":
    main()