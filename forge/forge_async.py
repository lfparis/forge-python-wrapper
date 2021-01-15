# -*- coding: utf-8 -*-

"""documentation placeholder"""

from __future__ import absolute_import

import asyncio
import os
import time

from aiohttp import (
    ClientConnectionError,
    ClientConnectorError,
    ClientSession,
    ContentTypeError,
    TCPConnector,
)
from json.decoder import JSONDecodeError
from uuid import uuid4

from .api import ForgeApi
from .auth import ForgeAuth
from .base import ForgeBase, Logger
from .decorators import (
    _validate_app,
    _validate_bim360_hub,
    _validate_host,
    _validate_hub,
    _validate_item,
    _validate_project,
    _validate_x_user_id,
)
from .utils import HTTPSemaphore, pretty_print
from .urls import OSS_V2_URL

logger = Logger.start(__name__)

# TODO - Error Logging and Level Consistency


class ForgeAppAsync(ForgeBase):
    def __init__(
        self,
        client_id=None,
        client_secret=None,
        scopes=None,
        hub_id=None,
        asession=None,
        three_legged=False,
        grant_type="implicit",
        redirect_uri=None,
        username=None,
        password=None,
        log_level="info",
    ):
        """"""
        self.logger = logger
        self.log_level = log_level

        self.auth = ForgeAuth(
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes,
            redirect_uri=redirect_uri,
            three_legged=three_legged,
            grant_type=grant_type,
            username=username,
            password=password,
            log_level=log_level,
        )

        self.api = ForgeApi(app=self, async_apis=True)
        self.retries = 5

        if hub_id or os.environ.get("FORGE_HUB_ID"):
            self.hub_id = hub_id or os.environ.get("FORGE_HUB_ID")

    async def __aenter__(self):
        conn = TCPConnector(limit=100)
        self._session = ClientSession(connector=conn, headers=self.auth.header)

        conn_remote = TCPConnector(limit=100)
        self._session_remote = ClientSession(connector=conn_remote)
        return self

    async def __aexit__(self, *err):
        await self._session.close()
        await self._session_remote.close()
        self._session = None
        self._session_remote = None

    def __repr__(self):
        return "<Forge App - Hub ID: {} at {}>".format(
            self.hub_id, hex(id(self))
        )

    async def _request(self, *args, session=None, **kwargs):
        if not session:
            session = self._session
        try:
            res = await session.request(*args, **kwargs)
            err = False
        except (
            ClientConnectionError,
            ClientConnectorError,
            asyncio.TimeoutError,
        ) as e:
            err = True
            self.logger.debug(e)

        count = 1
        step = 5
        while err or res.status in (408, 429, 503):
            self.logger.debug(kwargs)
            try:
                self.logger.debug(
                    f"{res.status}: trying again - {int(count/step)+1} of {self.retries+1} times"  # noqa: E501
                )
            except Exception:
                self.logger.debug(
                    f"Connection/Timeout Error: trying again - {int(count/step)+1} of {self.retries+1} times"  # noqa: E501
                )

            await asyncio.sleep(0.1 * count ** 2)

            try:
                res = await session.request(*args, **kwargs)
                err = False
            except (
                ClientConnectionError,
                ClientConnectorError,
                asyncio.TimeoutError,
            ) as e:
                err = True
                self.logger.debug(e)

            if count >= self.retries * step:
                break
            count += step
        if res.status in (408, 429, 503, 504):
            # res.raise_for_status()
            pass

        return res

    async def _get_data(self, res):
        try:
            return await res.json(encoding="utf-8")
        # else if raw data
        except JSONDecodeError:
            return await res.text(encoding="utf-8")
        except ContentTypeError:
            return await res.read()

    @_validate_bim360_hub
    async def _get_project_admin_data(self, project_id):
        if project_id[:2] in self.NAMESPACES:
            project_id = project_id[2:]

        return await self.api.hq.get_project(project_id)

    @property
    def hub_id(self):
        if getattr(self, "_hub_id", None):
            return self._hub_id

    @hub_id.setter
    def hub_id(self, val):
        self._set_hub_id(val)
        self.api.dm.hub_id = val
        self.api.hq.hub_id = val
        if getattr(self.api, "adm", None):
            self.api.adm.hub_id = val
            self.api.ahq.hub_id = val

    async def get_hubs(self):
        hubs = await self.api.dm.get_hubs()
        if isinstance(hubs, dict) and "data" in hubs:
            self.hubs = hubs.get("data")
        else:
            self.hubs = []

    @_validate_hub
    async def get_projects(self, source="all"):
        """
        Get all projects and sets the self.projects attribute
        Kwargs:
            source (``string``, default="all"): "all", "admin" or "docs"
        Returns:
            {
                id_1: {"docs": {}, "admin": {}},
                id_2: {"docs": {}, "admin": {}},
                id_3: {"docs": {}, "admin": {}},
                id_4: {"admin": {}},
                ...
            }
        """
        self.projects = []
        self._project_indices_by_id = {}
        self._project_indices_by_name = {}

        if self.hub_type == self.NAMESPACES["a."]:
            if not self.auth.three_legged:
                self.logger.warning(
                    "Failed to get projects. '{}' hubs only supports 3-legged access token.".format(  # noqa:E501
                        self.NAMESPACES["a."]
                    )
                )
            else:
                projects = await self.api.dm.get_projects()
                for project in projects:
                    self.projects.append(
                        Project(
                            project["attributes"]["name"],
                            project["id"][2:],
                            data=project,
                            app=self,
                        )
                    )

                    self._project_indices_by_id[project["id"][2:]] = (
                        len(self.projects) - 1
                    )
                    self._project_indices_by_name[
                        project["attributes"]["name"]
                    ] = (len(self.projects) - 1)

        elif self.hub_type == self.NAMESPACES["b."]:

            if source.lower() in ("all", "docs"):
                projects = await self.api.dm.get_projects()
                for project in projects:
                    self.projects.append(
                        Project(
                            project["attributes"]["name"],
                            project["id"][2:],
                            data=project,
                            app=self,
                        )
                    )

                    self._project_indices_by_id[project["id"][2:]] = (
                        len(self.projects) - 1
                    )
                    self._project_indices_by_name[
                        project["attributes"]["name"]
                    ] = (len(self.projects) - 1)

            if (
                source.lower() in ("all", "admin")
                and not self.auth.three_legged
            ):

                projects = await self.api.hq.get_projects()
                for project in projects:
                    if project["id"] in self._project_indices_by_id:
                        self.projects[
                            self._project_indices_by_id[project["id"]]
                        ].data = project
                    else:
                        self.projects.append(
                            Project(
                                project["name"],
                                project["id"],
                                data=project,
                                app=self,
                            )
                        )
                        self._project_indices_by_id[project["id"]] = (
                            len(self.projects) - 1
                        )

                        self._project_indices_by_name[project["name"]] = (
                            len(self.projects) - 1
                        )

            elif source.lower() in ("all", "admin"):
                self.logger.debug(
                    "Failed to get projects. The BIM 360 API only supports 2-legged access tokens"  # noqa:E501
                )

    @_validate_hub
    async def get_project(self, project_id):
        if project_id[:2] not in self.NAMESPACES:
            project_id = "{}{}".format(self.hub_id[:2], project_id)

        project = await self.api.dm.get_project(
            project_id, x_user_id=self.x_user_id
        )
        if isinstance(project, dict) and "data" in project:
            pj = Project(
                project["data"]["attributes"]["name"],
                project["data"]["id"][2:],
                data=project["data"],
                app=self,
            )
            if self.hub_id[:2] == "b." and not self.auth.three_legged:
                admin_data = await self._get_project_admin_data(project_id[2:])
                if admin_data:
                    pj.data = admin_data
            return pj

    @_validate_bim360_hub
    async def get_users(self):
        self.users = await self.api.hq.get_users()
        self._user_indices_by_email = {
            user["email"]: i for i, user in enumerate(self.users)
        }

    @_validate_bim360_hub
    async def get_user(self, user_id):
        return await self.api.hq.get_user(user_id)

    @_validate_bim360_hub
    async def get_companies(self):
        self.companies = await self.api.hq.get_companies()
        self._company_indices_by_name = {
            company["name"]: i for i, company in enumerate(self.companies)
        }

    @_validate_bim360_hub
    async def add_project(
        self,
        name,
        start_date=ForgeBase.TODAY_STRING,
        end_date=ForgeBase.IN_ONE_YEAR_STRING,
        template=None,
    ):

        if not getattr(self, "projects", None):
            self.projects = []
            self._project_indices_by_id = {}
            self._project_indices_by_name = {}

        if name not in self._project_indices_by_name:
            project = await self.api.hq.post_project(
                name,
                start_date=start_date,
                end_date=end_date,
                template=template,
            )
            if project:
                self.projects.append(
                    Project(
                        project["name"], project["id"], app=self, data=project
                    )
                )
                self._project_indices_by_id[project["id"]] = (
                    len(self.projects) - 1
                )
                self._project_indices_by_name[project["name"]] = (
                    len(self.projects) - 1
                )
                return self.projects[-1]

    async def find_project(self, value, key="name"):
        """key = name or id"""
        if not value:
            return
        if key.lower() not in ("name", "id"):
            raise ValueError()

        if key == "name" and not getattr(self, "projects", None):
            await self.get_projects()
        elif key == "id" and not getattr(self, "projects", None):
            return await self.get_project(value)

        try:
            if key.lower() == "name":
                return self.projects[self._project_indices_by_name[value]]
            elif key.lower() == "id":
                return self.projects[self._project_indices_by_id[value]]
        except KeyError:
            self.logger.debug("Project {}: {} not found".format(key, value))

    async def find_user(self, value, key="name"):
        """key = name or email or id"""
        if not value:
            return

        if key.lower() not in ("name", "id", "email"):
            raise ValueError()

        if key.lower() == "id":
            return await self.get_user(value)
        else:
            params = {key.lower(): value}
            try:
                users = await self.api.hq.get_users_search(**params)
                return users[0]
            except IndexError:
                self.logger.debug("User {}: {} not found".format(key, value))

    async def find_company(self, name):
        if not getattr(self, "_company_indices_by_name", None):
            await self.get_companies()

        try:
            return self.companies[self._company_indices_by_name[name]]
        except KeyError:
            self.logger.debug("Company: {} not found".format(name))


