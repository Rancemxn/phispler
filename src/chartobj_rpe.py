from __future__ import annotations

import math
import typing
import logging
import random
from dataclasses import dataclass, field

import tool_funcs
import rpe_easing
import const
import tempdir

def _init_events(es: list[LineEvent]):
    aes = []
    for i, e in enumerate(es):
        if i != len(es) - 1:
            ne = es[i + 1]
            if e.endTime.value < ne.startTime.value:
                aes.append(LineEvent(e.endTime, ne.startTime, e.end, e.end, 1, isfill=True))
    es.extend(aes)
    es.sort(key = lambda x: x.startTime.value)
    if es: es.append(LineEvent(es[-1].endTime, Beat(const.INFBEAT, 0, 1), es[-1].end, es[-1].end, 1, isfill=True))

def geteasing_func(t: int):
    try:
        if not isinstance(t, int): t = 1
        t = 1 if t < 1 else (len(rpe_easing.ease_funcs) if t > len(rpe_easing.ease_funcs) else t)
        return rpe_easing.ease_funcs[int(t) - 1]
    except Exception as e:
        logging.warning(f"geteasing_func error: {e}")
        return rpe_easing.ease_funcs[0]

def findevent(events: list[LineEvent|ExtraVar], t: float, timeattr: str = "value") -> typing.Optional[LineEvent|ExtraVar]:
    l, r = 0, len(events) - 1
    
    while l <= r:
        m = (l + r) // 2
        e = events[m]
        st, et = getattr(e.startTime, timeattr), getattr(e.endTime, timeattr)
        if st <= t < et: return e
        elif st > t: r = m - 1
        else: l = m + 1
            
    return None

def split_different_speednotes(notes: list[Note]) -> list[list[Note]]:
    tempmap: dict[int, list[Note]] = {}
    
    for n in notes:
        h = hash((n.speed, n.yOffset))
        if h not in tempmap: tempmap[h] = []
        tempmap[h].append(n)
    
    return list(tempmap.values())
        
@dataclass
class Beat:
    v1: int
    v2: int
    v3: int
    
    secvar: typing.Optional[float] = None # only speed events
    
    def __post_init__(self):
        self.value = self.v1 + (self.v2 / self.v3)
        self._hash = hash(self.value)
    
    def dump(self):
        return [self.v1, self.v2, self.v3]
    
    def __hash__(self) -> int:
        return self._hash
    
    def __repr__(self):
        return f"{self.v1} + {self.v2} / {self.v3} = {self.value}"
    
    __str__ = __repr__
    
