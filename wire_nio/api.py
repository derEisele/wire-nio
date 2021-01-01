#  Is based of matrix-nio (nio/api.py)
#  Copyright © 2018 Damir Jelić <poljar@termina.org.uk>
#  Copyright © 2020 Famedly GmbH
#
#  Permission to use, copy, modify, and/or distribute this software for
#  any purpose with or without fee is hereby granted, provided that the
#  above copyright notice and this permission notice appear in all copies.
#
#  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#  WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#  MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
#  SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER
#  RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF
#  CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
#  CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

#  Copyright (c) 2021. Alexander Eisele <alexander@eiselecloud.de>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""wire nio api module.

This module contains primitives to build Wire API http requests.

In general these functions are not directly called. One should use an existing
client like AsyncClient or HttpClient.
"""

from typing import Dict, Iterable, List, Tuple, Optional
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
    def refresh_session():
        path = Api._build_path(["access"])
        return Method.POST, path

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
    def conversation(conv_id: str):
        path = Api._build_path(["conversations", conv_id])
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
    def register_client(password: str, last_prekey: PreKey, prekeys: Iterable[PreKey], cookie: str, persistent=False, class_="desktop", label="wire-nio"):
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

    @staticmethod
    def client_ids_from_user(user_id: str):
        path = Api._build_path(["users", user_id, "clients"])
        return Method.GET, path

    @staticmethod
    def pre_keys_for_client(user_id: str, client_id: str):
        path = Api._build_path(["users", user_id, "prekeys", client_id])
        return Method.GET, path

    @staticmethod
    def pre_keys_for_user(user_id: str):
        path = Api._build_path(["users", user_id, "prekeys"])
        return Method.GET, path