class Project(ForgeBase):
    def __init__(
        self,
        name,
        project_id,
        app=None,
        data=None,
        x_user_id=None,
        include_hidden=False,
    ):
        self.name = name
        self.id = {"hq": project_id}
        if app:
            self.app = app
        if data:
            self.data = data
        if x_user_id:
            self.x_user_id = x_user_id
        self.include_hidden = include_hidden

    def __repr__(self):
        return "<Project - Name: {} - ID: {} at {}>".format(
            self.name, self.id, hex(id(self))
        )

    @property
    def app(self):
        if getattr(self, "_app", None):
            return self._app

    @app.setter
    def app(self, app):
        if not isinstance(app, ForgeAppAsync):
            raise TypeError("Project.app must be a ForgeAppAsync")
        elif not app.hub_id:
            raise AttributeError(
                "A 'hub_id' attribute has not been defined in your app"
            )
        else:
            self._app = app
            self.id["dm"] = app.hub_id[:2] + self.id["hq"]

    @property
    def data(self):
        if getattr(self, "_data", None):
            return self._data

    @data.setter
    def data(self, data):
        if not isinstance(data, dict):
            raise TypeError("Project.data must be a dictionary")
        else:
            if not getattr(self, "_data", None):
                self._data = {}
            if "account_id" in data:
                self._data["admin"] = data
            elif "attributes" in data:
                self._data["docs"] = data

    @_validate_app
    @_validate_bim360_hub
    async def update(self, name=None, status=None):
        if self.app.auth.three_legged:
            raise ValueError(
                "The BIM 360 API only supports 2-legged access tokens"
            )

        if name or status:
            project = await self.app.api.hq.patch_project(
                self.id["hq"], name=name, status=status, project_name=self.name
            )

            if project:
                if name and getattr(self.app, "projects", None):
                    try:
                        index = self.app._project_indices_by_name[self.name]
                        self.app._project_indices_by_name[name] = index
                        self.name = name
                    except Exception as e:
                        print(e)
                self.data = project

    @_validate_app
    async def get_top_folders(self):
        data = []
        count = 0
        while not data:
            if count > 0:
                time.sleep(5)

            data = await self.app.api.dm.get_top_folders(
                self.id["dm"], x_user_id=self.x_user_id
            )
            if isinstance(data, dict) and "data" in data:
                folders = data.get("data") or []
            else:
                data = None
                folders = []

            count += 1
            if count > 6:
                break

        self.top_folders = [
            Folder(
                folder["attributes"]["name"],
                folder["id"],
                extension_type=folder["attributes"]["extension"]["type"],
                data=folder,
                project=self,
            )
            for folder in folders
        ]

        if self.top_folders:
            if self.app.hub_type == ForgeBase.NAMESPACES["a."]:
                self.project_files = self.top_folders[0]
                self.plans = None
            elif self.app.hub_type == ForgeBase.NAMESPACES["b."]:
                folder_names = [folder.name for folder in self.top_folders]
                self.project_files = (
                    self.top_folders[folder_names.index("Project Files")]
                    if "Project Files" in folder_names
                    else None
                )
                self.plans = (
                    self.top_folders[folder_names.index("Plans")]
                    if "Plans" in folder_names
                    else None
                )

        return self.top_folders

    async def get_contents(self):
        if not getattr(self, "top_folders", None):
            await self.get_top_folders()

        for folder in self.top_folders:
            await folder.get_contents()

    @_validate_app
    @_validate_bim360_hub
    async def get_roles(self):
        self.roles = await self.app.api.hq.get_project_roles(self.id["hq"])
        return self.roles

    @_validate_app
    @_validate_bim360_hub
    @_validate_x_user_id
    async def add_users(self, users, access_level="user", role_id=None):
        return await self.app.api.hq.post_project_users(
            self.id["hq"],
            users,
            access_level=access_level,
            role_id=role_id,
            x_user_id=self.x_user_id,
            project_name=self.name,
        )

    @_validate_app
    @_validate_bim360_hub
    @_validate_x_user_id
    async def update_user(
        self,
        user,
        company_id=None,
        role_id=None,
    ):
        return await self.app.api.hq.patch_project_user(
            self.id["hq"],
            user,
            company_id=company_id,
            role_id=role_id,
            x_user_id=self.x_user_id,
            project_name=self.name,
        )

    async def find(self, value, key="name"):
        """key = name or id or path"""
        if key.lower() not in ("name", "id", "path"):
            raise ValueError()

        if not getattr(self, "top_folders", None):
            await self.get_contents()

        for folder in self.top_folders:
            if getattr(folder, key, None) == value:
                return folder
            else:
                async for content, _ in folder._iter_contents():
                    if getattr(content, key, None) == value:
                        return content

        self.app.logger.debug(
            "{}: {} not found in '{}'".format(key, value, self.name)
        )

    async def walk(self):
        if not getattr(self, "top_folders", None):
            await self.get_contents()

        for folder in self.top_folders:
            print(folder.name)
            await folder.walk(level=1)


