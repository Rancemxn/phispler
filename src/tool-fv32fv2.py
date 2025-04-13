import json
from sys import argv

if len(argv) < 3:
    print("Usage: tool-fv32fv2 <input> <output>")
    raise SystemExit

with open(argv[1], "r", encoding="utf-8") as f:
    fv3 = json.load(f)

def getFloorPosition(es: list[dict], t: float, bpm: float):
    fp = 0.0
    for e in es:
        if e["endTime"] <= t:
            fp += e["value"] * (e["endTime"] - e["startTime"])
        elif e["startTime"] <= t <= e["endTime"]:
            fp += e["value"] * (t - e["startTime"])
    return fp * (1.875 / bpm)

def convertLine(fv3line: dict, lindex: int):
    fv3line["speedEvents"] = list(map(lambda e: {
        "startTime": e["startTime"],
        "endTime": 0.0,
        "value": e["value"],
        "floorPosition": getFloorPosition(fv3line["speedEvents"], e["startTime"], fv3line["bpm"])
    }, fv3line["speedEvents"]))
    
    fv3line["notesAbove"] = list(map(lambda n: {
        **n,
        "headSpeed": n["speed"] if n["type"] == 3 else 1.0,
        "judgeLineIndex": lindex,
        "isNotesAbove": True,
        "needDelet": False
    }, fv3line["notesAbove"]))
    
    fv3line["notesBelow"] = list(map(lambda n: {
        **n,
        "headSpeed": n["speed"] if n["type"] == 3 else 1.0,
        "judgeLineIndex": lindex,
        "isNotesAbove": False,
        "needDelet": False
    }, fv3line["notesBelow"]))
    
    fv3line["judgeLineDisappearEvents"] = list(map(lambda e: {
        **e,
        "start2": 0.0,
        "end2": 0.0,
        "easeType": 0,
        "easeType2": 0,
        "useEndNode": True
    }, fv3line["judgeLineDisappearEvents"]))
    
    fv3line["judgeLineRotateEvents"] = list(map(lambda e: {
        **e,
        "start2": 0.0,
        "end2": 0.0,
        "easeType": 0,
        "easeType2": 0,
        "useEndNode": True
    }, fv3line["judgeLineRotateEvents"]))
    
    fv3line["judgeLineMoveEvents"] = list(map(lambda e: {
        **e,
        "easeType": 0,
        "easeType2": 0,
        "useEndNode": True
    }, fv3line["judgeLineMoveEvents"]))
    
    return fv3line

fv2 = {
    "formatVersion": 2,
    "offset": fv3["offset"],
    "judgeLineList": list(map(convertLine, fv3["judgeLineList"], range(len(fv3["judgeLineList"]))))
}

json.dump(fv2, open(argv[2], "w", encoding="utf-8"), ensure_ascii=False)
