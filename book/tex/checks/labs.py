"""Flag labs that start at a page foot with too little of their Task: a lab's title, its meta line and at least the
first two lines of its Task must share a page.
  python3 -I checks/labs.py book.pdf     (or: sample.pdf)
A lab title is set in Open Sans Condensed at 11 pt and begins "Try it"; the meta line is Open Sans Condensed at 8.4 pt;
the Task is body text (Crimson Pro, with Ubuntu Mono for inline code). The folio line is Open Sans Condensed too."""
import sys, pymupdf
d = pymupdf.open(sys.argv[1]); bad = 0; labs = 0
for n, p in enumerate(d, 1):
    rows = []
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            sp = [s for s in l['spans'] if s['text'].strip()]
            if sp: rows.append((l['bbox'][0], l['bbox'][1], sp[0]['font'], sp[0]['size'], ''.join(s['text'] for s in sp).strip()))
    for x, y, font, size, text in rows:
        if not (text.startswith('Try it') and 'Condensed' in font and abs(size - 11) < .3): continue
        labs += 1
        below = {round(y2) for x2, y2, f2, s2, t2 in rows if y2 > y + 1 and x - 3 <= x2 < x + 330 and 'Condensed' not in f2}
        if len(below) < 2:
            print(f'page {n} (folio {p.get_label()}): lab "{text[:60]}" has {len(below)} line(s) of its Task on the page'); bad += 1
print('labs:', labs, ' stranded labs:', bad)
