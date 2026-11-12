# NOTES — eBPF, a book dossier

Living plan for the eBPF learning document, in the shape `~/workspace/learning/agent-directory/BOOK_STYLE_LEARNING.md` asks for (section 2.4). The HTML will sit next to this file as `ebpf-dossier.html`. Learner state (profile, probe maps) lives in `../.alvar/`.

## Status

| Date | State |
|---|---|
| 2026-11-11 | Scoping. Spec written. Reader contract drafted from the brief. Probe (Alvar) running; its map goes to `../.alvar/maps/ebpf-dossier-scope.md`. Plan not yet approved; no prose written. |
| 2026-11-11 | Book edition prototype (`sample-ch10-book.html` and `.pdf`) after "It doesnt look like a book"; papers re-sorted for plan B. Awaiting feedback. |
| 2026-11-11 | **Decision: plan B, finish line = kernel contributions.** Second sample built: `sample-ch10-verifier-source.html` (the chapter B adds). Awaiting feedback on both samples. |
| 2026-11-11 | Sample built: `sample-ch1.html` (the bytecode chapter alone, with front and back matter), awaiting the learner's feedback. Plan v2 still awaiting approval (A or B). |
| 2026-11-11 | Plan v2 written (session 2), awaiting approval; complaints audited. |
| 2026-11-11 | Probe done (session 2): trunk unknown or blocked except hooks (known); both branches unknown, papers unread. Pain points recorded. Finish line: the learner asked for a full breakdown of the three options before choosing. |

## Reader contract (draft, 2026-11-11, from the learner's brief; confirm after the probe)