@dataclass
class Note:
    type: int
    startTime: Beat
    endTime: Beat
    positionX: float
    above: int
    isFake: int
    speed: float
    yOffset: float
    visibleTime: float
    width: float
    alpha: int
    hitsound: typing.Optional[str]
    
    masterLine: typing.Optional[JudgeLine] = None
    master: typing.Optional[Chart] = None
    clicked: bool = False
    morebets: bool = False
    floorPosition: float = 0.0
    holdLength: float = 0.0
    masterLine: typing.Optional[JudgeLine] = None
    master_index: typing.Optional[int] = None
    nowpos: tuple[float, float] = (-1.0, -1.0)
    nowrotate: float = 0.0
    rotate_add: float = 0.0
    
    state: int = const.NOTE_STATE.MISS
    player_clicked: bool = False
    player_click_offset: float = 0.0
    player_click_sound_played: bool = False
    player_will_click: bool = False
    player_missed: bool = False
    player_badtime: float = float("nan")
    player_holdmiss_time: float = float("inf")
    player_last_testholdismiss_time: float = -float("inf")
    player_holdjudged: bool = False
    player_holdclickstate: int = const.NOTE_STATE.MISS
    player_holdjudged_tomanager: bool = False
    player_holdjudge_tomanager_time: float = float("nan")
    player_judge_safe_used: bool = False
    player_bad_posandrotate: typing.Optional[tuple[tuple[float, float], float]] = None
    
    def __post_init__(self):
        self.phitype = {1:1, 2:3, 3:4, 4:2}[self.type]
        self.type_string = const.TYPE_STRING_MAP[self.phitype]
        self.positionX2 = self.positionX / const.RPE_WIDTH
        self.float_alpha = (255 & int(self.alpha)) / 255
        self.ishold = self.type_string == "Hold"
        self.hitsound_reskey = self.phitype if self.hitsound is None else hash(tuple(map(ord, self.hitsound)))
        self.draworder = const.NOTE_RORDER_MAP[self.phitype]
        self.above = self.above == 1
    
    def init(self, avgBpm: float):
        self.secst = self.master.beat2sec(self.startTime.value, self.masterLine.bpmfactor)
        self.secet = self.master.beat2sec(self.endTime.value, self.masterLine.bpmfactor)
        self.player_holdjudge_tomanager_time = max(self.secst, self.secet - 0.2)
        
        self.floorPosition = self.masterLine.GetFloorPositionByTime(self.secst)
        if self.ishold: self.holdLength = self.masterLine.GetFloorPositionRange(self.secst, self.secet)

        self.effect_times = []
        self.effect_times.append((
            self.secst,
            tool_funcs.newRandomBlocks(),
            self.getNoteClickPos(self.startTime.value)
        ))
        
        if self.ishold:
            bt = 1 / avgBpm * 30
            t = self.secst + bt
            while t <= self.secet:
                self.effect_times.append((
                    t,
                    tool_funcs.newRandomBlocks(),
                    self.getNoteClickPos(self.master.sec2beat(t, self.masterLine.bpmfactor))
                ))
                t += bt
                
        self.player_effect_times = self.effect_times.copy()
        
        self.rotate_add = 0 if self.above else 180
        dub_text = "_dub" if self.morebets else ""
        if not self.ishold:
            self.img_keyname = f"{self.type_string}{dub_text}"
            self.imgname = f"Note_{self.img_keyname}"
        else:
            self.img_keyname = f"{self.type_string}_Head{dub_text}"
            self.imgname = f"Note_{self.img_keyname}"
            
            self.img_body_keyname = f"{self.type_string}_Body{dub_text}"
            self.imgname_body = f"Note_{self.img_body_keyname}"
            
            self.img_end_keyname = f"{self.type_string}_End{dub_text}"
            self.imgname_end = f"Note_{self.img_end_keyname}"
        
    def getNoteClickPos(self, time: float) -> tuple[typing.Callable[[int, int], tuple[float, float]], float]:
        linePos = tool_funcs.conrpepos(*self.masterLine.GetPos(time))
        lineRotate = sum([
            self.masterLine.getEventValue(time, layer.rotateEvents)
            for layer in self.masterLine.eventLayers
        ])
        
        cached: bool = False
        cachedata: typing.Optional[tuple[float, float]] = None
        
        def callback(w: int, h: int):
            nonlocal cached, cachedata
            
            if cached: return cachedata
            cached, cachedata = True, tool_funcs.rotate_point(
                linePos[0] * w, linePos[1] * h,
                lineRotate, self.positionX2 * w
            )
            
            return cachedata
        
        return callback, lineRotate

    def dump(self):
        return {
            "type": self.type,
            "startTime": self.startTime.dump(),
            "endTime": self.endTime.dump(),
            "above": self.above,
            "positionX": self.positionX,
            "alpha": self.alpha,
            "isFake": self.isFake,
            "visibleTime": self.visibleTime,
            "yOffset": self.yOffset
        }
    
    def __eq__(self, value): return self is value

