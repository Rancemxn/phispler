from __future__ import annotations

import typing
import logging
import math
from dataclasses import dataclass, field

import const
import rpe_easing
import tool_funcs
import chartobj_rpe

type eventValueType = float|str|tuple[float, float, float]

def _init_events(es: list[LineEvent], *, is_speed: bool = False):
    if not es: return
    
    es.sort(key = lambda e: e.startTime)
    
    aes = []
    for i, e in enumerate(es):
        if i != len(es) - 1:
            ne = es[i + 1]
            if e.endTime < ne.startTime:
                aes.append(LineEvent(
                    startTime = e.endTime,
                    endTime = ne.startTime,
                    start = e.end,
                    end = ne.start,
                    isFill = True
                ))
            elif e.endTime > ne.startTime:
                logging.warning(f"Event overlap: {e} {ne}")
    
    es.extend(aes)
    es.sort(key = lambda e: e.startTime)
    es.append(LineEvent(
        startTime = es[-1].endTime,
        endTime = es[-1].endTime + const.INFBEAT,
        start = es[-1].end,
        end = es[-1].end,
        isFill = True
    ))
    
    if not is_speed:
        es.insert(0, LineEvent(
            startTime = -const.INFBEAT,
            endTime = es[0].startTime,
            start = es[0].start,
            end = es[0].start,
            isFill = True
        ))
    
    if is_speed:
        fp = 0.0
        for e in es:
            e.floorPosotion = fp
            fp += (e.start + e.end) * (e.endTime - e.startTime) / 2

def findevent(es: list[LineEvent], t: float):
    if not es:
        return None
    
    l, r = 0, len(es) - 1
    
    while l <= r:
        m = (l + r) // 2
        e = es[m]
        st, et = e.startTime, e.endTime
        if st <= t < et: return e
        elif st > t: r = m - 1
        else: l = m + 1
    
    return es[-1] if t >= es[-1].endTime else None

def split_notes(notes: list[Note]) -> list[list[Note]]:
    tempmap: dict[int, list[Note]] = {}
    
    for n in notes:
        h = hash((n.speed, n.yOffset, n.isAbove))
        if h not in tempmap: tempmap[h] = []
        tempmap[h].append(n)
    
    return list(tempmap.values())

