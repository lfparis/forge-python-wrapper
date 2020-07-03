# -*- coding: utf-8 -*-

"""Validation Decorators"""

from __future__ import absolute_import

import sys

from datetime import datetime
from functools import wraps

from .base import ForgeBase

if sys.version_info >= (3, 7):
    from .extra.decorators import _async_validate_token  # noqa: F401


def _validate_app(func):
    """Project"""

    @wraps(func)
    def inner(self, *args, **kwargs):
        if not self.app:
            raise AttributeError("An 'app' attribute has not been defined")
        return func(self, *args, **kwargs)

    return inner


def _validate_bim360_hub(func):
    """Forge App & Project"""

    @wraps(func)
    def inner(self, *args, **kwargs):
        if getattr(self, "app", None):
            this = self.app
        else:
            this = self

        if this.auth.three_legged:
            raise ValueError(
                "The BIM 360 API only supports 2-legged access token."
            )
        elif not this.hub_id:
            raise AttributeError("A 'app.hub_id' has not been defined.")
        elif this.hub_id[:2] != "b.":
            raise ValueError(
                "The 'app.hub_id' must be a {} hub.".format(
                    ForgeBase.NAMESPACES["b."]
                )
            )
        return func(self, *args, **kwargs)

    return inner


def _validate_host(func):
    """Content"""

    @wraps(func)
    def inner(self, *args, **kwargs):
        if not self.host:
            raise AttributeError("An 'host' attribute has not been defined.")
        return func(self, *args, **kwargs)

    return inner


def _validate_hub(func):
    """Forge App"""

    @wraps(func)
    def inner(self, *args, **kwargs):
        if not self.hub_id:
            raise AttributeError("A 'app.hub_id' has not been defined.")
        return func(self, *args, **kwargs)

    return inner


def _validate_item(func):
    """Version"""

    @wraps(func)
    def inner(self, *args, **kwargs):
        if not self.item:
            raise AttributeError("An 'item' attribute has not been defined.")
        return func(self, *args, **kwargs)

    return inner


def _validate_project(func):
    """Content"""

    @wraps(func)
    def inner(self, *args, **kwargs):
        if not self.project:
            raise AttributeError(
                "An 'project' attribute has not been defined."
            )
        return func(self, *args, **kwargs)

    return inner


def _validate_token(func):
    """DM & HQ"""

    @wraps(func)
    def inner(self, *args, **kwargs):
        now = datetime.now()
        timedelta = int((now - self.auth.timestamp).total_seconds()) + 1
        if timedelta >= int(self.auth.expires_in):
            self.auth.timestamp = now
            self.auth.refresh()
        return func(self, *args, **kwargs)

    return inner


def _validate_x_user_id(func):
    """Project"""

    @wraps(func)
    def inner(self, *args, **kwargs):
        if not self.app.auth.three_legged and not self.x_user_id:
            raise AttributeError(
                "An 'x_user_id' attribute has not been defined"
            )
        return func(self, *args, **kwargs)

    return inner
