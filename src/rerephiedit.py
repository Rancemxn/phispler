from __future__ import annotations

import err_processer as _
import init_logging as _
import fix_workpath as _
import import_argvs as _
import check_edgechromium as _
import check_bin as _

import json
import sys
import time
import datetime
import logging
import typing
import random
import math
import hashlib
from threading import Thread, Timer
from os import popen, mkdir
from os.path import exists, isfile
from shutil import rmtree
from ntpath import basename

import requests
from PIL import Image, ImageFilter
from pydub import AudioSegment

import webcv
import dxsound
import const
import utils
import dialog
import info_loader
import ppr_help
import file_loader
import phira_respack
import phicore
import tempdir
import socket_webviewbridge
import wcv2matlike
import needrelease
import phichart
import phigame_obj
import rpe_easing
import dxsmixer_unix
from dxsmixer import mixer
from exitfunc import exitfunc
from graplib_webview import *

import load_extended as _

RRPEConfig_default = {
    "charts": []
}

RRPEConfig_chart_default = {
    "id": None,
    "name": "",
    "composer": "",
    "illustrator": "",
    "charter": "",
    "level": "UK Lv.1",
    "chartPath": None,
    "illuPath": None,
    "musicPath": None,
    "stdBpm": 140.0,
    "group": "Default"
}

def saveRRPEConfig():
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(json.dumps(RRPEConfig, indent=4, ensure_ascii=False))
    except Exception as e:
        logging.error(f"config save failed: {e}")

def loadRRPEConfig():
    global RRPEConfig
    
    RRPEConfig = RRPEConfig_default.copy()
    try:
        RRPEConfig.update(json.loads(open(CONFIG_PATH, "r", encoding="utf-8").read()))
    except Exception as e:
        logging.error(f"config load failed: {e}")

def getConfigData(key: str):
    return RRPEConfig.get(key, RRPEConfig_default[key])

def setConfigData(key: str, value: typing.Any):
    RRPEConfig[key] = value

try: mkdir("./rrpe_data")
except Exception as e: logging.error(f"rrpe_data mkdir failed: {e}")

CONFIG_PATH = "./rrpe_data/rrpe_config.json"
CHARTS_PATH = "./rrpe_data/charts"

try: mkdir(CHARTS_PATH)
except Exception as e: logging.error(f"charts mkdir failed: {e}")

loadRRPEConfig()

for chart in getConfigData("charts"):
    chart_bak = chart.copy()
    chart.clear()
    chart.update(RRPEConfig_chart_default)
    chart.update(chart_bak)

saveRRPEConfig()

def get_note_max_size_half(globalNoteWidth: float):
    note_max_width = globalNoteWidth * phira_respack.globalPack.dub_fixscale
    note_max_height = max((
        note_max_width / Resource["Notes"]["Tap"].width * Resource["Notes"]["Tap"].height,
        note_max_width / Resource["Notes"]["Tap_dub"].width * Resource["Notes"]["Tap_dub"].height,
        note_max_width / Resource["Notes"]["Drag"].width * Resource["Notes"]["Drag"].height,
        note_max_width / Resource["Notes"]["Drag_dub"].width * Resource["Notes"]["Drag_dub"].height,
        note_max_width / Resource["Notes"]["Flick"].width * Resource["Notes"]["Flick"].height,
        note_max_width / Resource["Notes"]["Flick_dub"].width * Resource["Notes"]["Flick_dub"].height,
        note_max_width / Resource["Notes"]["Hold_Head"].width * Resource["Notes"]["Hold_Head"].height,
        note_max_width / Resource["Notes"]["Hold_Head_dub"].width * Resource["Notes"]["Hold_Head_dub"].height,
        note_max_width / Resource["Notes"]["Hold_End"].width * Resource["Notes"]["Hold_End"].height
    ))
    
    note_max_size_half = ((note_max_width ** 2 + note_max_height ** 2) ** 0.5) / 2
    
    return note_max_size_half

def loadResource():
    global WaitLoading, LoadSuccess
    global chart_res
    global cksmanager
    
    logging.info("Loading Resource...")
    WaitLoading = mixer.Sound("./resources/WaitLoading.mp3")
    LoadSuccess = mixer.Sound("./resources/LoadSuccess.wav")
    LoadSuccess.set_volume(0.75)
    
    phi_rpack = phira_respack.PhiraResourcePack("./resources/resource_packs/default")
    phi_rpack.setToGlobal()
    phi_rpack.printInfo()
    
    Resource = {
        "levels":{
            "AP": Image.open("./resources/levels/AP.png"),
            "FC": Image.open("./resources/levels/FC.png"),
            "V": Image.open("./resources/levels/V.png"),
            "S": Image.open("./resources/levels/S.png"),
            "A": Image.open("./resources/levels/A.png"),
            "B": Image.open("./resources/levels/B.png"),
            "C": Image.open("./resources/levels/C.png"),
            "F": Image.open("./resources/levels/F.png")
        },
        "challenge_mode_levels": [
            Image.open(f"./resources/challenge_mode_levels/{i}.png")
            for i in range(6)
        ],
        "bd_icons": {
            k: Image.open(f"./resources/bytedance_icons/{k}.png")
            for k in (
                "pause", "unpause",
                "setting", "menu"
            )
        },
        "Retry": Image.open("./resources/Retry.png"),
        "Arrow_Right": Image.open("./resources/Arrow_Right.png"),
        "Over": mixer.Sound("./resources/Over.mp3"),
        "Pause": mixer.Sound("./resources/Pause.wav"),
        "PauseImg": Image.open("./resources/Pause.png"),
        "ButtonLeftBlack": Image.open("./resources/Button_Left_Black.png"),
        "ButtonRightBlack": None
    }
    
    Resource.update(phi_rpack.createResourceDict())
    
    respacker = webcv.LazyPILResPacker(root)
    
    Resource["ButtonRightBlack"] = Resource["ButtonLeftBlack"].transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)
    
    for k, v in Resource["Notes"].items():
        respacker.reg_img(Resource["Notes"][k], f"Note_{k}")
    
    for i in range(phira_respack.globalPack.effectFrameCount):
        respacker.reg_img(Resource["Note_Click_Effect"]["Perfect"][i], f"Note_Click_Effect_Perfect_{i + 1}")
        respacker.reg_img(Resource["Note_Click_Effect"]["Good"][i], f"Note_Click_Effect_Good_{i + 1}")
        
    for k,v in Resource["levels"].items():
        respacker.reg_img(v, f"Level_{k}")
    
    for i, v in enumerate(Resource["challenge_mode_levels"]):
        respacker.reg_img(v, f"cmlevel_{i}")
    
    for k, v in Resource["bd_icons"].items():
        respacker.reg_img(v, f"bdi_{k}")
        
    respacker.reg_img(Resource["Retry"], "Retry")
    respacker.reg_img(Resource["Arrow_Right"], "Arrow_Right")
    respacker.reg_img(Resource["PauseImg"], "PauseImg")
    respacker.reg_img(Resource["ButtonLeftBlack"], "ButtonLeftBlack")
    respacker.reg_img(Resource["ButtonRightBlack"], "ButtonRightBlack")
    
    chart_res = {}
        
    root.reg_res(open("./resources/font.ttf", "rb").read(), "pgrFont.ttf")
    root.reg_res(open("./resources/font-thin.ttf", "rb").read(), "pgrFontThin.ttf")
    respacker.load(*respacker.pack())
    
    root.wait_jspromise(f"loadFont('pgrFont', \"{root.get_resource_path("pgrFont.ttf")}\");")
    root.wait_jspromise(f"loadFont('pgrFontThin', \"{root.get_resource_path("pgrFontThin.ttf")}\");")
    root.unreg_res("pgrFont.ttf")
    root.unreg_res("pgrFontThin.ttf")
    
    # root.file_server.shutdown()
                
    shaders = {
        "chromatic": open("./shaders/chromatic.glsl", "r", encoding="utf-8").read(),
        "circleBlur": open("./shaders/circle_blur.glsl", "r", encoding="utf-8").read(),
        "fisheye": open("./shaders/fisheye.glsl", "r", encoding="utf-8").read(),
        "glitch": open("./shaders/glitch.glsl", "r", encoding="utf-8").read(),
        "grayscale": open("./shaders/grayscale.glsl", "r", encoding="utf-8").read(),
        "noise": open("./shaders/noise.glsl", "r", encoding="utf-8").read(),
        "pixel": open("./shaders/pixel.glsl", "r", encoding="utf-8").read(),
        "radialBlur": open("./shaders/radial_blur.glsl", "r", encoding="utf-8").read(),
        "shockwave": open("./shaders/shockwave.glsl", "r", encoding="utf-8").read(),
        "vignette": open("./shaders/vignette.glsl", "r", encoding="utf-8").read()
    }
    
    cksmanager = phicore.ClickSoundManager(Resource["Note_Click_Audio"])
    logging.info("Load Resource Successfully")
    return Resource
    