@dataclass
class LineEvent:
    startTime: Beat
    endTime: Beat 
    start: float|str|list[int]
    end: float|str|list[int]
    easingType: int = 1
    easingLeft: float = 0.0
    easingRight: float = 1.0
    
    bezier: int = 0
    bezierPoints: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    
    easingFunc: typing.Callable[[float], float] = rpe_easing.ease_funcs[0]
    
    floorPosition: typing.Optional[float] = None # only speed events have this
    isfill: bool = False
    
    def __post_init__(self):
        self.easingFunc = geteasing_func(self.easingType) if not self.bezier else tool_funcs.createBezierFunction(self.bezierPoints)
        self.easingLeft = max(0.0, min(1.0, self.easingLeft))
        self.easingRight = max(0.0, min(1.0, self.easingRight))
        
        if self.easingLeft != 0.0 or self.easingRight != 1.0:
            self.easingFunc = tool_funcs.createCuttingEasingFunction(self.easingFunc, self.easingLeft, self.easingRight)
    
    def dump(self):
        return {
            "startTime": self.startTime.dump(),
            "endTime": self.endTime.dump(),
            "start": self.start,
            "end": self.end,
            "easingType": self.easingType,
            "easingLeft": self.easingLeft,
            "easingRight": self.easingRight,
            "bezier": self.bezier,
            "bezierPoints": self.bezierPoints
        }
    
@dataclass
class EventLayer:
    speedEvents: list[LineEvent]
    moveXEvents: list[LineEvent]
    moveYEvents: list[LineEvent]
    rotateEvents: list[LineEvent]
    alphaEvents: list[LineEvent]
    
    def __post_init__(self):
        self.speedEvents.sort(key = lambda x: x.startTime.value)
        self.moveXEvents.sort(key = lambda x: x.startTime.value)
        self.moveYEvents.sort(key = lambda x: x.startTime.value)
        self.rotateEvents.sort(key = lambda x: x.startTime.value)
        self.alphaEvents.sort(key = lambda x: x.startTime.value)
        
        _init_events(self.speedEvents)
        _init_events(self.moveXEvents)
        _init_events(self.moveYEvents)
        _init_events(self.rotateEvents)
        _init_events(self.alphaEvents)
    
    def dump(self):
        return {
            "speedEvents": [e.dump() for e in self.speedEvents],
            "moveXEvents": [e.dump() for e in self.moveXEvents],
            "moveYEvents": [e.dump() for e in self.moveYEvents],
            "rotateEvents": [e.dump() for e in self.rotateEvents],
            "alphaEvents": [e.dump() for e in self.alphaEvents]
        }
        
@dataclass
class Extended:
    scaleXEvents: list[LineEvent]
    scaleYEvents: list[LineEvent]
    colorEvents: list[LineEvent]
    textEvents: list[LineEvent]
    gifEvents: list[LineEvent]
    
    def __post_init__(self):
        self.scaleXEvents.sort(key = lambda x: x.startTime.value)
        self.scaleYEvents.sort(key = lambda x: x.startTime.value)
        self.colorEvents.sort(key = lambda x: x.startTime.value)
        self.textEvents.sort(key = lambda x: x.startTime.value)
        self.gifEvents.sort(key = lambda x: x.startTime.value)

        _init_events(self.scaleXEvents)
        _init_events(self.scaleYEvents)
        _init_events(self.colorEvents)
        _init_events(self.textEvents)
        _init_events(self.gifEvents)
    
    def dump(self):
        return {
            "scaleXEvents": [e.dump() for e in self.scaleXEvents],
            "scaleYEvents": [e.dump() for e in self.scaleYEvents],
            "colorEvents": [e.dump() for e in self.colorEvents],
            "textEvents": [e.dump() for e in self.textEvents],
            "gifEvents": [e.dump() for e in self.gifEvents]
        }

@dataclass
class ControlItem:
    sval: float
    tval: float
    easing: int
    easingFunc: typing.Callable[[float], float] = rpe_easing.ease_funcs[0]
    next: typing.Optional[ControlItem] = None
    
    def __post_init__(self):
        self.easingFunc = geteasing_func(self.easing)

