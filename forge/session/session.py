# -*- coding: utf-8 -*-

"""documentation placeholder"""

from __future__ import absolute_import

import json
import sys

if sys.implementation.name != "ironpython":
    from requests import codes
    from requests import Session as _Session
    from requests.adapters import HTTPAdapter
    from requests.exceptions import ConnectionError, Timeout

    SUCCESS_CODES = (
        codes.ok,
        codes.created,
        codes.accepted,
        codes.partial_content,
    )

else:
    from System.Net import (
        SecurityProtocolType,
        ServicePointManager,
        WebRequest,
    )
    from System.IO import File, StreamReader
    from System.Text.Encoding import UTF8

    ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12

    SUCCESS_CODES = ("OK", "Created", "Accepted", "Partial Content")


from ..utils import Logger  # noqa: E402


class Response(object):
    def __init__(self, response, stream=False, message="", logger=None):
        self.response = response
        self.stream = stream
        self.message = message
        self.logger = logger

    @property
    def data(self):
        if not getattr(self, "_data", None):
            if sys.implementation.name == "ironpython":
                self._data = self.response[0]
            else:  # if sys.implementation.name == "cpython"
                # if response is a json object
                try:
                    self._data = self.response.json()
                # else if raw data
                except json.decoder.JSONDecodeError:
                    self._data = self.response.content
        return self._data

    @property
    def success(self):
        if not getattr(self, "_success", None):
            if sys.implementation.name == "ironpython":
                self._success = self.response[1]
            else:  # if sys.implementation.name == "cpython"
                self._success = self.response.status_code in SUCCESS_CODES

        if not self._success and self.logger:
            self._log_error()

        return self._success

    def _log_error(self):
        if sys.implementation.name == "ironpython":
            error_msg = self.data
        else:  # if sys.implementation.name == "cpython"
            try:
                response_error = (
                    json.loads(self.response.text).get("error")
                    or json.loads(self.response.text).get("errors")
                    or self.response.json().get("message")
                )
            except json.decoder.JSONDecodeError:
                response_error = self.response.text
            if response_error:
                if isinstance(response_error, list):
                    error_msg = ", ".join(
                        [error["detail"] for error in response_error]
                    )
                elif isinstance(response_error, dict):
                    error_msg = response_error.get(
                        "message"
                    ) or response_error.get("type")
                else:
                    error_msg = str(response_error)
            else:
                error_msg = self.response.status_code

        self.logger.debug(
            "Failed to {} - ERROR: {}".format(self.message, error_msg)
        )


