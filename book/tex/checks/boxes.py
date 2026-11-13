"""List box parts drawn open: a ruled sidebar whose frame lacks its top or bottom rule on some page.
  python3 -I checks/boxes.py book.pdf
tcolorbox draws a frame as a black area with a white area over it; a side is ruled where the two differ, or where
a stroked rule of the frame's width runs along that edge (the closing rules ebpfbook.sty draws at a page break)."""
import sys, pymupdf
d = pymupdf.open(sys.argv[1]); bad = 0
for n, p in enumerate(d, 1):
    draws = p.get_drawings()
    dr = [x for x in draws if x['type'] == 'f' and x['rect'].width > 200]
    black = [x['rect'] for x in dr if x.get('fill') == (0.0, 0.0, 0.0)]
    white = [x['rect'] for x in dr if x.get('fill') == (1.0, 1.0, 1.0)]
    strokes = [x['rect'] for x in draws if x['type'] in ('s', 'fs') and x['rect'].width > 200 and x['rect'].height < 1.5]
    for o in black:
        inner = [w for w in white if o.x0 - .1 <= w.x0 and w.x1 <= o.x1 + .1 and o.y0 - .1 <= w.y0 and w.y1 <= o.y1 + .1]
        if not inner: continue
        w = max(inner, key=lambda r: r.width * r.height)
        ruled = lambda y: any(abs(s.y0 - y) < 1 and abs(s.x0 - o.x0) < 1 and abs(s.x1 - o.x1) < 1 for s in strokes)
        miss = [s for s, gap, y in (('top', w.y0 - o.y0, o.y0), ('bottom', o.y1 - w.y1, o.y1 - .5), ('left', w.x0 - o.x0, None), ('right', o.x1 - w.x1, None))
                if gap < .2 and not (y is not None and ruled(y))]
        if miss: print(f'page {n} (folio {p.get_label()}): box at y {o.y0:.0f}-{o.y1:.0f} has no {" or ".join(miss)} rule'); bad += 1
print('open box parts:', bad)
