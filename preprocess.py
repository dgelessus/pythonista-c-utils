#!/usr/bin/env python
########################################################################.......
from __future__ import division, print_function

"""Basic C preprocessor in Python. This is intended for use with
``ctypes``/``cffi`` in Pythonista on iOS.

When dealing with C source code, this module uses Unicode strings
exclusively. Internal text is stored in ``str`` strings (which are
still 8-bit in Python 2), for example token names and exception
messages.
"""

import errno
import io
import functools
import os
import re
import string
import sys
import warnings

# Tokens are 2-tuples of their type and a text string.
# When one token ends, this blank token is set as the current token.
# The token type should never be ``None`` for any final token, it is
# only a temporary value.
BLANK_TOKEN = (None, u"")

# "Character class" strings, used to determine token types, check for
# valid identifiers, etc.
WHITESPACE_CHARS = u" \t\n\v\f"
IDENT_CHARS = string.ascii_letters + string.digits + u"_"
SYMBOL_CHARS = u"!#%&()*+,-./:;<=>?@^[]`{|}~"
OCT_DIGITS = string.octdigits + u""
DEC_DIGITS = string.digits + u""
HEX_DIGITS = string.hexdigits + u""

# Trigraphs and digraphs and their substitutions.
TRIGRAPHS = {
    u"??<": u"{",
    u"??>": u"}",
    u"??(": u"[",
    u"??)": u"]",
    u"??=": u"#",
    u"??/": u"\\",
    u"??'": u"^",
    u"??!": u"|",
    u"??-": u"~",
}

DIGRAPHS = {
    u"<%": u"{",
    u"%>": u"}",
    u"<:": u"[",
    u":>": u"]",
    u"%:": u"#",
}

# Parenthesis pairing data. Currently this is only used when
# parsing macro functions, to determine whether a comma means
# the start of a new argument or not. Square brackets are not
# listed here, because in C they cannot contain commas.
PARENS_OPEN = u"({"
PARENS_CLOSE = u")}"
PAREN_PAIRS = list(zip(PARENS_OPEN, PARENS_CLOSE))

# Default macros that are always defined in any :class:`Preprocessor`.
# These macros are not special-cased in any way, user code can redefine
# them like any other macro. Changes to this ``dict`` only affect
# :class:`Preprocessor` instances created afterwards, not existing ones.
DEFAULT_MACROS = {
    # Standard C
    u"__STDC__": [("identifier", u"1")],
    u"__STDC_VERSION__": [("identifier", u"199409L")],
    u"__STDC_HOSTED__": [("identifier", u"1")],
    # Placeholders for __FILE__ and __LINE__
    u"__FILE__": [("string_literal", u'"YOU FORGOT TO SET A FILE NAME"')],
    u"__LINE__": [("identifier", u"0x1D107")],
    # Ignore GCC stuff
    # (Did you know that lambdas kann take *args and **kwargs?)
    u"__attribute__": (lambda *args: []),
    # Pretend that we're clang
    u"__clang__": [],
}

