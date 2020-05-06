# -*- coding: utf-8 -*-

"""documentation placeholder"""

from __future__ import absolute_import

import re
import sys
import urllib

from datetime import date, timedelta

from .session import Session
from .urls import BASE_URL
from .utils import Logger  # noqa:F401


if sys.version_info >= (3, 7):
    from asyncio import BoundedSemaphore

    semaphore = BoundedSemaphore(value=50)


class ForgeBase(object):
    """
    Superclass for all api model classes in this Forge Python Wrapper.
    """

    session = Session(base_url=BASE_URL)
    TODAY = date.today()
    TODAY_STRING = TODAY.strftime("%Y-%m-%d")
    IN_ONE_YEAR_STRING = (TODAY + timedelta(365)).strftime("%Y-%m-%d")

    # TODO - Reorganise Extension Types (https://forge.autodesk.com/en/docs/data/v2/developers_guide/basics/#extension-types)  # noqa: E501

    BASE_TYPES = [
        "hubs",
        "items",
        "folders",
        "versions",
        "commands",
        "derived",
        "xrefs",
        "auxiliary",
        "dependencies",
    ]

    NAMESPACES = {
        "a.": "autodesk.core",  # bim360teams
        "b.": "autodesk.bim360",  # bim360docs
        "fusion360": "autodesk.fusion360",  # fusion360
        "a360": "autodesk.a360",  # a360
    }

    EXTENSION_TYPES = [
        "Account",
        "Attachment",
        "C4RModel",
        "CompositeDesign",
        "Deleted",
        "Design",
        "Document",
        "Drawing",
        "DrawingToDesign",
        "File",
        "FileToDocument",
        "FileToReviewDocument",
        "Folder",
        "Hub",
        "PersonalHub",
        "Xref",
    ]

    COMMAND_TYPES = [
        "CheckPermission",
        "ListRefs",
        "ListItems",
        "CreateFolder",
        "C4RModelPublish",
        "C4RModelGetPublishJob",
    ]

    TYPES = {
        NAMESPACES["a."]: {
            "hubs": {"Hub": "hubs:{}:Hub".format(NAMESPACES["a."])},
            "items": {"File": "items:{}:File".format(NAMESPACES["a."])},
            "folders": {
                "Folder": "folders:{}:Folder".format(NAMESPACES["a."])
            },
            "versions": {
                "File": "versions:{}:File".format(NAMESPACES["a."]),
                "CompositeDesign": "versions:{}:CompositeDesign".format(
                    NAMESPACES["a360"]
                ),
                "Deleted": "versions:{}:Deleted".format(NAMESPACES["a."]),
            },
            "commands": None,
            "derived": None,
            "xrefs": None,
            "auxiliary": None,
            "dependencies": None,
        },
        NAMESPACES["b."]: {
            "hubs": {"Hub": "hubs:{}:Account".format(NAMESPACES["b."])},
            "items": {
                "File": "items:{}:File".format(NAMESPACES["b."]),
                "C4RModel​": "items:{}:C4RModel​".format(NAMESPACES["b."]),
            },
            "folders": {
                "Folder": "folders:{}:Folder".format(NAMESPACES["b."])
            },
            "versions": {
                "File": "versions:{}:File".format(NAMESPACES["b."]),
                "CompositeDesign": "versions:{}:File".format(NAMESPACES["b."]),
                "C4RModel​": "versions:{}:C4RModel​".format(NAMESPACES["b."]),
                "Deleted": "versions:{}:Deleted".format(NAMESPACES["b."]),
            },
            "commands": {
                "C4RModelGetPublishJob": "commands:{}:C4RModelGetPublishJob".format(  # noqa:E501
                    NAMESPACES["b."]
                ),
                "C4RModelPublish": "commands:{}:C4RModelPublish".format(
                    NAMESPACES["b."]
                ),
            },
            "derived": None,
            "xrefs": None,
            "auxiliary": None,
            "dependencies": None,
        },
    }

    @staticmethod
    def _urlencode(value):
        try:
            value = urllib.parse.quote(value)
        except Exception:
            value = urllib.pathname2url(value)
        return value

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
            url_params += ForgeBase._urlencode(value)
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

    @staticmethod
    def _validate_extension_type(extension_type):
        assert isinstance(
            extension_type, str
        ), "extension_type must be a string"

        try:
            _, namespace, _ = extension_type.split(":")
        except ValueError:
            raise ValueError(
                "Invalid extension_type: {}".format(
                    "Expecting a string in the format '<base type>:<namespace>:<extension_type>'",  # noqa: E501
                )
            )

    @staticmethod
    def _convert_extension_type(extension_type, target_namespace):
        ForgeBase._validate_extension_type(extension_type)
        base_type, namespace, ext_type = extension_type.split(":")
        if target_namespace == namespace:
            return extension_type
        else:
            # TODO - CompositeDesign to C4R Conversion
            try:
                return ForgeBase.TYPES[target_namespace][base_type][ext_type]
            except Exception:
                return

    @property
    def log_level(self):
        if getattr(self, "_log_level", None):
            return self._log_level

    @log_level.setter
    def log_level(self, log_level):
        """ """
        if not (isinstance(log_level, str)):
            raise TypeError("log_level must be a string")
        # elif log_level not in(x_user_id) == 12:
        #     raise ValueError("x_user_id must be a user UID")
        else:
            self._log_level = log_level
            if getattr(self, "logger", None):
                Logger.set_level(self.logger, log_level)
            if getattr(self, "session", None):
                Logger.set_level(ForgeBase.session.logger, log_level)

    @property
    def x_user_id(self):
        if getattr(self, "_x_user_id", None):
            return self._x_user_id

    @x_user_id.setter
    def x_user_id(self, x_user_id):
        """ """
        if not (isinstance(x_user_id, str)):
            raise TypeError("x_user_id must be a string")
        elif not len(x_user_id) == 12:
            raise ValueError("x_user_id must be a user UID")
        else:
            self._x_user_id = x_user_id

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
            self.hub_type = ForgeBase.NAMESPACES.get(val[:2])
            self.account_id = val.split(".")[-1]
            if not self.hub_type:
                raise ValueError("Invalid Hub ID")