class Content(object):
    def __init__(
        self,
        name,
        content_id,
        extension_type=None,
        data=None,
        project=None,
        host=None,
    ):
        self.name = name
        self.id = content_id
        self.extension_type = extension_type
        self.data = data
        self.path = "/{}".format(self.name)
        if project:
            self.project = project
        if host:
            self.host = host
            self.path = "{}{}".format(host.path, self.path)

    @property
    def extension_type(self):
        if getattr(self, "_extension_type", None):
            return self._extension_type

    @extension_type.setter
    def extension_type(self, extension_type):
        self._extension_type = extension_type
        self.deleted = extension_type in (
            ForgeBase.TYPES[ForgeBase.NAMESPACES["a."]]["versions"]["Deleted"],
            ForgeBase.TYPES[ForgeBase.NAMESPACES["b."]]["versions"]["Deleted"],
        )

    @property
    def project(self):
        if getattr(self, "_project", None):
            return self._project

    @project.setter
    def project(self, project):
        if not isinstance(project, Project):
            raise TypeError("Item.project must be a Project")
        elif not project.app:
            raise AttributeError(
                "A 'app' attribute has not been defined in your Project"
            )
        else:
            self._project = project

    @property
    def host(self):
        if getattr(self, "_host", None):
            return self._host

    @host.setter
    def host(self, host):
        if not isinstance(host, Folder):
            raise TypeError("Item.project must be a Project")
        elif not host.project:
            raise AttributeError(
                "A 'project' attribute has not been defined in your host"
            )
        else:
            self._host = host

    def _unpack_storage_id(self, storage_id):
        """returns bucket_key, object_name"""
        return storage_id.split(":")[-1].split("/")


