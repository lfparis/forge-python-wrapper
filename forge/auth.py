# -*- coding: utf-8 -*-

"""documentation placeholder"""

from __future__ import absolute_import

import chromedriver_autoinstaller
import os
import sys

from datetime import datetime
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

from .base import ForgeBase, Logger
from .urls import AUTH_V1_URL

logger = Logger.start(__name__)


class ForgeAuth(ForgeBase):
    def __init__(
        self,
        client_id=None,
        client_secret=None,
        scopes=None,
        three_legged=False,
        grant_type="implicit",
        redirect_uri=None,
        username=None,
        password=None,
        log_level="info",
    ):
        """
        This class wraps methods found in the Authentication (OAuth) API
        https://forge.autodesk.com/en/docs/oauth/v2/reference/http/

        In a two-legged context you must provide:

        Kwargs:
            client_id (``string``, default=None): Client ID of the app. If not provided, it will attempt to look for the 'FORGE_CLIENT_ID' environment variable.
            client_secret (``string``, default=None): Client secret of the app. If not provided, it will attempt to look for the 'FORGE_CLIENT_SECRET' environment variable.
            scopes (``list``, default=["account:read", "account:write", "data:read", "data:write", "data:create", "bucket:read", "bucket:create"]): List of required scopes as ``strings``.
            three_legged (``bool``, default=False): (Not needed for 2-Legged Context) If True it will attempt to get a 3-Legged Token; if False it will attempt to get a 2-Legged Token.
            grant_type (``string``, default="implicit"): (Not needed for 2-Legged Context) Grant type for 3-Legged Token. Either "implicit" of "authorization_code".
            redirect_uri (``string``, default=None): (Not needed for 2-Legged Context) URL-encoded callback URL which must match the pattern of the callback URL field of the app's registration. If not provided, it will attempt to look for the 'FORGE_REDIRECT_URI' environment variable.
            username (``string``, default=None): (Not needed for 2-Legged Context) Email or Username credential to an Autodesk Account. If not provided, it will attempt to look for the 'FORGE_USERNAME' environment variable.
            password (``string``, default=None): (Not needed for 2-Legged Context) Password credential to an Autodesk Account. If not provided, it will attempt to look for the 'FORGE_PASSWORD' environment variable.
            log_level (``string``, default="info"): Logging level.
        """  # noqa:E501
        self.timestamp = datetime.now()
        self.logger = logger
        Logger.set_level(self.logger, log_level)
        self.client_id = client_id or os.environ.get("FORGE_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get(
            "FORGE_CLIENT_SECRET"
        )
        self.scopes = scopes or [
            "account:read",
            "account:write",
            "data:read",
            "data:write",
            "data:create",
            "bucket:read",
            "bucket:create",
        ]
        self.grant_type = grant_type
        self.redirect_uri = redirect_uri or os.environ.get(
            "FORGE_REDIRECT_URI"
        )
        self.username = username or os.environ.get("FORGE_USERNAME")
        self.password = password or os.environ.get("FORGE_PASSWORD")
        if not self.client_id or not self.client_secret:
            raise AttributeError(
                "Client ID and/or Client Secret not found. "
                + "Pass them as kwargs or set environment variables: "
                + "'FORGE_CLIENT_ID' and 'FORGE_CLIENT_SECRET'"
            )

        self.three_legged = three_legged
        if self.three_legged:
            if self.redirect_uri and self.username and self.password:
                self._get_auth3()
            else:
                raise AttributeError(
                    "Three-legged Authentication requires a valid "
                    + "redirect_uri, username, and password"
                )
        else:
            self._get_auth2()

    # API Endpoints
    # Two-Legged Context

    def _authenticate(self):
        """https://forge.autodesk.com/en/docs/oauth/v2/reference/http/authenticate-POST/"""  # noqa:E501
        url = "{}/authenticate".format(AUTH_V1_URL)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": " ".join(self.scopes),
        }

        self._get_auth(url, headers, params)

    # Three-Legged Context

    def _authorize(self, response_type="token"):
        """https://forge.autodesk.com/en/docs/oauth/v2/reference/http/authorize-GET/"""  # noqa:E501
        url = "{}/authorize".format(AUTH_V1_URL)
        params = {
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "scope": " ".join(self.scopes),
            "response_type": response_type,
        }
        url = self._compose_url(url, params)

        chrome_driver_path = os.environ.get("CHROMEDRIVER_PATH")

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

        google_chrome_path = os.environ.get("GOOGLE_CHROME_BIN")
        if google_chrome_path:
            chrome_options.binary_location = google_chrome_path

        try:
            driver = Chrome(
                executable_path=chrome_driver_path,
                chrome_options=chrome_options,
            )
        except (TypeError, WebDriverException):
            chrome_driver_path = chromedriver_autoinstaller.install()
            driver = Chrome(
                executable_path=chrome_driver_path,
                chrome_options=chrome_options,
            )

        try:
            driver.implicitly_wait(15)
            driver.get(url)

            user_name = driver.find_element(by=By.ID, value="userName")
            user_name.send_keys(self.username)
            verify_user_btn = driver.find_element(
                by=By.ID, value="verify_user_btn"
            )
            verify_user_btn.click()

            pwd = driver.find_element(by=By.ID, value="password")
            pwd.send_keys(self.password)
            submit_btn = driver.find_element(by=By.ID, value="btnSubmit")
            submit_btn.click()

            allow_btn = driver.find_element(by=By.ID, value="allow_btn")
            allow_btn.click()

            return_url = driver.current_url
            driver.quit()

        except Exception as e:
            self.logger.error(
                "Please provide the correct user information."
                + "\n\nException: {}".format(e)
            )
            "chrome://settings/help"
            "https://chromedriver.chromium.org/downloads"
            sys.exit()

        params = self._decompose_url(return_url)
        self.__dict__.update(params)

    def _get_token(self):
        """https://forge.autodesk.com/en/docs/oauth/v2/reference/http/gettoken-POST/"""  # noqa:E501
        url = "{}/gettoken".format(AUTH_V1_URL)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": self.code,
            "redirect_uri": self.redirect_uri,
        }

        self._get_auth(url, headers, params)

    def _refresh_token(self):
        """https://forge.autodesk.com/en/docs/oauth/v2/reference/http/refreshtoken-POST/"""  # noqa:E501
        url = "{}/refreshtoken".format(AUTH_V1_URL)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "scope": " ".join(self.scopes),
        }
        self._get_auth(url, headers, params)

    # Private Methods

    def _set_auth_header(self):
        try:
            self.header = {
                "Authorization": "{} {}".format(
                    self.token_type, self.access_token
                )
            }
            self.logger.info("Authorized Forge App")
        except Exception:
            raise AttributeError("Failed to get Bearer Token")

    def _get_auth(self, url, headers, params):
        data, success = self.session.request(
            "post", url, headers=headers, urlencode=params
        )
        self.__dict__.update(data)
        self._set_auth_header()

    def _get_auth2(self):
        """https://forge.autodesk.com/en/docs/oauth/v2/tutorials/get-2-legged-token/"""  # noqa:E501
        self._authenticate()

    def _get_auth3(self):
        """
        Authorization Code Grant:
        https://forge.autodesk.com/en/docs/oauth/v2/tutorials/get-3-legged-token/

        Implicit Grant:
        https://forge.autodesk.com/en/docs/oauth/v2/tutorials/get-3-legged-token-implicit/
        """  # noqa:E501
        if self.grant_type == "implicit":
            self._authorize()
            self.refresh_token = None
            self._set_auth_header()

        elif self.grant_type == "authorization_code":
            self._authorize(response_type="code")
            self._get_token()

    # Public Methods

    def refresh(self):
        """Refresh Token"""
        if self.three_legged:
            if self.refresh_token:
                self._refresh_token()
            else:
                self._get_auth3()
        else:
            self._get_auth2()
