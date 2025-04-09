import json
import typing
import copy
from sys import argv

import rpe_easing
import light_utils

if len(argv) < 3:
    print("Usage: tool-rpe2phi <input> <output>")
    raise SystemExit

with open(argv[1], "r", encoding="utf-8") as f:
    rpec = json.load(f)

globalBpm = rpec["BPMList"][0]["bpm"]
globalT = 1.875 / globalBpm
inft = 1e9
phic = {
    "formatVersion": 3,
    "offset": rpec["META"]["offset"] / 1000,
    "judgeLineList": []
}
offsetT = phic["offset"] / globalT

def calbeat(t: list[int]):
    return t[0] + t[1] / t[2]

def rt2pt(t: list[int]):
    beat = calbeat(t)
    sec = 0.0
    for i, e in enumerate(rpec["BPMList"]):
        if i != len(rpec["BPMList"]) - 1:
            et_beat = calbeat(rpec["BPMList"][i + 1]["startTime"]) - calbeat(e["startTime"])
            
            if beat >= et_beat:
                sec += et_beat * (60 / e["bpm"])
                beat -= et_beat
            else:
                sec += beat * (60 / e["bpm"])
                break
        else:
            sec += beat * (60 / e["bpm"])
    return sec / globalT

def linear(t: float, st: float, et: float, sv: float, ev: float):
    return (t - st) / (et - st) * (ev - sv) + sv

def easing(t: float, st: float, et: float, sv: float, ev: float, e: dict):
    ef = rpe_easing.ease_funcs[e.get("easingType", 1) - 1] if not e.get("bezier", 0) else light_utils.createBezierFunction(e.get("bezierPoints", [1.0, 1.0, 1.0, 1.0]))
    return ef((t - st) / (et - st)) * (ev - sv) + sv

def getDt(big_edt: float):
    # 谱师能不能用点缓动切割
    # if big_edt >= 512: dt = 16
    # elif big_edt >= 256: dt = 8
    # elif big_edt >= 128: dt = 4
    # else: dt = 1
    # return dt
    return 2

def convertEventsTime(es: list[dict]):
    for e in es:
        e["startTime"] = rt2pt(e["startTime"])
        e["endTime"] = rt2pt(e["endTime"])

def sortEvents(es: list[dict]):
    es.sort(key=lambda e: e["startTime"])

def fillEvents(es: list[dict]):
    if not es:
        es.append({
            "startTime": -inft,
            "endTime": inft,
            "start": 0,
            "end": 0,
            "easingType": 1
        })
        return
    
    othes = []
    for i, e in enumerate(es):
        if i == 0: continue
        le = es[i - 1]
        if le["endTime"] < e["startTime"]:
            othes.append({
                "startTime": le["endTime"],
                "endTime": e["startTime"],
                "start": le["end"],
                "end": le["end"],
                "easingType": 1
            })
    es.extend(othes)
    sortEvents(es)
    
    fe, le = es[0], es[-1]
    if fe["start"] != fe["end"]:
        es.insert(0, {
            "startTime": -inft,
            "endTime": fe["startTime"],
            "start": 0,
            "end": 0,
            "easingType": 1
        })
    else:
        fe["startTime"] = -inft
    
    if le["start"] != le["end"]:
        es.append({
            "startTime": le["endTime"],
            "endTime": inft,
            "start": le["end"],
            "end": le["end"],
            "easingType": 1
        })
    else:
        le["endTime"] = inft

