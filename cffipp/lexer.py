"""Lexer part of the preprocessor. Based on ply/cpp.py from the PLY library by David Beazley (http://www.dabeaz.com). See the LICENSE file for license info."""

import ply
import ply.lex

__all__ = [
	"build",
]

# Default preprocessor lexer definitions. These tokens are enough to get
# a basic preprocessor working. Other modules may import these if they want.

tokens = (
	'CPP_ID',
	'CPP_INTEGER',
	'CPP_FLOAT',
	'CPP_STRING',
	'CPP_CHAR',
	'CPP_WS',
	'CPP_COMMENT1',
	'CPP_COMMENT2',
	'CPP_POUND',
	'CPP_DPOUND',
)

literals = "+-*/%|&~^<>=!?()[]{}.,;:\\\'\""

# Whitespace
def t_CPP_WS(t):
	r'\s+'
	t.lexer.lineno += t.value.count("\n")
	return t

t_CPP_POUND = r'\#'
t_CPP_DPOUND = r'\#\#'

# Identifier
t_CPP_ID = r'[A-Za-z_][\w_]*'

# Integer literal
def CPP_INTEGER(t):
	r'(((((0x)|(0X))[0-9a-fA-F]+)|(\d+))([LUlu]*))'
	return t

t_CPP_INTEGER = CPP_INTEGER

# Floating literal
t_CPP_FLOAT = r'((\d+)(\.\d+)(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))([FLfl]*)'

# String literal
def t_CPP_STRING(t):
	r'\"([^\\\n]|(\\(.|\n)))*?\"'
	t.lexer.lineno += t.value.count("\n")
	return t

# Character constant 'c' or L'c'
def t_CPP_CHAR(t):
	r'(L)?\'([^\\\n]|(\\(.|\n)))*?\''
	t.lexer.lineno += t.value.count("\n")
	return t

# Comment
def t_CPP_COMMENT1(t):
	r'(/\*(.|\n)*?\*/)'
	ncr = t.value.count("\n")
	t.lexer.lineno += ncr
	# replace with one space or a number of '\n'
	t.type = 'CPP_WS'
	t.value = '\n' * ncr if ncr else ' '
	return t

# Line comment
def t_CPP_COMMENT2(t):
	r'(//.*?(\n|$))'
	# replace with '\n'
	t.type = 'CPP_WS'
	t.value = '\n'
	return t
	
def t_error(t):
	t.type = t.value[0]
	t.value = t.value[0]
	t.lexer.skip(1)
	return t

def build(*args, **kwargs):
	return ply.lex.lex(*args, **kwargs)

