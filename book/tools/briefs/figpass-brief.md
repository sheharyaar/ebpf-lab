You are redrawing figures for the print edition of a technical book, "eBPF for Systems Engineers" (/home/wazir/workspace/repos/eBPF-playground/book). The book now prints in the O'Reilly format on a 127 mm text column, and every figure is set at that width. Most figures were drawn for the screen: at 127 mm their smallest labels print at 4.8-7.1 pt, and they use five to nine colours. Your job is to redraw the figures listed under "Your figures" so that they read at a glance in print. Another agent may be redrawing a different set of figures at the same time; touch only your own.

## Read first
- book/NOTES.md, section "Figure rules" (binding) and the decisions-log entries of 2026-11-12 (night) about the eleven figures already redrawn.
- The model figures, already done to these rules. Look at each at print size before you start:
  - figs/out/ch04-walk-flow.svg, a flowchart with a decision; code at the end of figs/ch04.py.
  - ch08-path-print.svg, a path with attachments; code in figs/ch08.py.
  - ch03-relo-print.svg, a flowchart; figs/ch03.py.
  - ch01-helpercall-print.svg, a grid; figs/ch01.py.
  - ch06-narrow-print.svg, rows on one axis; figs/ch06.py.
  - ch02-loadseq.svg, a sequence; figs/ch02.py.
  - ch12-road.svg, a flowchart; figs/ch12.py.
  - Copy their helpers, `t()`, `node()`, `line()` and the SANS/UMONO font stacks, rather than inventing new ones.
- For each figure: the chapter's source in src/ (the figure's caption and every sentence that refers to it), and the figure's current SVG at print size.

## For each figure
1. Write down the one claim the figure makes. Take it from the caption and the prose, not from the old drawing.
2. Choose the form from the relation, as the rules say:
   - a process with decisions is a flowchart;
   - a mapping or comparison is a table;
   - a memory layout is a box diagram;
   - history is a timeline.
   A figure that is really a table drawn as boxes becomes an HTML `<table>` inside its `<figure>`, keeping its id and caption. Figures 0.1, 1.1, 5.3, 8.2 and 12.3 show how. Never draw a table as boxes joined by arrows.
3. Redraw on the 680-unit canvas.
   - Words at least 14.5 units, node titles 16.
   - Open Sans Condensed for words, Ubuntu Mono for code names.
   - Black and grey with one accent. Whatever the accent marks also differs by line style or weight, so the figure reads in greyscale.
   - A legend inside the figure when it uses more than one line style.
   If the claim no longer fits the width at that size, split the figure's content between the drawing and the caption, or drop decoration. Never shrink the type.
4. Keep every fact.
   - Every number, name and log line in the old figure must still be in the new figure or its caption, unless it contradicts the prose.
   - If the figure and the prose disagree, do not choose: report it.
   - Do not invent content; any wording that is your own goes in your report.
5. Fix the words that point at the old drawing.
   - Captions and prose that name colours ("each coral dot", "the amber row", "teal for registers") or old positions ("the left column", "the top frame") must describe the new drawing.
   - Captions describe what is drawn; the observation stays in the prose.
   - Colour words in the chapters now: ch00, ch02, ch03, ch05, ch06, ch07, ch09, ch10, ch11, ch12, ch13, ch14, ch17 and the primer. Check each one that belongs to your figures.
6. Redraw in place: same output name, same {{fig:NAME}} reference.
   - Before you change a figure script, copy it once to book/figs/pre-print/ (create the folder), so the screen-era code is kept.
   - If a figure becomes an HTML table, leave its SVG file where it is (unused files are deleted only with the learner's permission) and remove the {{fig:NAME}} reference.
7. Look at it at print size and fix what you see. From book/:
   `FONTCONFIG_FILE=$PWD/tex/out/fc/fonts.conf rsvg-convert -w 750 -b white -o /tmp/x.png figs/out/NAME.svg`, then view the PNG.
   Check that the arrows agree with the prose, that no text is cropped or overlapping, that no tag floats free of its node, and that nothing would need colour to be understood.

## Checks before you report
- `cd book && python3 -I build.py /tmp/figpass.html && python3 -I audit.py /tmp/figpass.html` ends with `RESULT: clean`.
- A label-size check over your figures: the smallest font-size in each SVG is at least 14.5 units, the viewBox width is 680, and there are at most three non-grey colours, all of them one hue.
- `grep -n -i -w "teal\|coral\|amber\|purple\|green"` over your chapters' sources finds nothing that still refers to a figure.

## Rules
- Write only these: your figures' scripts in book/figs/, their outputs in book/figs/out/, the backups in book/figs/pre-print/, and in your chapters' sources (book/src/chNN.html) only the figure markup, captions and sentences that refer to your figures.
- Do not edit:
  - book/tex/ (another agent is converting the book to LaTeX);
  - NOTES.md, build.py, audit.py, book.css, front.html;
  - src/ch16.html or figs/ch16.py;
  - any figure not on your list.
- Do not commit. Do not install packages. Do not spawn subagents.
- The organisation's limits are 50 requests a minute and 500,000 input tokens a minute, and other agents are running: keep tool output small, and look at images at 750 px wide, not larger.

## Report back (short)
For each figure:
- the claim;
- the form before and after;
- the height before and after at 127 mm;
- any wording that is yours;
- any prose you changed.
Then:
- the checks' results;
- every disagreement between a figure and its prose that you found and left alone.

## Your figures
{{SCOPE}}
