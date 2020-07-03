# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sys

"""
Forge APIs urls
https://forge.autodesk.com/en/docs/
"""

if sys.version_info >= (3, 7):
    from .extra.urls import *  # noqa: F401,F403

else:
    BASE_URL = "https://developer.api.autodesk.com"

    # Authentication (OAuth)
    # https://forge.autodesk.com/en/docs/oauth/v2/developers_guide/basics/
    AUTH_V1_URL = "{}/authentication/v1".format(BASE_URL)

    # BIM 360 API
    # https://forge.autodesk.com/en/docs/bim360/v1/overview/basics/
    HQ_V1_URL = "{}/hq/v1".format(BASE_URL)
    HQ_V2_URL = "{}/hq/v2".format(BASE_URL)

    # Data Management API
    # https://forge.autodesk.com/en/docs/data/v2/developers_guide/basics/
    # Data Service
    DATA_V1_URL = "{}/data/v1".format(BASE_URL)
    # Project Service
    PROJECT_V1_URL = "{}/project/v1".format(BASE_URL)
    # Object Storage Service
    OSS_V2_URL = "{}/oss/v2".format(BASE_URL)
