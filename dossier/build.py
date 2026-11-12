#!/usr/bin/env python3
"""Assemble the eBPF book dossier (book edition) from src/ and figs/out/.

  src/front.html      title page and how-to-read
  src/chNN.html       one chapter, in four parts separated by markers:
                        <!--CHAPTER--> the <section class="chapter">
                        <!--ANSWERS--> .ans and .sol blocks for the key
                        <!--GLOSSARY--> <dt>/<dd> pairs
                        <!--REFS-->    <li> items whose first <span class="tag X"> names the layer
  figs/out/NAME.svg   inserted where a chapter says {{fig:NAME}}; {{twins:NAME}} inserts NAME-twin1.svg, -twin2 ...

Run from this folder:  python3 -I build.py   ->  ebpf-dossier.html
One chapter alone:     python3 -I build.py /tmp/x.html ch02 [ch03 ...]  (front matter and the named chapters only)
"""
import glob, html, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else 'ebpf-dossier.html')
TAG_ORDER = ['LINEAGE', 'ISA', 'LOADER', 'VERIFIER', 'RUNTIME', 'HW']

def read(p): return open(os.path.join(HERE, p), encoding='utf-8').read()

def fig(m):
    return read(f'figs/out/{m.group(1)}.svg')

def twins(m):
    files = sorted(glob.glob(os.path.join(HERE, 'figs', 'out', f'{m.group(1)}-twin*.svg')))
    if not files: raise SystemExit(f'no twins for {m.group(1)}')
    return ''.join(open(f, encoding='utf-8').read() for f in files)

def text(t):
    t = re.sub(r'<(script|style|svg|template)[^>]*>.*?</\1>', ' ', t, flags=re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t))).strip()

def prose_words(t):
    for pat in [r'<figure.*?</figure>', r'<pre.*?</pre>', r'<table.*?</table>', r'<ol class="ribbon".*?</ol>', r'<header.*?</header>',
                r'<aside class="mn".*?</aside>', r'<div class="(check|lab|readwith|words|recap|field)".*?</div>', r'<template.*?</template>']:
        t = re.sub(pat, ' ', t, flags=re.S)
    return len(text(t).split())

ONLY = set(sys.argv[2:])
chapters = []
for path in sorted(glob.glob(os.path.join(HERE, 'src', 'ch[0-9][0-9].html'))):
    if ONLY and os.path.basename(path)[:4] not in ONLY: continue
    raw = open(path, encoding='utf-8').read()
    parts = dict(re.findall(r'<!--(CHAPTER|ANSWERS|GLOSSARY|REFS)-->(.*?)(?=<!--(?:CHAPTER|ANSWERS|GLOSSARY|REFS)-->|\Z)', raw, re.S))
    sec = parts['CHAPTER']
    # a side note floats beside the paragraph it follows in the source: move it above that block
    sec = re.sub(r'(<p(?:\s[^>]*)?>(?:(?!</p>).)*</p>|<div class="field">.*?</div>)\s*(<aside class="mn">.*?</aside>)',
                 lambda m: m.group(2) + '\n' + m.group(1), sec, flags=re.S)
    sec = re.sub(r'\{\{fig:([\w-]+)\}\}', fig, sec)
    sec = re.sub(r'\{\{twins:([\w-]+)\}\}', twins, sec)
    cid = re.search(r'<section id="(ch\d+)"', sec).group(1)
    num = int(cid[2:])
    title = text(re.search(r'<h2>(.*?)</h2>', sec, re.S).group(1))
    words = prose_words(sec)
    figs = sec.count('<figure class="fig')
    minutes = round(words / 200 + figs)
    sec = sec.replace('{{min}}', str(minutes))
    chapters.append(dict(id=cid, num=num, title=title, sec=sec, words=words, figs=figs, minutes=minutes,
                         answers=parts.get('ANSWERS', '').strip(), glossary=parts.get('GLOSSARY', '').strip(),
                         refs=parts.get('REFS', '').strip()))
chapters.sort(key=lambda c: c['num'])
label = lambda c: 'Prologue' if c['num'] == 0 else ('Epilogue' if 'Epilogue' in c['title'] else f"Chapter {c['num']}")

tot_words = sum(c['words'] for c in chapters); tot_figs = sum(c['figs'] for c in chapters)
tot_min = sum(c['minutes'] for c in chapters)

front = read('src/front.html')
front = (front.replace('{{chapters}}', str(len(chapters))).replace('{{words}}', f'{round(tot_words, -2):,}')
              .replace('{{minutes}}', str(tot_min)).replace('{{figures}}', str(tot_figs)))
contents = ['<section id="contents" class="front"><h2>Contents</h2><ol>',
            '<li><span class="n">—</span><a href="#how-to-read">How to read this</a><span class="rt"></span></li>']
for c in chapters:
    n = '' if c['num'] == 0 else str(c['num'])
    contents.append(f'<li><span class="n">{n}</span><a href="#{c["id"]}">{html.escape(c["title"])}</a><span class="rt">{c["minutes"]} min</span></li>')
contents.append('<li class="group">Back matter</li>')
for sid, name in [('answers', 'Answer key'), ('glossary', 'Glossary'), ('references', 'References')]:
    contents.append(f'<li><span class="n">—</span><a href="#{sid}">{name}</a><span class="rt"></span></li>')
contents.append('</ol></section>')

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
        bytag.setdefault(tag, []).append(li)
refs = ['<section id="references" class="backmatter"><h2>References</h2><div class="refs">']
for tag in TAG_ORDER:
    if tag in bytag: refs += [f'<h4>{tag.title() if tag not in ("ISA", "HW") else tag}</h4><ul>'] + bytag[tag] + ['</ul>']
refs.append('</div></section>')

body = '\n'.join([front.split('<!--HOWTO-->')[0], '<main>', '\n'.join(contents), front.split('<!--HOWTO-->')[1]]
                 + [c['sec'] for c in chapters] + ['\n'.join(key), '\n'.join(gloss), '\n'.join(refs), '</main>'])
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
<title>The life of one program — an eBPF book dossier</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,500;0,7..72,600;1,7..72,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{read('book.css')}
</style>
<script>window.PagedConfig = {{auto: false}};</script>
<script src="https://cdn.jsdelivr.net/npm/pagedjs@0.4.3/dist/paged.polyfill.min.js"></script>
</head>
<body>
<div class="book">
{body}
</div>
<script type="module">
document.querySelectorAll('details.hint').forEach(d => d.open = true);{mermaid}
await document.fonts.ready;
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
