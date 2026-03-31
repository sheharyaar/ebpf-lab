#ifndef __RINGBUF_H
#define __RINGBUF_H

#define TASK_COMM_LEN 16

struct event {
	__u32 pid;
	char comm[TASK_COMM_LEN];
};

#endif /* __RINGBUF_H */