@dataclass
class ControlEvents:
    alphaControls: list[ControlItem]
    posControls: list[ControlItem]
    sizeControls: list[ControlItem]
    yControls: list[ControlItem]
    
    def __post_init__(self):
        self.alphaControls.sort(key = lambda x: x.sval)
        self.posControls.sort(key = lambda x: x.sval)
        self.sizeControls.sort(key = lambda x: x.sval)
        self.yControls.sort(key = lambda x: x.sval)
        self._inite(self.alphaControls)
        self._inite(self.posControls)
        self._inite(self.sizeControls)
        self._inite(self.yControls)
    
    def _inite(self, es: list[ControlItem]):
        for i, e in enumerate(es):
            if i != len(es) - 1:
                e.next = es[i + 1]
    
    def _gtvalue(self, s: float, es: list[ControlItem], default: float = 1.0):
        for e in es:
            if e.next is None:
                return e.sval
            if e.sval <= s < e.next.sval:
                return e.easingFunc((s - e.sval) / (e.next.sval - e.sval)) * (e.next.tval - e.tval) + e.tval
        return default
    
    def gtvalue(self, x: float):
        return (
            self._gtvalue(x, self.alphaControls, 1.0),
            self._gtvalue(x, self.posControls, 0.0),
            self._gtvalue(x, self.sizeControls, 1.0),
            self._gtvalue(x, self.yControls, 0.0)
        )

@dataclass
class MetaData:
    RPEVersion: int
    offset: int
    name: str
    id: str
    song: str
    background: str
    composer: str
    charter: str
    level: str
    
    def dump(self):
        return {
            "RPEVersion": self.RPEVersion,
            "background": self.background,
            "charter": self.charter,
            "composer": self.composer,
            "id": self.id,
            "level": self.level,
            "name": self.name,
            "offset": self.offset,
            "song": self.song
        }

@dataclass
class BPMEvent:
    startTime: Beat
    bpm: float
    
    def dump(self):
        return {
            "bpm": self.bpm,
            "startTime": self.startTime.dump()
        }