# Simple test code that uses basically all currently supported features
# of the preprocessor.
TEST_CODE = ur"""
#warning This is a soft warning
/* #error This is a hard error */

#define ONE 1
#define TWO 2 /* This is a multiline comment on a single line */
#define THREE 3 // This is a singleline comment
#define TEN 10
#undef TEN

/* This is a multiline comment
 * across multiple lines */

/* This "toggles" the existence of FORTYTWO. */
#ifdef FORTYTWO
#undef FORTYTWO
#else
#define FORTYTWO 42
#endif

#ifndef SIX
#define SIX 6
#endif

#if 0
#error The end is nigh, zero is true!
#elif 1
#define ONE_IS_TRUE 1
#else
#error The end is nigh, one is not true!
#endif

#if defined(ONE) && defined(TWO)
#if ONE < TWO
#define ONE_IS_LT_TWO 1
#else
#error It would appear that you cannot do basic math.
#endif
#endif

/* This is totally necessary for portability.
 * Test macro constants in various situations. */
#define MAINFUNC_RETURNTYPE int
#define MAINFUNC_NAME main
#define MAINFUNC_ARGC_TYPE int
#define MAINFUNC_ARGV_TYPE char **
#define MAINFUNC_ARGS \
    MAINFUNC_ARGC_TYPE argc, MAINFUNC_ARGV_TYPE argv

/* Test macro functions. */
#define ADD(x, y) ((x) + (y))
#define SUB(x, y) ((x) - (y))
#define MUL(x, y) ((x) * (y))
#define DIV(x, y) ((x) / (y))

/* Test special operators in macro functions. */
#define CONCAT(x, y) x##y
#define STRINGIFY(x) #x
#define DUMB_ARRAY_WRAPPER_TEST(x) (x)

/* Test includes.
 * This requires a file "stdbool.h" in the folder "include"
 * of the Script Library, which must do basic stdbool stuff. */
#include <stdbool.h>

#ifndef true
#error Something went wrong when including stdbool.h, true is not defined
#endif

#if false
#error The end is nigh, false from stdbool.h is true!
#endif

MAINFUNC_RETURNTYPE MAINFUNC_NAME(MAINFUNC_ARGS)
{
    /* Test concat and stringify.
     * Also includes a macro function call followed by symbols. */
    char CONCAT(str,ing)[] = STRINGIFY(rope);
    /* Test commas in nested parens inside a macro function arg. */
    string = DUMB_ARRAY_WRAPPER_TEST({'o', 'h', 'a', 'i', '\0'});
    /* Test nested macro functions. */
    return SUB(ADD(ONE, TWO), DIV(SIX, THREE));
}
/* Test that ``preformat`` correctly adds a newline at the end. */"""

class TokenizerError(Exception):
    pass

class PreprocessorError(Exception):
    def __str__(self):
        return self.message

class PreprocessorWarning(UserWarning):
    def __str__(self):
        return self.message

class PPSyntaxError(PreprocessorError):
    def __init__(self, msg=None, line=None, lineno=None, charno=None):
        if msg is None:
            super(PPSyntaxError, self).__init__()
        elif line is None:
            super(PPSyntaxError, self).__init__(msg)
            self.message = msg
        elif lineno is None:
            super(PPSyntaxError, self).__init__(msg, line)
            self.message = line + "\n" + msg
        elif charno is None:
            super(PPSyntaxError, self).__init__(msg, line, lineno)
            self.message = ("Line {lineno}\n"
                "{line}\n"
                "{msg}".format(
                    lineno=lineno,
                    line=line,
                    msg=msg,
                )
            )
        else:
            super(PPSyntaxError, self).__init__(msg, line, lineno, charno)
            self.message = ("Line {lineno}, char {charno}\n"
                "{line}\n"
                "{marker:>{charno}}\n"
                "{msg}".format(
                    lineno=lineno,
                    charno=charno,
                    line=line,
                    marker="^",
                    msg=msg,
                )
            )

class IncludeNotFoundError(PreprocessorError):
    def __init__(self, name):
        super(IncludeNotFoundError, self).__init__(name)
        self.message = "Include file {name!r} not found".format(name=name)

class PPErrorDirective(PreprocessorError):
    def __init__(self, msg, lineno):
        super(PPErrorDirective, self).__init__(msg, lineno)
        self.message = "Line {lineno}: {msg}".format(
            lineno=lineno, msg=msg)

class PPWarningDirective(PreprocessorWarning):
    def __init__(self, msg, lineno):
        super(PPWarningDirective, self).__init__(msg, lineno)
        self.message = "Line {lineno}: {msg}".format(
            lineno=lineno, msg=msg)

class UnknownPragmaWarning(PreprocessorWarning):
    def __init__(self, pragma, lineno):
        super(UnknownPragmaWarning, self).__init__(args, lineno)
        self.message = "Line {lineno}: Unknown pragma: {pragma}".format(
            lineno=lineno, pragma=pragma)

