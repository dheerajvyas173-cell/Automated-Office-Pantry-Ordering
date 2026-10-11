"""Checks the generated canvas app source (Src/*.pa.yaml) before it is packed.

Run: python3 power-apps/canvas-app/validate_app.py
Exits non-zero on errors. Checks:
  * every property is documented for its control type (Studio reports PA2108 otherwise),
  * enum values (ButtonAppearance.Primary, ...) exist, and control names are unique,
  * layout, by laying every screen out the way auto-layout containers do, at several screen sizes:
    nothing overflows its container, controls in manual containers and gallery templates stay
    inside their parent and don't overlap, and text/buttons are big enough for their content.
"""
import itertools
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REF = json.load(open(os.path.join(HERE, "control_reference.json")))

GEOMETRY = {"X", "Y", "Width", "Height", "Visible", "DisplayMode"}
LAYOUT_CHILD = set(REF["layoutChild"])
NOT_ENUMS = {"ThisItem", "ThisRecord", "Self", "Parent", "App", "User", "Host"}
ENUMS = set(REF["enums"])
ENUM_TYPES = {e.split(".")[0] for e in ENUMS} - NOT_ENUMS
SCREENS = ((1366, 768), (1280, 720), (1920, 1080))   # design size first
# Controls drawn underneath others on purpose (backgrounds, selection markers, dividers, overlays).
BACKGROUND = re.compile(r"(Image|SelBar|Divider)$")

errors, warnings = {}, {}


def err(msg):
    errors.setdefault(msg, None)


def allowed(type_, in_auto_layout):
    name = type_.split("@")[0]
    props = set(REF["controls"].get(name, ())) | GEOMETRY
    if not name.startswith("Modern"):
        props |= set(REF["common"])
    if in_auto_layout:
        props |= LAYOUT_CHILD
    return props


def walk(children, parent, out):
    for entry in children or []:
        (name, body), = entry.items()
        node = {"name": name, "type": body["Control"], "variant": body.get("Variant", ""),
                "props": {k: str(v).lstrip("=") for k, v in (body.get("Properties") or {}).items()},
                "parent": parent, "children": []}
        out.append(node)
        if parent is not None:
            parent["children"].append(node)
        walk(body.get("Children"), node, out)


def num(expr, env, default=None):
    """Evaluates a size/position formula; None when it isn't plain arithmetic."""
    if expr is None:
        return default
    s = str(expr)
    for _ in range(3):
        m = re.fullmatch(r"If\(App\.(Width|Height) ([<>]=?) (\d+), (.+?), (.+)\)", s)
        if not m:
            break
        a = env[f"App.{m.group(1)}"]
        cond = eval(f"{a} {m.group(2)} {m.group(3)}")
        s = m.group(4) if cond else m.group(5)
    for k in sorted(env, key=len, reverse=True):
        s = s.replace(k, str(env[k]))
    if not re.fullmatch(r"[\d\s.+\-*/()<>=]+", s):
        return default
    try:
        return eval(s, {"__builtins__": {}})
    except Exception:
        return default


def visible(node, env):
    v = node["props"].get("Visible")
    if v is None:
        return True
    r = num(v, env)
    return bool(r) if r is not None else v != "false"


def literal_width(node):
    """Rough width of a literal label (Segoe UI averages ~0.55em per character)."""
    p = node["props"]
    value = p.get("Text", p.get("Content", ""))
    m = re.fullmatch(r'"([^"]*)"', value)
    if m:
        return len(m.group(1)) * float(p.get("Size", 14)) * 0.55
    # A formula choosing between messages (If/Switch): its longest message must fit too.
    choices = [c for c in re.findall(r'"([^"]*)"', value) if len(c) > 20]
    return max(len(c) for c in choices) * float(p.get("Size", 14)) * 0.55 if choices else None


