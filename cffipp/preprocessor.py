"""A C preprocessor for CFFI.

Most parts of the preprocessor are based on ply/cpp.py from the PLY library by David Beazley (http://www.dabeaz.com). See the LICENSE file for license info.
"""

import copy
import os
import re
import sys
import time

__all__ = [
	"Macro",
	"Preprocessor",
	"PreprocessorError",
]

_trigraph_pat = re.compile(r'''\?\?[=/\'\(\)\!<>\-]''')
_trigraph_rep = {
	'=': '#',
	'/': '\\',
	"'": '^',
	'(': '[',
	')': ']',
	'!': '|',
	'<': '{',
	'>': '}',
	'-': '~',
}

def trigraph(inp):
	"""Given an input string, this function replaces all trigraph sequences.
	The following mapping is used:
	
	??=	#
	??/	\
	??'	^
	??(	[
	??)	]
	??!	|
	??<	{
	??>	}
	??-	~
	"""
	
	return _trigraph_pat.sub(lambda g: _trigraph_rep[g.group()[-1]], inp)

class PreprocessorError(Exception):
	def __init__(self, msg, file=None, line=None):
		if file is not None:
			if line is not None:
				super().__init__("File {}, line {}: {}".format(file, line, msg))
			else:
				super().__init__("File {}: {}".format(file, msg))
		else:
			super().__init__(msg)
		
		self.msg = msg
		self.file = file
		self.line = line

class Macro(object):
	"""This object holds information about preprocessor macros.
	
		.name - Macro name (string)
		.value - Macro value (a list of tokens)
		.arglist - List of argument names
		.variadic - Boolean indicating whether or not variadic macro
		.vararg - Name of the variadic parameter
	
	When a macro is created, the macro replacement token sequence is
	pre-scanned and used to create patch lists that are later used
	during macro expansion.
	"""
	
	def __init__(self, name, value, arglist=None, variadic=False):
		self.name = name
		self.value = value
		self.arglist = arglist
		self.variadic = variadic
		self.vararg = arglist[-1] if variadic else None
		self.source = None
	
	def __repr__(self):
		return "{cls.__module__}.{cls.__name__}(name={self.name!r}, value={self.value!r}, arglist={self.arglist!r}, variadic={self.variadic!r}, vararg={self.vararg!r}, source={self.source!r})".format(cls=type(self), self=self)

