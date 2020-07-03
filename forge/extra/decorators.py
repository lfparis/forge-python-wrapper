# -*- coding: utf-8 -*-

"""Validation Decorators"""

from __future__ import absolute_import

from datetime import datetime
from functools import wraps


def _async_validate_token(func):
    """DM & HQ"""

    @wraps(func)
    async def inner(self, *args, **kwargs):
        now = datetime.now()
        timedelta = int((now - self.app.auth.timestamp).total_seconds()) + 1
        if timedelta >= int(self.app.auth.expires_in):
            self.app.auth.timestamp = now
            self.app.auth.refresh()
            self.app._session.headers = self.app.auth.header
        return await func(self, *args, **kwargs)

    return inner
