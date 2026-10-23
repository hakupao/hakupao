"""Generate assets/hero-dark.svg and assets/hero-light.svg.

Run from the repo root:  python3 scripts/build_hero.py
Edit the copy or palette here, never the generated SVGs.
"""
from pathlib import Path

W, H = 960, 348
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans','Hiragino Sans','PingFang SC',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

PALETTES = {
    "dark": dict(bg="#0d1117", card="#161b22", border="#30363d", text="#e6edf3",
                 muted="#8b949e", accent="#38bdf8", know="#34d399", knowbg="#0f2a22"),
    "light": dict(bg="#ffffff", card="#f6f8fa", border="#d0d7de", text="#1f2328",
                  muted="#59636e", accent="#0284c7", know="#059669", knowbg="#ecfdf5"),
}

# (stage label, project name, one-line role) in data-flow order
STAGES = [
    ("01 · AUDIT", "MedAudit", "diff every data drop"),
    ("02 · PREP", "DataForge", "convert · clean · mask"),
    ("03 · MAP", "Mapping System", "Excel config → SDTM"),
    ("04 · SPEC", "Spec Forge", "spec workbooks"),
]

PIPE_Y, NODE_H = 148, 76
SRC_X, SRC_W = 32, 96
SINK_W = 112
SINK_X = W - 32 - SINK_W
GAP = 28
NODE_W = (SINK_X - (SRC_X + SRC_W) - GAP * (len(STAGES) + 1)) // len(STAGES)
KNOW_Y = 270


def node_x(i):
    return SRC_X + SRC_W + GAP + i * (NODE_W + GAP)


def build(p):
    cy = PIPE_Y + NODE_H // 2
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="Bojiang Zhang, Clinical Data Engineer, Oncology">',
        "<style>",
        f".sans{{font-family:{SANS}}} .mono{{font-family:{MONO}}}",
        ".flow{stroke-dasharray:4 6;animation:flow 1.2s linear infinite}",
        "@keyframes flow{to{stroke-dashoffset:-20}}",
        ".pulse{animation:pulse 2.4s ease-in-out infinite}",
        "@keyframes pulse{0%,100%{opacity:.35}50%{opacity:1}}",
        "@media (prefers-reduced-motion:reduce){.flow,.pulse{animation:none}}",
        "</style>",
        f'<defs><marker id="arr" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0 0L8 4L0 8z" fill="{p["accent"]}"/></marker></defs>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="{p["bg"]}" stroke="{p["border"]}"/>',
        # header
        f'<text x="32" y="58" class="sans" font-size="30" font-weight="700" fill="{p["text"]}">Bojiang Zhang</text>',
        f'<text x="32" y="86" class="sans" font-size="16" font-weight="600" fill="{p["accent"]}">Clinical Data Engineer · Oncology</text>',
        f'<text x="32" y="110" class="sans" font-size="13" fill="{p["muted"]}">Yokohama / Tokyo  ·  中文 · 日本語 · English</text>',
    ]
    # header stats, right-aligned
    for i, (num, label) in enumerate([("10,000+", "patients' data managed"), ("7", "oncology studies delivered")]):
        x = W - 32 - i * 196
        out.append(f'<text x="{x}" y="66" text-anchor="end" class="sans" font-size="26" font-weight="700" fill="{p["text"]}">{num}</text>')
        out.append(f'<text x="{x}" y="88" text-anchor="end" class="sans" font-size="12" fill="{p["muted"]}">{label}</text>')

    def pill(x, w, title, sub):
        out.append(f'<rect x="{x}" y="{PIPE_Y + 14}" width="{w}" height="{NODE_H - 28}" rx="24" fill="none" stroke="{p["muted"]}" stroke-dasharray="3 3"/>')
        out.append(f'<text x="{x + w // 2}" y="{cy - 2}" text-anchor="middle" class="mono" font-size="12" font-weight="700" fill="{p["text"]}">{title}</text>')
        out.append(f'<text x="{x + w // 2}" y="{cy + 14}" text-anchor="middle" class="sans" font-size="11" fill="{p["muted"]}">{sub}</text>')

    pill(SRC_X, SRC_W, "RAW EDC", "study exports")
    pill(SINK_X, SINK_W, "SDTM + M5", "submission-ready")

    # connectors: source → nodes → sink
    xs = [SRC_X + SRC_W] + [node_x(i) + NODE_W for i in range(len(STAGES))]
    xe = [node_x(i) for i in range(len(STAGES))] + [SINK_X]
    for a, b in zip(xs, xe):
        out.append(f'<line x1="{a + 3}" y1="{cy}" x2="{b - 4}" y2="{cy}" stroke="{p["accent"]}" stroke-width="2" class="flow" marker-end="url(#arr)"/>')

    for i, (stage, name, role) in enumerate(STAGES):
        x = node_x(i)
        mx = x + NODE_W // 2
        out.append(f'<rect x="{x}" y="{PIPE_Y}" width="{NODE_W}" height="{NODE_H}" rx="10" fill="{p["card"]}" stroke="{p["border"]}"/>')
        out.append(f'<rect x="{x}" y="{PIPE_Y}" width="{NODE_W}" height="3" rx="1.5" fill="{p["accent"]}"/>')
        out.append(f'<text x="{x + 14}" y="{PIPE_Y + 24}" class="mono" font-size="10.5" font-weight="700" letter-spacing=".5" fill="{p["accent"]}">{stage}</text>')
        out.append(f'<text x="{x + 14}" y="{PIPE_Y + 46}" class="sans" font-size="15" font-weight="700" fill="{p["text"]}">{name}</text>')
        out.append(f'<text x="{x + 14}" y="{PIPE_Y + 64}" class="sans" font-size="11" fill="{p["muted"]}">{role}</text>')
        # dotted tie down to the knowledge layer
        out.append(f'<line x1="{mx}" y1="{PIPE_Y + NODE_H}" x2="{mx}" y2="{KNOW_Y}" stroke="{p["know"]}" stroke-width="1.5" stroke-dasharray="2 4" class="pulse"/>')

    kx, kw = node_x(0), node_x(len(STAGES) - 1) + NODE_W - node_x(0)
    out += [
        f'<rect x="{kx}" y="{KNOW_Y}" width="{kw}" height="46" rx="10" fill="{p["knowbg"]}" stroke="{p["know"]}" stroke-opacity=".6"/>',
        f'<text x="{kx + 16}" y="{KNOW_Y + 28}" class="mono" font-size="10.5" font-weight="700" letter-spacing=".5" fill="{p["know"]}">KNOWLEDGE LAYER</text>',
        f'<text x="{kx + 140}" y="{KNOW_Y + 28}" class="sans" font-size="13" fill="{p["text"]}">'
        f'<tspan font-weight="700">SDTM Pedia</tspan>'
        f'<tspan fill="{p["muted"]}">  ·  SDTMIG v3.4 · 63 domains · 37,939 CDISC terms · LLM-ready</tspan></text>',
        "</svg>",
    ]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    for name, palette in PALETTES.items():
        (root / "assets" / f"hero-{name}.svg").write_text(build(palette), encoding="utf-8")
    print("wrote assets/hero-dark.svg, assets/hero-light.svg")
