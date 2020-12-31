from typing import Dict
from base64 import b64decode

from cryptobox import cbox


class CrytoHandler:
    def __init__(self, path="./box"):
        self.prekeys: Dict[int, cbox.PreKey] = {}
        self.last_prekey: cbox.PreKey = None
        self.cryptobox = cbox.CBox()
        self.cryptobox.file_open(path)

    def generate_prekeys(self, start: int = 0, count: int = 50):
        self.last_prekey = self.cryptobox.new_last_pre_key()
        for i in range(start, count):
            self.prekeys[i] = self.cryptobox.new_pre_key(i)

    def decrypt_message(self, from_: str, sender: str, text: str):
        dec = self.cryptobox.decrypt(from_, sender, b64decode(text))
        return dec

