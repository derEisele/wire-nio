from dataclasses import dataclass, field
from typing import Type, Union, List, Dict

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


@dataclass
class ErrorResponse(BaseResponse):
    _model: Type[models.ErrorResponse] = field(default=models.ErrorResponse)


@dataclass
class UsersResponse(BaseResponse):
    _model: Type[models.UsersResponse] = field(default=models.UsersResponse)
    _model_many: bool = field(default=True)


@dataclass
class ConverstionsResponse(BaseResponse):
    _model: Type[models.ConversationsResponse] = field(default=models.ConversationsResponse)


@dataclass
class ClientsResponse(BaseResponse):
    _model: Type[models.Client] = field(default=models.Client)
    _model_many: bool = field(default=True)


@dataclass
class NotificationsResponse(BaseResponse):
    _model: Type[models.NotificationsResponse] = field(default=models.NotificationsResponse)
