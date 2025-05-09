import struct
from sys import argv

import light_utils

if len(argv) < 3:
    print("Usage: tool-get-metadata <game.dat> <output.dat>")
    raise SystemExit

metadata = light_utils.raw_metadata_to_dec(open(argv[1], "rb").read())
    
with open(argv[2], "wb") as f:
    f.write(metadata)

print("done.")