@dataclass
class JudgeLine:
    isCover: int
    Texture: str
    attachUI: typing.Optional[str]
    eventLayers: list[EventLayer]
    extended: typing.Optional[Extended]
    notes: list[Note]
    bpmfactor: float
    father: int|JudgeLine # in other typing.Any, __post_init__ change this value to a line
    zOrder: int
    isGif: bool
    
    controlEvents: ControlEvents
    
    master: typing.Optional[Chart] = None
    index: int = -1
    textureSize: tuple[int|float, int|float] = (0.0, 0.0)
    effectNotes: typing.Optional[list[Note]] = None
    renderNotes: typing.Optional[list[list[Note]]] = None
    
    def __post_init__(self):
        for note in self.notes:
            note.masterLine = self
    
    def setChartMaster(self):
        for note in self.notes:
            note.master = self.master
        
    def getEventValue(self, t: float, es: list[LineEvent], default: float|int|str|tuple[float] = 0.0):
        if not es: return default
        
        e = findevent(es, t)
        
        if e is None:
            if t >= es[-1].endTime.value:
                default = es[-1].end
                if isinstance(default, list): default = tuple(default)
            return default
        
        if isinstance(e.start, float|int):
            return tool_funcs.easing_interpolation(t, e.startTime.value, e.endTime.value, e.start, e.end, e.easingFunc)
        elif isinstance(e.start, str):
            return tool_funcs.rpe_text_tween(e.start, e.end, tool_funcs.easing_interpolation(t, e.startTime.value, e.endTime.value, 0.0, 1.0, e.easingFunc), e.isfill)
        elif isinstance(e.start, list):
            return tuple(tool_funcs.easing_interpolation(t, e.startTime.value, e.endTime.value, e.start[i], e.end[i], e.easingFunc) for i in range(len(e.start)))
    
    def GetPos(self, t: float) -> tuple[float, float]:
        linePos = (
            sum(self.getEventValue(t, layer.moveXEvents) for layer in self.eventLayers),
            sum(self.getEventValue(t, layer.moveYEvents) for layer in self.eventLayers)
        )
            
        if self.father != -1:
            try:
                sec = self.master.beat2sec(t, self.bpmfactor)
                
                fatherBeat = self.master.sec2beat(sec, self.father.bpmfactor)
                fatherPos = self.father.GetPos(fatherBeat)
                fatherRotate = sum(self.father.getEventValue(fatherBeat, layer.rotateEvents) for layer in self.father.eventLayers)
                
                if fatherRotate == 0.0:
                    return list(map(lambda v1, v2: v1 + v2, fatherPos, linePos))
                
                return list(map(lambda v1, v2: v1 + v2, fatherPos, 
                    tool_funcs.rotate_point(
                        0.0, 0.0,
                        90 - (math.degrees(math.atan2(*linePos)) + fatherRotate),
                        tool_funcs.getLineLength(*linePos, 0.0, 0.0)
                    )
                ))
            except IndexError:
                pass
            
        return linePos

    def GetState(self, t: float, defaultColor: tuple[int, int, int]) -> tuple[tuple[float, float], float, float, tuple[float, float, float], float, float, typing.Optional[str]]:
        "linePos, lineAlpha, lineRotate, lineColor, lineScaleX, lineScaleY, lineText"
        
        lineAlpha = sum(self.getEventValue(t, layer.alphaEvents) for layer in self.eventLayers) if t >= 0.0 or self.attachUI is not None else -255
        lineRotate = sum(self.getEventValue(t, layer.rotateEvents) for layer in self.eventLayers)
        lineScaleX = self.getEventValue(t, self.extended.scaleXEvents, 1.0) if lineAlpha > 0.0 and self.extended else 1.0
        lineScaleY = self.getEventValue(t, self.extended.scaleYEvents, 1.0) if lineAlpha > 0.0 and self.extended else 1.0
        lineText = self.getEventValue(t, self.extended.textEvents, "") if lineAlpha > 0.0 and self.extended and self.extended.textEvents else None
        lineColor = (
            (255, 255, 255)
            if self.Texture != "line.png" or self.attachUI or (self.extended and self.extended.textEvents) else
            defaultColor
        )
        linePos = self.GetPos(t)
        
        if lineAlpha > 0.0 and self.extended:
            lineColor = self.getEventValue(t, self.extended.colorEvents, lineColor)
        
        return tool_funcs.conrpepos(*linePos), lineAlpha / 255, lineRotate, lineColor, lineScaleX, lineScaleY, lineText
    
    def GetEventRawFloorPosition(self, e: LineEvent, l: float, r: float) -> float:
        st, et = e.startTime.secvar, e.endTime.secvar
        if r < st or l > et: return 0.0
        v1, v2 = max(st, l), min(et, r)
        
        if e.start == e.end:
            return (v2 - v1) * e.start
        else:
            s1 = tool_funcs.linear_interpolation(v1, st, et, e.start, e.end)
            s2 = tool_funcs.linear_interpolation(v2, st, et, e.start, e.end)
            return (v2 - v1) * (s1 + s2) / 2
    
    def GetFloorPositionRange(self, l: float, r: float):
        yl, yr = l, r
        l, r = sorted((l, r))
                    
        return (self.GetFloorPositionByTime(r) - self.GetFloorPositionByTime(l)) * (-1.0 if yl > yr else 1.0)
    
    def GetFloorPositionByTime(self, t: float):
        fp = 0.0
        
        for layer in self.eventLayers:
            if not layer.speedEvents: continue
            e = findevent(layer.speedEvents, t, "secvar")
            
            if e is None:
                if t >= layer.speedEvents[-1].endTime.secvar:
                    e = layer.speedEvents[-1]
                    t = e.endTime.secvar
                else:
                    continue
                
            fp += e.floorPosition + self.GetEventRawFloorPosition(e, e.startTime.secvar, t)
        
        return fp * 120 / const.RPE_HEIGHT

    def dump(self):
        return {
            "Texture": self.Texture,
            "bpmfactor": self.bpmfactor,
            "father": self.father if isinstance(self.father, int) else self.master.judgeLineList.index(self.father),
            "isCover": self.isCover,
            "zOrder": self.zOrder,
            "eventLayers": [i.dump() for i in self.eventLayers],
            "extended": self.extended.dump(),
            "notes": [i.dump() for i in self.notes],
        }
    
    def __hash__(self) -> int:
        return id(self)
    
    def __eq__(self, oth: typing.Any) -> bool:
        return self is oth

