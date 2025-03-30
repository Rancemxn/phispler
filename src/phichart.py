from __future__ import annotations

import typing
import json
import logging
from dataclasses import dataclass, field

import const
import rpe_easing
import light_tool_funcs

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
            data = light_tool_funcs.SaveAsNewFormat(data)
        
        result = CommonChart()
        result.type = ChartFormat.phi
        
        result.offset = data.get("offset", 0.0)
        
        for json_line in data.get("judgeLineList", []):
            json_line: dict
            
            line = JudgeLine()
            
            for json_note in json_line.get("notesAbove", []):
                _put_note(
                    json_line = json_line,
                    line = line,
                    json_note = json_note,
                    isAbove = True
                )
            
            for json_note in json_line.get("notesBelow", []):
                _put_note(
                    json_line = json_line,
                    line = line,
                    json_note = json_note,
                    isAbove = False
                )
            
            if formatVersion == 1:
                for json_e in json_line.get("judgeLineMoveEvents", []):
                    json_e["start"], json_e["start2"] = light_tool_funcs.unpack_pos(json_e.get("start", 0))
                    json_e["end"], json_e["end2"] = light_tool_funcs.unpack_pos(json_e.get("end", 0))
            
            elayer = EventLayerItem()
            _put_events(elayer.alphaEvents, json_line.get("judgeLineDisappearEvents", []), lambda x: x)
            _put_events(elayer.moveXEvents, json_line.get("judgeLineMoveEvents", []), lambda x: x)
            _put_events(elayer.moveYEvents, json_line.get("judgeLineMoveEvents", []), lambda y: 1.0 - y, "start2", "end2")
            _put_events(elayer.rotateEvents, json_line.get("judgeLineRotateEvents", []), lambda r: -r)
            _put_events(elayer.speedEvents, json_line.get("speedEvents", []), _pos_coverter_y, "value", "value")
            line.eventLayers.append(elayer)
            
            result.lines.append(line)
            
        return result
    
    @staticmethod
    def load_rpe(data: dict):
        ...
    
    @staticmethod
    def load_pec(data: str):
        ...

    @staticmethod
    def load_pbc(data: bytes):
        ...

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
    
    def init(self, master: JudgeLine):
        self.master = master

@dataclass
class LineEvent(MemEq):
    startTime: float
    endTime: float
    start: eventValueType
    end: eventValueType
    ease: typing.Callable[[float], float] = rpe_easing.ease_funcs[0]
    
    isFill: bool = False

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
class JudgeLine(MemEq):
    notes: list[Note] = field(default_factory=list)
    eventLayers: list[EventLayerItem] = field(default_factory=list)
    extendEvents: ExtendEventsItem = field(default_factory=ExtendEventsItem)
    
    isTextureLine: bool = False
    texture: typing.Optional[str] = None
    
    isAttachUI: bool = False
    attachUI: typing.Optional[str] = None
    
    enableCover: bool = True
    
    def init(self, master: CommonChart):
        self.master = master
        
        for el in self.eventLayers:
            el.init()
        
        self.extendEvents.init()
        
        for note in self.notes:
            note.init(self)

@dataclass
class CommonChartOptions:
    holdIndependentSpeed: bool = True
    holdCoverAtHead: bool = True
    rpeVersion: int = -1

@dataclass
class CommonChart:
    offset: float = 0.0
    lines: list[JudgeLine] = field(default_factory=list)
    
    options: CommonChartOptions = field(default_factory=CommonChartOptions)
    type: object = field(default=lambda: ChartFormat.unset)
    
    def init(self):
        for line in self.lines:
            line.init(self)

def load(data: bytes):
    def _unknow_type():
        raise ValueError("Unknown chart type")
    
    try:
        str_data = data.decode("utf-8")
    except Exception:
        return ChartFormat.load_pbc(data)
    
    try:
        json_data = json.loads(data)
        
        if not isinstance(json_data, dict):
            _unknow_type()
            
        if "formatVersion" in json_data:
            return ChartFormat.load_phi(json_data)
        
        elif "META" in json_data:
            return ChartFormat.load_rpe(json_data)
        
        else:
            _unknow_type()
        
    except json.JSONDecodeError:
        return ChartFormat.load_pec(str_data)
