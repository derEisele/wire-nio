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

import typing
from uuid import uuid4

from . import messages_pb2 as pb2
from . import models as dc


def generate_text_message(text: str, message_id: typing.Optional[str] = None) -> pb2.GenericMessage:
    if not message_id:
        message_id = str(uuid4())

    message = pb2.GenericMessage()
    message.message_id = message_id
    message.text.content = text


def get_message_type(p_message: pb2.GenericMessage):
    if p_message.HasField("text"):
        return dc.Text
    elif p_message.HasField("knock"):
        return dc.Knock


def to_dataclass(p_message: pb2.GenericMessage):
    content_class = get_message_type(p_message)
    content = content_class.from_proto(p_message)

    return dc.MessageContainer(
        _type=content_class,
        content=content,
        message_id=p_message.message_id
    )


def to_proto(d_message: dc.MessageContainer):
    return d_message.to_proto()