def splitEvents(es: list[dict], isspeed: bool):
    nes = []
    for e in es:
        if not isspeed:
            if e["start"] == e["end"] or e.get("easingType", 1) == 1:
                nes.append(e)
                continue
            
            t = e["startTime"]
            dt = getDt(e["endTime"] - e["startTime"])
            while t <= e["endTime"]:
                nes.append({
                    "startTime": t,
                    "endTime": t + dt,
                    "start": easing(t, e["startTime"], e["endTime"], e["start"], e["end"], e),
                    "end": easing(t + dt, e["startTime"], e["endTime"], e["start"], e["end"], e),
                })
                t += dt
            
            if t < e["endTime"]:
                nes.append({
                    "startTime": t,
                    "endTime": e["endTime"],
                    "start": easing(t, e["startTime"], e["endTime"], e["start"], e["end"], e),
                    "end": e["end"],
                })
        
        else: # isspeed
            if e["start"] == e["end"]:
                nes.append({
                    "startTime": e["startTime"],
                    "endTime": e["endTime"],
                    "start": e["start"],
                    "end": e["start"]
                })
                continue
            
            t = e["startTime"]
            dt = getDt(e["endTime"] - e["startTime"])
            while t <= e["endTime"]:
                v = easing(t, e["startTime"], e["endTime"], e["start"], e["end"], e)
                nes.append({
                    "startTime": t,
                    "endTime": t + dt,
                    "start": v,
                    "end": v
                })
                t += dt
            
            if t < e["endTime"]:
                nes.append({
                    "startTime": t,
                    "endTime": e["endTime"],
                    "start": e["end"],
                    "end": e["end"],
                })
                
    es.clear()
    es.extend(nes)

def getEventsValue(es: list[dict], t: float, d: bool):
    if not es: return 0.0
    result = es[0]["start"]
    for e in es:
        if t < e["startTime"]: break
        if d and t == e["startTime"]: break
        if t >= e["endTime"]: result = e["end"]
        else: result = e["start"]
    return result

def mergeEvents(es: list[dict]):
    times = sorted(set([e["startTime"] for e in es] + [e["endTime"] for e in es]))
    nes = []
    for i, t in enumerate(times):
        if i == 0: continue
        nes.append({
            "startTime": times[i - 1],
            "endTime": t,
            "start": getEventsValue(es, times[i - 1], False),
            "end": getEventsValue(es, t, True)
        })
    es.clear()
    es.extend(nes)

def mergeEvents_move(esx: list[dict], esy: list[dict]):
    times = sorted(set([e["startTime"] for e in esx] + [e["endTime"] for e in esx] + [e["startTime"] for e in esy] + [e["endTime"] for e in esy]))
    nes = []
    for i, t in enumerate(times):
        if i == 0: continue
        nes.append({
            "startTime": times[i - 1],
            "endTime": t,
            "start": getEventsValue(esx, times[i - 1], False),
            "end": getEventsValue(esx, t, True),
            "start2": getEventsValue(esy, times[i - 1], False),
            "end2": getEventsValue(esy, t, True)
        })
    return nes

def convertEvents2Phi(es: list[dict], f: typing.Callable[[float], float]):
    for e in es:
        e["start"] = f(e["start"])
        e["end"] = f(e["end"])
    return es

def convertEvents2Phi_move(es: list[dict], fx: typing.Callable[[float], float], fy: typing.Callable[[float], float]):
    for e in es:
        e["start"] = fx(e["start"])
        e["end"] = fx(e["end"])
        e["start2"] = fy(e["start2"])
        e["end2"] = fy(e["end2"])
    return es

def convertEvents2Phi_speed(es: list[dict], f: typing.Callable[[float], float]):
    for e in es:
        e["value"] = f(e["start"])
        del e["start"], e["end"]
    return es

def getSpeedValue(es: list[dict], t: float):
    for e in es:
        if e["startTime"] <= t < e["endTime"]: return e["value"]
    return 0.0

def getFloorPosition(es: list[dict], t: float):
    if not es: return 0.0
    
    result = 0.0
    for e in es:
        if e["endTime"] <= t:
            result += e["value"] * (e["endTime"] - e["startTime"])
        elif e["startTime"] <= t <= e["endTime"]:
            result += e["value"] * (t - e["startTime"])
            
    if t >= offsetT and es[0]["startTime"] <= offsetT:
        et = min(t, es[0]["endTime"])
        result -= es[0]["value"] * (et - es[0]["startTime"])
    
    return result * globalT

