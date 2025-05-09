import struct
from sys import argv

import light_utils

if len(argv) < 3:
    print("Usage: tool-get-metadata <game.dat> <output.dat>")
    raise SystemExit

class ByteReader:
    def __init__(self, data: bytes):
        self.data = data
        self.index = 0
    
    def read(self, length: int) -> bytes:
        value = self.data[self.index:self.index + length]
        self.index += length
        return value
    
    def read_at(self, offset: int, length: int) -> bytes:
        return self.data[offset:offset + length]
    
    def read_int(self) -> int:
        return struct.unpack("<i", self.read(4))[0]
    
def read_from_magic(magic: int):
    reader = ByteReader(raw_metadata)
    while True:
        try: v = reader.read_int()
        except struct.error: break

        if v == magic:
            start, length = reader.index - 4 + 16, reader.read_int()
            return raw_metadata[start:start + length]

raw_metadata = open(argv[1], "rb").read()
rc4_decryptor = light_utils.RC4(read_from_magic(1451223060))
metadata = light_utils.MetadataXorDecryptor(ByteReader(rc4_decryptor.crypt(read_from_magic(-1124405112)))).get()
    
with open(argv[2], "wb") as f:
    f.write(metadata)

print("done.")