class UIManager:
    def __init__(self):
        self.uiItems: list[BaseUI] = []
    
    def _check_ui(self, ui: BaseUI):
        ui.set_master(self)
    
    def bind_events(self):
        def _bind_event(name: str, target_name: str, args_eval: str):
            apiname = f"uim_event_{target_name}"
            root.jsapi.set_attr(apiname, lambda *args: self.event_proxy(self.uiItems, target_name, *args))
            root.run_js_code(f"window.addEventListener(\"{name}\", e => pywebview.api.call_attr(\"{apiname}\", {args_eval}));")
        
        _bind_event("mousemove", "mouse_move", "e.x, e.y")
        _bind_event("mousedown", "mouse_down", "e.x, e.y, e.button")
        _bind_event("mouseup", "mouse_up", "e.x, e.y, e.button")
        _bind_event("wheel", "mouse_wheel", "e.x, e.y, e.deltaY")
        _bind_event("keydown", "key_down", "e.key")
    
    def render_bytag(self, tag: str):
        self.render_items([ui for ui in self.uiItems if ui.tag == tag])
    
    def render_items(self, uis: list[BaseUI]):
        for ui in uis:
            self._check_ui(ui)
            ui.render()
    
    def event_proxy(self, uis: list[BaseUI], name: str, *args):
        for ui in reversed(uis):
            self._check_ui(ui)
            getattr(ui, name)(*args)
            ui.event_proxy(name, *args)
            if ui.break_event_chain():
                break
    
    def extend_uiitems(self, items: list[BaseUI], tag: str):
        for ui in items:
            ui.tag = tag
            self._check_ui(ui)
            
        self.uiItems.extend(items)
    
    def remove_ui_bytag(self, tag: str):
        for ui in self.uiItems.copy():
            if ui.tag == tag:
                self._check_ui(ui)
                ui.when_remove()
                self.uiItems.remove(ui)
    
    def remove_ui(self, ui: BaseUI):
        for ui2 in self.uiItems.copy():
            if ui2 is ui:
                self._check_ui(ui)
                ui.when_remove()
                self.uiItems.remove(ui2)
                return
    
    def get_input_value_bytag(self, tag: str):
        for ui in self.uiItems:
            if isinstance(ui, Input) and ui.value_tag == tag:
                return ui.text

class BaseUI:
    tag: typing.Optional[str] = None
    
    def render(self): ...
    def mouse_move(self, x: int, y: int): ...
    def mouse_down(self, x: int, y: int, i: int): ...
    def mouse_up(self, x: int, y: int, i: int): ...
    def mouse_wheel(self, x: int, y: int, d: int): ...
    def key_down(self, k: str): ...
    def key_up(self, k: int): ...
    def when_remove(self): ...
    
    def set_master(self, master: UIManager): ...
    def break_event_chain(self) -> bool: return False
    def event_proxy(self, name: str, *args): ...
    
class Button(BaseUI):
    def __init__(
        self,
        x: float, y: float,
        text: str, color: str,
        command: typing.Optional[typing.Callable[[float, float], None]] = None,
        test: typing.Optional[typing.Callable[[float, float], bool]] = None,
        size: typing.Optional[tuple[int, int]] = None,
        fontscale: float = 1.0,
    ):
        self._x = x
        self._y = y
        self.dx = 0
        self.dy = 0
        self.text = text
        self.color = color
        self.fontscale = fontscale
        self.rect = const.EMPTY_RECT
        self.command = command
        self.test = test
        self.size = size
        self.mouse_isin = False
        
        self.scale_value_tr = phigame_obj.valueTranformer(rpe_easing.ease_funcs[9], 0.3)
        self.scale_value_tr.target = 1.0
    
    @property
    def x(self):
        return self._x + self.dx
    
    @property
    def y(self):
        return self._y + self.dy
    
    def render(self):
        self.rect = drawRPEButton(
            self.x, self.y,
            self.text, self.color,
            scale = self.scale_value_tr.value,
            **({} if self.size is None else {"size": self.size}),
            fontscale = self.fontscale
        )
    
    def mouse_move(self, x: int, y: int):
        isin = utils.inrect(x, y, self.rect)
        
        if isin != self.mouse_isin:
            self.scale_value_tr.target = 1.1 if isin else 1.0
            self.mouse_isin = isin
    
    def mouse_down(self, x: int, y: int, _):
        self.mouse_move(x, y)
        if utils.inrect(x, y, self.rect) and self.command is not None:
            if self.test is None or self.test(x, y):
                self.command(x, y)

class IconButton(BaseUI):
    def __init__(
        self,
        x: float, y: float,
        icon: str,
        command: typing.Optional[typing.Callable[[], None]] = None
    ):
        self.x = x
        self.y = y
        self.icon = icon
        self.size = (w + h) / 57
        self.command = command
        self.mouse_isin = False
        self.rect = (
            self.x - self.size / 2, self.y - self.size / 2,
            self.x + self.size / 2, self.y + self.size / 2
        )
        
        self.scale_value_tr = phigame_obj.valueTranformer(rpe_easing.ease_funcs[9], 0.3)
        self.scale_value_tr.target = 1.0

    def render(self):
        s = self.size * self.scale_value_tr.value
        
        drawImage(
            f"bdi_{self.icon}",
            self.x - s / 2, self.y - s / 2,
            s, s,
            wait_execute = True
        )
    
    def mouse_move(self, x: int, y: int):
        isin = utils.inrect(x, y, self.rect)
        
        if isin != self.mouse_isin:
            self.scale_value_tr.target = 1.1 if isin else 1.0
            self.mouse_isin = isin
    
    def mouse_down(self, x: int, y: int, _):
        if utils.inrect(x, y, self.rect):
            if self.command is not None:
                self.command()
            self.scale_value_tr.target -= 0.3
    
    def mouse_up(self, x: int, y: int, _):
        if utils.inrect(x, y, self.rect):
            self.scale_value_tr.target += 0.3

