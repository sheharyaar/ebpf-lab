#!/usr/bin/env python3
"""Every number the two editions print, one per line, to diff before and after a change to the numbering.
  python3 -I tools/numbers_snapshot.py BUILT.html TEXOUTDIR > list.txt
Screen: the eyebrow of each chapter, each figure's number, each answer-key label.
Print: the contents number of each chapter, its figure numbers in order, the answer-key headings and labels."""
import glob, html, os, re, sys

def strip(t):
    t = re.sub(r'\\hypertarget\{[^}]*\}\{\}', '', t)
    t = re.sub(r'\\hyperlink\{[^}]*\}\{([^{}]*)\}', r'\1', t)
    return re.sub(r'<[^>]+>', '', html.unescape(t)).strip()

s = open(sys.argv[1], encoding='utf-8').read()
out = []
for cid, body in re.findall(r'<section id="([\w-]+)" class="chapter"[^>]*>(.*?)(?=<section[ >]|</main>)', s, re.S):
    out.append(f'screen chapter {cid} {strip(re.search(r"<p class=.eyebrow.>(.*?)</p>", body).group(1))}')
    for fid, fn in re.findall(r'<figure class="fig[^"]*" id="([\w-]+)".*?<b class="fn">(.*?)</b>', body, re.S):
        out.append(f'screen figure {fid} {strip(fn)}')
key = s[s.index('<section id="answers"'):]
key = key[:key.index('</section>')]
for kind, tid, lab in re.findall(r'<div class="(ans|sol)" data-for="([\w-]+)"[^>]*><p class="q"[^>]*>(.*?)</p>', key):
    out.append(f'screen {kind} {tid} {strip(lab)}')
for h in re.findall(r'<h3>(.*?)</h3>', key): out.append(f'screen keyhead {strip(h)}')

d = sys.argv[2]
for f in sorted(glob.glob(os.path.join(d, 'ch*.tex')) + glob.glob(os.path.join(d, 'primer.tex'))):
    t = open(f, encoding='utf-8').read(); name = os.path.basename(f)[:-4]
    out.append(f'print chapter {name} {re.search(r"chaptocinfo\{([^}]*)\}", t).group(1)} '
               f'{strip(re.search(r"chapteropen\{([^}]*)\}", t).group(1))}')
    for i, n in enumerate(re.findall(r"\\figcap(?:save)?\{([^}]*)\}", t), 1): out.append(f'print figure {name} #{i} {n}')
b = open(os.path.join(d, 'back.tex'), encoding='utf-8').read()
b = b[b.index('Answer key'):b.index('backmatterhead{Glossary}')]
for m in re.finditer(r'\\keychapter\{([^}]*)\}|\\begin\{(answer|solution)\}\{((?:[^{}]|\{[^{}]*\})*)\}', b):
    out.append(f'print keyhead {m.group(1)}' if m.group(1) else f'print {m.group(2)} {strip(m.group(3))}')
print('\n'.join(out))
