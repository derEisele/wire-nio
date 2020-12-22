from dataclasses import dataclass
from typing import (
    Optional,
    Union,
    Coroutine,
    Any
)
from functools import wraps

from ..responses import (
    Response,
    LoginResponse,
    ErrorResponse
)
from ..exceptions import (
    LocalProtocolError
)


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
    def __init__(self, email, config: ClientConfig):
        self.email = email
        self.access_token = ""

    @property
    def logged_in(self):
        return self.access_token != ""

    def receive_response(
            self, response: Response
    ) -> Optional[Coroutine[Any, Any, None]]:
        """Receive a Matrix Response and change the client state accordingly.

        Some responses will get edited for the callers convenience e.g. sync
        responses that contain encrypted messages. The encrypted messages will
        be replaced by decrypted ones if decryption is possible.

        Args:
            response (Response): the response that we wish the client to handle
        """
        if not isinstance(response, Response):
            raise ValueError("Invalid response received")
        if isinstance(response, LoginResponse):
            self.restore_login(response.access_token)

    def _handle_login(self, response: Union[LoginResponse, ErrorResponse]):
        if isinstance(response, ErrorResponse):
            return

        self.restore_login(
            response.access_token
        )

    def restore_login(
            self,
            # user_id: str,
            access_token: str,
    ):
        """Restore a previous login to the homeserver.

        Args:
           user_id (str): The full mxid of the current user.
           device_id (str): An unique identifier that distinguishes
               this client instance.
           access_token (str): Token authorizing the user with the server.
        """
        # self.user_id = user_id
        # self.device_id = device_id
        self.access_token = access_token
        # if ENCRYPTION_ENABLED:
        #     self.load_store()
