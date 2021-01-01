#  Is based of matrix-nio (nio/client/async_client.py)
#  Copyright © 2018, 2019 Damir Jelić <poljar@termina.org.uk>
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
#
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

from typing import (
    Type,
    Union,
    Optional,
    Tuple,
    Any,
    Dict,
    Callable,
    List
)
from functools import wraps, partial
from dataclasses import dataclass, field
from asyncio import Event as AsyncioEvent
from asyncio import TimeoutError as AsyncioTimeoutError
from asyncio import sleep, gather, ensure_future
import warnings
from datetime import datetime

from aiohttp import (
    ClientResponse,
    ClientSession,
    ClientTimeout,
    TraceConfig,
)
from aiohttp.client_exceptions import ClientConnectionError
from aiohttp.connector import Connection

from pprint import pprint
from cryptobox.cbox import PreKey
from base64 import b64decode, b64encode

from . import Client, ClientConfig
from .base_client import logged_in
from ..api import (
    Api
)

from .. import response
from ..crypto.client import CrytoHandler

from ..__version__ import __version__

USER_AGENT = f"wire-nio/{__version__}"
# USER_AGENT = "foo"

@dataclass
class ResponseCb:
    """Response callback."""

    func: Callable = field()
    filter: Union[Tuple[Type], Type, None] = None


async def connect_wrapper(self, *args, **kwargs) -> Connection:
    connection = await type(self).connect(self, *args, **kwargs)
    connection.transport.set_write_buffer_limits(16 * 1024)
    return connection


def client_session(func):
    """Ensure that the Async client has a valid client session."""

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.client_session:
            trace = TraceConfig()

            self.client_session = ClientSession(
                timeout=ClientTimeout(total=self.config.request_timeout),
                trace_configs=[trace],
            )

            self.client_session.connector.connect = partial(
                connect_wrapper, self.client_session.connector,
            )

        return await func(self, *args, **kwargs)

    return wrapper


class AsyncClientConfig(ClientConfig):
    pass