class ChartFormat:
    unset = object()
    phi = object()
    rpe = object()
    pec = object()
    pbc = object()
    
    notetype_map: dict[object, dict[int, int]] = {
        phi: {1: 1, 2: 2, 3: 3, 4: 4}, # standard
        rpe: ...
    }
    
    @staticmethod
    def load_phi(data: dict):
        def _time_coverter(json_line: dict, t: float):
            return t * (1.875 / json_line.get("bpm", 140.0))
        
        def _pos_coverter_x(x: float):
            return x * const.PGR_UW
        
        def _pos_coverter_y(y: float):
            return y * const.PGR_UH
        
        def _put_note(*, json_line: dict, line: JudgeLine, json_note: dict, isAbove: bool):
            if not isinstance(json_note, dict):
                logging.warning(f"Invalid note type: {type(json_note)}")
                return
            
            note_type = ChartFormat.notetype_map[result.type].get(json_note.get("type", 1), const.NOTE_TYPE.TAP)
            speed = json_note.get("speed", 0.0)
            
            note = Note(
                type = note_type,
                time = _time_coverter(json_line, json_note.get("time", 0.0)),
                holdTime = _time_coverter(json_line, json_note.get("holdTime", 0.0)),
                positionX = _pos_coverter_x(json_note.get("positionX", 0.0)),
                speed = _pos_coverter_y(speed) if note_type == const.NOTE_TYPE.HOLD else speed,
                isAbove = isAbove
            )
            
            line.notes.append(note)
        
        def _put_events(es: list[LineEvent], json_es: list[dict], converter: typing.Callable[[float], float], startkey: str = "start", endkey: str = "end"):
            for json_e in json_es:
                if not isinstance(json_e, dict):
                    logging.warning(f"Invalid event type: {type(json_e)}")
                    continue
                
                es.append(LineEvent(
                    startTime = _time_coverter(json_line, json_e.get("startTime", 0.0)),
                    endTime = _time_coverter(json_line, json_e.get("endTime", 0.0)),
                    start = converter(json_e.get(startkey, 0.0)),
                    end = converter(json_e.get(endkey, 0.0))
                ))
        
        formatVersion = data.get("formatVersion", 0)
        if formatVersion not in (1, 2, 3):
            logging.warning(f"Unsupported phi chart format version: {formatVersion}")
            formatVersion = 3
        
        if formatVersion == 2:
            data = tool_funcs.SaveAsNewFormat(data)
        
        result = CommonChart()
        result.type = ChartFormat.phi
        
        result.offset = data.get("offset", 0.0)
        result.options.lineWidthUnit = (0.0, 5.76)
        result.options.lineHeightUnit = (0.0, const.LINEWIDTH.PHI)
        
        for line_i, json_line in enumerate(data.get("judgeLineList", [])):
            json_line: dict
            
            line = JudgeLine()
            line.index = line_i
            line.bpms.append(BPMEvent(0.0, json_line.get("bpm", 140.0)))
            
            for i, json_note in enumerate(json_line.get("notesAbove", [])):
                _put_note(
                    json_line = json_line,
                    line = line,
                    json_note = json_note,
                    isAbove = True
                )
                line.notes[-1].master_index = i
            
            for i, json_note in enumerate(json_line.get("notesBelow", [])):
                _put_note(
                    json_line = json_line,
                    line = line,
                    json_note = json_note,
                    isAbove = False
                )
                line.notes[-1].master_index = i
            
            if formatVersion == 1:
                for json_e in json_line.get("judgeLineMoveEvents", []):
                    json_e["start"], json_e["start2"] = tool_funcs.unpack_pos(json_e.get("start", 0))
                    json_e["end"], json_e["end2"] = tool_funcs.unpack_pos(json_e.get("end", 0))
            
            elayer = EventLayerItem()
            _put_events(elayer.alphaEvents, json_line.get("judgeLineDisappearEvents", []), lambda x: x)
            _put_events(elayer.moveXEvents, json_line.get("judgeLineMoveEvents", []), lambda x: x)
            _put_events(elayer.moveYEvents, json_line.get("judgeLineMoveEvents", []), lambda y: 1.0 - y, "start2", "end2")
            _put_events(elayer.rotateEvents, json_line.get("judgeLineRotateEvents", []), lambda r: -r)
            _put_events(elayer.speedEvents, json_line.get("speedEvents", []), _pos_coverter_y, "value", "value")
            line.eventLayers.append(elayer)
            
            result.lines.append(line)
            
        result.init()
        return result
    
    @staticmethod
    def load_rpe(data: dict):
        result = CommonChart()
        
        result.init()
        return result
    
    @staticmethod
    def load_pec(data: str):
        return ChartFormat.load_rpe(tool_funcs.pec2rpe(data))

@dataclass
class MemEq:
    def __hash__(self):
        return id(self)
    
    def __eq__(self, value: typing.Any):
        return self is value

@dataclass
class Note(MemEq):
    type: int
    time: float
    holdTime: float
    positionX: float
    speed: float
    
    isAbove: bool
    isFake: bool = False
    yOffset: float = 0.0
    visibleTime: typing.Optional[float] = None
    width: float = 1.0
    alpha: float = 1.0
    hitsound: typing.Optional[str] = None
    
    def __post_init__(self):
        self.ishold = self.type == const.NOTE_TYPE.HOLD
        self.isontime = False
        self.morebets = False
        self.holdEndTime = self.time + self.holdTime
        self.giveComboTime = self.time if not self.ishold else max(self.time, self.holdEndTime - 0.2)
        self.hitsound_reskey = self.type if self.hitsound is None else hash(tuple(map(ord, self.hitsound)))
        self.type_string = const.TYPE_STRING_MAP[self.type]
        self.rotate_add = 0 if self.isAbove else 180
        self.draworder = const.NOTE_RORDER_MAP[self.type]
        
        self.master_index = -1
        self.nowpos = (0.0, 0.0)
        self.nowrotate = 0.0
        
        self.state = const.NOTE_STATE.MISS
        self.player_clicked = False
        self.player_missed = False
    
    def init(self, master: JudgeLine):
        self.master = master
        self.floorPosition = self.master.getFloorPosition(self.time)
        self.holdLength = (
            self.master.getRangeFloorPosition(self.time, self.time + self.holdTime)
            if not self.master.master.options.holdIndependentSpeed
            else self.holdTime * self.speed
        ) if self.ishold else 0.0
        
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

