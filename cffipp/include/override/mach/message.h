/*
 * Copyright (c) 2000-2005 Apple Computer, Inc. All rights reserved.
 *
 * @APPLE_OSREFERENCE_LICENSE_HEADER_START@
 * 
 * This file contains Original Code and/or Modifications of Original Code
 * as defined in and that are subject to the Apple Public Source License
 * Version 2.0 (the 'License'). You may not use this file except in
 * compliance with the License. The rights granted to you under the License
 * may not be used to create, or enable the creation or redistribution of,
 * unlawful or unlicensed copies of an Apple operating system, or to
 * circumvent, violate, or enable the circumvention or violation of, any
 * terms of an Apple operating system software license agreement.
 * 
 * Please obtain a copy of the License at
 * http://www.opensource.apple.com/apsl/ and read it before using this file.
 * 
 * The Original Code and all software distributed under the License are
 * distributed on an 'AS IS' basis, WITHOUT WARRANTY OF ANY KIND, EITHER
 * EXPRESS OR IMPLIED, AND APPLE HEREBY DISCLAIMS ALL SUCH WARRANTIES,
 * INCLUDING WITHOUT LIMITATION, ANY WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE, QUIET ENJOYMENT OR NON-INFRINGEMENT.
 * Please see the License for the specific language governing rights and
 * limitations under the License.
 * 
 * @APPLE_OSREFERENCE_LICENSE_HEADER_END@
 */
/*
 * @OSF_COPYRIGHT@
 */
/* 
 * Mach Operating System
 * Copyright (c) 1991,1990,1989,1988,1987 Carnegie Mellon University
 * All Rights Reserved.
 * 
 * Permission to use, copy, modify and distribute this software and its
 * documentation is hereby granted, provided that both the copyright
 * notice and this permission notice appear in all copies of the
 * software, derivative works or modified versions, and any portions
 * thereof, and that both notices appear in supporting documentation.
 * 
 * CARNEGIE MELLON ALLOWS FREE USE OF THIS SOFTWARE IN ITS "AS IS"
 * CONDITION.  CARNEGIE MELLON DISCLAIMS ANY LIABILITY OF ANY KIND FOR
 * ANY DAMAGES WHATSOEVER RESULTING FROM THE USE OF THIS SOFTWARE.
 * 
 * Carnegie Mellon requests users of this software to return to
 * 
 *  Software Distribution Coordinator  or  Software.Distribution@CS.CMU.EDU
 *  School of Computer Science
 *  Carnegie Mellon University
 *  Pittsburgh PA 15213-3890
 * 
 * any improvements or extensions that they make and grant Carnegie Mellon
 * the rights to redistribute these changes.
 */
/*
 * NOTICE: This file was modified by McAfee Research in 2004 to introduce
 * support for mandatory and extensible security protections.  This notice
 * is included in support of clause 2.2 (b) of the Apple Public License,
 * Version 2.0.
 * Copyright (c) 2005 SPARTA, Inc.
 */
/*
 */
/*
** Small modifications to make packing work with CFFI.
*/

#ifndef	_MACH_MESSAGE_H_
#define _MACH_MESSAGE_H_

#include <stdint.h>
#include <mach/port.h>
#include <mach/boolean.h>
#include <mach/kern_return.h>
#include <mach/machine/vm_types.h>

#include <sys/cdefs.h>
#include <sys/appleapiopts.h>
#include <Availability.h>

typedef natural_t mach_msg_timeout_t;

#define MACH_MSG_TIMEOUT_NONE		((mach_msg_timeout_t) 0)

#define MACH_MSGH_BITS_ZERO		0x00000000

#define MACH_MSGH_BITS_REMOTE_MASK	0x0000001f
#define MACH_MSGH_BITS_LOCAL_MASK	0x00001f00
#define MACH_MSGH_BITS_VOUCHER_MASK	0x001f0000

#define	MACH_MSGH_BITS_PORTS_MASK		\
		(MACH_MSGH_BITS_REMOTE_MASK |	\
		 MACH_MSGH_BITS_LOCAL_MASK |	\
		 MACH_MSGH_BITS_VOUCHER_MASK)

#define MACH_MSGH_BITS_COMPLEX		0x80000000U

#define MACH_MSGH_BITS_USER             0x801f1f1fU