class Folder(Content):
    def __init__(self, *args, **kwargs):
        """
        Args:
            name (``str``): The name of the folder.
            id (``str``): The id of the folder.

        Kwargs:
            data (``dict``): The data of the folder.
            project (``Project``): The Project where this folder is.
            host (``Folder``): The host folder.
        """
        super().__init__(*args, **kwargs)
        self.type = "folders"
        self.contents = []

    async def _iter_contents(self, level=0):
        for content in self.contents:
            yield content, level
            if content.type == "folders":
                async for sub_content, sub_level in content._iter_contents(
                    level=level + 1
                ):
                    yield sub_content, sub_level

    @_validate_project
    async def get_contents(self):
        contents = await self.project.app.api.dm.get_folder_contents(
            self.project.id["dm"],
            self.id,
            include_hidden=self.project.include_hidden,
            x_user_id=self.project.x_user_id,
        )

        self.contents = []
        for content in contents:
            if content["type"] == "items":
                self.contents.append(
                    Item(
                        # TODO - name or displayName
                        content["attributes"]["displayName"],
                        content["id"],
                        extension_type=content["attributes"]["extension"][
                            "type"
                        ],
                        data=content,
                        project=self.project,
                        host=self,
                    )
                )
            elif content["type"] == "folders":
                self.contents.append(
                    Folder(
                        content["attributes"]["name"],
                        content["id"],
                        extension_type=content["attributes"]["extension"][
                            "type"
                        ],
                        data=content,
                        project=self.project,
                        host=self,
                    )
                )
                await self.contents[-1].get_contents()

        return self.contents

    @_validate_project
    async def add_sub_folder(self, folder_name):
        """"""
        if not self.contents:
            await self.get_contents()

        if self.contents:
            try:
                sub_folder_names = [
                    content.name
                    for content in self.contents
                    if content.type == "folders"
                ]

                if folder_name not in sub_folder_names:
                    folder = await self.project.app.api.dm.post_folder(
                        self.project.id["dm"],
                        self.id,
                        folder_name,
                        project_name=self.project.name,
                        x_user_id=self.project.x_user_id,
                    )

                    self.contents.append(
                        Folder(
                            folder["data"]["attributes"]["name"],
                            folder["data"]["id"],
                            extension_type=folder["data"]["attributes"][
                                "extension"
                            ]["type"],
                            data=folder["data"],
                            project=self.project,
                            host=self,
                        )
                    )
                    folder = self.contents[-1]

                else:
                    index = sub_folder_names.index(folder_name)
                    folder = self.contents[index]
                    self.project.app.logger.debug(
                        "{}: folder '{}' already exists in '{}'".format(
                            self.project.name, folder_name, self.name
                        )
                    )
            except Exception as e:
                self.project.app.logger.debug(
                    "{}: couldn't add '{}' folder to '{}'".format(
                        self.name, folder_name, self.name
                    )
                )
                raise (e)
        else:
            folder = await self.project.app.api.dm.post_folder(
                self.project.id["dm"],
                self.id,
                folder_name,
                project_name=self.project.name,
                x_user_id=self.project.x_user_id,
            )
            self.contents.append(
                Folder(
                    folder["data"]["attributes"]["name"],
                    folder["data"]["id"],
                    extension_type=folder["data"]["attributes"]["extension"][
                        "type"
                    ],
                    data=folder["data"],
                    project=self.project,
                    host=self,
                )
            )
            folder = self.contents[-1]
        return folder

    @_validate_project
    async def _add_storage(self, name):
        for i in range(5):
            storage = await self.project.app.api.dm.post_storage(
                self.project.id["dm"],
                "folders",
                self.id,
                name,
                x_user_id=self.project.x_user_id,
            )
            if isinstance(storage, dict) and "data" in storage:
                return storage.get("data")
            else:
                await asyncio.sleep(i ** 2)

    # TODO - untested
    @_validate_project
    async def _upload_file(self, storage_id, obj_bytes):
        bucket_key, object_name = self._unpack_storage_id(storage_id)
        return await self.project.app.api.dm.put_object(
            bucket_key, object_name, obj_bytes
        )

    # TODO - untested
    @_validate_project
    async def add_item(
        self,
        name,
        storage_id=None,
        obj_bytes=None,
        item_extension_type=None,
        version_extension_type=None,
    ):
        """
        name include extension
        """
        if not storage_id and obj_bytes:
            storage = await self._add_storage(name)
            if isinstance(storage, dict) and "id" in storage:
                storage_id = storage.get("id")
            else:
                storage_id = None

        if obj_bytes:
            await self._upload_file(storage_id, obj_bytes)

        if not storage_id:
            return

        item = await self.project.app.api.dm.post_item(
            self.project.id["dm"],
            self.id,
            storage_id,
            name,
            item_extension_type=item_extension_type,
            version_extension_type=version_extension_type,
            x_user_id=self.project.x_user_id,
        )

        if isinstance(item, dict) and "data" in item:
            self.contents.append(
                Item(
                    item["data"]["attributes"]["displayName"],
                    item["data"]["id"],
                    extension_type=item["data"]["attributes"]["extension"][
                        "type"
                    ],
                    data=item["data"],
                    project=self.project,
                    host=self,
                )
            )
            return self.contents[-1]

    @_validate_project
    async def copy_item(self, original_item):
        """
        name include extension
        """
        await original_item.get_versions()
        storage = await self._add_storage(original_item.name)
        item = await self.project.app.api.dm.post_item(
            self.project.id["dm"],
            self.id,
            storage["id"],
            original_item.name,
            x_user_id=self.project.x_user_id,
            copy_from_id=original_item.versions[
                len(original_item.versions) - 1
            ].id,
        )

        if isinstance(item, dict) and "data" in item:
            return Item(
                item["data"]["attributes"]["displayName"],
                item["data"]["id"],
                extension_type=item["data"]["attributes"]["extension"]["type"],
                data=item,
                project=self.project,
                host=self,
            )
        else:
            return item

    async def find(self, value, key="name", shallow=True):
        """key = name or id or path"""
        if key.lower() not in ("name", "id", "path"):
            raise ValueError()

        if not self.contents:
            await self.get_contents()

        async for content, level in self._iter_contents():
            if shallow and level != 0:
                continue
            if getattr(content, key, None) == value:
                return content

        self.project.app.logger.debug(
            "{}: {} not found in '{}'".format(key, value, self.name)
        )

    async def walk(self, level=0):
        if not self.contents:
            await self.get_contents()

        async for content, level in self._iter_contents(level=level):
            print("{}{}".format(" " * 4 * level, content.name))