class Preprocessor(object):
	"""Object representing a preprocessor.
	Contains macro definitions, include directories, and other information.
	"""
	
	def __init__(self, lexer=None):
		if lexer is None:
			lexer = lex.lexer
		self.lexer = lexer
		self.macros = {}
		self.path = []
		self.source = None
		self.temp_path = []
		self.included_files = set()
		
		# Probe the lexer for selected tokens
		self.lexprobe()
		
		tm = time.localtime()
		# These date and time formats are standardized.
		# Do not modify (even though they are terrible).
		self.define('__DATE__ "%s"' % time.strftime("%b %d %Y", tm))
		self.define('__TIME__ "%s"' % time.strftime("%H:%M:%S", tm))
		self.parser = None
	
	def __iter__(self):
		yield from iter(self.token, None)
	
	def tokenize(self, text):
		"""Utility function. Given a string of text, tokenize into a list of tokens."""
		
		tokens = []
		self.lexer.input(text)
		while True:
			tok = self.lexer.token()
			if not tok:
				break
			tokens.append(tok)
		return tokens
	
	def lexprobe(self):
		"""This method probes the preprocessor lexer object to discover
		the token types of symbols that are important to the preprocessor.
		If this works right, the preprocessor will simply "work"
		with any suitable lexer regardless of how tokens have been named.
		"""
		
		# Determine the token type for identifiers
		self.lexer.input("identifier")
		tok = self.lexer.token()
		if not tok or tok.value != "identifier":
			raise PreprocessorError("Couldn't determine identifier type")
		else:
			self.t_ID = tok.type
		
		# Determine the token type for integers
		self.lexer.input("12345")
		tok = self.lexer.token()
		if not tok or int(tok.value) != 12345:
			raise PreprocessorError("Couldn't determine integer type")
		else:
			self.t_INTEGER = tok.type
			self.t_INTEGER_TYPE = type(tok.value)
		
		# Determine the token type for strings enclosed in double quotes
		self.lexer.input('"filename"')
		tok = self.lexer.token()
		if not tok or tok.value != '"filename"':
			raise PreprocessorError("Couldn't determine string type")
		else:
			self.t_STRING = tok.type
		
		# Determine the token type for whitespace--if any
		self.lexer.input("  ")
		tok = self.lexer.token()
		if not tok or tok.value != "  ":
			self.t_SPACE = None
		else:
			self.t_SPACE = tok.type
		
		# Determine the token type for newlines
		self.lexer.input("\n")
		tok = self.lexer.token()
		if not tok or tok.value != "\n":
			self.t_NEWLINE = None
			raise PreprocessorError("Couldn't determine token for newlines")
		else:
			self.t_NEWLINE = tok.type
		
		self.t_WS = (self.t_SPACE, self.t_NEWLINE)
		
		# Check for other characters used by the preprocessor
		chars = ['<', '>', '#', '##', '\\', '(', ')', ',', '.']
		for c in chars:
			self.lexer.input(c)
			tok = self.lexer.token()
			if not tok or tok.value != c:
				raise PreprocessorError("Unable to lex {!r} required for preprocessor".format(c))
	
	def add_path(self, path):
		"""Adds a search path to the preprocessor."""
		
		self.path.append(path)
	
	def group_lines(self, inp):
		r"""Given an input string, this function splits it into lines.
		Trailing whitespace is removed. Any line ending with \ is grouped with the next line.
		This function forms the lowest level of the preprocessor---grouping into text into
		a line-by-line format.
		"""
		
		lex = self.lexer.clone()
		lines = [x.rstrip() for x in inp.splitlines()]
		for i in range(len(lines)):
			j = i+1
			while lines[i].endswith('\\') and j < len(lines):
				lines[i] = lines[i][:-1]+lines[j]
				lines[j] = ""
				j += 1
		
		inp = "\n".join(lines)
		lex.input(inp)
		lex.lineno = 1
		
		current_line = []
		while True:
			tok = lex.token()
			if not tok:
				break
			current_line.append(tok)
			if tok.type in self.t_WS and '\n' in tok.value:
				yield current_line
				current_line = []
		
		if current_line:
			yield current_line
	
	def tokenstrip(self, tokens):
		"""Remove leading/trailing whitespace tokens from a token list."""
		
		i = 0
		while i < len(tokens) and tokens[i].type in self.t_WS:
			i += 1
		del tokens[:i]
		i = len(tokens)-1
		while i >= 0 and tokens[i].type in self.t_WS:
			i -= 1
		del tokens[i+1:]
		return tokens
	
	def collect_args(self, tokenlist):
		"""Collects comma separated arguments from a list of tokens.
		The arguments must be enclosed in parentheses.
		Returns a tuple (tokencount, args, positions) where tokencount
		is the number of tokens consumed, args is a list of arguments,
		and positions is a list of integers containing the starting index of each
		argument. Each argument is represented by a list of tokens.
		
		When collecting arguments, leading and trailing whitespace is removed
		from each argument.  
		
		This function properly handles nested parenthesis and commas---these do not
		define new arguments.
		"""
		
		args = []
		positions = []
		current_arg = []
		nesting = 1
		tokenlen = len(tokenlist)
		
		# Search for the opening '('.
		i = 0
		while (i < tokenlen) and (tokenlist[i].type in self.t_WS):
			i += 1
		
		if (i < tokenlen) and (tokenlist[i].value == '('):
			positions.append(i+1)
		else:
			raise PreprocessorError("Missing '(' in macro arguments", self.source, tokenlist[0].lineno)
		
		i += 1
		
		while i < tokenlen:
			t = tokenlist[i]
			if t.value == '(':
				current_arg.append(t)
				nesting += 1
			elif t.value == ')':
				nesting -= 1
				if nesting == 0:
					if current_arg:
						args.append(self.tokenstrip(current_arg))
						positions.append(i)
					return i+1,args,positions
				current_arg.append(t)
			elif t.value == ',' and nesting == 1:
				args.append(self.tokenstrip(current_arg))
				positions.append(i+1)
				current_arg = []
			else:
				current_arg.append(t)
			i += 1
		
		# Missing end argument
		raise PreprocessorError("Missing ')' in macro arguments", self.source, tokenlist[-1].lineno)
	
	def macro_prescan(self, macro):
		"""Examine the macro value (token sequence) and identify patch points.
		This is used to speed up macro expansion later on---we'll know
		right away where to apply patches to the value to form the expansion.
		"""
		
		##print("Prescanning {}".format(macro.name))
		
		macro.patch = [] # Standard macro arguments 
		macro.str_patch = [] # String conversion expansion
		macro.var_comma_patch = [] # Variadic macro comma patch
		i = 0
		while i < len(macro.value):
			##print(i, macro.value[i])
			if macro.value[i].type == self.t_ID:
				if macro.value[i].value in macro.arglist:
					argnum = macro.arglist.index(macro.value[i].value)
					# Conversion of argument to a string
					if i > 0 and macro.value[i-1].value == '#':
						##print("String conversion expansion here")
						macro.value[i] = copy.copy(macro.value[i])
						macro.value[i].type = self.t_STRING
						del macro.value[i-1]
						macro.str_patch.append((argnum,i-1))
						continue
					# Concatenation
					elif i > 0 and macro.value[i-1].value == '##':
						##print("Concatenation expansion here from op before")
						macro.patch.append(('c',argnum,i-1))
						del macro.value[i-1]
						continue
					elif i+1 < len(macro.value) and macro.value[i+1].value == '##':
						##print("Concatenation expansion here from op after")
						macro.patch.append(('c',argnum,i))
						i += 1
						continue
					# Standard expansion
					else:
						##print("Standard expansion")
						macro.patch.append(('e',argnum,i))
				else:
					if i > 0 and macro.value[i-1].value == '##':
						##print("Removing concatenation operator before")
						del macro.value[i-1]
						continue
			elif macro.value[i].value == '##':
				if (
					macro.variadic
					and i > 0
					and macro.value[i-1].value == ','
					and i+1 < len(macro.value)
					and macro.value[i+1].type == self.t_ID
					and macro.value[i+1].value == macro.vararg
				):
					##print("Comma-vararg removal operator here")
					macro.var_comma_patch.append(i-1)
			i += 1
		macro.patch.sort(key=lambda x: x[2], reverse=True)
	
	def macro_expand_args(self, macro, args):
		"""Given a Macro and list of arguments (each a token list), this method
		returns an expanded version of a macro. The return value is a token sequence
		representing the replacement macro tokens.
		"""
		
		##print("Expanding call of {} with args {}".format(macro.name, args))
		
		# Make a copy of the macro token sequence
		rep = [copy.copy(_x) for _x in macro.value]
		
		# Make string expansion patches. These do not alter the length of the replacement sequence
		
		str_expansion = {}
		for argnum, i in macro.str_patch:
			if argnum not in str_expansion:
				str_expansion[argnum] = ('"%s"' % "".join([x.value for x in args[argnum]])).replace("\\", "\\\\")
			rep[i] = copy.copy(rep[i])
			rep[i].value = str_expansion[argnum]
		
		# Make the variadic macro comma patch.  If the variadic macro argument is empty, we get rid
		comma_patch = False
		if macro.variadic and not args[-1]:
			for i in macro.var_comma_patch:
				rep[i] = None
				comma_patch = True
		
		# Make all other patches. The order of these matters. It is assumed that the patch list
		# has been sorted in reverse order of patch location since replacements will cause the
		# size of the replacement sequence to expand from the patch point.
		
		expanded = {}
		for ptype, argnum, i in macro.patch:
			##print(ptype, argnum, i)
			# Concatenation. Argument is left unexpanded
			if ptype == 'c':
				##print("Unexpanded {}".format(args[argnum]))
				rep[i:i+1] = args[argnum]
			# Normal expansion. Argument is macro expanded first
			elif ptype == 'e':
				if argnum not in expanded:
					expanded[argnum] = self.expand_macros(args[argnum])
				##print("Expanded {} to {}".format(args[argnum], expanded[argnum]))
				rep[i:i+1] = expanded[argnum]
		
		# Join adjacent tokens to prevent incorrect expansion
		for i in range(len(rep)-1, 0, -1):
			if rep[i-1].type in (self.t_ID, self.t_INTEGER) and rep[i].type in (self.t_ID, self.t_INTEGER):
				rep[i-1] = copy.copy(rep[i-1])
				rep[i-1].value += rep[i].value
				del rep[i]
		
		# Get rid of removed comma if necessary
		if comma_patch:
			rep = [_i for _i in rep if _i]
		
		return rep
	
	def expand_macros(self, tokens, expanded=None):
		"""Given a list of tokens, this function performs macro expansion.
		The expanded argument is a dictionary that contains macros already
		expanded. This is used to prevent infinite recursion.
		"""
		
		##joined = "".join(t.value for t in tokens)
		##if joined.strip():
		##	print("Expanded: {}, expanding: {}".format(expanded, tokens))
		
		if expanded is None:
			expanded = {}
		
		i = 0
		
		while i < len(tokens):
			t = tokens[i]
			if t.type == self.t_ID:
				if t.value == 'defined':
					j = i + 1
					needparen = False
					result = None
					
					while j < len(tokens):
						if tokens[j].type in self.t_WS:
							j += 1
							continue
						elif tokens[j].type == self.t_ID:
							if tokens[j].value in self.macros:
								result = "1"
							else:
								result = "0"
							
							if not needparen:
								break
						elif tokens[j].value == '(':
							needparen = True
						elif tokens[j].value == ')':
							break
						else:
							raise PreprocessorError("Malformed defined()", self.source, t.lineno)
						j += 1
					
					if result is None:
						raise PreprocessorError("Malformed defined()", self.source, t.lineno)
					
					t.type = self.t_INTEGER
					t.value = self.t_INTEGER_TYPE(result)
					del tokens[i+1:j+1]
				elif t.value in self.macros and t.value not in expanded:
					# Yes, we found a macro match
					expanded[t.value] = True
					
					m = self.macros[t.value]
					if not m.arglist:
						# A simple macro
						ex = self.expand_macros([copy.copy(_x) for _x in m.value], expanded)
						for e in ex:
							e.lineno = t.lineno
						tokens[i:i+1] = ex
						i += len(ex)
					else:
						# A macro with arguments
						j = i + 1
						while j < len(tokens) and tokens[j].type in self.t_WS:
							j += 1
						
						if len(tokens) > j and tokens[j].value == '(':
							# Macro function is called
							tokcount, args, positions = self.collect_args(tokens[j:])
							if not m.variadic and len(args) !=  len(m.arglist):
								raise PreprocessorError("Macro {} requires {} arguments".format(t.value, len(m.arglist)), self.source, t.lineno)
								i = j + tokcount
							elif m.variadic and len(args) < len(m.arglist)-1:
								if len(m.arglist) > 2:
									raise PreprocessorError("Macro {} must have at least {} arguments".format(t.value, len(m.arglist)-1), self.source, t.lineno)
								else:
									raise PreprocessorError("Macro {} must have at least {} argument".format(t.value, len(m.arglist)-1), self.source, t.lineno)
								i = j + tokcount
							else:
								if m.variadic:
									if len(args) == len(m.arglist)-1:
										args.append([])
									else:
										args[len(m.arglist)-1] = tokens[j+positions[len(m.arglist)-1]:j+tokcount-1]
										del args[len(m.arglist):]
										
								# Get macro replacement text
								rep = self.macro_expand_args(m, args)
								##rep = self.expand_macros(rep, expanded)
								for r in rep:
									r.lineno = t.lineno
								tokens[i:j+tokcount] = rep
								##i += len(rep)
								# Intentionally do not increment i and do not call expand_macros.
								# Instead, in the next loop iteration, let the replacement get expanded.
								# This is important for macro functions that return the name of a macro function, such as
								# a(something)(whatever)
						else:
							# Macro function is not called - just move on
							i += 1
					del expanded[t.value]
					continue
				elif t.value == '__LINE__':
					t.type = self.t_INTEGER
					t.value = self.t_INTEGER_TYPE(t.lineno)
			
			i += 1
		return tokens
	
	def evalexpr(self, tokens):
		"""Evaluate an expression token sequence for the purposes of evaluating integral expressions."""
		
		# tokens = tokenize(line)
		
		tokens = self.expand_macros(tokens)
		for i, t in enumerate(tokens):
			if t.type == self.t_ID:
				tokens[i] = copy.copy(t)
				tokens[i].type = self.t_INTEGER
				tokens[i].value = self.t_INTEGER_TYPE("0")
			elif t.type == self.t_INTEGER:
				tokens[i] = copy.copy(t)
				tokens[i].value = str(tokens[i].value)
				
				# Strip off any trailing suffixes
				while tokens[i].value[-1] not in "0123456789abcdefABCDEF":
					tokens[i].value = tokens[i].value[:-1]
				
				# Convert octal integers to Python 3 style
				if len(tokens[i].value) >= 2 and tokens[i].value[0] == "0" and tokens[i].value[1] not in "bx":
					tokens[i].value = oct(int(tokens[i].value, 8))
		
		expr = "".join(str(x.value) for x in tokens)
		expr = expr.replace("&&", " and ")
		expr = expr.replace("||", " or ")
		expr = expr.replace("!", " not ")
		
		try:
			result = eval(expr, {"__builtins__": None})
		except Exception:
			raise PreprocessorError(
				"Couldn't evaluate expression:\nOriginal: {}\nPython: {}"
				.format("".join(t.value for t in tokens), expr), self.source, tokens[0].lineno)
		
		return result
	
	def parsegen(self, inp, source="<parsegen>"):
		"""Parse an input string."""
		
		# Replace trigraph sequences
		t = trigraph(inp)
		lines = self.group_lines(t)
		
		self.define('__FILE__ "{}"'.format(source.replace("\\", r"\\").replace('"', r'\"')))
		
		self.source = source
		chunk = []
		enable = True
		iftrigger = False
		ifstack = []
		unknown_directive = False
		
		for x in lines:
			for i, tok in enumerate(x):
				if tok.type not in self.t_WS:
					break
			
			if tok.value == '#':
				# Preprocessor directive
				
				dirtokens = self.tokenstrip(x[i+1:])
				if dirtokens:
					name = dirtokens[0].value
					args = self.tokenstrip(dirtokens[1:])
				else:
					name = ""
					args = []
				
				unknown_directive = False
				
				if name == "":
					pass
				elif name == "error":
					if enable:
						raise PreprocessorError("#error directive: {}".format("".join(arg.value for arg in args)), self.source, dirtokens[0].lineno)
				elif name == 'define':
					if enable:
						for tok in self.expand_macros(chunk):
							yield tok
						chunk = []
						self.define(args)
				elif name in ("include", "import"):
					if enable:
						for tok in self.expand_macros(chunk):
							yield tok
						chunk = []
						oldfile = self.macros['__FILE__']
						for tok in self.include(args, once=(name == "import")):
							yield tok
						self.macros['__FILE__'] = oldfile
						self.source = source
				elif name == 'undef':
					if enable:
						for tok in self.expand_macros(chunk):
							yield tok
						chunk = []
						self.undef(args)
				elif name == 'ifdef':
					ifstack.append((enable, iftrigger))
					if enable:
						if not args[0].value in self.macros:
							enable = False
							iftrigger = False
						else:
							iftrigger = True
				elif name == 'ifndef':
					ifstack.append((enable, iftrigger))
					if enable:
						if args[0].value in self.macros:
							enable = False
							iftrigger = False
						else:
							iftrigger = True
				elif name == 'if':
					ifstack.append((enable, iftrigger))
					if enable:
						result = self.evalexpr(args)
						if not result:
							enable = False
							iftrigger = False
						else:
							iftrigger = True
				elif name == 'elif':
					if ifstack:
						if ifstack[-1][0]: # We only pay attention if outer "if" allows this
							if enable: # If already true, we flip enable False
								enable = False
							
							elif not iftrigger: # If False, but not triggered yet, we'll check expression
								result = self.evalexpr(args)
								if result:
									enable = True
									iftrigger = True
					else:
						raise PreprocessorError("Misplaced #elif", self.source, dirtokens[0].lineno)
				
				elif name == 'else':
					if ifstack:
						if ifstack[-1][0]:
							if enable:
								enable = False
							elif not iftrigger:
								enable = True
								iftrigger = True
					else:
						raise PreprocessorError("Misplaced #else", self.source, dirtokens[0].lineno)
				
				elif name == 'endif':
					if ifstack:
						enable, iftrigger = ifstack.pop()
					else:
						raise PreprocessorError("Misplaced #endif", self.source, dirtokens[0].lineno)
				else:
					# Unknown preprocessor directive
					unknown_directive = True
				
				if unknown_directive:
					# Unknown directive, put the tokens back
					if enable:
						chunk += x
				else:
					# insert necessary whitespace instead of eaten tokens
					for tok in x:
						if tok.type in self.t_WS and '\n' in tok.value:
							chunk.append(tok)
			
			else:
				# Normal text
				if enable:
					chunk += x
			
			yield from (chunk if unknown_directive else self.expand_macros(chunk))
			
			chunk = []
	
	def include(self, tokens, once=False):
		"""Implementation of file-inclusion.
		
		If once is true, behave like Objective-C #import, i. e. do not include the file again if it has been included previously.
		"""
		
		# Try to extract the filename and then process an include file
		if not tokens:
			raise PreprocessorError("Malformed #include", self.source)
		
		if tokens[0].value != '<' and tokens[0].type != self.t_STRING:
			tokens = self.expand_macros(tokens)
		
		if tokens[0].value == '<':
			# Include <...>
			i = 1
			while i < len(tokens):
				if tokens[i].value == '>':
					break
				i += 1
			else:
				raise PreprocessorError("Malformed #include <...>", self.source, tokens[0].lineno)
			
			filename = "".join(x.value for x in tokens[1:i])
			path = self.path + [""] + self.temp_path
		elif tokens[0].type == self.t_STRING:
			filename = tokens[0].value[1:-1]
			path = self.temp_path + [""] + self.path
		else:
			raise PreprocessorError("Malformed #include statement", self.source, tokens[0].lineno)
		
		if once and filename in self.included_files:
			return
		else:
			self.included_files.add(filename)
		
		print('#include "{}" {{'.format(filename)) # }}
		
		for p in path:
			iname = os.path.join(p, filename)
			try:
				with open(iname, "r", encoding="utf-8") as f:
					data = f.read()
				
				dname = os.path.dirname(iname)
				if dname:
					self.temp_path.insert(0, dname)
				
				for tok in self.parsegen(data, iname):
					yield tok
				
				if dname:
					del self.temp_path[0]
				
				break
			except FileNotFoundError:
				pass
		else:
			raise PreprocessorError(
				"Could not find header on include path: {}"
				.format("".join(token.value for token in tokens)),
				self.source, tokens[0].lineno,
			)
		
		# {
		print("}")
	
	def define(self, tokens):
		"""Define a new macro."""
		
		if isinstance(tokens, str):
			tokens = self.tokenize(tokens)
		
		##print("Defining: {!r}".format("".join(t.value for t in tokens)))
		
		linetok = tokens
		try:
			name = linetok[0]
			if len(linetok) > 1:
				mtype = linetok[1]
			else:
				mtype = None
			if not mtype:
				m = Macro(name.value,[])
				self.macros[name.value] = m
			elif mtype.type in self.t_WS:
				# A normal macro
				m = Macro(name.value,self.tokenstrip(linetok[2:]))
				self.macros[name.value] = m
			elif mtype.value == '(':
				# A macro with arguments
				tokcount, args, positions = self.collect_args(linetok[1:])
				variadic = False
				for a in args:
					if variadic:
						raise PreprocessorError("No more arguments may follow a variadic argument", self.source, tokens[0].lineno)
					
					astr = "".join(str(_i.value) for _i in a)
					if astr == "...":
						variadic = True
						a[0].type = self.t_ID
						a[0].value = '__VA_ARGS__'
						variadic = True
						del a[1:]
						continue
					elif astr[-3:] == "..." and a[0].type == self.t_ID:
						variadic = True
						del a[1:]
						# If, for some reason, "." is part of the identifier, strip off the name for the purposes
						# of macro expansion
						if a[0].value[-3:] == '...':
							a[0].value = a[0].value[:-3]
						continue
					if len(a) > 1 or a[0].type != self.t_ID:
						raise PreprocessorError("Invalid macro argument", self.source, tokens[0].lineno)
				else:
					mvalue = self.tokenstrip(linetok[1+tokcount:])
					i = 0
					while i < len(mvalue):
						if i+1 < len(mvalue):
							if mvalue[i].type in self.t_WS and mvalue[i+1].value == '##':
								del mvalue[i]
								continue
							elif mvalue[i].value == '##' and mvalue[i+1].type in self.t_WS:
								del mvalue[i+1]
						i += 1
					m = Macro(name.value,mvalue,[x[0].value for x in args],variadic)
					self.macro_prescan(m)
					self.macros[name.value] = m
			else:
				raise PreprocessorError("Bad macro definition", self.source, tokens[0].lineno)
		except LookupError:
			raise PreprocessorError("Bad macro definition", self.source, tokens[0].lineno)
	
	def undef(self, tokens):
		"""Undefine a macro."""
		
		if isinstance(tokens, str):
			tokens = self.tokenize(tokens)
		
		self.macros.pop(tokens[0].value, None)
	
	def parse(self, inp, source=None, ignore={}):
		"""Parse input text."""
		
		self.ignore = ignore
		self.parser = self.parsegen(inp, source)
	
	def token(self):
		"""Method to return individual tokens."""
		
		try:
			while True:
				tok = next(self.parser)
				if tok.type not in self.ignore:
					return tok
		except StopIteration:
			self.parser = None
			return None

