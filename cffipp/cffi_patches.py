import cffi
import cffi.api
import cffi.cparser
import pycparser
import pycparser.c_ast

__all__ = [
	"BetterParser",
	"FFIWithBetterParser",
]

class BetterParser(cffi.cparser.Parser):
	def __init__(self, ffi):
		super().__init__()
		self._ffi = ffi
	
	def _declare(self, name, obj, included=False, quals=0):
		if name in self._declarations:
			prevobj, prevquals = self._declarations[name]
			if prevobj == obj and prevquals == quals:
				return
			if not self._options.get('override'):
				raise cffi.api.FFIError(
					"multiple declarations of %s (for interactive usage, "
					"try cdef(xx, override=True))" % (name,))
		assert '__dotdotdot__' not in name.split()
		self._declarations[name] = (obj, quals)
		if included:
			self._included_declarations.add(obj)
	
	def _get_type_and_quals(self, typenode, *args, **kwargs):
		if isinstance(typenode, pycparser.c_ast.Typename):
			return self._get_type_and_quals(typenode.type, *args, **kwargs)
		else:
			return super()._get_type_and_quals(typenode, *args, **kwargs)
	
	def _parse_constant(self, exprnode, **kwargs):
		if isinstance(exprnode, pycparser.c_ast.UnaryOp):
			if exprnode.op == "+":
				return self._parse_constant(exprnode.expr)
			elif exprnode.op == "-":
				return -self._parse_constant(exprnode.expr)
			elif exprnode.op == "~":
				return ~self._parse_constant(exprnode.expr)
			elif exprnode.op == "!":
				return int(not self._parse_constant(exprnode.expr))
			elif exprnode.op == "sizeof":
				tp, quals = self._get_type_and_quals(exprnode.expr)
				return self._ffi.sizeof(tp.build_backend_type(self._ffi, []))
		elif isinstance(exprnode, pycparser.c_ast.BinaryOp):
			if exprnode.op == "+":
				return self._parse_constant(exprnode.left) + self._parse_constant(exprnode.right)
			elif exprnode.op == "-":
				return self._parse_constant(exprnode.left) - self._parse_constant(exprnode.right)
			elif exprnode.op == "*":
				return self._parse_constant(exprnode.left) * self._parse_constant(exprnode.right)
			elif exprnode.op == "/":
				return self._parse_constant(exprnode.left) // self._parse_constant(exprnode.right)
			elif exprnode.op == "%":
				return self._parse_constant(exprnode.left) % self._parse_constant(exprnode.right)
			elif exprnode.op == "&":
				return self._parse_constant(exprnode.left) & self._parse_constant(exprnode.right)
			elif exprnode.op == "|":
				return self._parse_constant(exprnode.left) | self._parse_constant(exprnode.right)
			elif exprnode.op == "^":
				return self._parse_constant(exprnode.left) ^ self._parse_constant(exprnode.right)
			elif exprnode.op == "<<":
				return self._parse_constant(exprnode.left) << self._parse_constant(exprnode.right)
			elif exprnode.op == ">>":
				return self._parse_constant(exprnode.left) >> self._parse_constant(exprnode.right)
			elif exprnode.op == "&&":
				return self._parse_constant(exprnode.left) and self._parse_constant(exprnode.right)
			elif exprnode.op == "||":
				return self._parse_constant(exprnode.left) or self._parse_constant(exprnode.right)
			elif exprnode.op == "==":
				return int(self._parse_constant(exprnode.left) == self._parse_constant(exprnode.right))
			elif exprnode.op == "!=":
				return int(self._parse_constant(exprnode.left) != self._parse_constant(exprnode.right))
			elif exprnode.op == "<=":
				return int(self._parse_constant(exprnode.left) <= self._parse_constant(exprnode.right))
			elif exprnode.op == ">=":
				return int(self._parse_constant(exprnode.left) >= self._parse_constant(exprnode.right))
			elif exprnode.op == "<":
				return int(self._parse_constant(exprnode.left) < self._parse_constant(exprnode.right))
			elif exprnode.op == ">":
				return int(self._parse_constant(exprnode.left) > self._parse_constant(exprnode.right))
		elif isinstance(exprnode, pycparser.c_ast.TernaryOp):
			return self._parse_constant(exprnode.iftrue) if self._parse_constant(exprnode.cond) else self._parse_constant(exprnode.iffalse)
		elif isinstance(exprnode, pycparser.c_ast.Constant):
			# Strip suffixes for long and unsigned ints from constants.
			return super()._parse_constant(pycparser.c_ast.Constant(exprnode.type, exprnode.value.rstrip("LUlu"), exprnode.coord))
		else:
			return super()._parse_constant(exprnode, **kwargs)
	
	def _internal_parse(self, csource):
		ast, macros, csource = self._parse(csource)
		# add the macros
		self._process_macros(macros)
		# find the first "__dotdotdot__" and use that as a separator
		# between the repeated typedefs and the real csource
		iterator = iter(ast.ext)
		for decl in iterator:
			if decl.name == '__dotdotdot__':
				break
		#
		try:
			self._inside_extern_python = False
			for decl in iterator:
				if isinstance(decl, pycparser.c_ast.FuncDef):
					self._parse_decl(decl.decl)
				elif isinstance(decl, pycparser.c_ast.Decl):
					self._parse_decl(decl)
				elif isinstance(decl, pycparser.c_ast.Typedef):
					if not decl.name:
						raise cffi.api.CDefError("typedef does not declare any name", decl)
					quals = 0
					if (isinstance(decl.type.type, pycparser.c_ast.IdentifierType)
							and decl.type.type.names[-1] == '__dotdotdot__'):
						realtype = self._get_unknown_type(decl)
					elif (isinstance(decl.type, pycparser.c_ast.PtrDecl) and
						isinstance(decl.type.type, pycparser.c_ast.TypeDecl) and
						isinstance(decl.type.type.type, pycparser.c_ast.IdentifierType) and
						decl.type.type.type.names == ['__dotdotdot__']):
						realtype = model.unknown_ptr_type(decl.name)
					else:
						realtype, quals = self._get_type_and_quals(
							decl.type, name=decl.name)
					self._declare('typedef ' + decl.name, realtype, quals=quals)
				else:
					raise cffi.api.CDefError("unrecognized construct", decl)
		except cffi.api.FFIError as e:
			msg = self._convert_pycparser_error(e, csource)
			if msg:
				e.args = (e.args[0] + "\n    *** Err: %s" % msg,)
			raise

class FFIWithBetterParser(cffi.api.FFI):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._parser = BetterParser(self)