class Label(BaseUI):
    def __init__(
        self,
        x: float, y: float,
        text: str, color: str,
        font: str,
        textAlign: str = "left",
        textBaseline: str = "top"
    ):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.font = font
        self.textAlign = textAlign
        self.textBaseline = textBaseline

    def render(self):
        drawText(
            self.x, self.y,
            self.text,
            font = self.font,
            fillStyle = self.color,
            textAlign = self.textAlign,
            textBaseline = self.textBaseline,
            wait_execute = True
        )

class Input(BaseUI):
    def __init__(
        self,
        x: float, y: float,
        text: str, font: str,
        width: float, height: float,
        default_text: typing.Optional[str] = None,
        value_tag: typing.Optional[str] = None
    ):
        self.x = x
        self.y = y
        self.text = text
        self.font = font
        self.width = width
        self.height = height
        self.default_text = default_text
        self.value_tag = value_tag
        self.id = random.randint(0, 2 << 31)
        
        self.removed = False
    
    def render(self):
        if self.removed:
            return
        
        fillRectEx(self.x, self.y, self.width, self.height, "rgba(255, 255, 255, 0.5)", wait_execute=True)
        strokeRectEx(self.x, self.y, self.width, self.height, "white", (w + h) / 650, wait_execute=True)
        
        self.text = root.run_js_code(f"updateCanvasInput({self.id}, {self.x}, {self.y}, {self.width}, {self.height}, \"{self.font}\", {repr(self.default_text) if self.default_text is not None else "null"})")
    
    def when_remove(self):
        self.removed = True
        root.run_js_code(f"removeCanvasInput({self.id})")
    
    def set_text(self, value: str):
        root.run_js_code(f"setCanvasInputText({self.id}, {repr(value)})")

class MessageShower(BaseUI):
    def __init__(self):
        self.msgs: list[Message] = []
        self.max_show_time = 2.0
        self.padding_y = h / 50
    
    @utils.thread_lock_func
    def render(self):
        for msg in self.msgs.copy():
            if time.time() - msg.st > self.max_show_time + msg.left_tr.animation_time:
                self.msgs.remove(msg)
                continue
            elif time.time() - msg.st > self.max_show_time and not msg.timeout:
                msg.timeout = True
                msg.top_tr.target -= self.padding_y
                msg.alpha_tr.target = 0.0
                
                for msg2 in self.msgs:
                    msg2.top_tr.target -= msg2.height + self.padding_y
            
            rect = (
                msg.left_tr.value,
                msg.top_tr.value,
                msg.left_tr.value + msg.width,
                msg.top_tr.value + msg.height
            )
            
            ctxSave(wait_execute=True)
            ctxMutGlobalAlpha(msg.alpha_tr.value, wait_execute=True)
            
            fillRectEx(*utils.xxyy_rect2_xywh(rect), msg.color, wait_execute=True)
            drawText(
                rect[0] + msg.padding_x,
                rect[1] + msg.height / 2,
                msg.text,
                font = msg.font,
                fillStyle = "white",
                textAlign = "left",
                textBaseline = "middle",
                wait_execute = True
            )
            
            timeout_p = utils.fixorp((time.time() - msg.st) / self.max_show_time)
            timeout_height = msg.padding_y * 0.4
            fillRectEx(
                rect[0],
                rect[1] + (rect[3] - rect[1]) - timeout_height,
                (rect[2] - rect[0]) * timeout_p,
                timeout_height,
                "rgba(255, 255, 255, 0.4)",
                wait_execute = True
            )
            
            ctxRestore(wait_execute=True)
    
    @utils.thread_lock_func(lock=render.lock)
    def submit(self, msg: Message):
        vaild_msgs = [i for i in self.msgs if not i.timeout]
        
        msg.top_tr.target = max(
            self.padding_y
            if not vaild_msgs else
            (vaild_msgs[-1].top_tr.target + vaild_msgs[-1].height + self.padding_y),
            
            self.padding_y
        )
        self.msgs.append(msg)

class Message:
    INFO_COLOR = "skyblue"
    WARNING_COLOR = "orange"
    ERROR_COLOR = "red"
    
    TEXT_SIZE = 79
    
    def __init__(self, text: str, color: str):
        self.text = text
        self.font = f"{(w + h) / Message.TEXT_SIZE}px pgrFont"
        self.color = color
        self.st = time.time()
        self.timeout = False
        
        textsize = root.run_js_code(f"ctx.getTextSize({repr(text)}, \"{self.font}\");")
        self.padding_x = w / 75
        self.padding_y = h / 65
        self.width = textsize[0] + self.padding_x * 2
        self.height = textsize[1] + self.padding_y * 2
        
        self.left_tr = phigame_obj.valueTranformer(rpe_easing.ease_funcs[9])
        self.left_tr.target = w * 1.1
        self.left_tr.target = w - self.width - w / 60
        
        self.top_tr = phigame_obj.valueTranformer(rpe_easing.ease_funcs[9])
        
        self.alpha_tr = phigame_obj.valueTranformer(rpe_easing.ease_funcs[9])
        self.alpha_tr.target = 1.0

class ChartChooser(BaseUI):
    def __init__(
        self,
        change_test: typing.Optional[typing.Callable[[], bool]] = None,
        when_change: typing.Optional[typing.Callable[[], None]] = None
    ):
        self.last_chart = None
        self.last_call_wc = time.time()
        self.i = 0
        self.dc = 0
        
        self.change_test = change_test
        self.when_change = when_change
        self.tr_map: dict[str, tuple[phigame_obj.valueTranformer, ...]] = {}
    
    def get_chart_tr_values(self, i: int, is_chosing: bool, chosing_index: int):
        size = pos1k(800, 450) if is_chosing else pos1k(508, 285)
        center_pos = utils.getCenterPointByRect((*pos1k(141, 315), *pos1k(940, 765)))
        
        if not is_chosing:
            di = i - chosing_index
            di_less = (di - 1) if di > 0 else (di + 1)
            center_pos = (
                center_pos[0] + (pos1k(800, 0)[0] / 2 * (1 if di > 0 else -1)) + (di * pos1k(303.5, 0)[0] + di_less * pos1k(253.5, 0)[0]),
                pos1k(0, 640)[1]
            )
            
        return (
            size,
            center_pos
        )
    
    def update(self, charts: list[dict]):
        self.i += self.dc
        self.dc = 0
        
        if charts:
            self.i %= len(charts)
        else:
            return
        
        chosing_chart = charts[self.i]
        
        if chosing_chart != self.last_chart and time.time() - self.last_call_wc > 0.3:
            self.last_chart = chosing_chart
            self.last_call_wc = time.time()
            if self.when_change is not None:
                self.when_change()
        
        all_ids = []
        for i, chart in enumerate(charts):
            chart_id = chart["id"]
            all_ids.append(chart_id)
            
            if chart_id not in self.tr_map:
                self.tr_map[chart_id] = tuple(
                    phigame_obj.valueTranformer(rpe_easing.ease_funcs[9])
                    for _ in range(4)
                )
                
            tr_values = self.get_chart_tr_values(i, chart is chosing_chart, self.i)
            def _set(i: int, v: float):
                if self.tr_map[chart_id][i].target != v:
                    self.tr_map[chart_id][i].target = v
            
            _set(0, tr_values[0][0])
            _set(1, tr_values[0][1])
            _set(2, tr_values[1][0])
            _set(3, tr_values[1][1])
        
        for k in self.tr_map.copy().keys():
            if k not in all_ids:
                self.tr_map.pop(k)
    
    def key_down(self, k: str):
        if self.change_test is None or self.change_test():
            if k == "ArrowLeft":
                self.dc -= 1
            elif k == "ArrowRight":
                self.dc += 1
            else:
                return

