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

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union, Dict
from datetime import datetime

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    expires_in: int
    access_token: str
    token_type: str


class ErrorResponse(BaseModel):
    code: int


class Asset(BaseModel):
    size: str
    key: str
    type: str


class QualifiedId(BaseModel):
    domain: str
    id: str


class PictureInfo(BaseModel):
    height: int
    tag: str
    original_width: int
    width: int
    original_height: int
    nonce: str
    public: bool


class Picture(BaseModel):
    content_length: int
    data: Optional[Any]
    content_type: str
    id: str
    info: PictureInfo


class UsersResponse(BaseModel):
    handle: str
    locale: Optional[str]
    accent_id: int
    name: str
    id: str
    picture: List[Picture]
    assets: List[Asset]
    qualified_id: QualifiedId


class ServiceRef(BaseModel):
    id: str
    provider: str


class Member(BaseModel):
    hidden_ref: Optional[str]
    service: Optional[ServiceRef]
    otr_muted_ref: Optional[str]
    hidden: Optional[bool]
    id: str
    otr_archived: Optional[bool]
    otr_muted: Optional[bool]
    otr_archived_ref: Optional[str]
    conversation_role: str
    status_ref: float
    status_time: datetime


class OtherMember(BaseModel):
    service: Optional[ServiceRef]
    id: str
    conversation_role: str


class ConversationMembers(BaseModel):
    self: Member
    others: List[OtherMember]


class Conversation(BaseModel):
    access: List[str]
    creator: str
    members: ConversationMembers
    name: Optional[str]
    team: Optional[Any]
    id: str
    type: int
    message_timer: Optional[int]
    receipt_mode: Optional[Any]
    last_event_time: datetime
    last_event: float


class ConversationsResponse(BaseModel):
    has_more: bool
    conversations: List[Conversation]


class Location(BaseModel):
    lat: float
    lon: float


class Client(BaseModel):
    time: datetime
    location: Location
    model: Optional[str]
    id: str
    type: str
    class_: Optional[str] = Field(alias="class")
    label: Optional[str]
    cookie: Optional[str]


class User(BaseModel):
    email: str
    locale: str
    managed_by: str
    accent_id: int
    picture: List[Picture]
    name: str
    id: str
    assets: List[Asset]


class NUserActivate(BaseModel):
    type: Literal["user.activate"]
    user: User


class NUserClientAdd(BaseModel):
    type: Literal["user.client-add"]
    client: Client


class NUserUpdate(BaseModel):
    type: Literal["user.update"]
    user: Dict[str, Any]  # User with all optional


class NUserPropertiesSet(BaseModel):
    type: Literal["user.properties-set"]
    key: str
    value: Dict[str, Any]


class NConversationCreate(BaseModel):
    type: Literal["conversation.create"]
    conversation: str
    time: datetime
    from_: str = Field(alias="from")
    data: Conversation


class ConversationRequest(BaseModel):
    email: Optional[str]
    name: str
    message: str
    recipient: str


class NConversationConnectRequest(BaseModel):
    type: Literal["conversation.connect-request"]
    conversation: str
    time: datetime
    from_: str = Field(alias="from")
    data: ConversationRequest


class ClientId(BaseModel):
    id: str


class NUserClientRemove(BaseModel):
    type: Literal["user.client-remove"]
    client: ClientId


class Connection(BaseModel):
    status: str
    conversation: str
    to: str
    from_: str = Field(alias="from")
    last_update: datetime
    message: str


class NUserConnection(BaseModel):
    type: Literal["user.connection"]
    connection: Connection


class UserMember(BaseModel):
    conversation_role: str
    id: str


class MemberJoin(BaseModel):
    users: List[UserMember]
    user_ids: List[str]


class NConversationMemberJoin(BaseModel):
    type: Literal["conversation.member-join"]
    conversation: str
    time: datetime
    data: MemberJoin
    from_: str = Field(alias="from")


class OtrMessage(BaseModel):
    text: str
    sender: str
    recipient: str


class NConversationOtrMessageAdd(BaseModel):
    type: Literal["conversation.otr-message-add"]
    conversation: str
    time: datetime
    data: OtrMessage
    from_: str = Field(alias="from")


class Notification(BaseModel):
    payload: List[Union[
        NUserActivate,
        NUserClientAdd,
        NUserUpdate,
        NConversationConnectRequest,
        NConversationCreate,
        NConversationMemberJoin,
        NConversationOtrMessageAdd,
        NUserConnection,
        NUserPropertiesSet,
        NUserClientRemove,
        # Dict[str, Any]
    ]]
    id: str


class NotificationsResponse(BaseModel):
    has_more: bool
    notifications: List[Notification]
    time: Optional[datetime]


class Key(BaseModel):
    key: str
    id: int


class SigKey(BaseModel):
    enckey: str
    mackey: str


class ClientRegisterRequest(BaseModel):
    cookie: str
    lastkey: Key
    sigkeys: SigKey
    password: str
    type: Literal["permanent", "temporary"]
    prekeys: List[Key]
    class_: str = Field(alias="class", default="desktop")
    model: str = Field(default="Wire-Nio")
    label: str


class ClientRegisterResponse(BaseModel):
    id: str
    cookie: str
    label: str
    location: Location
    time: datetime
    type: Literal["permanent", "temporary"]


class PreKeyResponse(BaseModel):
    client: str
    prekey: Key


class UserPrekeysResponse(BaseModel):
    user: str
    clients: List[PreKeyResponse]


ResponseType = Union[
    NotificationsResponse,
    LoginResponse,
    UsersResponse,
    ErrorResponse,
    ConversationsResponse,
    ClientRegisterRequest,
    UserPrekeysResponse,
    PreKeyResponse
]