class Item(Content):
    def __init__(self, *args, **kwargs):
        """
        Args:
            name (``str``): The name of the file including the file extension.
            id (``str``): The id of the file.

        Kwargs:
            data (``dict``): The data of the file.
            project (``Project``): The Project where this file is.
            host (``Folder``): The host folder.
        """
        super().__init__(*args, **kwargs)
        self.type = "items"
        self.versions = []
        self.storage_id = None

    @_validate_project
    async def get_metadata(self):
        self.metadata = await self.project.app.api.dm.get_item(
            self.project.id["dm"], self.id, x_user_id=self.project.x_user_id
        )

        self.hidden = self.metadata["data"]["attributes"]["hidden"]
        self.deleted = self.metadata["included"][0]["attributes"]["extension"][
            "type"
        ] in (
            ForgeBase.TYPES[ForgeBase.NAMESPACES["a."]]["versions"]["Deleted"],
            ForgeBase.TYPES[ForgeBase.NAMESPACES["b."]]["versions"]["Deleted"],
        )

        try:
            self.storage_id = self.metadata["included"][0]["relationships"][
                "storage"
            ]["data"]["id"]
            self.bucket_key, self.object_name = self._unpack_storage_id(
                self.storage_id
            )
        except (AttributeError, KeyError, TypeError):
            # no storage key
            pass

    # TODO - untested
    @_validate_project
    @_validate_host
    async def add_version(
        self,
        name,
        storage_id=None,
        obj_bytes=None,
        version_extension_type=None,
    ):
        """
        name include extension
        """
        if not storage_id and obj_bytes:
            storage = await self.host._add_storage(name)
            if isinstance(storage, dict) and "id" in storage:
                storage_id = storage.get("id")
            else:
                storage_id = None

        if obj_bytes:
            await self.host._upload_file(storage_id, obj_bytes)

        if not storage_id:
            return

        version = await self.project.app.api.dm.post_item_version(
            self.project.id["dm"],
            storage_id,
            self.id,
            name,
            version_extension_type=version_extension_type,
            x_user_id=self.project.x_user_id,
        )

        if isinstance(version, dict) and "data" in version:
            self.versions.append(
                Version(
                    version["data"]["attributes"]["name"],
                    int(version["data"]["attributes"]["versionNumber"]),
                    version["data"]["id"],
                    extension_type=version["data"]["attributes"]["extension"][
                        "type"
                    ],
                    item=self,
                    data=version["data"],
                )
            )
            self._version_names.append(self.versions[-1].name)
            return self.versions[-1]
        else:
            pretty_print(version)

    @_validate_project
    async def get_versions(self):
        self.versions = [
            Version(
                # TODO - name or displayName
                version["attributes"]["name"],
                int(version["attributes"]["versionNumber"]),
                version["id"],
                extension_type=version["attributes"]["extension"]["type"],
                item=self,
                data=version,
            )
            for version in await self.project.app.api.dm.get_item_versions(
                self.project.id["dm"],
                self.id,
                x_user_id=self.project.x_user_id,
            )
            if version["type"] == "versions"
        ]
        self._version_indices_by_number = {
            version.number: i for i, version in enumerate(self.versions)
        }

        self._version_names = [version.name for version in self.versions][::-1]
        return self.versions

    @_validate_project
    async def get_publish_status(self):
        return await self.project.app.api.dm.get_publish_model_job(
            self.project.id["dm"], self.id, x_user_id=self.project.x_user_id
        )

    @_validate_project
    async def publish(self):
        publish_status = await self.get_publish_status()
        if isinstance(publish_status, dict) and (
            "data" in publish_status and "errors" not in publish_status
        ):
            publish_job = await self.project.app.api.dm.publish_model(
                self.project.id["dm"],
                self.id,
                x_user_id=self.project.x_user_id,
            )
            status = publish_job["data"]["attributes"]["status"]
            self.project.app.logger.info(
                "Published model. Status is '{}'".format(status)
            )
        elif (
            isinstance(publish_status, dict) and "errors" not in publish_status
        ):
            status = publish_status["data"]["attributes"]["status"]
            self.project.app.logger.info(
                "Model did not need to be published. Latest version status is '{}'".format(  # noqa:E501
                    status
                )
            )
        else:
            status = None
            self.project.app.logger.info(
                "This item cannot need to be published"
            )

    @_validate_project
    async def download(self, save=False, location=None):
        if not getattr(self, "metadata", None):
            await self.get_metadata()

        if not getattr(self, "storage_id", None):
            self.project.app.logger.info(
                "File '{}': No data to download. Hidden: {}, Deleted: {}".format(  # noqa:E501
                    self.name, self.hidden, self.deleted
                )
            )
            self.bytes = None
            return

        self.project.app.logger.info("Downloading Item {}".format(self.name))
        self.bytes = await self.project.app.api.dm.get_object(
            self.bucket_key, self.object_name
        )
        self.project.app.logger.info(
            "Download Finished - file size: {0:0.1f} MB".format(
                len(self.bytes) / 1024 / 1024
            )
        )
        if save and location and os.path.isdir(location):
            self.filepath = os.path.join(location, self.name)
            with open(self.filepath, "wb") as fp:
                fp.write(self.bytes)
            self.bytes = None

    async def load(self):
        if getattr(self, "filepath", None):
            with open(self.filepath, "rb") as fp:
                self.bytes = fp.read()


