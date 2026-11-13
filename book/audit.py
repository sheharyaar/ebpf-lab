# audit.py — run from the folder holding the dossier and NOTES.md:  python3 -I audit.py dossier.html
import re, html, sys
from html.parser import HTMLParser
F = sys.argv[1] if len(sys.argv) > 1 else 'dossier.html'
s = open(F, encoding='utf-8').read()
body = s[s.index('<main>'):s.index('</main>')]
BOX = r'(check|lab|readwith|words|recap|field|costs|refs)'
def text(t):
    t = re.sub(r'<(script|style|template)[^>]*>.*?</\1>', ' ', t, flags=re.S)
    t = re.sub(r'<a class="xref[^>]*>(.*?)</a>', r'\1', t)      # a cross-reference is part of the word it stands for
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
chaps = [(cid, (re.search(r'data-shape="(\w+)"', at) or re.match('', '')).group(1) if 'data-shape' in at else '', t)
         for cid, at, t in re.findall(r'<section id="([\w-]+)" class="chapter"([^>]*)>(.*?)(?=<section[ >]|\Z)', body, re.S)]   # stop at any section, including part title pages
partof = {}                        # chapter id -> the part it sits in ('Part I' ...), from the part title pages before it
cur = None
for m in re.finditer(r'<section class="part"[^>]*><p class="eyebrow">([^<]*)</p>|<section id="([\w-]+)" class="chapter"', body):
    if m.group(1): cur = m.group(1)
    else: partof[m.group(2)] = cur
shapes = []
# an old chapter file that a merge has partly absorbed, kept until the next merge takes the rest, carries data-remnant on its
# <section>: it is exempt from the size, figure, sentence-spread and shape-rhythm rules, which judge whole chapters
REMNANT = set(re.findall(r'<section id="([\w-]+)" class="chapter"[^>]*\sdata-remnant', body))
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
    if cid not in REMNANT: shapes.append(shape)
    if words > 4500: flag(f'{cid}: prose over 4,500 words ({words})')   # Plan v4: merged chapters of 15-25 pages
    if cid not in REMNANT and (figs < 2 or figs < words / 450): flag(f'{cid}: too few figures ({figs} for {words} words; want one per 450)')
    sl = [len(x.split()) for x in sents]; sd = (sum((n - avg) ** 2 for n in sl) / max(1, len(sl))) ** 0.5
    if not 16 <= avg <= 28: flag(f'{cid}: average sentence {avg:.1f} words (want 20-24)')
    if sd < 8 and cid not in REMNANT: flag(f'{cid}: sentence lengths too even (sd {sd:.1f}, want 9 or more)')
    yous = len(re.findall(r"\byou(?:r|rs)?\b", p.lower())) * 1000 / max(1, words)
    if yous > 8: flag(f'{cid}: "you/your" {yous:.0f} per 1,000 words of prose (want under 4)')
    caps = text(' '.join(re.findall(r'<figcaption>(.*?)</figcaption>', t, re.S))).lower()
    for tic in [r'\bnotice\b', r'\bthe [\w-]+ figure \(figure', r'\band nothing else\b', r'\bcarries on\b']:
        if re.search(tic, p.lower() + ' ' + caps): flag(f'{cid}: voice tic {tic!r}')
    numbered = re.search(r'<p class="eyebrow">Chapter \d+</p>', t)
    if numbered and partof.get(cid) in ('Part I', 'Part II') and 'class="costs"' not in t: flag(f'{cid}: no "What it costs" box (Parts I and II)')
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
qids = re.findall(r'<li id="(q(?:\d+|P)-\d+)"', body); labids = re.findall(r'<div class="lab" id="(lab[\w-]+)"', body)
ans = re.findall(r'<div class="ans" data-for="([\w-]+)">(.*?)</div>', body, re.S); sols = re.findall(r'<div class="sol" data-for="([\w-]+)">', body)
amap = dict(ans)
for q in qids:
    if q not in amap: flag(f'question {q} has no answer in the key')
    else:
        n = len(text(amap[q]).split())
        if n < 40 or n > 150: flag(f'answer for {q} is {n} words (want 40-150)')
        if re.search(r'\bnear-miss\b', text(amap[q]).lower()): flag(f'answer for {q} uses the fixed "near-miss" frame')
for a in amap:
    if a not in qids: flag(f'key entry {a} has no question')
for l in labids:
    if l not in sols: flag(f'lab {l} has no solution in the key')
# the key lists each chapter's answers in the order of their printed numbers (a merge can keep the old files' order)
qnum = dict(re.findall(r'<li id="(q[\w-]+)" data-n="([^"]+)"', body))
def _n(q):
    c, _, k = qnum.get(q, '0.0').rpartition('.'); return c, int(k) if k.isdigit() else 0
for c in dict.fromkeys(_n(a)[0] for a, _ in ans if a in qnum):
    seq = [a for a, _ in ans if a in qnum and _n(a)[0] == c]
    if seq != sorted(seq, key=lambda a: _n(a)[1]):
        flag(f'answer key for chapter {c} out of order: ' + ' '.join(qnum[a] for a in seq))
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
        m = re.match(r'\|\s*`?([^`|]+?)`?\s*\|\s*([a-z][\w-]*)\s*\|', line)   # any chapter id: ch4, primer, object
        if m and m.group(1).strip() != 'term': TERMS[m.group(1).strip()] = m.group(2)
