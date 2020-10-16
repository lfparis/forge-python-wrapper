# -*- coding: utf-8 -*-

"""documentation placeholder"""

from __future__ import absolute_import

from functools import wraps

from ..base import ForgeBase, Logger, semaphore
from ..decorators import _async_validate_token
from ..utils import HTTPSemaphore
from ..urls import DATA_V1_URL, PROJECT_V1_URL, OSS_V2_URL

logger = Logger.start(__name__)


class ADM(ForgeBase):
    logger = logger

    def __init__(self, app, *args, **kwargs):
        self.app = app
        self.log_level = self.app.log_level
        ADM._set_rate_limits()

    @classmethod
    def _set_rate_limits(cls):
        if getattr(cls, "semaphores", None):
            return
        oss_sem = HTTPSemaphore(value=50, interval=60, max_calls=1000)
        cls.semaphores = {
            ADM.get_hubs.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=50
            ),  # noqa: E501 # fmt: off
            ADM.get_project.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=50
            ),  # noqa: E501 # fmt: off
            ADM.get_projects.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=50
            ),  # noqa: E501 # fmt: off
            ADM.get_top_folders.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=300
            ),  # noqa: E501 # fmt: off
            ADM.get_folder.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=300
            ),  # noqa: E501 # fmt: off
            ADM.get_folder_contents.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=50
            ),  # noqa: E501 # fmt: off
            ADM.get_item.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=300
            ),  # noqa: E501 # fmt: off
            ADM.get_item_parent.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=50
            ),  # noqa: E501 # fmt: off
            ADM.get_item_versions.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=800
            ),  # noqa: E501 # fmt: off
            ADM.get_version.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=300
            ),  # noqa: E501 # fmt: off
            ADM.get_version_download_formats.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=50
            ),  # noqa: E501 # fmt: off
            ADM.get_version_downloads.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=50
            ),  # noqa: E501 # fmt: off
            ADM.post_item.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=50
            ),  # noqa: E501 # fmt: off
            ADM.post_item_version.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=300
            ),  # noqa: E501 # fmt: off
            ADM.post_storage.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=300
            ),  # noqa: E501 # fmt: off
            ADM.post_folder.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=50
            ),  # noqa: E501 # fmt: off
            ADM.post_command.__name__: HTTPSemaphore(
                value=50, interval=60, max_calls=300
            ),  # noqa: E501 # fmt: off
            ADM.get_object_details.__name__: oss_sem,
            ADM.get_object.__name__: oss_sem,
            ADM.put_object.__name__: oss_sem,
            ADM.put_object_resumable.__name__: oss_sem,
            ADM.put_object_copy.__name__: oss_sem,
        }

    def _throttle(func):
        """ """

        @wraps(func)
        @_async_validate_token
        async def inner(self, *args, **kwargs):
            async with ADM.semaphores[func.__name__] and semaphore:
                return await func(self, *args, **kwargs)

        return inner

    def _set_headers(self, x_user_id=None):
        headers = {}
        if x_user_id:
            headers = {"x-user-id": x_user_id}
        return headers

    # Pagination Methods

    async def _get_iter(self, sema, url, params={}, x_user_id=None):
        params.update({"page[number]": 0, "page[limit]": 200})
        headers = self._set_headers(x_user_id)

        res = await self.app._request(
            method="GET", url=url, headers=headers, params=params
        )
        data = await self.app._get_data(res)

        try:
            results = data.get("data") or []
        except (AttributeError, KeyError, TypeError):
            results = []

        if results:
            try:
                next_url = data["links"].get("next")["href"]
            except (AttributeError, KeyError, TypeError):
                return results

            while next_url:
                async with sema:
                    res = await self.app._request(
                        method="GET", url=next_url, headers=headers
                    )
                    data = await self.app._get_data(res)
                    try:
                        results.extend(data.get("data") or [])
                    except (AttributeError, KeyError, TypeError):
                        pass

                    try:
                        next_url = data["links"].get("next")["href"]
                    except (AttributeError, KeyError, TypeError):
                        break

        return results

    # PROJECT_V1

    @_throttle
    async def get_hubs(self, x_user_id=None):
        url = "{}/hubs".format(PROJECT_V1_URL)
        headers = self._set_headers(x_user_id)
        res = await self.app._request(method="GET", url=url, headers=headers)
        return await self.app._get_data(res)

    @_throttle
    async def get_project(self, project_id, x_user_id=None):
        url = "{}/hubs/{}/projects/{}".format(
            PROJECT_V1_URL, self.hub_id, project_id
        )
        headers = self._set_headers(x_user_id)
        res = await self.app._request(method="GET", url=url, headers=headers)
        return await self.app._get_data(res)

    @_throttle
    async def get_projects(self, x_user_id=None):
        sema = ADM.semaphores["get_projects"]
        url = "{}/hubs/{}/projects".format(PROJECT_V1_URL, self.hub_id)
        projects = await self._get_iter(sema, url, x_user_id=x_user_id)
        if projects:
            self.logger.info(
                "Fetched {} projects from Autodesk BIM 360".format(
                    len(projects)
                )
            )

        return projects

    @_throttle
    async def get_top_folders(self, project_id, x_user_id=None):
        url = "{}/hubs/{}/projects/{}/topFolders".format(
            PROJECT_V1_URL, self.hub_id, project_id
        )
        headers = self._set_headers(x_user_id)
        res = await self.app._request(method="GET", url=url, headers=headers)
        return await self.app._get_data(res)

    # DATA_V1

    @_throttle
    async def get_folder(self, project_id, folder_id, x_user_id=None):
        url = "{}/projects/{}/folders/{}".format(
            DATA_V1_URL, project_id, folder_id
        )
        headers = self._set_headers(x_user_id)
        res = await self.app._request(method="GET", url=url, headers=headers)
        return await self.app._get_data(res)

    @_throttle
    async def get_folder_contents(
        self, project_id, folder_id, include_hidden=False, x_user_id=None
    ):
        sema = ADM.semaphores["get_folder_contents"]
        url = "{}/projects/{}/folders/{}/contents".format(
            DATA_V1_URL, project_id, folder_id
        )
        params = {
            "includeHidden": int(include_hidden),
        }
        contents = await self._get_iter(
            sema, url, params=params, x_user_id=x_user_id
        )
        if contents:
            self.logger.debug(
                "Fetched {} items from project: {}, folder: {}".format(
                    len(contents), project_id, folder_id
                )
            )

        return contents

    @_throttle
    async def get_item(self, project_id, item_id, x_user_id=None):
        url = "{}/projects/{}/items/{}".format(
            DATA_V1_URL, project_id, item_id
        )
        headers = self._set_headers(x_user_id)
        res = await self.app._request(method="GET", url=url, headers=headers)
        return await self.app._get_data(res)

    @_throttle
    async def get_item_parent(self, project_id, item_id, x_user_id=None):
        url = "{}/projects/{}/items/{}/parent".format(
            DATA_V1_URL, project_id, item_id
        )
        headers = self._set_headers(x_user_id)
        res = await self.app._request(method="GET", url=url, headers=headers)
        return await self.app._get_data(res)

    @_throttle
    async def get_item_versions(self, project_id, item_id, x_user_id=None):
        sema = ADM.semaphores["get_item_versions"]
        url = "{}/projects/{}/items/{}/versions".format(
            DATA_V1_URL, project_id, item_id
        )
        versions = await self._get_iter(sema, url, x_user_id=x_user_id)
        if versions:
            self.logger.debug(
                "Fetched {} versions from item: {} in project: {}".format(
                    len(versions), item_id, project_id
                )
            )

        return versions

    @_throttle
    async def get_version(self, project_id, version_id, x_user_id=None):
        url = "{}/projects/{}/versions/{}".format(
            DATA_V1_URL, project_id, self._urlencode(version_id)
        )
        headers = self._set_headers(x_user_id)
        res = await self.app._request(method="GET", url=url, headers=headers)
        return await self.app._get_data(res)

    @_throttle
    async def get_version_download_formats(
        self, project_id, version_id, x_user_id=None
    ):
        url = "{}/projects/{}/versions/{}/downloadFormats".format(
            DATA_V1_URL, project_id, self._urlencode(version_id)
        )
        headers = self._set_headers(x_user_id)
        res = await self.app._request(method="GET", url=url, headers=headers)
        return await self.app._get_data(res)

    @_throttle
    async def get_version_downloads(
        self, project_id, version_id, x_user_id=None
    ):
        url = "{}/projects/{}/versions/{}/downloads".format(
            DATA_V1_URL, project_id, self._urlencode(version_id)
        )
        headers = self._set_headers(x_user_id)
        res = await self.app._request(method="GET", url=url, headers=headers)
        return await self.app._get_data(res)

    @_throttle
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

        res = await self.app._request(
            method="POST",
            url=url,
            headers=headers,
            json=json_data,
        )
        return await self.app._get_data(res)

    @_throttle
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

        res = await self.app._request(
            method="POST",
            url=url,
            headers=headers,
            json=json_data,
        )
        return await self.app._get_data(res)

    @_throttle
    async def post_storage(
        self,
        project_id,
        host_type,
        host_id,
        name,
        x_user_id=None,
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
        res = await self.app._request(
            method="POST",
            url=url,
            headers=headers,
            json=json_data,
        )
        return await self.app._get_data(res)

    @_throttle
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

        res = await self.app._request(
            method="POST",
            url=url,
            headers=headers,
            json=json_data,
        )
        data = await self.app._get_data(res)

        if res.status >= 200 and res.status < 300:
            self.logger.info(
                "{}: added '{}' folder".format(
                    project_name or project_id, folder_name
                )
            )
            return data

    # DATA_V1 - COMMANDS

    @_throttle
    async def post_command(self, project_id, json_data, x_user_id=None):
        url = "{}/projects/{}/commands".format(DATA_V1_URL, project_id)
        headers = self._set_headers(x_user_id)
        headers.update({"Content-Type": "application/vnd.api+json"})
        res = await self.app._request(
            method="POST",
            url=url,
            headers=headers,
            json=json_data,
        )
        return await self.app._get_data(res)

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
        return await self.post_command(
            project_id, json_data, x_user_id=x_user_id
        )

    async def get_publish_model_job(
        self,
        project_id,
        item_id,
        x_user_id=None,
    ):
        command = ForgeBase.TYPES[self.hub_type]["commands"][
            "C4RModelGetPublishJob"
        ]
        return await self._commands_publish(
            project_id, item_id, command, x_user_id=x_user_id
        )

    async def publish_model(
        self,
        project_id,
        item_id,
        x_user_id=None,
    ):
        command = ForgeBase.TYPES[self.hub_type]["commands"]["C4RModelPublish"]
        return await self._commands_publish(
            project_id, item_id, command, x_user_id=x_user_id
        )

    # OSS V2

    @_throttle
    async def get_object_details(self, bucket_key, object_name):
        url = "{}/buckets/{}/objects/{}/details".format(
            OSS_V2_URL, bucket_key, object_name
        )
        res = await self.app._request(method="GET", url=url)
        return await self.app._get_data(res)

    @_throttle
    async def get_object(self, bucket_key, object_name, byte_range=None):
        url = "{}/buckets/{}/objects/{}".format(
            OSS_V2_URL, bucket_key, object_name
        )
        headers = {}
        if byte_range:
            headers.update({"Range": "bytes={}-{}".format(*byte_range)})
        res = await self.app._request(method="GET", url=url, headers=headers)
        return await self.app._get_data(res)

    @_throttle
    async def put_object(self, bucket_key, object_name, object_bytes):
        url = "{}/buckets/{}/objects/{}".format(
            OSS_V2_URL, bucket_key, object_name
        )
        res = await self.app._request(method="PUT", url=url, data=object_bytes)
        return await self.app._get_data(res)

    @_throttle
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
        res = await self.app._request(
            method="PUT", url=url, headers=headers, data=object_bytes
        )
        return await self.app._get_data(res)

    @_throttle
    async def put_object_copy(self, bucket_key, object_name, new_object_name):
        url = "{}/buckets/{}/objects/{}/copyto/{}".format(
            OSS_V2_URL, bucket_key, object_name, new_object_name
        )
        res = await self.app._request(method="PUT", url=url)
        return await self.app._get_data(res)