#define	MACH_MSGH_BITS_RAISEIMP		0x20000000U
#define MACH_MSGH_BITS_DENAP		MACH_MSGH_BITS_RAISEIMP

#define	MACH_MSGH_BITS_IMPHOLDASRT	0x10000000U
#define MACH_MSGH_BITS_DENAPHOLDASRT	MACH_MSGH_BITS_IMPHOLDASRT

#define	MACH_MSGH_BITS_CIRCULAR		0x10000000U

#define	MACH_MSGH_BITS_USED		0xb01f1f1fU

#define MACH_MSGH_BITS(remote, local)  /* legacy */		\
		((remote) | ((local) << 8))
#define	MACH_MSGH_BITS_SET_PORTS(remote, local, voucher)	\
	(((remote) & MACH_MSGH_BITS_REMOTE_MASK) | 		\
	 (((local) << 8) & MACH_MSGH_BITS_LOCAL_MASK) | 	\
	 (((voucher) << 16) & MACH_MSGH_BITS_VOUCHER_MASK))
#define MACH_MSGH_BITS_SET(remote, local, voucher, other)	\
	(MACH_MSGH_BITS_SET_PORTS((remote), (local), (voucher)) \
	 | ((other) &~ MACH_MSGH_BITS_PORTS_MASK))

#define	MACH_MSGH_BITS_REMOTE(bits)				\
		((bits) & MACH_MSGH_BITS_REMOTE_MASK)
#define	MACH_MSGH_BITS_LOCAL(bits)				\
		(((bits) & MACH_MSGH_BITS_LOCAL_MASK) >> 8)
#define	MACH_MSGH_BITS_VOUCHER(bits)				\
		(((bits) & MACH_MSGH_BITS_VOUCHER_MASK) >> 16)
#define	MACH_MSGH_BITS_PORTS(bits)				\
	((bits) & MACH_MSGH_BITS_PORTS_MASK)
#define	MACH_MSGH_BITS_OTHER(bits)				\
		((bits) &~ MACH_MSGH_BITS_PORTS_MASK)

#define MACH_MSGH_BITS_HAS_REMOTE(bits)				\
	(MACH_MSGH_BITS_REMOTE(bits) != MACH_MSGH_BITS_ZERO)
#define MACH_MSGH_BITS_HAS_LOCAL(bits)				\
	(MACH_MSGH_BITS_LOCAL(bits) != MACH_MSGH_BITS_ZERO)
#define MACH_MSGH_BITS_HAS_VOUCHER(bits)			\
	(MACH_MSGH_BITS_VOUCHER(bits) != MACH_MSGH_BITS_ZERO)
#define MACH_MSGH_BITS_IS_COMPLEX(bits)				\
	(((bits) & MACH_MSGH_BITS_COMPLEX) != MACH_MSGH_BITS_ZERO)

#define MACH_MSGH_BITS_RAISED_IMPORTANCE(bits)			\
	(((bits) & MACH_MSGH_BITS_RAISEIMP) != MACH_MSGH_BITS_ZERO)
#define MACH_MSGH_BITS_HOLDS_IMPORTANCE_ASSERTION(bits)		\
	(((bits) & MACH_MSGH_BITS_IMPHOLDASRT) != MACH_MSGH_BITS_ZERO)

typedef unsigned int mach_msg_bits_t;
typedef	natural_t mach_msg_size_t;
typedef integer_t mach_msg_id_t;


#define MACH_MSG_SIZE_NULL (mach_msg_size_t *) 0

typedef unsigned int mach_msg_type_name_t;

#define MACH_MSG_TYPE_MOVE_RECEIVE	16
#define MACH_MSG_TYPE_MOVE_SEND		17
#define MACH_MSG_TYPE_MOVE_SEND_ONCE	18
#define MACH_MSG_TYPE_COPY_SEND		19
#define MACH_MSG_TYPE_MAKE_SEND		20
#define MACH_MSG_TYPE_MAKE_SEND_ONCE	21
#define MACH_MSG_TYPE_COPY_RECEIVE	22
#define MACH_MSG_TYPE_DISPOSE_RECEIVE	24
#define MACH_MSG_TYPE_DISPOSE_SEND	25
#define MACH_MSG_TYPE_DISPOSE_SEND_ONCE 26

typedef unsigned int mach_msg_copy_options_t;

