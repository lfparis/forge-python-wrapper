# -*- coding: utf-8 -*-

"""Provide the Forge API models."""

from __future__ import absolute_import


class ForgeApi:
    def __init__(self, *args, **kwargs):
        if kwargs.get("async_apis"):
            import sys

            assert sys.version_info >= (3, 7), "Python 3.7+ is required."
            from .adm import ADM
            from .ahq import AHQ

            self.hq = AHQ(*args, **kwargs)
            self.dm = ADM(*args, **kwargs)
        else:
            from .dm import DM
            from .hq import HQ

            self.dm = DM(*args, **kwargs)
            self.hq = HQ(*args, **kwargs)
