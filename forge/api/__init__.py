# -*- coding: utf-8 -*-

"""Provide the Forge API models."""

from __future__ import absolute_import

import sys


class ForgeApi:
    def __init__(self, *args, async_apis=False, **kwargs):
        if async_apis:
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
