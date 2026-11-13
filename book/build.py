#!/usr/bin/env python3
"""Assemble the eBPF book from src/ and figs/out/.

  src/front.html      title page and how-to-read
  src/chNN.html       one chapter, in four parts separated by markers:
                        <!--CHAPTER--> the <section class="chapter">
                        <!--ANSWERS--> .ans and .sol blocks for the key
                        <!--GLOSSARY--> <dt>/<dd> pairs
                        <!--REFS-->    <li> items whose first <span class="tag X"> names the layer
  figs/out/NAME.svg   inserted where a chapter says {{fig:NAME}}; {{twins:NAME}} inserts NAME-twin1.svg, -twin2 ...
Chapter, figure, question and lab numbers and every cross-reference are filled in by numbering.py (shared with the
print edition, tex/html2tex.py); the chapter order and the parts are set there too.

Run from this folder:  python3 -I build.py   ->  ebpf-book.html
One chapter alone:     python3 -I build.py /tmp/x.html ch02 [ch03 ...]  (front matter and the named chapters only)
"""
import functools, glob, html, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numbering

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else 'ebpf-book.html')
TAG_ORDER = ['LINEAGE', 'ISA', 'LOADER', 'VERIFIER', 'RUNTIME', 'HW']

def read(p): return open(os.path.join(HERE, p), encoding='utf-8').read()

def fig(m):
    return read(f'figs/out/{m.group(1)}.svg')

def twins(m):
    files = sorted(glob.glob(os.path.join(HERE, 'figs', 'out', f'{m.group(1)}-twin*.svg')))
    if not files: raise SystemExit(f'no twins for {m.group(1)}')
    return ''.join(open(f, encoding='utf-8').read() for f in files)

@functools.lru_cache(maxsize=None)
def qr(url):
    """A QR code for a printed reader: qrencode SVG, 2-module quiet zone, medium error correction."""
    level = 'M' if len(url) <= 60 else 'L'          # long URLs: fewer modules, still fine on clean print
    svg = subprocess.run(['qrencode', '-t', 'SVG', '-m', '2', '-l', level, '--svg-path', '-o', '-', url],
                         capture_output=True, text=True, check=True).stdout
    svg = svg[svg.index('<svg'):]
    n = int(re.search(r'viewBox="0 0 (\d+) ', svg).group(1))  # modules including the quiet zone
    size = min(26, max(14, round(n * 0.42, 1)))      # at least 0.42 mm per module, 14-26 mm square
    svg = re.sub(r'<svg width="[^"]*" height="[^"]*"',
                 f'<svg class="qr" role="img" aria-label="QR code for {html.escape(url)}" shape-rendering="crispEdges"', svg, count=1)
    return size, re.sub(r'\s+', ' ', svg.replace(' id="QRcode"', ''))

def add_qr(block):
    """Put a QR code in front of every list item in a reference list that links to the web."""
    def li(m):
        href = re.search(r'href="(https?://[^"]+)"', m.group(0))
        if not href: return m.group(0)
        size, svg = qr(html.unescape(href.group(1)))
        return m.group(0).replace('<li>', f'<li class="hasqr" style="--qr:{size}mm"><span class="qrbox">{svg}</span>', 1)
    return re.sub(r'<li>.*?</li>', li, block, flags=re.S)

def text(t):
    t = re.sub(r'<(script|style|svg|template)[^>]*>.*?</\1>', ' ', t, flags=re.S)
    t = re.sub(r'<a class="xref[^>]*>(.*?)</a>', r'\1', t)      # a cross-reference is part of the word it stands for
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t))).strip()

def prose_words(t):
    for pat in [r'<figure.*?</figure>', r'<pre.*?</pre>', r'<table.*?</table>', r'<ol class="ribbon".*?</ol>', r'<header.*?</header>',
                r'<aside class="mn".*?</aside>', r'<div class="(check|lab|readwith|words|recap|field|costs|refs)".*?</div>', r'<template.*?</template>']:
        t = re.sub(pat, ' ', t, flags=re.S)
    return len(text(t).split())

