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

from typing import Dict

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