class Slider(BaseUI):
    def __init__(
        self,
        minv: float, maxv: float,
        value: float,
        x: float, y: float,
        width: float,
        when_change: typing.Callable[[float], typing.Any]
    ):
        self.min = minv
        self.max = maxv
        self.value = value
        self.x = x
        self.y = y
        self.width = width
        self.height = h / 50
        self.when_change = when_change

        self.rect = (
            x, y - self.height / 2,
            width, self.height
        )
        
        self._ismousedown = False
    
    def render(self):
        p = (self.value - self.min) / (self.max - self.min)
        
        prect = (
            self.x, self.y - self.height / 2,
            self.width * p, self.height
        )
        
        pady = self.height / 4
        brect = (
            self.x + self.width * p,
            self.y - self.height / 2 - pady,
            w / 125, self.height + pady * 2
        )
        
        fillRectEx(*self.rect, "#e8e7ff", wait_execute=True)
        fillRectEx(*prect, "#acafff", wait_execute=True)
        fillRectEx(*brect, "#787ddd", wait_execute=True)
    
    def mouse_down(self, x: int, y: int, _):
        self._ismousedown = utils.inrect(x, y, utils.xywh_rect2_xxyy(self.rect))
        self.mouse_move(x, y)
    
    def mouse_move(self, x: int, y: int):
        if self._ismousedown:
            p = utils.fixorp((x - self.x) / self.width)
            self.value = self.min + p * (self.max - self.min)
            self.when_change(self.value)
    
    def mouse_up(self, x: int, y: int, _):
        self._ismousedown = False

class ModalUI(BaseUI):
    def __init__(self, uis: list[BaseUI], mark_color: str = "black"):
        self.uis = uis
        self.mark_color = mark_color
        self.bec = True
        
    def render(self):
        ctxSave(wait_execute=True)
        ctxMutGlobalAlpha(0.4, wait_execute=True)
        fillRectEx(0, 0, w, h, self.mark_color, wait_execute=True)
        ctxRestore(wait_execute=True)
        
        self.master.render_items(self.uis)
    
    def set_master(self, master: UIManager):
        self.master = master
        
    def break_event_chain(self):
        return self.bec
    
    def event_proxy(self, name: str, *args):
        self.master.event_proxy(self.uis, name, *args)
        
