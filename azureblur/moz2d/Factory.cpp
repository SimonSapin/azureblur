/* -*- Mode: C++; tab-width: 20; indent-tabs-mode: nil; c-basic-offset: 2 -*-
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

#include "2D.h"

#ifdef USE_CAIRO
#include "DrawTargetCairo.h"
#include "ScaledFontCairo.h"
#endif

#ifdef USE_SKIA
#include "DrawTargetSkia.h"
#include "ScaledFontBase.h"
#if defined(MOZ_ENABLE_FREETYPE) && defined(USE_CAIRO)
#define USE_SKIA_FREETYPE
#include "ScaledFontCairo.h"
#endif
#endif

#if defined(WIN32)
#include "ScaledFontWin.h"
#endif

#ifdef XP_MACOSX
#include "ScaledFontMac.h"
#endif


#ifdef XP_MACOSX
#include "DrawTargetCG.h"
#endif

#ifdef WIN32
#include "DrawTargetD2D.h"
#ifdef USE_D2D1_1
#include "DrawTargetD2D1.h"
#endif
#include "ScaledFontDWrite.h"
#include <d3d10_1.h>
#include "HelpersD2D.h"
#endif

#include "DrawTargetDual.h"
#include "DrawTargetTiled.h"
#include "DrawTargetRecording.h"

#include "SourceSurfaceRawData.h"

#include "DrawEventRecorder.h"

#include "Logging.h"

#include "mozilla/CheckedInt.h"

#if defined(DEBUG) || defined(PR_LOGGING)
PRLogModuleInfo *
GetGFX2DLog()
{
  static PRLogModuleInfo *sLog;
  if (!sLog)
    sLog = PR_NewLogModule("gfx2d");
  return sLog;
}
#endif

// The following code was largely taken from xpcom/glue/SSE.cpp and
// made a little simpler.
enum CPUIDRegister { eax = 0, ebx = 1, ecx = 2, edx = 3 };

#ifdef HAVE_CPUID_H

// cpuid.h is available on gcc 4.3 and higher on i386 and x86_64
#include <cpuid.h>

static inline bool
HasCPUIDBit(unsigned int level, CPUIDRegister reg, unsigned int bit)
{
  unsigned int regs[4];
  return __get_cpuid(level, &regs[0], &regs[1], &regs[2], &regs[3]) &&
         (regs[reg] & bit);
}

#define HAVE_CPU_DETECTION
#else

#if defined(_MSC_VER) && _MSC_VER >= 1600 && (defined(_M_IX86) || defined(_M_AMD64))
// MSVC 2005 or later supports __cpuid by intrin.h
// But it does't work on MSVC 2005 with SDK 7.1 (Bug 753772)
#include <intrin.h>

#define HAVE_CPU_DETECTION
#elif defined(__SUNPRO_CC) && (defined(__i386) || defined(__x86_64__))

// Define a function identical to MSVC function.
#ifdef __i386
static void
__cpuid(int CPUInfo[4], int InfoType)
{
  asm (
    "xchg %esi, %ebx\n"
    "cpuid\n"
    "movl %eax, (%edi)\n"
    "movl %ebx, 4(%edi)\n"
    "movl %ecx, 8(%edi)\n"
    "movl %edx, 12(%edi)\n"
    "xchg %esi, %ebx\n"
    :
    : "a"(InfoType), // %eax
      "D"(CPUInfo) // %edi
    : "%ecx", "%edx", "%esi"
  );
}
#else
static void
__cpuid(int CPUInfo[4], int InfoType)
{
  asm (
    "xchg %rsi, %rbx\n"
    "cpuid\n"
    "movl %eax, (%rdi)\n"
    "movl %ebx, 4(%rdi)\n"
    "movl %ecx, 8(%rdi)\n"
    "movl %edx, 12(%rdi)\n"
    "xchg %rsi, %rbx\n"
    :
    : "a"(InfoType), // %eax
      "D"(CPUInfo) // %rdi
    : "%ecx", "%edx", "%rsi"
  );
}

#define HAVE_CPU_DETECTION
#endif
#endif

#ifdef HAVE_CPU_DETECTION
static inline bool
HasCPUIDBit(unsigned int level, CPUIDRegister reg, unsigned int bit)
{
  // Check that the level in question is supported.
  volatile int regs[4];
  __cpuid((int *)regs, level & 0x80000000u);
  if (unsigned(regs[0]) < level)
    return false;
  __cpuid((int *)regs, level);
  return !!(unsigned(regs[reg]) & bit);
}
#endif
#endif

namespace mozilla {
namespace gfx {

// XXX - Need to define an API to set this.
GFX2D_API int sGfxLogLevel = LOG_DEBUG;

#ifdef WIN32
ID3D10Device1 *Factory::mD3D10Device;
#ifdef USE_D2D1_1
ID3D11Device *Factory::mD3D11Device;
ID2D1Device *Factory::mD2D1Device;
#endif
#endif

#ifdef MOZ_ENABLE_FREETYPE
FT_Library Factory::mFreetypeLibrary = nullptr;
#endif

DrawEventRecorder *Factory::mRecorder;

bool
Factory::HasSSE2()
{
#if defined(__SSE2__) || defined(_M_X64) || \
    (defined(_M_IX86_FP) && _M_IX86_FP >= 2)
  // gcc with -msse2 (default on OSX and x86-64)
  // cl.exe with -arch:SSE2 (default on x64 compiler)
  return true;
#elif defined(HAVE_CPU_DETECTION)
  static enum {
    UNINITIALIZED,
    NO_SSE2,
    HAS_SSE2
  } sDetectionState = UNINITIALIZED;

  if (sDetectionState == UNINITIALIZED) {
    sDetectionState = HasCPUIDBit(1u, edx, (1u<<26)) ? HAS_SSE2 : NO_SSE2;
  }
  return sDetectionState == HAS_SSE2;
#else
  return false;
#endif
}

bool
Factory::CheckSurfaceSize(const IntSize &sz, int32_t limit)
{
  if (sz.width < 0 || sz.height < 0) {
    gfxDebug() << "Surface width or height < 0!";
    return false;
  }

  // reject images with sides bigger than limit
  if (limit && (sz.width > limit || sz.height > limit)) {
    gfxDebug() << "Surface size too large (exceeds caller's limit)!";
    return false;
  }

  // make sure the surface area doesn't overflow a int32_t
  CheckedInt<int32_t> tmp = sz.width;
  tmp *= sz.height;
  if (!tmp.isValid()) {
    gfxDebug() << "Surface size too large (would overflow)!";
    return false;
  }

  // assuming 4 bytes per pixel, make sure the allocation size
  // doesn't overflow a int32_t either
  CheckedInt<int32_t> stride = sz.width;
  stride *= 4;

  // When aligning the stride to 16 bytes, it can grow by up to 15 bytes.
  stride += 16 - 1;

  if (!stride.isValid()) {
    gfxDebug() << "Surface size too large (stride overflows int32_t)!";
    return false;
  }

  CheckedInt<int32_t> numBytes = GetAlignedStride<16>(sz.width * 4);
  numBytes *= sz.height;
  if (!numBytes.isValid()) {
    gfxDebug() << "Surface size too large (allocation size would overflow int32_t)!";
    return false;
  }

  return true;
}









#ifdef MOZ_ENABLE_FREETYPE
FT_Library
Factory::GetFreetypeLibrary()
{
  if (!mFreetypeLibrary) {
    FT_Init_FreeType(&mFreetypeLibrary);
  }
  return mFreetypeLibrary;
}
#endif

#ifdef WIN32


void
Factory::SetDirect3D10Device(ID3D10Device1 *aDevice)
{
  // do not throw on failure; return error codes and disconnect the device
  // On Windows 8 error codes are the default, but on Windows 7 the
  // default is to throw (or perhaps only with some drivers?)
  aDevice->SetExceptionMode(0);
  mD3D10Device = aDevice;
}

ID3D10Device1*
Factory::GetDirect3D10Device()

{
#ifdef DEBUG
  UINT mode = mD3D10Device->GetExceptionMode();
  MOZ_ASSERT(0 == mode);
#endif
  return mD3D10Device;
}

#ifdef USE_D2D1_1

void
Factory::SetDirect3D11Device(ID3D11Device *aDevice)
{
  mD3D11Device = aDevice;

  RefPtr<ID2D1Factory1> factory = D2DFactory1();

  RefPtr<IDXGIDevice> device;
  aDevice->QueryInterface((IDXGIDevice**)byRef(device));
  factory->CreateDevice(device, &mD2D1Device);
}

ID3D11Device*
Factory::GetDirect3D11Device()
{
  return mD3D11Device;
}

ID2D1Device*
Factory::GetD2D1Device()
{
  return mD2D1Device;
}

bool
Factory::SupportsD2D1()
{
  return !!D2DFactory1();
}
#endif


uint64_t
Factory::GetD2DVRAMUsageDrawTarget()
{
  return DrawTargetD2D::mVRAMUsageDT;
}

uint64_t
Factory::GetD2DVRAMUsageSourceSurface()
{
  return DrawTargetD2D::mVRAMUsageSS;
}

void
Factory::D2DCleanup()
{
  DrawTargetD2D::CleanupD2D();
}

#endif // XP_WIN

#ifdef USE_SKIA_GPU

#endif // USE_SKIA_GPU

void
Factory::PurgeTextureCaches()
{
}

#ifdef USE_SKIA_FREETYPE
#endif


#ifdef XP_MACOSX
#endif





void
Factory::SetGlobalEventRecorder(DrawEventRecorder *aRecorder)
{
  mRecorder = aRecorder;
}

LogForwarder* Factory::mLogForwarder = nullptr;

// static
void
Factory::SetLogForwarder(LogForwarder* aLogFwd) {
  mLogForwarder = aLogFwd;
}

// static
void
CriticalLogger::OutputMessage(const std::string &aString, int aLevel)
{
  if (Factory::GetLogForwarder()) {
    Factory::GetLogForwarder()->Log(aString);
  }

  BasicLogger::OutputMessage(aString, aLevel);
}

}
}
