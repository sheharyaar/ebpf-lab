#!/usr/bin/env python3
"""Turn chapter sources (src/chNN.html) into LaTeX for the printed book.

The HTML stays the source we write and audit; this script is only the print back end.
  python3 -I tex/html2tex.py ch04 [ch05 ...]   ->  tex/out/body.tex, tex/out/figs/*.pdf
Then:  cd tex && lualatex sample.tex  (twice, for the page-parity checks of wide figures)
The whole book:  python3 -I tex/html2tex.py --book  ->  tex/out/book-body.tex (front, one file a chapter, back)
Then:  cd tex && lualatex book.tex  (until the contents settle, two or three runs)  ->  tex/book.pdf

Every class the chapters use maps to one macro or environment in tex/ebpfbook.sty.
Numbers and cross-references come from numbering.py (shared with build.py); a cross-reference becomes \\hyperlink.
The index: --book writes out/index.json (what each \\ixm marker in the text stands for); after a lualatex run
  python3 -I html2tex.py --index   turns book.ixw (marker, page) into book.idx and runs makeindex -> book.ind
"""
import glob, html, json, os, re, shutil, subprocess, sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
BOOK = os.path.dirname(HERE)
sys.path.insert(0, BOOK)
import numbering
NUM = numbering.get(os.path.join(BOOK, 'src'))
LINKABLE = set()          # ids that have a target in this run: a reference to anything else prints without a link
WORK = HERE                       # where LuaLaTeX runs: tex/, or the private directory given with --out
OUT = os.path.join(HERE, 'out')
FIGOUT = os.path.join(OUT, 'figs')
TEXTHEIGHT = 233.4 - 20 - 25 # mm, from the geometry in ebpfbook.sty
FIGWIDTH = 127                # mm: the text width, as O'Reilly sets figures

# ---------------------------------------------------------------- a small DOM
VOID = {'br', 'col', 'img', 'meta', 'hr', 'wbr'}
class Node:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs or {}), parent, []
    @property
    def cls(self): return set(self.attrs.get('class', '').split())
    def has(self, c): return c in self.cls
    def elems(self): return [k for k in self.kids if isinstance(k, Node)]
    def find(self, tag=None, cls=None):
        for k in self.elems():
            if (tag is None or k.tag == tag) and (cls is None or k.has(cls)): return k
        return None
    def walk(self):
        for k in self.kids:
            if isinstance(k, Node):
                yield k; yield from k.walk()

class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.root = Node('#root'); self.cur = self.root
    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur); self.cur.kids.append(n)
        if tag not in VOID: self.cur = n
    def handle_startendtag(self, tag, attrs): self.cur.kids.append(Node(tag, attrs, self.cur))
    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag: n = n.parent
        if n is not self.root: self.cur = n.parent
    def handle_data(self, d): self.cur.kids.append(d)

def parse(s):
    t = Tree(); t.feed(s); t.close(); return t.root

# ---------------------------------------------------------------- text
TIE = '\ue000'           # a tie tied() puts into a title: inline() keeps it (it is not \s, as U+00A0 is) and esc() sets ~
SPECIAL = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
           '~': r'\textasciitilde{}', '^': r'\textasciicircum{}', '\u00a0': '~', '\u2009': r'\,', '\u202f': r'\,', TIE: '~'}
def esc(s): return ''.join(SPECIAL.get(c, c) for c in s)

def curly(s, prev):
    """Straight quotes to curly ones; prev is the character before s."""
    out = []
    for c in s:
        opening = (prev == '' or prev.isspace() or prev in '([{\u2014\u2013/' + TIE)
        if c == '"': c = '\u201c' if opening else '\u201d'
        elif c == "'": c = '\u2018' if opening else '\u2019'
        out.append(c); prev = c
    return ''.join(out)

def code_esc(s):
    s = re.sub(r'(?<![A-Za-z0-9])-|-(?![A-Za-z0-9])', r'\\codehy{}', esc(s))   # only a hyphen inside a word (ebpf-verifier) may end a line, never -EACCES or --flag
    s = re.sub(r'(/|\\_|\.|\((?!\))|,|=|::?)(?=\S)', r'\1\\allowbreak{}', s)   # never between ( and )   # break points inside long names and paths
    return re.sub(r'(?<![0-9a-fA-F])([0-9a-f]{8})(?=[0-9a-f]{8,}(?![0-9a-zA-Z]))', r'\1\\allowbreak{}', s)   # and inside 64-bit addresses

# ---------------------------------------------------------------- figures and QR codes
def svg_to_pdf(name):
    src = os.path.join(BOOK, 'figs', 'out', name + '.svg'); dst = os.path.join(FIGOUT, name + '.pdf')
    shared = os.path.join(HERE, 'out', 'figs', name + '.pdf')      # a private build starts from the shared conversions
    if WORK != HERE and not os.path.exists(dst) and os.path.exists(shared) and os.path.getmtime(shared) >= os.path.getmtime(src):
        shutil.copy2(shared, dst)
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        subprocess.run(['rsvg-convert', '-f', 'pdf', '-o', dst, src], check=True, env=FIGENV)
    return 'figs/' + name

def svg_width_px(name):
    s = open(os.path.join(BOOK, 'figs', 'out', name + '.svg'), encoding='utf-8').read(2000)
    m = re.search(r'viewBox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"', s)
    return (float(m.group(1)), float(m.group(2))) if m else (900.0, 400.0)

def qr_size(url):
    """The same size rule as build.py: 0.42 mm a module, 14 to 26 mm, quiet zone excluded here (the margin gives it)."""
    level = 'M' if len(url) <= 60 else 'L'
    svg = subprocess.run(['qrencode', '-t', 'SVG', '-m', '0', '-l', level, '-o', '-', url], capture_output=True, text=True, check=True).stdout
    n = int(re.search(r'viewBox="0 0 (\d+) ', svg).group(1))
    return level, max(12.4, min(24.3, round(n * 0.42, 1)))

def qr_tex(url):
    level, size = qr_size(url)
    u = ''.join('\\' + c if c in '#$&^_~%{}\\' else c for c in url)
    return f'\\qrcode[height={size}mm,level={level}]{{{u}}}'

# ---------------------------------------------------------------- inline content
TAGCOL = {'LINEAGE': 'grayx', 'ISA': 'coralx', 'LOADER': 'amberx', 'VERIFIER': 'tealx', 'RUNTIME': 'greenx', 'HW': 'purplex'}

class Ctx:
    def __init__(self):
        self.prev = ''; self.afterhead = False   # afterhead: the next block follows a heading
        self.nolink = False                      # inside a link already: cross-references print as text
        self.index = False                       # text here is indexed (chapter prose, not headings or back matter)
        self.inbold = False

def prose_text(t, ctx):
    """Escaped prose, with an index marker after each term the index lists."""
    if not (ctx.index and IX.on):
        return esc(t).replace('\\_', '\\_\\allowbreak{}')   # long identifiers in prose may break after _
    out, last = [], 0
    for m in IX.terms_in(t):
        out.append(esc(t[last:m.end()]).replace('\\_', '\\_\\allowbreak{}')); last = m.end()
        out.append(IX.mark_term(m.group(0)))
    out.append(esc(t[last:]).replace('\\_', '\\_\\allowbreak{}'))
    return ''.join(out)

# a number and the unit after it, a program and its version, "page 10": never split at a line end (prose only)
UNITS = r'(?:ns|[µμ]s|us|ms|s|min|KB|kB|MB|GB|TB|KiB|MiB|GiB|B|bytes|bits|pt|mm|GHz|MHz)(?!\w)|%|×'
NUMBER = r'(?<![\w.,\-−])[−~≈-]?\d(?:[\d,.]*\d)?'
TIE_RE = re.compile(rf'({NUMBER}) (?={UNITS})'
                    r'|\b((?:Linux|clang|LLVM|bpftool|libbpf) )(?=v?\d)'
                    r'|\b((?:kernel|version|v) )(?=\d+(?:\.\d+)+(?!\w))'
                    r'|\b((?:[Pp]age|Figure|Chapter|chapter|Lab|Table|Question|question|Part|Appendix) )(?=[\dP][\w.\-]*)')
UNIT_TIES = [0]
def tie_units(t, count=True):
    """t with the space of each such pair made non-breaking (U+00A0, which esc() sets ~)."""
    def one(m):
        UNIT_TIES[0] += count
        return m.group(0)[:-1] + ' '
    return TIE_RE.sub(one, t)

