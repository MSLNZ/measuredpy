"""Annotations for declaring semantic links between code and technical procedures.

Provides constructs for annotating Python source with references to
technical procedure (TP) requirements, and tools for statically
extracting those annotations.

Annotation constructs (from ``core``):
    md_ref      Decorator for functions and methods.
    md_block    Context manager for code regions.
    md_anchor   Marker call for single points.

Extraction (from ``extract``):
    extract         Extract records from a single file.
    extract_from    Extract records from a directory tree.
    Extractor       The underlying AST visitor.
"""

from .core import md_anchor, md_block, md_ref
from .extract import Extractor, extract, extract_from

__version__ = "0.1.0"

__all__ = [
    "md_anchor", "md_block", "md_ref",
    "Extractor", "extract", "extract_from",
]
