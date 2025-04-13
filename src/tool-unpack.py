import fix_workpath as _
import check_bin as _

import json
import struct
import base64
from os import mkdir, popen, listdir
from os.path import exists, isfile, basename, dirname
from shutil import rmtree
from threading import Thread
from time import sleep
from uuid import uuid4
from zipfile import ZipFile

import UnityPy
import UnityPy.files
import UnityPy.classes
from UnityPy.enums import ClassIDType
from fsb5 import FSB5

import pgr_catalog
    
iothread_num = 32
packthread_num = 1
p2rthread_num = 4

class ByteReaderA:
    def __init__(self, data: bytes):
        self.data = data
        self.position: int = 0
        self.d = {int: self.readInt, float: self.readFloat, str: self.readString}

    def readInt(self):
        self.position += 4
        return self.data[self.position - 4] ^ self.data[self.position - 3] << 8

    def readFloat(self):
        self.position += 4
        return struct.unpack("f", self.data[self.position - 4 : self.position])[0]

    def readString(self):
        length = self.readInt()
        result = self.data[self.position : self.position + length].decode()
        self.position += length // 4 * 4
        if length % 4 != 0:
            self.position += 4
        return result
    
    def readSchema(self, schema: dict):
        pbak = self.position
        try:
            result = []
            for _ in range(self.readInt()):
                item = {}
                for key, value in schema.items():
                    if value in (int, str, float):
                        item[key] = self.d[value]()
                    elif isinstance(value, list):
                        item[key] = [self.d[value[0]]() for _ in range(self.readInt())]
                    elif isinstance(value, tuple):
                        for t in value: self.d[t]()
                    elif isinstance(value, dict):
                        item[key] = self.readSchema(value)
                    else:
                        raise Exception("null")
                result.append(item)
            return result
        except Exception as e:
            self.position = pbak
            raise e
    
def setApk(path: str):
    global pgrapk
    pgrapk = path

def getZipItem(path: str) -> bytes:
    if path[0] in ("/", "\\"): path = path[1:]
    return ZipFile(pgrapk).read(path)

def createZip(files: str, to: str):
    with ZipFile(to, "w") as f:
        for file in files:
            f.write(file, arcname=basename(file))

def run(rpe: bool, need_otherillu: bool, need_other_res: bool):
    try: rmtree("unpack-temp")
    except Exception: pass
    try: mkdir("unpack-temp")
    except FileExistsError: pass
    
    print("generate info.json...")
    infoResult = generate_info()
    print("generated info.json")
    
    print("unpack...")
    generate_resources(need_otherillu, need_other_res)
    print("unpacked")
    
    print("pack charts...")
    pack_charts(infoResult, rpe)
    print("packed charts")
    
    try: rmtree("unpack-temp")
    except Exception: pass

def merge_list(lsts: list):
    return [item for lst in lsts for item in lst]

def load_level(env: UnityPy.Environment, i: int):
    try:
        env.load_file(getZipItem(f"/assets/bin/Data/level{i}"))
    except KeyError:
        split_i = 0
        while True:
            try:
                env.load_file(getZipItem(f"/assets/bin/Data/level{i}.split{split_i}"))
            except KeyError:
                if split_i == 0:
                    raise ValueError("level not found")
                break
            
            split_i += 1

def load_all_level(env: UnityPy.Environment):
    i = 0
    while True:
        try:
            load_level(env, i)
        except ValueError:
            break
        i += 1