def inline(node, ctx, code=False, root=True):
    """The content of one block (a paragraph, item, cell, caption, heading, term or definition) as LaTeX.
    Quotes are curled within the block: each block starts as at the start of a line."""
    if root and not code: ctx.prev = ''
    out = []
    for k in node.kids:
        if isinstance(k, str):
            if code:
                out.append(code_esc(k))
            else:
                t = re.sub(r'[^\S\u00a0]+', ' ', k)          # a typed &nbsp; stays: esc() sets it ~
                t = tie_units(t)
                t = curly(t, ctx.prev)
                if t: ctx.prev = t[-1]
                out.append(prose_text(t, ctx) if not ctx.inbold else esc(t).replace('\\_', '\\_\\allowbreak{}'))
            continue
        t = k.tag
        if t == 'code':
            out.append('\\code{' + inline(k, ctx, code=True, root=False) + '}'); ctx.prev = 'x'
            if ctx.index and IX.on and not code: out.append(IX.mark_code(plain_raw(k)))
        elif t == 'b' and k.has('fn'):
            continue                                   # figure numbers are set by the caption macro
        elif t == 'b' and k.has('hl'):
            out.append('\\hl{' + inline(k, ctx, code, False) + '}')
        elif t in ('b', 'strong'):
            defined = ctx.index and IX.on and not code and IX.defining(plain(k))
            ctx.inbold, was = bool(defined), ctx.inbold
            out.append('\\textbf{' + inline(k, ctx, code, False) + '}')
            ctx.inbold = was
            if defined: out.append(defined)
        elif t in ('i', 'em', 'cite'):
            out.append(('\\textcolor{mut}{' if code else '\\emph{') + inline(k, ctx, code, False) + '}')
        elif t == 'sup':
            out.append('\\textsuperscript{' + inline(k, ctx, code, False) + '}')
        elif t == 'sub':
            out.append('\\textsubscript{' + inline(k, ctx, code, False) + '}')
        elif t == 'wbr':
            out.append('\\allowbreak{}')
        elif t in ('col', 'colgroup'):
            continue
        elif t == 'br':
            out.append('\\newline{}' if not code else '\n')
        elif t == 'span' and k.has('tag'):
            name = (k.cls - {'tag'}).pop()
            out.append(f'\\layertag{{{TAGCOL.get(name, "ink")}}}{{{name.lower()}}}')
        elif t == 'span' and k.has('k'):
            continue                                   # side-note titles are taken out by the side-note macro
        elif t == 'a' and k.has('xref'):
            tid = k.attrs.get('href', '#')[1:]
            lab = esc(curly(tie_units(plain(k)), '')); ctx.prev = plain(k)[-1:] or ctx.prev
            if k.has('sec') or NUM.targets.get(tid, ('',))[0] == 'section':
                if tid in LINKABLE: lab += f' on page~\\pageref*{{{tid}}}'; ctx.prev = '0'   # O'Reilly: "Title" on page 136
            out.append(lab if ctx.nolink or tid not in LINKABLE else f'\\hyperlink{{{tid}}}{{{lab}}}')
        elif t == 'a':
            out.append(inline(k, ctx, code, False))
        else:
            out.append(inline(k, ctx, code, False))
    return ''.join(out)

def plain_raw(node):
    return ''.join(k if isinstance(k, str) else plain_raw(k) for k in node.kids)

def plain(node):
    return re.sub(r'\s+', ' ', ''.join(k if isinstance(k, str) else plain(k) for k in node.kids)).strip()

def tocplain(node):
    """A heading as plain text for PDF bookmarks: curly quotes, LaTeX specials escaped."""
    return esc(curly(plain(node), ''))

TIEMAX = 12              # a last word longer than this is left free: tied, it would leave a wide gap in the line above
def tied(node):
    """A copy of a title or heading with its last two words tied, so that the last word never stands alone on a line.
    Not when the last word is longer than TIEMAX characters, nor when the space is inside code. A tie typed in the
    source (&nbsp;) is kept, so a title that has one already converts as one that has not."""
    import copy
    node = copy.deepcopy(node)
    segs = []                                      # (parent, index in its kids, inside code), in reading order
    def go(n, incode):
        for i, k in enumerate(n.kids):
            if isinstance(k, str): segs.append((n, i, incode))
            else: go(k, incode or k.tag == 'code')
    go(node, node.tag == 'code')
    for n, i, incode in segs:                      # typed ties survive inline()'s squeezing of white space
        if not incode: n.kids[i] = n.kids[i].replace(' ', TIE)
    full = ''.join(n.kids[i] for n, i, _ in segs).rstrip()
    m = None
    for m in re.finditer(r'[\s' + TIE + ']+', full): pass
    if m is None or TIE in m.group(0) or m.start() == 0 or len(full) - m.end() > TIEMAX: return node
    at, rest = 0, 0                                # the last run of white space becomes the tie
    for n, i, incode in segs:
        k = n.kids[i]
        if at <= m.start() < at + len(k):
            if incode: return node
            j, end = m.start() - at, min(len(k), m.end() - at)
            n.kids[i] = k[:j] + TIE + k[end:]
            rest = m.end() - at - end              # the run goes on into the next piece of text: take it out there
        elif at > m.start() and rest > 0:
            cut = min(rest, len(k)); n.kids[i] = k[cut:]; rest -= cut
        at += len(k)
    return node

def tied_tex(t):
    """The same for a title that is LaTeX already (a part or appendix title): its last space becomes ~."""
    head, sp, last = t.rpartition(' ')
    if not sp or visible_len(last) > TIEMAX or head.count('{') != head.count('}'): return t
    return head + '~' + last

# ---------------------------------------------------------------- blocks
def sidenote(aside, ctx):
    k = aside.find('span', 'k')
    title = inline(k, ctx) if k else ''
    return f'\\sidenote{{{title}}}{{{inline(aside, ctx).strip()}}}'

def rawtext(node):
    return ''.join(k if isinstance(k, str) else rawtext(k) for k in node.kids)

VERIFIER_LINE = re.compile(r'^\s*\d+: \([0-9a-f]{2}\)', re.M)
def visible_len(line):
    """Characters a Verbatim line prints: macros, braces and escapes taken out."""
    t = re.sub(r'\\text(?:backslash|asciitilde|asciicircum)\{\}', 'x', line)
    t = re.sub(r'\\(?:textbf|hl|emph|textcolor\{mut\}|code)\{', '', t)
    t = re.sub(r'\\(.)', 'x', t)
    return len(t.replace('{', '').replace('}', ''))

def split_verifier(body, cols):
    """A verifier log line too long for the column breaks before the ' ; ' that starts the register state,
    which goes on an indented continuation line (Verbatim still breaks a state that is longer than a line)."""
    out = []
    for line in body.split('\n'):
        k = line.find(' ; ')
        head = line[:k] if k > 0 else ''
        if k > 0 and visible_len(line) > cols and re.sub(r'\\.', '', head).count('{') == re.sub(r'\\.', '', head).count('}'):
            out += [head.rstrip(), '    ' + line[k + 1:]]
        else:
            out.append(line)
    return '\n'.join(out)

# characters of Ubuntu Mono 8.5 pt (4.25 pt each) on a code line: the column less the 6 mm indent, less a box's own indent
TOKEN = re.compile(r'\\[a-zA-Z]+\{\}|\\textcolor\{\w+\}\{|\\[a-zA-Z]+\{|\\[^a-zA-Z]|[{}]|\n|[^\\{}\n]+')
def close_per_line(body):
    """Inline markup (\\hl{...}, \\textcolor{mut}{...}) that spans lines of a listing is closed at the end of each line
    and opened again on the next, so that every Verbatim line is a group of its own."""
    out, stack = [], []
    for t in TOKEN.findall(body):
        if t == '\n': out.append('}' * len(stack) + '\n' + ''.join(stack))
        elif t.endswith('{') and t.startswith('\\') and len(t) > 2: stack.append(t); out.append(t)
        elif t == '{': stack.append('{'); out.append(t)
        elif t == '}':
            if stack: stack.pop()
            out.append(t)
        else: out.append(t)
    return ''.join(out)