@dataclass
class LineEvent(MemEq):
    startTime: float
    endTime: float
    start: eventValueType
    end: eventValueType
    ease: typing.Callable[[float], float] = rpe_easing.ease_funcs[0]
    
    isFill: bool = False
    floorPosotion: typing.Optional[float] = None # only for speed event
    
    def __post_init__(self):
        if isinstance(self.start, int|float):
            self.get = lambda t: tool_funcs.easing_interpolation(t, self.startTime, self.endTime, self.start, self.end, self.ease)
        elif isinstance(self.start, str):
            self.get = lambda t: tool_funcs.rpe_text_tween(self.start, self.end, tool_funcs.easing_interpolation(t, 0.0, 1.0, 0.0, 1.0, self.ease), self.isFill)
        elif isinstance(self.start, typing.Iterable):
            self.get = lambda t: tuple(tool_funcs.easing_interpolation(t, self.startTime, self.endTime, self.start[i], self.end[i], self.ease) for i in range(len(self.start)))
        else:
            raise ValueError(f"Invalid event value type: {type(self.start)}")
    
    def speed_get(self, t: float):
        return (t - self.startTime) * (self.start + self.get(t)) / 2

@dataclass
class EventLayerItem(MemEq):
    alphaEvents: list[LineEvent] = field(default_factory=list)
    moveXEvents: list[LineEvent] = field(default_factory=list)
    moveYEvents: list[LineEvent] = field(default_factory=list)
    rotateEvents: list[LineEvent] = field(default_factory=list)
    speedEvents: list[LineEvent] = field(default_factory=list)
    
    def init(self):
        _init_events(self.alphaEvents)
        _init_events(self.moveXEvents)
        _init_events(self.moveYEvents)
        _init_events(self.rotateEvents)
        _init_events(self.speedEvents, is_speed=True)

@dataclass
class ExtendEventsItem(MemEq):
    colorEvents: list[LineEvent] = field(default_factory=list)
    scaleXEvents: list[LineEvent] = field(default_factory=list)
    scaleYEvents: list[LineEvent] = field(default_factory=list)
    textEvents: list[LineEvent] = field(default_factory=list)
    gifEvents: list[LineEvent] = field(default_factory=list)
    
    def init(self):
        _init_events(self.colorEvents)
        _init_events(self.scaleXEvents)
        _init_events(self.scaleYEvents)
        _init_events(self.textEvents)
        _init_events(self.gifEvents, is_speed=True)

@dataclass
class BPMEvent(MemEq):
    time: float
    bpm: float

