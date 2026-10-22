#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""透明游戏资源的基础机械门禁；不替代地板/草地的人工语义检查。"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


def inspect_png(path: Path, expected_size=(256, 256), margin=2, minimum_transparent_ratio=0.1):
    fail = []
    passed = []
    try:
        with Image.open(path) as src:
            if src.format != "PNG":
                fail.append("FORMAT_NOT_PNG")
            if src.mode != "RGBA":
                fail.append("NOT_RGBA")
            img = src.convert("RGBA")
    except Exception as exc:
        return {"file": str(path), "status": "FAIL", "errors": ["OPEN_FAILURE:" + str(exc)]}
    w, h = img.size
    if expected_size and (w, h) != expected_size:
        fail.append(f"DIMENSION_MISMATCH:{w}x{h}_EXPECTED:{expected_size[0]}x{expected_size[1]}")
    a = img.getchannel("A")
    lo, hi = a.getextrema()
    if lo == 255 and hi == 255:
        fail.append("ALPHA_ALL_OPAQUE")
    if hi == 0:
        fail.append("ALPHA_ALL_TRANSPARENT")
    hst = a.histogram()
    transparent_ratio = hst[0] / (w * h)
    if transparent_ratio < minimum_transparent_ratio:
        fail.append("TOO_LITTLE_TRANSPARENT_AREA")
    bands = [a.crop((0, 0, w, margin)), a.crop((0, h-margin, w, h)),
             a.crop((0, 0, margin, h)), a.crop((w-margin, 0, w, h))]
    if any(b.getextrema()[1] != 0 for b in bands):
        fail.append("BORDER_NOT_CLEAN")
    bbox = a.getbbox()
    if not fail:
        passed.extend(["PNG_RGBA", "ALPHA_REAL", "BORDER_ALPHA_ZERO", "EXPECTED_DIMENSIONS"])
    return {"file": str(path), "status": "PASS_MACHINE_ONLY" if not fail else "FAIL",
            "errors": fail, "checksPassed": passed, "imagePx": [w,h],
            "alphaExtrema": [lo, hi], "fullyTransparentFraction": round(transparent_ratio,4),
            "alphaBoundingBox": bbox, "semanticGrassFloorReview": "MANUAL_REQUIRED",
            "runtimeAnimationReview": "ENGINE_REQUIRED"}


def self_test():
    with tempfile.TemporaryDirectory(prefix="turret-alpha-") as td:
        ok_path = Path(td) / "真实透明.png"
        good = Image.new("RGBA", (256,256), (0,0,0,0))
        d = ImageDraw.Draw(good)
        d.ellipse((65,50,187,212),fill=(50,110,190,255))
        good.save(ok_path)
        fail_path = Path(td) / "伪透明.png"
        Image.new("RGB",(256,256),(255,255,255)).save(fail_path)
        good_report = inspect_png(ok_path)
        bad_report = inspect_png(fail_path)
        success = good_report["status"] == "PASS_MACHINE_ONLY" and bad_report["status"] == "FAIL"
        print(json.dumps({"selfTest":"PASS" if success else "FAIL",
          "transparentCase":good_report,"opaqueCase":bad_report},ensure_ascii=False,indent=2))
        return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(description="验证游戏资源真实透明RGBA、尺寸、空边；绿草/地板语义需要人工和引擎叠图检查。")
    parser.add_argument("png", nargs="?", help="待验证的透明运行时 PNG")
    parser.add_argument("--width",type=int,default=256)
    parser.add_argument("--height",type=int,default=256)
    parser.add_argument("--margin",type=int,default=2)
    parser.add_argument("--self-test",action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.png:
        parser.error("需要PNG路径或 --self-test")
    result = inspect_png(Path(args.png), (args.width,args.height), args.margin)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result["status"]=="PASS_MACHINE_ONLY" else 1


if __name__ == "__main__":
    sys.exit(main())
