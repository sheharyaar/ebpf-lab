# eBPF for Systems Engineers

A book about eBPF on Linux, written for systems engineers. It follows one small
program, a counter of `write()` calls, through every stage of its life: the
instruction set, the compiler and BTF, the `bpf()` load path, the verifier, the
JIT, the hook it attaches to, the helpers and maps it uses. It then goes into the
kernel's own source and ends by asking whether the verifier itself can be proved
correct.

Every chapter shows the mechanism at work, explains it with figures, reads it in
the Linux v7.2 source, says what it costs (measured, with a decision rule) and
how it goes wrong, and ends with labs and questions. The answers are at the back.

**Read it:** [`book/ebpf-book-print.pdf`](book/ebpf-book-print.pdf) (500 pages,
print layout) or [`book/ebpf-book.html`](book/ebpf-book.html) (the same book
paged on screen; open it in a browser with network access, since it loads
Paged.js and its fonts from a CDN).

## Why this repository exists

The repository began as an eBPF playground of small libbpf exercises. Those were
dropped for something deeper: a book that goes from the instruction set to the
verifier's source, with the goal of being able to read, test and eventually
change the kernel's BPF code. The book is the record of that learning, and its
program, labs and kernel patches live here with it.

## Contents

- **Prologue**: 1993, a filter inside the kernel. **Primer**: registers and instructions.
- **Part I, The program and its machine**: the instruction set and calls; from C
  to an object with clang, BTF and CO-RE; the load path and who holds what.
- **Part II, The verifier**: the walk over every path; reading a rejection from
  log line to source line; how the verifier tracks numbers.
- **Part III, Running**: the JIT and tail calls; hooks and attaching; helpers and
  kfuncs; maps.
- **Part IV, Extending the kernel**: memory you manage (allocated objects, kptrs,
  lists, trees, arenas); `sched_ext`; a capstone that builds a count-min sketch
  twice, once in an arena and once as a new kernel map type.
- **Part V, Proving the verifier**: a formal-methods refresher; one proof by hand
  and one bug found by the Z3 solver; readings of the Agni and PREVAIL papers.
- **Epilogue**, appendices (the lineage in commits, the answer key), glossary,
  references and index.

## Layout

| Path | What it is |
|---|---|
| `book/ebpf-book-print.pdf`, `book/ebpf-book.html` | The book, print and screen editions |
| `book/src/` | The sources: one HTML file per chapter, plus the front matter and the lineage data |
| `book/figs/` | One figure script per chapter and the SVG figures they produce |
| `book/labs/` | Lab code, the scripts that run labs in a VM, and the capstone's kernel patches (never submitted upstream) |
| `book/program/` | The write counter the book follows |
| `book/numbering.py`, `build.py`, `audit.py`, `book.css` | Chapter, figure and question numbering; the screen build; the audit; the screen stylesheet |
| `book/tex/` | The print edition: the HTML-to-LaTeX converter, the style file, page checks and the bundled fonts |
| `book/tools/` | The chapter-order tool, a numbering snapshot, and the briefs the chapter agents worked from |
| `book/NOTES.md` | Plans, style rules and a dated log of every decision and audit |

## Building

- **Screen edition**: `cd book && python3 -I build.py && python3 -I audit.py ebpf-book.html`.
  Needs Python 3 and `qrencode`.
- **Print edition**: the commands are in the header of `book/tex/book.tex`. Needs
  LuaLaTeX (TeX Live, including the `crimsonpro` font package), the Open Sans
  Condensed font, `rsvg-convert` (librsvg), `qrencode` and `makeindex`; the page
  checks in `book/tex/checks/` need `pdftotext` (poppler) and PyMuPDF.
- **Labs and the program**: Linux with `clang`, `bpftool` and libbpf. Steps that
  need root run in a throwaway VM with virtme-ng (`vng`), never on the host.
  The proof chapters use Z3: `python3 -m venv book/.venv && book/.venv/bin/pip install z3-solver`.

## How it was written

Written by Mohammad Shehar Yaar Tausif with Claude, an AI model by Anthropic.
Each chapter was planned figures first, checked against the Linux v7.2 source or
a real run, audited by script, and looked at page by page in print.
`book/NOTES.md` records every plan, decision and audit.

## Licence

Copyright © 2026 Mohammad Shehar Yaar Tausif. Written with Claude, an AI model by Anthropic.

- **The book's text and figures** (`book/src/`, `book/figs/out/`, `book/ebpf-book.html`,
  `book/ebpf-book-print.pdf`): Creative Commons Attribution-ShareAlike 4.0
  International, in [`book/LICENSE-CC-BY-SA-4.0.txt`](book/LICENSE-CC-BY-SA-4.0.txt).
- **The code** (everything else: the build, audit and print tools, the figure
  scripts, the labs, the program and the kernel patches): GNU General Public
  License, version 2, in [`LICENSE`](LICENSE).
- **The fonts** in `book/tex/fonts/`: their own licences, beside them (SIL Open
  Font License 1.1 for Literata and JetBrains Mono, Ubuntu Font Licence 1.0 for
  Ubuntu Mono).
- Quotations from papers, documentation and the Linux source remain under their
  own terms.