class AsyncClient(Client):
    def __init__(
            self,
            email: str = "",
            config: Optional[AsyncClientConfig] = None,
            proxy: Optional[str] = None,
            crypto_handler: Optional[CrytoHandler] = None
    ):
        self.client_session: Optional[ClientSession] = None
        self.server = "https://prod-nginz-https.wire.com"
        self.ssl = True

        self.proxy = proxy

        self._presence: Optional[str] = None

        self.synced = AsyncioEvent()
        self.response_callbacks: List[ResponseCb] = []

        self.sharing_session: Dict[str, AsyncioEvent] = dict()

        is_config = isinstance(config, ClientConfig)
        is_async_config = isinstance(config, AsyncClientConfig)

        if is_config and not is_async_config:
            warnings.warn(
                "Pass an AsyncClientConfig instead of ClientConfig.",
                DeprecationWarning,
            )
            config = AsyncClientConfig(**config.__dict__)

        self.config: AsyncClientConfig = config or AsyncClientConfig()

        if not crypto_handler:
            crypto_handler = CrytoHandler()

        super().__init__(email, self.config, crypto_handler)

    @client_session
    async def send(
            self,
            method: str,
            path: str,
            data: Optional[str] = None,
            headers: Optional[Dict[str, str]] = None,
            timeout: Optional[float] = None,
    ) -> ClientResponse:
        """Send a request.

        This function does not call receive_response().

        Args:
            method (str): The request method that should be used. One of get,
                post, put, delete.
            path (str): The URL path of the request.
            data (str, optional): Data that will be posted with the request.
            headers (Dict[str,str] , optional): Additional request headers that
                should be used with the request.
            timeout (int, optional): How many seconds the request has before
                raising `asyncio.TimeoutError`.
                Overrides `AsyncClient.config.request_timeout` if not `None`.
        """
        assert self.client_session

        return await self.client_session.request(
            method,
            self.server + path,
            data=data,
            ssl=self.ssl,
            proxy=self.proxy,
            headers=headers,
            timeout=self.config.request_timeout if timeout is None else timeout
            )

    async def api_send(
            self,
            response_class: Type[response.BaseResponse],
            method: str,
            path: str,
            data: Union[None, str] = None,
            response_data: Optional[Tuple[Any, ...]] = None,
            content_type: Optional[str] = None,
            timeout: Optional[float] = None,
            content_length: Optional[int] = None,
    ):
        headers = {
            "Content-Type": content_type if content_type else "application/json",
            "Accept": "*/*",
            "User-Agent": USER_AGENT
        }

        if not isinstance(response_class, response.LoginResponse):
            headers["Authorization"] = f"Bearer {self.access_token}"

        if self.cookie:
            headers["Cookie"] = f"zuid={self.cookie}"

        if content_length is not None:
            headers["Content-Length"] = str(content_length)

        got_429 = 0
        max_429 = self.config.max_limit_exceeded

        got_timeouts = 0
        max_timeouts = self.config.max_timeouts

        while True:
            try:
                transport_resp = await self.send(
                    method, path, data, headers, timeout,
                )

                resp = await self.parse_wire_response(
                    response_class, transport_resp, response_data,
                )

                if (
                        transport_resp.status == 429 or
                        isinstance(resp, response.ErrorResponse)
                ):
                    got_429 += 1

                    if max_429 is not None and got_429 > max_429:
                        break

                    retry_after_ms = getattr(resp, "retry_after_ms", 0) or 5000
                    await sleep(retry_after_ms / 1000)
                else:
                    break

            except (ClientConnectionError, TimeoutError, AsyncioTimeoutError):
                got_timeouts += 1

                if max_timeouts is not None and got_timeouts > max_timeouts:
                    raise

                wait = 5
                await sleep(wait)

        await self.receive_response(resp)
        return resp

    async def receive_response(self, resp: response.BaseResponse) -> None:
        """Receive a Matrix Response and change the client state accordingly.

        Automatically called for all "high-level" methods of this API (each
        function documents calling it).

        Some responses will get edited for the callers convenience e.g. sync
        responses that contain encrypted messages. The encrypted messages will
        be replaced by decrypted ones if decryption is possible.

        Args:
            resp (Response): the response that we wish the client to handle
        """
        if not isinstance(resp, response.BaseResponse):
            raise ValueError("Invalid response received")

        # if isinstance(response, SyncResponse):
        #     await self._handle_sync(response)
        # else:
        super().receive_response(resp)

    @staticmethod
    async def parse_wire_response(
            response_class: Type[response.BaseResponse],
            transport_response: ClientResponse,
            data: Tuple[Any, ...] = None,
    ) -> response.BaseResponse:
        """Transform a transport response into a nio matrix response.

        Low-level function which is normally only used by other methods of
        this class.

        Args:
            response_class (Type): The class that the requests belongs to.
            transport_response (ClientResponse): The underlying transport
                response that contains our response body.
            data (Tuple, optional): Extra data that is required to instantiate
                the response class.

        Returns a subclass of `Response` depending on the type of the
        response_class argument.
        """
        data = data or ()

        content_type = transport_response.content_type
        content = await transport_response.json()
        pprint(content)
        is_json = content_type == "application/json"

        resp = response_class()
        resp.parse_data(content)

        if isinstance(resp, response.LoginResponse):
            c = transport_response.cookies.get("zuid")
            if c:
                resp.cookie = c.value
                resp.cookie_expire = datetime.strptime(c.get("expires"), "%a, %d-%b-%Y %H:%M:%S %Z")

        return resp

    async def login(self, password: str, persist: bool = False) -> response.LoginResponse:
        method, path, data = Api.login(self.email, password, persist)
        return await self.api_send(response.LoginResponse, method.name, path, data)

    @logged_in
    async def refresh_session(self):
        method, path = Api.refresh_session()
        return await self.api_send(response.LoginResponse, method.name, path)

    @logged_in
    async def users(self, handles: Optional[str] = None, ids: Optional[str] = None) -> response.UsersResponse:
        method, path = Api.users(handles, ids)
        return await self.api_send(response.UsersResponse, method.name, path)

    @logged_in
    async def conversations(self, start: Optional[int] = None, size: Optional[int] = None) -> response.ConversationsResponse:
        method, path = Api.conversations(size=size, start=start)
        return await self.api_send(response.ConversationsResponse, method.name, path)

    @logged_in
    async def conversation(self, conv_id: str) -> response.ConversationResponse:
        method, path = Api.conversation(conv_id)
        return await self.api_send(response.ConversationResponse, method.name, path)

    @logged_in
    async def clients(self) -> response.ClientsResponse:
        method, path = Api.clients()
        return await self.api_send(response.ClientsResponse, method.name, path)

    @logged_in
    async def notifications(self, since: datetime) -> response.NotificationsResponse:
        method, path = Api.notifications(self.client_id, since)
        return await self.api_send(response.NotificationsResponse, method.name, path)

    @logged_in
    async def register_client(self, password: str, persistent=True, label="wire-nio") -> response.ClientRegisterResponse:
        cookie = self.cookie
        self.crypto_handler.generate_prekeys()
        last_prekey = self.crypto_handler.last_prekey
        prekeys = self.crypto_handler.prekeys.values()

        method, path, content = Api.register_client(password, last_prekey, prekeys, cookie, persistent=persistent, label=label)
        return await self.api_send(response.ClientRegisterResponse, method.name, path, content)

    @logged_in
    async def client_ids_from_user(self, user_id: str):
        method, path = Api.client_ids_from_user(user_id)
        return await self.api_send(response.ClientIdsFromUserResponse, method.name, path)

    @logged_in
    async def pre_keys_for_client(self, user_id: str, client_id: str):
        method, path = Api.pre_keys_for_client(user_id, client_id)
        return await self.api_send(response.PreKeyResponse, method.name, path)

    @logged_in
    async def pre_keys_for_user(self, user_id):
        method, path = Api.pre_keys_for_user(user_id)
        return await self.api_send(response.UserPreKeysResponse, method.name, path)

    @logged_in
    async def _encrypt_for_conv(self, conv_id: str, message: bytes):
        conf: response.ConversationResponse = await self.conversation(conv_id)
        key_requests = []

        for other in conf.data.members.others:
            task = ensure_future(self.pre_keys_for_user(other.id))
            key_requests.append(task)

        res = await gather(*key_requests)
        pprint(res)
        enc_dict = {}

        for r in res:
            user_id = r.data.user
            enc_dict[user_id] = {}
            for c in r.data.clients:
                client_id = c.client
                pk = PreKey(
                    id=c.prekey.id,
                    data=b64decode(c.prekey.key)
                )
                cipher = self.crypto_handler.encrypt_message(
                    user_id=user_id,
                    client_id=client_id,
                    pre_key=pk,
                    text=message
                )
                enc_dict[user_id][client_id] = b64encode(cipher)

        return enc_dict

