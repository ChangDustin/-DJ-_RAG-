"""Make the last RAG02 cell safe under "Run all": only stop the Gradio demo when STOP_DEMO is True."""
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
nb = json.loads(path.read_text(encoding="utf-8"))
cells = nb["cells"]


def text(cell):
    return "".join(cell["source"])


def set_text(cell, value):
    lines = value.split("\n")
    cell["source"] = [line + "\n" for line in lines[:-1]] + [lines[-1]]


[md] = [c for c in cells if text(c).startswith("## 20. 展示結束後：停止服務")]
set_text(md, "## 20. 展示結束後：停止服務\n\n「全部執行」不會關掉展示。展示結束後，把 STOP_DEMO 改成 True 再執行這一格，就會停止服務。")

[code] = [c for c in cells if c["cell_type"] == "code" and text(c).startswith("demo.close()")]
set_text(code, 'STOP_DEMO = False  # 展示結束後改成 True，再執行這一格停止服務\nif STOP_DEMO:\n    demo.close()\n    print("展示服務已停止。")')

path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("patched", path.name)
