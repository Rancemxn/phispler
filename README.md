# phispler

![MIT License](https://img.shields.io/badge/license-MIT-yellow)
![Language](https://img.shields.io/badge/language-python-brightgreen)

> (1) 本项目是一款仿制作品，原作为Pigeon Games 鸽游创作的《Phigros》。
>
> (2) 本项目仅为研究学习目的，不可商业使用、违法使用。

## 简单的部分功能介绍

- `main.py`: 谱面模拟器
- `phigros.py`: 还原Phigros游戏界面

## 环境配置

- Python 版本: `3.12.8`
- Windows

```batch
git clone https://github.com/qaqFei/phispler
cd phispler\src
pip install -r requirements.txt
python main.py <chart> [args] [kwargs]
```

- Termux (运行 `main.py` 后访问 `https://qaqfei.github.io/phispler/src/web_canvas.html` 并触发 `touchstart` 连接 `127.0.0.1` 即可)

```bash
curl https://qaqfei.github.io/phispler/src/termux_install.sh -o install.sh
chmod 777 install.sh
./install.sh

cd phispler/src
python main.py <chart> --disengage-webview [args] [kwargs]
```

## 使用 `phigros.py`

自行探索。

## 谱面兼容

- [x] phi
  - [x] formatVersion
    - [x] 1
    - [x] 2
    - [x] 3
  - [x] offset
  - [x] judgeLineList
    - [x] bpm
    - [x] notesAbove
    - [x] notesBelow
    - [x] speedEvents
    - [x] judgeLineMoveEvents
    - [x] judgeLineRotateEvents
    - [x] judgeLineDisappearEvents
- [x] rpe
  - [x] BPMList
  - [x] META (无法获取info文件时读取)
    - [x] RPEVersion (???, 参见 RPEVersion 特殊处理)
    - [x] background
    - [x] charter
    - [x] composer
    - [ ] id
    - [x] level
    - [x] name
    - [x] offset
    - [x] song
  - [x] judgeLineList
    - [x] Texture
    - [x] bpmfactor
    - [x] father
    - [x] isCover
    - [x] isGif
    - [x] eventLayers
      - [ ] gifEvents (???)
      - [x] alphaEvents
      - [x] moveXEvents
      - [x] moveYEvents
      - [x] rotateEvents
      - [x] speedEvents
    - [x] extended
      - [x] colorEvents
      - [ ] inclineEvents (???)
      - [x] scaleXEvents
      - [x] scaleYEvents
      - [ ] paintEvents (???)
      - [x] textEvents
    - [x] notes
      - [x] startTime
      - [x] endTime
      - [x] above
      - [x] alpha
      - [x] isFake
      - [x] positionX
      - [x] size
      - [x] speed
      - [x] type
      - [x] visibleTime
      - [x] yOffset
      - [x] hitsound
      - [ ] tint (PhiZone)
      - [ ] tintHitEffects (PhiZone)
    - [ ] alphaControl
    - [ ] posControl
    - [ ] sizeControl
    - [ ] skewControl
    - [ ] yControl
    - [x] zOrder
- [x] pec
  - [x] 读取转换为 `rpe` 格式
- [x] extra
  - [x] bpm
  - [x] videos
    - [x] path
    - [x] time
    - [x] scale
    - [x] alpha
    - [x] dim
    - [ ] zIndex (PhiZone)
    - [ ] attach (PhiZone)
  - [x] effects
    - [x] start
    - [x] end
    - [x] shader (由于 WebGL 与 OpenGL 的差异, 部分效果无法实现)
    - [x] global
    - [ ] targetRange (PhiZone)
    - [x] vars
- [x] phira resource pack
  - [x] click.png
  - [x] click_mh.png
  - [x] drag.png
  - [x] drag_mh.png
  - [x] hold.png
  - [x] hold_mh.png
  - [x] flick.png
  - [x] flick_mh.png
  - [x] hit_fx.png
  - [x] click.ogg
  - [x] drag.ogg
  - [x] flick.ogg
  - [ ] ending.mp3
  - [ ] info.yml
    - [x] name
    - [x] author
    - [x] description
    - [x] hitFx
    - [x] holdAtlas
    - [x] holdAtlasMH
    - [x] hitFxDuration
    - [x] hitFxScale
    - [x] hitFxRotate
    - [x] hitFxTinted
    - [x] hideParticles
    - [x] holdKeepHead
    - [ ] holdRepeat
    - [x] holdCompact
    - [x] colorPerfect
    - [x] colorGood

## 鸣谢

- [7z](https://github.com/ip7z/7zip)
- [libogg](https://github.com/gcp/libogg)
- [libvorbis](https://github.com/xiph/vorbis)
- [oggvorbis2fsb5](https://github.com/uyjulian/oggvorbis2fsb5)