#define MACH_MSG_PHYSICAL_COPY		0
#define MACH_MSG_VIRTUAL_COPY   	1
#define MACH_MSG_ALLOCATE		2
#define MACH_MSG_OVERWRITE		3
#ifdef  MACH_KERNEL
#define MACH_MSG_KALLOC_COPY_T		4
#endif  /* MACH_KERNEL */

typedef unsigned int mach_msg_descriptor_type_t;

#define MACH_MSG_PORT_DESCRIPTOR 		0
#define MACH_MSG_OOL_DESCRIPTOR  		1
#define MACH_MSG_OOL_PORTS_DESCRIPTOR 		2
#define MACH_MSG_OOL_VOLATILE_DESCRIPTOR  	3

//#pragma pack(4)

typedef struct
{
  natural_t			pad1;
  mach_msg_size_t		pad2;
  unsigned int			pad3 : 24;
  mach_msg_descriptor_type_t	type : 8;
} mach_msg_type_descriptor_t;

typedef struct
{
  mach_port_t			name;
  mach_msg_size_t		pad1;
  unsigned int			pad2 : 16;
  mach_msg_type_name_t		disposition : 8;
  mach_msg_descriptor_type_t	type : 8;
} mach_msg_port_descriptor_t;

typedef struct
{
  uint32_t			address;
  mach_msg_size_t       	size;
  boolean_t     		deallocate: 8;
  mach_msg_copy_options_t       copy: 8;
  unsigned int     		pad1: 8;
  mach_msg_descriptor_type_t    type: 8;
} mach_msg_ool_descriptor32_t;

typedef struct
{
  uint64_t			address;
  boolean_t     		deallocate: 8;
  mach_msg_copy_options_t       copy: 8;
  unsigned int     		pad1: 8;
  mach_msg_descriptor_type_t    type: 8;
  mach_msg_size_t       	size;
} mach_msg_ool_descriptor64_t;

typedef struct
{
  void*				address;
#if !defined(__LP64__)
  mach_msg_size_t       	size;
#endif
  boolean_t     		deallocate: 8;
  mach_msg_copy_options_t       copy: 8;
  unsigned int     		pad1: 8;
  mach_msg_descriptor_type_t    type: 8;
#if defined(__LP64__)
  mach_msg_size_t       	size;
#endif
} mach_msg_ool_descriptor_t;

typedef struct
{
  uint32_t			address;
  mach_msg_size_t		count;
  boolean_t     		deallocate: 8;
  mach_msg_copy_options_t       copy: 8;
  mach_msg_type_name_t		disposition : 8;
  mach_msg_descriptor_type_t	type : 8;
} mach_msg_ool_ports_descriptor32_t;

typedef struct
{
  uint64_t			address;
  boolean_t     		deallocate: 8;
  mach_msg_copy_options_t       copy: 8;
  mach_msg_type_name_t		disposition : 8;
  mach_msg_descriptor_type_t	type : 8;
  mach_msg_size_t		count;
} mach_msg_ool_ports_descriptor64_t;

typedef struct
{
  void*				address;
#if !defined(__LP64__)
  mach_msg_size_t		count;
#endif
  boolean_t     		deallocate: 8;
  mach_msg_copy_options_t       copy: 8;
  mach_msg_type_name_t		disposition : 8;
  mach_msg_descriptor_type_t	type : 8;
#if defined(__LP64__)
  mach_msg_size_t		count;
#endif
} mach_msg_ool_ports_descriptor_t;

typedef union
{
  mach_msg_port_descriptor_t		port;
  mach_msg_ool_descriptor_t		out_of_line;
  mach_msg_ool_ports_descriptor_t	ool_ports;
  mach_msg_type_descriptor_t		type;
} mach_msg_descriptor_t;

typedef struct
{
        mach_msg_size_t msgh_descriptor_count;
} mach_msg_body_t;

#define MACH_MSG_BODY_NULL (mach_msg_body_t *) 0
#define MACH_MSG_DESCRIPTOR_NULL (mach_msg_descriptor_t *) 0

typedef	struct 
{
  mach_msg_bits_t	msgh_bits;
  mach_msg_size_t	msgh_size;
  mach_port_t		msgh_remote_port;
  mach_port_t		msgh_local_port;
  mach_port_name_t	msgh_voucher_port;
  mach_msg_id_t		msgh_id;
} mach_msg_header_t;

#define	msgh_reserved		msgh_voucher_port
#define MACH_MSG_NULL	(mach_msg_header_t *) 0

