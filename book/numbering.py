"""numbering.py: every chapter, figure, question and lab number in the book, computed at build time.

build.py (the screen edition) and tex/html2tex.py (the print edition) both import this module, so the two editions
cannot disagree. No number is typed into src/*.html; the sources carry handles and empty slots instead.

ORDER
  ORDER below lists the chapter files in reading order (every src/*.html with a <section class="chapter"> must be in
  it, and nothing else; src/old/ is not read). A merge replaces its old files with its new one in a single idempotent
  step that is safe while another agent does the same for other files (it locks numbering.py):
      python3 -I tools/order.py merge maps ch09 ch15 ch16
  puts maps where the first of ch09, ch15, ch16 stood, drops the others, and renames any PARTS key that is now one of
  the new chapter's aliases (PARTS keys resolve through aliases anyway, so a stale key still works). Run it after the
  new file is in src/ and the old ones are in src/old/; running it again changes nothing.
      python3 -I tools/order.py move numbers --after walk        (or --before walk)
  puts a file already in ORDER directly after (or before) another, moving nothing else; it refuses if either is
  missing from ORDER, locks numbering.py as merge does, and a second run changes nothing.
  A <section class="chapter"> may say data-kind="prologue",
  data-kind="primer" or data-kind="epilogue": those are not numbered (the primer is "P"); every other chapter takes the
  next number, 1, 2, 3 ... Figures, questions and labs are numbered within their chapter: 0.n in the prologue,
  P.n in the primer, E.n in the epilogue.

HANDLES
  An id is an opaque handle. It never changes, even when the thing moves to another chapter: fig-4-2 may one day be
  the third figure of chapter 9 and is still fig-4-2.
    <section id="ch4" class="chapter">     a chapter; its <p class="eyebrow"></p> is filled "Chapter 4"
    <section id="maps" class="chapter" data-aliases="ch9 ch15 ch16">
                                           a merged chapter: links to #ch9, #ch15 and #ch16 resolve to it (the href is
                                           rewritten to #maps), as do the Terms table in NOTES.md and src/commits.json.
                                           A split chapter is aliased by the chapter that takes its main part.
    <h3 id="sec-locks">                    a section a reference can name (ids by hand, only where referenced)
    <figure class="fig" id="fig-4-2">      a figure, numbered by order of appearance in its chapter; the
                                           <b class="fn"></b> of its caption is filled "Figure 4.2" (print "Figure 4-2")
    <li id="q4-1">                         a question: those in the chapter's "Check yourself" box come first, in
                                           order, then every other question of the chapter in order of appearance;
                                           the build gives the <li> data-n="4.1", which both editions print as its label
    <div class="lab" id="lab4-1">          a lab, numbered by order of appearance: "Lab 4.1"
    <div class="ans" data-for="q4-1"><p class="q"></p>     answer-key label, filled "4.1"
    <div class="sol" data-for="lab4-1"><p class="q"></p>   filled "Lab 4.1"

CROSS-REFERENCES
  A reference is an empty link to a handle; the build writes the label into it (anything typed inside is replaced).
    <a class="xref" href="#fig-4-2"></a>       Figure 4.2     print: Figure 4-2
    <a class="xref" href="#ch4"></a>           chapter 4      the prologue / the primer / the epilogue
    <a class="xref cap" href="#ch4"></a>       Chapter 4      cap: a capital, as at the start of a sentence
    <a class="xref" href="#q4-3"></a>          question 4.3   (cap: Question 4.3)
    <a class="xref" href="#lab4-1"></a>        Lab 4.1
    <a class="xref num" href="#fig-4-2"></a>   4.2            num: the number alone, for "Figures 4.2 and 4.3" or
                                                              "chapters 7 and 16" (an unnumbered chapter is an error)
    <a class="xref sec" href="#sec-locks"></a> the section "Who waits when several CPUs count"
                                               print: the same, then "on page 136" (O'Reilly: see "Title" on page 136);
                                               cap: The section ...
  A chapter-level reference inside the chapter it names is flagged by audit.py (after a merge it must become a section
  reference or plain wording); "the answer key under <chapter>" is the one exception.
  A possessive stays outside the link: <a class="xref" href="#ch5"></a>'s.
  A link to an id that does not exist is filled "??id" and reported; audit.py flags it.
  src/commits.json lists chapters as ids ("ch7"); an entry that is not an id (a chapter not yet written) prints as typed.
  A one-off script (since removed) turned the typed numbers of the first draft into this markup.
"""
import glob, html, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'src')