class PPLMRPE_Proxy(tool_funcs.PPLM_ProxyBase):
    def __init__(self, cobj: Chart): self.cobj = cobj
    
    def get_lines(self): return self.cobj.judgeLineList
    def get_all_pnotes(self): return self.cobj.playerNotes
    def remove_pnote(self, n: Note): self.cobj.playerNotes.remove(n)
    
    def nproxy_stime(self, n: Note): return n.secst
    def nproxy_etime(self, n: Note): return n.secet
    def nproxy_hcetime(self, n: Note): return n.player_holdjudge_tomanager_time
    
    def nproxy_typein(self, n: Note, ts: tuple[int]): return n.phitype in ts
    def nproxy_typeis(self, n: Note, t: int): return n.phitype == t
    def nproxy_phitype(self, n: Note): return n.phitype
    
    def nproxy_nowpos(self, n: Note): return n.nowpos
    def nproxy_nowrotate(self, n: Note) -> float: return n.nowrotate
    def nproxy_effects(self, n: Note): return n.player_effect_times
    
    def nproxy_get_pclicked(self, n: Note): return n.player_clicked
    def nproxy_set_pclicked(self, n: Note, state: bool): n.player_clicked = state
    
    def nproxy_get_wclick(self, n: Note): return n.player_will_click
    def nproxy_set_wclick(self, n: Note, state: bool): n.player_will_click = state
    
    def nproxy_get_pclick_offset(self, n: Note): return n.player_click_offset
    def nproxy_set_pclick_offset(self, n: Note, offset: float): n.player_click_offset = offset
    
    def nproxy_get_ckstate(self, n: Note): return n.state
    def nproxy_set_ckstate(self, n: Note, state: int): n.state = state
    def nproxy_get_ckstate_ishit(self, n: Note): return n.state in (const.NOTE_STATE.PERFECT, const.NOTE_STATE.GOOD)
    
    def nproxy_get_cksound_played(self, n: Note): return n.player_click_sound_played
    def nproxy_set_cksound_played(self, n: Note, state: bool): n.player_click_sound_played = state
    
    def nproxy_get_missed(self, n: Note): return n.player_missed
    def nproxy_set_missed(self, n: Note, state: bool): n.player_missed = state
    
    def nproxy_get_holdjudged(self, n: Note): return n.player_holdjudged
    def nproxy_set_holdjudged(self, n: Note, state: bool): n.player_holdjudged = state
    
    def nproxy_get_holdjudged_tomanager(self, n: Note): return n.player_holdjudged_tomanager
    def nproxy_set_holdjudged_tomanager(self, n: Note, state: bool): n.player_holdjudged_tomanager = state
    
    def nproxy_get_last_testholdmiss_time(self, n: Note): return n.player_last_testholdismiss_time
    def nproxy_set_last_testholdmiss_time(self, n: Note, time: float): n.player_last_testholdismiss_time = time
    
    def nproxy_get_safe_used(self, n: Note): return n.player_judge_safe_used
    def nproxy_set_safe_used(self, n: Note, state: bool): n.player_judge_safe_used = state
    
    def nproxy_get_holdclickstate(self, n: Note): return n.player_holdclickstate
    def nproxy_set_holdclickstate(self, n: Note, state: int): n.player_holdclickstate = state
    
    def nproxy_get_pbadtime(self, n: Note): return n.player_badtime
    def nproxy_set_pbadtime(self, n: Note, time: float): n.player_badtime = time
    
