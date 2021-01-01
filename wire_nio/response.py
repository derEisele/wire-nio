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

from dataclasses import dataclass, field
from typing import Type, Union, List, Dict, Optional
from datetime import datetime

from . import models


@dataclass
class BaseResponse:
    _model: Type = field(default=None)
    data: Union[models.ResponseType, List[models.ResponseType]] = field(default=None)
    _model_many: bool = field(default=False)

    def parse_data(self, data: Union[List[Dict], Dict]):
        if self._model_many:
            self.data = [self._model.parse_obj(m) for m in data]
        else:
            self.data = self._model.parse_obj(data)

        return self


@dataclass
class LoginResponse(BaseResponse):
    _model: Type[models.LoginResponse] = field(default=models.LoginResponse)
    cookie: Optional[str] = field(default="")
    cookie_expire: Optional[datetime] = field(default=None)


@dataclass
class ErrorResponse(BaseResponse):
    _model: Type[models.ErrorResponse] = field(default=models.ErrorResponse)


@dataclass
class UsersResponse(BaseResponse):
    _model: Type[models.UsersResponse] = field(default=models.UsersResponse)
    _model_many: bool = field(default=True)


@dataclass
class ConversationsResponse(BaseResponse):
    _model: Type[models.ConversationsResponse] = field(default=models.ConversationsResponse)


@dataclass
class ConversationResponse(BaseResponse):
    _model: Type[models.Conversation] = field(default=models.Conversation)


@dataclass
class ClientsResponse(BaseResponse):
    _model: Type[models.Client] = field(default=models.Client)
    _model_many: bool = field(default=True)


@dataclass
class NotificationsResponse(BaseResponse):
    _model: Type[models.NotificationsResponse] = field(default=models.NotificationsResponse)


@dataclass
class ClientRegisterResponse(BaseResponse):
    _model: Type[models.ClientRegisterResponse] = field(default=models.ClientRegisterResponse)


@dataclass
class ClientIdsFromUserResponse(BaseResponse):
    _model: Type[models.ClientId] = field(default=models.ClientId)
    _model_many: bool = field(default=True)


@dataclass
class PreKeyResponse(BaseResponse):
    _model: Type[models.PreKeyResponse] = field(default=models.PreKeyResponse)


@dataclass
class UserPreKeysResponse(BaseResponse):
    _model: Type[models.UserPrekeysResponse] = field(default=models.UserPrekeysResponse)