@dataclass
class JudgeLine(MemEq):
    bpms: list[BPMEvent] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    eventLayers: list[EventLayerItem] = field(default_factory=list)
    extendEvents: ExtendEventsItem = field(default_factory=ExtendEventsItem)
    father: typing.Optional[JudgeLine]|int = None
    
    isTextureLine: bool = False
    isGifLine: bool = False
    texture: typing.Optional[str] = None
    
    isAttachUI: bool = False
    attachUI: typing.Optional[str] = None
    
    enableCover: bool = True
    
    def __post_init__(self):
        self.playingFloorPosition = 0.0
        self.index = -1
    
    def init(self, master: CommonChart):
        self.master = master
        
        if self.father is not None:
            self.father = master.lines[self.father]
        
        for el in self.eventLayers:
            el.init()
        
        self.extendEvents.init()
        
        for note in self.notes:
            note.init(self)
        
        self.renderNotes = split_notes(self.notes)
    
    def getFloorPosition(self, t: float):
        fp = 0.0
        
        for el in self.eventLayers:
            e = findevent(el.speedEvents, t)
            if e is not None:
                fp += e.floorPosotion + e.speed_get(t)
        
        return fp
    
    def getRangeFloorPosition(self, s: float, e: float):
        return self.getFloorPosition(e) - self.getFloorPosition(s)

    def getEventsValue(self, es: list[LineEvent], t: float, default: float = 0.0):
        e = findevent(es, t)
        return e.get(t) if e is not None else default
    
    def getPos(self, t: float):
        linePos = (
            sum(self.getEventsValue(el.moveXEvents, t) for el in self.eventLayers),
            sum(self.getEventsValue(el.moveYEvents, t) for el in self.eventLayers)
        )
        
        if self.father is not None:
            fatherPos = self.father.getPos(t)
            fatherRotate = sum(self.father.getEventsValue(el.rotateEvents, t) for el in self.father.eventLayers)
            
            if fatherRotate == 0.0:
                return list(map(lambda v1, v2: v1 + v2, fatherPos, linePos))
            
            return list(map(lambda v1, v2: v1 + v2, fatherPos,
                tool_funcs.rotate_point(
                    0.0, 0.0,
                    90 - (math.degrees(math.atan2(*linePos)) + fatherRotate),
                    tool_funcs.getLineLength(*linePos, 0.0, 0.0)
                )
            ))
        
        return linePos
    
    def getState(self, t: float, defaultColor: tuple[int, int, int]):
        lineAlpha = sum(self.getEventsValue(el.alphaEvents, t) for el in self.eventLayers) if t >= 0.0 or self.attachUI is not None else 0.0
        lineRotate = sum(self.getEventsValue(el.rotateEvents, t) for el in self.eventLayers)
        lineScaleX = self.getEventsValue(self.extendEvents.scaleXEvents, t, 1.0) if lineAlpha > 0.0 else 1.0
        lineScaleY = self.getEventsValue(self.extendEvents.scaleYEvents, t, 1.0) if lineAlpha > 0.0 else 1.0
        lineText = self.getEventsValue(t, self.extendEvents.textEvents, "") if lineAlpha > 0.0 and self.extendEvents.textEvents else None
        lineColor = (
            (255, 255, 255)
            if (
                self.texture is not None or
                self.attachUI is not None or
                self.extendEvents.textEvents
            ) else
            defaultColor
        )
        linePos = self.getPos(t)
        
        if lineAlpha > 0.0 and self.extendEvents.colorEvents:
            lineColor = self.getEventsValue(self.extendEvents.colorEvents, t, lineColor)
        
        return (
            self.master.options.posConverter(linePos),
            lineAlpha,
            lineRotate,
            
            lineScaleX,
            lineScaleY,
            lineText,
            lineColor
        )
    
    def sec2beat(self, t: float):
        if len(self.bpms) == 1:
            return t / (60 / self.bpms[0].bpm)
        
        beat = 0.0
        for i, e in enumerate(self.bpms):
            if i != len(self.bpms) - 1:
                et_beat = self.bpms[i + 1].time - e.time
                et_sec = et_beat * (60 / e.bpm)
                
                if t >= et_sec:
                    brat += et_beat
                    t -= et_sec
                else:
                    beat += t / (60 / e.bpm)
                    break
            else:
                beat += t / (60 / e.bpm)
        
        return beat
    
    def beat2sec(self, t: float):
        if len(self.bpms) == 1:
            return t * (60 / self.bpms[0].bpm)

        sec = 0.0
        for i, e in enumerate(self.bpms):
            if i != len(self.bpms) - 1:
                et_beat = self.bpms[i + 1].time - e.time
                
                if t >= et_beat:
                    sec += et_beat * (60 / e.bpm)
                    t -= et_beat
                else:
                    sec += t * (60 / e.bpm)
                    break
            else:
                sec += t * (60 / e.bpm)

        return sec