typedef struct
{
        mach_msg_header_t       header;
        mach_msg_body_t         body;
} mach_msg_base_t;

typedef	unsigned int mach_msg_trailer_type_t;

#define	MACH_MSG_TRAILER_FORMAT_0	0

typedef	unsigned int mach_msg_trailer_size_t;
typedef char *mach_msg_trailer_info_t;

typedef struct 
{
  mach_msg_trailer_type_t	msgh_trailer_type;
  mach_msg_trailer_size_t	msgh_trailer_size;
} mach_msg_trailer_t;

typedef struct
{
  mach_msg_trailer_type_t       msgh_trailer_type;
  mach_msg_trailer_size_t       msgh_trailer_size;
  mach_port_seqno_t             msgh_seqno;
} mach_msg_seqno_trailer_t;

typedef struct
{
  unsigned int			val[2];
} security_token_t;

typedef struct 
{
  mach_msg_trailer_type_t	msgh_trailer_type;
  mach_msg_trailer_size_t	msgh_trailer_size;
  mach_port_seqno_t		msgh_seqno;
  security_token_t		msgh_sender;
} mach_msg_security_trailer_t;

typedef struct
{
  unsigned int			val[8];
} audit_token_t;

typedef struct 
{
  mach_msg_trailer_type_t	msgh_trailer_type;
  mach_msg_trailer_size_t	msgh_trailer_size;
  mach_port_seqno_t		msgh_seqno;
  security_token_t		msgh_sender;
  audit_token_t			msgh_audit;
} mach_msg_audit_trailer_t;

typedef struct 
{
  mach_msg_trailer_type_t	msgh_trailer_type;
  mach_msg_trailer_size_t	msgh_trailer_size;
  mach_port_seqno_t		msgh_seqno;
  security_token_t		msgh_sender;
  audit_token_t			msgh_audit;
  mach_port_context_t		msgh_context;
} mach_msg_context_trailer_t;



typedef struct
{
  mach_port_name_t sender;
} msg_labels_t;

typedef struct
{
  mach_msg_trailer_type_t       msgh_trailer_type;
  mach_msg_trailer_size_t       msgh_trailer_size;
  mach_port_seqno_t             msgh_seqno;
  security_token_t              msgh_sender;
  audit_token_t                 msgh_audit;
  mach_port_context_t		msgh_context;
  int				msgh_ad;
  msg_labels_t                  msgh_labels;
} mach_msg_mac_trailer_t;


#define MACH_MSG_TRAILER_MINIMUM_SIZE  sizeof(mach_msg_trailer_t)

typedef mach_msg_mac_trailer_t mach_msg_max_trailer_t;
#define MAX_TRAILER_SIZE ((mach_msg_size_t)sizeof(mach_msg_max_trailer_t))

typedef mach_msg_security_trailer_t mach_msg_format_0_trailer_t;

#define MACH_MSG_TRAILER_FORMAT_0_SIZE sizeof(mach_msg_format_0_trailer_t)

#define   KERNEL_SECURITY_TOKEN_VALUE  { {0, 1} }
extern security_token_t KERNEL_SECURITY_TOKEN;

#define   KERNEL_AUDIT_TOKEN_VALUE  { {0, 0, 0, 0, 0, 0, 0, 0} }
extern audit_token_t KERNEL_AUDIT_TOKEN;

typedef	integer_t mach_msg_options_t;

typedef struct
{
  mach_msg_header_t	header;
} mach_msg_empty_send_t;

typedef struct
{
  mach_msg_header_t	header;
  mach_msg_trailer_t	trailer;
} mach_msg_empty_rcv_t;

typedef union
{
  mach_msg_empty_send_t	send;
  mach_msg_empty_rcv_t	rcv;
} mach_msg_empty_t;

//#pragma pack()

#define round_msg(x)	(((mach_msg_size_t)(x) + sizeof (natural_t) - 1) & \
				~(sizeof (natural_t) - 1))

#define	MACH_MSG_SIZE_MAX	((mach_msg_size_t) ~0)

#if defined(__APPLE_API_PRIVATE)
#define	MACH_MSG_SIZE_RELIABLE	((mach_msg_size_t) 256 * 1024)
#endif
#define MACH_MSGH_KIND_NORMAL		0x00000000
#define MACH_MSGH_KIND_NOTIFICATION	0x00000001
#define	msgh_kind			msgh_seqno
#define mach_msg_kind_t			mach_port_seqno_t

