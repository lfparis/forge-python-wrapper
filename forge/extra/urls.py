# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sys

"""
Forge APIs urls
https://forge.autodesk.com/en/docs/
"""

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


if sys.version_info >= (3, 7):

    # get
    PROJECT_V1_HUBS = f"{PROJECT_V1_URL}/hubs"
    PROJECT_V1_PROJECTS = f"{PROJECT_V1_URL}/hubs/:hub_id/projects"
    PROJECT_V1_PROJECT = f"{PROJECT_V1_URL}/hubs/:hub_id/projects/:project_id"
    PROJECT_V1_TOPFOLDERS = f"{PROJECT_V1_URL}/hubs/:hub_id/projects/:project_id/topFolders"  # noqa: E501 # fmt: off
    DATA_V1_FOLDERS = f"{DATA_V1_URL}/projects/:project_id/folders/:folder_id"  # noqa: E501 # fmt: off
    DATA_V1_CONTENTS = f"{DATA_V1_URL}/projects/:project_id/folders/:folder_id/contents"  # noqa: E501 # fmt: off
    DATA_V1_ITEM = f"{DATA_V1_URL}/projects/:project_id/items/:item_id"
    DATA_V1_VERSIONS = f"{DATA_V1_URL}/projects/:project_id/items/:item_id/versions"  # noqa: E501 # fmt: off
    DATA_V1_VERSION = f"{DATA_V1_URL}/projects/:project_id/versions/:version_id"  # noqa: E501 # fmt: off
    DATA_V1_VERSION_DOWNLOADFORMATS = f"{DATA_V1_URL}/projects/:project_id/versions/:version_id/downloadFormats"  # noqa: E501 # fmt: off
    DATA_V1_VERSION_DOWNLOADS = f"{DATA_V1_URL}/projects/:project_id/versions/:version_id/downloads"  # noqa: E501 # fmt: off
    OSS_V2_URL_OBJECT = f"{OSS_V2_URL}/buckets/:bucket_key/objects/:object_name"  # noqa: E501 # fmt: off
    OSS_V2_URL_OBJECT_DETAILS = f"{OSS_V2_URL}/buckets/:bucket_key/objects/:object_name/details"  # noqa: E501 # fmt: off
    HQ_V1_URL_USERS = f"{HQ_V1_URL}/accounts/:account_id/users"
    HQ_V1_URL_USER_SEARCH = f"{HQ_V1_URL}/accounts/:account_id/users/search"
    HQ_V1_URL_USER = f"{HQ_V1_URL}/accounts/:account_id/users/:user_id"
    HQ_V1_URL_PROJECTS = f"{HQ_V1_URL}/accounts/:account_id/projects"
    HQ_V1_URL_PROJECT = f"{HQ_V1_URL}/accounts/:account_id/projects/:project_id"  # noqa: E501 # fmt: off
    HQ_V1_URL_ROLES = f"{HQ_V1_URL}/accounts/:account_id/projects/:project_id/industry_roles"  # noqa: E501 # fmt: off
    HQ_V1_URL_COMPANIES = f"{HQ_V1_URL}/accounts/:account_id/companies"

    # post
    DATA_V1_URL_ITEMS = f"{DATA_V1_URL}/projects/:project_id/items"
    DATA_V1_URL_VERSIONS = f"{DATA_V1_URL}/projects/:project_id/versions"
    DATA_V1_URL_STORAGE = f"{DATA_V1_URL}/projects/:project_id/storage"
    DATA_V1_URL_FOLDERS = f"{DATA_V1_URL}/projects/:project_id/folders"
    DATA_V1_URL_COMMANDS = f"{DATA_V1_URL}/projects/:project_id/commands"
    HQ_V1_URL_PROJECTS = f"{HQ_V1_URL}/accounts/:account_id/projects"
    HQ_V1_URL_USERS_IMPORT = f"{HQ_V1_URL}/accounts/:account_id/projects/:project_id/users/import"  # noqa: E501 # fmt: off

    # put
    OSS_V2_URL_OBJECT = f"{OSS_V2_URL}/buckets/:bucket_key/objects/:object_name"  # noqa: E501 # fmt: off
    OSS_V2_URL_OBJECT_RESUMABLE = f"{OSS_V2_URL}/buckets/:bucket_key/objects/:object_name/resumable"  # noqa: E501 # fmt: off
    OSS_V2_URL_OBJECT_COPY = f"{OSS_V2_URL}/buckets/:bucket_key/objects/:object_name/copyto/:new_object_name"  # noqa: E501 # fmt: off

    # patch
    HQ_V1_URL_PROJECT = f"{HQ_V1_URL}/accounts/:account_id/projects/:project_id"  # noqa: E501 # fmt: off
    HQ_V1_URL_PROJECT_USER = f"{HQ_V1_URL}/accounts/:account_id/projects/:project_id/users/:user_id"  # noqa: E501 # fmt: off