CODECOLS = {None: 81, 'ans': 72, 'lab': 75, 'readwith': 75, 'costs': 75}
CODELINE = 10.2                       # pt, the Verbatim baseline skip in ebpfbook.sty
def listing_lines(body, cols=81):
    """Lines a listing prints, counting the continuation lines Verbatim breaks a long line into."""
    return sum(max(1, -(-visible_len(l) // cols)) for l in body.split('\n'))

def pre_block(pre, ctx, box=None, infig=None):
    """A listing. Outside a figure one longer than 24 lines may break across pages; inside one (infig: the figure's
    id) it never does, as the figure cannot, and is set unbroken whatever its length (fitbody scales it to the page)."""
    code = pre.find('code') or pre
    body = inline(code, ctx, code=True).strip('\n')
    body = body.replace('\\allowbreak{}', '')           # Verbatim breaks lines itself
    body = body.replace('~', '\u00a0')                  # a typed &nbsp; (esc() made it ~, which Verbatim prints as a
                                                      # tilde): the character itself, at which fvextra does not break
    body = close_per_line(body)
    if VERIFIER_LINE.search(rawtext(code)):
        body = split_verifier(body, CODECOLS.get(box, 81))
    if ctx.index and IX.on:
        marks = IX.mark_commands(rawtext(code))
        if marks: body = marks + body                        # on the first line: the page the listing starts on
    env = 'codeboxlong' if body.count('\n') > 24 and infig is None else 'codebox'   # short listings stay on one page, as in book.css
    if infig is not None:                    # a breakable box in fitbody's minipage spaces its lines unevenly: never there
        n = listing_lines(body, CODECOLS.get(box, 81))
        room = (TEXTHEIGHT * 72.27 / 25.4 - 2 * 12.6 - 3 - 2 * 2.85) / CODELINE   # less a two-line caption and the box's padding
        if n > room:
            warn(f'figure {infig}: its listing prints {n} lines, more than the {int(room)} a page holds under the caption: '
                 f'it is shrunk to fit ({100 * room / n:.0f} %); shorten it or take it out of the figure')
    return f'\\begin{{{env}}}\n\\begin{{Verbatim}}[commandchars=\\\\\\{{\\}}]\n' + body + f'\n\\end{{Verbatim}}\n\\end{{{env}}}\n'

# ---------------------------------------------------------------- measuring table text with the real fonts
FONTFILES = {'serif': '/usr/share/texmf-dist/fonts/truetype/public/crimsonpro/CrimsonPro-Regular.ttf',
             'bold': '/usr/share/texmf-dist/fonts/truetype/public/crimsonpro/CrimsonPro-SemiBold.ttf',
             'head': '/usr/share/fonts/TTF/OpenSans-CondensedSemiBold.ttf',
             'mono': os.path.join(HERE, 'fonts', 'UbuntuMono-Regular.ttf')}
MONOSCALE = 0.806                     # Scale=MatchLowercase in ebpfbook.sty
_fonts = {}
def advance(face, s, size):
    """Width of s in points at size, from the font's advance widths (kerning ignored)."""
    if face not in _fonts:
        try:
            from fontTools.ttLib import TTFont
            f = TTFont(FONTFILES[face]); _fonts[face] = (f.getBestCmap(), f['hmtx'].metrics, f['head'].unitsPerEm)
        except Exception:
            _fonts[face] = None
    if _fonts[face] is None: return len(s) * size * (0.5 if face == 'mono' else 0.45)
    cmap, hmtx, upm = _fonts[face]
    w = 0
    for c in s:
        g = cmap.get(ord(c)); w += hmtx[g][0] if g in hmtx else upm / 2
    return w * size / upm * (MONOSCALE if face == 'mono' else 1)

def cell_runs(node, face='serif'):
    """The text of a table cell as lines of (face, text) runs; <br> starts a new line."""
    lines = [[]]
    def go(n, face):
        for k in n.kids:
            if isinstance(k, str): lines[-1].append((face, tie_units(re.sub(r'[^\S\u00a0]+', ' ', k), False) if face != 'mono' else k))
            elif k.tag == 'br': lines.append([])
            elif k.tag == 'code': go(k, 'mono')
            elif k.tag in ('b', 'strong') and face == 'serif': go(k, 'bold')
            else: go(k, face)
    go(node, face)
    return lines

def cell_widths(node, size, face):
    """(longest unbreakable word, longest line) of a cell, in points."""
    word = line = 0.0
    for runs in cell_runs(node, face):
        lw = 0.0; cur = 0.0
        for f, t in runs:
            lw += advance(f, t, size)
            for i, piece in enumerate(t.split(' ')):
                if i > 0: word = max(word, cur); cur = 0.0
                bits = re.split(r'(?<=[/_.,=])(?=\S)|(?<=\()(?=[^\s)])|(?<=::)(?=\S)|(?<=^[0-9a-f]{8})(?=[0-9a-f]{8})', piece) if f == 'mono' else [piece]   # code_esc's break points
                for j, b in enumerate(bits):
                    if j > 0: word = max(word, cur); cur = 0.0
                    cur += advance(f, b, size)
        word = max(word, cur); line = max(line, lw)
    return word, line

TABLESIZE = 9.6                       # the booktable font size in ebpfbook.sty
def column_widths(rows, ncol, width=FIGWIDTH):
    """Column widths in points that fill the text width. No column is narrower than its longest word; a column whose
    longest line fits under a cap keeps it, so short row labels do not wrap; the rest share what is left by content."""
    pt = 72.27 / 25.4
    avail = width * pt - ncol * 12.0                     # \tabcolsep 6 pt on each side of each column
    minw = [0.0] * ncol; natw = [0.0] * ncol; mass = [0.0] * ncol
    for r in rows:
        cs = [c for c in r.elems() if c.tag in ('td', 'th')]
        for i, c in enumerate(cs[:ncol]):
            w, l = cell_widths(c, TABLESIZE, 'head' if c.tag == 'th' else 'serif')
            minw[i] = max(minw[i], w + 1); natw[i] = max(natw[i], l + 1); mass[i] += l
    if sum(minw) > avail:                                   # even the longest words do not fit: share in proportion
        return [avail * m / sum(minw) for m in minw]
    if sum(natw) <= avail:                                  # everything fits on one line: share the slack by length
        return [n + (avail - sum(natw)) * n / sum(natw) for n in natw]
    cap = 0.3 * avail
    fixed = {i for i in range(ncol) if natw[i] <= cap}
    while True:
        rest = [i for i in range(ncol) if i not in fixed]
        room = avail - sum(natw[i] for i in fixed)
        if rest and room >= sum(minw[i] for i in rest): break
        if not fixed: break
        fixed.discard(max(fixed, key=lambda i: natw[i]))    # give up the widest short column first
    w = [natw[i] if i in fixed else 0.0 for i in range(ncol)]
    free = list(rest); room = avail - sum(w)
    while free:                                             # share by content, never below the longest word
        tot = sum(mass[i] for i in free) or 1.0
        short = [i for i in free if room * mass[i] / tot < minw[i]]
        if not short:
            for i in free: w[i] = room * mass[i] / tot
            break
        for i in short: w[i] = minw[i]; room -= minw[i]; free.remove(i)
    over = [i for i in range(ncol) if i not in fixed and w[i] > natw[i]]
    for i in over:                                          # never wider than the longest line: give the rest back
        extra = w[i] - natw[i]; w[i] = natw[i]
        others = [j for j in range(ncol) if j not in fixed and w[j] < natw[j]] or [j for j in range(ncol) if j != i]
        for j in others: w[j] += extra / len(others)
    return w

def table_block(tab, ctx, width=FIGWIDTH):
    rows = [r for r in tab.walk() if r.tag == 'tr']
    if not rows: return ''
    ncol = max(len([c for c in r.elems() if c.tag in ('td', 'th')]) for r in rows)
    width = column_widths(rows, ncol, width)
    width = [ncol * w / sum(width) for w in width]           # X columns, each its share of the table
    spec = ''.join(f'>{{\\hsize={w:.3f}\\hsize\\raggedright\\arraybackslash}}X' for w in width)
    lines = [f'\\begin{{booktable}}{{{spec}}}']
    head = [r for r in rows if r.find('th')]
    body = [r for r in rows if not r.find('th')]
    for r in head:
        lines.append(' & '.join('\\thead{' + inline(c, ctx) + '}' for c in r.elems() if c.tag in ('td', 'th')) + ' \\\\ \\midrule')
    for i, r in enumerate(body):
        lines.append(' & '.join(inline(c, ctx).strip() for c in r.elems() if c.tag in ('td', 'th')) + ' \\\\' + (' \\rowrule' if i < len(body) - 1 else ''))
    lines.append('\\end{booktable}')
    return '\n'.join(lines) + '\n'

def figure_block(fig, ctx, figs):
    cap = fig.find('figcaption')
    num = plain(cap.find('b', 'fn')) if cap and cap.find('b', 'fn') else ''
    num = re.sub(r'(\d+|P)\.(\d+)$', r'\1-\2', num)
    captext = inline(cap, ctx).strip() if cap else ''
    names = figs.get(fig.attrs.get('id'), [])
    missing = [n for n in names if not os.path.exists(os.path.join(BOOK, 'figs', 'out', n + '.svg'))]
    if missing:
        warn(f'figure {fig.attrs.get("id")}: no SVG for {", ".join(missing)}')
        names = [n for n in names if n not in missing]
    parts = []
    nat = [FIGWIDTH * h / w for w, h in (svg_width_px(n) for n in names)]   # natural heights at full width
    room = 0.86 * TEXTHEIGHT - 16 - 2 * max(0, len(names) - 1)            # less the caption and the gaps
    scale = min(1.0, room / sum(nat)) if nat else 1.0
    for n in names:
        parts.append(f'\\figimage{{{svg_to_pdf(n)}}}{{{FIGWIDTH * scale:.1f}mm}}')
    if not names:
        t = fig.find('table'); p = fig.find('pre')
        if t is not None: parts.append(table_block(t, ctx))
        if p is not None: parts.append(pre_block(p, ctx, infig=fig.attrs.get('id', '(no id)')))
    if not parts or missing:                              # a Mermaid block, a widget without twins, a missing drawing
        if not missing: warn(f'figure {fig.attrs.get("id")}: nothing printable (no SVG, table or listing); set as a placeholder')
        parts.append(f'\\figplaceholder{{{fig.attrs.get("id", "")}}}')
    body = '\n\\par\\vspace{2mm}\n'.join(parts)
    target = f'\\hypertarget{{{fig.attrs["id"]}}}{{}}' if fig.attrs.get('id') else ''
    if not names:                                     # a table or a listing: shrunk to fit the page if it is taller (fitbody)
        return (f'\\begin{{figure}}[tbp]{target}\n\\figcapsave{{{num}}}{{{captext}}}\n\\begin{{fitbody}}\n{body}\n\\end{{fitbody}}\n'
                '\\usebox\\cbcapbox\n\\end{figure}\n')
    return f'\\begin{{figure}}[tbp]{target}\n{body}\n\\figcap{{{num}}}{{{captext}}}\n\\end{{figure}}\n'

BOXES = {'recap': 'ink', 'words': 'ink', 'check': 'accentx', 'refs': 'ink', 'lab': 'amberx', 'readwith': 'purplex', 'costs': 'coralx'}

def nobreak_opt(ctx):
    """A list right under a heading may not break before its first item, or the heading is left alone at a page foot."""
    return '[beginpenalty=10000]' if getattr(ctx, 'afterhead', False) else ''

def dl_block(dl, ctx, kind):
    out = [f'\\begin{{{kind}}}' + nobreak_opt(ctx)]
    for k in dl.elems():
        if k.tag == 'dt': out.append(f'\\item[{{{inline(k, ctx).strip()}}}]')
        elif k.tag == 'dd': out.append(inline(k, ctx).strip() + '\\wordend')   # as tall as a term set on two lines
    out.append(f'\\end{{{kind}}}')
    return '\n'.join(out) + '\n'

def list_block(lst, ctx, refs=False):
    env = 'enumerate' if lst.tag == 'ol' else 'itemize'
    if refs: env = 'reflist'
    opts = [] if refs else [o for o in [nobreak_opt(ctx)[1:-1]] if o]
    qs = [NUM.number(li.attrs['id']) for li in lst.elems() if li.tag == 'li' and NUM.targets.get(li.attrs.get('id', ''), ('',))[0] == 'question']
    if qs and env == 'enumerate':                      # labels are the questions' numbers (4.1), as wide as the widest
        w = max(qs, key=len).replace('1', '0')
        opts.append(f'labelwidth=\\widthof{{{w}}},labelsep=5pt,leftmargin=\\widthof{{{w}}}+5pt')
    out = [f'\\begin{{{env}}}' + (f'[{",".join(opts)}]' if opts else '')]
    for li in lst.elems():
        if li.tag != 'li': continue
        qr = ''
        if refs:
            a = next((a for a in li.walk() if a.tag == 'a' and a.attrs.get('href', '').startswith('http')), None)
            if a is not None: qr = qr_tex(html.unescape(a.attrs["href"]))
        if refs:
            out.append(f'\\refitem{{{qr}}}{{{inline(li, ctx).strip()}}}'); continue
        item = '\\item '
        qid = li.attrs.get('id')
        if qid and qid in NUM.targets and NUM.targets[qid][0] == 'question':
            mark = NUM.number(qid) if env == 'enumerate' else '\\textbullet'   # the page and the key agree
            item = (f'\\item[\\hyperlink{{ans-{qid}}}{{{mark}}}]' if 'ans-' + qid in LINKABLE else f'\\item[{mark}]') + f'\\hypertarget{{{qid}}}{{}}'
        if li.find('p') is not None or li.find('pre') is not None:
            out.append(item + blocks(li, ctx, {}))
        else:
            out.append(item + inline(li, ctx).strip())
    out.append(f'\\end{{{env}}}')
    return '\n'.join(x for x in out if not (refs and x.startswith('\\begin{reflist}') or refs and x.startswith('\\end{reflist}'))) + '\n'

def box_block(div, ctx, kind):
    h4 = div.find('h4')
    head = inline(tied(h4), ctx).strip() if h4 is not None else ''
    sect = f'\\sectiontarget{{{h4.attrs["id"]}}}' if h4 is not None and h4.attrs.get('id') else ''
    inner = Node('div'); inner.kids = [k for k in div.kids if k is not h4]
    if kind in ('recap', 'words', 'check', 'refs'):           # O'Reilly ends a chapter with plain sections ("Summary")
        ctx.afterhead = True
        was, ctx.index = ctx.index, False                      # summaries, word lists and questions are not indexed
        body = blocks(inner, ctx, {}, box=kind)
        ctx.index = was
        return sect + f'\\closingsection{{{head}}}\n\n' + body   # the same look, no contents line
    target = f'\\hypertarget{{{div.attrs["id"]}}}{{}}' if div.attrs.get('id') else ''
    ctx.lab = div.attrs.get('id') if kind == 'lab' else None
    body = blocks(inner, ctx, {}, box=kind)
    ctx.lab = None
    need = '\\Needspace{6\\baselineskip}'
    meta = next((p for p in inner.elems() if p.tag == 'p' and 'labmeta' in p.cls), None) if kind == 'lab' else None
    if meta is not None:                               # a lab keeps its title, meta line and two lines of its Task together
        was, ctx.index = ctx.index, False
        need = f'\\labneed{{{head}}}{{{inline(meta, ctx).strip()}}}'
        ctx.index = was
    return f'{need}{sect}\\begin{{sidebar}}{{{head}}}{target}\\cbsectarget\n' + body + '\\end{sidebar}\n'   # O'Reilly sidebar

def blocks(node, ctx, figs, box=None):
    out = []; kids = node.elems() if any(isinstance(k, Node) for k in node.kids) else []
    if not kids:                                       # bare text inside a block element
        t = inline(node, ctx).strip()
        return (t + '\n\n') if t else ''
    prev = None; pending = []; deferred = []
    i = 0
    while i < len(kids):
        k = kids[i]; t = k.tag; c = k.cls
        if t != 'aside': ctx.afterhead, after = False, ctx.afterhead   # true only for the block right after a heading
        else: after = ctx.afterhead
        if t == 'aside' and 'mn' in c:
            pending.append(sidenote(k, ctx)); i += 1; continue
        # a side note belongs beside the paragraph it follows in the source: look ahead and pull it in
        j = i + 1; notes = []
        if t in ('p', 'div') and ('field' in c or t == 'p'):
            while j < len(kids) and kids[j].tag == 'aside' and kids[j].has('mn'):
                notes.append(sidenote(kids[j], ctx)); j += 1
        notes = pending + notes; pending = []
        lead = ''.join(notes)
        if t == 'p':
            if c & {'screen-only', 'html-only'}: i = j; continue
            body = inline(k, ctx).strip()
            if 'labmeta' in c: out.append(f'\\labmeta{{{lead}{body}}}\n\n')
            elif 'note' in c:
                lab = getattr(ctx, 'lab', None)
                if lab and 'sol-' + lab in LINKABLE and plain(k).startswith('Solution'):   # "Solution in the answer key ...": to the solution
                    ctx.nolink = True; body = inline(k, ctx).strip(); ctx.nolink = False
                    body = f'\\hyperlink{{sol-{lab}}}{{{body}}}'
                out.append(f'\\labnote{{{lead}{body}}}\n\n')
            elif 'rule' in c: out.append(f'\\costrule{{{lead}{body}}}\n\n')
            elif 'q' in c: out.append(f'\\ansnum{{{body}}}')
            else:
                out.append(f'{body}\n\n{lead}')                  # notes follow the paragraph they belong to
                out += deferred; deferred = []
            prev = 'p'
        elif t == 'h3':
            was, ctx.index = ctx.index, False; IX.section += 1
            if k.attrs.get('id'): out.append(f'\\sectiontarget{{{k.attrs["id"]}}}')
            out.append(f'\\booksection[{tocplain(k)}]{{{inline(tied(k), ctx).strip()}}}\n\n'); prev = 'h'; ctx.afterhead = True
            ctx.index = was
        elif t == 'h4':
            was, ctx.index = ctx.index, False
            if k.attrs.get('id'): out.append(f'\\sectiontarget{{{k.attrs["id"]}}}')
            out.append(f'\\boxhead{{{inline(tied(k), ctx).strip()}}}\n\n'); prev = 'h'; ctx.afterhead = True
            ctx.index = was
        elif t == 'figure' and prev == 'h':
            deferred.append(lead + figure_block(k, ctx, figs))   # a float right after a heading lets the heading strand: set it after the first paragraph
        elif t == 'figure':
            out.append(lead + figure_block(k, ctx, figs)); prev = 'fig'
        elif t == 'pre':
            out.append(lead + pre_block(k, ctx, box)); prev = 'pre'
        elif t == 'table':
            out.append(lead + table_block(k, ctx, FIGWIDTH - 12 if box == 'ans' else FIGWIDTH)); prev = 'table'   # answers are indented 12 mm
        elif t == 'div' and c & set(BOXES):
            out.append(lead + box_block(k, ctx, (c & set(BOXES)).pop())); prev = 'box'
        elif t == 'div' and 'field' in c:
            # each <cite> attributes the quotes before it (back to the cite before), as the screen edition sets them
            groups, cur = [], []
            for x in k.kids:
                if isinstance(x, Node) and x.tag == 'cite': groups.append((cur, x)); cur = []
                else: cur.append(x)
            if cur and any(not isinstance(x, str) or x.strip() for x in cur): groups.append((cur, None))
            body = ''
            for n, (part, cite) in enumerate(groups):
                inner = Node('div'); inner.kids = part
                body += ('\\par\\vspace{4pt}' if n else '') + blocks(inner, ctx, {}).strip()
                if cite is not None: body += f'\\fieldcite{{{inline(cite, ctx).strip()}}}'
            out.append(f'\\begin{{field}}{lead}{body}\\end{{field}}\n\n'); prev = 'box'
        elif t == 'details':
            s = k.find('summary'); inner = Node('div'); inner.kids = [x for x in k.kids if x is not s]
            out.append(f'\\begin{{hint}}{{{inline(s, ctx).strip()}}}\n' + blocks(inner, ctx, {}) + '\\end{hint}\n'); prev = 'box'
        elif t == 'dl':
            ctx.afterhead = after
            out.append(dl_block(k, ctx, 'costlist' if box == 'costs' else 'wordlist')); prev = 'dl'
        elif t in ('ol', 'ul'):
            ctx.afterhead = after
            out.append(list_block(k, ctx, refs=(box == 'refs'))); prev = 'list'
        elif t == 'div' and ('ans' in c or 'sol' in c):
            out.append(answer_block(k, ctx)); prev = 'box'
        elif t in ('div', 'section'):
            out.append(blocks(k, ctx, figs, box)); prev = 'div'
        i = j
    return ''.join(out + deferred)

def answer_block(div, ctx):
    q = div.find('p', 'q'); label = plain(q) if q is not None else ''
    inner = Node('div'); inner.kids = [k for k in div.kids if k is not q]
    env = 'solution' if div.has('sol') else 'answer'
    tid = div.attrs.get('data-for', '')
    if tid:                                            # the label goes back to the question or lab; the key entry is a target
        label = (f'\\hyperlink{{{tid}}}{{{label}}}' if tid in LINKABLE else label)
        label = f'\\hypertarget{{{"sol" if env == "solution" else "ans"}-{tid}}}{{}}' + label
    return f'\\begin{{{env}}}{{{label}}}\n' + blocks(inner, ctx, {}, box='ans') + f'\\end{{{env}}}\n'

# ---------------------------------------------------------------- the chapter opening
def opening(header, ctx, minutes, cid=''):
    eyebrow = inline(header.find('p', 'eyebrow'), ctx).strip()
    title = inline(tied(header.find('h2')), ctx).strip()
    lede = inline(header.find('p', 'lede'), ctx).strip()
    out = [f'\\chaptertarget{{{cid}}}\\chapteropen{{{eyebrow}}}{{{title}}}{{{tocplain(header.find("h2"))}}}{{{lede}}}']
    rib = header.find('ol', 'ribbon')
    if rib is not None:
        items = []
        for li in rib.elems():
            parts = [esc(p.strip()) for p in re.split(r'\n', ''.join(x if isinstance(x, str) else '\n' for x in li.kids))]
            items.append(('1' if li.has('here') else '0', parts[0], ' '.join(parts[1:])))
        out.append('\\begin{ribbon}{%d}' % len(items))
        out += [f'\\ribbonitem{{{i}}}{{{h}}}{{{y}}}{{{l}}}' for i, (h, y, l) in enumerate(items)]
        out.append('\\end{ribbon}')
    ul = header.find('ul', 'inthis')
    if ul is not None:
        out.append('\\begin{inthis}\n' + '\n'.join('\\item ' + inline(li, ctx).strip() for li in ul.elems()) + '\n\\end{inthis}')
    sp = header.find('p', 'spine')
    if sp is not None: out.append(f'\\spine{{{inline(sp, ctx).strip()}}}')
    cm = header.find('p', 'chmeta')
    if cm is not None: out.append(f'\\chmeta{{{inline(cm, ctx).strip().replace(r"\{\{min\}\}", str(minutes))}}}')
    return '\n'.join(out) + '\n\\chapterbody\n\n'

# ---------------------------------------------------------------- one chapter
def prose_words(t):
    for pat in [r'<figure.*?</figure>', r'<pre.*?</pre>', r'<table.*?</table>', r'<ol class="ribbon".*?</ol>', r'<header.*?</header>',
                r'<aside class="mn".*?</aside>', r'<div class="(check|lab|readwith|words|recap|field|costs|refs)".*?</div>', r'<template.*?</template>']:
        t = re.sub(pat, ' ', t, flags=re.S)
    t = re.sub(r'<a class="xref[^>]*>(.*?)</a>', r'\1', t)      # a cross-reference is part of the word it stands for
    t = re.sub(r'<[^>]+>', ' ', t)
    return len(html.unescape(t).split())

def chapter(cid):
    raw = NUM.fill_chapter(open(os.path.join(BOOK, 'src', f'{cid}.html'), encoding='utf-8').read(), 'print', cid)
    parts = dict(re.findall(r'<!--(CHAPTER|ANSWERS|GLOSSARY|REFS)-->(.*?)(?=<!--(?:CHAPTER|ANSWERS|GLOSSARY|REFS)-->|\Z)', raw, re.S))
    sec = parts['CHAPTER']
    figs = {}                                          # figure id -> svg names, the print twins standing in for widgets
    for m in re.finditer(r'<figure class="fig[^"]*" id="([\w-]+)"[^>]*>(.*?)</figure>', sec, re.S):
        body = re.sub(r'<template.*?</template>', '', m.group(2), flags=re.S)
        names = re.findall(r'\{\{fig:([\w-]+)\}\}', body)
        for t in re.findall(r'\{\{twins:([\w-]+)\}\}', body):
            found = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(BOOK, 'figs', 'out', f'{t}-twin*.svg')))
            names += found or [t + '-twin1']          # no twins yet: reported as missing by figure_block
        figs[m.group(1)] = names
    nfig = sec.count('<figure class="fig')
    minutes = round(prose_words(sec) / 200 + nfig)
    sec = re.sub(r'\{\{(fig|twins):[\w-]+\}\}', '', sec)
    root = parse(sec)
    section = next(n for n in root.walk() if n.tag == 'section')
    ctx = Ctx()
    header = section.find('header')
    rest = Node('div'); rest.kids = [k for k in section.kids if k is not header]
    IX.chapter = section.attrs.get('id', cid); IX.section = 0
    head = opening(header, ctx, minutes, section.attrs.get('id', cid))
    ctx.index = True
    tex = head + blocks(rest, ctx, figs)
    ctx.index = False
    answers = blocks(parse(parts.get('ANSWERS', '')), Ctx(), {}, box='ans')
    label = plain(header.find('p', 'eyebrow'))
    return dict(id=section.attrs.get('id', cid), tex=tex, label=label, answers=answers, title=plain(header.find('h2')),
                glossary=parts.get('GLOSSARY', '').strip(), refs=parts.get('REFS', '').strip())

def set_linkable(stems):
    """Targets that exist in this run: the chapters converted, their figures, questions and labs, their key entries."""
    LINKABLE.clear()
    for tid, (typ, c, n) in NUM.targets.items():
        if c['file'] in stems: LINKABLE.add(tid)
    for stem in stems:
        raw = open(os.path.join(BOOK, 'src', stem + '.html'), encoding='utf-8').read()
        for kind, tid in re.findall(r'<div class="(ans|sol)" data-for="([\w-]+)"', numbering.split_parts(raw).get('ANSWERS', '')):
            LINKABLE.add(f'{kind}-{tid}')

def main(ids):
    os.makedirs(FIGOUT, exist_ok=True)
    set_linkable(ids); IX.on = False                  # a sample has no index
    body, key = [], []
    for cid in ids:
        c = chapter(cid)
        body.append(c['tex'])
        key.append(f'\\keychapter{{{c["label"]}}}\n' + c['answers'])
    with open(os.path.join(OUT, 'body.tex'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(body) + '\n\\backmatterhead{Answer key}\n' + '\n'.join(key))
    print('wrote', os.path.join(OUT, 'body.tex'))

# ---------------------------------------------------------------- the whole book
WARNINGS = []
def warn(msg):
    WARNINGS.append(msg); print('warning:', msg, file=sys.stderr)

def build_settings():
    """TAG_ORDER, read from build.py so the two editions cannot drift apart (the parts are in numbering.py)."""
    import ast
    tree = ast.parse(open(os.path.join(BOOK, 'build.py'), encoding='utf-8').read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == 'TAG_ORDER':
            return ast.literal_eval(node.value)

def book_chapters():
    """Every chapter file, in reading order (numbering.ORDER)."""
    return [c['file'] for c in NUM.chapters]

def tex_text(s):
    """Plain text from the HTML into LaTeX: curly quotes, specials escaped."""
    return esc(curly(re.sub(r'\s+', ' ', html.unescape(s)).strip(), ''))

def title_pages():
    front = NUM.fill_xrefs(open(os.path.join(BOOK, 'src', 'front.html'), encoding='utf-8').read(), 'print', 'front')
    head = parse(front.split('<!--HOWTO-->')[0])
    tp = next(n for n in head.walk() if n.tag == 'header')
    title = inline(tp.find('h1'), Ctx()).strip(); sub = inline(tp.find('p', 'sub'), Ctx()).strip()
    # the author line of the title page and the copyright notice of the edition page come from front.html
    au = tp.find('p', 'author'); cp = tp.find('p', 'copyright')
    author = inline(au, Ctx()).strip() if au else 'Linux v7.2 \\textperiodcentered{} November 2026'
    notice = (f'by {author}\\par ' if au else '') + (inline(cp, Ctx()).strip() + '\\par ' if cp else '')
    out = [f'\\booktitlepage{{{title}}}{{{sub}}}{{{author}}}',
           f'\\editionpage{{{title}}}{{{notice}Written in November 2026 against the Linux v7.2 source; measurements on Linux 7.2.15 '
           'unless a chapter says otherwise.}{Set in Crimson Pro, Open Sans Condensed and Ubuntu Mono with LuaLaTeX.}',
           '\\booktoc']
    how = parse(front.split('<!--HOWTO-->')[1])
    sec = next(n for n in how.walk() if n.tag == 'section')
    h2 = sec.find('h2'); rest = Node('div'); rest.kids = [k for k in sec.kids if k is not h2]
    ctx = Ctx()
    out.append(f'\\backmatterhead{{{inline(h2, ctx).strip()}}}\n\n' + blocks(rest, ctx, {}))
    return '\n'.join(out) + '\n'

MONTHS = 'January February March April May June July August September October November December'.split()
def commits_appendix():
    """The lineage in commits: src/commits.json, one entry per row of Figure 0.3 (plus starred extras), two QR codes each."""
    import json
    rows = json.load(open(os.path.join(BOOK, 'src', 'commits.json'), encoding='utf-8'))
    intro = NUM.fill_xrefs(open(os.path.join(BOOK, 'src', 'commits-intro.html'), encoding='utf-8').read(), 'print', 'commits-intro')
    out = [f'\\appendixopen[The lineage in commits]{{A}}{{{tied_tex("The lineage in commits")}}}\n',blocks(parse('<div>' + intro + '</div>'), Ctx(), {})]
    for e in rows:
        codes = [(e['code'], e.get('codelabel', 'commit'))] + ([(e['thread'], 'thread')] if e.get('thread') else [])
        qrs = '\\hspace{3mm}'.join(f'\\commitqr{{{qr_tex(u)}}}{{{tex_text(lab)}}}' for u, lab in codes)
        star = '*' if e.get('extra') else ''
        head = f'{tex_text(e["year"])}\\quad {tex_text(e["version"])}\\quad {star}{tex_text(e["what"])}'
        if e.get('sha'):
            y, m, d = e['date'].split('-')
            meta = (f'\\commitsha{{\\code{{{e["sha"][:12]}}}\\enspace {tex_text(e["subject"])}}}'
                    f'\\commitmeta{{{tex_text(e["author"])}, {int(d)} {MONTHS[int(m) - 1]} {y}\\enspace\\textperiodcentered\\enspace '
                    f'+{e["added"]:,} \u2212{e["removed"]:,} lines in {e["files"]} file{"s" if e["files"] != 1 else ""}}}')
        else:
            meta = ''
        chs = ', '.join(f'\\hyperlink{{{cid}}}{{{n}}}' if cid in LINKABLE else tex_text(n) for cid, n in NUM.commit_chapters(e['chapters']))
        note = inline(parse('<p>' + NUM.fill_xrefs(e['note'], 'print', 'commits.json') + '</p>').find('p'), Ctx()).strip().replace('\\allowbreak{}', '')   # as tex_text set it
        out.append(f'\\commitentry{{{qrs}}}{{{head}}}{{ch.~{chs}}}{{{meta}}}{{{note}}}\n')
    return '\n'.join(out)

def back_matter(chs, tag_order):
    out = [commits_appendix(), f'\\appendixopen[Answer key]{{B}}{{{tied_tex("Answer key")}}}\n']
    for c in chs:
        if c['answers'].strip(): out.append(f'\\keychapter{{{c["label"]}}}\n' + c['answers'])
    out.append('\\backmatterhead{Glossary}\n')
    for c in chs:
        if c['glossary']:
            out.append(f'\\keychapter{{{c["label"]}}}\n' + dl_block(parse('<dl>' + c['glossary'] + '</dl>').find('dl'), Ctx(), 'wordlist'))
    seen, bytag = set(), {}
    for c in chs:                                      # de-duplicated by href, as build.py does
        for li in re.findall(r'<li>.*?</li>', c['refs'], re.S):
            href = re.search(r'href="([^"]+)"', li)
            k = href.group(1) if href else re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', li))).strip()
            if k in seen: continue
            seen.add(k)
            tag = re.search(r'<span class="tag (\w+)">', li).group(1)
            bytag.setdefault(tag, []).append(li)
    out.append('\\backmatterhead{References}\n')
    for tag in tag_order:
        if tag in bytag:
            out.append(f'\\keychapter{{{tag.title() if tag not in ("ISA", "HW") else tag}}}\n'
                       + list_block(parse('<ul>' + re.sub(r'<span class="tag \w+">[^<]*</span>\s*', '', ''.join(bytag[tag]))   # the heading names the layer
                                        + '</ul>').find('ul'), Ctx(), refs=True))
    out.append('\\printbookindex\n')
    return '\n'.join(out)

def book():
    os.makedirs(FIGOUT, exist_ok=True)
    TAG_ORDER = build_settings()
    ids = book_chapters()
    set_linkable(ids); IX.load_terms()
    chs = []
    for nc in NUM.chapters:
        c = chapter(nc['file']); c.update(kind=nc['kind'], num=nc['num'], pos=ids.index(nc['file'])); chs.append(c)
    PARTS = {ids.index(NUM.by_id[k]['file']): v for k, v in NUM.part_openers().items()}   # position of the opening chapter
    files = []
    def write(name, text):
        with open(os.path.join(OUT, name + '.tex'), 'w', encoding='utf-8') as f: f.write(text)
        files.append(name)
    write('front', title_pages())
    opened = set(); main_started = False
    for c in chs:
        epi = c['kind'] == 'epilogue'
        pre = '' if main_started else '\\mainmatter\n'; main_started = True
        starts = [k for k in PARTS if k <= c['pos']]
        pk = max(starts) if starts else None
        if pk is not None and pk not in opened and not epi:
            opened.add(pk); label, title, intro = PARTS[pk]
            pre += f'\\partpage[{tex_text(title)}]{{{tex_text(label)}}}{{{tied_tex(tex_text(title))}}}{{{tex_text(intro)}}}\n'
        if c['kind'] == 'prologue': num, kind = 'Prologue.', 'ebtop'
        elif c['kind'] == 'primer': num, kind = 'Primer.', 'ebchap'
        elif epi: num, kind = 'Epilogue.', 'ebtop'
        else: num, kind = f'{c["num"]}.', 'ebchap'
        write(c['id'], pre + f'\\chaptocinfo{{{num}}}{{{kind}}}\n' + c['tex'])
    write('back', back_matter(chs, TAG_ORDER))
    with open(os.path.join(OUT, 'book-body.tex'), 'w', encoding='utf-8') as f:
        f.write('\\frontmatter\n' + ''.join(f'\\input{{out/{n}.tex}}\n' for n in files))
    print('wrote', os.path.join(OUT, 'book-body.tex'), 'with', ', '.join(files))
    print(f'ties: {UNIT_TIES[0]} number-unit, version and reference pairs')
    IX.save()
    for p in NUM.problems: warn(p)
    for w in WARNINGS: print('warning:', w)

# ---------------------------------------------------------------- the index
# --book puts a marker \ixm{N} after each indexed word and writes what N stands for to out/index.json; LuaLaTeX writes
# "N page" to book.ixw at shipout; --index turns that into book.idx (makeindex syntax, page numbers linked through
# hyperref's \hyperpage, a term's defining page bold) and runs makeindex. Markers instead of \index{...} so that an
# entry is written the same way wherever it sits (in a macro argument or not), and so that pages are known before
# the entries are chosen: identical entries are capped per page and words on most pages keep only their main pages.
CMDS = ['bpftool', 'strace', 'perf', 'vng', 'clang', 'llvm-objdump', 'llvm-readelf', 'llvm-strip', 'readelf', 'objdump',
        'bpftrace', 'pahole', 'taskset', 'setpriv', 'gdb']
SRCDIRS = r'(?:kernel|include|arch|tools|net|lib|mm|fs|drivers|samples|security|scripts|Documentation)/'

def ix_quote(t):
    return re.sub(r'([@!|"])', r'"\1', t)

class Index:
    def __init__(self):
        self.on = False; self.chapter = ''; self.section = 0
        self.occ = []                    # marker -> [levels [[sort, display], ...], bold, chapter, kind]
        self.seen = set()
        self.terms = {}                  # lower-case term -> [sort, display]
        self.term_re = None
        self.helpers, self.kfuncs = set(), set()

    def load_terms(self):
        self.on = True
        found = {}
        def add(t, how):
            t = re.sub(r'\s+', ' ', html.unescape(t)).strip().strip('`')
            if not t or len(t) < 2 or len(t.split()) > 4 or not re.match(r'[A-Za-z]', t): return
            if not re.fullmatch(r"[\w .'/+-]+", t): return
            k = t.lower()
            if k.endswith('s') and k[:-1] in found: return
            if k + 's' in found: del found[k + 's']
            if k not in found or how == 'glossary': found[k] = t
        for c in NUM.chapters:
            raw = open(os.path.join(BOOK, 'src', c['file'] + '.html'), encoding='utf-8').read()
            parts = numbering.split_parts(raw)
            for d in re.findall(r'<dt>(.*?)</dt>', parts.get('GLOSSARY', ''), re.S): add(re.sub(r'<[^>]+>', '', d), 'glossary')
        try:
            notes = open(os.path.join(BOOK, 'NOTES.md'), encoding='utf-8').read()
            sec = re.split(r'^## Terms\s*$', notes, maxsplit=1, flags=re.M)[1].split('\n## ', 1)[0]
            for line in sec.splitlines():
                m = re.match(r'\|\s*`?([^`|]+?)`?\s*\|\s*(ch\d+|primer)\s*\|', line)
                if m: add(m.group(1), 'notes')
        except Exception as e:
            warn(f'index: no Terms table read from NOTES.md ({e})')
        for c in NUM.chapters:                 # a word in bold in a paragraph is being defined (NOTES.md)
            raw = open(os.path.join(BOOK, 'src', c['file'] + '.html'), encoding='utf-8').read()
            sec = re.sub(r'<div class="(?:readwith|lab|costs|recap|words|check|refs)".*?</div>', '', numbering.split_parts(raw)['CHAPTER'], flags=re.S)
            for para in re.findall(r'<p>(.*?)</p>', sec, re.S):
                for b in re.findall(r'<b>([^<]*)</b>', para):
                    if not b.rstrip().endswith(('.', ':')): add(b, 'bold')
        for k, t in found.items():
            disp = t if (t[:1].isupper() and (t[1:2].isupper() or t.split()[0][1:] != t.split()[0][1:].lower())) else t[0].lower() + t[1:]
            self.terms[k] = [k, esc(disp) if re.fullmatch(r"[\w .'+-]+", t) and '_' not in t else '\\code{' + esc(t) + '}']
        alts = []
        for k, (sort, disp) in sorted(self.terms.items(), key=lambda x: -len(x[0])):
            raw = found[k]
            pat = r'\s+'.join(re.escape(w) for w in raw.split()) + (r'(?:s|es)?' if raw[-1].isalpha() else '')
            alts.append(pat if any(ch.isupper() for ch in raw[1:]) else '(?i:' + pat + ')')
        alts += [re.escape(c) for c in CMDS if c not in self.terms]
        self.term_re = re.compile(r'(?<![\w/.-])(?:' + '|'.join(alts) + r')(?![\w/-]|\.\w)')
        vm = os.path.join(BOOK, 'program', 'vmlinux.h')
        if os.path.exists(vm):
            v = open(vm, encoding='utf-8', errors='replace').read()
            self.helpers = {'bpf_' + h for h in re.findall(r'\bBPF_FUNC_(\w+) = \d+', v)}
            self.kfuncs = set(re.findall(r'^extern [^;(]*?\b(\w+)\([^;]*\)\s*__weak __ksym;', v, re.M))
        else:
            warn('index: no program/vmlinux.h, so helpers and kfuncs are not told apart')

    def terms_in(self, t):
        return self.term_re.finditer(t) if self.term_re else []

    def lookup(self, word):
        k = re.sub(r'\s+', ' ', word).lower()
        for cand in (k, k[:-2] if k.endswith('es') else None, k[:-1] if k.endswith('s') else None):
            if cand and cand in self.terms: return self.terms[cand]
        return None

    def mark(self, levels, bold=False, kind='term'):
        key = (tuple(map(tuple, levels)), self.chapter, self.section)
        if not bold:
            if key in self.seen: return ''
            self.seen.add(key)
        self.occ.append([levels, bold, self.chapter, kind])
        return f'\\ixm{{{len(self.occ) - 1}}}'

    def mark_term(self, word):
        e = self.lookup(word)
        if e: return self.mark([e])
        if word in CMDS: return self.mark([[word, f'\\code{{{esc(word)}}}']], kind='command')
        return ''

    def defining(self, text):
        e = self.lookup(text)
        return self.mark([e], bold=True) if e else ''

    def function(self, name):
        disp = '\\code{' + code_esc(name + '()') + '}'; sort = name.lstrip('_').lower()
        out = self.mark([[sort, disp]], kind='code')
        if name in self.helpers: out += self.mark([['helpers', 'helpers'], [sort, disp]], kind='code')
        elif name in self.kfuncs: out += self.mark([['kfuncs', 'kfuncs'], [sort, disp]], kind='code')
        return out

    def mark_code(self, text):
        t = re.sub(r'\s+', ' ', text).strip()
        out = ''
        m = re.fullmatch(r'([A-Za-z_]\w*)\(\)', t)
        if m: return self.function(m.group(1))
        if re.fullmatch(r'bpf_\w+', t) and (t in self.helpers or t in self.kfuncs): return self.function(t)
        m = re.match(SRCDIRS + r'[\w./-]*\w', t)
        if m and m.end() >= len(t.split(':')[0]):
            path = m.group(0)
            return self.mark([[path.lower(), '\\code{' + code_esc(path) + '}']], kind='code')
        for kind, head in (('MAP', 'map types'), ('PROG', 'program types')):
            for x in re.findall(rf'\bBPF_{kind}_TYPE_\w+', t):
                d = '\\code{' + code_esc(x) + '}'
                out += self.mark([[x.lower(), d]], kind='code') + self.mark([[head, head], [x.lower(), d]], kind='code')
        if out: return out
        out = self.mark_commands(t)
        if out: return out
        e = self.terms.get(t.lower())
        return self.mark([e]) if e else ''

    def mark_commands(self, text):
        out = ''
        for line in text.splitlines():
            m = re.match(r'\s*(?:[$#]\s+)?(?:sudo\s+(?:-E\s+)?)?([\w.-]+)((?:\s+[\w.-]+){0,4})', line)
            if not m or m.group(1) not in CMDS: continue
            cmd = m.group(1)
            out += self.mark([[cmd, f'\\code{{{esc(cmd)}}}']], kind='command')
            if cmd == 'bpftool':
                words = [w for w in m.group(2).split() if not w.startswith('-')][:2]
                if len(words) == 2 and all(re.fullmatch(r'[a-z_]+', w) for w in words):
                    sub = ' '.join(words)
                    out += self.mark([['bpftool', '\\code{bpftool}'], [sub, f'\\code{{{esc(sub)}}}']], kind='command')
        return out

    def save(self):
        with open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8') as f:
            json.dump(dict(occ=self.occ, chapters=[c['id'] for c in NUM.chapters]), f)
        print(f'index: {len(self.occ)} markers, {len({tuple(map(tuple, o[0])) for o in self.occ})} entries')

IX = Index()

MAXPAGES = 12          # an entry on more pages keeps its defining pages and the first page in each chapter
def make_index(job='book'):
    """book.ixw (marker, page) and out/index.json -> book.idx -> makeindex -> book.ind"""
    data = json.load(open(os.path.join(OUT, 'index.json'), encoding='utf-8'))
    occ, nchap = data['occ'], len(data['chapters'])
    pages = {}                                           # entry -> {page: [bold, chapter]}
    for line in open(os.path.join(WORK, job + '.ixw'), encoding='utf-8'):
        n, page = line.split()
        if not page.isdigit(): continue
        levels, bold, chap, kind = occ[int(n)]
        key = tuple(tuple(x) for x in levels)
        p = pages.setdefault(key, {}).setdefault(int(page), [False, chap, kind])
        p[0] = p[0] or bold
    lines, dropped = [], 0
    for key, ps in pages.items():
        kind = next(iter(ps.values()))[2]
        bold = sorted(p for p, v in ps.items() if v[0])
        chaps = {v[1] for v in ps.values()}
        keep = sorted(ps)
        if kind == 'term' and len(key) == 1 and len(chaps) > nchap / 2:     # a word of most chapters: its main pages only
            keep = bold or keep[:3]
        elif len(keep) > MAXPAGES:
            first = {}
            for p in sorted(ps): first.setdefault(ps[p][1], p)
            keep = sorted(set(bold) | set(first.values()))
        dropped += len(ps) - len(keep)
        name = '!'.join(ix_quote(s) + '@' + ix_quote(d) for s, d in key)
        for p in keep:
            enc = 'hyperindexformat{\\textbf}' if ps[p][0] else 'hyperpage'
            lines.append(f'\\indexentry{{{name}|{enc}}}{{{p}}}')
    with open(os.path.join(WORK, job + '.idx'), 'w', encoding='utf-8') as f: f.write('\n'.join(lines) + '\n')
    r = subprocess.run(['makeindex', '-q', '-s', os.path.join(HERE, 'ebpfbook.ist'), '-o', job + '.ind', job + '.idx'], cwd=WORK, capture_output=True, text=True)
    log = open(os.path.join(WORK, job + '.ilg'), encoding='utf-8', errors='replace').read()
    m = re.search(r'(\d+) entries accepted, (\d+) rejected', log)
    tops = {k[0] for k in pages}
    print(f'index: {len(pages)} entries ({len(tops)} top level), {len(lines)} page references after dropping {dropped}; '
          f'makeindex {m.group(0) if m else "?"}{"; " + r.stderr.strip() if r.returncode else ""}')
    if 'rejected' in log and m and m.group(2) != '0': print(log[-1500:])

# figures are drawn with Literata and JetBrains Mono (older ones) or Open Sans Condensed and Ubuntu Mono: hand rsvg-convert a font configuration that knows them
def configure(work=None):
    """Generated files go to tex/ (the default) or to a private directory: work/out/ for the LaTeX and the figures,
    work/out/fc for the font configuration, work/book.tex and work/sample.tex as masters; the style, the makeindex
    style, the fonts and the checks are linked from tex/, so LuaLaTeX runs in work/ exactly as it does in tex/."""
    global WORK, OUT, FIGOUT, FIGENV
    if work:
        WORK = os.path.abspath(work); OUT = os.path.join(WORK, 'out'); FIGOUT = os.path.join(OUT, 'figs')
        os.makedirs(FIGOUT, exist_ok=True)
        for name in ['ebpfbook.sty', 'ebpfbook.ist', 'fonts', 'checks']:
            link = os.path.join(WORK, name)
            if not os.path.lexists(link): os.symlink(os.path.join(HERE, name), link)
        for master in ['book.tex', 'sample.tex']:
            shutil.copy(os.path.join(HERE, master), os.path.join(WORK, master))
    FCDIR = os.path.join(OUT, 'fc'); os.makedirs(os.path.join(FCDIR, 'fonts'), exist_ok=True)
    for f in ['Literata10-Regular', 'Literata10-SemiBold', 'Literata10-RegularItalic', 'JetBrainsMono-Regular', 'JetBrainsMono-Medium', 'JetBrainsMono-Bold',
              'UbuntuMono-Regular', 'UbuntuMono-Bold', 'UbuntuMono-Italic']:   # the redrawn figures use Ubuntu Mono (Open Sans Condensed is system-wide)
        dst = os.path.join(FCDIR, 'fonts', f + '.ttf')
        if not os.path.exists(dst): shutil.copy(os.path.join(HERE, 'fonts', f + '.ttf'), dst)
    open(os.path.join(FCDIR, 'fonts.conf'), 'w').write(
        '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>'
        f'<include ignore_missing="yes">/etc/fonts/fonts.conf</include><dir>{FCDIR}/fonts</dir><cachedir>{FCDIR}/cache</cachedir></fontconfig>')
    FIGENV = dict(os.environ, FONTCONFIG_FILE=os.path.join(FCDIR, 'fonts.conf'))

if __name__ == '__main__':
    args = sys.argv[1:]
    work = None
    if '--out' in args:
        i = args.index('--out'); work = args[i + 1]; del args[i:i + 2]
    configure(work)
    if args == ['--book']: book()
    elif args[:1] == ['--index']: make_index(args[1] if len(args) > 1 else 'book')
    else: main(args or ['ch04'])
