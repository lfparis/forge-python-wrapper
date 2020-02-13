from __future__ import absolute_import

import re
import urllib

from datetime import date, timedelta

from .session import Session
from .utils import Logger  # noqa:F401


class ForgeBase(object):
    """
    Superclass for all api model classes in this Forge Python Wrapper.
    """

    session = Session()
    TODAY = date.today()
    TODAY_STRING = TODAY.strftime("%Y-%m-%d")
    IN_ONE_YEAR_STRING = (TODAY + timedelta(365)).strftime("%Y-%m-%d")

    BIM_360_TYPES = {
        "a.": "autodesk.core",  # bim360teams
        "b.": "autodesk.bim360",  # bim360docs
    }

    TYPES = {
        BIM_360_TYPES["a."]: {
            "hubs": "hubs:{}:Hub".format(BIM_360_TYPES["a."]),
            "items": "items:{}:File".format(BIM_360_TYPES["a."]),
            "folders": "folders:{}:Folder".format(BIM_360_TYPES["a."]),
            "versions": "versions:{}:File".format(BIM_360_TYPES["a."]),
        },
        BIM_360_TYPES["b."]: {
            "hubs": "hubs:{}:Account".format(BIM_360_TYPES["b."]),
            "items": "items:{}:File".format(BIM_360_TYPES["b."]),
            "folders": "folders:{}:Folder".format(BIM_360_TYPES["b."]),
            "versions": "versions:{}:File".format(BIM_360_TYPES["b."]),
            "commands": {
                "get_publish_model_job": "commands:{}:C4RModelGetPublishJob".format(  # noqa:E501
                    BIM_360_TYPES["b."]
                ),
                "publish_model": "commands:{}:C4RModelPublish".format(
                    BIM_360_TYPES["b."]
                ),
            },
        },
    }

    @staticmethod
    def _compose_url(url, params):
        """
        Composes url with query string params.

        Returns:
            url (``string``): Composed url.
        """
        url_params = ""
        count = 0
        for key, value in params.items():
            if count == 0:
                url_params += "?"
            else:
                url_params += "&"
            url_params += key + "="
            value = str(params[key])
            try:
                value = urllib.parse.quote(value)
            except Exception:
                value = urllib.pathname2url(value)
            url_params += value
            count += 1
        return url + url_params

    @staticmethod
    def _decompose_url(url, include_url=False):
        param_strings = re.split("[?&#]", url)

        params = {}

        if include_url:
            params["url"] = param_strings[0]

        for field_value in param_strings[1:]:
            field, value = field_value.split("=")
            params[field] = value

        return params

    @property
    def hub_id(self):
        if getattr(self, "_hub_id", None):
            return self._hub_id

    @hub_id.setter
    def hub_id(self, val):
        self._set_hub_id(val)

    def _set_hub_id(self, val):
        if not isinstance(val, str):
            raise TypeError("Hub ID must be a string")
        else:
            self._hub_id = val
            self.hub_type = ForgeBase.BIM_360_TYPES.get(val[0:2])
            self.account_id = val.split(".")[-1]
            if not self.hub_type:
                raise ValueError("Invalid Hub ID")