@dataclass
class CommonChartOptions:
    holdIndependentSpeed: bool = True
    holdCoverAtHead: bool = True
    rpeVersion: int = -1
    alwaysLineOpenAnimation: bool = True
    
    lineWidthUnit: tuple[float, float] = (0.0, 0.0)
    lineHeightUnit: tuple[float, float] = (0.0, 0.0)
    
    posConverter: typing.Callable[[tuple[float, float]], tuple[float, float]] = lambda pos: pos
    
    res_ext_song: typing.Optional[str] = None
    res_ext_background: typing.Optional[str] = None
    
    meta_ext_name: typing.Optional[str] = None
    meta_ext_composer: typing.Optional[str] = None
    meta_ext_level: typing.Optional[str] = None
    meta_ext_charter: typing.Optional[str] = None

@dataclass
class CommonChart:
    offset: float = 0.0
    lines: list[JudgeLine] = field(default_factory=list)
    extra: typing.Optional[chartobj_rpe.Extra] = None
    
    options: CommonChartOptions = field(default_factory=CommonChartOptions)
    type: object = field(default=lambda: ChartFormat.unset)
    
    def __post_init__(self):
        self.combotimes = []
    
    def init(self):
        self.all_notes = [j for i in self.lines for j in i.notes]
        self.all_notes.sort(key=lambda note: note.time)
        
        self.playerNotes = [i for i in self.all_notes if not i.isFake]
        self.note_num = len(self.playerNotes)
        
        self.checkMorebets()
        self.initCombotimes()
        
        for line in self.lines:
            line.init(self)
    
    def checkMorebets(self):
        last_note = None
        for note in self.all_notes:
            if last_note is not None and last_note.time == note.time:
                last_note.morebets = True
                note.morebets = True
            
            last_note = note
    
    def initCombotimes(self):
        self.combotimes.extend(note.giveComboTime for note in self.all_notes if not note.isFake)
    
    def getCombo(self, t: float):
        l, r = 0, len(self.combotimes)
        while l < r:
            m = (l + r) // 2
            if self.combotimes[m] <= t: l = m + 1
            else: r = m
        return l
    
    def is_phi(self): return self.type is ChartFormat.phi
    def is_rpe(self): return self.type is ChartFormat.rpe
    def is_pec(self): return self.type is ChartFormat.pec
    def is_pbc(self): return self.type is ChartFormat.pbc
    
    def dump(self):
        return {
            
        }

class PPLMProxy_CommonChart(tool_funcs.PPLM_ProxyBase):
    def __init__(self, cobj: CommonChart): self.cobj = cobj
    
    def get_lines(self) -> list[JudgeLine]: return self.cobj.lines
    def get_all_pnotes(self) -> list[Note]: return self.cobj.playerNotes
    def remove_pnote(self, n: Note): self.cobj.playerNotes.remove(n)
    
    def nproxy_stime(self, n: Note): return n.time
    def nproxy_etime(self, n: Note): return n.holdEndTime
    def nproxy_hcetime(self, n: Note): return n.giveComboTime
    
    def nproxy_typein(self, n: Note, ts: tuple[int]): return n.type in ts
    def nproxy_typeis(self, n: Note, t: int): return n.type == t
    def nproxy_phitype(self, n: Note): return n.type
    
    def nproxy_nowpos(self, n: Note): return n.nowpos
    def nproxy_nowrotate(self, n: Note) -> float: return n.nowrotate

def load(data: str) -> CommonChart:
    def _unknow_type():
        raise ValueError("Unknown chart type")
    
    if not isinstance(data, dict):
        _unknow_type()
        
    if "formatVersion" in data:
        return ChartFormat.load_phi(data)
    
    elif "META" in data:
        return ChartFormat.load_rpe(data)
    
    else:
        _unknow_type()

if __name__ == "__main__":
    ct = load(open(r"C:\Users\QAQ\Desktop\a.json", "rb").read())
    a = ct.lines[0].getRangeFloorPosition(0.5, 1.0)
    print(a)
