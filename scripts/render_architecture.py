"""Render Resolve's Atlas diagrams with only the Python standard library.

Adapts the Rootweaver Atlas renderer's palette, icon strokes, text and labelled
request/result convention. Models live in docs/diagrams/models.json. No runtime
telemetry is represented by animation. The original platform renderer is unchanged.
"""
import hashlib
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/diagrams"
COLORS = {"paper": "#f7f6f2", "ink": "#26313a", "muted": "#53606a", "accent": "#7146e8", "line": "#d9d7ce", "result": "#64727a"}
ICONS = {
    "terminal": '<rect x="-17" y="-12" width="34" height="24" rx="3"/><path d="M-11,-5 L-5,0 L-11,5 M0,6 H10"/>',
    "database": '<ellipse cx="0" cy="-10" rx="16" ry="6"/><path d="M-16,-10 V11 C-16,19 16,19 16,11 V-10 M-16,0 C-16,8 16,8 16,0"/>',
    "network": '<circle r="5"/><path d="M-4,-4 L-12,-12 M4,-4 L12,-12 M0,5 V15"/><circle cx="-14" cy="-14" r="4"/><circle cx="14" cy="-14" r="4"/><circle cy="18" r="4"/>',
    "human": '<circle cy="-9" r="7"/><path d="M-15,17 V12 C-15,-1 15,-1 15,12 V17"/>',
    "shield": '<path d="M0,-18 L15,-11 V1 Q15,12 0,20 Q-15,12 -15,1 V-11 Z M-7,0 L-1,6 L8,-5"/>',
    "model": '<path d="M-15,-6 L0,-16 L15,-6 V10 L0,19 L-15,10 Z M-15,-6 L0,3 L15,-6 M0,3 V19"/>',
    "clock": '<circle r="17"/><path d="M0,-10 V0 L8,5"/>',
}


def text(x, y, value, size=16, color="ink", weight=400, anchor="start"):
    return f'<text x="{x}" y="{y}" fill="{COLORS.get(color, color)}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>'


def render(model, animated):
    width, height = model.get("width", 1280), model.get("height", 820)
    css = "@keyframes flow{to{stroke-dashoffset:-24}}.motion{animation:flow 1.6s linear 3}@media(prefers-reduced-motion:reduce){.motion{display:none;animation:none}}@media print{.motion{display:none;animation:none}}"
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc"><title id="title">{escape(model["title"])}</title><desc id="desc">{escape(model["description"])} Animation illustrates direction only, not live traffic or measured timing.</desc><defs>']
    for name, color in [("action", COLORS["accent"]), ("result", COLORS["result"])]:
        svg.append(f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M1,1 L9,5 L1,9 Z" fill="{color}"/></marker>')
    svg.append(f'<pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".6" fill="#ddd9d0"/></pattern><style>{css if animated else ""}</style></defs><rect width="{width}" height="{height}" fill="{COLORS["paper"]}"/><g font-family="Arial, Helvetica, sans-serif">')
    svg.extend([text(44, 36, "ROOTWEAVER RESOLVE / ATLAS / " + model["kicker"], 12, "accent", 700), text(44, 83, model["title"], 32, weight=600), text(44, 117, model["subtitle"], 17, "muted")])
    svg.append(f'<rect x="40" y="150" width="1200" height="{height-270}" fill="url(#dots)"/>')
    for group in model.get("groups", []):
        svg.append(f'<rect x="{group["x"]}" y="{group["y"]}" width="{group["w"]}" height="{group["h"]}" rx="14" fill="#fff" fill-opacity=".45" stroke="{COLORS["line"]}" stroke-dasharray="{group.get("dash", "none")}"/>')
        svg.append(text(group["x"] + 18, group["y"] + 27, group["label"], 14, "muted", 600))
    for i, edge in enumerate(model["edges"]):
        d = "M" + " L".join(f"{x},{y}" for x, y in edge["points"])
        result = edge.get("kind") == "result"
        color = COLORS["result" if result else "accent"]
        dash = ' stroke-dasharray="5 6"' if result else ""
        svg.append(f'<path id="edge-{i}" d="{d}" fill="none" stroke="{color}" stroke-width="1.8" marker-end="url(#{"result" if result else "action"})"{dash}/>')
        if animated:
            svg.append(f'<path class="motion" aria-hidden="true" d="{d}" fill="none" stroke="{color}" stroke-width="3.3" stroke-opacity=".55" stroke-dasharray="2 22"/>')
        if edge.get("label"):
            x, y = edge["label_position"]
            w = edge.get("label_width", len(edge["label"]) * 8 + 18)
            svg.append(f'<rect x="{x-w/2}" y="{y-17}" width="{w}" height="25" rx="6" fill="{COLORS["paper"]}"/>')
            svg.append(text(x, y, edge["label"], 15, "muted" if result else "accent", anchor="middle"))
    for node in model["nodes"]:
        x, y, w, h = node["x"], node["y"], node.get("w", 310), node.get("h", 144)
        svg.append(f'<g data-node="{node["id"]}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#fff" stroke="{COLORS["line"]}"/><circle cx="{x+34}" cy="{y+35}" r="22" fill="#f1ecff" stroke="#c9b8f7"/><g transform="translate({x+34},{y+35}) scale(.7)" fill="none" stroke="{COLORS["accent"]}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS[node["icon"]]}</g>')
        svg.append(text(x + 66, y + 31, node["title"], node.get("title_size", 19), weight=600))
        svg.append(text(x + 66, y + 54, node["role"], 13, "accent"))
        for j, line in enumerate(node["detail"]):
            svg.append(text(x + 18, y + 88 + 23 * j, line, 16, "muted"))
        svg.append("</g>")
    for note in model.get("annotations", []):
        svg.append(text(note["x"], note["y"], note["text"], note.get("size", 16), note.get("color", "muted"), note.get("weight", 400)))
    svg.append(f'<path d="M44,{height-100} H1236" stroke="{COLORS["line"]}"/>')
    svg.append(text(44, height - 70, "Solid arrows: action / request   ·   Dotted arrows: returned evidence / result", 14, "muted"))
    svg.append(text(44, height - 40, model["footer"], 14, "muted"))
    svg.append("</g></svg>\n")
    return "".join(svg)


def main():
    source = OUT / "models.json"
    models = json.loads(source.read_text())["diagrams"]
    inventory = {}
    for model in models:
        for animated in [True, False]:
            name = model["id"] + (".svg" if animated else ".static.svg")
            content = render(model, animated)
            (OUT / name).write_text(content)
            inventory[name] = hashlib.sha256(content.encode()).hexdigest()
    manifest = {"schema": "resolve-atlas-diagrams/v1", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "files": inventory, "animation": "Illustrative direction; stops after 4.8 seconds; suppressed for reduced motion and print", "owner_acceptance": "pending"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Rendered {len(models)} Atlas views with animated and static exports")


if __name__ == "__main__":
    main()
