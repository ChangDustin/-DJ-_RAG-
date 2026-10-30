"""Fill RAG_DATA_URL and point the RAG02 write-up cells at the Word file (only the Word file is submitted)."""
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
share_url = sys.argv[2]
nb = json.loads(path.read_text(encoding="utf-8"))
cells = nb["cells"]


def text(cell):
    return "".join(cell["source"])


def set_text(cell, value):
    lines = value.split("\n")
    cell["source"] = [line + "\n" for line in lines[:-1]] + [lines[-1]]


def markdown(value):
    cell = {"cell_type": "markdown", "metadata": {}, "source": []}
    set_text(cell, value)
    return cell


def find(prefix):
    matches = [i for i, c in enumerate(cells) if text(c).startswith(prefix)]
    if len(matches) != 1:
        raise SystemExit(f"expected one cell starting with {prefix!r}, found {len(matches)}")
    return matches[0]


# 1. rag-data.zip 的雲端分享連結
placeholder = "https://drive.google.com/file/d/請貼上rag-data.zip的檔案ID/view?usp=sharing"
url_cells = [c for c in cells if placeholder in text(c)]
if len(url_cells) != 1:
    raise SystemExit("RAG_DATA_URL placeholder not found exactly once")
set_text(url_cells[0], text(url_cells[0]).replace(placeholder, share_url))

# 2. 本作業 Colab 連結
intro = cells[find("---\n# 📝 作業說明")]
set_text(intro, text(intro).replace(
    "> 👉 **（在這裡貼上這份 Notebook 的分享連結）**",
    "> 👉 就是你現在開啟的這份 Notebook（分享連結也寫在繳交的 Word 檔第一節）。",
))

# 3. 對話截圖與重點截圖 → 一格說明
start, end = find("## 💬 Gradio 對話結果"), find("## 和老師範例的差異")
cells[start:end] = [markdown(
    "## 💬 Gradio 對話結果與重點截圖\n"
    "\n"
    "實際和 DJ「音痴」對話的截圖（婚禮歌推薦、多輪追問、百科模式、地區篩選、拒絕給歌詞、知識庫沒有的歌、RAG vs 純 LLM、歌單分頁），"
    "以及 RAG01／RAG02 的重點執行畫面，都整理在**繳交的 Word 檔第六、七節**，每段對話下面附上我的觀察。\n"
    "\n"
    "Gradio 的公開連結是臨時的，Colab 中斷後就不能用了，所以用截圖保存成果。"
)]

# 4. AI 協作說明 → 指向 Word 檔
diff_index = find("## 和老師範例的差異")
diff = text(cells[diff_index])
head, _, _ = diff.partition("## 🤖 AI 協作說明")
set_text(cells[diff_index], head + (
    "## 🤖 AI 協作說明（依作業規定特別說明）\n"
    "本作業有使用生成式 AI（Claude）協助。協助的部分、我的理解，以及對話截圖（Prompt 與生成結果）整理在**繳交的 Word 檔第九節**。"
))
del cells[find("### AI 對話截圖")]

path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("cells:", len(cells), "| code cells:", sum(c["cell_type"] == "code" for c in cells))