def preformat(src, trigraphs=False, digraphs=False):
    """Perform pre-tokenization tasks on src.
    
    This includes:
    
    * Replacing alternative new line formats (``"\r\n"`` and ``"\r"``)
        with ``"\n"``
    * Replacing trigraphs and digraphs, if explicitly enabled;
        they are almost never used in public/production code, and the
        replacement algorithm isn't perfect.
    * Backslash-joining of lines
    * Ensuring that src ends with a new line
    
    src is expected to be a Unicode string, i. e. it should be
    already decoded. Byte strings are not guaranteed to work, and the
    returned string will always be a Unicode string.
    """
    
    # Unify newline variants
    src = src.replace(u"\r\n", u"\n").replace(u"\r", u"\n")
    
    # If enabled, replace trigraphs with their "real" counterparts
    if trigraphs:
        for tri, char in TRIGRAPHS.items():
            src = src.replace(tri, char)
    
    # If enabled, replace digraphs with their "real" counterparts
    if digraphs:
        for di, char in DIGRAPHS.items():
            src = src.replace(di, char)
    
    # Ensure that the last character is a newline
    if not src.endswith(u"\n"):
        src += u"\n"
    
    # Join backslash-joined lines
    src = src.replace(u"\\\n", u"")
    
    # Ensure *again* that the last character is a newline
    if not src.endswith(u"\n"):
        src += u"\n"
    
    return src

def _tokenize_internal(src):
    """Internal tokenizer genfunc. Produces tokens without sanity checks."""
    
    tname, tstr = BLANK_TOKEN
    string_escaped = False
    
    for i, c in enumerate(src):
        if tname == "block_comment":
            # Inside block comment
            tstr += c
            if c == u"/" and src[i-1] == "*":
                yield tname, tstr
                tname, tstr = BLANK_TOKEN
                continue
        
        elif tname == "line_comment":
            # Inside line comment
            if c == u"\n":
                yield tname, tstr
                tname, tstr = BLANK_TOKEN
            tstr += c
        
        elif tname == "whitespace":
            # Inside whitespace
            if c not in WHITESPACE_CHARS:
                yield tname, tstr
                tname, tstr = BLANK_TOKEN
            tstr += c
        
        elif tname == "string_literal":
            # Inside string literal
            tstr += c
            if string_escaped:
                string_escaped = False
            elif c == u"\\":
                string_escaped = True
            elif c == u'"':
                yield tname, tstr
                tname, tstr = BLANK_TOKEN
                continue
        
        elif tname == "char_literal":
            # Inside character literal
            tstr += c
            if string_escaped:
                string_escaped = False
            elif c == u"\\":
                string_escaped = True
            elif c == u"'":
                yield tname, tstr
                tname, tstr = BLANK_TOKEN
                continue
        
        elif tname == "identifier":
            # Inside identifier
            if c not in IDENT_CHARS:
                yield tname, tstr
                tname, tstr = BLANK_TOKEN
            tstr += c
        
        elif tname == "symbol":
            # Inside symbol sequence
            if c == u"*" and src[i-1] == u"/":
                tname = "block_comment"
            elif c == u"/" and src[i-1] == u"/":
                tname = "line_comment"
            elif c not in SYMBOL_CHARS:
                yield tname, tstr
                tname, tstr = BLANK_TOKEN
            tstr += c
        
        else:
            # Some other case, just append the character.
            tstr += c
        
        if tname is None:
            # Figure out what token type this is
            if c in WHITESPACE_CHARS:
                tname = "whitespace"
            elif c == u'"':
                tname = "string_literal"
            elif c == u"'":
                tname = "char_literal"
            elif c in IDENT_CHARS:
                tname = "identifier"
            elif c in SYMBOL_CHARS:
                tname = "symbol"
    
    # Yield the last token
    yield tname, tstr