@dataclass
class Chart:
    META: MetaData
    BPMList: list[BPMEvent]
    judgeLineList: list[JudgeLine]
    isPec: bool
    
    combotimes: typing.Optional[list[float]] = None
    extra: typing.Optional[Extra] = None
    
    def __post_init__(self):
        self.BPMList = list(filter(lambda x: x.bpm != 0.0, self.BPMList))
        self.BPMList.sort(key=lambda x: x.startTime.value)
        self.combotimes = []
        
        try: avgBpm = sum([e.bpm for e in self.BPMList]) / len(self.BPMList)
        except ZeroDivisionError: avgBpm = 140.0

        def morebets_note(note: list[Note]):
            times = {}
            
            for i in note:
                if i.startTime.value not in times: times[i.startTime.value] = 1
                else: times[i.startTime.value] += 1
                
            for i in note:
                if times[i.startTime.value] > 1:
                    i.morebets = True

        morebets_note([note for line in self.judgeLineList for note in line.notes])
        
        for lindex, line in enumerate(self.judgeLineList):
            line.master = self
            line.index = lindex
            line.setChartMaster()
            
            if line.father != -1:
                line.father = self.judgeLineList[line.father]
            
            if line.bpmfactor == 0.0:
                line.bpmfactor = 1.0
                
            for layer in line.eventLayers:
                fp = 0.0
                for e in layer.speedEvents:
                    e.startTime.secvar = self.beat2sec(e.startTime.value, line.bpmfactor)
                    e.endTime.secvar = self.beat2sec(e.endTime.value, line.bpmfactor)
                    e.floorPosition = fp
                    fp += line.GetEventRawFloorPosition(e, e.startTime.secvar, e.endTime.secvar)
            
            for i, note in enumerate(line.notes):
                note.master_index = i
                note.masterLine = line
                note.init(avgBpm)
                if not note.isFake:
                    self.combotimes.append(note.secst if not note.ishold else max(note.secst, note.secet - 0.2))
            
            line.notes.sort(key=lambda x: x.startTime.value)
            line.effectNotes = [i for i in line.notes if not i.isFake]
            line.renderNotes = (
                split_different_speednotes([i for i in line.notes if i.above])
                + split_different_speednotes([i for i in line.notes if not i.above])
            )
        
        self.note_num = len([i for line in self.judgeLineList for i in line.notes if not i.isFake])
        self.combotimes.sort()
        self.playerNotes = sorted([i for line in self.judgeLineList for i in line.notes if not i.isFake], key = lambda x: x.secst)
        self.sortedLines = sorted(self.judgeLineList, key=lambda x: x.zOrder)
    
    def getCombo(self, t: float):
        l, r = 0, len(self.combotimes)
        while l < r:
            m = (l + r) // 2
            if self.combotimes[m] < t: l = m + 1
            else: r = m
        return l
    
    def sec2beat(self, t: float, bpmfactor: float, BPMList: typing.Optional[list[BPMEvent]] = None):
        if BPMList is None:
            BPMList = self.BPMList
        
        if len(BPMList) == 1:
            return t / (60 / (BPMList[0].bpm / bpmfactor))
            
        beat = 0.0
        for i, e in enumerate(BPMList):
            bpmv = e.bpm / bpmfactor
            if i != len(BPMList) - 1:
                et_beat = BPMList[i + 1].startTime.value - e.startTime.value
                et_sec = et_beat * (60 / bpmv)
                
                if t >= et_sec:
                    beat += et_beat
                    t -= et_sec
                else:
                    beat += t / (60 / bpmv)
                    break
            else:
                beat += t / (60 / bpmv)
        return beat
    
    def beat2sec(self, t: float, bpmfactor: float, BPMList: typing.Optional[list[BPMEvent]] = None):
        if BPMList is None:
            BPMList = self.BPMList
        
        if len(BPMList) == 1:
            return t * (60 / (BPMList[0].bpm / bpmfactor))
            
        sec = 0.0
        for i, e in enumerate(BPMList):
            bpmv = e.bpm / bpmfactor
            if i != len(BPMList) - 1:
                et_beat = BPMList[i + 1].startTime.value - e.startTime.value
                
                if t >= et_beat:
                    sec += et_beat * (60 / bpmv)
                    t -= et_beat
                else:
                    sec += t * (60 / bpmv)
                    break
            else:
                sec += t * (60 / bpmv)
        return sec
    
    def dump(self):
        return {
            "META": self.META.dump(),
            "BPMList": [i.dump() for i in self.BPMList],
            "judgeLineList": [i.dump() for i in self.judgeLineList],
        }

    def __hash__(self) -> int:
        return id(self)
    
    def __eq__(self, oth) -> bool:
        if isinstance(oth, JudgeLine):
            return self is oth
        return False

