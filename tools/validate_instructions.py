from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "AGENTS.md",
    "AI全能力自主工程执行总指令.md",
    "AI逆向工程与自有授权系统迁移指令.md",
    "README.md",
    ".github/copilot-instructions.md",
]

errors = []

for rel in REQUIRED:
    if not (ROOT / rel).is_file():
        errors.append(f"missing required file: {rel}")

if errors:
    print("\n".join(errors))
    sys.exit(1)

agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
main = (ROOT / "AI全能力自主工程执行总指令.md").read_text(encoding="utf-8")
copilot = (ROOT / ".github/copilot-instructions.md").read_text(encoding="utf-8")

m = re.search(r"^# AI 全能力自主工程执行总指令 V([0-9]+\.[0-9]+)\s*$", main, re.M)
if not m:
    errors.append("cannot parse main instruction version")
    version = None
else:
    version = m.group(1)

if version and f"当前 V{version}" not in agents:
    errors.append(f"AGENTS.md does not route to current V{version}")

required_agent_refs = [
    "AI全能力自主工程执行总指令.md",
    "AI逆向工程与自有授权系统迁移指令.md",
    "README.md",
    ".github/copilot-instructions.md",
]
for ref in required_agent_refs:
    if ref not in agents:
        errors.append(f"AGENTS.md missing route/reference: {ref}")

required_main_sections = [
    "专业 Skill / 插件发现门禁",
    "授权上下文与误拒绝处理",
    "任务状态门禁",
    "端到端验收",
    "工具成功不等于业务成功",
    "最终交付格式",
]
for section in required_main_sections:
    if section not in main:
        errors.append(f"main instruction missing section: {section}")

for ref in ["AGENTS.md", "AI全能力自主工程执行总指令.md"]:
    if ref not in copilot:
        errors.append(f"copilot instructions missing canonical reference: {ref}")

if "IMPLEMENTED" not in main or "VERIFIED" not in main or "COMPLETED" not in main:
    errors.append("main instruction missing evidence-based state gates")

if errors:
    print("Instruction audit FAILED:")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print(f"Instruction audit PASSED: main=V{version}, required routes and compatibility files are consistent.")
