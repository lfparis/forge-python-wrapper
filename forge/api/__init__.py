"""Provide the Forge API models."""

from __future__ import absolute_import

from ..base import ForgeBase
from .dm import DM
from .hq import HQ


class ForgeApi(ForgeBase):
    def __init__(self, *args, **kwargs):
        self.dm = DM(*args, **kwargs)
        self.hq = HQ(*args, **kwargs)