def tokenize(src, replace_comments=True):
    """Tokenize src and yield tokens in the form ``(tname, tstr)``.
    
    ``tname`` is one of the following:
    
    * ``"block_comment"``: A block comment delimited by ``"/*"``
        and ``"*/"``.
    * ``"line_comment"``: A line comment, delimited by ``"//"``
        and ``"\n"``.
    * ``"whitespace"``: A sequence of whitespace characters. (If enabled,
        the above two token types will be replaced by a single space
        whitespace token, and joined with adjacent whitespace tokens.)
    * ``"string_literal"``: A string literal, delimited by
        ``'"'`` characters.
    * ``"char_literal"``: A char literal, delimited by
        ``"'"`` characters.
    * ``"identifier"``: A sequence of alphanumeric characters. (This
        also includes language keywords and parts of number literals.)
    * ``"symbol"``: A sequence of symbol characters.
    
    ``tstr`` is the character sequence of the token.
    
    If the last token is not whitespace, an exception is raised instead
    of yielding the token. (C source files are required to end in a
    newline, which is whitespace. The preformat function ensures this.)
    """
    
    token_geniter = _tokenize_internal(src)
    lastname, laststr = next(token_geniter)
    
    if replace_comments and lastname in ("block_comment", "line_comment"):
        lastname, laststr = "whitespace", u" "
    
    for tname, tstr in token_geniter:
        ##print(tname, tstr, lastname, laststr)
        
        if replace_comments and tname in ("block_comment", "line_comment"):
            tname, tstr = "whitespace", u" "
        
        # Join adjacent tokens of same type.
        # This should only happen when comments are replaced.
        if lastname == tname:
            laststr += tstr
        else:
            yield lastname, laststr
            lastname, laststr = tname, tstr
    
    # Check that everything was closed correctly
    if not (lastname == "whitespace" and laststr.endswith(u"\n")):
        raise TokenizerError(
            "Last token is not a newline - did you forget to close"
            " a comment or a literal, or is the code not preformatted?"
        )
    
    # Yield the last token
    yield lastname, laststr

def linesplit(tokens):
    """Split an iterable of tokens into lines and yield them.
    
    Each line is a sequence of tokens. The last token is always
    a whitespace token that ends with ``"\n"``. This means that
    combining all lines into one sequence, then joining all token
    strings results in a valid program again.
    """
    
    line = []
    
    for tname, tstr in tokens:
        if tname == "whitespace" and u"\n" in tstr:
            for match in re.finditer(ur"[^\n]*\n", tstr):
                line.append((tname, tstr[match.start():match.end()]))
                yield line
                line = []
            
            if match.end() != len(tstr):
                line.append((tname, tstr[match.end():]))
        else:
            line.append((tname, tstr))

def check_token_types(tokens, types):
    """Return whether the types of the iterable ``tokens`` match
    the types specified in the iterable ``types``."""
    
    if len(tokens) != len(types):
        return False
    
    for (tname, tstr), wantname in zip(tokens, types):
        if tname != wantname:
            return False
    
    return True

def join_tokens(tokens):
    """Convert the iterable ``tokens`` back to a single string."""
    
    return u"".join(tstr for tname, tstr in tokens)

def clean_code(src):
    """Preformat and tokenize the string ``src``, and return the
    tokens joined together again."""
    return join_tokens(tokenize(preformat(src)))

def count_parens(s):
    return sum(
        s.count(start) - s.count(end)
        for start, end in PAREN_PAIRS
    )

def simple_string_escape(s):
    return s.replace(u"\\", ur"\\").replace(u"\"", ur"\"")

