from sys import argv

import light_utils
import const

if len(argv) < 3:
    print(f"Usage: tool-create-game-dat <global-metadata.dat> <output.dat> [rc4_key]=\"{" ".join(map(str, const.PGR_METADATA_DEFAULT_RC4_KEY))}\"")
    raise SystemExit

rc4_key = bytes(map(int, argv[3].split())) if len(argv) > 3 else const.PGR_METADATA_DEFAULT_RC4_KEY
gamedat = light_utils.metadata_encrypt(open(argv[1], "rb").read(), rc4_key)
    
with open(argv[2], "wb") as f:
    f.write(gamedat)

print("done.")
