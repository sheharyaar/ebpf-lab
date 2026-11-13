"""Flag pages that end on a heading: the last text line (before the folio) is a section, box or hint title.
  python3 -I checks/strand.py book.pdf out/*.tex     (or: sample.pdf out/body.tex)"""
import sys, re, subprocess
pdf, texs = sys.argv[1], sys.argv[2:]
src = ''.join(open(t, encoding='utf-8').read() for t in texs)
HEAD = (r'\\(?:booksection(?:\[[^]]*\])?|closingsection|boxhead|keychapter|backmatterhead|commitsha)\{([^}]*)\}'
        r'|\\begin\{(?:hint|rbox|sidebar)\}(?:\{[^}]*\})?\{([^}]*)\}'
        r'|\\(?:partpage|appendixopen|chapteropen)\{[^}]*\}\{([^}]*)\}')
heads = [re.sub(r'\\[a-z]+\{|[{}\\]', '', m).strip().lower() for m in re.findall(HEAD, src) for m in m if m]
pages = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout.split('\f')
bad = 0
for n, p in enumerate(pages, 1):
    ls = [l.strip() for l in p.splitlines() if l.strip() and not re.fullmatch(r'[\divxlc]+', l.strip()) and not re.search(r'^[\divxlc]+\s+\||\|\s+[\divxlc]+$', l.strip())]
    if 'Table of Contents' in p: continue                     # the contents list every heading by design
    last = re.sub(r'\s+', ' ', ls[-1].lower()) if ls else ''
    if last and any(h and (last == h or (last.startswith(h[:25]) and len(last) <= len(h) + 4)) for h in heads):
        print('page', n, 'ends on a heading:', ls[-1][:70]); bad += 1
print('stranded headings:', bad)
