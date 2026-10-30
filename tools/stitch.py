"""Stitch vertically scrolled screenshots of the same page region into one image.

usage: python stitch.py OUT.png TOP BOTTOM VIEW_H IMG1:SCROLL_Y1 [IMG2:SCROLL_Y2 ...]
TOP/BOTTOM are document rows (CSS px) to keep; VIEW_H is the viewport height in CSS px.
Each image is a full-height capture of the viewport taken at that scroll position.
"""
import sys

from PIL import Image

out, top, bottom, view_h = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
shots = []
for arg in sys.argv[5:]:
    path, scroll_y = arg.rsplit(":", 1)
    shots.append((Image.open(path).convert("RGB"), float(scroll_y)))

scale = shots[0][0].height / view_h
canvas = Image.new("RGB", (shots[0][0].width, round((bottom - top) * scale)), "black")
for image, scroll_y in shots:
    start, end = max(top, scroll_y), min(bottom, scroll_y + view_h)
    if end <= start:
        continue
    piece = image.crop((0, round((start - scroll_y) * scale), image.width, round((end - scroll_y) * scale)))
    canvas.paste(piece, (0, round((start - top) * scale)))
canvas.save(out)
print(out, canvas.size)
