/*
 * Copyright (c) 2004-2010 Apple Inc. All rights reserved.
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
 * NOTICE: This file was modified by SPARTA, Inc. in 2005 to introduce
 * support for mandatory and extensible security protections.  This notice
 * is included in support of clause 2.2 (b) of the Apple Public License,
 * Version 2.0.
 */
/*
** Small modifications to make packing work with CFFI.
*/

#ifndef _SYS_KAUTH_H
#define _SYS_KAUTH_H

#include <sys/appleapiopts.h>
#include <sys/cdefs.h>
#include <mach/boolean.h>
#include <sys/_types.h>
#include <sys/syslimits.h>

#ifdef __APPLE_API_EVOLVING

#define KAUTH_UID_NONE	(~(uid_t)0 - 100)
#define KAUTH_GID_NONE	(~(gid_t)0 - 100)

#include <sys/_types/_guid_t.h>

//#pragma pack(1)
#pragma cffi packed true
typedef struct {
	u_int8_t		sid_kind;
	u_int8_t		sid_authcount;
	u_int8_t		sid_authority[6];
#define KAUTH_NTSID_MAX_AUTHORITIES 16
	u_int32_t	sid_authorities[KAUTH_NTSID_MAX_AUTHORITIES];
} ntsid_t;
//#pragma pack()
#pragma cffi packed false
#define _NTSID_T

#define KAUTH_NTSID_HDRSIZE	(8)
#define KAUTH_NTSID_SIZE(_s)	(KAUTH_NTSID_HDRSIZE + ((_s)->sid_authcount * sizeof(u_int32_t)))

struct kauth_identity_extlookup {
	u_int32_t	el_seqno;
	u_int32_t	el_result;
#define KAUTH_EXTLOOKUP_SUCCESS		0
#define KAUTH_EXTLOOKUP_BADRQ		1
#define KAUTH_EXTLOOKUP_FAILURE		2
#define KAUTH_EXTLOOKUP_FATAL		3
#define KAUTH_EXTLOOKUP_INPROG		100
	u_int32_t	el_flags;
#define KAUTH_EXTLOOKUP_VALID_UID	(1<<0)
#define KAUTH_EXTLOOKUP_VALID_UGUID	(1<<1)
#define KAUTH_EXTLOOKUP_VALID_USID	(1<<2)
#define KAUTH_EXTLOOKUP_VALID_GID	(1<<3)
#define KAUTH_EXTLOOKUP_VALID_GGUID	(1<<4)
#define KAUTH_EXTLOOKUP_VALID_GSID	(1<<5)
#define KAUTH_EXTLOOKUP_WANT_UID	(1<<6)
#define KAUTH_EXTLOOKUP_WANT_UGUID	(1<<7)
#define KAUTH_EXTLOOKUP_WANT_USID	(1<<8)
#define KAUTH_EXTLOOKUP_WANT_GID	(1<<9)
#define KAUTH_EXTLOOKUP_WANT_GGUID	(1<<10)
#define KAUTH_EXTLOOKUP_WANT_GSID	(1<<11)
#define KAUTH_EXTLOOKUP_WANT_MEMBERSHIP	(1<<12)
#define KAUTH_EXTLOOKUP_VALID_MEMBERSHIP (1<<13)
#define KAUTH_EXTLOOKUP_ISMEMBER	(1<<14)
#define KAUTH_EXTLOOKUP_VALID_PWNAM	(1<<15)
#define	KAUTH_EXTLOOKUP_WANT_PWNAM	(1<<16)
#define KAUTH_EXTLOOKUP_VALID_GRNAM	(1<<17)
#define	KAUTH_EXTLOOKUP_WANT_GRNAM	(1<<18)
#define	KAUTH_EXTLOOKUP_VALID_SUPGRPS	(1<<19)
#define	KAUTH_EXTLOOKUP_WANT_SUPGRPS	(1<<20)

	__darwin_pid_t	el_info_pid;
	u_int64_t	el_extend;
	u_int32_t	el_info_reserved_1;

	uid_t		el_uid;
	guid_t		el_uguid;
	u_int32_t	el_uguid_valid;
	ntsid_t		el_usid;
	u_int32_t	el_usid_valid;
	gid_t		el_gid;
	guid_t		el_gguid;
	u_int32_t	el_gguid_valid;
	ntsid_t		el_gsid;
	u_int32_t	el_gsid_valid;
	u_int32_t	el_member_valid;
 	u_int32_t	el_sup_grp_cnt;
 	gid_t		el_sup_groups[NGROUPS_MAX];
};

struct kauth_cache_sizes {
	u_int32_t kcs_group_size;
	u_int32_t kcs_id_size;
};

