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
