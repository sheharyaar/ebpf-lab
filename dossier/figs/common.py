# Shared SVG helpers for the dossier figures (spec §5.3: 680 wide, palette tokens, one marker per figure).
# Generates the three chapter-1 figures as SVG (spec §5.3 tokens, 680 wide).
# Writes .alvar/visuals/*.svg and /tmp/ch1/figs.json (svg strings for the HTML build).
import json, os, re, sys

C = dict(teal=('#E1F5EE', '#0F6E56', '#085041'), purple=('#EEEDFE', '#534AB7', '#3C3489'),
         coral=('#FAECE7', '#993C1D', '#712B13'), amber=('#FAEEDA', '#854F0B', '#633806'),
         green=('#EAF3DE', '#3B6D11', '#27500A'), gray=('#F1EFE8', '#5F5E5A', '#444441'))
SERIF = "Literata, 'Source Serif 4', Charter, Georgia, serif"
MONO = "'JetBrains Mono', 'IBM Plex Mono', monospace"
LINE = '#5F5E5A'

def esc(t): return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def svg(vb_h, title, label, body, mid):
    return (f'<svg viewBox="0 0 680 {vb_h}" width="100%" role="img" aria-label="{esc(label)}" '
            f'font-family="{SERIF}" xmlns="http://www.w3.org/2000/svg"><title>{esc(title)}</title>'
            f'<defs><marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>'
            + ''.join(body) + '</svg>')

def box(x, y, w, h, col, t1=None, t2=None, mono1=False, size1=13, step=None, sw=0.9):
    l, d, xx = C[col]
    st = f' data-step="{step}"' if step else ''
    out = f'<g{st}><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{l}" stroke="{d}" stroke-width="{sw}"/>'
    cx = x + w / 2
    if t1 and t2:
        f1 = f' font-family="{MONO}"' if mono1 else ''
        out += (f'<text x="{cx}" y="{y + h/2 - 8}" text-anchor="middle" dominant-baseline="central" font-size="{size1}" '
                f'font-weight="600" fill="{xx}"{f1}>{esc(t1)}</text>'
                f'<text x="{cx}" y="{y + h/2 + 9}" text-anchor="middle" dominant-baseline="central" font-size="11" fill="{d}">{esc(t2)}</text>')
    elif t1:
        f1 = f' font-family="{MONO}"' if mono1 else ''
        out += (f'<text x="{cx}" y="{y + h/2}" text-anchor="middle" dominant-baseline="central" font-size="{size1}" '
                f'font-weight="600" fill="{xx}"{f1}>{esc(t1)}</text>')
    return out + '</g>'

def text(x, y, t, size=11, col=None, anchor='middle', mono=False, weight=None, step=None, italic=False):
    fill = C[col][1] if col else '#444B52'
    st = f' data-step="{step}"' if step else ''
    f = f' font-family="{MONO}"' if mono else ''
    w = f' font-weight="{weight}"' if weight else ''
    it = ' font-style="italic"' if italic else ''
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-size="{size}" '
            f'fill="{fill}"{f}{w}{it}{st}>{esc(t)}</text>')

def arrow(x1, y1, x2, y2, mid, width=1.3, color=LINE, step=None, dash=None):
    st = f' data-step="{step}"' if step else ''
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{da} '
            f'marker-end="url(#{mid})"{st}/>')

def bar(y, h, text_):  # summary bar across the bottom
    return (f'<rect x="40" y="{y}" width="600" height="{h}" rx="6" fill="{C["gray"][0]}" stroke="{C["gray"][1]}" stroke-width="0.75"/>'
            + text(340, y + h / 2, text_, size=12, col='gray'))


def tx(x, y, t, size=11, col=None, anchor='middle', mono=False, weight=None, step=None, italic=False):
    return text(x, y, t, size=size, col=col, anchor=anchor, mono=mono, weight=weight, step=step, italic=italic)

def frames(svgsrc, mid, ks, crop=None):
    """Print twins for a step widget: copies of the source SVG with hidden parts deleted."""
    out = []
    for k in ks:
        def keep(spec):
            if spec.endswith('+'): return k >= int(spec[:-1])
            return k in [int(x) for x in spec.split(',')]
        s = re.sub(r'<(g|text|line|path)([^>]*?) data-step="([^"]+)"([^>]*?)(/>|>.*?</\1>)',
                   lambda mm: ('<' + mm.group(1) + mm.group(2) + mm.group(4) + mm.group(5)) if keep(mm.group(3)) else '', svgsrc, flags=re.S)
        s = s.replace(mid, f'{mid}-f{k}')
        if crop and k in crop: s = re.sub(r'viewBox="0 0 680 \d+"', f'viewBox="0 0 680 {crop[k]}"', s, count=1)
        out.append(s)
    return out

def save(name, svgtext):
    import os
    os.makedirs(os.path.join(os.path.dirname(__file__), 'out'), exist_ok=True)
    open(os.path.join(os.path.dirname(__file__), 'out', name + '.svg'), 'w', encoding='utf-8').write(svgtext)
