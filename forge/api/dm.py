from __future__ import absolute_import

from ..base import ForgeBase, Logger
from ..urls import DATA_V1_URL, PROJECT_V1_URL, OSS_V2_URL

logger = Logger(__name__)()


class DM(ForgeBase):
    def __init__(self, *args, **kwargs):
        self.auth = kwargs.get("auth")
        self.log = kwargs.get("log")
        if self.log:
            self.logger = logger

    def _set_headers(self, x_user_id=None):
        headers = {}
        if x_user_id:
            headers = {"x-user-id": x_user_id}
        headers.update(self.auth.header)
        return headers

    def _get_iter(self, url, params={}, x_user_id=None):
        params.update({"page[number]": 0, "page[limit]": 200})
        headers = self._set_headers(x_user_id)
        data, _ = self.session.request(
            "get", url, headers=headers, params=params
        )

        response_data = data.get("data") or []
        if response_data:
            while data["links"].get("next") and data["data"]:
                next_url = data["links"].get("next")["href"]
                data, _ = self.session.request(
                    "get", next_url, headers=headers
                )
                response_data.extend(data["data"])
                next_url = data["links"].get("next")

        return response_data

    # PROJECT_V1

    def get_hubs(self, x_user_id=None):
        url = "{}/hubs".format(PROJECT_V1_URL)
        headers = self._set_headers(x_user_id)
        data, _ = self.session.request("get", url, headers=headers)
        return data

    def get_project(self, project_id, x_user_id=None):
        url = "{}/hubs/{}/projects/{}".format(
            PROJECT_V1_URL, self.hub_id, project_id
        )
        headers = self._set_headers(x_user_id)
        data, _ = self.session.request("get", url, headers=headers)
        return data

    def get_projects(self, x_user_id=None):
        url = "{}/hubs/{}/projects".format(PROJECT_V1_URL, self.hub_id)
        projects = self._get_iter(url, x_user_id=x_user_id)
        if projects and self.log:
            self.logger.info(
                "Fetched {} projects from Autodesk BIM 360".format(
                    len(projects)
                )
            )

        return projects

    def get_top_folders(self, project_id, x_user_id=None):
        url = "{}/hubs/{}/projects/{}/topFolders".format(
            PROJECT_V1_URL, self.hub_id, project_id
        )
        headers = self._set_headers(x_user_id)
        data, _ = self.session.request(
            "get",
            url,
            headers=headers,
            message="top folders for project '{}'".format(project_id),
        )
        return data

    # DATA_V1

    def get_folder(self, project_id, folder_id, x_user_id=None):
        url = "{}/projects/{}/folders/{}".format(
            DATA_V1_URL, project_id, folder_id
        )
        headers = self._set_headers(x_user_id)
        data, _ = self.session.request("get", url, headers=headers)
        return data

    def get_folder_contents(
        self, project_id, folder_id, include_hidden=False, x_user_id=None
    ):
        url = "{}/projects/{}/folders/{}/contents".format(
            DATA_V1_URL, project_id, folder_id
        )
        params = {
            "includeHidden": include_hidden,
        }
        contents = self._get_iter(url, params=params, x_user_id=x_user_id)
        if contents and self.log:
            self.logger.info(
                "Fetched {} items from project: {}, folder: {}".format(
                    len(contents), project_id, folder_id
                )
            )

        return contents

    def get_item(self, project_id, item_id, x_user_id=None):
        url = "{}/projects/{}/items/{}".format(
            DATA_V1_URL, project_id, item_id
        )
        headers = self._set_headers(x_user_id)
        data, _ = self.session.request("get", url, headers=headers)
        return data

    def get_item_versions(self, project_id, item_id, x_user_id=None):
        url = "{}/projects/{}/items/{}/versions".format(
            DATA_V1_URL, project_id, item_id
        )
        versions = self._get_iter(url, x_user_id=x_user_id)
        if versions and self.log:
            self.logger.info(
                "Fetched {} versions from item: {} in projcet: {}".format(
                    len(versions), item_id, project_id
                )
            )

        return versions

    def post_item(
        self,
        project_id,
        folder_id,
        object_id,
        name,
        copy_from_id=None,
        x_user_id=None,
    ):
        """
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
                {"type": DM.TYPES[self.hub_type]["items"]}
            )
            json_data["included"][0]["attributes"]["extension"].update(
                {"type": DM.TYPES[self.hub_type]["versions"]}
            )

        data, _ = self.session.request(
            "post", url, headers=headers, json_data=json_data
        )
        return data

    def post_item_version(
        self,
        project_id,
        storage_id,
        item_id,
        name,
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
                    "item": {"data": {"type": "items", "id": item_id}},
                },
            },
        }

        if not copy_from_id:
            json_data["data"]["attributes"]["extension"].update(
                {"type": DM.TYPES[self.hub_type]["versions"]}
            )
            json_data["data"]["relationships"].update(
                {"storage": {"data": {"type": "objects", "id": storage_id}}}
            )
        # else:
        #     json_data["data"]["attributes"]["extension"].update(
        #         {"displayName": name}
        #     )

        data, _ = self.session.request(
            "post", url, headers=headers, json_data=json_data
        )
        return data

    def post_storage(
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
        data, _ = self.session.request(
            "post", url, headers=headers, json_data=json_data
        )
        return data

    def post_folder(
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
                        "type": DM.TYPES[self.hub_type]["folders"],
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
        data, success = self.session.request(
            "post",
            url,
            headers=headers,
            json_data=json_data,
            message="folder '{}' to project '{}'".format(
                folder_name, project_name or project_id
            ),
        )
        if success:
            if self.log:
                self.logger.info(
                    "{}: added '{}' folder".format(
                        project_name or project_id, folder_name
                    )
                )
            return data

    # DATA_V1 - COMMANDS

    def _commands(self, project_id, json_data, x_user_id=None):
        url = "{}/projects/{}/commands".format(DATA_V1_URL, project_id)
        headers = self._set_headers(x_user_id)
        headers.update({"Content-Type": "application/vnd.api+json"})
        data, _ = self.session.request(
            "post", url, headers=headers, json_data=json_data
        )
        return data

    def _commands_publish(self, project_id, item_id, command, x_user_id=None):
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
        return self._commands(project_id, json_data, x_user_id=x_user_id)

    def get_publish_model_job(
        self, project_id, item_id, x_user_id=None,
    ):
        command = DM.TYPES[self.hub_type]["commands"]["get_publish_model_job"]
        return self._commands_publish(
            project_id, item_id, command, x_user_id=x_user_id
        )

    def publish_model(
        self, project_id, item_id, x_user_id=None,
    ):
        command = DM.TYPES[self.hub_type]["commands"]["publish_model"]
        return self._commands_publish(
            project_id, item_id, command, x_user_id=x_user_id
        )

    # OSS V2

    def get_object(self, bucket_key, object_name):
        url = "{}/buckets/{}/objects/{}".format(
            OSS_V2_URL, bucket_key, object_name
        )
        data, _ = self.session.request("get", url, headers=self.auth.header)
        return data

    def put_object(self, bucket_key, object_name, object_bytes):
        url = "{}/buckets/{}/objects/{}".format(
            OSS_V2_URL, bucket_key, object_name
        )
        data, _ = self.session.request(
            "put", url, headers=self.auth.header, byte_data=object_bytes,
        )
        return data
