# AGENTS.md

## Project overview
It's a playground for the human programmer to learn and implement eBPF programs. For C programs libbpf is to be used and ebpf-go for Go programs. The human programmer can ask for both Go and C variants of the same exercise. The repository will have exercises that will be implemented by the human programmer and the agent will assist in generating skeleton code. Each program will have accompanying README.md for the exercise which the human reads and implements.

## Skeleton Definition
Skeleton code must include:
- Program entry points (empty SEC macros for C, equivalent for Go)
- Required map definitions
  - include maps only if the program cannot compile or attach without them
  - do not predefine helper maps “just in case”
- Function signatures
- Build integration
- Do not add the SEC paths, add comments to guide the user to find the sec path

Skeleton must NOT include:
- Business logic
- Loops or condition logic beyond stubs
- Comments that reveal solution approach

Each exercise should contain:
- ebpf program (C or Go)
- Include a user-space loader only when:
  - data needs to be read from maps, OR
  - events are emitted (perf/ring buffer)
- Makefile entry
- README.md with the sections: `Exercise Problem`, `Theory`, `Tasks`, `Expected Results`.

Use consistent naming:
- <exercise>.bpf.c for eBPF programs
- <exercise>.go for Go variants

## Do
- group the programs on the basis of the tracing they do (e.g, cpu, memory) or on the basis of concept that exercise teaches and the exercise level starting from 01. Examples: `cpu/01-<exercise>`, `bpf_maps/01-<exercise>`.
- generate skeleton code which the human programmer will implement
- add build steps to Makefile to be tested using `make <test>`
  - <test> corresponds to the exercise directory name.
  - Running `make <test>` should:
    - build the program
    - attach (if applicable)
    - exit cleanly without errors
- default to C variant unless specified
- use CO-RE / libbpf
- update the root README.md with the added exercise as a table entry

## Don't
- build the entire directory
- do not over-engineer abstractions
- do not implement the exercise logic
- mention the SEC path, add comments to guide the user to find the sec path

## Example

Exercise: cpu/01-trace-exec

Expected skeleton:
- tracepoint program attached to sched_process_exec
- empty handler function
- minimal Makefile entry

## Commands

- `make <test>` to run test for a program

## Coding Style
- kernel module style for .c and .h files
- normal go format for .go files
- use libbpf for C programs and eBPF-go for go programs

## Safety and permissions

Allowed without prompt:
- read files, list files
- test programs

Ask first: 
- package installs,
- git push
- deleting files, chmod
- running full build

## Project structure
- Makefile for building the programs

## When stuck
- ask a clarifying question, propose a short plan.