class Session(object):
    def __init__(
        self, timeout=5, max_retries=3, base_url=None, log_level="info"
    ):
        """
        Kwargs:
            timeout (``int``, default=2): maximum time for one request in minutes.
            max_retries (``int``, default=3): maximum number of retries.
            base_url (``str``, optional): Base URL for this Session
        """  # noqa:E501
        self.log_level = log_level
        self.logger = Logger.start(__name__)
        self.timeout = int(timeout * 60)  # in secs
        self.success_codes = SUCCESS_CODES

        if sys.implementation.name != "ironpython":
            self.session = _Session()
            self.session.trust_env = False
            if base_url:
                adapter = HTTPAdapter(max_retries=max_retries)
                self.session.mount(base_url, adapter)
        else:
            self.session = None

    @staticmethod
    def _add_url_params(url, params):
        """
        Appends an encoded dict as url parameters to the call API url
        Args:
            url (``str``): uri for API call.
            params (``dict``): dictionary of request uri parameters.
        Returns:
            url (``str``): url with params
        """
        url_params = ""
        count = 0
        for key, value in params.items():
            if count == 0:
                url_params += "?"
            else:
                url_params += "&"
            url_params += key + "="
            url_params += str(params[key])
            count += 1
        return url + url_params

    @staticmethod
    def _url_encode(data):
        """
        Encodes a dict into a url encoded string.
        Args:
            data (``dict``): source data
        Returns:
            urlencode (``str``): url encoded string
        """
        urlencode = ""
        count = len(data)
        for key, value in data.items():
            urlencode += key + "=" + str(value)
            if count != 1:
                urlencode += "&"
            count -= 1
        return urlencode

    @property
    def log_level(self):
        if getattr(self, "_log_level", None):
            return self._log_level

    @log_level.setter
    def log_level(self, log_level):
        """ """
        if not (isinstance(log_level, str)):
            raise TypeError("log_level must be a string")
        # elif log_level not in(x_user_id) == 12:
        #     raise ValueError("x_user_id must be a user UID")
        else:
            self._log_level = log_level
            if getattr(self, "logger", None):
                Logger.set_level(self.logger, log_level)

    def _request_cpython(self, *args, **kwargs):
        method, url = args
        headers = kwargs.get("headers")
        params = kwargs.get("params")
        json_data = kwargs.get("json_data")
        byte_data = kwargs.get("byte_data")
        urlencode = kwargs.get("urlencode")
        filepath = kwargs.get("filepath")
        stream = kwargs.get("stream")

        try:
            if headers:
                self.session.headers = headers

            # get file contents as bytes
            if filepath:
                with open(filepath, "rb") as fp:
                    data = fp.read()
            # else raw bytes
            elif byte_data:
                data = byte_data
            # else urlencode
            elif urlencode:
                data = urlencode
            else:
                data = None

            return self.session.request(
                method.lower(),
                url,
                params=params,
                json=json_data,
                data=data,
                timeout=self.timeout,
                stream=stream,
            )

        except (ConnectionError, Timeout) as e:
            raise e

    def _request_ironpython(self, *args, **kwargs):  # noqa: C901
        method, url = args
        headers = kwargs.get("headers")
        params = kwargs.get("params")
        json_data = kwargs.get("json_data")
        byte_data = kwargs.get("byte_data")
        urlencode = kwargs.get("urlencode")
        filepath = kwargs.get("filepath")

        try:
            # prepare params
            if params:
                url = self._add_url_params(url, params)

            web_request = WebRequest.Create(url)
            web_request.Method = method.upper()
            web_request.Timeout = self.timeout * 1000  # in ms

            # prepare headers
            if headers:
                for key, value in headers.items():
                    if key == "Content-Type":
                        web_request.ContentType = value
                    elif key == "Content-Length":
                        web_request.ContentLength = value
                    else:
                        web_request.Headers.Add(key, value)

            byte_arrays = []
            if json_data:
                byte_arrays.append(
                    UTF8.GetBytes(json.dumps(json_data, ensure_ascii=False))
                )
            if filepath:
                byte_arrays.append(File.ReadAllBytes(filepath))
            if byte_data:
                pass
                # TODO - Add byte input for System.Net
            if urlencode:
                byte_arrays.append(UTF8.GetBytes(self._url_encode(urlencode)))

            for byte_array in byte_arrays:
                web_request.ContentLength = byte_array.Length
                with web_request.GetRequestStream() as req_stream:
                    req_stream.Write(byte_array, 0, byte_array.Length)
            try:
                with web_request.GetResponse() as response:
                    content_type = response.Headers.Get("Content-Type")
                    success = response.StatusDescription in SUCCESS_CODES
                    with response.GetResponseStream() as response_stream:
                        with StreamReader(response_stream) as stream_reader:
                            raw = stream_reader.ReadToEnd()
                        try:
                            data = json.loads(raw)
                        except json.decoder.JSONDecodeError:
                            print(content_type)
                            data = raw
                        except Exception as e:
                            raise (e)
            except SystemError as e:
                return e, False
            finally:
                web_request.Abort()

        except Exception as e:
            raise e

        return data, success

    def request(
        self,
        method,
        url,
        headers=None,
        params=None,
        json_data=None,
        byte_data=None,
        urlencode=None,
        filepath=None,
        stream=False,
        message="",
    ):
        """
        Request wrapper for cpython and ironpython.
        Args:
            method (``str``): api method.
            url (``str``): uri for API call.
        Kwargs:
            headers (``dict``, optional): dictionary of request headers.
            params (``dict``, optional): dictionary of request uri parameters.
            json_data (``json``, optional): request body if Content-Type is json.
            urlencode (``dict``, optional): request body if Content-Type is urlencoded.
            filepath (``str``, optional): filepath of object to upload.
            stream (``bool``, default=False) whether to sream content of not
            message (``str``, optional): filepath of object to upload.

        Returns:
            data (``json``): Body of response.
            success (``bool``): True if response returned a accepted, created or ok status code.
        """  # noqa: E501

        if sys.implementation.name == "ironpython":
            _request = self._request_ironpython
        else:  # if sys.implementation.name == "cpython"
            _request = self._request_cpython

        req = _request(
            method,
            url,
            headers=headers,
            params=params,
            json_data=json_data,
            byte_data=byte_data,
            urlencode=urlencode,
            filepath=filepath,
            stream=stream,
        )
        res = Response(
            req,
            message=message,
            logger=self.logger,
        )
        return res.data, res.success


if __name__ == "__main__":
    pass