#define KAUTH_EXTLOOKUP_REGISTER	(0)
#define KAUTH_EXTLOOKUP_RESULT		(1<<0)
#define KAUTH_EXTLOOKUP_WORKER		(1<<1)
#define	KAUTH_EXTLOOKUP_DEREGISTER	(1<<2)
#define	KAUTH_GET_CACHE_SIZES		(1<<3)
#define	KAUTH_SET_CACHE_SIZES		(1<<4)
#define	KAUTH_CLEAR_CACHES		(1<<5)



#if defined(KERNEL) || defined (_SYS_ACL_H)

typedef u_int32_t kauth_ace_rights_t;

struct kauth_ace {
	guid_t		ace_applicable;
	u_int32_t	ace_flags;
#define KAUTH_ACE_KINDMASK		0xf
#define KAUTH_ACE_PERMIT		1
#define KAUTH_ACE_DENY			2
#define KAUTH_ACE_AUDIT			3
#define KAUTH_ACE_ALARM			4
#define	KAUTH_ACE_INHERITED		(1<<4)
#define KAUTH_ACE_FILE_INHERIT		(1<<5)
#define KAUTH_ACE_DIRECTORY_INHERIT	(1<<6)
#define KAUTH_ACE_LIMIT_INHERIT		(1<<7)
#define KAUTH_ACE_ONLY_INHERIT		(1<<8)
#define KAUTH_ACE_SUCCESS		(1<<9)
#define KAUTH_ACE_FAILURE		(1<<10)
/* All flag bits controlling ACE inheritance */
#define KAUTH_ACE_INHERIT_CONTROL_FLAGS		\
		(KAUTH_ACE_FILE_INHERIT |	\
		 KAUTH_ACE_DIRECTORY_INHERIT |	\
		 KAUTH_ACE_LIMIT_INHERIT |	\
		 KAUTH_ACE_ONLY_INHERIT)
	kauth_ace_rights_t ace_rights;
#define KAUTH_ACE_GENERIC_ALL		(1<<21) 
#define KAUTH_ACE_GENERIC_EXECUTE	(1<<22)
#define KAUTH_ACE_GENERIC_WRITE		(1<<23)
#define KAUTH_ACE_GENERIC_READ		(1<<24)

};

#ifndef _KAUTH_ACE
#define _KAUTH_ACE
typedef struct kauth_ace *kauth_ace_t;
#endif


struct kauth_acl {
	u_int32_t	acl_entrycount;
	u_int32_t	acl_flags;
	
	struct kauth_ace acl_ace[1];
};

#define KAUTH_ACL_MAX_ENTRIES		128

#define KAUTH_ACL_FLAGS_PRIVATE	(0xffff)

#define KAUTH_ACL_DEFER_INHERIT	(1<<16)
#define KAUTH_ACL_NO_INHERIT	(1<<17)

#define KAUTH_FILESEC_NOACL ((u_int32_t)(-1))

#define KAUTH_ACL_SIZE(c)	(__offsetof(struct kauth_acl, acl_ace) + ((u_int32_t)(c) != KAUTH_FILESEC_NOACL ? ((c) * sizeof(struct kauth_ace)) : 0))
#define KAUTH_ACL_COPYSIZE(p)	KAUTH_ACL_SIZE((p)->acl_entrycount)


#ifndef _KAUTH_ACL
#define _KAUTH_ACL
typedef struct kauth_acl *kauth_acl_t;
#endif


struct kauth_filesec {
	u_int32_t	fsec_magic;
#define KAUTH_FILESEC_MAGIC	0x012cc16d
	guid_t		fsec_owner;
	guid_t		fsec_group;

	struct kauth_acl fsec_acl;
};

#define fsec_entrycount fsec_acl.acl_entrycount
#define fsec_flags 	fsec_acl.acl_flags
#define fsec_ace	fsec_acl.acl_ace
#define KAUTH_FILESEC_FLAGS_PRIVATE	KAUTH_ACL_FLAGS_PRIVATE
#define KAUTH_FILESEC_DEFER_INHERIT	KAUTH_ACL_DEFER_INHERIT
#define KAUTH_FILESEC_NO_INHERIT	KAUTH_ACL_NO_INHERIT
#define KAUTH_FILESEC_NONE	((kauth_filesec_t)0)
#define KAUTH_FILESEC_WANTED	((kauth_filesec_t)1)
	
#ifndef _KAUTH_FILESEC
#define _KAUTH_FILESEC
typedef struct kauth_filesec *kauth_filesec_t;
#endif

#define KAUTH_FILESEC_SIZE(c)		(__offsetof(struct kauth_filesec, fsec_acl) + __offsetof(struct kauth_acl, acl_ace) + (c) * sizeof(struct kauth_ace))
#define KAUTH_FILESEC_COPYSIZE(p)	KAUTH_FILESEC_SIZE(((p)->fsec_entrycount == KAUTH_FILESEC_NOACL) ? 0 : (p)->fsec_entrycount)
#define KAUTH_FILESEC_COUNT(s)		(((s)  - KAUTH_FILESEC_SIZE(0)) / sizeof(struct kauth_ace))
#define KAUTH_FILESEC_VALID(s)		((s) >= KAUTH_FILESEC_SIZE(0) && (((s) - KAUTH_FILESEC_SIZE(0)) % sizeof(struct kauth_ace)) == 0)

