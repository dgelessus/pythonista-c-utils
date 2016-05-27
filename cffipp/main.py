import os
import re
import sys
import warnings

import cffi.backend_ctypes

from . import lexer
from . import preprocessor
from . import cffi_patches

__all__ = [
	"CFFIPreprocessor",
]

DEFAULT_INCLUDE_PATH = [
	"include/builtin",
	"include/override",
	"include_private/usr_include",
	"include_private/frameworks",
	# clang should go after usr_include. Some headers are present in both, and the usr_include version is usually easier to parse as it's not compiler-specific. Certain headers (such as stdbool.h) are only provided by the compiler, which is why we need these at all.
	"include/clang",
]

DEFAULT_INCLUDE_PATH = [
	os.path.join(os.path.dirname(__file__), path)
	for path in DEFAULT_INCLUDE_PATH
]

class CFFIPreprocessor(object):
	"""Wrapper around a cffipp.preprocessor.Preprocessor and a customized cffi.FFI.
	
	The underlying FFI object is accessible via the ffi attribute.
	
	To preprocess and cdef code, use the cdef method of the CFFIPreprocessor.
	The FFI's cdef method does not do any preprocessing!
	
	To include a header file, use the cdef_include method.
	"""
	
	def __init__(self, include_path=None, **kwargs):
		self.ffi = cffi_patches.FFIWithBetterParser(backend=cffi.backend_ctypes.CTypesBackend())
		self.pp = preprocessor.Preprocessor(lexer.build())
		self._last_source = None
		
		if include_path is None:
			include_path = DEFAULT_INCLUDE_PATH
		
		for path in include_path:
			self.pp.add_path(path)
		
		if sys.platform != "ios":
			warnings.warn(UserWarning("This library is meant to run in the Pythonista app on iOS. You seem to be on a different platform. Things may not work well."))
		
		self.cdef_include("builtin_arm.h")
		
		if sys.maxsize > 2**31 - 1:
			# 64-bit
			self.cdef_include("builtin_arm64.h")
		else:
			# 32-bit
			self.cdef_include("builtin_arm32.h")
		
		self.cdef("""
		#define __asm(...) // Marks Assembler function names - not important here
		#define __attribute__(...) // GCC attributes - can usually be ignored
		#define __has_extension(...) 0 // No extensions here
		#define __has_feature(...) 0 // Whatever feature it is, we probably don't support it
		#define __has_include(...) 0 // Would be annoying to implement properly
		#define __has_include_next(...) 0 // Same
		#define _DARWIN_C_SOURCE // Enable the full Darwin APIs
		
		// Nonstandard type qualifiers that pycparser/cffi doesn't understand
		#define _Nonnull
		#define _Null_unspecified
		#define _Nullable
		
		// sys/cdefs.h defines some really annoying macros for some keywords, which confuses pycparser/cffi.
		#include <sys/cdefs.h>
		#undef const
		#undef inline
		#undef signed
		#undef volatile
		#define __const const
		#define __inline inline
		#define __signed signed
		#define __volatile volatile
		#define __asm__ asm
		#define __const__ const
		#define __inline__ inline
		#define __signed__ signed
		#define __typeof__ typeof
		#define __volatile__ volatile
		""", "<built-in>")
	
	def cdef(self, text, filename="<cdef>", header=None):
		"""Preprocess the given C source and pass it to the FFI.
		
		filename sets the value of the __FILE__ macro. header is an internal argument used by cdef_include to pass the original name of the header file.
		"""
		
		if header is None:
			msg = 'Manual definition from "{}" {{'.format(filename) # }}
		else:
			msg = 'Top-level #include "{}" {{'.format(header) # }}
		
		##print(msg)
		
		if "__attribute__((packed))" in text:
			warnings.warn(UserWarning("Use of unsupported __attribute__((packed)) in file {}".format(filename)))
		
		self.pp.parse(text, filename)
		
		line = []
		lines = []
		packed = False
		
		def _do_cdef():
			text = "".join(lines)
			self._last_source = text
			##text = re.sub(r"^\s*\n\s*", "\n", text)
			##print(text)
			self.ffi.cdef(text, packed=packed)
			line.clear()
			lines.clear()
		
		for tok in self.pp:
			if tok.type == self.pp.t_SPACE and "\n" in tok.value:
				line.append(tok.value)
				append = True
				joined = "".join(line)
				parts = joined.split()
				
				if not joined.strip():
					append = False
				elif parts and parts[0].startswith("#"):
					# Preprocessor directive not handled by the parser.
					if parts[0] == "#":
						directive = parts[1]
						args = parts[2:]
					else:
						directive = parts[0][1:]
						args = parts[1:]
					
					if directive == "pragma" and len(args) >= 3 and args[:2] == ["cffi", "packed"]:
						_do_cdef()
						packed = {"false": False, "true": True}[args[2]]
						append = False
					else:
						raise preprocessor.PreprocessorError("Unknown #pragma directive:\n{}".format(joined))
				
				if append:
					##print(joined, end="")
					lines.append(joined)
				
				line.clear()
			else:
				line.append(tok.value)
		
		lines.append("".join(line))
		_do_cdef()
		
		# {
		##print("}")
	
	def cdef_include(self, header, once=False):
		"""Include the header with the given name."""
		
		if once and header in self.pp.included_files:
			return
		else:
			self.pp.included_files.add(header)
		
		for path in self.pp.path:
			filename = os.path.join(path, header)
			try:
				f = open(filename, "r", encoding="utf-8")
			except FileNotFoundError:
				pass
			else:
				break
		else:
			raise FileNotFoundError('Header "{}" not found in include path'.format(header))
		
		with f:
			text = f.read()
		
		self.cdef(text, filename, header)
	
	"""
	def load_macros(self):
		lines = []
		
		for name, macro in self.macros.items():
			value = None
			
			if macro.arglist is None:
				macro_tokens = list(macro.value)
				negative = False
				
				done = False
				while not done:
					# Strip parens and whitespace around integers.
					# Loop exits when one iteration completes without any "cleanup actions".
					done = True
					
					if macro_tokens and macro_tokens[0].value == "(" and macro_tokens[-1].value == ")":
						del macro_tokens[0]
						del macro_tokens[-1]
						done = False
					
					if macro_tokens and (macro_tokens[0].type == self.pp.t_SPACE or macro_tokens[0].value == "+"):
						del macro_tokens[0]
						done = False
					
					if macro_tokens and macro_tokens[-1].type == self.pp.t_SPACE:
						del macro_tokens[-1]
						done = False
					
					if macro_tokens and macro_tokens[0].value == "-":
						negative = not negative
						del macro_tokens[0]
						done = False
				
				if len(macro_tokens) == 1 and macro_tokens[0].type == self.pp.t_INTEGER:
					value = ("-" if negative else "") + macro_tokens[0].value
			
			if value is not None:
				lines.append("#define {} {}\n".format(name, value))
		
		self.ffi.cdef("".join(lines))
	#"""

