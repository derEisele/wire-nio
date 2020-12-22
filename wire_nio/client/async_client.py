import json
from json.decoder import JSONDecodeError
from typing import (
    Type,
    Union,
    Optional,
    Tuple,
    Any,
    Dict,
    Callable, List
)
from functools import wraps, partial
from dataclasses import dataclass, field
from asyncio import Event as AsyncioEvent
from asyncio import TimeoutError as AsyncioTimeoutError
from asyncio import sleep
import warnings

from aiohttp import (
    ClientResponse,
    ClientSession,
    ClientTimeout,
    ContentTypeError,
    TraceConfig,
)
from aiohttp.client_exceptions import ClientConnectionError
from aiohttp.connector import Connection

from . import Client, ClientConfig
from .async_attachements import AsyncDataT
from .base_client import logged_in
from ..api import (
    Api
)
from ..monitors import TransferMonitor
from ..responses import (
    Response,
    LoginResponse,
    ErrorResponse,
    UsersResponse
)
from ..__version__ import __version__

USER_AGENT = f"wire-nio/{__version__}"


@dataclass
class ResponseCb:
    """Response callback."""

    func: Callable = field()
    filter: Union[Tuple[Type], Type, None] = None


async def on_request_chunk_sent(session, context, params):
    """TraceConfig callback to run when a chunk is sent for client uploads."""

    context_obj = context.trace_request_ctx

    if isinstance(context_obj, TransferMonitor):
        context_obj.transferred += len(params.chunk)


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
            trace.on_request_chunk_sent.append(on_request_chunk_sent)

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

        super().__init__(email, self.config)

    @client_session
    async def send(
            self,
            method: str,
            path: str,
            data: Union[None, str, AsyncDataT] = None,
            headers: Optional[Dict[str, str]] = None,
            trace_context: Any = None,
            timeout: Optional[float] = None,
    ) -> ClientResponse:
        """Send a request to the homeserver.

        This function does not call receive_response().

        Args:
            method (str): The request method that should be used. One of get,
                post, put, delete.
            path (str): The URL path of the request.
            data (str, optional): Data that will be posted with the request.
            headers (Dict[str,str] , optional): Additional request headers that
                should be used with the request.
            trace_context (Any, optional): An object to use for the
                ClientSession TraceConfig context
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
            trace_request_ctx=trace_context,
            timeout=self.config.request_timeout
            if timeout is None
            else timeout,
            )

    async def _send(
            self,
            response_class: Type,
            method: str,
            path: str,
            data: Union[None, str] = None,
            response_data: Optional[Tuple[Any, ...]] = None,
            content_type: Optional[str] = None,
            trace_context: Optional[Any] = None,
            # data_provider: Optional[DataProvider] = None,
            timeout: Optional[float] = None,
            content_length: Optional[int] = None,
    ):
        headers = {
            "Content-Type": content_type if content_type else "application/json",
            "Accept": "*/*",
            "User-Agent": USER_AGENT
        }

        if not isinstance(response_class, LoginResponse):
            headers["Authorization"] = f"Bearer {self.access_token}"

        if content_length is not None:
            headers["Content-Length"] = str(content_length)

        got_429 = 0
        max_429 = self.config.max_limit_exceeded

        got_timeouts = 0
        max_timeouts = self.config.max_timeouts

        while True:
            try:
                transport_resp = await self.send(
                    method, path, data, headers, trace_context, timeout,
                )

                resp = await self.create_wire_response(
                    response_class, transport_resp, response_data,
                )

                if (
                        transport_resp.status == 429 or (
                        isinstance(resp, ErrorResponse) and
                        resp.status_code in ("M_LIMIT_EXCEEDED", 429)
                )
                ):
                    got_429 += 1

                    if max_429 is not None and got_429 > max_429:
                        break

                    await self.run_response_callbacks([resp])

                    retry_after_ms = getattr(resp, "retry_after_ms", 0) or 5000
                    await sleep(retry_after_ms / 1000)
                else:
                    break

            except (ClientConnectionError, TimeoutError, AsyncioTimeoutError):
                got_timeouts += 1

                if max_timeouts is not None and got_timeouts > max_timeouts:
                    raise

                wait = await self.get_timeout_retry_wait_time(got_timeouts)
                await sleep(wait)

        await self.receive_response(resp)
        return resp

    async def receive_response(self, response: Response) -> None:
        """Receive a Matrix Response and change the client state accordingly.

        Automatically called for all "high-level" methods of this API (each
        function documents calling it).

        Some responses will get edited for the callers convenience e.g. sync
        responses that contain encrypted messages. The encrypted messages will
        be replaced by decrypted ones if decryption is possible.

        Args:
            response (Response): the response that we wish the client to handle
        """
        if not isinstance(response, Response):
            raise ValueError("Invalid response received")

        # if isinstance(response, SyncResponse):
        #     await self._handle_sync(response)
        else:
            super().receive_response(response)

    @staticmethod
    async def parse_body(
            transport_response: ClientResponse
    ) -> Dict[Any, Any]:
        """Parse the body of the response.

        Low-level function which is normally only used by other methods of
        this class.

        Args:
            transport_response(ClientResponse): The transport response that
                contains the body of the response.

        Returns a dictionary representing the response.
        """
        try:
            return await transport_response.json()
        except (JSONDecodeError, ContentTypeError):
            try:
                # matrix.org return an incorrect content-type for .well-known
                # API requests, which leads to .text() working but not .json()
                return json.loads(await transport_response.text())
            except (JSONDecodeError, ContentTypeError):
                pass

            return {}

    async def create_wire_response(
            self,
            response_class: Type,
            transport_response: ClientResponse,
            data: Tuple[Any, ...] = None,
    ) -> Response:
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
        is_json = content_type == "application/json"

        name = None
        if transport_response.content_disposition:
            name = transport_response.content_disposition.filename

        parsed_dict = await self.parse_body(transport_response)
        resp = response_class.from_dict(parsed_dict, *data)

        resp.transport_response = transport_response
        return resp

    async def login(self, password: str):
        method, path, data = Api.login(self.email, password)
        return await self._send(LoginResponse, method.name, path, data)

    @logged_in
    async def users(self, handles: Optional[str] = None, ids: Optional[str] = None):
        method, path = Api.users(handles, ids)
        return await self._send(UsersResponse, method.name, path)
