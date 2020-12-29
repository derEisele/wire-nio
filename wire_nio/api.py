"""wire nio api module.

This module contains primitives to build Wire API http requests.

In general these functions are not directly called. One should use an existing
client like AsyncClient or HttpClient.
"""

from typing import Dict, Any, List, Tuple, Optional
from urllib.parse import urlencode, quote
from datetime import datetime
from base64 import b64encode

from cryptobox.cbox import PreKey

from .messages.messages_pb2 import GenericMessage
from .http import Method
from .models import LoginRequest, ClientRegisterRequest, Key, SigKey

WIRE_API_PATH: str = ""


class Api:
    """Wire API class.

    Static methods reflecting the Wire REST API.
    """

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
            quoted_path = '/'.join([quote(str(part), safe="") for part in path])
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
    def login(email: str, password: str, persist: bool = False) -> Tuple[Method, str, str]:
        path = Api._build_path(["login"], {"persist": persist})
        content = LoginRequest(email=email, password=password)

        return Method.POST, path, content.json()

    @staticmethod
    def users(handles: Optional[str] = None, ids: Optional[str] = None):
        query_params = {
            "handles": handles,
            "ids": ids
        }

        path = Api._build_path(["users"], query_params)
        return Method.GET, path

    @staticmethod
    def conversations(size: Optional[int] = None, start: Optional[int] = None, ids: List[str] = None):
        if ids is None:
            ids = []

        query_params = {}
        if size:
            query_params["size"] = size
        if start:
            query_params["start"] = start

        path = Api._build_path(["conversations"], query_params)
        return Method.GET, path

    @staticmethod
    def clients():
        return Method.GET, Api._build_path(["clients"])

    @staticmethod
    def notifications(client: Optional[str] = None, since: Optional[datetime] = None):
        query_params = {}
        if client:
            query_params["client"] = client
        if since:
            query_params["since"] = since.isoformat()
        else:
            query_params["since"] = datetime.fromtimestamp(0).isoformat()

        path = Api._build_path(["notifications"], query_params)

        return Method.GET, path

    @staticmethod
    def register_client(password: str, last_prekey: PreKey, prekeys: List[PreKey], cookie: str, persistent=False, class_="desktop", label="wire-nio"):
        path = Api._build_path(["clients"])
        sigkey = SigKey(
            enckey=b64encode(32 * b"\x00"),
            mackey=b64encode(32 * b"\x00")
        )

        last_prekey_dto = Key(
            id=last_prekey.id,
            key=b64encode(last_prekey.data)
        )

        prekeys_dto = [Key(id=pk.id, key=b64encode(pk.data))
                       for pk in prekeys]

        content = ClientRegisterRequest(
            cookie=cookie,
            lastkey=last_prekey_dto,
            sigkeys=sigkey,
            password=password,
            prekeys=prekeys_dto,
            type="permanent" if persistent else "temporary",
            class_=class_,
            label=label
        )

        return Method.POST, path, content.json()
