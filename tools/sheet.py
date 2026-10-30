"""Render PDF pages and tile them into contact sheets for a quick layout check."""
import sys

import fitz
from PIL import Image

pdf, prefix = sys.argv[1], sys.argv[2]
per_sheet, cols, width = 8, 4, 300
doc = fitz.open(pdf)
pages = []
for page in doc:
    pix = page.get_pixmap(dpi=40)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    pages.append(img.resize((width, round(img.height * width / img.width))))
height = max(p.height for p in pages)
for start in range(0, len(pages), per_sheet):
    chunk = pages[start:start + per_sheet]
    rows = (len(chunk) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (width + 10), rows * (height + 10)), "white")
    for i, img in enumerate(chunk):
        sheet.paste(img, ((i % cols) * (width + 10), (i // cols) * (height + 10)))
    out = f"{prefix}-{start // per_sheet + 1}.png"
    sheet.save(out)
    print(out, f"pages {start + 1}-{start + len(chunk)}")
