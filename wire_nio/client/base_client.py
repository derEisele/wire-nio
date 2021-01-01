#  Is based of matrix-nio (nio/client/base_client.py)
#  Copyright © 2018, 2019 Damir Jelić <poljar@termina.org.uk>
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

from dataclasses import dataclass
from typing import (
    Optional,
    Union,
    Coroutine,
    Any
)
from functools import wraps
from datetime import datetime

from ..response import (
    BaseResponse,
    LoginResponse,
    ErrorResponse,
    ClientRegisterResponse
)
from ..exceptions import (
    LocalProtocolError
)
from ..crypto.client import CrytoHandler
from ..storage.client import ClientState


def logged_in(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.logged_in:
            raise LocalProtocolError("Not logged in.")
        return func(self, *args, **kwargs)

    return wrapper


@dataclass(frozen=True)
class ClientConfig:
    """Async nio client configuration.

    Attributes:
        max_limit_exceeded (int, optional): How many 429 (Too many requests)
            errors can a request encounter before giving up and returning
            an ErrorResponse.
            Default is None for unlimited.

        max_timeouts (int, optional): How many timeout connection errors can
            a request encounter before giving up and raising the error:
            a ClientConnectionError, TimeoutError, or asyncio.TimeoutError.
            Default is None for unlimited.

        backoff_factor (float): A backoff factor to apply between retries
            for timeouts, starting from the second try.
            nio will sleep for `backoff_factor * (2 ** (total_retries - 1))`
            seconds.
            For example, with the default backoff_factor of 0.1,
            nio will sleep for 0.0, 0.2, 0.4, ... seconds between retries.

        max_timeout_retry_wait_time (float): The maximum time in seconds to
            wait between retries for timeouts, by default 60.

        request_timeout (float): How many seconds a request has to finish,
            before it is retried or raise an `asycio.TimeoutError` depending
            on `max_timeouts`.
            Defaults to 60 seconds, and can be disabled with `0`.
            `AsyncClient.sync()` overrides this option with its
            `timeout` argument.
            The `download()`, `thumbnail()` and `upload()` methods ignore
            this option and use `0`.
    """

    max_limit_exceeded: Optional[int] = None
    max_timeouts: Optional[int] = None
    backoff_factor: float = 0.1
    max_timeout_retry_wait_time: float = 60
    request_timeout: float = 60


class Client:
    def __init__(self, email, config: ClientConfig, crypto_handler: CrytoHandler):
        self.email = email
        self.access_token = ""
        self.client_id = ""
        self.cookie_expire = datetime.now()
        self.cookie = ""
        self.crypto_handler = crypto_handler

    @property
    def logged_in(self):
        return self.access_token != ""

    def receive_response(
            self, response: BaseResponse
    ) -> Optional[Coroutine[Any, Any, None]]:
        """Receive a Matrix Response and change the client state accordingly.

        Some responses will get edited for the callers convenience e.g. sync
        responses that contain encrypted messages. The encrypted messages will
        be replaced by decrypted ones if decryption is possible.

        Args:
            response (Response): the response that we wish the client to handle
        """
        if not isinstance(response, BaseResponse):
            raise ValueError("Invalid response received")
        if isinstance(response, LoginResponse):
            self._handle_login(response)
        elif isinstance(response, ClientRegisterResponse):
            self._handle_register(response)

    def _handle_login(self, response: Union[LoginResponse, ErrorResponse]):
        if isinstance(response, ErrorResponse):
            return

        self.restore_login(
            response.data.access_token,
            response.cookie,
            response.cookie_expire
        )

    def _handle_register(self, response: ClientRegisterResponse):
        self.client_id = response.data.id

    def restore_login(
            self,
            access_token: str,
            cookie: str,
            cookie_expire: datetime
    ):
        """Restore a previous login

        Args:
           access_token (str): Token authorizing the user with the server.
           cookie: The cookie
        """
        self.access_token = access_token
        if cookie and cookie_expire:
            self.cookie = cookie
            self.cookie_expire = cookie_expire

    def export_state(self) -> ClientState:
        return ClientState(
            client_id=self.client_id,
            cookie=self.cookie,
            cookie_expire=self.cookie_expire,
            access_token=self.access_token
        )

    def import_state(self, client_state: ClientState):
        self.access_token = client_state.access_token
        self.client_id = client_state.client_id
        self.cookie = client_state.cookie
        self.cookie_expire = client_state.cookie_expire
