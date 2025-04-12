import UnityPy.math
import fix_workpath as _
import check_bin as _

import json
import typing
import struct
from sys import argv
from os import popen

import UnityPy
import UnityPy.classes
import UnityPy.files
import UnityPy.streams
from pydub import AudioSegment
from PIL import Image, ImageFilter

import tempdir

if len(argv) < 6:
    print("Usage: tool-modpack <mod-list> <info> <extended-info> <apk-unpack-dir> <output-dir>")
    raise SystemExit
    
def loadbundle(fn: str) -> UnityPy.files.BundleFile:
    fp = f"{argv[4]}/assets/aa/Android/{fn}"
    env = UnityPy.load(fp)
    return list(env.files.values())[0]

def savebundle(bundle: UnityPy.files.BundleFile, fn: str):
    fp = f"{argv[5]}/{fn}"
    with open(fp, "wb") as f:
        f.write(bundle.save("lz4"))

def findinfo_byname(name: str):
    for i in info:
        if i["songName"] == name:
            return i
    return None

def findexinfo_byinfo(iitem: dict, key: str):
    for i in extended_info:
        if i["key"] == iitem["songIdBak"] + "/" + key:
            return i
    return None if not key.endswith(".png") else findexinfo_byinfo(iitem, key[:-4] + ".jpg")

def putinto_t2d(t2d: UnityPy.classes.Texture2D, im: Image.Image):
    t2d.set_image(im)
    
    # https://github.com/K0lb3/UnityPy/issues/230
    tree = t2d.read_typetree()
    
    if "m_MipMap" in tree:
        tree["m_MipMap"] = t2d.m_MipMap
    else:
        tree["m_MipCount"] = t2d.m_MipCount

    tree["m_TextureFormat"] = t2d.m_TextureFormat
    tree["m_CompleteImageSize"] = len(t2d.image_data)
    tree["image data"] = t2d.image_data

    tree["m_StreamData"] = {
        "offset": 0,
        "size": 0,
        "path": ""
    }
    
    t2d.reader.save_typetree(tree)

def putimto_bundle(bundle: typing.Optional[UnityPy.files.BundleFile], im: Image.Image, pid: int):
    if bundle is None: return
    for name, f in bundle.files.copy().items():
        if isinstance(f, UnityPy.files.SerializedFile):
            for pid2, asset in f.files.copy().items():
                asset: UnityPy.files.ObjectReader
                realasset = asset.read()
                if isinstance(realasset, UnityPy.classes.Texture2D):
                    putinto_t2d(realasset, im)
                elif isinstance(realasset, UnityPy.classes.Sprite):
                    reader: UnityPy.files.ObjectReader = realasset.m_RD.texture.get_obj()
                    t2d: UnityPy.classes.Texture2D = reader.read()
                    putinto_t2d(t2d, im)
                else:
                    f.files.pop(pid2)
        else:
            bundle.files.pop(name)

def fail(mod: dict):
    print(f"Failed to process mod: {mod["name"]}")

modlist = json.load(open(argv[1], "r", encoding="utf-8"))
info = json.load(open(argv[2], "r", encoding="utf-8"))
extended_info = json.load(open(argv[3], "r", encoding="utf-8"))

for mod in modlist:
    match mod["type"]:
        case "Chart":
            iitem = findinfo_byname(mod["name"])
            if iitem is None:
                fail(mod)
                continue
            
            exiitem = findexinfo_byinfo(iitem, f"Chart_{mod["level"]}.json")
            if exiitem is None:
                fail(mod)
                continue
            
            chart = json.load(open(mod["content_path"], "r", encoding="utf-8"))
            if "META" in chart:
                rpe2phi = input("rpe2phi runner: ").replace("/", "\\")
                print(f"Mod {mod["name"]} is rpe format, converting...")
                tdir = tempdir.createTempDir()
                popen(f"{rpe2phi} \"{mod["content_path"]}\" \"{tdir}\\chart.json\"").read()
                chart = json.load(open(f"{tdir}\\chart.json", "r", encoding="utf-8"))
            content = json.dumps(chart, ensure_ascii=False).encode("utf-8")
            
            bundle = loadbundle(exiitem["fn"])
            for name, f in bundle.files.items():
                f: UnityPy.files.SerializedFile
                for pid, asset in f.files.items():
                    asset: UnityPy.files.ObjectReader
                    if pid == exiitem["path_id"]:
                        textasset: UnityPy.classes.TextAsset = asset.read()
                        rawchart = textasset.script.tobytes()
                        rawdata: bytes = asset.get_raw_data().tobytes()
                        moded = rawdata.replace(rawchart, content)
                        size = len(rawchart).to_bytes(4, "little")
                        newsize = len(content).to_bytes(4, "little")
                        asset.set_raw_data(memoryview(moded.replace(size, newsize, 1)))
                        
            savebundle(bundle, exiitem["fn"])
        
        case "Audio":
            iitem = findinfo_byname(mod["name"])
            if iitem is None:
                fail(mod)
                continue

            exiitem = findexinfo_byinfo(iitem, "music.wav")
            if exiitem is None:
                fail(mod)
                continue
            
            tdir = tempdir.createTempDir()
            seg: AudioSegment = AudioSegment.from_file(mod["content_path"])
            seg.export(f"{tdir}/music.ogg", format="ogg")
            popen(f".\\bin\\oggvorbis2fsb5.exe \"{tdir}/music.ogg\" \"{tdir}/music.fsb\"").read()
            fsb = open(f"{tdir}/music.fsb", "rb").read()

            bundle = loadbundle(exiitem["fn"])
            for name, f in bundle.files.items():
                if isinstance(f, UnityPy.streams.EndianBinaryReader):
                    f.view = memoryview(fsb)
                    f.Length = len(fsb)
                else:
                    f: UnityPy.files.SerializedFile
                    for pid, asset in f.files.items():
                        asset: UnityPy.files.ObjectReader
                        realasset = asset.read()
                        if isinstance(realasset, UnityPy.classes.AudioClip):
                            asset.data = memoryview(
                                asset.get_raw_data().tobytes()
                                .replace(realasset.m_Size.to_bytes(4, "little"), len(fsb).to_bytes(4, "little"), 1)
                                .replace(struct.pack("f", realasset.m_Length), struct.pack("f", seg.duration_seconds), 1)
                            )
            
            savebundle(bundle, exiitem["fn"])
            
        case "Ill":
            print("Warning: Ill mod has bugs, it will make game crash.")
            iitem = findinfo_byname(mod["name"])
            if iitem is None:
                fail(mod)
                continue
            
            im = Image.open(mod["content_path"])
            if im.size != (2048, 1080):
                im = im.resize((2048, 1080))
            
            i1, i2, i3 = (
                findexinfo_byinfo(iitem, "IllustrationBlur.png"),
                findexinfo_byinfo(iitem, "Illustration.png"),
                findexinfo_byinfo(iitem, "IllustrationLowRes.png"),
            )
            b1, b2, b3 = loadbundle(i1["fn"]), loadbundle(i2["fn"]), loadbundle(i3["fn"])
            
            putimto_bundle(b1, im.filter(ImageFilter.GaussianBlur(10)).resize((256, 135)), i1["path_id"])
            putimto_bundle(b2, im, i2["path_id"])
            putimto_bundle(b3, im.resize((512, 270)), i3["path_id"])
            
            savebundle(b1, i1["fn"])
            savebundle(b2, i2["fn"])
            savebundle(b3, i3["fn"])
            
        case _:
            print(f"Unknown mod type: {mod["type"]}")
