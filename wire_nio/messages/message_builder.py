import typing
from uuid import uuid4

from . import messages_pb2 as pb2


def generate_text_message(text: str, message_id: typing.Optional[str] = None) -> pb2.GenericMessage:
    if not message_id:
        message_id = str(uuid4())

    message = pb2.GenericMessage()
    message.message_id = message_id
    message.text.content = text
