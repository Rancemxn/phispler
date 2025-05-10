import fix_workpath as _

import json
from sys import argv

import UnityPy
import UnityPy.classes

if len(argv) < 5:
    print("Usage: tool-modlevel0 <level> <globalgamemanagers.assets> <info-ftt> <output-dir> [name=GameInformation]")
    raise SystemExit

mb_name = argv[5] if len(argv) >= 6 else "GameInformation"

with open("./resources/pgr_unpack_typetree.json", "r", encoding="utf-8") as f:
    typetree = json.load(f)
    
info_ftt = json.load(open(argv[3], "r", encoding="utf-8"))
        
env = UnityPy.Environment()
env.load_file(argv[2], name="assets/bin/Data/globalgamemanagers.assets")
env.load_file(argv[1])

for obj in env.objects:
    if obj.type.name != "MonoBehaviour": continue
    
    data: UnityPy.classes.MonoBehaviour = obj.read(check_read=False)
    pptr: UnityPy.classes.PPtr = data.m_Script
    name = pptr.read().m_ClassName
    
    if name == mb_name:
        obj.save_typetree(info_ftt, typetree[mb_name])
    
env.save(out_path=argv[4])
print("modified.")
