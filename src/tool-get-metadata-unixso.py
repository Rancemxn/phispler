import ctypes
import typing
from os.path import isfile

import light_utils

if not all((
    isfile("./libUnityPlugin.so"),
    isfile("./game.dat")
)):
    print("libUnityPlugin.so or game.dat not found in current directory.")
    raise SystemExit

class MemReader:
    def __init__(self, baseAddr: int):
        self.baseAddr = baseAddr
    
    def read_at(self, offset: int, size: int):
        return ctypes.string_at(self.baseAddr + offset, size)

so = ctypes.CDLL("./libUnityPlugin.so")
getGlobalMetadata: typing.Callable[[bytes], int] = so._Z26il2cpp_get_global_metadataPKc
getGlobalMetadata.argtypes = (ctypes.c_char_p, )
getGlobalMetadata.restype = ctypes.c_void_p
ggmresult_addr: int = getGlobalMetadata(b"./game.dat")

metadata = light_utils.MetadataXorCryptor(MemReader(ggmresult_addr)).decrypt()
    
with open("./global-metadata.dat", "wb") as f:
    f.write(metadata)

print("done.")
