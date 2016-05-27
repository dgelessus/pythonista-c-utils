/*
 * Portions Copyright (c) 1985-2011 by Apple Inc.. All rights reserved.
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
** Small modifications to make packing work with CFFI.
*/

#ifndef __MACTYPES__
#define __MACTYPES__

#ifndef __CONDITIONALMACROS__
#include <ConditionalMacros.h>
#endif

#include <stdbool.h>

#include <sys/types.h>

#include <Availability.h>

#if PRAGMA_ONCE
#pragma once
#endif

#ifdef __cplusplus
extern "C" {
#endif

//#pragma pack(push, 2)


#if  ! defined(ALLOW_OBSOLETE_CARBON) || ! ALLOW_OBSOLETE_CARBON

#define ALLOW_OBSOLETE_CARBON_MACMEMORY        0
#define ALLOW_OBSOLETE_CARBON_OSUTILS     0

#else

#define ALLOW_OBSOLETE_CARBON_MACMEMORY       1
#define ALLOW_OBSOLETE_CARBON_OSUTILS       1

#endif

#ifndef NULL
#define NULL    __DARWIN_NULL
#endif /* ! NULL */
#ifndef nil
  #if defined(__has_feature) 
    #if __has_feature(cxx_nullptr)
      #define nil nullptr
    #else
      #define nil __DARWIN_NULL
    #endif
  #else
    #define nil __DARWIN_NULL
  #endif
#endif

typedef unsigned char                   UInt8;
typedef signed char                     SInt8;
typedef unsigned short                  UInt16;
typedef signed short                    SInt16;

#if __LP64__
typedef unsigned int                    UInt32;
typedef signed int                      SInt32;
#else
typedef unsigned long                   UInt32;
typedef signed long                     SInt32;
#endif

#ifndef _OS_OSTYPES_H
#if TARGET_RT_BIG_ENDIAN
struct wide {
  SInt32              hi;
  UInt32              lo;
};
typedef struct wide                     wide;
struct UnsignedWide {
  UInt32              hi;
  UInt32              lo;
};
typedef struct UnsignedWide             UnsignedWide;
#else
struct wide {
  UInt32              lo;
  SInt32              hi;
};
typedef struct wide                     wide;
struct UnsignedWide {
  UInt32              lo;
  UInt32              hi;
};
typedef struct UnsignedWide             UnsignedWide;
#endif  /* TARGET_RT_BIG_ENDIAN */

#endif

#if TYPE_LONGLONG
    #if defined(_MSC_VER) && !defined(__MWERKS__) && defined(_M_IX86)
      typedef   signed __int64                SInt64;
        typedef unsigned __int64                UInt64;
    #else
      typedef   signed long long              SInt64;
        typedef unsigned long long              UInt64;
    #endif
#else


typedef wide                            SInt64;
typedef UnsignedWide                    UInt64;
#endif  /* TYPE_LONGLONG */

typedef SInt32                          Fixed;
typedef Fixed *                         FixedPtr;
typedef SInt32                          Fract;
typedef Fract *                         FractPtr;
typedef UInt32                          UnsignedFixed;
typedef UnsignedFixed *                 UnsignedFixedPtr;
typedef short                           ShortFixed;
typedef ShortFixed *                    ShortFixedPtr;


typedef float               Float32;
typedef double              Float64;
struct Float80 {
    SInt16  exp;
    UInt16  man[4];
};
typedef struct Float80 Float80;

struct Float96 {
    SInt16  exp[2];
    UInt16  man[4];
};
typedef struct Float96 Float96;
struct Float32Point {
    Float32             x;
    Float32             y;
};
typedef struct Float32Point Float32Point;

typedef char *                          Ptr;
typedef Ptr *                           Handle;
typedef long                            Size;

typedef SInt16                          OSErr;
typedef SInt32                          OSStatus;
typedef void *                          LogicalAddress;
typedef const void *                    ConstLogicalAddress;
typedef void *                          PhysicalAddress;
typedef UInt8 *                         BytePtr;
typedef unsigned long                   ByteCount;
typedef unsigned long                   ByteOffset;
typedef SInt32                          Duration;
typedef UnsignedWide                    AbsoluteTime;
typedef UInt32                          OptionBits;
typedef unsigned long                   ItemCount;
typedef UInt32                          PBVersion;
typedef SInt16                          ScriptCode;
typedef SInt16                          LangCode;
typedef SInt16                          RegionCode;
typedef UInt32                          FourCharCode;
typedef FourCharCode                    OSType;
typedef FourCharCode                    ResType;
typedef OSType *                        OSTypePtr;
typedef ResType *                       ResTypePtr;
typedef unsigned char                   Boolean;
typedef CALLBACK_API_C( long , ProcPtr )();
typedef CALLBACK_API( void , Register68kProcPtr )();
#if TARGET_RT_MAC_CFM
typedef struct RoutineDescriptor *UniversalProcPtr;
#else
typedef ProcPtr                         UniversalProcPtr;
#endif  /* TARGET_RT_MAC_CFM */

typedef ProcPtr *                       ProcHandle;
typedef UniversalProcPtr *              UniversalProcHandle;
typedef void *                          PRefCon;
#if __LP64__
typedef void *                          URefCon;
typedef void *                          SRefCon;
#else
typedef UInt32                          URefCon;
typedef SInt32                          SRefCon;
#endif  /* __LP64__ */

enum {
  noErr                         = 0
};

enum {
  kNilOptions                   = 0
};

#define kInvalidID   0
enum {
  kVariableLengthArray  
#ifdef __has_extension
   #if __has_extension(enumerator_attributes)
		__attribute__((deprecated))  
	#endif
#endif
  = 1
};

enum {
  kUnknownType                  = 0x3F3F3F3F /* "????" QuickTime 3.0: default unknown ResType or OSType */
};



typedef UInt32                          UnicodeScalarValue;
typedef UInt32                          UTF32Char;
typedef UInt16                          UniChar;
typedef UInt16                          UTF16Char;
typedef UInt8                           UTF8Char;
typedef UniChar *                       UniCharPtr;
typedef unsigned long                   UniCharCount;
typedef UniCharCount *                  UniCharCountPtr;
typedef unsigned char                   Str255[256];
typedef unsigned char                   Str63[64];
typedef unsigned char                   Str32[33];
typedef unsigned char                   Str31[32];
typedef unsigned char                   Str27[28];
typedef unsigned char                   Str15[16];
typedef unsigned char                   Str32Field[34];
typedef Str63                           StrFileName;
typedef unsigned char *                 StringPtr;
typedef StringPtr *                     StringHandle;
typedef const unsigned char *           ConstStringPtr;
typedef const unsigned char *           ConstStr255Param;
typedef const unsigned char *           ConstStr63Param;
typedef const unsigned char *           ConstStr32Param;
typedef const unsigned char *           ConstStr31Param;
typedef const unsigned char *           ConstStr27Param;
typedef const unsigned char *           ConstStr15Param;
typedef ConstStr63Param                 ConstStrFileNameParam;
#ifdef __cplusplus
inline unsigned char StrLength(ConstStr255Param string) { return (*string); }
#else
#define StrLength(string) (*(unsigned char *)(string))
#endif  /* defined(__cplusplus) */

#if OLDROUTINENAMES
#define Length(string) StrLength(string)
#endif  /* OLDROUTINENAMES */

struct ProcessSerialNumber {
  UInt32              highLongOfPSN;
  UInt32              lowLongOfPSN;
};
typedef struct ProcessSerialNumber      ProcessSerialNumber;
typedef ProcessSerialNumber *           ProcessSerialNumberPtr;
struct Point {
  short               v;
  short               h;
};
typedef struct Point                    Point;
typedef Point *                         PointPtr;
struct Rect {
  short               top;
  short               left;
  short               bottom;
  short               right;
};
typedef struct Rect                     Rect;
typedef Rect *                          RectPtr;
struct FixedPoint {
  Fixed               x;
  Fixed               y;
};
typedef struct FixedPoint               FixedPoint;
struct FixedRect {
  Fixed               left;
  Fixed               top;
  Fixed               right;
  Fixed               bottom;
};
typedef struct FixedRect                FixedRect;

typedef short                           CharParameter;
enum {
  normal                        = 0,
  bold                          = 1,
  italic                        = 2,
  underline                     = 4,
  outline                       = 8,
  shadow                        = 0x10,
  condense                      = 0x20,
  extend                        = 0x40
};

typedef unsigned char                   Style;
typedef short                           StyleParameter;
typedef Style                           StyleField;


typedef SInt32                          TimeValue;
typedef SInt32                          TimeScale;
typedef wide                            CompTimeValue;
typedef SInt64                          TimeValue64;
typedef struct TimeBaseRecord*          TimeBase;
// Packing required because TimeBase is a pointer, which would normally be 8-byte-aligned on 64-bit platforms.
#pragma cffi packed true
struct TimeRecord {
  CompTimeValue       value;
  TimeScale           scale;
  TimeBase            base;
};
#pragma cffi packed false
typedef struct TimeRecord               TimeRecord;

#if defined(__SC__) && !defined(__STDC__) && defined(__cplusplus)
        class __machdl HandleObject {};
        #if TARGET_CPU_68K
            class __pasobj PascalObject {};
        #endif
#endif


#if TARGET_RT_BIG_ENDIAN
struct NumVersion {
  UInt8               majorRev;
  UInt8               minorAndBugRev;
  UInt8               stage;
  UInt8               nonRelRev;
};
typedef struct NumVersion               NumVersion;
#else
struct NumVersion {
  UInt8               nonRelRev;
  UInt8               stage;
  UInt8               minorAndBugRev;
  UInt8               majorRev;
};
typedef struct NumVersion               NumVersion;
#endif  /* TARGET_RT_BIG_ENDIAN */

enum {
  developStage                  = 0x20,
  alphaStage                    = 0x40,
  betaStage                     = 0x60,
  finalStage                    = 0x80
};

union NumVersionVariant {
  NumVersion          parts;
  UInt32              whole;
};
typedef union NumVersionVariant         NumVersionVariant;
typedef NumVersionVariant *             NumVersionVariantPtr;
typedef NumVersionVariantPtr *          NumVersionVariantHandle;
struct VersRec {
  NumVersion          numericVersion;
  short               countryCode;
  Str255              shortVersion;
  Str255              reserved;
};
typedef struct VersRec                  VersRec;
typedef VersRec *                       VersRecPtr;
typedef VersRecPtr *                    VersRecHndl;
typedef UInt8                           Byte;
typedef SInt8                           SignedByte;
typedef wide *                          WidePtr;
typedef UnsignedWide *                  UnsignedWidePtr;
typedef Float80                         extended80;
typedef Float96                         extended96;
typedef SInt8                           VHSelect;
extern void 
Debugger(void)                                                __OSX_AVAILABLE_BUT_DEPRECATED(__MAC_10_0, __MAC_10_8, __IPHONE_NA, __IPHONE_NA);


extern void 
DebugStr(ConstStr255Param debuggerMsg)                        __OSX_AVAILABLE_BUT_DEPRECATED(__MAC_10_0, __MAC_10_8, __IPHONE_NA, __IPHONE_NA);


#if TARGET_CPU_PPC
#endif  /* TARGET_CPU_PPC */

extern void 
SysBreak(void)                                                __OSX_AVAILABLE_BUT_DEPRECATED(__MAC_10_0, __MAC_10_8, __IPHONE_NA, __IPHONE_NA);


extern void 
SysBreakStr(ConstStr255Param debuggerMsg)                     __OSX_AVAILABLE_BUT_DEPRECATED(__MAC_10_0, __MAC_10_8, __IPHONE_NA, __IPHONE_NA);


extern void 
SysBreakFunc(ConstStr255Param debuggerMsg)                    __OSX_AVAILABLE_BUT_DEPRECATED(__MAC_10_0, __MAC_10_8, __IPHONE_NA, __IPHONE_NA);


#if OLDROUTINENAMES && TARGET_CPU_68K
    #define Debugger68k()   Debugger()
    #define DebugStr68k(s)  DebugStr(s)
#endif


//#pragma pack(pop)

#ifdef __cplusplus
}
#endif

#endif /* __MACTYPES__ */