class ButtonList(BaseUI):
    def __init__(self, x: float, y: float, width: float, height: float, buts: list[typing.Optional[dict]], fontsize: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        self.butheight = h / 30
        self.fontsize = fontsize
        self.pady = h / 75
        self.padx = w / 75
        
        self.buts = [
            Button(
                x + self.padx, y + self.pady + sum([(self.butheight + self.pady) * (1.0 if j is not None else 0.4) for j in buts[:i]]),
                butcfg["text"], "skyblue",
                butcfg["command"],
                size = apos1k(width - self.padx * 2, self.butheight),
                fontscale = 0.5
            )
            for i, butcfg in enumerate(buts)
            if butcfg is not None
        ]
        
        self.set_scroll(0.0)
        self.w_tr = phigame_obj.valueTranformer(rpe_easing.ease_funcs[9])
        self.h_tr = phigame_obj.valueTranformer(rpe_easing.ease_funcs[9])
        self.a_tr = phigame_obj.valueTranformer(rpe_easing.ease_funcs[15])
        self._set_trs()
        self._set_trs(1.0, 1.0, 1.0)
    
    def _set_trs(self, w: float = 0.0, h: float = 0.0, a: float = 0.0, at: float = 0.5):
        self.w_tr.animation_time = at
        self.h_tr.animation_time = at
        self.a_tr.animation_time = at
        self.w_tr.target = w
        self.h_tr.target = h
        self.a_tr.target = a
    
    def render(self):
        ctxSave(wait_execute=True)
        ctxTranslate(self.x, self.y, wait_execute=True)
        ctxScale(self.w_tr.value, self.h_tr.value, wait_execute=True)
        ctxMutGlobalAlpha(self.a_tr.value, wait_execute=True)
        
        fillRectEx(0, 0, self.width, self.height, "#7474ff", wait_execute=True)
        
        ctxSave(wait_execute=True)
        ctxBeginPath(wait_execute=True)
        ctxRect(0, self.y + self.pady, w, h - self.pady * 2, wait_execute=True)
        ctxClip(wait_execute=True)
        self.master.render_items(self.buts)
        ctxRestore(wait_execute=True)
        
        ctxRestore(wait_execute=True)
    
    def set_master(self, master: UIManager):
        self.master = master
    
    def event_proxy(self, name: str, *args):
        self.master.event_proxy(self.buts, name, *args)
    
    def set_scroll(self, scroll: float):
        for i in self.buts:
            if i is not None:
                i.dy = -scroll + self.pady
    
    def delete_ui(self, callback: typing.Callable[[], typing.Any]):
        self._set_trs(at=0.4)
        Timer(self.w_tr.animation_time, callback).start()

class ChartEditor:
    def __init__(self, chart: phichart.CommonChart, chart_config: dict):
        self.chart = chart
        self.chart_config = chart_config
        self.chart_dir = f"{CHARTS_PATH}/{chart_config["id"]}"
        
        self.step_dumps: list[bytes] = []
        self.can_undo = False
        self.now_step_i = -1
        self.last_chart_now_t = 0
        self.paused = True
        self.editing_line = 0
    
    def emit_command(self, command: EditBaseCmd):
        self.new_dump()
        self.can_undo = True
        
        if isinstance(command, ...):
            ...
            
        elif isinstance(command, EditBaseCmd):
            pass
        else:
            assert False, f"Unknown command type: {type(command)}"
    
    def new_dump(self):
        if self.can_undo:
            if self.now_step_i < len(self.step_dumps) - 1:
                self.step_dumps = self.step_dumps[:self.now_step_i + 1]
            
        self.step_dumps.append(self.chart.dump())
        self.now_step_i += 1
    
    def undo(self):
        if self.can_undo:
            self.now_step_i -= 1
            self.load_chart_from_dumps()
    
    def load_chart_from_dumps(self):
        self.chart = phichart.CommonChart.loaddump(self.step_dumps[self.now_step_i])
    
    def pause_play(self):
        self.paused = True
        mixer.music.pause()
        
    def unpause_play(self):
        self.paused = False
        mixer.music.unpause()
    
    def seek_to(self, t: float):
        mixer.music.set_pos(t)
        
    def seek_by(self, delta: float):
        self.seek_to(mixer.music.get_pos() + delta)
    
    def update(self):
        ...

    def when_timejump(self, new_t: float, is_negtive: bool):
        if is_negtive:
            self.chart.fast_init()
            
            for line in self.chart.lines:
                for note in line.notes:
                    note.isontime = note.time < new_t
        else:
            for line in self.chart.lines:
                for nc in line.renderNotes:
                    for note in nc:
                        note.isontime = note.isontime or new_t - note.time > 0.5
    
    @property
    @utils.thread_lock_func
    def chart_now_t(self) -> float:
        ret = mixer.music.get_pos()
        self.when_timejump(ret, ret < self.last_chart_now_t)
        self.last_chart_now_t = ret
        return ret
    
    @utils.thread_lock_func
    def new_save(self):
        globalMsgShower.submit(Message(f"保存...", Message.INFO_COLOR))
        dmp = self.chart.dump()
        
        with open(f"{self.chart_config["chartPath"]}", "wb") as f:
            f.write(dmp)
        
        self.new_bak(dmp)
    
    def new_bak(self, dmp: bytes):
        try: mkdir(f"{self.chart_dir}/baks")
        except Exception as e: logging.error(f"baks mkdir failed: {e}")
        
        dt = datetime.datetime.now()
        fn = f"{dt.year}.{dt.month}.{dt.day}.{dt.hour}.{dt.minute}.{dt.second}.{dt.microsecond}.bpc"
        
        with open(f"{self.chart_dir}/baks/{fn}", "wb") as f:
            f.write(dmp)
            
        globalMsgShower.submit(Message(f"已创建备份文件: {fn}", Message.INFO_COLOR))

class EditBaseCmd:
    ...

class Edit_NewNote(EditBaseCmd):
    def __init__(self, note: phichart.Note):
        self.note = note

class EditorPreviewArea:
    def __init__(self, size: float):
        self.size = size
        self.ratio = 16 / 9
    
    def get_rect(self):
        preview_w, preview_h = w * self.size, h * self.size
        preview_ratio = preview_w / preview_h
        chart_ratio = self.ratio
        
        if preview_ratio > chart_ratio:
            chart_h = preview_h
            chart_w = chart_h * chart_ratio
        else:
            chart_w = preview_w
            chart_h = chart_w / chart_ratio

        preview_x = 0
        preivew_y = h - preview_h
        
        chart_x = preview_x + (preview_w - chart_w) / 2
        chart_y = preivew_y + (preview_h - chart_h) / 2
        
        return (
            (preview_x, preivew_y, preview_w, preview_h),
            (chart_x, chart_y, chart_w, chart_h)
        )
    
    @property
    def preview_rect(self):
        return self.get_rect()[0]
    
    @property
    def chart_rect(self):
        return self.get_rect()[1]

def drawRPEButton(
    x: float, y: float,
    text: str, color: str,
    *,
    scale: float = 1.0,
    size: tuple[int, int] = (341, 84),
    fontscale: float = 1.0
):
    button_size = pos1k(*size)
    x, y = (x + button_size[0] / 2, y + button_size[1] / 2)
    rect = (
        x - button_size[0] / 2 * scale,
        y - button_size[1] / 2 * scale,
        x + button_size[0] / 2 * scale,
        y + button_size[1] / 2 * scale
    )
    
    xywh_rect = utils.xxyy_rect2_xywh(rect)
    
    ctxSave(wait_execute=True)
    ctxMutGlobalAlpha(0.8, wait_execute=True)
    fillRectEx(*xywh_rect, color, wait_execute=True)
    ctxRestore(wait_execute=True)
    
    strokeRectEx(*xywh_rect, color, (w + h) / 650 * scale * fontscale, wait_execute=True)
    strokeRectEx(*xywh_rect, "rgba(255, 255, 255, 0.4)", (w + h) / 650 * scale * fontscale, wait_execute=True)
    
    drawText(
        *utils.getCenterPointByRect(rect),
        text,
        font = f"{(w + h) / 75 * scale * fontscale}px pgrFont",
        textAlign = "center",
        textBaseline = "middle",
        fillStyle = "white",
        wait_execute = True
    )
    
    return rect

def pos1k(x: float, y: float):
    return w * (x / 1920), h * (y / 1080)

def apos1k(x: float, y: float):
    return x / w * 1920, y / h * 1080

def createNewChartId():
    dt = datetime.datetime.now()
    return f"{dt.year}.{dt.month}.{dt.day}.{dt.hour}.{dt.minute}.{dt.second}.{dt.microsecond}-{random.randint(0, 1024)}"

def hashChartId(chart_id: str):
    return "hash_" + hashlib.md5(chart_id.encode("utf-8")).hexdigest()

def web_alert(msg: str):
    root.run_js_code(f"alert({repr(msg)});")

def web_prompt(msg: str) -> typing.Optional[str]:
    return root.run_js_code(f"prompt({repr(msg)});")

def web_confirm(msg: str) -> bool:
    return root.run_js_code(f"confirm({repr(msg)});")

def renderGlobalItems():
    globalUIManager.render_bytag("modal")
    globalUIManager.render_bytag("global")

def editorRender(chart_config: dict):
    global raw_audio_length

    def updateCoreConfig():
        chart_information = {
            "Name": chart_config["name"],
            "Artist": chart_config["composer"],
            "Level": chart_config["level"],
            "Illustrator": chart_config["illustrator"],
            "Charter": chart_config["charter"],
            "BackgroundDim": 0.6
        }
        
        new_w, new_h = chart_rect[2:]
        globalNoteWidth = new_w * const.NOTE_DEFAULTSIZE
        
        phicore.CoreConfigure(phicore.PhiCoreConfig(
            SETTER = lambda vn, vv: globals().update({vn: vv}),
            root = root, w = new_w, h = new_h,
            chart_information = chart_information,
            chart_obj = editor.chart,
            Resource = Resource,
            globalNoteWidth = globalNoteWidth,
            note_max_size_half = get_note_max_size_half(globalNoteWidth),
            raw_audio_length = raw_audio_length,
            chart_res = chart_res,
            cksmanager = cksmanager,
            showfps = True, debug = True,  combotips = "EDITOR",
        ))
    
    mixer.music.stop()
    mixer.music.unload()
    
    chart = phichart.CommonChart.loaddump(open(chart_config["chartPath"], "rb").read())
    editor = ChartEditor(chart, chart_config)
    
    respacker = webcv.LazyPILResPacker(root)
    
    chart_image_ve: utils.ValueEvent[Image.Image] = utils.ValueEvent()
    
    def load_res():
        chart_image = Image.open(chart_config["illuPath"])
    
        if chart_image.mode != "RGB":
            chart_image = chart_image.convert("RGB")

        chart_image_ve.set(chart_image)
    
    Thread(target=load_res, daemon=True).start()
    
    respacker.reg_img(lambda: chart_image_ve.wait().filter(ImageFilter.GaussianBlur(sum(chart_image_ve.wait().size) / 50)), "background_blur")
    respacker.reg_img(chart_image_ve.wait, "chart_image")
    
    respacker.load(*respacker.pack())
    
    mixer.music.load(chart_config["musicPath"])
    mixer.music.play()
    mixer.music.pause()
    
    raw_audio_length = mixer.music.get_length()
    
    nextUI = None
    preview_area = EditorPreviewArea(0.75)
    preview_rect, chart_rect = preview_area.get_rect()
    top_more = preview_rect[1]
    right_more = w - preview_rect[2]
    
    def posm(x: float, y: float):
        return w * (x / 1920), top_more * (y / 145)
    
    def getButtonPos(c: int, r: int):
        return posm(42 * 1.1 + 63 * c * 1.3, 38 / 2 * 1.1 + 63 * r * 1.3)
    
    def seek_time(t: float):
        update_info_labels()
        editor.seek_to(t)
    
    def update_info_labels():
        editing_line = editor.chart.lines[editor.editing_line]
        now_t = chart_time_slider.value
        
        chart_time_show_labels[0].text = f"beat: {editing_line.sec2beat(now_t):.2f}"
        chart_time_show_labels[1].text = f"bpm: {editing_line.getBpm(now_t):.2f}"
        chart_time_show_labels[2].text = f"{now_t:.2f}/{raw_audio_length:.2f}s"
        
        chart_type_label.text = f"chart type: {editor.chart.type} ({phichart.ChartFormat.get_type_string(editor.chart.type)})"
    
    def popupMenu():
        def _close_menu():
            butlst.delete_ui(lambda: globalUIManager.remove_ui(modal))
            Timer(0.1, lambda: setattr(modal, "bec", False)).start()
            
        def _back_tomain(*, isnosave: bool = False):
            nonlocal nextUI
            
            if isnosave:
                if not web_confirm(f"确定不保存并返回主界面？\n如果有未保存的更改，它们将会丢失！！！"):
                    return
            
                globalMsgShower.submit(Message("你说得对, 但是还是我们还是准备给你创建一个备份...", Message.WARNING_COLOR))
                editor.new_bak(editor.chart.dump())
            
            nextUI = mainRender
            _close_menu()
        
        def _save_as():
            fp = dialog.savefile(Filter="Binary Phigros Chart 文件 (*.bpc)|*.bpc|所有文件 (*.*)|*.*", fn="save_as.bpc")
            
            if fp is not None:
                with open(fp, "wb") as f:
                    f.write(editor.chart.dump())
                
                globalMsgShower.submit(Message(f"已另存到: {fp}", Message.INFO_COLOR))
            else:
                globalMsgShower.submit(Message("取消另存", Message.WARNING_COLOR))
            
        butlst = ButtonList(
            0, 0, w / 6, h,
            [
                {"text": "关闭菜单", "command": lambda *_: _close_menu()},
                None,
                {"text": "保存", "command": lambda *_: editor.new_save()},
                {"text": "另存为", "command": lambda *_: _save_as()},
                None,
                {"text": "保存并返回主界面", "command": lambda *_: (editor.new_save(), _back_tomain(), _close_menu())},
                {"text": "不保存并返回主界面", "command": lambda *_: _back_tomain(isnosave=True)},
            ], (w + h) / 150
        )
        
        modal = ModalUI([butlst])
        
        globalUIManager.extend_uiitems([modal], "modal")
    
    updateCoreConfig()
    
    chart_time_slider = Slider(
        0.0, raw_audio_length, 0.0,
        preview_rect[2] + w / 150, h / 50 + h / 100,
        (w - preview_rect[2]) - w / 150 * 2, seek_time
    )
    
    chart_time_show_labels_pady = h / 50
    chart_time_show_labels = [
        Label(chart_time_slider.x, chart_time_slider.y + chart_time_show_labels_pady, "", "white", f"{(w + h) / 150}px pgrFont", "left"),
        Label(chart_time_slider.x + chart_time_slider.width / 2, chart_time_slider.y + chart_time_show_labels_pady, "", "white", f"{(w + h) / 150}px pgrFont", "center"),
        Label(chart_time_slider.x + chart_time_slider.width, chart_time_slider.y + chart_time_show_labels_pady, "", "white", f"{(w + h) / 150}px pgrFont", "right")
    ]
    chart_type_label = Label(chart_time_show_labels[0].x, chart_time_show_labels[0].y + h / 50, "", "#a4c7ff", f"{(w + h) / 150}px pgrFont")
    update_info_labels()
    
    globalUIManager.extend_uiitems([
        chart_time_slider,
        *chart_time_show_labels,
        chart_type_label,
        IconButton(*getButtonPos(0, 0), "menu", popupMenu),
        IconButton(*getButtonPos(1, 0), "unpause", editor.unpause_play),
        IconButton(*getButtonPos(2, 0), "pause", editor.pause_play)
    ], "editorRender")
    editor.unpause_play()
    
    while True:
        clearCanvas(wait_execute=True)
        
        editor.update()
        editor_now_t = editor.chart_now_t
        chart_time_slider.value = editor_now_t
        update_info_labels()
        
        fillRectEx(*preview_rect, "rgb(64, 64, 64)", wait_execute=True)
        
        fillRectEx(0, 0, w, preview_rect[1], "rgb(24, 24, 24)", wait_execute=True)
        fillRectEx(preview_rect[2], 0, w, preview_rect[1], "rgb(32, 32, 32)", wait_execute=True)
        fillRectEx(preview_rect[2], preview_rect[1], w, h, "rgb(48, 48, 48)", wait_execute=True)
        
        ctxSave(wait_execute=True)
        ctxTranslate(*chart_rect[:2], wait_execute=True)
        ctxBeginPath(wait_execute=True)
        ctxRect(0, 0, *chart_rect[2:], wait_execute=True)
        ctxClip(wait_execute=True)
        extasks = phicore.renderChart_Common(editor_now_t, clear=False, rjc=False, need_deepbg=False, editing_line=editor.editing_line)
        ctxRestore(wait_execute=True)
        
        phicore.processExTask(extasks)
        
        globalUIManager.render_bytag("editorRender")
        renderGlobalItems()
        
        root.run_js_wait_code()
        
        if nextUI is not None:
            globalUIManager.remove_ui_bytag("editorRender")
            respacker.unload(respacker.getnames())
            mixer.music.fadeout(250)
            Thread(target=nextUI, daemon=True).start()
            return

def mainRender():
    nextUI = None
    
    topButtonLock = False
    createChartData = None
    needUpdateIllus = False
    
    illuPacker: typing.Optional[webcv.LazyPILResPacker] = None
    def updateIllus():
        nonlocal illuPacker
        
        if illuPacker is not None:
            illuPacker.unload(illuPacker.getnames())
        
        illuPacker = webcv.LazyPILResPacker(root)
        
        for chart in getConfigData("charts"):
            illuPacker.reg_img(chart["illuPath"], f"illu_{hashChartId(chart["id"])}")
        
        illuPacker.load(*illuPacker.pack())
    
    def createChart(*_):
        nonlocal createChartData, topButtonLock
        
        topButtonLock = True
        
        music_file = dialog.openfile(Filter="音乐文件 (*.mp3;*.wav;*.ogg)|*.mp3;*.wav;*.ogg|所有文件 (*.*)|*.*")
        if music_file is None or not isfile(music_file):
            topButtonLock = False
            return
        
        illu_file = dialog.openfile(Filter="图片文件 (*.png;*.jpg;*.jpeg)|*.png;*.jpg;*.jpeg|所有文件 (*.*)|*.*", fn="可跳过  can be skipped")
        if illu_file is None or not isfile(illu_file):
            illu_file = "./resources/transparent_blocks.png"
        
        createChartData = {
            "music": music_file,
            "illu": illu_file
        }
        
        def _cancal(*_):
            nonlocal createChartData
            
            globalUIManager.remove_ui_bytag("mainRender-createChart")
            createChartData = None
        
        def _confirm(*_):
            nonlocal createChartData, needUpdateIllus
            
            userInputData = {
                k: globalUIManager.get_input_value_bytag(k)
                for k in ["chartName", "chartComposer", "chartCharter", "chartBPM", "chartLines"]
            }
            
            try:
                v = float(userInputData["chartBPM"])
                if math.isnan(v) or math.isinf(v) or v == 0.0:
                    raise ValueError
            except Exception:
                globalMsgShower.submit(Message("请输入有效的BPM", Message.ERROR_COLOR))
                return
            
            try:
                v = int(userInputData["chartLines"])
                if v < 0:
                    raise ValueError
            except Exception:
                globalMsgShower.submit(Message("请输入有效的线数", Message.ERROR_COLOR))
                return
            
            createChartData.update(userInputData)
            
            chart_config = RRPEConfig_chart_default.copy()
            chart_config["name"] = createChartData["chartName"]
            chart_config["composer"] = createChartData["chartComposer"]
            chart_config["charter"] = createChartData["chartCharter"]
            chart_config["stdBpm"] = float(createChartData["chartBPM"])
            chart_config["id"] = createNewChartId()
            
            chart_id = chart_config["id"]
            
            try: mkdir(f"{CHARTS_PATH}/{chart_id}")
            except Exception: logging.error(f"chart mkdir failed: {e}")
            
            chart_obj = phichart.CommonChart(lines=[phichart.JudgeLine(bpms=[phichart.BPMEvent(0, chart_config["stdBpm"])]) for _ in range(int(createChartData["chartLines"]))])
            
            for i, line in enumerate(chart_obj.lines):
                line.index = i
            
            chart_obj.type = phichart.ChartFormat.rpe
            chart_obj.options.globalBpmList = [phichart.BPMEvent(0, chart_config["stdBpm"])]
            chart_obj.init()
            
            with open(f"{CHARTS_PATH}/{chart_id}/chart.bpc", "wb") as f:
                f.write(chart_obj.dump())
            
            try: illu = Image.open(createChartData["illu"])
            except Exception:
                illu = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
                logging.error(f"illu open failed: {e}")
            
            illu.save(f"{CHARTS_PATH}/{chart_id}/image.png", format="PNG")
            
            try:
                seg: AudioSegment = AudioSegment.from_file(createChartData["music"])
                seg.export(f"{CHARTS_PATH}/{chart_id}/music.wav", format="wav")
            except Exception:
                globalMsgShower.submit(Message("音频读取失败", Message.ERROR_COLOR))
                rmtree(f"{CHARTS_PATH}/{chart_id}")
                return
            
            chart_config["chartPath"] = f"{CHARTS_PATH}/{chart_id}/chart.bpc"
            chart_config["illuPath"] = f"{CHARTS_PATH}/{chart_id}/image.png"
            chart_config["musicPath"] = f"{CHARTS_PATH}/{chart_id}/music.wav"
            
            getConfigData("charts").append(chart_config)
            saveRRPEConfig()
            needUpdateIllus = True
            
            globalUIManager.remove_ui_bytag("mainRender-createChart")
            createChartData = None
        
        globalUIManager.extend_uiitems(utils.unfold_list([
            [
                Label(*pos1k(586, 283 + 133 * i), name, "white", f"{(w + h) / 75}px pgrFont", textBaseline="middle"),
                Input(*pos1k(885, 253 + 133 * i), "", f"{(w + h) / 95}px pgrFont", *pos1k(500, 60), default_text[0] if default_text else None, key)
            ]
            for i, (name, key, *default_text) in enumerate([
                ("谱面名称", "chartName"),
                ("作曲者", "chartComposer"),
                ("谱面设计", "chartCharter"),
                ("基础BPM", "chartBPM", "140"),
                ("基础线数", "chartLines", "24")
            ])
        ] + [
            Button(*pos1k(529, 883), "取消", "red", _cancal, size=(210, 71), fontscale=0.9),
            Button(*pos1k(1183, 883), "确定", "green", _confirm, size=(210, 71), fontscale=0.9),
        ]), "mainRender-createChart")
        
        topButtonLock = False
    
    def deleteChart(*_):
        nonlocal needUpdateIllus
        
        charts = getConfigData("charts")
        
        if not charts:
            globalMsgShower.submit(Message("你还没有谱面可以删除...", Message.ERROR_COLOR))
            return
        
        chooser.update(charts)
        chosing_chart = charts[chooser.i]
        
        if web_confirm(f"你确定要删除谱面 \"{chosing_chart["name"]}\" 吗？\n这个操作不可逆！\n你真的要删除吗？这个谱面会丢失很久（真的很久！）\n\n谱面 config: {json.dumps(chosing_chart, indent=4, ensure_ascii=False)}"):
            charts.remove(chosing_chart)
            dxsmixer_unix.mixer.music.stop()
            dxsmixer_unix.mixer.music.unload()
            
            try: rmtree(f"{CHARTS_PATH}/{chosing_chart["id"]}")
            except Exception as e: logging.error(f"chart rmtree failed: {e}")
            
            saveRRPEConfig()
            needUpdateIllus = True
    
    def gotoEditor(*_):
        nonlocal nextUI
        
        charts = getConfigData("charts")
        
        if not charts:
            globalMsgShower.submit(Message("你还没有谱面可以编辑...", Message.ERROR_COLOR))
            return
        
        chart_config = charts[chooser.i]
        nextUI = lambda: editorRender(chart_config)
    
    def can_click_top_button(*_):
        return (
            not topButtonLock and
            createChartData is None
        )
    
    def chooser_when_change():
        chart = getConfigData("charts")[chooser.i]
        
        def _play_preview():
            try:
                dxsmixer_unix.mixer.music.load(chart["musicPath"])
                dxsmixer_unix.mixer.music.play(-1)
            except Exception as e:
                logging.error(f"music play failed: {e}")
                globalMsgShower.submit(Message(f"音频播放失败: {e}", Message.ERROR_COLOR))
                return
        
        Thread(target=_play_preview, daemon=True).start()
    
    uiItems = [
        Button(*pos1k(80, 51), "创建谱面", "green", createChart, can_click_top_button),
        Button(*pos1k(462, 51), "导入谱面", "gray", None, can_click_top_button),
        Button(*pos1k(846, 51), "导出谱面", "gray", None, can_click_top_button),
        Button(*pos1k(1124, 192), "分组显示", "gray", None, can_click_top_button),
        Button(*pos1k(1507, 192), "排序方式", "gray", None, can_click_top_button),
        Button(*pos1k(78, 957), "删除谱面", "red", deleteChart, can_click_top_button),
        Button(*pos1k(1127, 957), "修改谱面信息", "yellow", None, can_click_top_button),
        Button(*pos1k(1509, 957), "进入编辑", "green", gotoEditor, can_click_top_button),
    ]
    
    chooser = ChartChooser(
        change_test=can_click_top_button,
        when_change=chooser_when_change
    )
    
    uiItems.append(chooser)
    globalUIManager.extend_uiitems(uiItems, "mainRender")
    updateIllus()
    
    while True:
        clearCanvas(wait_execute=True)
        
        if not getConfigData("charts"):
            drawText(
                w / 2, h / 2,
                "点击 “创建谱面” 后选择音乐、曲绘来创建你的第一张谱面",
                font = f"{(w + h) / 65}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = "white",
                wait_execute = True
            )
        else:
            charts = getConfigData("charts")
            chooser.update(charts)
            chosing_chart = charts[chooser.i]
            
            ctxSave(wait_execute=True)
            bgBlurRatio = (w + h) / 50
            bgScale = max((w + bgBlurRatio) / w, (h + bgBlurRatio) / h)
            ctxSetFilter(f"blur({bgBlurRatio}px)", wait_execute=True)
            ctxTranslate(w / 2, h / 2, wait_execute=True)
            ctxScale(bgScale, bgScale, wait_execute=True)
            ctxTranslate(-w / 2 * bgScale, -h / 2 * bgScale, wait_execute=True)
            drawCoverFullScreenImage(
                f"illu_{hashChartId(chosing_chart["id"])}",
                w * bgScale, h * bgScale, wait_execute=True
            )
            ctxRestore(wait_execute=True)
            
            fillRectEx(0, 0, w, h, "rgba(0, 0, 0, 0.6)", wait_execute=True)
            
            drawText(
                *pos1k(161, 202),
                chosing_chart["level"],
                font = f"{(w + h) / 65}px pgrFont",
                textAlign = "left",
                textBaseline = "middle",
                fillStyle = "white",
                wait_execute = True
            )
            
            drawText(
                *pos1k(161, 263),
                "谱面设计: " + chosing_chart["charter"],
                font = f"{(w + h) / 65}px pgrFont",
                textAlign = "left",
                textBaseline = "middle",
                fillStyle = "white",
                wait_execute = True
            )
            
            drawText(
                *pos1k(161, 820),
                chosing_chart["name"],
                font = f"{(w + h) / 60}px pgrFont",
                textAlign = "left",
                textBaseline = "middle",
                fillStyle = "white",
                wait_execute = True
            )
            
            drawText(
                *pos1k(161, 880),
                chosing_chart["composer"],
                font = f"{(w + h) / 80}px pgrFont",
                textAlign = "left",
                textBaseline = "middle",
                fillStyle = "white",
                wait_execute = True
            )
            
            
            utils.shadowDrawer.root = root
            for chart in charts:
                trs = chooser.tr_map[chart["id"]]
                size, center_pos = (trs[0].value, trs[1].value), (trs[2].value, trs[3].value)
                
                with utils.shadowDrawer("rgba(16, 16, 16, 0.8)", (w + h) / 150):
                    fillRectEx(
                    center_pos[0] - size[0] / 2,
                    center_pos[1] - size[1] / 2,
                    *size,
                    "black",
                    wait_execute=True
                )
                    
                drawCoverFullScreenImage(
                    f"illu_{hashChartId(chart["id"])}",
                    *size,
                    center_pos[0] - size[0] / 2,
                    center_pos[1] - size[1] / 2,
                    wait_execute=True
                )
        
        globalUIManager.render_bytag("mainRender")
        
        if createChartData is not None:
            fillRectEx(0, 0, w, h, "rgba(0, 0, 0, 0.2)", wait_execute=True)
            fillRectEx(*pos1k(261, 69 + 78), *pos1k(1920 - 261 * 2, 841), "rgba(64, 64, 64, 0.8)", wait_execute=True)
            fillRectEx(*pos1k(261, 69), *pos1k(1920 - 261 * 2, 80), "gray", wait_execute=True)
            drawText(
                *utils.getCenterPointByRect(utils.xywh_rect2_xxyy((*pos1k(261, 69), *pos1k(1920 - 261 * 2, 80)))),
                "添加谱面",
                font = f"{(w + h) / 65}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = "white",
                wait_execute = True
            )
            
            globalUIManager.render_bytag("mainRender-createChart")
        
        renderGlobalItems()
        
        root.run_js_wait_code()
        
        if needUpdateIllus:
            updateIllus()
            needUpdateIllus = False
        
        if nextUI is not None:
            globalUIManager.remove_ui_bytag("mainRender")
            dxsmixer_unix.mixer.music.fadeout(250)
            
            if illuPacker is not None:
                illuPacker.unload(illuPacker.getnames())
                
            Thread(target=nextUI, daemon=True).start()
            return


logging.info("Loading Window...")
root = webcv.WebCanvas(
    width = 1, height = 1,
    x = -webcv.screen_width, y = -webcv.screen_height,
    title = "phispler - editor",
    debug = "--debug" in sys.argv,
    resizable = False,
    renderdemand = True, renderasync = True
)

def init():
    global webdpr
    global w, h
    global Resource
    global globalUIManager, globalMsgShower
    
    if webcv.disengage_webview:
        socket_webviewbridge.hook(root)

    w, h, webdpr, _, _ = root.init_window_size_and_position(0.75)
    
    webdpr = root.run_js_code("window.devicePixelRatio;")
    
    if webdpr != 1.0:
        root.run_js_code(f"lowquality_scale = {1.0 / webdpr};")

    rw, rh = w, h
    root.run_js_code(f"resizeCanvas({rw}, {rh});")
    
    globalUIManager = UIManager()
    globalUIManager.bind_events()
    
    globalMsgShower = MessageShower()
    globalUIManager.extend_uiitems([globalMsgShower], "global")
    
    Resource = loadResource()

    # updateCoreConfig()

    Thread(target=mainRender, daemon=True).start()
    root.wait_for_close()
    atexit_run()

def atexit_run():
    tempdir.clearTempDir()
    needrelease.run()
    exitfunc(0)

Thread(target=root.init, args=(init, ), daemon=True).start()
root.start()
atexit_run()
