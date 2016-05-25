/*
 * Portions Copyright (c) 2007-2015 by Apple Inc.. All rights reserved.
 *
 * @APPLE_LICENSE_HEADER_START@
 * 
 * This file contains Original Code and/or Modifications of Original Code
 * as defined in and that are subject to the Apple Public Source License
 * Version 2.0 (the 'License'). You may not use this file except in
 * compliance with the License. Please obtain a copy of the License at
 * http://www.opensource.apple.com/apsl/ and read it before using this
 * file.
 * 
 * The Original Code and all software distributed under the License are
 * distributed on an 'AS IS' basis, WITHOUT WARRANTY OF ANY KIND, EITHER
 * EXPRESS OR IMPLIED, AND APPLE HEREBY DISCLAIMS ALL SUCH WARRANTIES,
 * INCLUDING WITHOUT LIMITATION, ANY WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE, QUIET ENJOYMENT OR NON-INFRINGEMENT.
 * Please see the License for the specific language governing rights and
 * limitations under the License.
 * 
 * @APPLE_LICENSE_HEADER_END@
 */
/*
** This is a modified version of the original Availability.h.
** All availability macros are unconditionally defined empty.
** This removes the need to include and parse the long AvailabilityInternal.h.
*/

#ifndef __AVAILABILITY__
#define __AVAILABILITY__

#define __MAC_10_0            1000
#define __MAC_10_1            1010
#define __MAC_10_2            1020
#define __MAC_10_3            1030
#define __MAC_10_4            1040
#define __MAC_10_5            1050
#define __MAC_10_6            1060
#define __MAC_10_7            1070
#define __MAC_10_8            1080
#define __MAC_10_9            1090
#define __MAC_10_10         101000
#define __MAC_10_10_2       101002
#define __MAC_10_10_3       101003
#define __MAC_10_11         101100
#define __MAC_10_11_2       101102
#define __MAC_10_11_3       101103
#define __MAC_10_11_4       101104

#define __IPHONE_2_0      20000
#define __IPHONE_2_1      20100
#define __IPHONE_2_2      20200
#define __IPHONE_3_0      30000
#define __IPHONE_3_1      30100
#define __IPHONE_3_2      30200
#define __IPHONE_4_0      40000
#define __IPHONE_4_1      40100
#define __IPHONE_4_2      40200
#define __IPHONE_4_3      40300
#define __IPHONE_5_0      50000
#define __IPHONE_5_1      50100
#define __IPHONE_6_0      60000
#define __IPHONE_6_1      60100
#define __IPHONE_7_0      70000
#define __IPHONE_7_1      70100
#define __IPHONE_8_0      80000
#define __IPHONE_8_1      80100
#define __IPHONE_8_2      80200
#define __IPHONE_8_3      80300
#define __IPHONE_8_4      80400
#define __IPHONE_9_0      90000
#define __IPHONE_9_1      90100
#define __IPHONE_9_2      90200
#define __IPHONE_9_3      90300

#define __TVOS_9_0        90000
#define __TVOS_9_1        90100
#define __TVOS_9_2        90200

#define __WATCHOS_1_0     10000
#define __WATCHOS_2_0     20000

#define __OSX_AVAILABLE_STARTING(_osx, _ios)
#define __OSX_AVAILABLE_BUT_DEPRECATED(_osxIntro, _osxDep, _iosIntro, _iosDep)
#define __OSX_AVAILABLE_BUT_DEPRECATED_MSG(_osxIntro, _osxDep, _iosIntro, _iosDep, _msg)


#define __OS_AVAILABILITY(_target, _availability)
#define __OS_AVAILABILITY_MSG(_target, _availability, _msg)


#define __OSX_EXTENSION_UNAVAILABLE(_msg)
#define __IOS_EXTENSION_UNAVAILABLE(_msg)

#define __OS_EXTENSION_UNAVAILABLE(_msg)  __OSX_EXTENSION_UNAVAILABLE(_msg) __IOS_EXTENSION_UNAVAILABLE(_msg)



#ifndef __OSX_UNAVAILABLE
  #define __OSX_UNAVAILABLE
#endif

#ifndef __OSX_AVAILABLE
  #define __OSX_AVAILABLE(_vers)
#endif

#ifndef __OSX_DEPRECATED
  #define __OSX_DEPRECATED(_start, _dep, _msg)
#endif


#ifndef __IOS_UNAVAILABLE
  #define __IOS_UNAVAILABLE
#endif

#ifndef __IOS_PROHIBITED
  #define __IOS_PROHIBITED
#endif

#ifndef __IOS_AVAILABLE
  #define __IOS_AVAILABLE(_vers)
#endif

#ifndef __IOS_DEPRECATED
  #define __IOS_DEPRECATED(_start, _dep, _msg)
#endif


#ifndef __TVOS_UNAVAILABLE
  #define __TVOS_UNAVAILABLE
#endif

#ifndef __TVOS_PROHIBITED
  #define __TVOS_PROHIBITED
#endif

#ifndef __TVOS_AVAILABLE
  #define __TVOS_AVAILABLE(_vers)
#endif

#ifndef __TVOS_DEPRECATED
  #define __TVOS_DEPRECATED(_start, _dep, _msg)
#endif


#ifndef __WATCHOS_UNAVAILABLE
  #define __WATCHOS_UNAVAILABLE
#endif

#ifndef __WATCHOS_PROHIBITED
  #define __WATCHOS_PROHIBITED
#endif

#ifndef __WATCHOS_AVAILABLE
  #define __WATCHOS_AVAILABLE(_vers)
#endif

#ifndef __WATCHOS_DEPRECATED
  #define __WATCHOS_DEPRECATED(_start, _dep, _msg)
#endif

#endif /* __AVAILABILITY__ */

