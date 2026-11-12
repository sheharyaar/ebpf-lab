# audit.py — run from the folder holding the dossier and NOTES.md:  python3 -I audit.py dossier.html
import re, html, sys
from html.parser import HTMLParser
F = sys.argv[1] if len(sys.argv) > 1 else 'dossier.html'
s = open(F, encoding='utf-8').read()
body = s[s.index('<main>'):s.index('</main>')]
BOX = r'(check|lab|readwith|words|recap|field)'
def text(t):
    t = re.sub(r'<(script|style|template)[^>]*>.*?</\1>', ' ', t, flags=re.S)
    return html.unescape(re.sub(r'<[^>]+>', ' ', t))
def prose(t):                      # chapter body minus everything that is not prose
    for pat in [r'<figure.*?</figure>', r'<pre.*?</pre>', r'<table.*?</table>', r'<ol class="ribbon".*?</ol>',
                r'<header.*?</header>', r'<aside class="mn".*?</aside>', r'<div class="%s".*?</div>' % BOX, r'<template.*?</template>']:
        t = re.sub(pat, ' ', t, flags=re.S)
    return text(t)
bad = []
def flag(m): bad.append(m); print('!!', m)

# --- 1. structure ----------------------------------------------------------
print('figures', s.count('<figure class="fig'), 'captions', s.count('<figcaption>'),
      'mermaid', s.count('<div class="mermaid">'), 'widgets', s.count('class="fig widget"'))
if '<!--APPEND-->' in s: flag('leftover APPEND marker')
BOOK = 'pagedjs' in s   # book edition: paged by Paged.js, no web-only furniture
for need in ['id="contents"', 'id="how-to-read"', 'id="answers"', 'id="glossary"', 'id="references"', 'class="titlepage"'] + ([] if BOOK else ['id="answerctl"', 'beforeprint', 'zoomlayer']):
    if need not in s: flag('missing ' + need)
if 'details class="peek"' in s or "class='peek'" in body: flag('details.peek in source: answers must be cloned by script, not written inline')
if '@page' not in s or ('@media print' not in s and not BOOK): flag('print stylesheet missing')
if re.search(r'font-weight:\s*(?!400|500|600|700|bold|normal)\d+', s): flag('font-weight outside 400/500/600/700')
if 'background:#0f1720' in s or 'background:#0d1117' in s: flag('dark code block; print will not like it')

