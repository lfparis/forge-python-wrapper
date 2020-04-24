from __future__ import absolute_import

import sys

from .forge import ForgeApp  # noqa: F401

if sys.version_info >= (3, 7):
    from .forge_async import ForgeAppAsync  # noqa: F401