def convertNotes(line: dict, notes: typing.Iterable[dict]):
    nns = []
    for n in notes:
        nns.append({
            "type": {1:1, 2:3, 3:4, 4:2}[n["type"]],
            "time": rt2pt(n["startTime"]),
            "positionX": n["positionX"] / 1350 / 0.05625,
            "speed": n["speed"]
        })
        
        pn = nns[-1]
        
        pn["holdTime"] = rt2pt(n["endTime"]) - pn["time"] if n["endTime"] != n["startTime"] else 0.0
        pn["floorPosition"] = getFloorPosition(line["speedEvents"], pn["time"])
        
        if pn["type"] == 3:
            pn["speed"] = getSpeedValue(line["speedEvents"], pn["time"])
    return nns

for i, line in enumerate(copy.deepcopy(rpec["judgeLineList"])):
    line: dict
    print(f"\rconverting line {i + 1}/{len(rpec["judgeLineList"])} ...", end="")
    
    if line.get("father", -1) != -1:
        first_l = line["eventLayers"][0]
        first_l["moveXEvents"] = first_l.get("moveXEvents", [])
        first_l["moveYEvents"] = first_l.get("moveYEvents", [])
        father_ls = rpec["judgeLineList"][line["father"]]["eventLayers"]
        for layer in father_ls:
            if layer is None: continue
            first_l["moveXEvents"].extend(copy.deepcopy(layer.get("moveXEvents", [])))
            first_l["moveYEvents"].extend(copy.deepcopy(layer.get("moveYEvents", [])))
    
    phil = {
        "bpm": globalBpm,
        "notesAbove": [],
        "notesBelow": [],
        "speedEvents": [],
        "judgeLineMoveEvents": [],
        "judgeLineRotateEvents": [],
        "judgeLineDisappearEvents": []
    }
    isAttachUI = line.get("attachUI", None) is not None
    
    speedEvents = []
    moveXEvents = []
    moveYEvents = []
    rotateEvents = []
    alphaEvents = []
    
    for layer in line["eventLayers"]:
        if layer is None: continue
        
        aes = [layer.get(f"{i}Events", []) for i in ("speed", "moveX", "moveY", "rotate", "alpha")]
        
        for i, es in enumerate(aes):
            if isAttachUI and i == 4: # alpha events
                continue
                
            convertEventsTime(es)
            sortEvents(es)
            fillEvents(es)
            splitEvents(es, i == 0)
            
        speedEvents.extend(aes[0])
        moveXEvents.extend(aes[1])
        moveYEvents.extend(aes[2])
        rotateEvents.extend(aes[3])
        if not isAttachUI: alphaEvents.extend(aes[4])
    
    (*map(mergeEvents, [speedEvents, moveXEvents, moveYEvents, rotateEvents, *((alphaEvents, ) if not isAttachUI else ())]), )
    
    moveEvents = mergeEvents_move(moveXEvents, moveYEvents)
    
    phil["speedEvents"] = convertEvents2Phi_speed(speedEvents, lambda x: x * 120 / 900 / 0.6)
    phil["judgeLineMoveEvents"] = convertEvents2Phi_move(moveEvents, lambda x: (x + 675) / 1350, lambda y: (y + 450) / 900)
    phil["judgeLineRotateEvents"] = convertEvents2Phi(rotateEvents, lambda x: -x)
    phil["judgeLineDisappearEvents"] = convertEvents2Phi(alphaEvents, lambda x: (255 & int(x)) / 255) if not isAttachUI else [{
        "startTime": -inft,
        "endTime": inft,
        "start": 0.0,
        "end": 0.0
    }]
    
    if phil["speedEvents"]: phil["speedEvents"][0]["startTime"] = 0.0
    phil["notesAbove"] = convertNotes(phil, filter(lambda x: x["above"] == 1, line.get("notes", [])))
    phil["notesBelow"] = convertNotes(phil, filter(lambda x: x["above"] != 1, line.get("notes", [])))
    
    phic["judgeLineList"].append(phil)

print("\nconverting finished.")
json.dump(phic, open(argv[2], "w", encoding="utf-8"), ensure_ascii=False)