except Exception as e: print('no term map read from NOTES.md:', e)
SKIP = {'how-to-read', 'contents', 'answers', 'glossary', 'references', 'whats-new', 'whats-quiz'}
ids = [(m.start(), m.group(1)) for m in re.finditer(r'<section id="([\w-]+)"', body)]
order = [i for _, i in ids]
def chapter_of(pos):
    c = 'pre'
    for p_, n in ids:
        if p_ <= pos: c = n
    return c
vbody = re.sub(r'<ol class="ribbon".*?</ol>|<div class="refs">.*?</div>|<figure class="fig lineage".*?</figure>|<section class="part"[^>]*>.*?</section>', lambda m: ' ' * len(m.group(0)), body, flags=re.S)  # timelines and cited titles may name later terms
vbody = re.sub(r'<[^>]+>', lambda m: ' ' * len(m.group(0)), vbody)   # text only: not ids, hrefs or aria-label attributes
ALIAS = {}                                           # old chapter id -> the merged chapter that declares it
for cid, at in re.findall(r'<section id="([\w-]+)" class="chapter"([^>]*)>', body):
    for a in (re.findall(r'data-aliases="([^"]*)"', at) or [''])[0].split(): ALIAS[a] = cid
for t, e in list(TERMS.items()):                     # the table may name a chapter by an id a merged chapter now aliases
    TERMS[t] = ALIAS.get(e, e)
    if TERMS[t] not in order: flag(f'Terms table: {t!r} is defined in {e}, which is no chapter of the book')
for t, expect in TERMS.items():
    for m in re.finditer(r'(?<![\w-])' + re.escape(t) + r'(?![\w-])', vbody, re.I):
        c = chapter_of(m.start())
        if c in SKIP: continue
        if c in order and expect in order and order.index(c) < order.index(expect):
            flag(f'EARLY USE: {t!r} in {c}, defined in {expect} | ' + body[max(0, m.start()-60):m.start()+30].replace('\n', ' ')); break
print('terms checked', len(TERMS))

# --- 8. numbers and cross-references (numbering.py) ---------------------------
# Every chapter, figure, question and lab number is computed at build time; a reference is <a class="xref" href="#id">.
# Flag a reference whose target is missing, and a number typed into prose. Exempt: code, quotations, ribbons, field
# notes, links (reference titles and the filled xrefs themselves), the numbers the build writes (eyebrows, captions,
# key labels and headings), ranges ("chapters 1 to 9"), chapters not yet written (beyond the last chapter), and the
# phrases in TYPED_OK, which cite another book's chapters.
TYPED_OK = ['Chapters 2, 3 and 5, on TIP', 'chapters 7 to 11']
allids = set(re.findall(r'\sid="([\w-]+)"', s))
xrefs = re.findall(r'<a class="xref([^"]*)" href="#([\w-]+)">(.*?)</a>', body, re.S)
for mods, tid, lab in xrefs:
    if tid not in allids or lab.startswith('??') or not lab.strip(): flag(f'xref to #{tid}{mods}: target missing ({lab!r})')
# a chapter-level reference inside the chapter it names ("chapter 10" in chapter 10): after a merge it must become a
# section reference or plain wording. "the answer key under <chapter>" is a pointer into the key and may name its own chapter.
chapids = {cid for cid, _, _ in chaps}
for m in re.finditer(r'<a class="xref([^"]*)" href="#([\w-]+)">(.*?)</a>', body):
    if m.group(2) in chapids and chapter_of(m.start()) == m.group(2) and not re.search(r'key under\s*$', body[max(0, m.start() - 40):m.start()]):
        flag(f'xref to its own chapter #{m.group(2)} ({m.group(3)!r}): use a section reference or plain wording | '
             + re.sub(r'\s+', ' ', text(re.sub(r'^[^<]*>|<[^>]*$', '', body[max(0, m.start() - 160):m.end() + 60]))).strip()[-140:])
last = max([int(n) for n in re.findall(r'<p class="eyebrow">Chapter (\d+)</p>', body)] or [0])
blank = lambda m: ' ' * len(m.group(0))
pbody = re.sub(r'<(code|pre|cite|blockquote|template|svg|script|a)\b[^>]*>.*?</\1>|<ol class="ribbon".*?</ol>|<div class="field">.*?</div>'
               r'|<b class="fn">.*?</b>|<p class="(?:eyebrow|q)">.*?</p>|<h3>.*?</h3>|<section id="contents".*?</section>'
               r'|<section class="part".*?</section>|<!--.*?-->', blank, body, flags=re.S)
pbody = re.sub(r'<[^>]+>', blank, pbody)
TYPED = re.compile(r'(?<![\w/-])(?:Figures? (?:\d+|P)\.\d+|[Cc]hapters? \d+(?:(?:,|,? and|,? or) \d+)*(?: to \d+)?|[Qq]uestions? (?:\d+|P)\.\d+|Labs? (?:\d+|P)\.\d+)')
typed_left = []
for m in TYPED.finditer(pbody):
    t = m.group(0); around = re.sub(r'\s+', ' ', html.unescape(pbody[max(0, m.start() - 50):m.end() + 50]))
    if t.lower().startswith('chapter') and (' to ' in t or all(int(n) > last for n in re.findall(r'\d+', t))
                                             or any(ok in around for ok in TYPED_OK)):
        typed_left.append(t); continue
    flag(f'typed number {t!r} in prose (use <a class="xref" href="#id">) | {around.strip()}')
print('xrefs', len(xrefs), 'typed ranges, other books and chapters not yet written left as text', len(typed_left))
print('\nRESULT:', 'clean' if not bad else f'{len(bad)} problem(s)')