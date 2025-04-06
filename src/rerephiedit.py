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
import logging
import typing
import random
from threading import Thread
from os import popen
from os.path import exists, isfile
from ntpath import basename

import requests
from PIL import Image, ImageFilter
from pydub import AudioSegment

import webcv
import dxsound
import const
import uilts
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
from dxsmixer import mixer
from exitfunc import exitfunc
from graplib_webview import *

import load_extended as _

RRPEConfig_default = {
    "charts": []
}

RRPEConfig_chart_default = {
    
}

def saveRRPEConfig():
    try:
        with open("./rrpe_config.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(RRPEConfig, indent=4, ensure_ascii=False))
    except Exception as e:
        logging.error(f"rrpe_config.json save failed: {e}")

def loadRRPEConfig():
    global RRPEConfig
    
    RRPEConfig = RRPEConfig_default.copy()
    try:
        RRPEConfig.update(json.loads(open("./rrpe_config.json", "r", encoding="utf-8").read()))
    except Exception as e:
        logging.error(f"rrpe_config.json load failed: {e}")

def getConfigData(key: str):
    return RRPEConfig.get(key, RRPEConfig_default[key])

def setConfigData(key: str, value: typing.Any):
    RRPEConfig[key] = value

loadRRPEConfig()
saveRRPEConfig()

def loadResource():
    global globalNoteWidth
    global note_max_width, note_max_height
    global note_max_size_half
    global WaitLoading, LoadSuccess
    global chart_res
    global cksmanager
    
    logging.info("Loading Resource...")
    WaitLoading = mixer.Sound("./resources/WaitLoading.mp3")
    LoadSuccess = mixer.Sound("./resources/LoadSuccess.wav")
    LoadSuccess.set_volume(0.75)
    globalNoteWidth = w * const.NOTE_DEFAULTSIZE
    
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
        "le_warn": Image.open("./resources/le_warn.png"),
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
        
    respacker.reg_img(Resource["le_warn"], "le_warn")
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

logging.info("Loading Window...")
root = webcv.WebCanvas(
    width = 1, height = 1,
    x = -webcv.screen_width, y = -webcv.screen_height,
    title = "phispler - editor",
    debug = "--debug" in sys.argv,
    resizable = False,
    renderdemand = True, renderasync = True
)

def updateCoreConfig():
    global PhiCoreConfigObject
    
    PhiCoreConfigObject = phicore.PhiCoreConfig(
        SETTER = lambda vn, vv: globals().update({vn: vv}),
        root = root, w = w, h = h,
        chart_information = chart_information,
        chart_obj = chart_obj,
        Resource = Resource,
        globalNoteWidth = globalNoteWidth,
        note_max_size_half = note_max_size_half, audio_length = audio_length,
        raw_audio_length = raw_audio_length, show_start_time = float("nan"),
        chart_image = chart_image,
        chart_res = chart_res,
        cksmanager = cksmanager,
        showfps = True,
        debug = True, combotips = "EDITOR",
    )
    phicore.CoreConfigure(PhiCoreConfigObject)
    
class UIManager:
    def __init__(self):
        self.uiItems: list[BaseUI] = []
    
    def bind_events(self):
        def _bind_event(name: str, target_name: str, args_eval: str):
            apiname = f"uim_event_{target_name}"
            root.jsapi.set_attr(apiname, lambda *args: self._event_proxy(target_name, *args))
            root.run_js_code(f"window.addEventListener(\"{name}\", e => pywebview.api.call_attr(\"{apiname}\", {args_eval}));")
        
        _bind_event("mousemove", "mouse_move", "e.x, e.y")
        _bind_event("mousedown", "mouse_down", "e.x, e.y, e.button")
        _bind_event("mouseup", "mouse_up", "e.x, e.y, e.button")
        _bind_event("wheel", "mouse_wheel", "e.x, e.y, e.deltaY")
        _bind_event("keydown", "key_down", "e.key")
    
    def render(self, tag: str):
        for ui in self.uiItems:
            if ui.tag == tag:
                ui.render()
    
    def _event_proxy(self, name: str, *args):
        for ui in self.uiItems:
            getattr(ui, name)(*args)
    
    def extend_uiitems(self, items: list[BaseUI], tag: str):
        for item in items:
            item.tag = tag
            
        self.uiItems.extend(items)
    
    def remove_uiitems(self, tag: str):
        for i in self.uiItems.copy():
            if i.tag == tag:
                i.when_remove()
                self.uiItems.remove(i)
    
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
    def key_down(self, k: int): ...
    def key_up(self, k: int): ...
    def when_remove(self): ...

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
        self.x = x
        self.y = y
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
    
    def render(self):
        self.rect = drawRPEButton(
            self.x, self.y,
            self.text, self.color,
            scale = self.scale_value_tr.value,
            **({} if self.size is None else {"size": self.size}),
            fontscale = self.fontscale
        )
    
    def mouse_move(self, x: int, y: int):
        isin = uilts.inrect(x, y, self.rect)
        
        if isin != self.mouse_isin:
            self.scale_value_tr.target = 1.1 if isin else 1.0
            self.mouse_isin = isin
    
    def mouse_down(self, x: int, y: int, _):
        if uilts.inrect(x, y, self.rect) and self.command is not None:
            if self.test is None or self.test(x, y):
                self.command(x, y)

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
    
    def render(self):
        fillRectEx(self.x, self.y, self.width, self.height, "rgba(255, 255, 255, 0.5)", wait_execute=True)
        strokeRectEx(self.x, self.y, self.width, self.height, "white", (w + h) / 650, wait_execute=True)
        
        self.text = root.run_js_code(f"updateCanvasInput({self.id}, {self.x}, {self.y}, {self.width}, {self.height}, \"{self.font}\", {repr(self.default_text) if self.default_text is not None else "null"})")

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
    
    xywh_rect = uilts.xxyy_rect2_xywh(rect)
    
    ctxSave(wait_execute=True)
    ctxMutGlobalAlpha(0.8, wait_execute=True)
    fillRectEx(*xywh_rect, color, wait_execute=True)
    ctxRestore(wait_execute=True)
    
    strokeRectEx(*xywh_rect, "black", (w + h) / 650 * scale * fontscale, wait_execute=True)
    
    drawText(
        *uilts.getCenterPointByRect(rect),
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

def mainRender():
    nextUI = None
    
    topButtonLock = False
    createChartData = None
    
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
        
        globalUIManager.extend_uiitems(uilts.unfold_list([
            [
                Label(*pos1k(586, 283 + 133 * i), name, "white", f"{(w + h) / 75}px pgrFont", textBaseline="middle"),
                Input(*pos1k(885, 253 + 133 * i), "", f"{(w + h) / 110}px pgrFont", *pos1k(500, 60), default_text[0] if default_text else None, key)
            ]
            for i, (name, key, *default_text) in enumerate([
                ("谱面名称", "chartName"),
                ("作曲者", "chartComposer"),
                ("谱面设计", "chartCharter"),
                ("基础BPM", "chartBPM", "140"),
                ("基础线数", "chartLines", "24")
            ])
        ] + [
            Button(*pos1k(529, 883), "取消", "red", size=pos1k(210, 71), fontscale=0.7),
            Button(*pos1k(1183, 883), "确定", "green", size=pos1k(210, 71), fontscale=0.7),
        ]), "mainRender-createChart")
        topButtonLock = False
    
    def can_click_top_button(*_):
        return (
            not topButtonLock and
            createChartData is None
        )
    
    uiItems = [
        Button(*pos1k(80, 51), "创建谱面", "green", createChart, can_click_top_button),
        Button(*pos1k(462, 51), "导入谱面", "gray", None, can_click_top_button),
        Button(*pos1k(846, 51), "导出谱面", "gray", None, can_click_top_button),
        Button(*pos1k(1124, 192), "分组显示", "gray", None, can_click_top_button),
        Button(*pos1k(1507, 192), "排序方式", "gray", None, can_click_top_button),
        Button(*pos1k(78, 957), "删除谱面", "red", None, can_click_top_button),
        Button(*pos1k(1127, 957), "修改谱面信息", "yellow", None, can_click_top_button),
        Button(*pos1k(1509, 957), "进入编辑", "green", None, can_click_top_button),
    ]
    
    globalUIManager.extend_uiitems(uiItems, "mainRender")
    
    while True:
        clearCanvas(wait_execute=True)
        
        globalUIManager.render("mainRender")
        
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
        
        if createChartData is not None:
            fillRectEx(0, 0, w, h, "rgba(0, 0, 0, 0.2)", wait_execute=True)
            fillRectEx(*pos1k(261, 69 + 78), *pos1k(1920 - 261 * 2, 841), "rgba(64, 64, 64, 0.8)", wait_execute=True)
            fillRectEx(*pos1k(261, 69), *pos1k(1920 - 261 * 2, 80), "gray", wait_execute=True)
            drawText(
                *uilts.getCenterPointByRect(uilts.xywh_rect2_xxyy((*pos1k(261, 69), *pos1k(1920 - 261 * 2, 80)))),
                "添加谱面",
                font = f"{(w + h) / 65}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = "white",
                wait_execute = True
            )
            
            globalUIManager.render("mainRender-createChart")
        
        root.run_js_wait_code()
        if nextUI is not None:
            globalUIManager.remove_uiitems("mainRender")
            Thread(target=nextUI, daemon=True).start()
            return

def init():
    global webdpr
    global w, h
    global Resource
    global globalUIManager
    
    if webcv.disengage_webview:
        socket_webviewbridge.hook(root)

    w, h, webdpr, _, _ = root.init_window_size_and_position(0.6)
    
    webdpr = root.run_js_code("window.devicePixelRatio;")
    
    if webdpr != 1.0:
        root.run_js_code(f"lowquality_scale = {1.0 / webdpr};")

    rw, rh = w, h
    root.run_js_code(f"resizeCanvas({rw}, {rh});")
    
    globalUIManager = UIManager()
    globalUIManager.bind_events()
    
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