@dataclass
class ExtraVar:
    startTime: Beat
    endTime: Beat
    start: float|list[float]
    end: float|list[float]
    easingType: int
    
    def __post_init__(self):
        self.easingFunc = geteasing_func(self.easingType)
    
@dataclass
class ExtraEffect:
    start: Beat
    end: Beat
    shader: str
    global_: bool
    vars: dict[str, list[ExtraVar]]
    
    def _init_events(self, es: list[ExtraVar]):
        aes = []
        for i, e in enumerate(es):
            if i != len(es) - 1:
                ne = es[i + 1]
                if e.endTime.value < ne.startTime.value:
                    aes.append(ExtraVar(e.endTime, ne.startTime, e.end, e.end, 1))
        es.extend(aes)
        es.sort(key = lambda x: x.startTime.value)
        if es: es.append(ExtraVar(es[-1].endTime, Beat(31250000, 0, 1), es[-1].end, es[-1].end, 1))
        
    def __post_init__(self):
        for v in self.vars.values():
            self._init_events(v)

@dataclass
class ExtraVideo:
    path: str
    time: Beat
    scale: typing.Literal["cropCenter", "inside", "fit"]
    alpha: list[ExtraVar]
    dim: list[ExtraVar]
    
    def __post_init__(self):
        if self.scale not in ("cropCenter", "inside", "fit"):
            logging.warning(f"Invalid scale type {self.scale} for video {self.path}")
            self.scale = "cropCenter"
        
        self.h264data, self.size = tool_funcs.video2h264(f"{tempdir.createTempDir()}/{self.path}")
        self.unqique_id = f"extra_video_{random.randint(0, 2 << 31)}"

@dataclass
class Extra:
    bpm: list[BPMEvent]
    effects: list[ExtraEffect]
    videos: list[ExtraVideo]
    
    def getShaderEffect(self, t: float, isglobal: bool):
        beat = Chart.sec2beat(None, t, 1.0, self.bpm)
        result = []
        
        for e in self.effects:
            if e.global_ != isglobal: continue
            if e.start.value <= beat < e.end.value:
                values = {}
                
                for k, v in e.vars.items():
                    ev = JudgeLine.getEventValue(None, beat, v, v[0].start if v else None)
                    if ev is not None: values.update({k: ev})
                    
                if e.shader in const.EXTRA_DEFAULTS.keys():
                    defvs: dict = const.EXTRA_DEFAULTS[e.shader].copy()
                    defvs.update(values)
                    values = defvs
                    
                result.append((e.shader, values))
                
        return result
    
    def getVideoEffect(self, t: float) -> list[tuple[ExtraVideo, float]]:
        beat = Chart.sec2beat(None, t, 1.0, self.bpm)
        result = []
        
        for video in self.videos:
            if video.time.value <= beat:
                result.append((video, t - Chart.beat2sec(None, video.time.value, 1.0, self.bpm)))
        
        return result