- **Finish line**: plan B with kernel contributions as the goal (2026-11-11); see *Plan B adopted*. Earlier: three candidates under *Purpose* below. Recommendation: A as the trunk, B as the axis, C as two branch chapters.
- **Starting point**: systems engineering background; has implemented `hello_world/01–03` and `maps/01–02` in this playground with libbpf, CO-RE, `vmlinux.h` and skeleton loaders; has not yet done ringbuf, pinning, timers, kfuncs. Has the 1993 BSD Packet Filter paper and the hXDP paper printed.
- **Depth floor**: proposed. Mechanism level with source anchors: read `Documentation/bpf/verifier.rst` and the ISA RFC, read small parts of `kernel/bpf/verifier.c` and `arch/x86/net/bpf_jit_comp.c` where a figure needs them; never transcribe either. Paper-reading depth for the hardware branch. "Intuition plus one worked example" for the formal branch (intervals and tnums by hand on a four-bit example; what a soundness claim says).
- **Implementation bias**: Linux, x86-64, libbpf and CO-RE in C (the playground's conventions), `bpftool` for every "look at it" moment; the learner's kernel is 7.2 (Arch). Go variants mentioned only where the playground offers them.
- **Medium**: print-first. Step widgets on at most four figures: the verifier walking one branch with state pruning; one packet through the hook points (driver, XDP, tc, socket); one bytecode instruction and a tail call becoming x86; the lineage timeline (filter by branch). Everything else static.
- **Natural axis of the lineage**: time, labelled by kernel version. The learner asked for "a timeline way, as things started getting added".
- **Hands-on**: yes, the playground. Labs are "Try it".
- **Existing pain** (asked 2026-11-11): verifier errors; SEC names and attaching; `vmlinux.h`, BTF and CO-RE; and, in their words, "how the verification works at the kernel level, and how can I add more points, etc." ("points" is unclear: attach points or verifier checks; ask). These get the first figures, and each gets its own chapter or opening figure in every option.
- **Budget**: default, about 75 minutes of reading and 9,000 words of prose; 11 chapters plus an epilogue.

## Purpose: three candidate finish lines

**A. The mechanism (trunk).** "I can draw, from memory, what happens between `clang -target bpf` and my program's first event: ELF sections, the `bpf()` syscall, the verifier (what it promises and how it walks the program), the JIT, the attach point, the map, and the read from user space. Given a verifier rejection from the playground, I can name the rule that tripped."

**B. The lineage (axis).** "I can place every eBPF mechanism I meet on a timeline and say which problem it was added to solve: why tracepoints after kprobes, why BTF before CO-RE, why `bpf_link`, why kfuncs after helpers, why arena."

**C. The branches.** Hardware: "I can explain what hXDP had to build to run XDP bytecode on an FPGA, why maps, helpers and instruction-level parallelism are the hard parts, and where eHDL moved the line." Formal: "I can say what 'the verifier's range analysis is sound' means, what intervals and tnums are, and what Agni proves and does not prove."

**Recommendation.** A is the spine; B is the ribbon that runs through every chapter; C is two interludes near the end, each with a read-with card for the printed paper. Depth as in the contract above. The probe decides which trunk chapters can be short and which branch gets the deeper treatment.

## Volume shapes put to the learner (2026-11-11, after the probe)

Shared core in all three, by kernel version: 0 why run code in the kernel and the full timeline · 1 1993 filter machine · 2 2014 ISA · 3 load vs attach, SEC names to hooks, links · 4 BTF, `vmlinux.h`, CO-RE (split out because of the pain points) · 5 verifier I, the walk · 6 verifier II, reading rejections from the playground · 7 JIT · 8 hooks · 9 maps · E epilogue. About 7,500 words.

| Shape | Adds to the core | Size | Branches |
|---|---|---|---|
| A balanced (recommended) | "How the verifier tracks numbers" after ch 6 (intervals and tnums by hand from `bpf_reg_state` and `kernel/bpf/tnum.c`, what "sound" means, what Agni checks); "The program on the NIC" (hXDP first-read on-ramp) near the end | 13 ch, ~9,500 words, ~80 min, 3 read-with cards | on-ramp |
| B deep trunk | "Verifier III: inside `verifier.c`" (`do_check()`, state fork, pruning, where each log message is raised) | 12 ch, ~8,500 words, ~70 min, 1 read-with card | volume 2 |
| C deep branches | hXDP design + hXDP vs NIC offload vs eHDL; abstract interpretation by hand + what PREVAIL and Agni prove | 15 ch, ~11,500 words, ~100 min, 4 read-with cards | full chapters |

## Branch map

| Branch | What it is | Proposed depth | Why now, or why later | Anchor sources |
|---|---|---|---|---|
| Lineage: cBPF to eBPF | The 1993 filter machine, Linux socket filter, cBPF JIT, seccomp, then eBPF in 2014 | one interlude chapter | the learner's own axis; the printed paper | McCanne and Jacobson 1993; `bpf-internals-1`; LWN 599755 |
| ISA and bytecode | registers, 64-bit, calls, the encoding, reading `bpftool prog dump xlated` | one mechanism chapter | everything else is read through it | RFC 9669; kernel `instruction-set.rst`; armosec reverse-engineering post |
| Object model and loader | `bpf()`, fds, maps, programs, links, BTF, pinning, ELF sections, CO-RE, skeletons | one mechanism chapter | the playground already exercises it; make the mechanism explicit | kernel libbpf overview; Nakryiko CO-RE guide; kernel `btf.rst` |
| Verifier | what it promises, the state walk, pruning, bounded loops, helper and kfunc contracts, reading rejections | two chapters: mechanism, then case | the centre of the document | kernel `verifier.rst`; LWN 794934 (bounded loops) |
| JIT | bytecode to x86, interpreter versus JIT, tail calls, trampolines | one mechanism chapter | the learner listed it; the Cloudflare post is excellent | Cloudflare tail-calls post; `arch/x86/net/bpf_jit_comp.c` |
| Hooks and program types | kprobe, tracepoint, fentry, tc, XDP, LSM, struct_ops, sched_ext: what each sees and when it runs | one comparison chapter | ties the playground exercises together | kernel docs per type; bcc kernel-versions |
| Maps and memory | array, hash, per-cpu, ringbuf, spinlocks, arena; what the verifier knows about a map value | one comparison or lab chapter | the next playground exercises (ringbuf, pinning) | kernel map docs; LWN on arena |
| Hardware offload | XDP offload (Netronome nfp), hXDP, Warp, eHDL, AF_XDP | one interlude with a read-with card | the learner's interest; paper in hand | hXDP OSDI 2020; Warp ATC 2022; eHDL ASPLOS 2023; pchaigno's hXDP summary |
| Proving the verifier | PREVAIL, tnums, Agni, state embedding, "untenable", KFlex, Rex | one interlude with a read-with card and one worked example | the learner's interest; needs an on-ramp, not a maths course | PREVAIL PLDI 2019; Tnums CGO 2022; Agni CAV 2023 and the Agni site; State Embedding OSDI 2024; HotOS 2023 |
| Tracing and observability tooling | bpftrace, BCC, perf tools, USDT | **later** | tooling drifts; the mechanism chapters cover what the tools rest on | Gregg, *BPF Performance Tools* (2019) |
| Networking datapaths | sk_lookup, sockmap, Cilium's datapath | **later** | a document of its own; the Cilium dossiers in `~/workspace/learning/cilium-k8s-control-plane/` already exist | Cilium BPF reference guide; ebpfchirp sk_lookup post |
| Security | LSM programs, seccomp lineage, tokens, signed programs | **later**, mentioned in the hooks chapter and the epilogue | not in the finish line | kernel LSM docs |
| Beyond Linux | eBPF for Windows, uBPF, the ISA standard | epilogue only | context, not mechanism | RFC 9669; PREVAIL summary |

## Lineage event list (draft; "verified" means confirmed against the source this session)

| Year | Kernel | Event | Chapter | Source | Status |
|---|---|---|---|---|---|
| 1993 | — | The BSD Packet Filter paper: a register-based filter machine for tcpdump | 1 | McCanne and Jacobson, USENIX Winter 1993 | verified (paper in hand) |
| 1997 | 2.1.75 | Linux Socket Filter: cBPF arrives in Linux | 0 | patch-2.1.75 (21 Dec 1997) adds filter.txt, net/core/filter.c, filter.h as new files | verified |
| 2011 | 3.0 | cBPF JIT for x86-64 (Eric Dumazet) | 0, 7 | kernelnewbies Linux_3.0 "Berkeley Packet Filter just-in-time filtering"; commit 0a14842f5a, 27 Apr 2011 | verified |
| 2012 | 3.5 | seccomp-bpf: cBPF filters system calls | 0 | kernelnewbies Linux_3.5 "Seccomp-based system call filtering" | verified (3.5; LWN 599755's "3.4" is wrong) |
| 2014 | 3.15 | eBPF internal: cBPF converted to the new machine inside the kernel | 2 | bcc kernel-versions | verified |
| 2014 | 3.16 | x86-64 eBPF JIT | 6 | bcc kernel-versions | verified |
| 2014 | 3.18 | the `bpf()` syscall and maps | 3 | bcc kernel-versions | verified |
| 2015 | 3.19 | programs attach to sockets; hash and array maps | 3, 8 | bcc kernel-versions | verified |
| 2015 | 4.1 | kprobes; tc `cls_bpf` and `act_bpf` | 7 | bcc kernel-versions | verified |
| 2015 | 4.2 | tail calls; program arrays | 6 | bcc kernel-versions | verified |
| 2016 | 4.4 | bpffs: persistent maps and programs; tc direct-action | 3 | bcc kernel-versions | verified |
| 2016 | 4.7 | tracepoints; direct packet access | 7 | bcc kernel-versions | verified |
| 2016 | 4.8 | XDP | 7, 9 | bcc kernel-versions | verified |
| 2016 | 4.9 | perf-event programs; tc hardware offload | 7, 9 | bcc kernel-versions | verified |
| 2017 | 4.10 | cgroup programs; Netronome `nfp` XDP (offload base) | 7, 9 | bcc kernel-versions | verified |
| 2017 | 4.12 | generic XDP; map-in-map | 8 | bcc kernel-versions | verified |
| 2018 | 4.15 | bpftool in the kernel tree | 2 | bcc kernel-versions | verified |
| 2018 | 4.16 | bpf-to-bpf function calls | 6 | bcc kernel-versions | verified |
| 2018 | 4.17 | raw tracepoints | 7 | bcc kernel-versions | verified |
| 2018 | 4.18 | BTF; AF_XDP | 3, 9 | bcc kernel-versions | verified |
| 2019 | 5.1 | `bpf_spin_lock` | 8 | bcc kernel-versions (helpers) | verified |
| 2019 | 5.2 | one-million-instruction limit | 4 | bcc kernel-versions | verified |
| 2019 | 5.3 | bounded loops | 4 | bcc kernel-versions; LWN 794934 | verified |
| 2019–20 | libbpf | CO-RE: compile once, run everywhere | 3 | nakryiko.com | verified (URL) |
| 2020 | 5.5 | BPF trampoline: fentry and fexit | 6, 7 | bcc kernel-versions | verified |
| 2020 | 5.6 | struct_ops (TCP congestion control in BPF) | 7 | bcc kernel-versions | verified |
| 2020 | 5.7 | LSM programs; `bpf_link` | 2, 8 | bcc (LSM); docs.ebpf.io BPF_LINK_CREATE "v5.7" | verified |
| 2020 | 5.8 | ring buffer; iterators | 8 | bcc kernel-versions | verified |
| 2020 | 5.10 | sleepable programs | 4 | bcc kernel-versions | verified |
| 2021 | 5.13 | kfuncs: calling kernel functions; `for_each_map_elem` | 8 | bcc (helper 5.13); docs.ebpf.io KFuncs "v5.13" | verified |
| 2021 | 5.15 | `bpf_timer`; the syscall program type | 8 | bcc kernel-versions | verified |
| 2022 | 5.17 | `bpf_loop` | 4 | bcc kernel-versions | verified |
| 2022 | 5.19 | dynptr; kptr | 8 | bcc kernel-versions | verified |
| 2022 | 6.1 | user ring buffer | 8 | bcc kernel-versions | verified |
| 2023 | 6.4 | open-coded iterators (`bpf_for`) | 4 | docs.ebpf.io bpf_iter_num_new "v6.4" | verified |
| 2024 | 6.7 | BPF exceptions (`bpf_throw`) | 4 | docs.ebpf.io bpf_throw "v6.7" (6.7 released January 2024) | verified |
| 2024 | 6.9 | arena; BPF token | 8 | LWN 6.9 merge-window coverage | verified (search) |
| 2024 | 6.10 | `bpf_wq` | 8 | docs.ebpf.io bpf_wq_init "v6.10" | verified |
| 2024 | 6.12 | sched_ext | 7 | LWN, heise | verified (search) |
| 2024-10 | — | RFC 9669: the BPF ISA becomes a standard | 2, 11 | rfc-editor.org | verified |
| 2025 | 6.18 | signed BPF programs | 11 | kernelnewbies Linux_6.18 "Signed bpf programs" (featured) | verified |

**Ribbon labels (canonical, 2026-11-11; every event verified).** Chapters pick 8–12 and mark their span with `class="here"`. Write each as `<li>YEAR<br>LABEL</li>`, exactly as here:
1993 BSD filter · 1997 2.1.75 socket filter · 2011 3.0 cBPF JIT · 2012 3.5 seccomp · 2014 3.15 eBPF · 2014 3.16 x86 JIT · 2014 3.18 bpf(), maps · 2015 3.19 socket programs · 2015 4.1 kprobes · 2015 4.2 tail calls · 2016 4.4 bpffs · 2016 4.7 tracepoints · 2016 4.8 XDP · 2016 4.9 perf events · 2017 4.10 cgroups · 2018 4.15 bpftool · 2018 4.16 bpf-to-bpf calls · 2018 4.17 raw tracepoints · 2018 4.18 BTF · 2019 5.2 1M insns · 2019 5.3 bounded loops · 2020 CO-RE · 2020 5.5 trampolines · 2020 5.6 struct_ops · 2020 5.7 LSM, bpf_link · 2020 5.8 ring buffer · 2020 5.10 sleepable · 2021 5.13 kfuncs · 2022 5.17 bpf_loop · 2023 6.4 bpf_for · 2024 6.7 exceptions · 2024 6.9 arena, token · 2024 6.10 bpf_wq · 2024 6.12 sched_ext · 2024 RFC 9669 · 2025 6.18 signing.
(CO-RE: libbpf and Nakryiko's guide, February 2020; the kernel half is BTF in 4.18.)

Research lane (for the two branch chapters): 1993 BSD BPF · 1996 proof-carrying code (Necula and Lee, compared to cBPF) · 2014 Jitk · 2019 PREVAIL · 2020 Jitterbug, JitSynth, hXDP · 2021 K2 · 2022 Tnums, Warp · 2023 Agni, eHDL, "Kernel extension verification is untenable" · 2024 Agni++ (SAS), State Embedding (OSDI), verifier fuzzing (EuroSys), KFlex (SOSP) · 2025 Rex (ATC), SoK on memory safety (S&P), refinement types for PREVAIL (OOPSLA), approximation-enforced execution (Security).

Provenance (rechecked 2026-11-11, session 2; the first draft said "all from pchaigno's list", which was wrong): every title above is on pchaigno's list except three, verified elsewhere: Tnums = "Sound, Precise, and Fast Abstract Interpretation with Tristate Numbers" (Vishwanathan, Shachnai, Narayana, Nagarakatte; CGO 2022; arXiv 2105.05398); "Kernel extension verification is untenable" (Jia et al., HotOS 2023, sigops.org PDF); Agni++ = "Fixing Latent Unsound Abstract Operators in the eBPF Verifier of the Linux Kernel" (SAS 2024; per the Rutgers Agni page and the authors' slides; full text not read). K2 is on the list under its title "Synthesizing Safe and Efficient Kernel Extensions for Packet Processing" (SIGCOMM'21); KFlex under "Fast, Flexible, and Practical Kernel Extensions" (SOSP'24).

## Plan v2 (2026-11-11, session 2; proposed, awaiting approval)

Supersedes the first chapter sketch. Fitted to the spec's limits (8–12 chapters counting prologue and epilogue, 600–800 words each, at least two figures each, Mermaid at most 40%).

**Deliverable.** `dossier/ebpf-dossier.html`, one file, with `NOTES.md` and `audit.py` beside it. Literata for prose, JetBrains Mono for code and labels. Loads Mermaid 11 only (three sequence diagrams); no D3 or Plot, because the one numeric figure has fewer than eight points and is hand SVG. Print-first, A4, about 60 pages.

**Medium decision.** Print-first. Step widgets on four figures, the four mechanisms in this topic whose state changes step by step: the CO-RE relocation, the verifier walking a branch, a register's range narrowing, one event passing the hooks. Everything else is static. Each widget prints as a film strip of three to five frames.

**Spine.** "The life of one program": the learner's own `maps/02-hash-map` program (counts `write()` calls per PID). C source → bytecode with a `call` to the map-lookup helper → `bpf()` load → the verifier proves the NULL check → JIT → attached to its hook → first event → the hash map → the loader iterates the keys from user space. Chosen because it passes through the four strands the probe found blocked: the helper call, load vs attach, the NULL check, reading a map from user space.

**Lineage.** Axis: time, labelled by kernel version. 25 events on the lineage figure, 8–12 per ribbon. Not yet on any ribbon until verified: Linux Socket Filter (2.1.75, 1997), cBPF JIT (3.0, 2011), seccomp-bpf (3.5, 2012), `bpf_link` (5.7), kfuncs (5.13), BPF signing (version).

Events: 1993 BSD Packet Filter · 1997 Linux Socket Filter · 2011 cBPF JIT · 2012 seccomp-bpf · 2014 3.15 eBPF inside the kernel · 2014 3.16 x86-64 eBPF JIT · 2014 3.18 `bpf()` and maps · 2015 4.1 kprobes, tc · 2015 4.2 tail calls · 2016 4.4 bpffs pinning · 2016 4.7 tracepoints · 2016 4.8 XDP · 2016–17 4.9–4.10 hardware offload, Netronome `nfp` · 2018 4.16 bpf-to-bpf calls · 2018 4.18 BTF · 2019 5.3 bounded loops · 2019–20 CO-RE · 2020 5.5 trampolines, fentry · 2020 5.7 LSM programs, `bpf_link` · 2020 5.8 ring buffer · 2020 hXDP · 2021 5.13 kfuncs · 2022–23 tnums proved, Agni · 2024 6.9 arena, token · 2024 6.12 sched_ext · 2024 RFC 9669.

**Layer tags.** `[LINEAGE] [ISA] [LOADER] [VERIFIER] [RUNTIME] [HW]`.

| # | Title | Shape | Opens with | Figures (kind · job) | Lab | Ribbon | Read-with / to verify |
|---|---|---|---|---|---|---|---|
| 0 | Prologue: 1993, a filter inside the kernel | interlude | a scene: tcpdump losing packets | three ways to run your code in the kernel: module, user-space daemon, filter machine (hand SVG columns) · the BSD network tap redrawn from the paper's overview figure (hand SVG) · the lineage figure, all events (hand SVG, wide) | none; margin note: `tcpdump -d` still prints the 1993 machine | whole | card: BSD 1993 |
| 1 | 2014: the filter becomes a machine | mechanism | the figure itself | classic vs extended machine side by side (hand SVG columns) · one instruction's 64-bit encoding (hand SVG) · your program's bytecode with the helper call marked (`llvm-objdump -d`, pre as figure) | Try it: find the helper call in your own object (~20 min, read) | 3.15–3.18, 2024 RFC | card: RFC 9669 encoding section; armosec, LWN 599755, `bpf-internals-2`, kernel "Classic BPF vs eBPF" |
| 2 | Load, then attach | mechanism | a command and its output (`strace`) | **pain:** from SEC name to hook (hand SVG) · the load sequence (Mermaid sequence) · the object model: descriptors, reference counts, pinning (hand SVG) | Try it: watch the syscalls, then `bpftool prog show` and `link show` (~25 min, measure) | 3.18, 4.4, 5.7 | docs.ebpf.io syscall pages and ELF concept; kernel libbpf program-types page (verify which page holds the section table) |
| 3 | One binary, many kernels: BTF and CO-RE | comparison | a question you have: why does `vmlinux.h` exist? | three ways to cope with changing struct layouts: headers at run time, fixed offsets, CO-RE (table as figure) · **pain:** a CO-RE relocation (step widget) · where `vmlinux.h` comes from (hand SVG) | Try it: find `task_struct` in your kernel's BTF and the relocation record in your object (~25 min, read) | 4.18, 2019–20 | Nakryiko's CO-RE guide (verify URL); kernel `btf.rst`; Unstable Foundations (EuroSys'25) |
| 4 | The verifier, part one: walking every path | mechanism | a number: one million instructions | the promise: what a loaded program can never do (hand SVG absence list) · **pain:** the verifier walking your program (step widget) · one register's state at one instruction, described by function (hand SVG) | Trace it by hand: walk your program's paths on paper (~20 min, no environment) | 5.2, 5.3 | card: `verifier.rst` (value tracking, pruning, liveness); LWN 794934; SoK memory safety (S&P'25) |
| 5 | The verifier, part two: reading a rejection | case | the log itself | your program rejected three ways (three logs, pre as figure, lines marked) · **pain:** from message to rule to the `verifier.c` function that raised it (hand SVG) | Try it: break it three ways (~30 min, break a real one) | points back | `verifier.rst` "Understanding eBPF verifier messages" (points back to the card); the three verifier-fuzzing papers |
| 6 | How the verifier tracks numbers | mechanism | a question: how does the kernel know `x < 8`? | a tnum on four bits (hand SVG) · a range narrowing (step widget) · sound vs precise on a number line (hand SVG) | Try it: read the ranges in your own verifier log at log level 2 (~20 min, read) | 2019 PREVAIL, 2022 Tnums, 2023 Agni | card: Agni (CAV'23), sections chosen after reading it; Tnums (CGO'22); ISSTA'25 combined domains; Agni++ (SAS'24) |
| 7 | The JIT: bytecode becomes x86 | comparison | a command and its output (`bpftool prog dump jited`) | interpreter vs JIT (table as figure) · one instruction becoming x86 (hand SVG, three static frames) · a tail call on x86, redrawn from the Cloudflare post (hand SVG) | Try it: see your program as x86 (~20 min, read) | 3.16, 4.2, 4.16, 5.5 | Cloudflare tail calls; Jitterbug (OSDI'20); `arch/x86/net/bpf_jit_comp.c`; tail-call limit value (verify) |
| 8 | Hooks: where a program runs and what it sees | comparison | a two-line quote from the kernel docs | one event through the hooks, packet path and task path (step widget) · what each program type receives and may do (table as figure) · kprobe vs tracepoint vs fentry on one function (Mermaid sequence) | Try it: predict, then count the tracepoints and kprobe-able functions on your machine (~20 min, measure) | 4.1, 4.7, 4.8, 5.5, 5.7, 6.12 | docs.ebpf.io program types; cache_ext (SOSP'25) as "how a new hook gets into the kernel"; Late-Binding (OSDI'26) |
| 9 | Maps: where the data lives | mechanism | your loader's output, as a figure | map kinds side by side (table as figure) · how your loader reads the map (Mermaid sequence) · ring buffer vs perf buffer (hand SVG, conceptual, no code: ring buffers are the next exercise) | Try it: read your map from outside while it runs (~20 min, measure) | 3.18, 5.8, 6.9 | kernel maps docs; docs.ebpf.io map types |
| 10 | The program on the NIC: hXDP | interlude | a scene from the paper's problem statement | three ways to run XDP off the CPU: NIC offload, hXDP soft processor, eHDL circuit per program (hand SVG columns) · hXDP's hardware redrawn from the paper (hand SVG) · throughput from the paper's evaluation (hand SVG plot, numbers to verify) | Trace it by hand: pack eight instructions into four lanes (~25 min, no environment) | 4.9–4.10, 2020, 2022, 2023 | card: hXDP; pchaigno's summary; Warp (ATC'22); eHDL (ASPLOS'23) |
| 11 | Epilogue: limits, traps, and where it went | interlude | a question | the whole tower, every box from earlier figures (hand SVG) · the argument about the verifier: verifier, KFlex, Rex, "untenable" (hand SVG) | none | 6.9, 6.12, RFC, signing | SoK; KFlex; Rex; "untenable"; previews of volume 2 |

Shapes in order: interlude, mechanism, mechanism, comparison, mechanism, case, mechanism, comparison, comparison, mechanism, interlude, interlude. Four kinds; never three alike in a row; the lineage chapter is an interlude.

Totals: 34 figures (about 19 hand SVG, 4 tables as figures, 4 step widgets, 3 Mermaid = 9%, 2 logs or listings, 1 plot, plus the lineage figure and ribbons); 10 labs, 2 of them need no environment; 5 read-with cards; about 9,000 words of prose.

**Term map (draft; the audit reads the `## Terms` table once approved).** Prologue: kernel extension, filter, classic BPF, accumulator, control-flow graph, program, hook, map (plain sense). Bytecode chapter: eBPF, instruction, opcode, immediate, registers r0–r10, calling convention, helper function, helper ID, bytecode, ELF object. Load chapter: `bpf()` syscall, map (formal), program type, attach type, ELF section, `SEC()`, libbpf, skeleton, load, attach, link, pinning, bpffs. CO-RE chapter: BTF, `vmlinux.h`, struct layout, relocation, CO-RE. Verifier part one: verifier, verifier state, register type, scalar, pointer-or-NULL, path, pruning, bounded loop, instruction limit. Verifier part two: verifier log, log level, reference tracking. Numbers chapter: abstract value, interval, tnum, sound, precise, abstract interpretation. JIT chapter: JIT compiler, interpreter, native code, tail call, program array, bpf-to-bpf call, trampoline. Hooks chapter: context, kprobe, tracepoint, raw tracepoint, fentry and fexit, XDP, tc, LSM program, struct_ops, kfunc, sched_ext. Maps chapter: map type, key, value, per-CPU map, ring buffer, perf buffer, arena. hXDP chapter: hardware offload, SmartNIC, FPGA, soft processor, VLIW, lane, high-level synthesis. Dependency checks: the verifier chapters need "map" and "program type" (load chapter) and "helper" (bytecode chapter); the hooks chapter needs "trampoline" (JIT chapter); the hXDP chapter needs XDP (hooks chapter), helpers and maps.

**Question mix.** Two to four per chapter, at least one *predict the value* and one *here is a symptom*. Examples: the byte size of a program with one 64-bit immediate load (bytecode); `bpftool prog show` lists the program but the counter stays at zero (load vs attach); loads on the laptop, fails on the server with a CO-RE relocation error (CO-RE); how many paths three independent branches make, and what pruning leaves (verifier part one); add two four-bit tnums by hand (numbers); a kprobe program goes silent after a kernel upgrade (hooks); bundle cycles for eight dependent instructions in four lanes (hXDP).

**Volume shapes under the 12-chapter cap.** A = this plan. B = swap the hXDP chapter for "Verifier III: inside `verifier.c`"; hXDP moves to volume 2. C cannot fit one volume (15 chapters), so C = A now plus a branches volume later (hXDP in depth, Warp and eHDL, abstract interpretation, PREVAIL, Agni and Agni++, the verifier-replacement argument).

**Process.** (1) Phase 1: verify the six held-back lineage events, the CO-RE guide URL, the tail-call limit, the hXDP throughput numbers; read Agni and write the five read-with cards. (2) Draw the four pain-point figures first (SEC name to hook, CO-RE relocation, verifier walk, message to rule) and show them to the learner before any prose. (3) Build the prologue and the bytecode chapter, stop, and have the learner print them: the real test of the look-and-feel complaints. (4) The rest, one or two chapters per edit; audit, print check, screenshots. (5) Run every lab solution on the learner's kernel 7.2 before it ships. Labs use copies of the learner's solutions in a scratch directory and never touch the playground; nothing gives away `maps/03-ringbuf`, `pinning/*` or `timers_kfuncs/*`.

**Cut-lever.** Trim first: the JIT and hooks labs, the epilogue's second figure, margin papers. Never: figures elsewhere, the vocabulary discipline, the answer key.

**Assumptions (checked 2026-11-11).** Kernel 7.2 (Arch), `bpf_jit_enable=1`, BTF at `/sys/kernel/btf/vmlinux`; `bpftool`, `strace`, `llvm-objdump`, `llvm-readelf`, `tcpdump`, `clang`, `bpftrace`, Chrome and `pdftoppm` installed; labs need `sudo`; fonts load from the CDN (offline reading would need self-hosted fonts).

## Build status: the full book (started 2026-11-11, session 2)

The learner approved the book edition ("this looks awesome, go ahead for all the chapters"). Build layout, all in this folder:

- `src/front.html` (title page, how-to-read), `src/chNN.html` (one chapter each, with `<!--CHAPTER-->`, `<!--ANSWERS-->`, `<!--GLOSSARY-->`, `<!--REFS-->` parts), `figs/common.py` and `figs/chNN.py` (figure generators, output in `figs/out/`), `book.css`, `build.py` (→ `ebpf-dossier.html`), `audit.py` (book mode when Paged.js is present; reads `## Terms` below), `render.mjs` (real-time render to PDF and screenshot: `node render.mjs $PWD/ebpf-dossier.html /tmp/cdp/full 600`).
- Kernel source for facts: sparse v7.2 clone in `/tmp/linux-src-iTa3/linux` (kernel/bpf, include/linux/bpf*.h, tools/testing/selftests/bpf, Documentation/bpf). Re-clone with the commands in the verifier-source chapter if `/tmp` was cleared.
- Labs that need root are collected for one learner-run script at the end (`sudo` asks for a password here).
- "add more points" is still unanswered: the hooks chapter covers new hooks, the verifier-source chapter covers where checks live.

### Resume here (saved 2026-11-12, the learner shut the machine down)

- Done this session: all six held-back lineage events verified (table above; canonical ribbon labels written under it). `render.mjs` takes `CDP_PORT` and `CDP_PROFILE` from the environment so several renders can run at once. `build.py` takes an output path and chapter ids (`python3 -I build.py /tmp/x.html ch02 ch03`) and moves each side note above the paragraph or field it follows in the source. Full build and audit still clean (only the cross-chapter shape flags).
- Proposed, not run: four parallel forks writing ch02+ch03, ch04+ch05, ch06+ch07, ch08+ch09, each writing only its own `src/chNN.html`, `figs/chNN.py`, `labs/chNN-root.sh`, while I write the prologue and epilogue. The learner stopped the session before they started; ask before spawning them again.
- Next: prologue `src/ch00.html` + `figs/ch00.py` (three ways to run code in the kernel; BSD network tap redrawn; full lineage figure `<figure class="fig lineage">`; BSD read-with card: §1, §2 with Figure 1, §3.1–3.5 with Figures 4–7, skip Figures 2–3 and §3.6; margin note on `tcpdump -d`), then ch02–ch09, then the epilogue ch11, then one root script from `labs/*.sh` for the learner to run with `! sudo bash …`, then fix the lab solutions from real output.
- `/tmp` is cleared on reboot. Rebuild what the chapters need: the sparse v7.2 kernel clone (`git clone --filter=blob:none --no-checkout --depth 1 --branch v7.2 https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git`, then `git sparse-checkout set --no-cone kernel/bpf include/linux/bpf*.h include/linux/tnum.h tools/testing/selftests/bpf Documentation/bpf tools/lib/bpf arch/x86/net` and `git checkout v7.2`); RFC 9669 text; the BSD paper PDF (tcpdump.org/papers/bpf-usenix93.pdf); `/tmp/hashmap.bpf.o` (compile command in the chapter 1 lab solution). `render.mjs` lives here now, so `/tmp/cdp` only needs `mkdir`.

| Chapter | Status |
|---|---|
| prologue (ch00) | written 2026-11-12: 783 words, 3 figures (three ways, BSD tap, lineage of 25 rows), BSD read-with card, 2.1.75 field note; audit clean; rendered and looked at |
| bytecode (ch01) | converted from the sample |
| load and attach (ch02) | fork writing ch02+ch03 (2026-11-12) |
| BTF and CO-RE (ch03) | to write |
| verifier part one (ch04) | fork writing ch04+ch05 |
| verifier part two (ch05) | to write |
| numbers (ch06) | fork writing ch06+ch07 |
| JIT (ch07) | to write |
| hooks (ch08) | fork for ch08+ch09 hit the org rate limit (50 requests/min) before writing anything; resume when another fork finishes |
| maps (ch09) | to write |
| verifier source (ch10) | converted from the sample |
| epilogue (ch11) | to write |

## Book edition prototype (2026-11-11, session 2)

The learner, after the two web-edition samples: "It doesnt look like a book". Diagnosis: on screen the samples were a scrolling web article (ragged right, spaced paragraphs, coloured pill tags, monospace capitals, bordered cards, a hero block for a title page); print added pages but kept the card look on A4, so it read as a report.

- Fix: `book.css` plus Paged.js 0.4.3 (pinned on jsdelivr), so the screen shows the same pages that print. A4, single-sided textbook layout: a 118 mm text column, side notes in a 46 mm outer column, figures and tables across the full 170 mm. Justified and hyphenated text with first-line indents; small capitals for labels; ruled blocks for recap, words, check, lab and read-with; running heads (book title left, chapter title right, via `string-set`); page numbers bottom right; the contents shows page numbers (`target-counter`); answers live only in the key. On screen: cream pages on a grey desk, facing pages from 1700 px wide (even pages left).
- Files: `book.css`, `sample-ch10-book.html`, `sample-ch10-book.pdf` (15 A4 pages). Build: `/tmp/ch10/build-book.py` (scratch). Render check: `/tmp/cdp/drive.mjs`, a Node 24 driver for Chrome DevTools, because headless Chrome's `--virtual-time-budget` stalls Paged.js (even a minimal document never finishes); in real time it paginates in about 1.5 s with no errors.
- Paged.js quirks: it treats `@media print` as always on and drops `@media screen`, so screen-only styles are injected after `preview()`. Side notes are floats, so the build moves each note before the paragraph it annotates.
- Trade-offs: A5 rejected (figure labels would print near 5 pt); the web edition's interactive parts (answer toggles, zoom, the stepper) are off in the book edition; step widgets print as frames.
- For the learnings file: a print stylesheet alone does not make a book on screen. The book look needs paged rendering on screen, book typography (justified, indents, small capitals, running heads, page-numbered contents) and ruled blocks instead of cards.

## Papers for plan B (re-sorted 2026-11-11 for the contribution goal)

Read so far: none beyond the list's one-line summaries and, for the three off-list papers, their abstracts. Neither sample cites a research paper (the bytecode sample cites only the 1993 BSD paper).

| Role on the contribution path | Paper (venue) | Where in plan B |
|---|---|---|
| Bugs found in the code you would touch | Validating the eBPF Verifier via State Embedding (OSDI'24); Finding Correctness Bugs in eBPF Verifier with Structured and Sanitized Program (EuroSys'24); eBPF Misbehavior Detection: Fuzzing with a Specification-Based Oracle (SOSP'25) | verifier part two (margin); verifier-source chapter (go deeper, to add); volume 2 core reading |
| Proofs that found or fixed real problems | Verifying the Verifier: eBPF Range Analysis Verification, Agni (CAV'23); Agni++ (SAS'24, off-list); Tnums (CGO'22, off-list; its multiplication was merged into Linux); Formalizing the Linux eBPF Core ISA (OOPSLA'26, "identifying several bugs") | numbers chapter (Agni read-with card); bytecode chapter (margin); volume 2 |
| JIT correctness | Specification and Verification in the Field, Jitterbug (OSDI'20); Synthesizing JIT Compilers for In-Kernel DSLs (CAV'20) | JIT chapter |
| The map of bug classes | SoK: Challenges and Paths Toward Memory Safety for eBPF (S&P'25) | verifier part one (go deeper); volume 2 opener |
| How the verifier tracks values | Program Analysis Combining Generalized Bit-Level and Word-Level Abstractions (ISSTA'25); Prove It to the Kernel (SOSP'25) | numbers chapter |
| The design argument maintainers have | Fast, Flexible, and Practical Kernel Extensions, KFlex (SOSP'24); Rex (ATC'25); "Kernel extension verification is untenable" (HotOS'23, off-list) | epilogue |
| Security side of verifier bugs (if bug hunting leans to vulnerabilities) | An Analysis of Speculative Type Confusion Vulnerabilities in the Wild (Sec'21); BeeBox (Sec'24); Spinner: Detecting Locking Violations in the eBPF Runtime (ASE'25) | volume 2, optional |
| Kernel API drift | Revealing the Unstable Foundations of eBPF-Based Kernel Extensions (EuroSys'25) | CO-RE chapter |
| Adding hooks to the kernel | cache_ext (SOSP'25); FetchBPF (ATC'24); bpf_fault (SOSP'26) | hooks chapter, only if "add more points" meant attach points (still unanswered) |
| Moved out with plan B | hXDP (OSDI'20); Warp (ATC'22); eHDL (ASPLOS'23) | later branch volume |
| Not on this path | PREVAIL, the refinement-type verifier, VEP (other verifiers); the RIOT proofs; Serval; BpfChecker (user-space runtimes); MOAT, Hive, approximation-enforced execution (hardening proposals) | context only |

## Plan B adopted (2026-11-11): finish line, chapter swap, volume 2

The learner chose B and said: "I want kernel contributions".

- **Finish line, volume 1 (in the learner's direction, wording mine; confirm):** "Given any verifier rejection, I can find the line of the source for my kernel that raised it, say why it fired, find the selftest that pins it, and say which tree and which tests a change to it would need."
- **Chapter swap.** The hXDP chapter leaves volume 1 and goes to a later branch volume. In its slot (after the maps chapter, before the epilogue): **"Inside the verifier's source: one rejection, followed to its line"**, shape `lab`. Shapes are now interlude, mechanism, mechanism, comparison, mechanism, case, mechanism, comparison, comparison, mechanism, lab, interlude (five kinds).
- **Depth floor raised** for the verifier chapters: function and line level in the kernel the learner runs (v7.2), with file paths; still no struct transcribed field by field.
- **Volume 2, contributor (sketch, not yet planned):** build and boot a v7.2 or bpf-next kernel in a VM (`tools/testing/selftests/bpf/vmtest.sh`); run `test_progs` and `test_verifier`; write a selftest with `__failure __msg(...)`; prepare a cleanup patch (candidate: the stale `CONST_IMM` lines 155–158 and 173 of the `verifier.c` design comment, still present in bpf-next on 2026-11-11; search lore before writing it, and send nothing without the learner's say-so); read a syzbot or fuzzer report end to end; reproduce a known verifier bug on an old kernel in a VM. The four verifier-fuzzing papers and Agni from the paper-list pass are its reading list.

## Sample: the verifier-source chapter (2026-11-11, session 2)

`sample-ch10-verifier-source.html`: front matter, the chapter, key, glossary, references. Mermaid loaded (one sequence diagram); no widget.

- Figures: the search transcript (pre), the v7.2 verifier map (hand SVG), three instructions and their checkers (hand SVG), the road upstream (Mermaid sequence). Plus a stable-versus-drifting table, a field note (the design comment), a read-with card for `bpf_devel_QA.rst`, two margin notes, one lab.
- Audit: prose 729 words, 4 figures (mermaid, pre, svg), average sentence 14.9 words, 6 questions and 6 key entries, lab and solution; only the three cross-chapter shape flags. Print: 15 A4 pages; Mermaid renders on paper but its labels are small (about 7 pt). Screen: Mermaid has an SVG and no syntax error, 7 answer toggles, 4 zoom buttons.
- Verified against the v7.2 tree (tag "Linux 7.2", 16 August 2026, sparse clone in `/tmp/linux-src-iTa3`): the verifier is split over `verifier.c` (20,065 lines), `cfg.c` (`bpf_check_cfg`), `states.c` (`bpf_is_state_visited`, `states_equal`, `regsafe`), `backtrack.c`, `fixups.c`, `liveness.c`, `log.c`; `do_check()` hands instructions to `do_check_insn()`; the message sites 6164 and 6322; the exact-type compare at 6106; caller-saved reset at 10414; `PTR_TO_MAP_VALUE | ret_flag` at 10455; `mark_ptr_or_null_regs` at 16167 and 16169; the false branch made a known-zero scalar at 15688–15689; `_or_null` at `log.c:432`; the statistics line printed after a rejection (`print_verification_stats`, after `skip_full_check`); `BPF_COMPLEXITY_LIMIT_INSNS` 1,000,000; the disasm format `"(%02x) r%d = *(%s *)(r%d %+d)"`; 121 `progs/verifier_*.c`; the selftest "don't check return value before access" in `progs/verifier_map_ret_val.c` (4 tests), run as `test_verifier_map_ret_val`; `expect_msg` from `test_loader.c:979`; `bpf_devel_QA.rst` (CI on `kernel-patches/bpf`, `bpf@vger.kernel.org`, netdevbpf patchwork, bpf vs bpf-next, the subject prefixes, tests for verifier changes, the selftests-version rule). bpf-next checked on 2026-11-11: 7.4-rc1, `verifier.c` 25,732 lines, same split files, `CONST_IMM` still in the comment.
- **Not run:** the `bpftool prog load` step of the lab (needs root; `sudo` asks for a password and unprivileged BPF is disabled). The solution says so, and gives the expected log lines from the source.

## Sample chapter (2026-11-11, session 2)

`sample-ch1.html` holds the bytecode chapter ("2014: the filter becomes a machine") with title page, how-to-read card, answer key, glossary and references. Built from the spec's stylesheet and scripts (taken from `BOOK_STYLE_LEARNING.sample.html`), Mermaid dropped, four tag colours added (ISA coral, LOADER amber, VERIFIER teal, RUNTIME green).

- Figures: two-machines (hand SVG), eight-bytes encoding (hand SVG, the learner's slots 4 and 8), the learner's bytecode (`llvm-objdump`, pre), one helper call (step widget; print twin is three frames: before, after, the test). SVG sources in `../.alvar/visuals/ch1-*.svg`; generator `/tmp/ch1/gen.py` (scratch).
- Plan change: the bytecode chapter now has a step widget (the calling convention moves step by step), so plan v2 has five widgets, one over the spec's "two to four"; drop one later if the learner finds them noisy.
- Audit: prose 759 words, 4 figures, average sentence 14.6 words, 6 questions and 6 key entries, 1 lab and its solution. The only flags are the three cross-chapter shape checks a one-chapter file cannot pass. Print: 15 A4 pages, running head and page numbers, the chapter on a fresh page, the widget twin on one page, hints open, the key printed. Screen: answers cloned (7 toggles), zoom on all 4 figures, the stepper reaches step 3 of 4 after two clicks.
- Verified for this chapter: RFC 9669 sections 3.1–3.3, 4, 4.3, 4.3.1, 5.4; the kernel's "Classic BPF vs eBPF" page (A and X plus a hidden frame pointer, ten registers plus a read-only frame pointer, "R1 - R5 are reset to unreadable", the x86-64 register pairing); LWN 599755 (Starovoitov, "internal BPF", the quote); bcc kernel-versions (3.15, 3.16, 3.18, 4.1, 4.2, 4.8, 4.18, 5.5); `verifier.rst` (`R2 !read_ok` format); helper IDs from the repo's `vmlinux.h`; the learner's object compiled and disassembled with clang 23 (27 slots, 216 bytes). Not verified, kept out: the 512-byte stack limit (clang 23 accepts a 600-byte frame; docs fetch blocked).
- Found on the way: the audit's paragraph regex `<p[^>]*>` also matched `<pre>` and SVG `<path>`; fixed in this folder's `audit.py` to `<p(?:\s[^>]*)?>`; the spec's copy still has the bug (add to the spec fixes). The learner's `maps/02-hash-map` solution keys the map by the low 32 bits of `bpf_get_current_pid_tgid()`, the thread ID, so it counts per thread; the chapter says so in a margin note.
- Next: the learner's feedback on the sample; then A or B; then the learnings go into a separate format file (the learner's request), not into `BOOK_STYLE_LEARNING.md`.

## Original complaints, audited (2026-11-11, session 2)

The learner's brief to the first session, checked against `BOOK_STYLE_LEARNING.md`, its sample, and plan v2.

| Complaint or request (learner's words) | Where it is answered | Status |
|---|---|---|
| "too information dense, with too many words" | spec budget 600–800 words per chapter (900 max) and ~9,000 total, against 900–1,600 and ~15,000 in BLOG_STYLE; paragraphs 2–4 sentences; the audit measures it | answered in the rules; not yet tested on the learner |
| "less visualisations" | at least 2 figures per chapter and 1 per 300 words; figures planned before prose; plan v2 has 34 | answered; the sample (3 figures in 2 chapters) misses its own floor |
| "plain mermaid graphs, we can make use of other frameworks" | six figure kinds chosen by job; Mermaid capped at 40%, sequences only; verified CDN list; plan v2 is 9% Mermaid | answered |
| "the blog feels too monotonous" | five chapter shapes, rotating openings, block variety, the monotony test | answered in the rules; the 2-chapter sample cannot show it |
| print as a book or go "full digital", "depending on what's suitable for the topic... the agent has to figure it out" | per-figure widgets are chosen from the topic ("what moves"); the document-level medium defaults to print and changes only if the reader says so | **partly**: the spec lacks a topic test for the medium. Plan v2 decides from the topic: print-first, four widgets |
| "improved font style, color... reading friendly (explore the web for tips)", "a book person" | Literata and JetBrains Mono, cream paper, ink at 14.9:1 contrast, muted text 4.6:1, 17–19 px, line height ~1.5, 60–70 character measure, A4 running head and page numbers; researched from Butterick, Tufte CSS, gwern.net, Distill, MDN and Paged.js | **partly**: the research happened but the spec never cites it; the learner has not seen or printed the result |
| "questions and try outs at the end... answer at the end" so it works printed | check-yourself per chapter, answer key at the back, labs with hint ladders and solutions in the key | answered |
| a new dossier context file under `agent-directory` | `BOOK_STYLE_LEARNING.md` + sample + README entry | done; its example read-with card for the BSD paper has the wrong sections and figure |
| use the Alvar method to probe, then decide branches, depth and purpose; the maths worry | probe done (map in `.alvar/`); three volume shapes; the formal branch stays at four-bit arithmetic, with no proofs | done; choice pending |
| "I dont know which I should read or which I shouldn't" | reading-list triage, rechecked; full pass of the paper list | done |
| "a timeline way, as things started getting added... time based or topic based" | spine plus lineage ribbon by kernel version in every opener, plus the lineage figure; chapter order follows history where dependencies allow (CO-RE, from 2019, precedes the verifier chapters, whose topics date from 2014; the ribbon shows the jump) | answered |
| "personalise the learning" | the learner profile, the probe map, the pain points drawn first, the spine is the learner's own program | answered |

Spec fixes proposed (in `~/workspace/learning/agent-directory`, its own git repo; ask first): correct the example read-with card; cite the typography sources; add a topic test for the medium; make the sample meet the two-figure floor or label it a smoke test of the machinery.

## Reading list triage

The learner's own list, with a verdict each:

| Resource | Verdict | Why, and when |
|---|---|---|
Every row below was rechecked on 2026-11-11 (session 2) by fetching the source; the "Checked" column says what was confirmed. Chapter numbers follow the shared core in *Volume shapes* (3 load and attach, 4 BTF and CO-RE, 5–6 verifier, 7 JIT, 8 hooks, 9 maps).

| Resource | Verdict | Why, and when | Checked |
|---|---|---|---|
| *The BSD Packet Filter* (McCanne and Jacobson, USENIX Winter 1993), printed, **not yet read** | **read at chapter 1**, with its read-with card | first pass: §1, §2 (the network tap, Figure 1), §3.1–3.5 (tree vs CFG, the design criteria in §3.2.2, the pseudo-machine in §3.3, Figure 7 "host foo"); skim Figures 2–3 and §3.6, which are performance results | 11 pages, ~6,600 words; section titles and figure captions read from the PDF. The first draft said "figure 3"; Figure 3 is a performance graph, corrected |
| *hXDP* (Brunella et al., OSDI 2020), printed, **not yet read** | **read at the hXDP chapter**, with its read-with card | first pass: §1, §2 (§2.2 is an XDP primer), §3.1–3.3 (instruction reduction, ISA extension, parallelism), §4.1 (Sephirot, the VLIW soft processor; helper functions and maps in hardware); skim §5. pchaigno wrote a summary of it | sections read from the PDF. The PDF link on pchaigno's list (`usenix.org/system/files/osdi20-brunella.pdf`) returns 404; working copy: `files.usenix.org/s3fs-public/cdn/osdi20-brunella.pdf` |
| pchaigno's research-paper list | **do not read through**; use as the index | 113 entries (2026 venues included), tagged using/improving and by area; see *Paper list: full pass* below for the ~30 that matter here | all 113 titles, venues, tags and one-line summaries parsed |
| armosec, *Reverse Engineering eBPF Programs: A Deep Dive* (Amit Schendel, June 2024, updated Jan 2026) | **read at chapter 2** | covers the registers and calling convention (r0 return, r1–r5 arguments, r6–r9 callee-saved, r10 frame pointer) and the instruction encoding, then reads a compiled object with `llvm-objdump` and reverses a small rootkit (`bpf_probe_write_user`) in Ghidra. It answers probe Q7 directly. Security-flavoured; skip the vendor sidebars | the first draft said "a tour of `bpftool prog dump xlated`": wrong, the post never uses `bpftool`. The "look at it" habit needs another source (docs.ebpf.io, `bpftool` man pages) |
| iovisor `bpf-internals-1` (Suchakra Sharma, May 2015) | **read at chapter 1** | classic BPF only: the machine, the interpreter, the cBPF x86 JIT with its image prologue. eBPF is only promised for part II | headings and text read. **Part II exists** (`bpf-internals-2.md`: eBPF architecture, building programs, maps, the `bpf()` syscall); add it at chapters 2–3 as a dated 2015 view |
| kernel `Documentation/bpf/verifier.rst` | **read at chapter 5**; its last section at chapter 6 | sections: register value tracking (`var_off` tnums, unsigned bounds), direct packet access, pruning, register liveness, and "Understanding eBPF verifier messages", which is the verifier-errors pain point | section list read from docs.kernel.org |
| Cloudflare, *Assembly within! BPF tail calls on x86 and ARM* (Jakub Sitnicki, Oct 2022) | **read at chapter 7** | tail calls on x86-64 and arm64, and mixing BPF function calls with tail calls; a 16-minute read | author, date, section list |
| eunomia, papers list (yunwei37, Oct 2023, updated Aug 2024) | **skip** | 17 papers, each mostly its abstract; 10 are on pchaigno's list; the other 7 (traffic sketching, bpftime, Kgent, syscall security, eBPF vs WebAssembly, an ML IDS, Femto-containers) are applications or the author's own projects. The link given points at SPRIGHT (see below) | entries compared with pchaigno's list |
| eunomia, *Implementing an Inline Hook in C in 5 Minutes* (Jan 2024) | **skip for now**; optional margin note in chapter 8 | user-space function patching in C (`mprotect`, rewrite the function entry); the technique bpftime uses for user-space uprobes. Not kernel eBPF | headings read |
| ebpfchirp, *Are We Really Stuck with One Socket, One Port?* (Teodor Podobnik, Dec 2024) | **later**, networking branch | `sk_lookup` (5.9+). A paid post; Substack offers one free read with sign-up | date, author, gate read from the page |
| LWN | **by pointer only**: 599755 "BPF: the universal in-kernel virtual machine" (Corbet, May 2014) at chapter 2; 740157 "A thorough introduction to eBPF" (Matt Fleming, Dec 2017) as the chapter 0 companion; 794934 "Bounded loops in BPF for the 5.3 kernel" (Marta Rybczyńska, Jul 2019) at chapter 5 | read when a chapter sends you there | titles, authors and dates read |
| Kernel mailing list (`lore.kernel.org/bpf`) | **by pointer only** | when a timeline event needs the original patch series | the archive exists; it serves a bot check, so its content was not fetched |
| docs.ebpf.io | **reference** at chapters 3, 4, 5, 8, 9 | concept pages for ELF, BTF, CO-RE, verifier, trampolines, tail calls, kfuncs, pinning and loops, plus one page per `bpf()` command (`BPF_PROG_LOAD`, `BPF_LINK_CREATE`, ...) for the load-vs-attach chapter | site navigation read |
| kernel docs, `docs.kernel.org/bpf/` | **by pointer** from chapters 1–9 | the index has: verifier, libbpf, BPF standardization (the ISA), BTF, syscall API, helpers, kfuncs, program types, maps, **"Classic BPF vs eBPF"** (chapter 1–2; missed in the first draft), iterators, BPF signing, testing and debugging | index read |
| RFC 9669 | **skim at chapter 2**, section on instruction encoding | the standard; the chapter's figure is drawn from it |
| Liz Rice, *Learning eBPF* (O'Reilly, 2023) | **optional companion** for chapters 3, 7, 8 | the book-shaped tutorial; the free PDF Isovalent used to host returned 404 on 2026-11-11, so find it via Isovalent's site or buy it |
| Brendan Gregg, *BPF Performance Tools* (2019) | **later**, tracing branch | tooling, not mechanism |
| Cilium BPF and XDP reference guide | **later**, networking branch; chapter 7 points at its hook sections | long and datapath-centred |

## Paper list: full pass (2026-11-11, session 2)

All 113 entries on pchaigno's list were sorted against the shared core, the two branches and the pain points. About 30 fit. The rest are applications of eBPF (networking, storage, databases, security, scheduling) and stay out of this volume. ★ = not in the first draft's lane.

| Where | Paper (venue) | Why here |
|---|---|---|
| ch 1, lineage | The BSD Packet Filter (USENIX Winter'93) | the origin, printed |
| ch 1, margin | Safe Kernel Extensions Without Run-Time Checking (OSDI'96) | proof-carrying code, compared with cBPF by its authors |
| ch 1, margin ★ | Swift: A Fast Dynamic Packet Filter (NSDI'08) | a road not taken: a CISC filter ISA with SIMD, proposed as a cBPF alternative |
| ch 1, margin | Jitk (OSDI'14) | formally verified cBPF compilation, the year eBPF arrived |
| ch 2, margin ★ | Formalizing the Linux eBPF Core ISA: A Mechanized Operational Semantics (OOPSLA'26) | the ISA as a formal object; found ISA bugs; bridges to the formal branch |
| ch 4, pain point ★ | Revealing the Unstable Foundations of eBPF-Based Kernel Extensions (EuroSys'25) | kernel API drift for tracing programs: where CO-RE stops helping. Fits the `vmlinux.h`, BTF, CO-RE pain point |
| ch 5–6 | SoK: Challenges and Paths Toward Memory Safety for eBPF (S&P'25) | the survey: what the verifier promises and where it has failed |
| ch 5–6, margin | Validating the eBPF Verifier via State Embedding (OSDI'24); Finding Correctness Bugs in eBPF Verifier with Structured and Sanitized Program (EuroSys'24); ★ eBPF Misbehavior Detection: Fuzzing with a Specification-Based Oracle (SOSP'25) | verifier bugs found by fuzzing; one sentence each |
| ch 5–6, epilogue | Fast, Flexible, and Practical Kernel Extensions = KFlex (SOSP'24); Rex (ATC'25); "untenable" (HotOS'23, not on the list) | the argument about whether the verifier is the right design |
| ch 7 | Jitterbug (OSDI'20); JitSynth (CAV'20) | proving JITs correct; Jitterbug found bugs in the Linux JITs |
| ch 8, "adding points" ★ | cache_ext (SOSP'25); FetchBPF (ATC'24); It's the Kernel's Fault! bpf_fault (SOSP'26); RESYSTANCE (ICDE'26) | case studies of researchers adding new hooks, kfuncs and struct_ops to the kernel. cache_ext is the clearest. Use only if "add more points" means attach points |
| ch 8, margin ★ | Virtualizing eBPF with Late-Binding (OSDI'26) | sharing one hook between tenants |
| hXDP branch | hXDP (OSDI'20); Warp (ATC'22); eHDL (ASPLOS'23) | the only three FPGA papers on the list; already in the lane |
| formal branch | PREVAIL (PLDI'19); Agni (CAV'23); Tnums (CGO'22) and Agni++ (SAS'24), both off-list | the on-ramp core |
| formal branch ★ | Program Analysis Combining Generalized Bit-Level and Word-Level Abstractions (ISSTA'25) | combines the verifier's tnums and ranges into one domain (a reduced product): the exact subject of "how the verifier tracks numbers" |
| formal branch ★ | Prove It to the Kernel: Precise Extension Analysis via Proof-Guided Abstraction Refinement (SOSP'25) | refines the abstract state in user space and hands the kernel a proof; for the deep-branches shape only |
| formal branch | A Flow-Sensitive Refinement Type System for Verifying eBPF Programs (OOPSLA'25); Approximation Enforced Execution (Sec'25) | deep-branches shape only |
| later, networking | SPRIGHT (SIGCOMM'22) | the learner's eunomia link pointed here; an application paper (serverless dataplane on eBPF hooks and shared memory), so it belongs in the networking volume |

## Terms

Filled when the plan is approved. Format, one row per term, read by the audit: `| term | chN |`.

| term | chapter |
|---|---|
| kernel extension | ch0 |
| classic BPF | ch0 |
| accumulator | ch0 |
| control-flow graph | ch0 |
| helper ID | ch1 |
| wide instruction | ch1 |
| calling convention | ch1 |
| program type | ch2 |
| attach type | ch2 |
| bpf_link | ch2 |
| bpffs | ch2 |
| skeleton | ch2 |
| BTF | ch3 |
| CO-RE | ch3 |
| verifier | ch4 |
| pruning | ch4 |
| pointer-or-NULL | ch4 |
| bounded loop | ch4 |
| verifier log | ch5 |
| log level | ch5 |
| tnum | ch6 |
| abstract interpretation | ch6 |
| JIT | ch7 |
| tail call | ch7 |
| trampoline | ch7 |
| fentry | ch8 |
| XDP | ch8 |
| kfunc | ch8 |
| struct_ops | ch8 |
| sched_ext | ch8 |
| ring buffer | ch9 |
| perf buffer | ch9 |
| per-CPU | ch9 |
| selftest | ch10 |
| bpf-next | ch10 |
| patchwork | ch10 |

## Budget

Plan v2: 12 chapters counting prologue and epilogue (the spec caps a volume at 8–12), 600–800 words of prose each, about 9,000 words, about 75 minutes, about 60 A4 pages; 34 figures, 4 step widgets, 3 Mermaid; 2–4 questions per chapter with answers in the key; 10 labs (cut to 8 first if over); 5 read-with cards (BSD 1993, RFC 9669, `verifier.rst`, Agni, hXDP).

## Decisions log

- 2026-11-11: new format spec `BOOK_STYLE_LEARNING.md` chosen over `BLOG_STYLE_LEARNING.md` because the learner found the latter's documents too dense and monotonous and wants a printable book with figures first.
- 2026-11-11: lineage axis is time by kernel version; the ribbon appears in every opener.
- 2026-11-11: the two branches (hardware, formal) are interludes with read-with cards, not full mechanism chapters, until the probe says otherwise.
- 2026-11-11 (session 2): learner chose B, goal kernel contributions; hXDP chapter swapped for the verifier-source lab chapter; contributor volume 2 sketched.
- 2026-11-11 (session 2): plan v2 fitted to the 12-chapter cap by folding the 1993 chapter into the prologue; the numbers (tnum) chapter sits right after the verifier chapters because it answers the "verification at the kernel level" pain point and opens the formal branch; spine is the learner's `maps/02-hash-map` program.
- 2026-11-11 (session 2): every resource the learner gave was refetched and rechecked; three wrong claims in the first triage corrected (armosec content, BSD figure 3, lane provenance), and `bpf-internals-2`, the kernel's "Classic BPF vs eBPF" page and eleven papers added from a full pass of pchaigno's list.
- 2026-11-11: the dossier lives in this repo under `dossier/`; `.alvar/` at the repo root holds learner state. Neither is committed yet; the repo's `.gitignore` does not cover them, which is the learner's call.
- 2026-11-12: the learner said the repo's AGENTS.md skeleton project is abandoned (too basic). The dossier answers only to BOOK_STYLE_LEARNING.md: the "do not spoil `maps/03-ringbuf`, `pinning/*`, `timers_kfuncs/*`" rule is dropped (the ch02 fork was told mid-run; tell the ch06–09 forks when they resume), so ring buffers, pinning, kfuncs and timers can be shown with code. The spine stays `maps/02-hash-map`.

## Open questions the probe settles

1. Which finish line: A alone, A with B, or A with B and both branches. **Open**: three volume shapes (balanced, deep trunk, deep branches) put to the learner 2026-11-11.
2. Verifier depth: `verifier.rst` level, or also reading `verifier.c` around `regsafe()` and `states_equal()`. **Raised** by the pain points: at least the register state (`struct bpf_reg_state`) and the tnum code in `kernel/bpf/tnum.c` at figure level; the full `verifier.c` walk only in the deep-trunk shape.
3. Formal branch: on-ramp only, or also the Agni verification-condition idea. **Depends on 1**; on-ramp unless the learner picks deep branches.
4. Hardware branch: paper-reading only, or an XDP lab on a real NIC driver. **Paper reading**, first read (paper unread).
5. Whether the lineage chapter opens the document. **Opens it**: lineage is blocked and it is the learner's chosen axis.
6. The existing pain. **Answered**; see the reader contract.