ONLY = set(sys.argv[2:])
N = numbering.get(os.path.join(HERE, 'src'))
chapters = []
for pos, nc in enumerate(N.chapters):
    stem = nc['file']
    if ONLY and stem[:4] not in ONLY and stem not in ONLY: continue
    raw = N.fill_chapter(read(f'src/{stem}.html'), 'screen', stem)
    parts = dict(re.findall(r'<!--(CHAPTER|ANSWERS|GLOSSARY|REFS)-->(.*?)(?=<!--(?:CHAPTER|ANSWERS|GLOSSARY|REFS)-->|\Z)', raw, re.S))
    sec = parts['CHAPTER']
    # a side note floats beside the paragraph it follows in the source: move it above that block
    sec = re.sub(r'(<p(?:\s[^>]*)?>(?:(?!</p>).)*</p>|<div class="field">.*?</div>)\s*(<aside class="mn">.*?</aside>)',
                 lambda m: m.group(2) + '\n' + m.group(1), sec, flags=re.S)
    sec = re.sub(r'\{\{fig:([\w-]+)\}\}', fig, sec)
    sec = re.sub(r'\{\{twins:([\w-]+)\}\}', twins, sec)
    cid = nc['id']
    title = text(re.search(r'<h2>(.*?)</h2>', sec, re.S).group(1))
    words = prose_words(sec)
    sec = re.sub(r'<div class="refs">.*?</div>', lambda m: add_qr(m.group(0)), sec, flags=re.S)
    figs = sec.count('<figure class="fig')
    minutes = round(words / 200 + figs)
    sec = sec.replace('{{min}}', str(minutes))
    chapters.append(dict(id=cid, pos=pos, kind=nc['kind'], num=nc['num'], name=nc['name'], title=title, sec=sec, words=words, figs=figs, minutes=minutes,
                         answers=parts.get('ANSWERS', '').strip(), glossary=parts.get('GLOSSARY', '').strip(),
                         refs=parts.get('REFS', '').strip()))
PARTS = N.part_openers()      # chapter id that opens a part -> (label, title, introduction)
PARTPOS = {N.by_id[k]['file']: k for k in PARTS}
def part_before(c):
    # the part this chapter is in: the last part that opens at or before it (an excerpt opens it at its first chapter)
    starts = [(numbering.ORDER.index(f), k) for f, k in PARTPOS.items() if numbering.ORDER.index(f) <= c['pos']]
    return max(starts)[1] if starts else None
label = lambda c: c['name']

tot_words = sum(c['words'] for c in chapters); tot_figs = sum(c['figs'] for c in chapters)
tot_min = sum(c['minutes'] for c in chapters)

front = N.fill_xrefs(read('src/front.html'), 'screen', 'front')
front = (front.replace('{{chapters}}', str(len(chapters))).replace('{{words}}', f'{round(tot_words, -2):,}')
              .replace('{{minutes}}', str(tot_min)).replace('{{figures}}', str(tot_figs)))
contents = ['<section id="contents" class="front"><h2>Contents</h2><ol>',
            '<li><span class="n">—</span><a href="#how-to-read">How to read this</a><span class="rt"></span></li>']
opened = set()
for c in chapters:
    pk = part_before(c)
    if pk is not None and pk not in opened and c['kind'] != 'epilogue':
        opened.add(pk); c['part'] = pk
        contents.append(f'<li class="group">{PARTS[pk][0]} \u00b7 {PARTS[pk][1]}</li>')
    n = c['num']
    contents.append(f'<li><span class="n">{n}</span><a href="#{c["id"]}">{html.escape(c["title"])}</a><span class="rt">{c["minutes"]} min</span></li>')
contents.append('<li class="group">Back matter</li>')
for sid, name in [('commits', 'The lineage in commits'), ('answers', 'Answer key'), ('glossary', 'Glossary'), ('references', 'References')]:
    contents.append(f'<li><span class="n">—</span><a href="#{sid}">{name}</a><span class="rt"></span></li>')
contents.append('</ol></section>')

def commits_appendix():
    """The lineage in commits: src/commits.json, one entry per row of Figure 0.3 (plus starred extras), two QR codes each."""
    rows = __import__('json').load(open(os.path.join(HERE, 'src', 'commits.json'), encoding='utf-8'))
    intro = N.fill_xrefs(read('src/commits-intro.html'), 'screen', 'commits-intro')
    out = ['<section id="commits" class="backmatter"><p class="eyebrow">Appendix</p><h2>The lineage in commits</h2>', intro]
    months = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
    for e in rows:
        codes = [(e['code'], e.get('codelabel', 'commit'))] + ([(e['thread'], 'thread')] if e.get('thread') else [])
        qrs = ''.join(f'<span class="cq" style="--qr:{s}mm">{svg}<span class="cl">{lab}</span></span>'
                      for (s, svg), lab in ((qr(u), lab) for u, lab in codes))
        if e.get('sha'):
            y, m, d = e['date'].split('-')
            meta = (f'<p class="cms"><code>{e["sha"][:12]}</code> {html.escape(e["subject"])}</p>'
                    f'<p class="cmm">{html.escape(e["author"])}, {int(d)} {months[int(m) - 1]} {y} · '
                    f'+{e["added"]:,} −{e["removed"]:,} lines in {e["files"]} file{"s" if e["files"] != 1 else ""}</p>')
        else:
            meta = ''
        star = '*' if e.get('extra') else ''
        chs = ', '.join(f'<a href="#{cid}">{n}</a>' if cid else html.escape(n) for cid, n in N.commit_chapters(e['chapters']))
        out.append(f'<div class="cm"><div class="cmt"><p class="cmh"><span class="yr">{e["year"]}</span><span class="ver">{e["version"]}</span>'
                   f'{star}{html.escape(e["what"])}<span class="chs">ch. {chs}</span></p>{meta}'
                   f'<p class="cmn">{N.fill_xrefs(e["note"], "screen", "commits.json")}</p></div><div class="cmq">{qrs}</div></div>')
    out.append('</section>')
    return '\n'.join(out)

