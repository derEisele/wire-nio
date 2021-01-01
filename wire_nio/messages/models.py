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

from typing import Union, Type, Iterable
from dataclasses import dataclass, field

from .messages_pb2 import GenericMessage


@dataclass
class Mention:
    user_id: str


@dataclass
class Text:
    content: str
    expects_read_confirmation: bool = field(default=False)
    mentions: Iterable[Mention] = field(default=())

    @classmethod
    def from_proto(cls, p_message: GenericMessage):
        return cls(
            content=p_message.text.content,
            expects_read_confirmation=p_message.text.expects_read_confirmation
        )

    def fill_proto(self, p_message: GenericMessage):
        p_message.text.content = self.content
        p_message.text.expects_read_confirmation = self.expects_read_confirmation


@dataclass
class Knock:
    hot_knock: bool = field(default=False)
    expects_read_confirmation: bool = field(default=False)

    @classmethod
    def from_proto(cls, p_message: GenericMessage):
        return cls(
            hot_knock=p_message.knock.hot_knock,
            expects_read_confirmation=p_message.knock.expects_read_confirmation
        )

    def fill_proto(self, p_message: GenericMessage):
        p_message.knock.hot_knock = self.hot_knock
        p_message.knock.expects_read_confirmation = self.expects_read_confirmation


MessageTypes = Union[
    Text,
    Knock
]


@dataclass
class MessageContainer:
    _type: Type[MessageTypes]
    content: MessageTypes
    message_id: str

    def to_proto(self) -> GenericMessage:
        p = GenericMessage()
        p.message_id = self.message_id
        self.content.fill_proto(p)
        return p
