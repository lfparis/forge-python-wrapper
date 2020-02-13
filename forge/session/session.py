from __future__ import absolute_import

import json

try:
    import requests
except AttributeError:
    raise AttributeError(
        "Stack frames are disabled, please enable stack frames.\
        If in pyRevit, place the following at the top of your file: \
        '__fullframeengine__ = True' and reload pyRevit."
    )

try:
    from System.Net import (
        SecurityProtocolType,
        ServicePointManager,
        WebRequest,
    )
    from System.IO import File, IOException, StreamReader
    from System.Text.Encoding import UTF8

    ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12
except ImportError:
    IOException = Exception


from ..utils import Logger  # noqa: E402

logger = Logger(__name__)()


class Session(object):
    def __init__(self):
        pass

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

    @staticmethod
    def _log_error(method, message, response):
        response_error = (
            json.loads(response.text).get("error")
            or json.loads(response.text).get("errors")
            or response.json().get("message")
        )
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
            error_msg = response.status_code

        logger.warning(
            "Failed to {} {}: {}".format(method, message, error_msg)
        )

    def request(  # noqa
        self,
        method,
        url,
        headers=None,
        params=None,
        json_data=None,
        byte_data=None,
        urlencode=None,
        filepath=None,
        timeout=2,
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
            timeout (``int``, optional): maximum time for one request in minutes.
            message (``str``, optional): filepath of object to upload.
        Returns:
            data (``json``): Body of response.
            success (``bool``): True if response returned a accepted, created or ok status code.
        """  # noqa
        # try requests lib
        try:
            s = requests.Session()

            # update headers
            if headers:
                s.headers.update(headers)

            # get file contents as bytes
            if filepath:
                with open(filepath, "rb") as handle:
                    data = handle.read()
            elif byte_data:
                data = byte_data
            elif urlencode:
                data = urlencode
            else:
                data = None

            r = s.request(
                method.lower(), url, params=params, json=json_data, data=data
            )

            # if response is a json object
            try:
                data = r.json()

            # else if raw data
            except json.decoder.JSONDecodeError:
                data = r.content

            success = r.status_code in (
                requests.codes.ok,
                requests.codes.created,
                requests.codes.accepted,
            )
            if not success:
                self._log_error(method, message, r)

        # else use System.Net
        except (IOException, UnicodeDecodeError):
            # prepare params
            if params:
                url = self._add_url_params(url, params)

            web_request = WebRequest.Create(url)
            web_request.Method = method.upper()
            web_request.Timeout = timeout * 60 * 1000

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
                    success = response.StatusDescription in (
                        "OK",
                        "Created",
                        "Accepted",
                    )

                    # if not success:
                    #     self._log_error(method, message, response)

                    with response.GetResponseStream() as response_stream:
                        with StreamReader(response_stream) as stream_reader:
                            data = json.loads(stream_reader.ReadToEnd())
            except SystemError:
                return None, None
            finally:
                web_request.Abort()
        return data, success


if __name__ == "__main__":
    pass
