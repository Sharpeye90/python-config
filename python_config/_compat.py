from __future__ import unicode_literals

import sys

_PY2 = sys.version_info < (3,)
if _PY2:
    str = unicode


_BASIC_TYPES = (bool, int, float, bytes, str)
"""Python basic types."""

if _PY2:
    _BASIC_TYPES += (long,)

_COMPLEX_TYPES = (tuple, list, set, dict)
"""Python complex types."""

_VALID_TYPES = _BASIC_TYPES + _COMPLEX_TYPES
"""Option value must be one of these types."""