typedef natural_t mach_msg_type_size_t;
typedef natural_t mach_msg_type_number_t;

#define MACH_MSG_TYPE_PORT_NONE		0

#define MACH_MSG_TYPE_PORT_NAME		15
#define MACH_MSG_TYPE_PORT_RECEIVE	MACH_MSG_TYPE_MOVE_RECEIVE
#define MACH_MSG_TYPE_PORT_SEND		MACH_MSG_TYPE_MOVE_SEND
#define MACH_MSG_TYPE_PORT_SEND_ONCE	MACH_MSG_TYPE_MOVE_SEND_ONCE

#define MACH_MSG_TYPE_LAST		22

#define MACH_MSG_TYPE_POLYMORPHIC	((mach_msg_type_name_t) -1)

#define MACH_MSG_TYPE_PORT_ANY(x)			\
	(((x) >= MACH_MSG_TYPE_MOVE_RECEIVE) &&		\
	 ((x) <= MACH_MSG_TYPE_MAKE_SEND_ONCE))

#define	MACH_MSG_TYPE_PORT_ANY_SEND(x)			\
	(((x) >= MACH_MSG_TYPE_MOVE_SEND) &&		\
	 ((x) <= MACH_MSG_TYPE_MAKE_SEND_ONCE))

#define	MACH_MSG_TYPE_PORT_ANY_RIGHT(x)			\
	(((x) >= MACH_MSG_TYPE_MOVE_RECEIVE) &&		\
	 ((x) <= MACH_MSG_TYPE_MOVE_SEND_ONCE))

typedef integer_t mach_msg_option_t;

#define MACH_MSG_OPTION_NONE	0x00000000

#define	MACH_SEND_MSG		0x00000001
#define	MACH_RCV_MSG		0x00000002

#define MACH_RCV_LARGE		0x00000004
#define MACH_RCV_LARGE_IDENTITY	0x00000008

#define MACH_SEND_TIMEOUT	0x00000010
#define MACH_SEND_INTERRUPT	0x00000040
#define MACH_SEND_NOTIFY	0x00000080
#define MACH_SEND_ALWAYS	0x00010000
#define MACH_SEND_TRAILER	0x00020000
#define MACH_SEND_NOIMPORTANCE  0x00040000
#define MACH_SEND_NODENAP	MACH_SEND_NOIMPORTANCE
#define MACH_SEND_IMPORTANCE	0x00080000


#define MACH_RCV_TIMEOUT	0x00000100
#define MACH_RCV_NOTIFY		0x00000200
#define MACH_RCV_INTERRUPT	0x00000400
#define MACH_RCV_VOUCHER	0x00000800
#define MACH_RCV_OVERWRITE	0x00001000

#define MACH_RCV_TRAILER_NULL   0
#define MACH_RCV_TRAILER_SEQNO  1
#define MACH_RCV_TRAILER_SENDER 2
#define MACH_RCV_TRAILER_AUDIT  3
#define MACH_RCV_TRAILER_CTX    4
#define MACH_RCV_TRAILER_AV     7
#define MACH_RCV_TRAILER_LABELS 8

#define MACH_RCV_TRAILER_TYPE(x)     (((x) & 0xf) << 28) 
#define MACH_RCV_TRAILER_ELEMENTS(x) (((x) & 0xf) << 24)  
#define MACH_RCV_TRAILER_MASK 	     ((0xf << 24))

#define GET_RCV_ELEMENTS(y) (((y) >> 24) & 0xf)


#define REQUESTED_TRAILER_SIZE_NATIVE(y)			\
	((mach_msg_trailer_size_t)				\
	 ((GET_RCV_ELEMENTS(y) == MACH_RCV_TRAILER_NULL) ?	\
	  sizeof(mach_msg_trailer_t) :				\
	  ((GET_RCV_ELEMENTS(y) == MACH_RCV_TRAILER_SEQNO) ?	\
	   sizeof(mach_msg_seqno_trailer_t) :			\
	  ((GET_RCV_ELEMENTS(y) == MACH_RCV_TRAILER_SENDER) ?	\
	   sizeof(mach_msg_security_trailer_t) :		\
	   ((GET_RCV_ELEMENTS(y) == MACH_RCV_TRAILER_AUDIT) ?	\
	    sizeof(mach_msg_audit_trailer_t) :      		\
	    ((GET_RCV_ELEMENTS(y) == MACH_RCV_TRAILER_CTX) ?	\
	     sizeof(mach_msg_context_trailer_t) :      		\
	     ((GET_RCV_ELEMENTS(y) == MACH_RCV_TRAILER_AV) ?	\
	      sizeof(mach_msg_mac_trailer_t) :      		\
	     sizeof(mach_msg_max_trailer_t))))))))


