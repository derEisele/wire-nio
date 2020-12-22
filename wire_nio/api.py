"""wire nio api module.

This module contains primitives to build Wire API http requests.

In general these functions are not directly called. One should use an existing
client like AsyncClient or HttpClient.
"""

import json
from enum import Enum, auto
from typing import Dict, Any, List, Tuple, Optional
from urllib.parse import urlencode, quote
from .messages.messages_pb2 import GenericMessage
from .http import Method

WIRE_API_PATH: str = ""



class Api:
    """Wire API class.

    Static methods reflecting the Wire REST API.
    """

    @staticmethod
    def to_json(content_dict: Dict[str, Any]) -> str:
        """Turn a dictionary into a json string."""
        return json.dumps(content_dict, separators=(",", ":"))

    @staticmethod
    def to_canonical_json(content_dict: Dict[str, Any]) -> str:
        """Turn a dictionary into a canonical json string."""
        return json.dumps(
            content_dict,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

    @staticmethod
    def login(email: str, password: str) -> Tuple[Method, str, str]:
        path = Api._build_path(["login"])
        content_dict = {
            "email": email,
            "password": password
        }

        return Method.POST, path, Api.to_json(content_dict)

    @staticmethod
    def send_message(chat_id: str, msg: GenericMessage) -> Tuple[Method, str, str]:
        path = Api._build_path(["conversations", chat_id, "otr", "messages"])

    @staticmethod
    def _build_path(
            path: List[str],
            query_parameters: Dict = None,
            base_path: str = WIRE_API_PATH
    ) -> str:
        """Builds a percent-encoded path from a list of strings.

        For example, turns ["hello", "wo/rld"] into "/hello/wo%2Frld".
        All special characters are percent encoded,
        including the forward slash (/).

        Args:
            path (List[str]): the list of path elements.
            query_parameters (Dict, optional): [description]. Defaults to None.
            base_path (str, optional): A base path to be prepended to path. Defaults to WIRE_API_PATH.

        Returns:
            str: [description]
        """
        quoted_path = ""

        if isinstance(path, str):
            quoted_path = quote(path, safe="")
        elif isinstance(path, List):
            quoted_path='/'.join([quote(str(part), safe="") for part in path])
        else:
            raise AssertionError(f"'path' must be of type List[str] or str, got {type(path)}")

        built_path = "{base}/{path}".format(
            base=base_path,
            path=quoted_path
        )

        built_path = built_path.rstrip("/")

        if query_parameters:
            built_path += "?{}".format(urlencode(query_parameters))

        return built_path

    @staticmethod
    def users(handles: Optional[str] = None, ids: Optional[str] = None):
        query_params = {
            "handles": handles,
            "ids": ids
        }

        path = Api._build_path(["users"], query_params)
        return Method.GET, path
