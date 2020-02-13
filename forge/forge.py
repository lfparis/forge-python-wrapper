from __future__ import absolute_import

import os

from .api import ForgeApi
from .auth import ForgeAuth
from .base import ForgeBase, ForgeItem, Logger

logger = Logger(__name__)()


class ForgeApp(ForgeBase):
    def __init__(
        self,
        client_id=None,
        client_secret=None,
        scopes=None,
        hub_id=None,
        three_legged=False,
        redirect_uri=None,
        username=None,
        password=None,
        log=True,
    ):
        """
        """
        self.auth = ForgeAuth(
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes,
            redirect_uri=redirect_uri,
            three_legged=three_legged,
            username=username,
            password=password,
            log=log,
        )

        self.api = ForgeApi(auth=self.auth, log=log)

        if hub_id or os.environ.get("FORGE_HUB_ID"):
            self.hub_id = hub_id or os.environ.get("FORGE_HUB_ID")

        self.log = log
        if self.log:
            self.logger = logger

    def __repr__(self):
        return "<Forge App - Hub ID: {} at {}>".format(
            self.hub_id, hex(id(self))
        )

    def _validate_hub(func):
        def inner(self, *args, **kwargs):
            if not self.hub_id:
                raise AttributeError("A 'app.hub_id' has not been defined.")
            return func(self, *args, **kwargs)

        return inner

    def _validate_bim360_hub(func):
        def inner(self, *args, **kwargs):
            if self.auth.three_legged:
                raise ValueError(
                    "The BIM 360 API only supports 2-legged access token."
                )
            elif not self.hub_id:
                raise AttributeError("A 'app.hub_id' has not been defined.")
            elif self.hub_id[:2] != "b.":
                raise ValueError(
                    "The 'app.hub_id' must be a {} hub.".format(
                        ForgeBase.BIM_360_TYPES["b."]
                    )
                )
            return func(self, *args, **kwargs)

        return inner

    @property
    def hub_id(self):
        if getattr(self, "_hub_id", None):
            return self._hub_id

    @hub_id.setter
    def hub_id(self, val):
        self._set_hub_id(val)
        self.api.dm.hub_id = val
        self.api.hq.hub_id = val

    def get_hubs(self):
        self.hubs = self.api.dm.get_hubs().get("data")

    @_validate_hub
    def get_projects(self, source="all", include_app=True):
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
        app = self if include_app else None

        self.projects = []
        self._project_indices_by_id = {}
        self._project_indices_by_name = {}

        if self.hub_type == self.BIM_360_TYPES["a."]:
            if not self.auth.three_legged:
                if self.log:
                    self.logger.warning(
                        "Failed to get projects. '{}' hubs only supports 3-legged access token.".format(  # noqa:E501
                            self.BIM_360_TYPES["a."]
                        )
                    )
            else:
                for project in self.api.dm.get_projects():
                    self.projects.append(
                        Project(
                            project["attributes"]["name"],
                            project["id"][2:],
                            data=project,
                            app=app,
                        )
                    )

                    self._project_indices_by_id[project["id"][2:]] = (
                        len(self.projects) - 1
                    )
                    self._project_indices_by_name[
                        project["attributes"]["name"]
                    ] = (len(self.projects) - 1)

        elif self.hub_type == self.BIM_360_TYPES["b."]:

            if source.lower() in ("all", "docs"):
                for project in self.api.dm.get_projects():
                    self.projects.append(
                        Project(
                            project["attributes"]["name"],
                            project["id"][2:],
                            data=project,
                            app=app,
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

                for project in self.api.hq.get_projects():
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
                                app=app,
                            )
                        )
                        self._project_indices_by_id[project["id"]] = (
                            len(self.projects) - 1
                        )

                        self._project_indices_by_name[project["name"]] = (
                            len(self.projects) - 1
                        )

            elif source.lower() in ("all", "admin") and self.log:
                self.logger.warning(
                    "Failed to get projects. The BIM 360 API only supports 2-legged access tokens"  # noqa:E501
                )

    @_validate_bim360_hub
    def get_users(self):
        self.users = self.api.hq.get_users()
        self._user_indices_by_email = {
            user["email"]: i for i, user in enumerate(self.users)
        }

    @_validate_bim360_hub
    def get_companies(self):
        self.companies = self.api.hq.get_companies()
        self._company_indices_by_name = {
            company["name"]: i for i, company in enumerate(self.companies)
        }

    @_validate_bim360_hub
    def add_project(
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
            project = self.api.hq.post_project(
                name,
                start_date=start_date,
                end_date=end_date,
                template=template,
            )
            if project:
                self.projects.append(
                    Project(project["name"], project["id"], data=project)
                )
                self._project_indices_by_id[project["id"]] = (
                    len(self.projects) - 1
                )
                self._project_indices_by_name[project["name"]] = (
                    len(self.projects) - 1
                )
                return self.projects[-1]

    def find_project(self, value, key="name"):
        """key = name or id"""
        if key.lower() not in ("name", "id"):
            raise ValueError()

        if not getattr(self, "projects", None):
            self.get_projects()

        try:
            if key.lower() == "name":
                return self.projects[self._project_indices_by_name[value]]
            elif key.lower() == "id":
                return self.projects[self._project_indices_by_id[value]]
        except KeyError:
            self.logger.warning("Project {}: {} not found".format(key, value))

    def find_user(self, email):
        if not getattr(self, "_user_indices_by_email", None):
            self.get_users()
        try:
            return self.users[self._user_indices_by_email[email]]
        except KeyError:
            self.logger.warning("User email: {} not found".format(email))

    def find_company(self, name):
        if not getattr(self, "_company_indices_by_name", None):
            self.get_companies()

        try:
            return self.companies[self._company_indices_by_name[name]]
        except KeyError:
            self.logger.warning("Company: {} not found".format(name))


class Project(object):
    def __init__(self, name, project_id, app=None, data=None, x_user_id=None):
        self.name = name
        self.id = {"hq": project_id}
        if app:
            self.app = app
        if data:
            self.data = data
        if x_user_id:
            self.x_user_id = x_user_id

    def __repr__(self):
        return "<Project - Name: {} - ID: {} at {}>".format(
            self.name, self.id, hex(id(self))
        )

    def _validate_app(func):
        def inner(self, *args, **kwargs):
            if not self.app:
                raise AttributeError("An 'app' attribute has not been defined")
            return func(self, *args, **kwargs)

        return inner

    def _validate_bim360_hub(func):
        def inner(self, *args, **kwargs):
            if self.app.hub_id[:2] != "b.":
                raise ValueError(
                    "The app.hub_id attribute must be a {} hub.".format(
                        ForgeBase.BIM_360_TYPES["b."]
                    )
                )
            return func(self, *args, **kwargs)

        return inner

    def _validate_x_user_id(func):
        def inner(self, *args, **kwargs):
            if not self.app.auth.three_legged and not self.x_user_id:
                raise AttributeError(
                    "An 'x_user_id' attribute has not been defined"
                )
            return func(self, *args, **kwargs)

        return inner

    @property
    def app(self):
        if getattr(self, "_app", None):
            return self._app

    @app.setter
    def app(self, app):
        if not isinstance(app, ForgeApp):
            raise TypeError("Project.app must be a ForgeApp")
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

    @property
    def x_user_id(self):
        if getattr(self, "_x_user_id", None):
            return self._x_user_id

    @x_user_id.setter
    def x_user_id(self, x_user_id):
        """ """
        if not (isinstance(x_user_id, str)):
            raise TypeError("x_user_id must be a string")
        elif not (len(x_user_id) == 12 and x_user_id[0] == "U"):
            raise ValueError("x_user_id must be a user UID")
        else:
            self._x_user_id = x_user_id

    @_validate_app
    @_validate_bim360_hub
    def update(self, name=None, status=None):
        if self.app.auth.three_legged:
            raise ValueError(
                "The BIM 360 API only supports 2-legged access tokens"
            )

        if name or status:
            project = self.app.api.hq.patch_project(
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
    def get_top_folders(self):
        self.top_folders = self.app.api.dm.get_top_folders(
            self.id["dm"], x_user_id=self.x_user_id
        ).get("data")
        return self.top_folders

    def get_contents(self):
        if not getattr(self, "top_folders", None):
            self.get_top_folders()

        self.contents = {}
        for folder in self.top_folders:
            folder_name = folder["attributes"]["name"]
            self.contents[folder_name] = {"self": folder, "type": folder}
            folder_id = folder["id"]
            folder_contents = self.get_folder_contents(folder_id)
            for item in folder_contents:
                if item["type"] == "folders":
                    pass
                else:
                    pass

    @_validate_app
    def get_project_files_folder(self):
        if not getattr(self, "top_folders", None):
            self.get_top_folders()

        if self.top_folders:
            try:
                folder_names = [
                    folder["attributes"]["name"] for folder in self.top_folders
                ]
                if "Project Files" in folder_names:
                    index = folder_names.index("Project Files")
                    self.project_files_folder = self.top_folders[index]
                    return self.project_files_folder
            except Exception:
                return

    @_validate_app
    def get_folder_contents(self, folder_id, include_hidden=False):
        return self.app.api.dm.get_folder_contents(
            self.id["dm"],
            folder_id,
            include_hidden=include_hidden,
            x_user_id=self.x_user_id,
        )

    @_validate_app
    @_validate_bim360_hub
    def get_project_roles(self):
        self.roles = self.app.api.hq.get_project_roles(self.id["hq"])
        return self.roles

    @_validate_app
    @_validate_bim360_hub
    @_validate_x_user_id
    def add_users(self, users, access_level="user", role_id=None):
        return self.app.api.hq.post_project_users(
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
    def update_user(
        self, user, company_id=None, role_id=None,
    ):
        return self.app.api.hq.patch_project_user(
            self.id["hq"],
            user,
            company_id=company_id,
            role_id=role_id,
            x_user_id=self.x_user_id,
            project_name=self.name,
        )

    @_validate_app
    def add_folder(self, parent_folder_id, folder_name):
        """
        """
        parent_contents = self.get_folder_contents(
            parent_folder_id, include_hidden=True
        )

        if parent_contents:
            try:
                sub_folder_names = [
                    content["attributes"]["name"]
                    for content in parent_contents
                    if content["type"] == "folders"
                ]

                if folder_name not in sub_folder_names:
                    return self.app.api.dm.post_folder(
                        self.id["dm"],
                        parent_folder_id,
                        folder_name,
                        project_name=self.name,
                        x_user_id=self.x_user_id,
                    )

                else:
                    index = sub_folder_names.index(folder_name)
                    folder = parent_contents[index]
                    if self.app.log:
                        self.app.logger.warning(
                            "{}: folder '{}' already exists".format(
                                self.name, folder_name
                            )
                        )
                    return folder
            except Exception as e:
                self.app.logger.warning(
                    "{}: couldn't add '{}' folder".format(
                        self.name, folder_name
                    )
                )
                raise (e)
        else:
            return self.app.api.dm.post_folder(
                self.id["dm"],
                parent_folder_id,
                folder_name,
                project_name=self.name,
                x_user_id=self.x_user_id,
            )


class Folder(ForgeItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "folders"


class File(ForgeItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "items"