key = ['<section id="answers" class="backmatter"><h2>Answer key</h2>']
for c in chapters:
    if c['answers']: key += [f'<h3>{label(c)}</h3>', c['answers']]
key.append('</section>')
gloss = ['<section id="glossary" class="backmatter"><h2>Glossary</h2>']
for c in chapters:
    if c['glossary']: gloss += [f'<h3>{label(c)}</h3><dl>', c['glossary'], '</dl>']
gloss.append('</section>')
seen, bytag = set(), {}
for c in chapters:
    for li in re.findall(r'<li>.*?</li>', c['refs'], re.S):
        href = re.search(r'href="([^"]+)"', li)
        k = href.group(1) if href else text(li)
        if k in seen: continue
        seen.add(k)
        tag = re.search(r'<span class="tag (\w+)">', li).group(1)
        bytag.setdefault(tag, []).append(add_qr(li))
refs = ['<section id="references" class="backmatter"><h2>References</h2><div class="refs">']
for tag in TAG_ORDER:
    if tag in bytag: refs += [f'<h4>{tag.title() if tag not in ("ISA", "HW") else tag}</h4><ul>'] + bytag[tag] + ['</ul>']
refs.append('</div></section>')

body = '\n'.join([front.split('<!--HOWTO-->')[0], '<main>', '\n'.join(contents), front.split('<!--HOWTO-->')[1]]
                 + [(f'<section class="part" id="part-{c["part"]}"><p class="eyebrow">{PARTS[c["part"]][0]}</p><h2>{PARTS[c["part"]][1]}</h2><p class="lede">{PARTS[c["part"]][2]}</p></section>' if c.get('part') else '') + c['sec'] for c in chapters] + [commits_appendix(), '\n'.join(key), '\n'.join(gloss), '\n'.join(refs), '</main>'])
mermaid = '' if 'class="mermaid"' not in body else """
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({startOnLoad:false, deterministicIds:true, theme:'neutral',
  themeVariables:{fontFamily:'JetBrains Mono, IBM Plex Mono, monospace', fontSize:'13px'}, securityLevel:'loose'});
try { await mermaid.run({querySelector:'.mermaid'}); } catch (e) { console.error(e); }"""
desk = """const desk = document.createElement('style');
desk.textContent = `@media screen{
  body{background:#D9D5CB}
  .pagedjs_pages{display:flex;flex-direction:column;align-items:center;gap:7mm;padding:10mm 0}
  .pagedjs_page{background:#FBF8F2;border:1px solid #BDB7AA}
}
@media screen and (min-width:1700px){
  .pagedjs_pages{flex-direction:row;flex-wrap:wrap;justify-content:flex-start;width:calc(420mm + 7mm + 4px);margin:0 auto}
  .pagedjs_page:first-child{margin-left:calc(210mm + 7mm + 2px)}
}`;
document.head.appendChild(desk);"""
page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>eBPF for Systems Engineers</title><meta name="author" content="Mohammad Shehar Yaar Tausif">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,500;0,7..72,600;1,7..72,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{read('book.css')}
/* questions print their computed number (numbering.py: data-n="4.1"), so the page and the answer key agree */
ol:has(> li[data-n]){{padding-left:8mm}}
ol > li[data-n]{{list-style:none;position:relative}}
ol > li[data-n]::before{{content:attr(data-n);position:absolute;right:calc(100% + 1.8mm);font-variant-numeric:lining-nums tabular-nums}}
</style>
<script>window.PagedConfig = {{auto: false}};</script>
<script src="https://cdn.jsdelivr.net/npm/pagedjs@0.4.3/dist/paged.polyfill.min.js"></script>
</head>
<body>
<div class="book">
{body}
</div>
<script type="module">
document.querySelectorAll('details.hint').forEach(d => d.open = true);
await Promise.all(['13px "JetBrains Mono"', '500 13px "JetBrains Mono"', '10pt Literata', 'italic 10pt Literata'].map(f => document.fonts.load(f)));
await document.fonts.ready;{mermaid}
await window.PagedPolyfill.preview();
{desk}
document.documentElement.dataset.paged = 'done';
</script>
</body>
</html>
"""
open(OUT, 'w', encoding='utf-8').write(page)
for c in chapters:
    print(f"{c['id']:5} {c['words']:4} words {c['figs']} figs {c['minutes']:2} min  {c['title'][:60]}")
print(f'total {tot_words} words, {tot_figs} figures, {tot_min} min -> {os.path.basename(OUT)}')
