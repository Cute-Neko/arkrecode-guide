from __future__ import annotations
import html
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
CHARACTERS = OUT / "characters"
REFERENCE = OUT / "reference"
NODE_GRAPH_SOURCE = ROOT / "node_validation" / "sep08_closure_audit" / "COMPLETE_BATTLE_NODE_GRAPH_V9_COMPACT_CONTROL_FLOW.svg"

def plain(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return html.unescape(re.sub(r"\s+", " ", value)).strip()

def candidates() -> dict[str, Path]:
    found: dict[str, Path] = {}
    patterns = [
        (ROOT / "combined_node_sheets", "h*-build-damage-node-sheet.html"),
    ]
    for folder, pattern in patterns:
        if not folder.exists():
            continue
        for path in sorted(folder.glob(pattern)):
            match = re.match(r"(h\d+)-build-damage-node-sheet\.html$", path.name, re.I)
            if match:
                found[match.group(1).lower()] = path
    return found

def inject_directory_link(text: str) -> str:
    style = """<style id="site-directory-link-style">
.site-directory-link{position:fixed;right:18px;bottom:18px;z-index:99999;padding:10px 15px;border-radius:999px;background:#172033;color:#fff!important;text-decoration:none;font:600 14px/1.2 "Microsoft YaHei UI","Noto Sans SC",sans-serif;box-shadow:0 8px 24px rgba(15,23,42,.24)}
.site-directory-link:hover{background:#2563eb}.site-directory-link:focus-visible{outline:3px solid #93c5fd;outline-offset:3px}
@media print{.site-directory-link{display:none}}
</style>"""
    link = '<a class="site-directory-link" href="../index.html" aria-label="返回角色目录">← 角色目录</a>'
    text = text.replace("</head>", style + "</head>", 1)
    return re.sub(r"<body([^>]*)>", r"<body\1>" + link, text, count=1, flags=re.I)

def read_card(code: str, path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    title_match = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    title = plain(title_match.group(1)) if title_match else code.upper()
    name_match = re.search(r"^(.*?)\s+" + re.escape(code.upper()) + r"\b", title, re.I)
    name = name_match.group(1).strip() if name_match else code.upper()
    subtitle_match = re.search(r'<p[^>]*class=["\'][^"\']*subtitle[^"\']*["\'][^>]*>(.*?)</p>', text, re.I | re.S)
    subtitle = plain(subtitle_match.group(1)) if subtitle_match else "配装、理论伤害与技能节点表"
    panel_match = re.search(r"(\d+)\s*套面板", subtitle)
    panels = panel_match.group(1) + " 套面板" if panel_match else "单面板"
    return {"id": code.upper(), "name": name, "title": title, "subtitle": subtitle, "panels": panels, "source": str(path.relative_to(ROOT)).replace("\\", "/")}

def build_index(cards: list[dict[str, str]]) -> str:
    card_html = []
    for card in cards:
        searchable = " ".join((card["id"], card["name"], card["title"], card["subtitle"])).lower()
        card_html.append(f'''<a class="card" href="characters/{card["id"].lower()}.html" data-search="{html.escape(searchable, quote=True)}">
  <div class="card-top"><span class="role-id">{html.escape(card["id"])}</span><span class="panel-count">{html.escape(card["panels"])}</span></div>
  <h2>{html.escape(card["name"])}</h2>
  <p>{html.escape(card["subtitle"])}</p>
  <span class="open">查看完整表 <b>→</b></span>
</a>''')
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Ark Re:Code 角色配装、理论伤害与技能节点资料">
<title>Ark Re:Code 角色资料库</title>
<style>
:root{{--ink:#172033;--muted:#64748b;--line:#dbe3ee;--blue:#2563eb;--soft:#f5f8fc}}
*{{box-sizing:border-box}}html{{color-scheme:light}}body{{margin:0;background:#fff;color:var(--ink);font-family:"Microsoft YaHei UI","Noto Sans SC",Arial,sans-serif}}
header{{border-bottom:1px solid var(--line);background:linear-gradient(135deg,#f8fbff 0%,#fff 58%,#eef6ff 100%)}}
.header-inner,main{{width:min(1180px,calc(100% - 36px));margin:auto}}.header-inner{{padding:46px 0 34px}}
.eyebrow{{margin:0 0 8px;color:var(--blue);font:700 13px/1.2 Consolas,monospace;letter-spacing:.12em}}
h1{{margin:0;font-size:clamp(28px,5vw,46px);line-height:1.16;letter-spacing:-.03em}}.intro{{max-width:720px;margin:12px 0 0;color:var(--muted);font-size:16px;line-height:1.7}}
main{{padding:28px 0 56px}}.toolbar{{display:flex;align-items:center;gap:14px;margin-bottom:22px}}
.search-wrap{{position:relative;flex:1}}.search-wrap span{{position:absolute;left:15px;top:50%;transform:translateY(-50%);color:#94a3b8}}
input{{width:100%;height:48px;padding:0 16px 0 44px;border:1px solid #cbd5e1;border-radius:12px;background:#fff;color:var(--ink);font-size:16px;outline:none}}
input:focus{{border-color:var(--blue);box-shadow:0 0 0 3px #bfdbfe}}.count{{white-space:nowrap;color:var(--muted);font-size:14px}}
.resources{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-bottom:26px}}.resource{{display:block;padding:18px 20px;border:1px solid #bfdbfe;border-radius:14px;background:#f8fbff;color:inherit;text-decoration:none}}.resource:hover{{border-color:#60a5fa;background:#eff6ff}}.resource b{{display:block;margin-bottom:5px;color:#1d4ed8;font-size:18px}}.resource span{{color:var(--muted);font-size:13px;line-height:1.6}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}
.card{{display:block;min-height:205px;padding:22px;border:1px solid var(--line);border-radius:16px;background:#fff;color:inherit;text-decoration:none;box-shadow:0 8px 28px rgba(15,23,42,.05);transition:.16s ease}}
.card:hover{{transform:translateY(-2px);border-color:#93c5fd;box-shadow:0 14px 34px rgba(37,99,235,.12)}}.card:focus-visible{{outline:3px solid #93c5fd;outline-offset:3px}}
.card-top{{display:flex;justify-content:space-between;align-items:center}}.role-id{{color:var(--blue);font:700 14px Consolas,monospace}}.panel-count{{padding:5px 9px;border-radius:999px;background:#eff6ff;color:#1d4ed8;font-size:12px;font-weight:700}}
.card h2{{margin:22px 0 7px;font-size:25px}}.card p{{margin:0;color:var(--muted);font-size:14px;line-height:1.65}}.open{{display:block;margin-top:22px;color:#334155;font-size:14px;font-weight:700}}.open b{{color:var(--blue);font-size:18px}}
.empty{{display:none;padding:42px;border:1px dashed #cbd5e1;border-radius:16px;text-align:center;color:var(--muted)}}footer{{width:min(1180px,calc(100% - 36px));margin:0 auto 36px;color:#94a3b8;font-size:13px}}
@media(max-width:720px){{.header-inner{{padding:34px 0 26px}}.toolbar{{align-items:stretch;flex-direction:column}}.resources,.grid{{grid-template-columns:1fr}}.card{{min-height:0}}}}
</style>
</head>
<body>
<header><div class="header-inner"><p class="eyebrow">ARK RE:CODE DATABASE</p><h1>角色技能与配装资料库</h1><p class="intro">按角色查看面板、六件装备、理论伤害和经过验证的技能节点表。</p></div></header>
<main>
<div class="resources" aria-label="全局资料"><a class="resource" href="reference/battle-node-graph.html"><b>完整战斗节点图 V9 →</b><span>人类可读的完整控制流：146 个节点、187 条边。</span></a><a class="resource" href="reference/damage-formula.html"><b>伤害计算乘区说明 →</b><span>基于逆向与解包数据，逐项解释公式、贯穿、增减伤和事件结算。</span></a></div>
<div class="toolbar"><label class="search-wrap"><span>⌕</span><input id="search" type="search" autocomplete="off" placeholder="搜索角色中文名或编号，例如：蜜娜、H804" aria-label="搜索角色"></label><span class="count" id="count">共 {len(cards)} 名角色</span></div>
<div class="grid" id="grid">{''.join(card_html)}</div>
<div class="empty" id="empty">没有找到对应角色。</div>
</main>

<script>
(function(){{
var input=document.getElementById("search");
var cards=Array.prototype.slice.call(document.querySelectorAll(".card"));
var count=document.getElementById("count");
var empty=document.getElementById("empty");
function filter(){{
  var q=input.value.trim().toLowerCase();
  var shown=0;
  cards.forEach(function(card){{var ok=!q||card.getAttribute("data-search").indexOf(q)>=0;card.hidden=!ok;if(ok)shown++;}});
  count.textContent=q ? "找到 "+shown+" 名角色" : "共 "+cards.length+" 名角色";
  empty.style.display=shown ? "none" : "block";
}}
input.addEventListener("input",filter);
}})();
</script>
</body>
</html>'''

def main() -> None:
    CHARACTERS.mkdir(parents=True, exist_ok=True)
    REFERENCE.mkdir(parents=True, exist_ok=True)
    if not NODE_GRAPH_SOURCE.exists():
        raise FileNotFoundError(f"缺少完整节点图：{NODE_GRAPH_SOURCE}")
    shutil.copy2(NODE_GRAPH_SOURCE, REFERENCE / "complete-battle-node-graph-v9.svg")
    for old in CHARACTERS.glob("*.html"):
        old.unlink()
    cards=[]
    for code,path in candidates().items():
        card=read_card(code,path)
        cards.append(card)
        target=CHARACTERS/(code+".html")
        target.write_text(inject_directory_link(path.read_text(encoding="utf-8")),encoding="utf-8")
    cards.sort(key=lambda c:int(re.search(r"\d+",c["id"]).group()))
    (OUT/"index.html").write_text(build_index(cards),encoding="utf-8")
    (OUT/"characters.json").write_text(json.dumps(cards,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/".nojekyll").write_text("",encoding="utf-8")
    print(json.dumps({"ok":True,"characters":len(cards),"ids":[c["id"] for c in cards],"output":str(OUT)},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
