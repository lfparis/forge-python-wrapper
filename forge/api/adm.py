# -*- coding: utf-8 -*-

"""documentation placeholder"""

from __future__ import absolute_import

import time

from aiohttp import ContentTypeError
from json.decoder import JSONDecodeError

from ..base import ForgeBase, Logger
from ..decorators import _get_session
from ..urls import DATA_V1_URL, PROJECT_V1_URL, OSS_V2_URL

logger = Logger.start(__name__)


class ADM(ForgeBase):
    def __init__(self, *args, auth=None, log_level=None, retries=5, **kwargs):
        self.auth = auth
        self.logger = logger
        self.log_level = log_level
        self.retries = retries

    def _set_headers(self, x_user_id=None):
        headers = {}
        if x_user_id:
            headers = {"x-user-id": x_user_id}
        headers.update(self.auth.header)
        return headers

    async def _request(self, *args, **kwargs):
        res = await self.asession.request(*args, **kwargs)
        count = 0
        step = 5
        while res.status == 429:
            count += step
            time.sleep(0.1 * count ** count)
            res = await self.asession.request(*args, **kwargs)

            if count == self.retries * step:
                break
        if res.status == 429:
            res.raise_for_status()
        return res

    async def _get_data(self, res):
        try:
            return await res.json(encoding="utf-8")
        # else if raw data
        except JSONDecodeError:
            return await res.text(encoding="utf-8")
        except ContentTypeError:
            return await res.read()

    # Pagination Methods

    @_get_session
    async def _get_iter(self, url, params={}, x_user_id=None):
        params.update({"page[number]": 0, "page[limit]": 200})
        headers = self._set_headers(x_user_id)

        res = await self._request(
            method="GET", url=url, headers=headers, params=params
        )
        data = await self._get_data(res)

        results = data.get("data") or []

        if results:
            while data["links"].get("next") and data["data"]:
                next_url = data["links"].get("next")["href"]
                res = await self._request(
                    method="GET", url=next_url, headers=headers, params=params
                )
                data = await self._get_data(res)
                results.extend(data.get("data"))
                next_url = data["links"].get("next")

        return results

    # PROJECT_V1

    @_get_session
    async def get_hubs(self, x_user_id=None):
        url = "{}/hubs".format(PROJECT_V1_URL)
        headers = self._set_headers(x_user_id)
        res = await self._request(method="GET", url=url, headers=headers)
        return await self._get_data(res)

    @_get_session
    async def get_project(self, project_id, x_user_id=None):
        url = "{}/hubs/{}/projects/{}".format(
            PROJECT_V1_URL, self.hub_id, project_id
        )
        headers = self._set_headers(x_user_id)
        res = await self._request(method="GET", url=url, headers=headers)
        return await self._get_data(res)

    async def get_projects(self, x_user_id=None):
        url = "{}/hubs/{}/projects".format(PROJECT_V1_URL, self.hub_id)
        projects = await self._get_iter(url, x_user_id=x_user_id)
        if projects:
            self.logger.info(
                "Fetched {} projects from Autodesk BIM 360".format(
                    len(projects)
                )
            )

        return projects

    @_get_session
    async def get_top_folders(self, project_id, x_user_id=None):
        url = "{}/hubs/{}/projects/{}/topFolders".format(
            PROJECT_V1_URL, self.hub_id, project_id
        )
        headers = self._set_headers(x_user_id)
        res = await self._request(method="GET", url=url, headers=headers)
        return await self._get_data(res)

    # DATA_V1

    @_get_session
    async def get_folder(self, project_id, folder_id, x_user_id=None):
        url = "{}/projects/{}/folders/{}".format(
            DATA_V1_URL, project_id, folder_id
        )
        headers = self._set_headers(x_user_id)
        res = await self._request(method="GET", url=url, headers=headers)
        return await self._get_data(res)

    async def get_folder_contents(
        self, project_id, folder_id, include_hidden=False, x_user_id=None
    ):
        url = "{}/projects/{}/folders/{}/contents".format(
            DATA_V1_URL, project_id, folder_id
        )
        params = {
            "includeHidden": int(include_hidden),
        }
        contents = await self._get_iter(
            url, params=params, x_user_id=x_user_id
        )
        if contents:
            self.logger.debug(
                "Fetched {} items from project: {}, folder: {}".format(
                    len(contents), project_id, folder_id
                )
            )

        return contents

    @_get_session
    async def get_item(self, project_id, item_id, x_user_id=None):
        url = "{}/projects/{}/items/{}".format(
            DATA_V1_URL, project_id, item_id
        )
        headers = self._set_headers(x_user_id)
        res = await self._request(method="GET", url=url, headers=headers)
        return await self._get_data(res)

    async def get_item_versions(self, project_id, item_id, x_user_id=None):
        url = "{}/projects/{}/items/{}/versions".format(
            DATA_V1_URL, project_id, item_id
        )
        versions = await self._get_iter(url, x_user_id=x_user_id)
        if versions:
            self.logger.debug(
                "Fetched {} versions from item: {} in project: {}".format(
                    len(versions), item_id, project_id
                )
            )

        return versions

    @_get_session
    async def get_version(self, project_id, version_id, x_user_id=None):
        url = "{}/projects/{}/versions/{}".format(
            DATA_V1_URL, project_id, self._urlencode(version_id)
        )
        headers = self._set_headers(x_user_id)
        res = await self._request(method="GET", url=url, headers=headers)
        return await self._get_data(res)

    @_get_session
    async def get_version_download_formats(
        self, project_id, version_id, x_user_id=None
    ):
        url = "{}/projects/{}/versions/{}/downloadFormats".format(
            DATA_V1_URL, project_id, self._urlencode(version_id)
        )
        headers = self._set_headers(x_user_id)
        res = await self._request(method="GET", url=url, headers=headers)
        return await self._get_data(res)

    @_get_session
    async def get_version_downloads(
        self, project_id, version_id, x_user_id=None
    ):
        url = "{}/projects/{}/versions/{}/downloads".format(
            DATA_V1_URL, project_id, self._urlencode(version_id)
        )
        headers = self._set_headers(x_user_id)
        res = await self._request(method="GET", url=url, headers=headers)
        return await self._get_data(res)

    @_get_session
    async def post_item(
        self,
        project_id,
        folder_id,
        object_id,
        name,
        item_extension_type=None,
        version_extension_type=None,
        copy_from_id=None,
        x_user_id=None,
    ):
        """
        version_extension_type = file or composite_design or c4rmodel

        display_name = item["data"]["attributes"]["displayName"]
        file_type = "items:autodesk.bim360:File" or "items:autodesk.core:File"
        file_type = item["data"]["attributes"]["extension"]["type"]
        version = item["data"]["attributes"]["extension"]["version"]
        item_urn = item["data"]["id"]
        """
        url = "{}/projects/{}/items".format(DATA_V1_URL, project_id)
        headers = self._set_headers(x_user_id)
        headers.update({"Content-Type": "application/vnd.api+json"})

        if copy_from_id:
            url = self._compose_url(url, {"copyFrom": copy_from_id})

        json_data = {
            "jsonapi": {"version": "1.0"},
            "data": {
                "type": "items",
                "attributes": {
                    "displayName": name,
                    "extension": {"version": "1.0"},
                },
                "relationships": {
                    "tip": {"data": {"type": "versions", "id": "1"}},
                    "parent": {"data": {"type": "folders", "id": folder_id}},
                },
            },
            "included": [
                {
                    "type": "versions",
                    "id": "1",
                    "attributes": {
                        "name": name,
                        "displayName": name,
                        "extension": {"version": "1.0"},
                    },
                    "relationships": {
                        "storage": {
                            "data": {"type": "objects", "id": object_id}
                        },
                    },
                },
            ],
        }
        if not copy_from_id:
            json_data["data"]["attributes"]["extension"].update(
                {
                    "type": item_extension_type
                    or ForgeBase.TYPES[self.hub_type]["items"]["File"]
                }
            )
            json_data["included"][0]["attributes"]["extension"].update(
                {
                    "type": version_extension_type
                    or ForgeBase.TYPES[self.hub_type]["versions"]["File"]
                }
            )

        res = await self._request(
            method="POST", url=url, headers=headers, json=json_data,
        )
        return await self._get_data(res)

    @_get_session
    async def post_item_version(
        self,
        project_id,
        storage_id,
        item_id,
        name,
        version_extension_type=None,
        copy_from_id=None,
        x_user_id=None,
    ):
        url = "{}/projects/{}/versions".format(DATA_V1_URL, project_id)
        headers = self._set_headers(x_user_id=x_user_id)
        headers.update({"Content-Type": "application/vnd.api+json"})

        if copy_from_id:
            url = self._compose_url(url, {"copyFrom": copy_from_id})

        json_data = {
            "jsonapi": {"version": "1.0"},
            "data": {
                "type": "versions",
                "attributes": {"name": name, "extension": {"version": "1.0"}},
                "relationships": {
                    "item": {"data": {"type": "items", "id": item_id}}
                },
            },
        }

        if not copy_from_id:
            json_data["data"]["attributes"]["extension"].update(
                {
                    "type": version_extension_type
                    or ForgeBase.TYPES[self.hub_type]["versions"]["File"]
                }
            )
            json_data["data"]["relationships"].update(
                {"storage": {"data": {"type": "objects", "id": storage_id}}}
            )
        # else:
        #     json_data["data"]["attributes"]["extension"].update(
        #         {"displayName": name}
        #     )

        res = await self._request(
            method="POST", url=url, headers=headers, json=json_data,
        )
        return await self._get_data(res)

    @_get_session
    async def post_storage(
        self, project_id, host_type, host_id, name, x_user_id=None,
    ):
        """
        host is a folder or item
        folder_urn = folder["data"]["id"]
        folder_type = folder["data"]["type"]
        host_type = "items" or "folders"
        """
        url = "{}/projects/{}/storage".format(DATA_V1_URL, project_id)
        headers = self._set_headers(x_user_id)
        headers.update({"Content-Type": "application/vnd.api+json"})
        json_data = {
            "jsonapi": {"version": "1.0"},
            "data": {
                "type": "objects",
                "attributes": {"name": name},
                "relationships": {
                    "target": {"data": {"type": host_type, "id": host_id}}
                },
            },
        }
        res = await self._request(
            method="POST", url=url, headers=headers, json=json_data,
        )
        return await self._get_data(res)

    @_get_session
    async def post_folder(
        self,
        project_id,
        parent_folder_id,
        folder_name,
        project_name=None,
        x_user_id=None,
    ):
        url = "{}/projects/{}/folders".format(DATA_V1_URL, project_id)
        headers = self._set_headers(x_user_id)
        headers.update({"Content-Type": "application/vnd.api+json"})
        json_data = {
            "jsonapi": {"version": "1.0"},
            "data": {
                "type": "folders",
                "attributes": {
                    "name": folder_name,
                    "extension": {
                        "type": ForgeBase.TYPES[self.hub_type]["folders"][
                            "Folder"
                        ],
                        "version": "1.0",
                    },
                },
                "relationships": {
                    "parent": {
                        "data": {"type": "folders", "id": parent_folder_id}
                    }
                },
            },
        }

        res = await self._request(
            method="POST", url=url, headers=headers, json=json_data,
        )
        data = await self._get_data(res)

        if res.status >= 200 and res.status < 300:
            self.logger.info(
                "{}: added '{}' folder".format(
                    project_name or project_id, folder_name
                )
            )
            return data

    # DATA_V1 - COMMANDS

    @_get_session
    async def _commands(self, project_id, json_data, x_user_id=None):
        url = "{}/projects/{}/commands".format(DATA_V1_URL, project_id)
        headers = self._set_headers(x_user_id)
        headers.update({"Content-Type": "application/vnd.api+json"})
        res = await self._request(
            method="POST", url=url, headers=headers, json=json_data,
        )
        return await self._get_data(res)

    async def _commands_publish(
        self, project_id, item_id, command, x_user_id=None
    ):
        json_data = {
            "jsonapi": {"version": "1.0"},
            "data": {
                "type": "commands",
                "attributes": {
                    "extension": {"type": command, "version": "1.0.0"}
                },
                "relationships": {
                    "resources": {"data": [{"type": "items", "id": item_id}]}
                },
            },
        }
        return await self._commands(project_id, json_data, x_user_id=x_user_id)

    async def get_publish_model_job(
        self, project_id, item_id, x_user_id=None,
    ):
        command = ForgeBase.TYPES[self.hub_type]["commands"][
            "C4RModelGetPublishJob"
        ]
        return await self._commands_publish(
            project_id, item_id, command, x_user_id=x_user_id
        )

    async def publish_model(
        self, project_id, item_id, x_user_id=None,
    ):
        command = ForgeBase.TYPES[self.hub_type]["commands"]["C4RModelPublish"]
        return await self._commands_publish(
            project_id, item_id, command, x_user_id=x_user_id
        )

    # OSS V2

    @_get_session
    async def get_object_details(self, bucket_key, object_name):
        url = "{}/buckets/{}/objects/{}/details".format(
            OSS_V2_URL, bucket_key, object_name
        )
        res = await self._request(
            method="GET", url=url, headers=self.auth.header,
        )
        return await self._get_data(res)

    @_get_session
    async def get_object(self, bucket_key, object_name, byte_range=None):
        url = "{}/buckets/{}/objects/{}".format(
            OSS_V2_URL, bucket_key, object_name
        )
        headers = {k: v for k, v in self.auth.header.items()}
        if byte_range:
            headers.update({"Range": "bytes={}-{}".format(*byte_range)})
        res = await self._request(method="GET", url=url, headers=headers,)
        return await self._get_data(res)

    @_get_session
    async def put_object(self, bucket_key, object_name, object_bytes):
        url = "{}/buckets/{}/objects/{}".format(
            OSS_V2_URL, bucket_key, object_name
        )
        res = await self._request(
            method="PUT", url=url, headers=self.auth.header, data=object_bytes
        )
        return await self._get_data(res)

    @_get_session
    async def put_object_resumable(
        self,
        bucket_key,
        object_name,
        object_bytes,
        total_size,
        byte_range,
        session_id="-811577637",
    ):
        url = "{}/buckets/{}/objects/{}/resumable".format(
            OSS_V2_URL, bucket_key, object_name
        )
        headers = {
            "Content-Length": str(total_size),
            "Session-Id": session_id,
            "Content-Range": "bytes {}-{}/{}".format(
                byte_range[0], byte_range[1], total_size
            ),
        }
        headers.update(self.auth.header)
        res = await self._request(
            method="PUT", url=url, headers=headers, data=object_bytes
        )
        return await self._get_data(res)

    @_get_session
    async def put_object_copy(self, bucket_key, object_name, new_object_name):
        url = "{}/buckets/{}/objects/{}/copyto/{}".format(
            OSS_V2_URL, bucket_key, object_name, new_object_name
        )
        res = await self._request(
            method="PUT", url=url, headers=self.auth.header
        )
        return await self._get_data(res)
