You are writing one chapter of a printed technical book, "eBPF for Systems Engineers" (/home/wazir/workspace/repos/ebpf-lab/book), during a restructure the reader approved. The book used to take two passes over the life of one eBPF program (Part I, then Part II "inside the source"), in chapters of 8-10 pages. It is being rebuilt as one chapter per stage, in the order the program meets them, each 15-25 pages, in the O'Reilly format. Your job is the new chapter named under "Your chapter", built from the old chapters listed there. Another agent is building a different chapter at the same time from different old files; touch only yours.

## Read first
- book/NOTES.md: "Plan v4" (the new outline, the chapter arc, the merge rules: binding), "Voice", "Systems lens", "Figure rules", "Terms".
- ~/workspace/learning/agent-directory/BOOK_STYLE_LEARNING.md section 4 (voice, numbers). Its 600-900-word prose cap no longer applies: a merged chapter has about 2,500-4,000 words of prose.
- book/numbering.py, the comment block at the top: chapter, figure, question and lab numbers are computed; ids are opaque handles; every reference is an empty <a class="xref" ...></a>; chapters absorbed by a merge are named in data-aliases; section references (xref sec); how to update ORDER and PARTS with tools/order.py; how to build the print edition into a private directory with --out (also documented in tex/book.tex).
- The old chapters you absorb, in full, and their printed pages in book/ebpf-book-print.pdf (look at them: pdftoppm at a modest resolution).
- Two neighbours for the hand-offs: the new chapter before yours and after yours in Plan v4 (read the old chapters they come from if they are not merged yet).
- Finished chapters to see what is expected: src/load.html and src/hooks.html (merged from several old chapters), src/walk.html (grown from one old chapter: measured sections, limits table, VM lab), src/reject.html: their "When it goes wrong" tables, costs boxes and section references.

## What to write
1. One new file src/<id>.html with the four parts (<!--CHAPTER-->, <!--ANSWERS-->, <!--GLOSSARY-->, <!--REFS-->), its <section id="<id>" class="chapter" data-aliases="..."> naming every old chapter id whose main part it absorbs.
2. The arc of Plan v4, in this order: the opener (title, lede, a ribbon merged from the old ribbons using the canonical labels under NOTES' lineage table, "In this chapter", a Spine line that hands off from the previous chapter in the NEW order); then what you see (the counter, observed with a tool) → how it works → inside the v7.2 source → what it costs (one costs box: CPU, Memory, Switches, Locking, then a decision rule) → when it goes wrong (a table: symptom | cause | the command that confirms it, built from the old chapters' symptom questions, labs and findings) → the labs → Check yourself → Recap → New words → Go deeper (merged references and commits).
3. A merge is not concatenation. Rewrite the seams so the chapter reads as one argument; remove what the old Part I and Part II chapters both said; keep every measured number, figure, listing, lab and question (drop only exact duplicates), keep their ids, and keep the measured provenance (kernel, VM, date) beside each number. New prose only where a seam, the "when it goes wrong" section or a hand-off needs it; every new factual claim checked against the v7.2 source (/tmp/linux-src-iTa3/linux, sparse; add paths with `git -C ... sparse-checkout add <path>`, only add) or a real run, never from memory.
4. References: other chapters stay xrefs (aliases resolve them); a reference that now points into your own chapter becomes a section reference (<a class="xref sec" href="#sec-..."></a>, with an id on that heading) or plain words (audit flags self-references). Terms: definitions must still come before first use across the new order (audit enforces it); fix by moving a definition, never by dropping a term. NOTES' "## Terms" table names the defining chapter by its section id (aliases resolve): append rows for new terms, and for a term whose definition you move into your chapter change that row's id to yours; nothing else in NOTES.
5. Old files: move each old file you fully absorb to src/old/ (never delete). An old file another merge will finish keeps the rest and gets data-remnant on its <section>. Update ORDER and PARTS in numbering.py with tools/order.py as your last step.
6. Figures keep their SVGs and scripts; if the merged text needs a figure changed, follow "Figure rules" and look at it at print size. Code listings at most 80 characters a line. The answer key lists answers in the order of their printed numbers (audit checks it).

## Checks before you report
- cd book && python3 -I build.py /tmp/<id>.html && python3 -I audit.py /tmp/<id>.html: RESULT clean. (While another agent has a new chapter file in src/ that is not yet in ORDER, the build stops with "numbering.ORDER and src/ disagree"; then build from a snapshot: copy book/ to a fresh /tmp directory without that file and without tex/out, and build there.)
- Build the print edition into a private directory (--out /tmp/tex-<id>), never into book/tex/out; no LaTeX errors; checks/strand.py and checks/boxes.py clean on your chapter's pages; look at every page of your chapter.
- Report your chapter's page count and prose word count.

## Rules
- Write only: src/<id>.html, the old files of your scope (move to src/old/, or cut and mark data-remnant), ORDER and PARTS in numbering.py (through tools/order.py), rows in NOTES' Terms table as point 4 says, figure scripts and outputs for figures you change or add, lab files under book/labs/. In other chapters' files you may change only the href of a reference that points at material you moved, and the term markup your scope allows. Never edit build.py, audit.py or tex/.
- Do not commit. Do not install packages. Do not spawn subagents. Root steps only in the VM (vng; see NOTES "Resume here"), never sudo.
- Limits: 50 requests a minute and 500,000 input tokens a minute for the organisation, and another agent is running: keep tool output small.

## Report back (short)
Pages and prose words; the section outline; what you cut as duplicate (one line each); the "when it goes wrong" table's rows; any claim you could not verify; anything outside your files that needs a change.

## Your chapter
{{SCOPE}}