def generate_info():
    try: rmtree("unpack-result")
    except Exception: pass
    try: mkdir("unpack-result")
    except FileExistsError: pass
    
    env = UnityPy.Environment()
    env.load_file(
        getZipItem("/assets/bin/Data/globalgamemanagers.assets"),
        name = "assets/bin/Data/globalgamemanagers.assets"
    )
    
    load_level(env, 0)
    
    with open("./resources/pgr_unpack_treetype.json", "r", encoding="utf-8") as f:
        treetype = json.load(f)
            
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour": continue
        
        try:
            data = obj.read()
            name = data.m_Script.get_obj().read().name
            match name:
                case "GameInformation":
                    information: bytes = data.raw_data.tobytes()
                    information_ftt = obj.read_typetree(treetype["GameInformation"])
                    
                case "GetCollectionControl":
                    collection = obj.read_typetree(treetype["GetCollectionControl"])
                    with open("./unpack-result/collectionItems.json", "w", encoding="utf-8") as f:
                        json.dump(collection["collectionItems"], f, indent=4, ensure_ascii=False)
                    
                    with open("./unpack-result/avatars.json", "w", encoding="utf-8") as f:
                        json.dump(collection["avatars"], f, indent=4, ensure_ascii=False)
                        
                case "TipsProvider":
                    tips = obj.read_typetree(treetype["TipsProvider"])
                    with open("./unpack-result/tips.json", "w", encoding="utf-8") as f:
                        json.dump(tips["tips"], f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(repr(e))

    with open("./unpack-result/info_ftt.json", "w", encoding="utf-8") as f:
        json.dump(information_ftt, f, indent=4, ensure_ascii=False)
                        
    reader = ByteReaderA(information)
    reader.position = information.index(b"\x16\x00\x00\x00Glaciaxion.SunsetRay.0\x00\x00\n") - 4
    
    songBase_schema = {
        "songId": str,
        "songKey": str,
        "songName": str,
        "songTitle": str,
        "difficulty": [float],
        "illustrator": str,
        "charter": [str],
        "composer": str,
        "levels": [str],
        "previewTimeStart": float,
        "previewTimeEnd": float,
        "unlockList": {
            "unlockType": int,
            "unlockInfo": [str]
        },
        "levelMods": {
            "n": [str],
            "magic": int
        },
        "magic": int
    }
    
    def fttinfo_fromid(ftt: dict, key: str, songid: str):
        for i in ftt:
            if i[key] == songid: return i
        assert False, f"song {songid} not found in fttinfo"
    
    ftt_allsongs = merge_list(information_ftt["song"].values())
    ftt_keystore = information_ftt["keyStore"]
    
    with open("./unpack-result/chapters_info.json", "w", encoding="utf-8") as f:
        json.dump(information_ftt["chapters"], f, indent=4, ensure_ascii=False)
    
    chartItems = []
    
    while True:
        try:
            for item in reader.readSchema(songBase_schema):
                while 0.0 in item["difficulty"]:
                    i = item["difficulty"].index(0.0)
                    item["difficulty"].pop(i)
                    item["charter"].pop(i)
                    item["levels"].pop(i)

                item["songIdBak"] = item["songId"]
                if item["songId"][-2:] == ".0": item["songId"] = item["songId"][:-2]
                item["difficulty"] = list(map(lambda x: round(x, 1), item["difficulty"]))
                
                chartItems.append(item)
        except struct.error:
            break
        except Exception as e:
            print(e)
    
    for i in chartItems:
        fttinfo = fttinfo_fromid(ftt_allsongs, "songsId", i["songIdBak"])
        i.update({k: fttinfo[k] for k in [
            "unlockInfo", "levelMods",
            "isCnLimited"
        ]})
        
        fttinfo = fttinfo_fromid(ftt_keystore, "keyName", i["songKey"])
        i.update({"keyStore": {k: fttinfo[k] for k in [
            "unlockedTimes", "kindOfKey",
            "unlockTimes"
        ]}})
    
    with open("./unpack-result/info.json", "w", encoding="utf-8") as f:
        json.dump(chartItems, f, ensure_ascii=False, indent=4)
    
    return chartItems

def generate_resources(need_otherillu: bool = False, need_other_res: bool = False):
    catalog = json.loads(getZipItem("/assets/aa/catalog.json").decode("utf-8"))
    
    for i in [
        "Chart_EZ", "Chart_HD", "Chart_IN", "Chart_AT", "Chart_Legacy", "Chart_Error",
        *(("IllustrationBlur", "IllustrationLowRes") if need_otherillu else ()), "Illustration", "music",
        "avatars", *(("other_res", ) if need_other_res else ())
    ]:
        try: rmtree(f"./unpack-result/{i}")
        except Exception: pass
        try: mkdir(f"./unpack-result/{i}")
        except FileExistsError: pass
    
    table = pgr_catalog.decrypt(catalog)
    
    type res_table_item = tuple[str, str]
    player_res_table: list[res_table_item] = []
    avatar_res_table: list[res_table_item] = []
    other_res_table: list[res_table_item] = []
    
    for i in table:
        if isinstance(i[0], int): continue
    
        if i[0].startswith("Assets/Tracks/#"):
            other_res_table.append((i[0].replace("Assets/Tracks/#", "", 1), i[1]))
        
        elif i[0].startswith("Assets/Tracks/"):
            player_res_table.append((i[0].replace("Assets/Tracks/", "", 1), i[1]))
        
        elif i[0].startswith("avatar."):
            avatar_res_table.append((i[0].replace("avatar.", "", 1), i[1]))
    
    with open("./unpack-result/catalog.json", "w", encoding="utf-8") as f:
        json.dump({
            "raw": table,
            "player_res": player_res_table,
            "avatar_res": avatar_res_table
        }, f, ensure_ascii=False, indent=4)
    
    def save_player_res(key: str, entry: UnityPy.files.BundleFile, fn: str):
        obj: UnityPy.classes.TextAsset | UnityPy.classes.Sprite | UnityPy.classes.AudioClip
        obj = next(entry.get_filtered_objects((ClassIDType.TextAsset, ClassIDType.Sprite, ClassIDType.AudioClip))).read()
        extended_info.append({
            "key": key,
            "fn": fn,
            "type": obj.type.value,
            "type_string": obj.type.name,
            "path_id": obj.path_id,
            "name": obj.name
        })
        
        key = key.replace("\\", "/")
        keyfoldername = dirname(key)
        keybasename = basename(key)
        keymainname = ".".join(keybasename.split(".")[:-1])
        keyextname = keybasename.split(".")[-1]
        
        if keymainname.startswith("Chart_") and keyextname == "json":
            if not keymainname.endswith("_Error"):
                iocommands.append(("save-string", f"{keymainname}/{keyfoldername}.json", obj.script))
            else:
                level = keymainname.replace("Chart_", "").replace("_Error", "")
                iocommands.append(("save-string", f"Chart_Error/{keyfoldername}_{level}.json", obj.script))
        
        elif keymainname in ("IllustrationBlur", "IllustrationLowRes") and keyextname in ("png", "jpg", "jpeg"):
            if not need_otherillu: return
            iocommands.append(("save-pilimg", f"{keymainname}/{keyfoldername}.png", obj.image))
            
        elif keymainname.startswith("Illustration") and keyextname in ("png", "jpg", "jpeg"):
            iocommands.append(("save-pilimg", f"Illustration/{keyfoldername}.png", obj.image))
            
        elif keymainname == "music" and keyextname in ("wav", "ogg", "mp3"):
            fsb = FSB5(obj.m_AudioData.tobytes() if isinstance(obj.m_AudioData, memoryview) else obj.m_AudioData)
            iocommands.append(("save-music", f"music/{keyfoldername}.ogg", fsb.rebuild_sample(fsb.samples[0])))
        
        else:
            print(f"Unknown res: {key}: {obj}")
    
    def save_avatar_res(key: str, entry: UnityPy.files.BundleFile, fn: str):
        obj: UnityPy.classes.Sprite
        obj = next(entry.get_filtered_objects((ClassIDType.Sprite, ))).read()
        extended_info.append({
            "key": key,
            "fn": fn,
            "type": obj.type.value,
            "type_string": obj.type.name,
            "path_id": obj.path_id,
            "name": obj.name
        })
        iocommands.append(("save-pilimg", f"avatars/{key}.png", obj.image))
    
    def save_other_res(key: str, entry: UnityPy.files.BundleFile, fn: str):
        obj: UnityPy.classes.TextAsset | UnityPy.classes.Sprite | UnityPy.classes.AudioClip
        obj = next(entry.get_filtered_objects((ClassIDType.TextAsset, ClassIDType.Sprite, ClassIDType.AudioClip))).read()
        
        flodername = dirname(key)
        fp = f"other_res/{key}"
        try: mkdir(f"./unpack-result/other_res/{flodername}")
        except FileExistsError: pass
        
        if isinstance(obj, UnityPy.classes.TextAsset):
            iocommands.append(("save-string", fp, obj.script))
            
        elif isinstance(obj, UnityPy.classes.Sprite):
            iocommands.append(("save-pilimg", fp, obj.image))
            
        elif isinstance(obj, UnityPy.classes.AudioClip):
            fsb = FSB5(obj.m_AudioData.tobytes() if isinstance(obj.m_AudioData, memoryview) else obj.m_AudioData)
            iocommands.append(("save-music", fp, fsb.rebuild_sample(fsb.samples[0])))
    
    def io():
        nonlocal keunpack_count, save_string_count
        nonlocal save_pilimg_count, save_music_count
        nonlocal stopthread_count
        
        while True:
            try:
                item = iocommands.pop()
                if item is None: break
                item = list(item)
            except IndexError:
                break
            
            try:
                match item[0]:
                    case "ke-unpack-player-res":
                        env = UnityPy.Environment()
                        env.load_file(getZipItem(f"/assets/aa/Android/{item[2]}"), name = item[1])
                        for ikey, ientry in env.files.items():
                            save_player_res(ikey, ientry, item[2])
                        keunpack_count += 1
                    
                    case "ke-unpack-avatar-res":
                        env = UnityPy.Environment()
                        env.load_file(getZipItem(f"/assets/aa/Android/{item[2]}"), name = item[1])
                        for ikey, ientry in env.files.items():
                            save_avatar_res(ikey, ientry, item[2])
                        keunpack_count += 1
                    
                    case "ke-unpack-other-res":
                        env = UnityPy.Environment()
                        env.load_file(getZipItem(f"/assets/aa/Android/{item[2]}"), name = item[1])
                        for ikey, ientry in env.files.items():
                            save_other_res(ikey, ientry, item[2])
                        keunpack_count += 1

                    case "save-string":
                        with open(f"./unpack-result/{item[1]}", "wb") as f:
                            f.write(item[2].tobytes())
                        save_string_count += 1
                        
                    case "save-pilimg":
                        replace_exnames = [".jpg", ".jpeg"]
                        
                        for name in replace_exnames:
                            if item[1].endswith(name):
                                item[1] = item[1][:-len(name)] + ".png"
                                break
                            
                        item[2].save(f"./unpack-result/{item[1]}", "png")
                        save_pilimg_count += 1
                        
                    case "save-music":
                        with open(f"./unpack-result/{item[1]}", "wb") as f:
                            f.write(item[2])
                        save_music_count += 1
            except Exception as e:
                print(f"has err in io: {repr(e)}")
        
        stopthread_count += 1
    
    keunpack_count = 0
    save_string_count = 0
    save_pilimg_count = 0
    save_music_count = 0
    
    stopthread_count = 0
    iocommands = [None] * iothread_num
    extended_info = []
    
    iocommands.extend(("ke-unpack-player-res", *i) for i in player_res_table)
    iocommands.extend(("ke-unpack-avatar-res", *i) for i in avatar_res_table)
    iocommands.extend(("ke-unpack-other-res", *i) for i in other_res_table) if need_other_res else None

    iots = [Thread(target=io, daemon=True) for _ in range(iothread_num)]
    (*map(lambda x: x.start(), iots), )
    
    while stopthread_count != iothread_num:
        print(f"\r{keunpack_count} | {save_string_count} | {save_pilimg_count} | {save_music_count}", end="")
        sleep(0.1)
    
    with open(f"./unpack-result/extendedInfo.json", "w", encoding="utf-8") as f:
        json.dump(extended_info, f, indent=4, ensure_ascii=False)
    
    print()

def pack_charts(infos: list[dict], rpe: bool):
    try: rmtree(f"./unpack-result/packed")
    except Exception: pass
    try: mkdir(f"./unpack-result/packed")
    except FileExistsError: pass
        
    charts = []
    allcount = 0
    for info in infos:
        for li, l in enumerate(info["levels"]):
            # tip: 2 spaces
            levelString = f"{l}  Lv.{int(info["difficulty"][li])}"
            
            chartExn = "json"
            audioExn = "ogg"
            imageExn = "png"
            
            chartFile = f"./unpack-result/Chart_{l}/{info["songIdBak"]}.{chartExn}"
            audioFile = f"./unpack-result/music/{info["songIdBak"]}.{audioExn}"
            imageFile = f"./unpack-result/Illustration/{info["songIdBak"]}.{imageExn}"
            
            csvData = "\n".join([
                "Chart,Music,Image,Name,Artist,Level,Illustrator,Charter,AspectRatio,NoteScale,GlobalAlpha",
                ",".join(map(lambda x: f"\"{x}\"" if " " in x else x, [
                    f"{info["songIdBak"]}.{chartExn}",
                    f"{info["songIdBak"]}.{audioExn}",
                    f"{info["songIdBak"]}.{imageExn}",
                    info["songName"],
                    info["composer"],
                    levelString,
                    info["illustrator"],
                    info["charter"][li]
                ]))
            ])
            
            txtData = "\n".join([
                "#",
                f"Name: {info["songName"]}",
                "Path: 0",
                f"Song: {info["songIdBak"]}.{audioExn}",
                f"Picture: {info["songIdBak"]}.{imageExn}",
                f"Chart: {info["songIdBak"]}.{chartExn}",
                f"Level: {levelString}",
                f"Composer: {info["composer"]}",
                f"Charter: {info["charter"][li]}"
            ])
            
            ymlData = "\n".join([
                f"name: {repr(info["songName"])}",
                f"difficulty: {info["difficulty"][li]}",
                f"level: {repr(levelString)}",
                f"charter: {repr(info["charter"])}",
                f"composer: {repr(info["composer"])}",
                f"illustrator: {repr(info["illustrator"])}",
                f"chart: {repr(info["songIdBak"] + f".{chartExn}")}",
                f"music: {repr(info["songIdBak"] + f".{audioExn}")}",
                f"illustration: {repr(info["songIdBak"] + f".{imageExn}")}"
            ])
            
            charts.append((info["songIdBak"], l, chartFile, audioFile, imageFile, csvData, txtData, ymlData))
            allcount += 1
    
    stopthread_count = 0
    packed_num = 0
    charts_bak = charts.copy()
    
    def packworker(p2r: bool = False):
        nonlocal packed_num, stopthread_count
        
        while charts:
            try:
                item = charts.pop()
            except IndexError:
                break
            
            try:
                rid = uuid4()
                rfolder = f"./unpack-temp/pack-{rid}"
                mkdir(rfolder)
                with open(f"{rfolder}/info.csv", "w", encoding="utf-8") as f: f.write(item[5])
                with open(f"{rfolder}/info.txt", "w", encoding="utf-8") as f: f.write(item[6])
                with open(f"{rfolder}/info.yml", "w", encoding="utf-8") as f: f.write(item[7])
                
                createZip([
                    item[2], item[3], item[4],
                    f"{rfolder}/info.csv", f"{rfolder}/info.txt", f"{rfolder}/info.yml"
                ], f"./unpack-result/packed/{item[0]}_{item[1]}{"_RPE" if p2r else ""}.zip")
                packed_num += 1
            except Exception:
                pass
        
        stopthread_count += 1
        
    ts = [Thread(target=packworker, daemon=True) for _ in range(packthread_num)]
    (*map(lambda x: x.start(), ts),)
    
    while stopthread_count != packthread_num:
        print(f"\r{packed_num} / {allcount}", end="")
        sleep(0.1)
    print(f"\r{packed_num} / {allcount}")
    
    if not rpe: return
    
    p2r = "tool-phi2rpe.py" if exists("tool-phi2rpe.py") and isfile("tool-phi2rpe.py") else "tool-phi2rpe.exe"
    phicharts = [f"./unpack-result/Chart_{l}/{i}" for l in ["EZ", "HD", "IN", "AT", "Legacy"] for i in listdir(f"./unpack-result/Chart_{l}")]
    p2red_num = 0
    stopthread_count = 0
    
    def p2rworker():
        nonlocal p2red_num, stopthread_count
        
        while phicharts:
            try:
                item = phicharts.pop()
            except IndexError:
                break
            
            try:
                popen(f"{p2r} {item} {item}").read()
                p2red_num += 1
            except Exception:
                pass
        
        stopthread_count += 1
    
    ts = [Thread(target=p2rworker, daemon=True) for _ in range(p2rthread_num)]
    (*map(lambda x: x.start(), ts),)
    
    while stopthread_count != p2rthread_num:
        print(f"\rp2r: {p2red_num} / {allcount}", end="")
        sleep(0.1)
    print(f"\rp2r: {p2red_num} / {allcount}")
    
    stopthread_count = 0
    packed_num = 0
    charts = charts_bak
    
    ts = [Thread(target=packworker, daemon=True, args=(True, )) for _ in range(packthread_num)]
    (*map(lambda x: x.start(), ts),)
    
    while stopthread_count != packthread_num:
        print(f"\rp2r pack: {packed_num} / {allcount}", end="")
        sleep(0.1)
    print(f"\rp2r pack: {packed_num} / {allcount}")

if __name__ == "__main__":
    from sys import argv
    if len(argv) < 2:
        print("Usage: tool-unpack <apk>")
        raise SystemExit
    
    if "--iothread" in argv:
        iothread_num = int(argv[argv.index("--iothread") + 1])
    
    if "--packthread" in argv:
        packthread_num = int(argv[argv.index("--packthread") + 1])
    
    if "--p2rthread" in argv:
        p2rthread_num = int(argv[argv.index("--p2rthread") + 1])
    
    setApk(argv[1])
    run("--rpe" in argv, "--need-other-illu" in argv, "--need-other-res" in argv)