# get
DM_HUBS_URL = f"{PROJECT_V1_URL}/hubs"
DM_PROJECTS_URL = f"{DM_HUBS_URL}" + "/{}/projects"
DM_PROJECT_URL = f"{DM_HUBS_URL}" + "/{}/projects/{}"

PROJECT_V1_PROJECT = f"{PROJECT_V1_URL}/hubs/:hub_id/projects/:project_id"
PROJECT_V1_TOPFOLDERS = f"{PROJECT_V1_URL}/hubs/:hub_id/projects/:project_id/topFolders"  # noqa: E501 # fmt: off
DATA_V1_FOLDERS = f"{DATA_V1_URL}/projects/:project_id/folders/:folder_id"  # noqa: E501 # fmt: off
DATA_V1_CONTENTS = f"{DATA_V1_URL}/projects/:project_id/folders/:folder_id/contents"  # noqa: E501 # fmt: off
DATA_V1_ITEM = f"{DATA_V1_URL}/projects/:project_id/items/:item_id"
DATA_V1_VERSIONS = f"{DATA_V1_URL}/projects/:project_id/items/:item_id/versions"  # noqa: E501 # fmt: off
DATA_V1_VERSION = f"{DATA_V1_URL}/projects/:project_id/versions/:version_id"  # noqa: E501 # fmt: off
DATA_V1_VERSION_DOWNLOADFORMATS = f"{DATA_V1_URL}/projects/:project_id/versions/:version_id/downloadFormats"  # noqa: E501 # fmt: off
DATA_V1_VERSION_DOWNLOADS = f"{DATA_V1_URL}/projects/:project_id/versions/:version_id/downloads"  # noqa: E501 # fmt: off
OSS_V2_URL_OBJECT = f"{OSS_V2_URL}/buckets/:bucket_key/objects/:object_name"  # noqa: E501 # fmt: off
OSS_V2_URL_OBJECT_DETAILS = f"{OSS_V2_URL}/buckets/:bucket_key/objects/:object_name/details"  # noqa: E501 # fmt: off
HQ_V1_URL_USERS = f"{HQ_V1_URL}/accounts/:account_id/users"
HQ_V1_URL_USER_SEARCH = f"{HQ_V1_URL}/accounts/:account_id/users/search"
HQ_V1_URL_USER = f"{HQ_V1_URL}/accounts/:account_id/users/:user_id"
HQ_V1_URL_PROJECTS = f"{HQ_V1_URL}/accounts/:account_id/projects"
HQ_V1_URL_PROJECT = f"{HQ_V1_URL}/accounts/:account_id/projects/:project_id"  # noqa: E501 # fmt: off
HQ_V1_URL_ROLES = f"{HQ_V1_URL}/accounts/:account_id/projects/:project_id/industry_roles"  # noqa: E501 # fmt: off
HQ_V1_URL_COMPANIES = f"{HQ_V1_URL}/accounts/:account_id/companies"

# post
DATA_V1_URL_ITEMS = f"{DATA_V1_URL}/projects/:project_id/items"
DATA_V1_URL_VERSIONS = f"{DATA_V1_URL}/projects/:project_id/versions"
DATA_V1_URL_STORAGE = f"{DATA_V1_URL}/projects/:project_id/storage"
DATA_V1_URL_FOLDERS = f"{DATA_V1_URL}/projects/:project_id/folders"
DATA_V1_URL_COMMANDS = f"{DATA_V1_URL}/projects/:project_id/commands"
HQ_V1_URL_PROJECTS = f"{HQ_V1_URL}/accounts/:account_id/projects"
HQ_V1_URL_USERS_IMPORT = f"{HQ_V1_URL}/accounts/:account_id/projects/:project_id/users/import"  # noqa: E501 # fmt: off

# put
OSS_V2_URL_OBJECT = f"{OSS_V2_URL}/buckets/:bucket_key/objects/:object_name"  # noqa: E501 # fmt: off
OSS_V2_URL_OBJECT_RESUMABLE = f"{OSS_V2_URL}/buckets/:bucket_key/objects/:object_name/resumable"  # noqa: E501 # fmt: off
OSS_V2_URL_OBJECT_COPY = f"{OSS_V2_URL}/buckets/:bucket_key/objects/:object_name/copyto/:new_object_name"  # noqa: E501 # fmt: off

# patch
HQ_V1_URL_PROJECT = f"{HQ_V1_URL}/accounts/:account_id/projects/:project_id"  # noqa: E501 # fmt: off
HQ_V1_URL_PROJECT_USER = f"{HQ_V1_URL}/accounts/:account_id/projects/:project_id/users/:user_id"  # noqa: E501 # fmt: off