#define REQUESTED_TRAILER_SIZE(y) REQUESTED_TRAILER_SIZE_NATIVE(y)

typedef kern_return_t mach_msg_return_t;

#define MACH_MSG_SUCCESS		0x00000000


#define	MACH_MSG_MASK			0x00003e00
#define	MACH_MSG_IPC_SPACE		0x00002000
#define	MACH_MSG_VM_SPACE		0x00001000
#define	MACH_MSG_IPC_KERNEL		0x00000800
#define	MACH_MSG_VM_KERNEL		0x00000400

#define MACH_SEND_IN_PROGRESS		0x10000001
#define MACH_SEND_INVALID_DATA		0x10000002
#define MACH_SEND_INVALID_DEST		0x10000003
#define MACH_SEND_TIMED_OUT		0x10000004
#define MACH_SEND_INVALID_VOUCHER	0x10000005
#define MACH_SEND_INTERRUPTED		0x10000007
#define MACH_SEND_MSG_TOO_SMALL		0x10000008
#define MACH_SEND_INVALID_REPLY		0x10000009
#define MACH_SEND_INVALID_RIGHT		0x1000000a
#define MACH_SEND_INVALID_NOTIFY	0x1000000b
#define MACH_SEND_INVALID_MEMORY	0x1000000c
#define MACH_SEND_NO_BUFFER		0x1000000d
#define MACH_SEND_TOO_LARGE		0x1000000e
#define MACH_SEND_INVALID_TYPE		0x1000000f
#define MACH_SEND_INVALID_HEADER	0x10000010
#define MACH_SEND_INVALID_TRAILER	0x10000011
#define MACH_SEND_INVALID_RT_OOL_SIZE	0x10000015

#define MACH_RCV_IN_PROGRESS		0x10004001
#define MACH_RCV_INVALID_NAME		0x10004002
#define MACH_RCV_TIMED_OUT		0x10004003
#define MACH_RCV_TOO_LARGE		0x10004004
#define MACH_RCV_INTERRUPTED		0x10004005
#define MACH_RCV_PORT_CHANGED		0x10004006
#define MACH_RCV_INVALID_NOTIFY		0x10004007
#define MACH_RCV_INVALID_DATA		0x10004008
#define MACH_RCV_PORT_DIED		0x10004009
#define	MACH_RCV_IN_SET			0x1000400a
#define	MACH_RCV_HEADER_ERROR		0x1000400b
#define	MACH_RCV_BODY_ERROR		0x1000400c
#define	MACH_RCV_INVALID_TYPE		0x1000400d
#define	MACH_RCV_SCATTER_SMALL		0x1000400e
#define MACH_RCV_INVALID_TRAILER	0x1000400f
#define MACH_RCV_IN_PROGRESS_TIMED      0x10004011


__BEGIN_DECLS

__WATCHOS_PROHIBITED __TVOS_PROHIBITED
extern mach_msg_return_t	mach_msg_overwrite(
					mach_msg_header_t *msg,
					mach_msg_option_t option,
					mach_msg_size_t send_size,
					mach_msg_size_t rcv_size,
					mach_port_name_t rcv_name,
					mach_msg_timeout_t timeout,
					mach_port_name_t notify,
					mach_msg_header_t *rcv_msg,
					mach_msg_size_t rcv_limit);


__WATCHOS_PROHIBITED __TVOS_PROHIBITED
extern mach_msg_return_t	mach_msg(
					mach_msg_header_t *msg,
					mach_msg_option_t option,
					mach_msg_size_t send_size,
					mach_msg_size_t rcv_size,
					mach_port_name_t rcv_name,
					mach_msg_timeout_t timeout,
					mach_port_name_t notify);

__WATCHOS_PROHIBITED __TVOS_PROHIBITED
extern kern_return_t		mach_voucher_deallocate(
					mach_port_name_t voucher);


__END_DECLS

#endif	/* _MACH_MESSAGE_H_ */

