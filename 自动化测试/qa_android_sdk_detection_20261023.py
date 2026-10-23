from pathlib import Path
import subprocess, tempfile, os, json, shutil
project=Path(__file__).resolve().parents[1]
target=project/"自动化测试"/"平台发布环境预检.py"
def run(sdk):
 e=dict(os.environ,ANDROID_SDK_ROOT=str(sdk),PYTHONIOENCODING="utf-8")
 x=subprocess.run(["python","-X","utf8",str(target)],env=e,capture_output=True,text=True,encoding="utf-8",timeout=30,check=True)
 return json.loads(x.stdout)
with tempfile.TemporaryDirectory(prefix="turret-sdk-qa-") as d:
 base=Path(d)
 empty=run(base)
 assert not empty["gates"]["androidSdkReady"] and not empty["gates"]["androidNdkReady"],"empty-sdk false positive"
 (base/"platforms"/"android-32").mkdir(parents=True)
 (base/"platforms"/"android-32"/"android.jar").write_bytes(b"qa")
 (base/"build-tools"/"34.0.0").mkdir(parents=True)
 for name in ("aapt.exe","zipalign.exe"):
  (base/"build-tools"/"34.0.0"/name).write_bytes(b"qa")
 full=run(base)
 assert full["gates"]["androidSdkReady"] and not full["gates"]["androidNdkReady"],"sdk component selection"
 (base/"ndk"/"23.2.8568313").mkdir(parents=True)
 ndk=base/"ndk"/"23.2.8568313"
 for name in ("ndk-build.cmd","source.properties"): (ndk/name).write_text("qa",encoding="utf-8")
 all_=run(base)
 assert all_["gates"]["androidSdkReady"] and all_["gates"]["androidNdkReady"],"NDK component selection"
 print(json.dumps({"empty_sdk":"BLOCKED_CORRECTLY","populated_sdk":"READY_CORRECTLY","ndk_r23_fixture":"READY_CORRECTLY","result":"PASS"}))
