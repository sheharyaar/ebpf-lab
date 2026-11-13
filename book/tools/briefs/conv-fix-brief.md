You are fixing five small faults in the LaTeX print back end of a technical book, "eBPF for Systems Engineers" (/home/wazir/workspace/repos/eBPF-playground/book). The HTML in book/src/ is the source; tex/html2tex.py converts it, tex/ebpfbook.sty sets it in the O'Reilly format, tex/book.tex is the master. The main session will audit your work page by page, so report honestly what is not right yet.

## Read first
- tex/html2tex.py (a small DOM, one function per block kind), tex/ebpfbook.sty, tex/book.tex (its header comment: how to build the whole book or one chapter into a private directory with --out).
- tools/order.py and the comment block at the top of numbering.py (ORDER, PARTS, aliases).

## The faults
1. A listing longer than 24 lines inside a <figure> is set as the breakable `codeboxlong` inside the minipage that `fitbody` builds for the figure. The lines then come out unevenly spaced: 18.4 pt between some lines instead of 9.9 every few lines. A figure cannot break across pages anyway. Make every listing inside a figure set with even line spacing whatever its length; a figure taller than the text block must still fit (the existing rule for tall figures scales them) or be reported by html2tex as a warning naming the figure id. Listings outside figures keep today's rule (breakable over 24 lines). Test with a figure holding a 30-line and a 45-line listing (write a throwaway chapter file under /tmp, never in src/), and with src/object.html, whose Figure 2-1 (fig-object-c) was trimmed to 25 lines to dodge this fault.
2. Titles must not end with a lone short word on a line of its own. Tie the last two words with a non-breaking space when html2tex writes a chapter title, a part title, an appendix title, an h3 or h4 heading, and their contents and bookmark entries (bookmarks take plain text: use a plain space there). Do not tie when the last word is longer than about 12 characters, and never tie inside code. src/reject.html's title carries a hand-written &nbsp; for this; leave it, and make sure a title that already has one converts the same.
3. The chapter-opener ribbon (the lineage timeline drawn with TikZ across the text width) gives a 0.5 pt overfull hbox in nine chapters. Make it fit the text width exactly, without changing how it looks.
4. A field note (`<aside class="field">` or the block html2tex sets as a field note; find it in html2tex.py around the field-note code, near line 515) may hold several quotes, each with its own `<cite>`; html2tex prints only the first `<cite>`, so a second quote is attributed to the first source. Print each quote with its own attribution, as the screen edition does. Find every chapter that has a field note with more than one `<cite>` (src/*.html) and look at each in print.
5. tools/order.py has `merge NEW OLD...` and `show`. Add `move NEW --after STEM` (and `--before STEM`): put NEW, already in ORDER, directly after (or before) STEM; idempotent; same file locking as merge; refuse if either stem is missing. Document it in the module docstring and in numbering.py's comment block where order.py is described (that comment only).

## Checks before you report
- Whole book into a private directory (`--out /tmp/tex-fix`; never into book/tex/out while you work): no LaTeX errors, no undefined references, contents settled; checks/strand.py and checks/boxes.py clean; overfull hboxes not worse than before your change (count them before and after).
- `cd book/tex && python3 -I html2tex.py walk --out /tmp/tex-fix1 && cd /tmp/tex-fix1 && lualatex sample.tex` still works for one chapter (use any chapter id in ORDER).
- Look at the pages your changes touch: every figure with a listing over 24 lines, every chapter opener, the contents pages, and three part pages. Count the titles and headings that now break before their last two words, before and after.
- `python3 -I tools/order.py move X --after Y` on a copy of numbering.py (set the path through an environment variable or a flag you add for testing; never move a chapter in the real ORDER).

## Rules
- Write only tex/html2tex.py, tex/ebpfbook.sty, tex/book.tex, tex/checks/*, tools/order.py and numbering.py's comment block. Never edit src/, figs/, NOTES.md, build.py or audit.py.
- Two agents are writing chapters at the same time and build the print edition from tex/html2tex.py into their own directories. Edit a copy of each file you change, test the copy, and only then put it in place with one `mv`, so that no build of theirs ever reads a half-edited converter.
- Do not commit. Do not install packages. Do not spawn subagents. The organisation's limits are 50 requests a minute and 500,000 input tokens a minute and other agents are running: keep tool output small (pipe long logs through grep/tail; never print a whole .log or .tex).

## Report back (short)
Files changed; for each fault what you changed and the evidence it works (pages to look at); before and after counts (overfull boxes, titles broken before their last word); anything left.