# the chapter files, in reading order (file names in src/ without .html)
ORDER = ['ch00', 'primer', 'machine', 'object', 'load', 'walk', 'reject', 'numbers', 'jit', 'hooks', 'calls',
         'maps', 'memory', 'schedext', 'capstone', 'ch17', 'proof', 'agni', 'prevail', 'epilogue']

# the part that opens at a chapter: chapter id -> (label, title, two-sentence introduction)
PARTS = {
    'primer': ('Part I', 'The program and its machine',
        'We follow one small program, the write counter, from the instruction set it is written for, through the compiler '
        'and the object file that carry it, into the kernel, where the bpf() system call creates its maps and loads it.'),
    'walk': ('Part II', 'The verifier',
        'Before the counter runs, the kernel proves that it is safe. We watch the verifier walk every path of the program, '
        'read the log it leaves when it refuses one, follow that log line into verifier.c, and see how it tracks the values '
        'a register can hold.'),
    'jit': ('Part III', 'Running',
        'A program that passed is compiled to machine code, attached to an event and run each time the event fires. We follow '
        'the JIT, the hooks, the helpers and kfuncs the program calls, and the maps where its data lives, with what each one costs.'),
    'memory': ('Part IV', 'Extending the kernel',
        'Until now the kernel sized every map in advance and called each program to observe or decide one thing. We give '
        'programs memory they allocate and link themselves, let a set of programs act as the CPU scheduler, and add a data '
        'structure to the kernel twice, first on an arena and then as a map type of its own.'),
    'ch17': ('Part V', 'Proving the verifier',
         'The verifier is a static analyser, and a static analyser can be proved sound or shown to be wrong. We review the ideas '
         'and tools a proof needs, carry out one small proof by hand and with a solver, and then read two papers that apply them to eBPF.'),
}

SEP = {'screen': '.', 'print': '-'}          # figure numbers: O'Reilly prints Figure 4-2
PARTS_RE = r'<!--(CHAPTER|ANSWERS|GLOSSARY|REFS)-->(.*?)(?=<!--(?:CHAPTER|ANSWERS|GLOSSARY|REFS)-->|\Z)'
XREF = re.compile(r'<a class="xref((?: [\w-]+)*)" href="#([\w-]+)">(.*?)</a>', re.S)


def split_parts(raw):
    return dict(re.findall(PARTS_RE, raw, re.S))


