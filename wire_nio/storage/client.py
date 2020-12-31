from pydantic import BaseModel, Field
from datetime import datetime


class ClientState(BaseModel):
    client_id: str
    cookie: str
    cookie_expire: datetime
    access_token: str