class Preprocessor(object):
    def __init__(self, macros=None, include_dirs=None, encoding="utf8"):
        self.macros = dict(DEFAULT_MACROS)
        if macros is not None:
            self.macros.update(macros)
        self.macros[u"_Pragma"] = (lambda *args: self.pragma(args) or [])
        self.macros[u"defined"] = (lambda name: [("identifier",
            unicode(int(join_tokens(name).strip() in self.macros)))])
        
        self.include_dirs = ([] if include_dirs is None else include_dirs)
        self.include_dirs.append(os.path.expanduser(u"~/Documents/include"))
        
        self.encoding = encoding
        
        # Preprocessor state
        self.filename = u"__NOFILENAME__"
        self.lineno = 1
        self.output_lines = []
        self.if_stack = ["true"]
    
    def update_filename(self, new):
        self.filename = new
        self.macros[u"__FILE__"] = [("string_literal",
            u'"' + simple_string_escape(new) + u'"')]
    
    def update_lineno(self, new):
        self.lineno = new
        self.macros[u"__LINE__"] = [("identifier", unicode(self.lineno))]
    
    def exec_macro_function(self, subst, argnames, *argvals):
        argmap = {name: argvals[i] for i, name in enumerate(argnames)}
        outtokens = []
        stringify_next = False
        
        for tokenno, (tname, tstr) in enumerate(subst):
            if tname == "identifier" and tstr in argmap:
                if stringify_next:
                    outtokens.append(("string_literal", u'"'
                        + simple_string_escape(join_tokens(argmap[tstr]))
                        + u'"'))
                    stringify_next = False
                else:
                    outtokens += argmap[tstr]
            elif tname == "symbol" and tstr.endswith(u"##"):
                outtokens.append((tname, tstr[:-2]))
            elif tname == "symbol" and tstr.endswith(u"#"):
                stringify_next = True
                outtokens.append((tname, tstr[:-1]))
            else:
                outtokens.append((tname, tstr))
        
        return outtokens
    
    def eval_condition(self, args):
        while True:
            cond = self.expand_macros(args)
            try:
                return bool(int(cond, base=0))
            except ValueError:
                print("Please enter the result of the following expression:")
                print(cond)
                args = tokenize(preformat(unicode(raw_input("> "))))
    
    def include(self, name, extra_dirs=[]):
        last_err = None
        for dir in extra_dirs + self.include_dirs:
            try:
                old_filename, old_lineno = self.filename, self.lineno
                
                with io.open(os.path.join(dir, name), "r") as f:
                    self.preprocess_tokens(name, tokenize(preformat(f.read())))
                
                self.update_filename(old_filename)
                self.update_lineno(old_lineno)
                break
            except IOError as err:
                if err.errno != errno.ENOENT:
                    raise
        else:
            raise IncludeNotFoundError(name)
    
    def pragma(self, args):
        warnings.warn(UnknownPragmaWarning(join_tokens(args), self.srclineno))
    
    def ppdir(self, name, args):
        ##print(u"# {!r} {!r}".format(name, args))
        if self.if_stack[-1] != "true" and name not in ("elif", "else", "endif"):
            return
        
        try:
            return getattr(self, str("ppdir_" + name))(args)
        except PPSyntaxError as err:
            raise PPSyntaxError(
                err.args[0] if len(err.args) > 0 else "Invalid #{} directive".format(name),
                err.args[1] if len(err.args) > 1 else join_tokens(args),
                err.args[2] if len(err.args) > 2 else self.lineno,
            )
    
    def ppdir_define(self, args):
        if (
            check_token_types(args, ("identifier",))
            or check_token_types(args[:2], ("identifier", "whitespace"))
        ):
            self.macros[args[0][1]] = args[2:]
        elif (
            check_token_types(args[:2], ("identifier", "symbol"))
            and args[1][1].startswith(u"(") # )
        ):
            expect = "argname"
            argnames = []
            subst = []
            
            for tokenno, (tname, tstr) in enumerate(args[2:], 2):
                if tname == "whitespace":
                    if expect == "end":
                        subst = args[tokenno+1:]
                        break
                    # Whitespace is ignored otherwise
                elif (
                    expect == "argname"
                    and tname == "identifier"
                    and tstr[0] not in DEC_DIGITS
                ):
                    argnames.append(tstr)
                    expect = "sep"
                elif (
                    expect == "sep"
                    and tname == "symbol"
                    and tstr == u","
                ):
                    expect = "argname"
                elif (
                    expect == "sep"
                    and tname == "symbol"
                    and tstr == u")"
                ):
                    expect = "end"
            
            self.macros[args[0][1]] = functools.partial(
                self.exec_macro_function, subst, argnames)
        else:
            raise PPSyntaxError()
    
    def ppdir_elif(self, args):
        if self.if_stack[-1] == "ignore":
            pass
        elif self.if_stack[-1] == "wait":
            self.if_stack[-1] = ("true" if self.eval_condition(args) else "wait")
        elif self.if_stack[-1] == "true":
            self.if_stack[-1] = "ignore"
        else:
            print("Unknown if stack status: {}".format(self.if_stack[-1]))
    
    def ppdir_else(self, args):
        if self.if_stack[-1] == "ignore":
            pass
        elif not check_token_types(args, ()):
            raise PPSyntaxError()
        elif self.if_stack[-1] == "wait":
            self.if_stack[-1] = "true"
        elif self.if_stack[-1] == "true":
            self.if_stack[-1] = "ignore"
        else:
            print("Unknown if stack status: {}".format(self.if_stack[-1]))
    
    def ppdir_endif(self, args):
        if check_token_types(args, ()):
            self.if_stack.pop()
            if not self.if_stack:
                self.if_stack.push("true")
                raise PPSyntaxError("Unbalanced #endif")
        else:
            raise PPSyntaxError()
    
    def ppdir_error(self, args):
        raise PPErrorDirective(join_tokens(args), self.lineno)
    
    def ppdir_if(self, args):
        if self.if_stack[-1] in ("ignore", "wait"):
            self.if_stack.append("ignore")
        elif self.if_stack[-1] == "true":
            self.if_stack.append("true" if self.eval_condition(args) else "wait")
        else:
            print("Unknown if stack status: {}".format(self.if_stack[-1]))
    
    def ppdir_ifdef(self, args):
        if self.if_stack[-1] in ("ignore", "wait"):
            self.if_stack.append("ignore")
        elif not check_token_types(args, ("identifier",)):
            raise PPSyntaxError()
        elif self.if_stack[-1] == "true":
            self.if_stack.append("true" if args[0][1] in self.macros else "wait")
        else:
            print("Unknown if stack status: {}".format(self.if_stack[-1]))
    
    def ppdir_ifndef(self, args):
        if self.if_stack[-1] in ("ignore", "wait"):
            self.if_stack.append("ignore")
        elif not check_token_types(args, ("identifier",)):
            raise PPSyntaxError()
        elif self.if_stack[-1] == "true":
            self.if_stack.append("wait" if args[0][1] in self.macros else "true")
        else:
            print("Unknown if stack status: {}".format(self.if_stack[-1]))
    
    def ppdir_include(self, args):
        name = self.expand_macros(args)
        # TODO: Properly unquote file names
        if name.startswith(u'"') and name.endswith(u'"'):
            # include from CWD
            self.include(name[1:-1], [os.getcwdu()])
        elif name.startswith(u"<") and name.endswith(u">"):
            self.include(name[1:-1])
        else:
            raise PPSyntaxError()
    
    def ppdir_line(self, args):
        if check_token_types(args, ("identifier",)):
            self.lineno = int(args[0][1])
        elif check_token_types(args,
            ("identifier", "whitespace", "string_literal")
        ):
            self.lineno = int(args[0][1])
            # TODO: Properly unquote the string literal
            self.filename = args[2][1][1:-1]
            
            self.macros[u"__LINE__"] = [args[0]]
            self.macros[u"__FILE__"] = [args[2]]
        else:
            raise PPSyntaxError()
    
    def ppdir_pragma(self, args):
        self.pragma(args)
    
    def ppdir_undef(self, args):
        if check_token_types(args, ("identifier",)):
            del self.macros[args[0][1]]
        else:
            raise PPSyntaxError()
    
    def ppdir_warning(self, args):
        warnings.warn(
            PPWarningDirective(join_tokens(args), self.lineno))
    
    def expand_macros(self, tokens):
        """Expand all macros in an iterable of tokens and return
        the result as a normal string."""
        
        ##print("expand", tokens)
        outparts = []
        
        # Macro-func-related
        macro_func = None
        macro_func_args = [[]]
        ignore_start_paren = 0
        nparens = 1
        
        for tokenno, (tname, tstr) in enumerate(tokens):
            ##print("parse", tname, tstr)
            if macro_func is not None:
                if tname == "symbol":
                    # Iterate through all characters and handle paren nesting
                    # and argument separation.
                    # Manually advance the iterator once to skip to the first comma.
                    parts = iter(tstr[ignore_start_paren:].split(u","))
                    ignore_start_paren = 0
                    part = next(parts)
                    nparens += count_parens(part)
                    ##print("nparens", nparens)
                    
                    if part and nparens > 0:
                        ##print("append_first_arg", part)
                        macro_func_args[-1].append((tname, part))
                    
                    for part in parts:
                        ##print(part, nparens)
                        if nparens <= 0:
                            break
                        
                        if nparens == 1:
                            ##print("new_arg", part)
                            macro_func_args.append([(tname, part)] if part else [])
                        else:
                            ##print("append_comma", part)
                            macro_func_args[-1].append((tname, u"," + part))
                        
                        nparens += count_parens(part)
                        ##print("nparens", nparens)
                    
                    if nparens <= 0:
                        ##print("closing", part)
                        # Find where the macro function call's closing paren is,
                        # it might not be the last character (or even the last paren)
                        # of the token.
                        lasti = None
                        ##print("lasti", lasti)
                        
                        for _ in range(nparens, 1):
                            ##print(part, lasti, _)
                            lasti = max(part.rfind(c, lasti) for c in PARENS_CLOSE)
                            ##print("lasti", lasti)
                        
                        if lasti is None:
                            lasti = -1
                        
                        if part[:lasti]:
                            macro_func_args[-1].append((tname, part[:lasti]))
                        
                        ##print(macro_func_args)
                        outparts.append(self.expand_macros(
                            macro_func(*macro_func_args)))
                        
                        if part[lasti+1:]:
                            outparts.append(part[lasti+1:])
                        
                        macro_func = None
                        macro_func_args = [[]]
                        
                        if nparens != 0:
                            raise PPSyntaxError(
                                "Unbalanced parens in macro function call",
                                join_tokens(tokens),
                                self.lineno,
                            )
                        
                        nparens = 1
                else:
                    macro_func_args[-1].append((tname, tstr))
                            
            elif tname == "identifier" and tstr in self.macros:
                subst = self.macros[tstr]
                
                if callable(subst):
                    if (
                        tokens[tokenno+1][0] == "symbol"
                        and tokens[tokenno+1][1].startswith(u"(") # )
                    ):
                        macro_func = subst
                        ignore_start_paren = 1
                        continue
                    else:
                        subst = tstr
                else:
                    subst = self.expand_macros(subst)
                
                outparts.append(subst)
            else:
                outparts.append(tstr)
        
        return u"".join(outparts)
    
    def preprocess_token_line(self, tokens):
        """Preprocess a single line.
        
        This automatically increments the line number afterwards.
        """
        ppdir_found = False
        
        for tokenno, (tname, tstr) in enumerate(tokens):
            ##print("parse", ppdir_found, tokenno, tname, tstr)
            if not ppdir_found:
                if tname == "whitespace":
                    continue
                elif tname == "symbol" and tstr == u"#":
                    ppdir_found = True
                    continue
                else:
                    # Line is not a ppdir, expand macros and break
                    if self.if_stack[-1] == "true":
                        self.output_lines.append(self.expand_macros(tokens))
                    break
            else:
                if tname == "whitespace":
                    pass # Wait for non-whitespace
                elif tname == "identifier":
                    if tokens[tokenno+1][0] != "whitespace":
                        raise PPSyntaxError(
                            "Invalid preprocessor directive",
                            join_tokens(tokens),
                            self.lineno,
                        )
                    
                    self.ppdir(tstr, tokens[tokenno+2:-1])
                    break
                else:
                    raise PPSyntaxError(
                        "Invalid preprocessor directive",
                        join_tokens(tokens),
                        self.lineno,
                    )
        
        self.update_lineno(self.lineno + 1)
    
    def preprocess_tokens(self, filename, tokens):
        """Preprocess tokens from a file.
        
        This automatically sets the file name to ``filename``
        and the line number to ``1`` before any preprocessing.
        """
        
        self.update_filename(filename)
        self.update_lineno(1)
        
        for line in linesplit(tokens):
            self.preprocess_token_line(line)
