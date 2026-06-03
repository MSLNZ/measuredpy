"""Annotations for declaring semantic links between code and technical procedures.

This module provides three constructs for declaring links between
implementation code and requirements defined in a technical
procedure (TP).  All three are designed to be statically extractable
using the ``ast`` module without executing the source.

Constructs
----------
md_ref
    Decorator.  Declares that a function or method implements a TP
    requirement.
md_block
    Context manager.  Marks a region of code that addresses a specific
    TP requirement.
md_anchor
    Marker call.  Marks a point in the code that corresponds to a TP
    requirement or equation.

Labels
------
Every construct takes a *label* string as its first argument.  Labels
should match those declared in the TP source (e.g. ``eq:Y``,
``req:noise-reduction``).
"""

from contextlib import contextmanager

def md_ref(label):
    """Declare that a function or method implements a TP requirement.

    Parameters
    ----------
    label : str
        The TP requirement label (e.g. ``"req:calibration"``).

    Returns
    -------
    callable
        An identity decorator.

    Examples
    --------
    >>> @md_ref("req:calibration")
    ... def compute_result(readings):
    ...     pass
    """
    def decorator(obj):
        return obj
    return decorator


@contextmanager
def md_block(label, note=None):
    """Mark a block of code that addresses a TP requirement.

    Parameters
    ----------
    label : str
        The TP requirement label.
    note : str, optional
        A short description of what this block does.

    Examples
    --------
    >>> with md_block("req:noise-reduction", "average repeated observations"):
    ...     pass
    """
    yield


def md_anchor(label, note=None):
    """Mark a point in the code corresponding to a TP requirement.

    Parameters
    ----------
    label : str
        The TP requirement or equation label.
    note : str, optional
        A short description.

    Examples
    --------
    >>> md_anchor("eq:Y", "measurement model")
    """
    pass
    


    
