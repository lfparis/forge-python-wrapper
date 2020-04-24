# -*- coding: utf-8 -*-

"""documentation placeholder"""

from __future__ import absolute_import

import asyncio
import time

from aiohttp import ContentTypeError
from json.decoder import JSONDecodeError

from ..base import ForgeBase, Logger
from ..decorators import _get_session
from ..urls import HQ_V1_URL, HQ_V2_URL

logger = Logger.start(__name__)


class AHQ(ForgeBase):
    def __init__(
        self, *args, auth=None, log_level=None, retries=5, **kwargs,
    ):
        self.auth = auth
        self.logger = logger
        self.log_level = log_level
        self.retries = retries

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
        except (ContentTypeError, JSONDecodeError):
            return await res.text(encoding="utf-8")

    # Pagination Methods

    async def _get_page(
        self, url, page_number, page_size, responses, headers=None, params={},
    ):
        params["offset"] = page_number * page_size
        res = await self._request(
            method="GET", url=url, headers=headers, params=params
        )
        # res.raise_for_status()
        await responses.put((res, page_number))

    async def _get_page_data(self, responses, page_size, done, results):
        res, page_number = await responses.get()

        page_results = await self._get_data(res)

        if (page_number != 0 and len(page_results) < page_size) and (
            not getattr(done, "last_page", None)
            or page_number < done.last_page
        ):
            done.last_page = page_number
        elif page_number == 0 and len(page_results) < page_size:
            done.set()

        results.extend(page_results)

        if (
            getattr(done, "last_page", None)
            and len(results) >= done.last_page * page_size
        ):
            done.set()

        responses.task_done()

    @_get_session
    async def _get_iter(self, url, name, headers=None, params={}):
        responses = asyncio.Queue()
        done = asyncio.Event()

        page_size = 100
        params["limit"] = page_size
        results = []

        tasks = []
        page_number = 0
        while True:
            tasks.append(
                asyncio.create_task(
                    self._get_page(
                        url,
                        page_number,
                        page_size,
                        responses,
                        headers=headers,
                        params=params,
                    )
                )
            )
            tasks.append(
                asyncio.create_task(
                    self._get_page_data(responses, page_size, done, results)
                )
            )
            await asyncio.sleep(0.06)
            page_number += 1
            if done.is_set():
                break

        for t in tasks:
            t.cancel()

        if results:
            if isinstance(results[0], dict):
                self.logger.info(
                    "Fetched {} {} from Autodesk BIM 360".format(
                        len(results), name
                    )
                )
            else:
                self.logger.warning(
                    "No {} fetched from Autodesk BIM 360".format(name)
                )
        return results

    # HQ V1

    async def get_users(self):
        url = "{}/accounts/{}/users".format(HQ_V1_URL, self.account_id)
        return await self._get_iter(url, "users", headers=self.auth.header)

    async def get_users_search(
        self,
        name=None,
        email=None,
        company_name=None,
        partial=1,  # aiohttp does not take booleans as param values
        limit=None,
        sort=None,
        field=None,
    ):
        """
        https://forge.autodesk.com/en/docs/bim360/v1/reference/http/users-search-GET/
        """  # noqa: E501
        params = {k: v for k, v in locals().items() if v and k != "self"}
        url = "{}/accounts/{}/users/search".format(HQ_V1_URL, self.account_id)
        return await self._get_iter(
            url, "users", headers=self.auth.header, params=params
        )

    @_get_session
    async def get_user(self, user_id):
        url = "{}/accounts/{}/users/{}".format(
            HQ_V1_URL, self.account_id, user_id
        )
        res = await self._request(
            method="GET", url=url, headers=self.auth.header
        )
        return await self._get_data(res)

    async def get_projects(self):
        url = "{}/accounts/{}/projects".format(HQ_V1_URL, self.account_id)
        return await self._get_iter(url, "projects", headers=self.auth.header)

    @_get_session
    async def get_project(self, project_id):
        url = "{}/accounts/{}/projects/{}".format(
            HQ_V1_URL, self.account_id, project_id
        )
        res = await self._request(
            method="GET", url=url, headers=self.auth.header
        )
        return await self._get_data(res)

    async def get_companies(self):
        url = "{}/accounts/{}/companies".format(HQ_V1_URL, self.account_id)
        return await self._get_iter(url, "companies", headers=self.auth.header)

    @_get_session
    async def post_project(
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
                # aiohttp does not take booleans as param values
                json_data["template_project_id"] = template["id"]
                json_data["include_locations"] = 1
                json_data["include_companies"] = 1
            except KeyError:
                pass

        res = await self._request(
            method="POST", url=url, headers=headers, json=json_data,
        )
        data = await self._get_data(res)

        if res.status >= 200 and res.status < 300:
            self.logger.info("Added: {}".format(name))
            return data
        else:
            self.logger.debug(f"Failed to add '{name}': {data.get('message')}")

    @_get_session
    async def patch_project(
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

            res = await self._request(
                method="PATCH", url=url, headers=headers, json=json_data,
            )
            data = await self._get_data(res)

            if res.status >= 200 and res.status < 300:
                self.logger.info(
                    f"Updated '{project_name or project_id}' {key} to {json_data[key]}"  # noqa: E501
                )
            else:
                self.logger.debug(
                    f"Failed to update {key} of '{project_name or project_id}': {data.get('message')}"  # noqa: E501
                )

            return data

    # HQ V2

    @_get_session
    async def get_project_roles(self, project_id):
        url = "{}/accounts/{}/projects/{}/industry_roles".format(
            HQ_V2_URL, self.account_id, project_id
        )
        headers = {"Content-Type": "application/json"}
        headers.update(self.auth.header)

        res = await self._request(
            method="GET", url=url, headers=self.auth.header
        )
        data = await self._get_data(res)

        # if success
        if res.status >= 200 and res.status < 300:
            self.logger.info(
                f"Fetched industry roles for project: '{project_id}'"
            )
        else:
            self.logger.debug(
                f"Failed to get industry roles for project '{project_id}': {data.get('message')}"  # noqa: E501
            )

        return data

    @_get_session
    async def post_project_users(
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

        res = await self._request(
            method="POST", url=url, headers=headers, json=json_data,
        )
        data = await self._get_data(res)

        # if success
        if res.status >= 200 and res.status < 300:
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
            return data

    @_get_session
    async def patch_project_user(
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
            key = list(json_data.keys())[0]

            res = await self._request(
                method="PATCH", url=url, headers=headers, json=json_data,
            )
            data = await self._get_data(res)

            if res.status >= 200 and res.status < 300:
                self.logger.info(
                    f"Updated '{user['email']}' {key} to {json_data[key]} in '{project_name or project_id}'"  # noqa: E501
                )
            else:
                self.logger.debug(
                    f"Failed to update '{user['email']}' {key} to {json_data[key]} in '{project_name or project_id}': {data.get('message')}"  # noqa: E501
                )

            return data
