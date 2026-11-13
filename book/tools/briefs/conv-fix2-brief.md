You are fixing four small faults in the LaTeX print back end of a technical book, "eBPF for Systems Engineers" (/home/wazir/workspace/repos/ebpf-lab/book), before its final print build. The HTML in book/src/ is the source; tex/html2tex.py converts it, tex/ebpfbook.sty sets it in the O'Reilly format, tex/book.tex is the master. The book is complete: prologue, primer, chapters 1-17 in five parts, epilogue, appendices, index (numbering.py's ORDER; tools/order.py show). The main session will audit your work page by page, so report honestly what is not right yet.

## Read first
- tex/html2tex.py (a small DOM, one function per block kind), tex/ebpfbook.sty, tex/book.tex (its header comment: how to build the whole book or one chapter into a private directory with --out), tex/checks/strand.py and tex/checks/boxes.py.

## The faults
1. A lab box ("Try it", `class="lab"` in src/*.html) can start at the foot of a page with only its title and its meta line (time, kind, needs) there, and its Task on the next page. Seen in chapter 9 (src/calls.html, Lab 13.2, "Predict which calls the kernel keeps") and chapter 12 (src/schedext.html, "Take the CPU away from a scheduler"). Keep a lab's title, meta line and at least the first two lines of its Task together on one page, without changing how a lab looks. Extend tex/checks/strand.py (or add a check beside it) so that it reports a lab title stranded this way, and run it over the whole book before and after.
2. An inline code string in prose can run into the margin: the one known case is a 6 pt overfull line in chapter 3 (src/load.html), the libbpf message "failed to determine tracepoint 'syscalls/sys_enter_write' perf event ID: -EACCES" set in inline code. Let long inline code break at sensible points (after /, _, a comma, a colon or an opening parenthesis, never by hyphenating inside an identifier), in a way that applies to every chapter, not only this string. Count overfull boxes over the whole book before and after.
3. In the "New words in this chapter" list (the `wordlist` environment, style=multiline, in tex/ebpfbook.sty), a term that wraps onto two lines while its definition takes one line overlaps the next entry. Fix the environment so that an entry is always as tall as the taller of its term and its definition. Find every chapter whose New-words list has a term that wraps (src/*.html, the GLOSSARY part, or the converted .tex), and look at each in print.
4. The chapter-opener ribbon (the lineage timeline across the text width) hyphenates its labels: "6.9 arena, token" prints as "to-ken". Labels in the ribbon must never hyphenate; if a label then does not fit, report which chapter and label rather than shrinking type.

## Checks before you report
- Whole book into a private directory (`--out /tmp/tex-fix2`; never into book/tex/out), by the commands in tex/book.tex's header (lualatex, the --index pass, lualatex until the contents settle): no LaTeX errors, no undefined references; strand.py (with your lab check) and boxes.py clean; overfull hboxes not more than before (count before and after; the known 6 pt one should be gone).
- One chapter still builds alone: `python3 -I tex/html2tex.py calls --out /tmp/tex-fix2-one` then lualatex sample.tex twice in that directory.
- Look at the pages your changes touch: the two labs named above and every other lab that now moves, the line in chapter 3, every New-words list with a wrapping term, and every ribbon that has "arena, token" or another label that used to hyphenate. Report the PDF page numbers so they can be checked.
- Leave the final whole-book PDF in /tmp/tex-fix2/book.pdf; do not copy it into the book folder (the main session will, after its audit).

## Rules
- Write only tex/html2tex.py, tex/ebpfbook.sty, tex/book.tex and tex/checks/*. Never edit src/, figs/, NOTES.md, numbering.py, build.py or audit.py. If a fault can only be fixed in the HTML, stop and report which file and what change.
- Edit a copy of each file you change, test the copy, and only then put it in place with one mv, so that no build ever reads a half-edited converter.
- Do not commit. Do not install packages. Do not spawn subagents. The organisation's limits are 50 requests a minute and 500,000 input tokens a minute: keep tool output small (pipe long logs through grep/tail; never print a whole .log or .tex).

## Report back (short)
Files changed; for each fault what you changed and the evidence it works (PDF pages to look at); before and after counts (overfull boxes, stranded labs, hyphenated ribbon labels, overlapping word-list entries); the final page count; anything left.