class Numbers:
    def __init__(self, src=SRC):
        self.src = src
        self.chapters = []          # in reading order
        self.targets = {}           # id -> (type, chapter, n)
        self.titles = {}            # section id -> heading text
        self.problems = []
        self.aliases = {}           # old chapter id -> the id of the chapter that now declares it
        there = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(src, '*.html'))
                 if re.search(r'<section id="[\w-]+" class="chapter"', open(p, encoding='utf-8').read())}
        if there - set(ORDER) or set(ORDER) - there:
            raise SystemExit('numbering.ORDER and src/ disagree: '
                             + '; '.join(x for x in [f'chapter files not in ORDER: {", ".join(sorted(there - set(ORDER)))}' if there - set(ORDER) else '',
                                                     f'in ORDER but no src/NAME.html: {", ".join(sorted(set(ORDER) - there))}' if set(ORDER) - there else ''] if x)
                             + ' (see "ORDER" at the top of numbering.py)')
        if len(set(ORDER)) != len(ORDER):
            raise SystemExit(f'numbering.ORDER names a file twice: {sorted({x for x in ORDER if ORDER.count(x) > 1})}')
        n = 0
        for stem in ORDER:
            raw = open(os.path.join(src, stem + '.html'), encoding='utf-8').read()
            sec = split_parts(raw)['CHAPTER']
            m = re.search(r'<section id="([\w-]+)" class="chapter"([^>]*)>', sec)
            cid = m.group(1)
            k = re.search(r'data-kind="(\w+)"', m.group(2))
            kind = k.group(1) if k else 'chapter'
            if kind == 'chapter':
                n += 1; num = prefix = str(n); name = f'Chapter {n}'
            elif kind in ('prologue', 'primer', 'epilogue'):
                num, prefix = {'prologue': ('', '0'), 'primer': ('P', 'P'), 'epilogue': ('', 'E')}[kind]
                name = kind.title()
            else:
                raise SystemExit(f'{stem}: unknown data-kind {kind!r}')
            al = re.search(r'data-aliases="([^"]*)"', m.group(2))
            c = dict(file=stem, id=cid, kind=kind, num=num, prefix=prefix, name=name, aliases=al.group(1).split() if al else [])
            self.chapters.append(c)
            self.add(cid, 'chapter', c, None)
            for i, (hid, title) in enumerate(re.findall(r'<h[34] id="([\w-]+)"[^>]*>(.*?)</h[34]>', sec, re.S), 1):
                self.add(hid, 'section', c, i)
                self.titles[hid] = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', title))).strip()
            for i, fid in enumerate(re.findall(r'<figure class="fig[^"]*" id="([\w-]+)"', sec), 1):
                self.add(fid, 'figure', c, i)
            checks = ''.join(re.findall(r'<div class="check">.*?</div>', sec, re.S))
            first = re.findall(r'<li id="([\w-]+)"', checks)
            rest = [q for q in re.findall(r'<li id="([\w-]+)"', sec) if q not in first]
            for i, qid in enumerate(first + rest, 1):
                self.add(qid, 'question', c, i)
            for i, lid in enumerate(re.findall(r'<div class="lab" id="([\w-]+)"', sec), 1):
                self.add(lid, 'lab', c, i)
        for c in self.chapters:
            for a in c['aliases']:
                if a in self.targets or a in self.aliases:
                    raise SystemExit(f'alias {a} of {c["id"]} ({c["file"]}) is already '
                                     + (f'an id in {self.targets[a][1]["file"]}' if a in self.targets else f'an alias of {self.aliases[a]}'))
                self.aliases[a] = c['id']
        self.by_id = {c['id']: c for c in self.chapters}

    def resolve(self, tid):
        """An id, or the chapter id it is an alias of; None if neither."""
        if tid in self.targets: return tid
        return self.aliases.get(tid)

    def add(self, tid, typ, c, n):
        if tid in self.targets: raise SystemExit(f'id {tid} is used twice ({self.targets[tid][1]["file"]}, {c["file"]})')
        self.targets[tid] = (typ, c, n)

    # ------------------------------------------------------------ labels
    def number(self, tid, edition='screen'):
        """The bare number: '4' for a chapter, '4.2' for a figure (print '4-2'), '4.1' for a question or lab."""
        typ, c, n = self.targets[tid]
        if typ == 'chapter':
            if not c['num']: raise ValueError(f'{tid} ({c["name"]}) has no number')
            return c['num']
        return f'{c["prefix"]}{SEP[edition] if typ == "figure" else "."}{n}'

    def label(self, tid, mods=(), edition='screen'):
        """The text of a cross-reference to tid; mods: 'cap', 'num'."""
        typ, c, n = self.targets[tid]
        if typ == 'section':
            s = f'the section "{self.titles[tid]}"'
            return s[0].upper() + s[1:] if 'cap' in mods else s
        if 'num' in mods: s = self.number(tid, edition)
        elif typ == 'chapter': s = f'chapter {c["num"]}' if c['kind'] == 'chapter' else f'the {c["kind"]}'
        elif typ == 'figure': s = 'Figure ' + self.number(tid, edition)
        elif typ == 'question': s = 'question ' + self.number(tid, edition)
        else: s = 'Lab ' + self.number(tid, edition)
        return s[0].upper() + s[1:] if 'cap' in mods else s

    def key_label(self, tid):
        """The label of an answer or a solution in the key: '4.1', 'Lab 4.1'."""
        typ = self.targets[tid][0]
        return ('Lab ' if typ == 'lab' else '') + self.number(tid)

    def chapter_of(self, tid):
        return self.targets[tid][1]

    # ------------------------------------------------------------ filling the sources
    def fill_xrefs(self, text, edition='screen', where=''):
        def one(m):
            mods, tid = m.group(1).split(), self.resolve(m.group(2)) or m.group(2)
            if tid not in self.targets:
                self.problems.append(f'{where}: xref to missing id #{tid}')
                print(f'warning: {where}: xref to missing id #{tid}', file=sys.stderr)
                return f'<a class="xref{m.group(1)}" href="#{tid}">??{tid}</a>'
            try:
                lab = self.label(tid, mods, edition)
            except ValueError as e:
                self.problems.append(f'{where}: {e}'); lab = f'??{tid}'
            return f'<a class="xref{m.group(1)}" href="#{tid}">{html.escape(lab, quote=False)}</a>'
        return XREF.sub(one, text)

    def fill_chapter(self, raw, edition='screen', stem=''):
        """A chapter file with its eyebrow, figure numbers, answer-key labels and cross-references filled in."""
        c = next(c for c in self.chapters if c['file'] == stem) if stem else None
        if c is not None:
            raw = re.sub(r'(<p class="eyebrow">)[^<]*(</p>)', lambda m: m.group(1) + c['name'] + m.group(2), raw, count=1)
        def fig(m):
            tid = m.group(1)
            lab = 'Figure ' + self.number(tid, edition) if tid in self.targets else '??' + tid
            return re.sub(r'(<b class="fn">)[^<]*(</b>)', lambda b: b.group(1) + lab + b.group(2), m.group(0), count=1)
        raw = re.sub(r'<figure class="fig[^"]*" id="([\w-]+)".*?</figure>', fig, raw, flags=re.S)
        def key(m):
            tid = m.group(2)
            lab = self.key_label(tid) if tid in self.targets else '??' + tid
            return f'{m.group(1)}{lab}</p>'
        raw = re.sub(r'(<div class="(?:ans|sol)" data-for="([\w-]+)"><p class="q">)[^<]*</p>', key, raw)
        def qn(m):                                     # each question carries its number: data-n="4.1"
            tid = m.group(1)
            if tid not in self.targets or self.targets[tid][0] != 'question': return m.group(0)
            return f'<li id="{tid}" data-n="{self.number(tid)}">'
        raw = re.sub(r'<li id="([\w-]+)"(?: data-n="[^"]*")?>', qn, raw)
        return self.fill_xrefs(raw, edition, stem)

    def commit_chapters(self, items):
        """src/commits.json 'chapters': ids become numbers (the prologue is 0, as Figure 0.3 has it); anything else stays."""
        out = []
        for x in items:
            r = self.resolve(x)
            if r and self.targets[r][0] == 'chapter':
                if any(cid == r for cid, _ in out): continue      # two old chapters merged into one
                c = self.targets[r][1]
                out.append((r, c['num'] or c['prefix']))
            else:
                out.append((None, x))
        return out

    # ------------------------------------------------------------ parts
    def part_openers(self):
        """chapter id -> PARTS entry, for the first chapter of each part (the epilogue opens none)."""
        out = {}
        for cid, p in PARTS.items():
            r = self.resolve(cid)
            if r: out[r] = p
        return out


_cache = {}
def get(src=SRC):
    if src not in _cache: _cache[src] = Numbers(src)
    return _cache[src]
