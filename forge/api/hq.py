# -*- coding: utf-8 -*-

"""documentation placeholder"""

from __future__ import absolute_import

import time

from ..base import ForgeBase, Logger
from ..decorators import _validate_token
from ..urls import HQ_V1_URL, HQ_V2_URL

logger = Logger.start(__name__)


class HQ(ForgeBase):
    def __init__(self, *args, **kwargs):
        self.auth = kwargs.get("auth")
        self.logger = logger
        self.log_level = kwargs.get("log_level")

    def _get_iter(self, url, name, headers=None, params={}):
        params["limit"] = 100
        response = []
        count = 0
        while True:
            params["offset"] = count * 100
            # if self.refresh_token:
            #     self._refresh_token()
            data, _ = self.session.request(
                "get", url, headers=headers, params=params
            )
            time.sleep(0.200)
            response.extend(data)
            count += 1
            if len(data) < 100:
                break

        if response:
            if isinstance(response[0], dict):
                self.logger.info(
                    "Fetched {} {} from Autodesk BIM 360".format(
                        len(response), name
                    )
                )
            else:
                self.logger.warning(
                    "No {} fetched from Autodesk BIM 360".format(name)
                )
        return response

    # HQ V1

    @_validate_token
    def get_users(self):
        url = "{}/accounts/{}/users".format(HQ_V1_URL, self.account_id)
        return self._get_iter(url, "users", headers=self.auth.header)

    @_validate_token
    def get_users_search(
        self,
        name=None,
        email=None,
        company_name=None,
        partial=True,
        limit=None,
        sort=None,
        field=None,
    ):
        """
        https://forge.autodesk.com/en/docs/bim360/v1/reference/http/users-search-GET/
        """  # noqa: E501
        params = {
            "name": name,
            "email": email,
            "company_name": company_name,
            "partial": partial,
            "limit": limit,
            "sort": sort,
            "field": field,
        }
        url = "{}/accounts/{}/users/search".format(HQ_V1_URL, self.account_id)
        return self._get_iter(
            url, "users", headers=self.auth.header, params=params
        )

    @_validate_token
    def get_user(self, user_id):
        url = "{}/accounts/{}/users/{}".format(
            HQ_V1_URL, self.account_id, user_id
        )
        data, _ = self.session.request(
            "get",
            url,
            headers=self.auth.header,
            message="user '{}'".format(user_id),
        )
        return data

    @_validate_token
    def get_projects(self):
        url = "{}/accounts/{}/projects".format(HQ_V1_URL, self.account_id)
        return self._get_iter(url, "projects", headers=self.auth.header)

    @_validate_token
    def get_project(self, project_id):
        url = "{}/accounts/{}/projects/{}".format(
            HQ_V1_URL, self.account_id, project_id
        )
        data, _ = self.session.request(
            "get",
            url,
            headers=self.auth.header,
            message="project '{}'".format(project_id),
        )
        return data

    @_validate_token
    def get_companies(self):
        url = "{}/accounts/{}/companies".format(HQ_V1_URL, self.account_id)
        return self._get_iter(url, "companies", headers=self.auth.header)

    @_validate_token
    def post_project(
        self,
        name,
        start_date=ForgeBase.TODAY_STRING,
        end_date=ForgeBase.IN_ONE_YEAR_STRING,
        template=None,
    ):
        url = "{}/accounts/{}/projects".format(HQ_V1_URL, self.account_id)
        headers = {"Content-Type": "application/json"}
        headers.update(self.auth.header)

        json_data = {
            "name": name,
            "service_types": "doc_manager",
            "start_date": start_date,
            "end_date": end_date,
            "project_type": "Office",
            "value": "0",
            "currency": "USD",
        }

        if template:
            try:
                json_data["template_project_id"] = template["id"]
                json_data["include_locations"] = True
                json_data["include_companies"] = True
            except KeyError:
                pass

        data, success = self.session.request(
            "post",
            url,
            headers=headers,
            json_data=json_data,
            message="project '{}'".format(name),
        )
        if success:
            self.logger.info("Added: {}".format(name))
            return data
        else:
            self.logger.debug("Failed to add: {}".format(name))

    @_validate_token
    def patch_project(
        self, project_id, name=None, status=None, project_name=None
    ):
        json_data = {}
        if name:
            json_data["name"] = name
        if status:
            json_data["status"] = status
        if json_data:
            url = "{}/accounts/{}/projects/{}".format(
                HQ_V1_URL, self.account_id, project_id
            )
            headers = {"Content-Type": "application/json"}
            headers.update(self.auth.header)
            key = list(json_data.keys())[0]

            data, success = self.session.request(
                "patch",
                url,
                headers=headers,
                json_data=json_data,
                message="project <{}: {} to {}>".format(
                    project_name or project_id, key, json_data[key]
                ),
            )
            if success:
                self.logger.info(
                    "{}: updated {} to {}".format(
                        project_name or project_id, key, json_data[key]
                    )
                )
                return data

    # HQ V2

    @_validate_token
    def get_project_roles(self, project_id):
        url = "{}/accounts/{}/projects/{}/industry_roles".format(
            HQ_V2_URL, self.account_id, project_id
        )
        headers = {"Content-Type": "application/json"}
        headers.update(self.auth.header)
        data, _ = self.session.request(
            "get",
            url,
            headers=headers,
            message="industry roles for project '{}'".format(project_id),
        )
        return data

    @_validate_token
    def post_project_users(
        self,
        project_id,
        users,
        access_level="user",
        role_id=None,
        x_user_id=None,
        project_name=None,
    ):
        # TODO - Add other services, and company_id
        url = "{}/accounts/{}/projects/{}/users/import".format(
            HQ_V2_URL, self.account_id, project_id
        )
        headers = {"Content-Type": "application/json", "x-user-id": x_user_id}
        headers.update(self.auth.header)

        json_data = []
        for user in users:
            user_data = {
                "email": user["email"],
                "services": {
                    "document_management": {"access_level": access_level}
                },
                "company_id": user["company_id"],
                "industry_roles": [user["default_role_id"] or role_id],
            }

            if access_level == "admin":
                user_data["services"]["project_administration"] = {
                    "access_level": "admin"
                }
            json_data.append(user_data)

        data, success = self.session.request(
            "post",
            url,
            headers=headers,
            json_data=json_data,
            message="users to project: {}".format(project_name or project_id),
        )

        # if success
        if success:
            # users added
            if data.get("success") and data["success"] > 0:
                for item in data["success_items"]:
                    try:
                        email = item.get("email")
                        access_level = item["services"]["document_management"][
                            "access_level"
                        ]
                        self.logger.info(
                            "{}: added {} as a {}".format(
                                project_name or project_id, email, access_level
                            )
                        )
                    except Exception as e:
                        self.logger.debug(
                            "{}: Added user - Code Error: {}".format(
                                project_name or project_id, e
                            )
                        )

            # users not added
            if data.get("failure") and data["failure"] > 0:
                for item in data["failure_items"]:
                    try:
                        email = item.get("email")
                        access_level = item["services"]["document_management"][
                            "access_level"
                        ]
                        error_msg = ", ".join(
                            [error["message"] for error in item["errors"]]
                        )

                        self.logger.debug(
                            "{}: coudn't add {} as a {} because: {}".format(
                                project_name or project_id,
                                email,
                                access_level,
                                error_msg,
                            )
                        )
                    except Exception as e:
                        self.logger.debug(
                            "{}: coudn't add user because: {}".format(
                                project_name or project_id, e
                            )
                        )
        if success:
            return data

    @_validate_token
    def patch_project_user(
        self,
        project_id,
        user,
        company_id=None,
        role_id=None,
        x_user_id=None,
        project_name=None,
    ):

        json_data = {}
        if company_id:
            json_data["company_id"] = company_id
        if role_id:
            json_data["industry_roles"] = [role_id]
        if json_data:
            url = "{}/accounts/{}/projects/{}/users/{}".format(
                HQ_V2_URL, self.account_id, project_id, user["id"]
            )
            headers = {
                "Content-Type": "application/json",
                "x-user-id": x_user_id,
            }
            headers.update(self.auth.header)
            data, success = self.session.request(
                "patch",
                url,
                headers=headers,
                json_data=json_data,
                message="user '{}' in project '{}'".format(
                    user["email"], project_name or project_id
                ),
            )

            if success:
                self.logger.info(
                    "{}: updated {}".format(
                        project_name or project_id, user["email"]
                    )
                )
                return data
