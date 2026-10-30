"""在本機依序執行 notebook 的 code cell（模擬 Colab 環境），用來測試 RAG01 / RAG02。

用法：python run_notebook.py <notebook.ipynb> <workdir> [--serve]
"""
import json
import os
import re
import sys
import time
import types
from pathlib import Path

notebook_path, workdir = Path(sys.argv[1]), Path(sys.argv[2])
serve = "--serve" in sys.argv
os.chdir(workdir)

# ---- 模擬 google.colab ----------------------------------------------------
colab = types.ModuleType("google.colab")
files_mod = types.SimpleNamespace(
    upload=lambda: {name: Path(name).read_bytes() for name in os.environ["FAKE_UPLOADS"].split(",")},
    download=lambda path: print(f"[fake download] {path}"),
)
userdata_mod = types.SimpleNamespace(get=lambda name: "fake-key-for-local-test")
colab.files, colab.userdata = files_mod, userdata_mod
colab.drive = types.SimpleNamespace(mount=lambda path: None)
google = types.ModuleType("google")
google.colab = colab
sys.modules.setdefault("google", google)
sys.modules["google.colab"] = colab

# ---- 假的 LLM：回傳引用取回片段的固定格式回答 ----------------------------
import aisuite


class _Choice:
    def __init__(self, text):
        self.message = types.SimpleNamespace(content=text)
        self.finish_reason = "stop"


class FakeCompletions:
    calls = []

    def create(self, model, messages, temperature=None, max_tokens=None, **kwargs):
        FakeCompletions.calls.append(messages)
        system = messages[0]["content"]
        user = messages[-1]["content"]
        if system.startswith("你是搜尋查詢改寫器"):
            latest = user.split("最新的問題：")[-1]
            text = "米津玄師 " + latest if "他" in latest else latest
        else:
            ids = re.findall(r'"片段編號": "([WJC]\d{2}-\d)"', user)
            if ids:
                text = f"（假回答）根據資料 [{ids[0]}]，" + ("這裡是凌晨兩點的頻率，我是音痴。" if "DJ「音痴」" in system else "百科模式。")
            else:
                text = "（假的純 LLM 回答）"
        return types.SimpleNamespace(choices=[_Choice(text)])


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.chat = types.SimpleNamespace(completions=FakeCompletions())


aisuite.Client = FakeClient

# ---- 把 plt.show() 改成存圖（CHART_DIR 有設定時）-------------------------
if os.environ.get("CHART_DIR"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    chart_counter = {"n": 0}

    def _save_show(*args, **kwargs):
        chart_counter["n"] += 1
        target = Path(os.environ["CHART_DIR"]) / f"chart_{chart_counter['n']}.png"
        plt.savefig(target, dpi=160, bbox_inches="tight")
        plt.close("all")
        print(f"[saved chart] {target}")

    plt.show = _save_show

# ---- 依序執行 code cell ----------------------------------------------------
cells = json.loads(notebook_path.read_text(encoding="utf-8"))["cells"]
namespace = {"__name__": "__main__"}
code_cells = [c for c in cells if c["cell_type"] == "code"]
for number, cell in enumerate(code_cells, start=1):
    source = "".join(cell["source"])
    lines = [line for line in source.splitlines() if not line.lstrip().startswith(("%", "!"))]
    source = "\n".join(lines)
    if "demo.close()" in source and "展示服務已停止" in source:
        continue  # 最後的關閉格留到測試完再執行
    if "demo.launch(" in source:
        source = source.replace("share=True, inline=True,", "share=False, prevent_thread_lock=True, server_port=7861,")
    print(f"\n===== cell {number}: {source.splitlines()[0][:70] if source.strip() else '(empty)'}")
    started = time.time()
    exec(compile(source, f"<cell {number}>", "exec"), namespace)
    print(f"----- cell {number} ok ({time.time() - started:.1f}s)")

print("\nALL CELLS OK")

if "chat_respond" in namespace:
    ns = namespace
    _, history, status, sources = ns["chat_respond"]("米津玄師的〈Lemon〉背後有什麼故事？", [], ns["MODE_DJ"], "全部", 4)
    print("chat 1 status:", status.splitlines()[0])
    _, history, status, sources = ns["chat_respond"]("那他第一次上紅白是什麼情況？", history, ns["MODE_DJ"], "日本", 4)
    print("chat 2 status:", status.splitlines()[0])
    print("history roles:", [m["role"] for m in history])
    plain, rag, src = ns["compare_respond"]("back number 的〈水平線〉是為了誰寫的？", "全部", 4)
    print("compare:", plain[:30], "|", rag[:40])
    for q in ["有什麼適合婚禮的歌？", "推薦幾首適合畢業典禮的歌", "哪些歌是動畫主題曲？", "失戀的時候聽什麼？"]:
        res = ns["search_documents"](q, 4)
        print(q, "->", [(r["doc_id"], r["metadata"]["title"], round(r["score"], 3)) for r in res])

if serve:
    print("READY http://127.0.0.1:7861", flush=True)
    while True:
        time.sleep(5)
