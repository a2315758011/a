# -*- coding: utf-8 -*-
"""使用本机Microsoft Edge无界面模式真实打开HTML Canvas并截屏到项目根目录。无生成模型。"""
from pathlib import Path
import os
import subprocess
import json
import shutil
import hashlib
from PIL import Image, ImageStat

d=Path(__file__).resolve().parent
project=d.parent
browser=Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
assert browser.exists(),"Microsoft Edge not found"
page=(d/"打开游戏.html").resolve().as_uri()+"?overview=1"
out=project/"00-项目玩法总览图.png"
profile=project/"_assistant-temp"/"edge-greybox-screenshot"
profile.mkdir(parents=True,exist_ok=True)
args=[str(browser),"--headless=new","--disable-gpu","--no-first-run",
      "--no-default-browser-check","--hide-scrollbars","--disable-extensions",
      f"--user-data-dir={profile}","--window-size=540,960",
      "--force-device-scale-factor=2",f"--screenshot={out}",page]
try:
    p=subprocess.run(args,capture_output=True,text=True,timeout=50,encoding="utf-8",errors="replace")
except subprocess.TimeoutExpired:
    raise SystemExit("EDGE_SCREENSHOT_TIMEOUT")
print("EDGE_EXIT",p.returncode)
print("EDGE_STDERR",p.stderr[-1500:])
assert out.exists() and out.stat().st_size>9000, "EDGE_DID_NOT_CREATE_PNG"
with Image.open(out) as im:
    print("ORIGINAL_SCREENSHOT",im.size,im.mode,im.format)
    # Chromium window inner viewport may differ by a few pixels; do not distort the real render.
    if im.size!=(1080,1920):
        # If only viewport issue on Edge, create alternative full screenshot using same real pixels.
        print("EDGE_VIEWPORT_NOTE_ACTUAL_SIZE",im.size)
    rgb=im.convert("RGB")
    stat=ImageStat.Stat(rgb)
    samples=[rgb.getpixel((min(x,rgb.width-1),min(y,rgb.height-1))) for x,y in [(5,5),(rgb.width//2,rgb.height//2),(rgb.width//2,rgb.height//3)]]
    print("SCREENSHOT_PIXELS",samples)
    assert max(stat.stddev)>15,"CANVAS_LOOKS_BLANK"
    w,h=im.size
    assert abs(w/h-9/16)<0.08,"WRONG_IMAGE_ASPECT_RATIO"
print("PNG_BYTES",out.stat().st_size)
print("PNG_SHA256",hashlib.sha256(out.read_bytes()).hexdigest())
print("SAVED",str(out))
