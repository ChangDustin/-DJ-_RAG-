"""Remove emoji (and the space after them) from the Word generator: Word 2007 shows them as empty boxes."""
import re
import shutil
import sys
from pathlib import Path

path = Path(sys.argv[1])
shutil.copyfile(path, path.with_suffix(".js.bak"))
text = path.read_text(encoding="utf-8")
pattern = re.compile("[\U0001F000-\U0001FFFF☀-➿⬀-⯿]️? ?")
new_text, count = pattern.subn("", text)
path.write_text(new_text, encoding="utf-8")
print("removed", count)