class Version(Content):
    # heroku / lambda semaphore
    # https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html#limits-list  # noqa: E501
    lambda_sem = HTTPSemaphore(value=50, interval=60, max_calls=1000)

    def __init__(
        self,
        name,
        number,
        version_id,
        extension_type=None,
        item=None,
        data=None,
    ):
        self.name = name
        self.number = number
        self.id = version_id
        self.extension_type = extension_type
        self.data = data
        if item:
            self.item = item

    @property
    def item(self):
        if getattr(self, "_item", None):
            return self._item

    @item.setter
    def item(self, item):
        if not isinstance(item, Item):
            raise TypeError("Version.item must be a Item")
        elif not item.project:
            raise AttributeError(
                "A 'project' attribute has not been defined in your Item"
            )
        else:
            self._item = item

    @_validate_item
    async def get_metadata(self):
        self.metadata = await self.item.project.app.api.dm.get_version(
            self.item.project.id["dm"],
            self.id,
            x_user_id=self.item.project.x_user_id,
        )
        if self.extension_type is None:
            self.extension_type = self.metadata["data"]["attributes"][
                "extension"
            ]["type"]
        if self.name is None:
            self.name = self.metadata["data"]["attributes"]["name"]

        try:
            self.storage_id = self.metadata["data"]["relationships"][
                "storage"
            ]["data"]["id"]
            self.bucket_key, self.object_name = self._unpack_storage_id(
                self.storage_id
            )
        except (AttributeError, KeyError, TypeError):
            self.storage_id = None

        try:
            self.file_size = self.metadata["data"]["attributes"]["storageSize"]
        except (AttributeError, KeyError, TypeError):
            self.file_size = -1

    @_validate_item
    async def get_details(self):
        if not getattr(self, "metadata", None):
            await self.get_metadata()

        if not getattr(self, "storage_id", None):
            self.item.project.app.logger.info(
                "File '{}' - Version '{}' : No data to download. Deleted: {}".format(  # noqa:E501
                    self.item.name, self.number, self.deleted
                )
            )
            return

        self.details = await self.item.project.app.api.dm.get_object_details(
            self.bucket_key, self.object_name
        )
        try:
            self.storage_size = self.details["size"]
        except (AttributeError, KeyError, TypeError):
            self.storage_size = -1

    @_validate_item
    async def transfer(
        self,
        target_host,
        target_item=None,
        chunk_size=50000000,
        force_create=False,
        remote=None,
    ):
        """
        force_create to force create an item if item is not in target_host

        remote : None or dict
        {
            post_url: "url"
            callback_url: "url"
            force_local: True or False
        }
        """
        await self.get_details()

        if not getattr(self, "storage_size", None):
            self.item.project.app.logger.warning(
                "Couldn't add Version: {} of Item: '{}', because no data was found".format(  # noqa: E501
                    self.number, self.item.name
                )
            )
            return

        # find item to add version
        # TODO - name or displayName
        target_item = (
            target_item
            or await target_host.find(self.name)
            or await target_host.find(self.item.name)
            or await target_host.find(
                self.item._version_names[self.number - 2]
            )
        )

        if not target_item and (not force_create and self.number != 1):
            self.item.project.app.logger.warning(
                "Couldn't add Version: {} of Item: '{}' because no Item found".format(  # noqa: E501
                    self.number, self.name
                )
            )
            return

        elif target_item:
            await target_item.get_versions()
            if len(target_item.versions) == self.number:
                self.item.project.app.logger.warning(
                    "Couldn't add Version: {} of Item: '{}' because Version already exists".format(  # noqa: E501
                        self.number, self.name
                    )
                )
                return target_item
            elif len(target_item.versions) != self.number - 1:
                self.item.project.app.logger.warning(
                    "Couldn't add Version: {} of Item: '{}' because Item has {} versions".format(  # noqa: E501
                        self.number, self.name, len(target_item.versions)
                    )
                )
                return target_item

        # TODO - name or displayName
        tg_storage = await target_host._add_storage(self.name)
        if isinstance(tg_storage, dict) and "id" in tg_storage:
            tg_storage_id = tg_storage.get("id")
        else:
            self.item.project.app.logger.warning(
                "Couldn't add Version: {} of Item: '{}' because: Failed to create storage".format(  # noqa: E501
                    self.number, self.name
                )
            )
            return target_item

        start = time.perf_counter()
        self.item.project.app.logger.info(
            "Beginning transfer of: '{}' - version: {}".format(
                self.name, self.number
            )
        )

        if not (
            await self._transfer_remote(
                target_host,
                tg_storage_id,
                remote,
                chunk_size,
            )
            if remote
            else await self._transfer_local(
                target_host, tg_storage_id, chunk_size
            )
        ):
            self.item.project.app.logger.warning(
                f"Could not transfer: '{self.item.name}' version: '{self.number}'"  # noqa: E501
            )
            return target_item

        version_ext_type = ForgeBase._convert_extension_type(
            self.extension_type,
            target_host.project.app.hub_type,
        )

        if force_create or self.number == 1:
            item_ext_type = ForgeBase._convert_extension_type(
                self.item.extension_type,
                target_host.project.app.hub_type,
            )
            target_item = await target_host.add_item(
                # TODO - name or displayName
                self.name,
                storage_id=tg_storage_id,
                item_extension_type=item_ext_type,
                version_extension_type=version_ext_type,
            )
        else:
            await target_item.add_version(
                # TODO - name or displayName
                self.name,
                storage_id=tg_storage_id,
                version_extension_type=version_ext_type,
            )
        end = time.perf_counter() - start
        # TODO - name or displayName
        self.item.project.app.logger.info(
            f"Finished transfer of: '{self.name}' version: '{self.number}'. ({self.storage_size/1024**2:0.2f} MBs in {end:0.2f} seconds)"  # noqa: E501
        )
        return target_item

    async def _transfer_remote(
        self,
        target_host,
        tg_storage_id,
        remote,
        chunk_size,
    ):
        """ """
        tg_bucket_key, tg_object_name = self._unpack_storage_id(tg_storage_id)

        task_id = uuid4()
        tasks = []

        data_left = self.storage_size
        count = 0

        while data_left > 0:
            lower = count * chunk_size
            upper = lower + chunk_size
            if upper > self.storage_size:
                upper = self.storage_size
            upper -= 1

            source_headers = {"Range": f"bytes={lower}-{upper}"}
            source_headers.update(self.item.project.app.auth.header)

            target_headers = {
                "Content-Length": str(self.storage_size),
                "Session-Id": f"{task_id}",
                "Content-Range": f"bytes {lower}-{upper}/{self.storage_size}",  # noqa: E501
            }
            target_headers.update(target_host.project.app.auth.header)

            body = {
                "name": self.name,
                "task_id": f"{task_id}-{count}",
                "source": {
                    "url": f"{OSS_V2_URL}/buckets/{self.bucket_key}/objects/{self.object_name}",  # noqa: E501
                    "headers": source_headers,
                    "method": "GET",
                    "encoding": None,
                },
                "destination": {
                    "url": f"{OSS_V2_URL}/buckets/{tg_bucket_key}/objects/{tg_object_name}/resumable",  # noqa: E501
                    "headers": target_headers,
                    "method": "PUT",
                    "encoding": None,
                },
                "forceLocal": remote["force_local"],
            }

            headers = {"Content-Type": "application/json; charset=utf-8"}

            tasks.append(
                asyncio.create_task(
                    self._transfer_chunk(remote["post_url"], headers, body)
                )
            )

            data_left -= chunk_size
            count += 1
            await asyncio.sleep(0.21)

        chunk_status = await asyncio.gather(*tasks)

        if remote["force_local"] and 200 in chunk_status:
            return True

        for i in range(6):
            await asyncio.sleep(0.21 * (i + 1) ** 3)
            details = await self.item.project.app.api.dm.get_object_details(  # noqa: E501
                tg_bucket_key, tg_object_name
            )
            if isinstance(details, dict) and "size" in details:
                return True
        return False

    async def _transfer_chunk(self, url, headers, body):
        # async with Version.lambda_sem:
        res = await self.item.project.app._request(
            session=self.item.project.app._session_remote,
            method="POST",
            url=url,
            headers=headers,
            json=body,
        )
        data = await self.item.project.app._get_data(res)
        if res.status == 504:
            self.item.project.app.logger.debug(
                f"{res.status}: {data['name']}:{data['taskId']}"
            )
        elif not (res.status >= 200 and res.status < 300):
            # print(res.status)
            self.item.project.app.logger.debug(
                pretty_print(data, _print=False)
            )

        return res.status

    async def _transfer_local(self, target_host, tg_storage_id, chunk_size):
        """ """
        tg_bucket_key, tg_object_name = self._unpack_storage_id(tg_storage_id)

        data_left = self.storage_size
        count = 0
        while data_left > 0:
            lower = count * chunk_size
            upper = lower + chunk_size
            if upper > self.storage_size:
                upper = self.storage_size
            upper -= 1

            chunk = await self.item.project.app.api.dm.get_object(
                self.bucket_key,
                self.object_name,
                byte_range=(lower, upper),
            )

            await target_host.project.app.api.dm.put_object_resumable(
                tg_bucket_key,
                tg_object_name,
                chunk,
                self.storage_size,
                (lower, upper),
            )

            data_left -= chunk_size
            count += 1

        return True