#define KAUTH_FILESEC_XATTR	"com.apple.system.Security"

#define	KAUTH_ENDIAN_HOST	0x00000001
#define	KAUTH_ENDIAN_DISK	0x00000002

#endif /* KERNEL || <sys/acl.h> */



#if defined(KERNEL) || defined (_SYS_ACL_H)
#define KAUTH_VNODE_READ_DATA			(1<<1)
#define KAUTH_VNODE_LIST_DIRECTORY		KAUTH_VNODE_READ_DATA
#define KAUTH_VNODE_WRITE_DATA			(1<<2)
#define KAUTH_VNODE_ADD_FILE			KAUTH_VNODE_WRITE_DATA
#define KAUTH_VNODE_EXECUTE			(1<<3)
#define KAUTH_VNODE_SEARCH			KAUTH_VNODE_EXECUTE
#define KAUTH_VNODE_DELETE			(1<<4)
#define KAUTH_VNODE_APPEND_DATA			(1<<5)
#define KAUTH_VNODE_ADD_SUBDIRECTORY		KAUTH_VNODE_APPEND_DATA
#define KAUTH_VNODE_DELETE_CHILD		(1<<6)
#define KAUTH_VNODE_READ_ATTRIBUTES		(1<<7)
#define KAUTH_VNODE_WRITE_ATTRIBUTES		(1<<8)
#define KAUTH_VNODE_READ_EXTATTRIBUTES		(1<<9)
#define KAUTH_VNODE_WRITE_EXTATTRIBUTES		(1<<10)
#define KAUTH_VNODE_READ_SECURITY		(1<<11)
#define KAUTH_VNODE_WRITE_SECURITY		(1<<12)
#define KAUTH_VNODE_TAKE_OWNERSHIP		(1<<13)

#define KAUTH_VNODE_CHANGE_OWNER		KAUTH_VNODE_TAKE_OWNERSHIP

#define KAUTH_VNODE_SYNCHRONIZE			(1<<20)

#define KAUTH_VNODE_LINKTARGET			(1<<25)

#define KAUTH_VNODE_CHECKIMMUTABLE		(1<<26)

#define KAUTH_VNODE_ACCESS			(1<<31)

#define KAUTH_VNODE_NOIMMUTABLE			(1<<30)


#define KAUTH_VNODE_SEARCHBYANYONE		(1<<29)


#define	KAUTH_INVALIDATE_CACHED_RIGHTS		((kauth_action_t)~0)



#define KAUTH_VNODE_GENERIC_READ_BITS	(KAUTH_VNODE_READ_DATA |		\
					KAUTH_VNODE_READ_ATTRIBUTES |		\
					KAUTH_VNODE_READ_EXTATTRIBUTES |	\
					KAUTH_VNODE_READ_SECURITY)
 
#define KAUTH_VNODE_GENERIC_WRITE_BITS	(KAUTH_VNODE_WRITE_DATA |		\
					KAUTH_VNODE_APPEND_DATA |		\
					KAUTH_VNODE_DELETE |			\
					KAUTH_VNODE_DELETE_CHILD |		\
					KAUTH_VNODE_WRITE_ATTRIBUTES |		\
					KAUTH_VNODE_WRITE_EXTATTRIBUTES |	\
					KAUTH_VNODE_WRITE_SECURITY)
 
#define KAUTH_VNODE_GENERIC_EXECUTE_BITS (KAUTH_VNODE_EXECUTE)
 
#define KAUTH_VNODE_GENERIC_ALL_BITS	(KAUTH_VNODE_GENERIC_READ_BITS |	\
					KAUTH_VNODE_GENERIC_WRITE_BITS |	\
					KAUTH_VNODE_GENERIC_EXECUTE_BITS)
 
#define KAUTH_VNODE_WRITE_RIGHTS	(KAUTH_VNODE_ADD_FILE |				\
					KAUTH_VNODE_ADD_SUBDIRECTORY |			\
					KAUTH_VNODE_DELETE_CHILD |			\
					KAUTH_VNODE_WRITE_DATA |			\
					KAUTH_VNODE_APPEND_DATA |			\
					KAUTH_VNODE_DELETE |				\
					KAUTH_VNODE_WRITE_ATTRIBUTES |			\
					KAUTH_VNODE_WRITE_EXTATTRIBUTES |		\
					KAUTH_VNODE_WRITE_SECURITY |			\
	    				KAUTH_VNODE_TAKE_OWNERSHIP |			\
					KAUTH_VNODE_LINKTARGET |			\
					KAUTH_VNODE_CHECKIMMUTABLE)


#endif /* KERNEL || <sys/acl.h> */


#endif /* __APPLE_API_EVOLVING */
#endif /* _SYS_KAUTH_H */

