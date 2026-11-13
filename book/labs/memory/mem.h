/* mem.h: what the chapter "Memory you manage" needs on the BPF side, in one header.
 * The macros are those of the v7.2 selftests (tools/testing/selftests/bpf/bpf_experimental.h
 * and libarena/include/bpf_may_goto.h), copied so that the lab builds without a kernel tree. */
#pragma once
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

/* a bpf_list_head or bpf_rb_root holds nodes of type `name`, linked through member `node` */
#define __contains(name, node) __attribute__((btf_decl_tag("contains:" #name ":" #node)))
/* the kernel learns the type from its BTF id; the verifier turns it into a size */
#define bpf_obj_new(type) ((type *)bpf_obj_new(bpf_core_type_id_local(type)))
#define __kptr __attribute__((btf_type_tag("kptr")))

#ifndef container_of
#define container_of(ptr, type, member) \
	((type *)((void *)(ptr) - __builtin_offsetof(type, member)))
#endif

/* may_goto: a loop the verifier lets run until a budget it keeps runs out */
#define can_loop					\
	({ __label__ l_break, l_continue;		\
	bool ret = true;				\
	asm volatile goto("may_goto %l[l_break]"	\
		      :::: l_break);			\
	goto l_continue;				\
	l_break: ret = false;				\
	l_continue:;					\
	ret;						\
	})
