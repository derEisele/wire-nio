from dataclasses import dataclass, field

from typing import (
    Optional,
    Dict,
    Any,
    List
)

from .http import TransportResponse


@dataclass
class Response:
    uuid: str = field(default="", init=False)
    start_time: Optional[float] = field(default=None, init=False)
    end_time: Optional[float] = field(default=None, init=False)
    timeout: int = field(default=0, init=False)
    transport_response: Optional[TransportResponse] = field(
        init=False, default=None,
    )

    @property
    def elapsed(self):
        if not self.start_time or not self.end_time:
            return 0
        elapsed = self.end_time - self.start_time
        return max(0, elapsed - (self.timeout / 1000))


@dataclass
class LoginResponse(Response):
    expires_in: int = field()
    access_token: str = field()
    token_type: str = field()

    @classmethod
    def from_dict(cls, parsed_dict: Dict[str, Any]):
        return cls(
            parsed_dict["expires_in"],
            parsed_dict["access_token"],
            parsed_dict["token_type"]
        )


@dataclass
class Asset:
    size: str = field()
    key: str = field()
    type: str = field()

    @classmethod
    def from_dict(cls, parsed_dict: Dict[str, Any]):
        return cls(
            parsed_dict["size"],
            parsed_dict["key"],
            parsed_dict["type"]
        )


@dataclass
class User:
    handle: str = field()
    locale: str = field()
    accent_id: int = field()
    name: str = field()
    id: str = field()
    picture: List[Any] = field(default_factory=lambda _: [])
    assets: List[Asset] = field(default_factory=lambda _: [])

    @classmethod
    def from_dict(cls, parsed_dict: Dict[str, Any]):
        assets = [Asset.from_dict(a) for a in parsed_dict["assets"]]
        pictures = []  # TODO: Add Pictures
        return cls(
            parsed_dict["handle"],
            parsed_dict["locale"],
            parsed_dict["accent_id"],
            parsed_dict["name"],
            parsed_dict["id"],
            pictures,
            assets
        )


@dataclass
class UsersResponse(Response):
    users: List[User] = field()

    @classmethod
    def from_dict(cls, parsed_dict: List[Dict[str, Any]]):
        users = [User.from_dict(u) for u in parsed_dict]
        return cls(users)

@dataclass
class ErrorResponse(Response):
    pass