# --- 2. chapters: density, anatomy, variety --------------------------------
chaps = re.findall(r'<section id="(ch\d+)" class="chapter"(?: data-shape="(\w+)")?>(.*?)(?=<section id=|\Z)', body, re.S)
shapes = []
for cid, shape, t in chaps:
    p = prose(t); words = len(p.split())
    sents = [x for x in re.split(r'(?<=[.!?])\s+', p) if x.strip()]
    avg = words / max(1, len(sents))
    figs = len(re.findall(r'<figure class="fig', t)); merm = t.count('<div class="mermaid">'); widg = t.count('class="fig widget"')
    kinds = set(k for k, pat in [('mermaid', r'<div class="mermaid">'), ('widget', r'class="fig widget"'), ('svg', r'<figure class="fig"[^>]*>\s*<svg'),
                                 ('table', r'<figure class="fig"[^>]*>\s*<table'), ('pre', r'<figure class="fig"[^>]*>\s*<pre')] if re.search(pat, t))
    blocks = set(b for b, pat in [('table', r'<table'), ('mn', r'<aside class="mn"'), ('readwith', r'class="readwith"'), ('field', r'class="field"'), ('pre', r'<pre'), ('lab', r'class="lab"')] if re.search(pat, t))
    longp = sum(1 for para in re.findall(r'<p(?:\s[^>]*)?>(.*?)</p>', t, re.S) if len(re.split(r'(?<=[.!?])\s+', text(para).strip())) > 5)
    pres = len(re.findall(r'<pre', t)); mns = len(re.findall(r'<aside class="mn"', t)); ribbon = '<ol class="ribbon"' in t and 'class="here"' in t
    rt = round(words / 200 + figs)
    print(f'{cid:5} {shape or "?":10} prose={words:4} figs={figs} ({",".join(sorted(kinds))}) mermaid={merm} widgets={widg} avg_sentence={avg:4.1f} long_paras={longp} pre={pres} mn={mns} blocks={",".join(sorted(blocks)) or "-"} -> {rt} min')
    if not shape: flag(f'{cid}: no data-shape')
    shapes.append(shape)
    if words > 900: flag(f'{cid}: prose over 900 words ({words})')
    if figs < 2 or figs < words / 300: flag(f'{cid}: too few figures ({figs} for {words} words)')
    if avg > 20: flag(f'{cid}: average sentence over 20 words')
    if longp: flag(f'{cid}: {longp} paragraph(s) over 5 sentences')
    if pres > max(1, words // 400): flag(f'{cid}: too many code blocks ({pres})')
    if mns > 4: flag(f'{cid}: more than 4 margin notes')
    if not ribbon: flag(f'{cid}: ribbon missing or no "here" item')
    for need in ['class="eyebrow"', 'class="lede"', 'class="inthis"', 'class="spine"', 'class="recap"', 'class="words"', 'class="check"', 'class="refs"']:
        if need not in t: flag(f'{cid}: missing {need}')
    if not blocks: flag(f'{cid}: no block variety (needs a table, margin note, read-with card, field note, lab or transcript)')
if len(set(shapes)) < 3: flag('fewer than 3 chapter shapes')
for i in range(len(shapes) - 2):
    if shapes[i] == shapes[i+1] == shapes[i+2]: flag(f'three {shapes[i]} chapters in a row at chapter index {i}')
for need in ['interlude', 'case']:
    if need not in shapes: flag(f'no {need} chapter')
allfigs = s.count('<figure class="fig'); allmerm = s.count('<div class="mermaid">')
if allfigs and allmerm / allfigs > 0.4: flag(f'Mermaid share {allmerm}/{allfigs} over 40%')

# --- 3. questions, labs, key ------------------------------------------------
qids = re.findall(r'<li id="(q\d+-\d+)"', body); labids = re.findall(r'<div class="lab" id="(lab[\w-]+)"', body)
ans = re.findall(r'<div class="ans" data-for="([\w-]+)">(.*?)</div>', body, re.S); sols = re.findall(r'<div class="sol" data-for="([\w-]+)">', body)
amap = dict(ans)
for q in qids:
    if q not in amap: flag(f'question {q} has no answer in the key')
    else:
        n = len(text(amap[q]).split())
        if n < 40 or n > 150: flag(f'answer for {q} is {n} words (want 40-150)')
for a in amap:
    if a not in qids: flag(f'key entry {a} has no question')
for l in labids:
    if l not in sols: flag(f'lab {l} has no solution in the key')
print('questions', len(qids), 'answers', len(ans), 'labs', len(labids), 'solutions', len(sols))

# --- 4. widgets: twin, template, registration ------------------------------
for name in re.findall(r'<figure class="fig widget" id="[\w-]+" data-widget="([\w-]+)">', body):
    fig = re.search(r'<figure class="fig widget" id="[\w-]+" data-widget="%s">(.*?)</figure>' % name, body, re.S).group(1)
    if '<div class="twin">' not in fig or '<svg' not in fig.split('<div class="twin">')[-1]: flag(f'widget {name}: no print twin with an svg')
    if f'id="src-{name}"' not in fig: flag(f'widget {name}: no <template id="src-{name}">')
    if f"WIDGETS['{name}']" not in s and not BOOK: flag(f'widget {name}: not registered in WIDGETS')

# --- 5. mermaid sanity ------------------------------------------------------
for i, m in enumerate(re.findall(r'<div class="mermaid">\n(.*?)\n</div>', s, re.S), 1):
    head = m.strip().split('\n')[0]
    if not head.startswith(('flowchart', 'sequenceDiagram', 'graph', 'stateDiagram')): flag(f'mermaid {i}: bad header {head[:30]!r}')
    for e in ['&amp;', '&lt;', '&gt;']:
        if e in m: flag(f'mermaid {i}: entity {e} in a label')

# --- 6. HTML nesting --------------------------------------------------------
VOID = {'meta', 'br', 'hr', 'img', 'link', 'input', 'source', 'wbr'}
class P(HTMLParser):
    def __init__(self): super().__init__(); self.st = []; self.err = []
    def handle_startendtag(self, t, a): pass
    def handle_starttag(self, t, a):
        if t not in VOID: self.st.append((t, self.getpos()))
    def handle_endtag(self, t):
        if t in VOID: return
        if not self.st: self.err.append(('extra close', t, self.getpos())); return
        if self.st[-1][0] != t: self.err.append(('mismatch', t, 'open:' + self.st[-1][0], self.getpos()))
        else: self.st.pop()
p = P(); p.feed(s)
if p.st or p.err: flag(f'nesting: unclosed {p.st[:3]} errors {p.err[:3]}')

# --- 7. vocabulary: no term before the chapter that defines it (reads NOTES.md "## Terms") -----
TERMS = {}
try:
    notes = open('NOTES.md', encoding='utf-8').read()
    sec = re.split(r'^## Terms\s*$', notes, maxsplit=1, flags=re.M)[1].split('\n## ', 1)[0]
    for line in sec.splitlines():
        m = re.match(r'\|\s*`?([^`|]+?)`?\s*\|\s*(ch\d+)\s*\|', line)
        if m: TERMS[m.group(1).strip()] = m.group(2)
except Exception as e: print('no term map read from NOTES.md:', e)
SKIP = {'how-to-read', 'contents', 'answers', 'glossary', 'references', 'whats-new', 'whats-quiz'}
ids = [(m.start(), m.group(1)) for m in re.finditer(r'<section id="([\w-]+)"', body)]
order = [i for _, i in ids]
def chapter_of(pos):
    c = 'pre'
    for p_, n in ids:
        if p_ <= pos: c = n
    return c
vbody = re.sub(r'<ol class="ribbon".*?</ol>|<div class="refs">.*?</div>|<figure class="fig lineage".*?</figure>', lambda m: ' ' * len(m.group(0)), body, flags=re.S)  # timelines and cited titles may name later terms
for t, expect in TERMS.items():
    for m in re.finditer(r'(?<![\w-])' + re.escape(t) + r'(?![\w-])', vbody, re.I):
        c = chapter_of(m.start())
        if c in SKIP: continue
        if c in order and expect in order and order.index(c) < order.index(expect):
            flag(f'EARLY USE: {t!r} in {c}, defined in {expect} | ' + body[max(0, m.start()-60):m.start()+30].replace('\n', ' ')); break
print('terms checked', len(TERMS))
print('\nRESULT:', 'clean' if not bad else f'{len(bad)} problem(s)')