def check_content(n, w, h, where):
    kind = n["type"].split("@")[0]
    p = n["props"]
    if kind == "ModernText":
        line = float(p.get("Size", 14)) * 1.33
        if h < line:
            err(f"{n['name']}: {h:.0f}px tall clips its size {p.get('Size', 14)} text ({where})")
        tw = literal_width(n)
        lines = int(h // line) if p.get("Wrap", "true") != "false" else 1   # modern text wraps by default
        if tw and tw > (w - 4) * max(1, lines):
            err(f"{n['name']}: text needs ~{tw:.0f}px but has {max(1, lines)} line(s) of {w:.0f}px ({where})")
    elif kind == "ModernButton":
        tw = literal_width(n)
        icon_only = "IconOnly" in p.get("Layout", "") and w < 80
        if tw and not icon_only and tw + 32 + (24 if "Icon" in p else 0) > w:
            err(f"{n['name']}: button needs ~{tw + 32 + (24 if 'Icon' in p else 0):.0f}px, is {w:.0f}px ({where})")
    elif kind == "ModernBadge":
        tw = literal_width(n)
        if tw and tw + 16 > w:
            err(f"{n['name']}: badge needs ~{tw + 16:.0f}px, is {w:.0f}px ({where})")


def layout(n, w, h, env, where):
    n.setdefault("sizes", []).append((w, h))
    check_content(n, w, h, where)
    if n["variant"] == "AutoLayout":
        auto(n, w, h, env, where)
    elif n["variant"] == "ManualLayout":
        manual(n, w, h, {**env, "Parent.Width": w, "Parent.Height": h}, where)
    elif n["type"].startswith("Gallery"):
        th = float(n["props"]["TemplateSize"])
        tw = w / float(n["props"].get("WrapCount", 1))
        manual(n, tw, th, {**env, "Parent.TemplateWidth": tw, "Parent.TemplateHeight": th,
                           "Parent.Width": w, "Parent.Height": h}, f"{where}, template {tw:.0f}px")


def auto(c, w, h, env, where):
    p = c["props"]
    horiz = p.get("LayoutDirection") == "LayoutDirection.Horizontal"
    pl, pr, pt, pb = (float(p.get(k, 0)) for k in ("PaddingLeft", "PaddingRight", "PaddingTop", "PaddingBottom"))
    iw, ih = w - pl - pr, h - pt - pb
    inner_main, inner_cross = (iw, ih) if horiz else (ih, iw)
    main, cross = ("Width", "Height") if horiz else ("Height", "Width")
    min_key = "LayoutMinWidth" if horiz else "LayoutMinHeight"
    kids = [k for k in c["children"] if visible(k, env)]
    cenv = {**env, "Parent.Width": w, "Parent.Height": h}
    sizes, flex = {}, []
    for k in kids:
        if "FillPortions" not in k["props"]:
            err(f"{k['name']}: FillPortions not set inside auto-layout {c['name']} (Studio default is ambiguous)")
        fp = num(k["props"].get("FillPortions", "0"), cenv, 0)
        if fp:
            flex.append((k, fp, num(k["props"].get(min_key), cenv, 0)))
        else:
            v = num(k["props"].get(main), cenv)
            if v is None:
                warnings.setdefault(f"{k['name']}: {main} not evaluated ({where})")
                v = 0
            sizes[k["name"]] = v
    remaining = inner_main - sum(sizes.values()) - float(p.get("LayoutGap", 0)) * max(0, len(kids) - 1)
    while flex:
        total = sum(fp for _, fp, _ in flex)
        pinned = [(k, fp, mn) for k, fp, mn in flex if remaining * fp / total < mn]
        if not pinned:
            for k, fp, _ in flex:
                sizes[k["name"]] = remaining * fp / total
            break
        for k, fp, mn in pinned:
            sizes[k["name"]] = mn
            remaining -= mn
            flex.remove((k, fp, mn))
    used = sum(sizes.values()) + float(p.get("LayoutGap", 0)) * max(0, len(kids) - 1)
    scroll = "Scroll" in p.get("LayoutOverflowX" if horiz else "LayoutOverflowY", "")
    if used > inner_main + 0.5 and not scroll:
        err(f"{c['name']}: children need {used:.0f}px of {main.lower()} but only {inner_main:.0f}px fit ({where})")
    for k in kids:
        stretch = p.get("LayoutAlignItems") == "LayoutAlignItems.Stretch" or \
            k["props"].get("AlignInContainer") == "AlignInContainer.Stretch"
        cv = inner_cross if stretch else num(k["props"].get(cross), cenv)
        if cv is None:
            warnings.setdefault(f"{k['name']}: {cross} not evaluated ({where})")
            continue
        if cv > inner_cross + 0.5:
            err(f"{k['name']}: {cross.lower()} {cv:.0f}px doesn't fit {c['name']} ({inner_cross:.0f}px inside padding, {where})")
        kw, kh = (sizes[k["name"]], cv) if horiz else (cv, sizes[k["name"]])
        layout(k, kw, kh, env, where)


def manual(c, W, H, env, where):
    boxes = []
    for k in c["children"]:
        p = k["props"]
        w, h = num(p.get("Width"), env), num(p.get("Height"), env)
        senv = {**env, "Self.Width": w, "Self.Height": h}
        x, y = num(p.get("X", "0"), senv), num(p.get("Y", "0"), senv)
        if None in (x, y, w, h):
            warnings.setdefault(f"{k['name']}: position not evaluated ({where})")
            continue
        if w <= 0 or h <= 0:
            err(f"{k['name']}: collapses to {w:.0f}x{h:.0f} in {c['name']} ({where})")
        elif x < -0.5 or y < -0.5 or x + w > W + 0.5 or y + h > H + 0.5:
            err(f"{k['name']}: ({x:.0f},{y:.0f}) {w:.0f}x{h:.0f} sticks out of {c['name']} {W:.0f}x{H:.0f} ({where})")
        if "type" in c and not BACKGROUND.search(k["name"]) and p.get("Visible") != "false":
            boxes.append((k, x, y, w, h))
        layout(k, w, h, env, where)
    for (a, ax, ay, aw, ah), (b, bx, by, bw, bh) in itertools.combinations(boxes, 2):
        if ax < bx + bw - 0.5 and bx < ax + aw - 0.5 and ay < by + bh - 0.5 and by < ay + ah - 0.5:
            va, vb = a["props"].get("Visible", ""), b["props"].get("Visible", "")
            if va and vb and (va == f"!({vb})" or vb == f"!({va})"):
                continue    # never shown together
            err(f"{a['name']} overlaps {b['name']} in {c['name']} ({where})")


def main():
    src = os.path.join(HERE, "Src")
    names = {}
    for fname in sorted(os.listdir(src)):
        if not fname.endswith("Screen.pa.yaml"):
            continue
        doc = yaml.safe_load(open(os.path.join(src, fname)))
        for screen, body in doc["Screens"].items():
            nodes, roots = [], []
            walk(body.get("Children"), None, nodes)
            for n in nodes:
                if n["name"] in names:
                    err(f"duplicate control name {n['name']} ({fname} and {names[n['name']]})")
                names[n["name"]] = fname
                auto_parent = n["parent"] is not None and n["parent"]["variant"] == "AutoLayout"
                ok = allowed(n["type"], auto_parent)
                for k, v in n["props"].items():
                    if k not in ok:
                        err(f"{n['name']} ({n['type']}): unknown property {k}")
                    for e in re.findall(r"(?<![\w'.@\]])([A-Z][A-Za-z]+\.'?[A-Za-z0-9]+'?)", v):
                        if e.split(".")[0] in ENUM_TYPES and e not in ENUMS:
                            err(f"{n['name']}.{k}: unknown enum value {e}")
            for sw, sh in SCREENS:
                env = {"App.Width": sw, "App.Height": sh, "Parent.Width": sw, "Parent.Height": sh}
                manual({"name": screen, "children": [n for n in nodes if n["parent"] is None]}, sw, sh, env,
                       f"{screen} at {sw}x{sh}")
    for msg in warnings:
        print("warning:", msg)
    for msg in errors:
        print("ERROR:", msg)
    print(f"{len(names)} controls checked at {', '.join(f'{w}x{h}' for w, h in SCREENS)}: "
          f"{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
