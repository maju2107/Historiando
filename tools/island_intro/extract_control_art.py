"""Extract the supplied sticker buttons as transparent vectors (read-only PDF)."""
from pathlib import Path
import shutil
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/ui/historiando/controls"
OUT.mkdir(parents=True, exist_ok=True)
page = fitz.open(Path.home() / "Downloads/Adesivos_Historiando_A4_v4.pdf")[0]

def color(rgb):
    return "none" if rgb is None else "#" + "".join(f"{round(v*255):02x}" for v in rgb)

for letter, start in [("a", 1), ("y", 16)]:
    drawings = page.get_drawings()[start:start+5]
    box = drawings[0]["rect"] + (-1, -1, 1, 1)
    paths = []
    for drawing in drawings:
        commands, previous = [], None
        for item in drawing["items"]:
            kind, *points = item
            if previous != points[0]:
                commands.append(f"M{points[0].x:g},{points[0].y:g}")
            if kind == "c":
                commands.append("C" + " ".join(f"{p.x:g},{p.y:g}" for p in points[1:]))
            elif kind == "l":
                commands.append(f"L{points[1].x:g},{points[1].y:g}")
            else:
                raise ValueError(kind)
            previous = points[-1]
        if drawing["closePath"]:
            commands.append("Z")
        paths.append(f'<path d="{" ".join(commands)}" fill="{color(drawing["fill"])}" stroke="{color(drawing["color"])}" stroke-width="{drawing["width"] or 0:g}" fill-rule="{"evenodd" if drawing["even_odd"] else "nonzero"}"/>')
    (OUT / f"button_{letter}.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="132" height="132" viewBox="{box.x0:g} {box.y0:g} {box.width:g} {box.height:g}">\n'
        + "\n".join(paths) + "\n</svg>\n", encoding="utf-8")

shutil.copyfile(Path.home() / "Downloads/espiral guarana2.0 amarela (1).svg", OUT / "joystick_spiral.svg")
print("Extracted A/Y sticker vectors and copied the supplied spiral.")
