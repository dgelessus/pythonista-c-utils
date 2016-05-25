# These are old bits of code that I wrote before this was a repo.
# They didn't do their job well (enough), so they ended up here.
# At least now they aren't inside long string literals throughout the main file.
# Some parts might still be useful.
# Like that attempted macro function vararg processing down there.

def preprocess(lines, macros=None, filename=u"__NOFILENAME__"):
    macros = macros or {}
    macros.update(DEFAULT_MACROS)
    
    def _make_macro_func(argnames, subst):
        def _macro(*args):
            if argnames[-1] == u"...":
                argmap = {
                    name: val
                    for name, val
                    in zip(argnames[:-1], args[:len(argnames)-1])
                }
                
                # This weird for loop inserts a comma token
                # between all varargs
                
                argmap[u"__VA_ARGS__"] = []
                it = iter(args)
                lastname, laststr = next(it)
                
                for tname, tstr in it:
                    argmap[u"__VA_ARGS__"].append((lastname, laststr))
                    argmap[u"__VA_ARGS__"].append(("symbol", u","))
                    lastname, laststr = tname, tstr
                
                argmap[u"__VA_ARGS__"].append((lastname, laststr))
    
    def _expand_macros(tokens):
        expanded = []
        for tname, tstr in tokens:
            # TODO: Macro functions
            if tname == "identifier" and tstr in macros:
                expanded.append(_expand_macros(macros[tstr]))
            else:
                expanded.append(tstr)
        
        return u"".join(expanded)
    
    def _expand_macro_constant(name):
        return _expand_macros((("identifier", name),))
    
    srclineno = 1
    srcfile = filename
    outparts = []
    
    for lineno, line in enumerate(lines):
        lineparts = []
        charno = 0
        
        # Behold, the tri-state boolean!
        # None: This line might or might not be a pp-directive.
        # True: It certainly is.
        # False: It certainly is not.
        is_ppdir = None
        
        # Name of the ppdir, e. g. define.
        # None means the ppdir name was not yet reached.
        ppdir_name = None
        
        # Whether this line's warn ppdir already raised a warning.
        # Without this flag multiple warning messages would be displayed.
        did_warn = False
        
        # (define, undef) Macro name.
        # None means the macro name was not yet reached
        macro_name = None
        
        # (define) Macro function argument names.
        # None means the macro is not a macro function.
        macro_args = None
        
        # (define) Which part of the macro function arg list is
        # expected to come next.
        # ``"start"``: The opening parenthesis.
        # ``"name"``: An argument name.
        # ``"sep"``: A comma (argument separator).
        # ``"end"``: The closing parenthesis.
        # ``"done"``: Macro function arg list is over.
        macro_args_expect = "start"
        
        # (define) Tokens that form the macro substitution.
        macro_subst = []
        
        for tokenno, (tname, tstr) in enumerate(line):
            if is_ppdir is None:
                if tname == "whitespace":
                    lineparts.append(tstr)
                    continue
                elif tname == "symbol" and tstr == u"#":
                    is_ppdir = True
                    lineparts = []
                    continue
                else:
                    is_ppdir = False
            
            if is_ppdir:
                if ppdir_name is None:
                    if tname == "whitespace":
                        pass # Whitespace between # and the ppdir name
                    elif tname == "identifier":
                        if tstr[0] in string.digits:
                            raise PPSyntaxError(
                                "Expected an identifier",
                                u"".join(tstr for tname, tstr in line),
                                lineno, charno,
                            )
                        
                        if line[tokenno+1][0] != "whitespace":
                            raise PPSyntaxError(
                                "Expected whitespace",
                                u"".join(tstr for tname, tstr in line),
                                lineno, charno+len(tstr),
                            )
                        
                        ppdir_name = tstr
                    else:
                        raise PPSyntaxError(
                            "Expected an identifier",
                            u"".join(tstr for tname, tstr in line),
                            lineno, charno,
                        )
                elif ppdir_name == u"error":
                    raise PPErrorDirective(
                        u"".join(tstr for tname, tstr in line[tokenno+1:]),
                        lineno,
                    )
                elif ppdir_name == u"warning":
                    if not did_warn:
                        warnings.warn(PPWarningDirective(
                            u"".join(tstr for tname, tstr in line[tokenno+1:]),
                            lineno,
                        ))
                        did_warn = True
                elif ppdir_name == u"define":
                    # TODO: Function-like macros
                    if macro_name is None:
                        if tname == "whitespace":
                            pass # Whitespace between define and macro name
                        elif tname == "identifier":
                            if tstr[0] in string.digits:
                                raise PPSyntaxError(
                                    "Expected an identifier",
                                    u"".join(tstr for tname, tstr in line),
                                    lineno, charno,
                                )
                            
                            if line[tokenno+1][0] == "whitespace":
                                # Macro constant - skip macro function
                                # argument parsing
                                macro_args_expect = "done"
                            elif (
                                line[tokenno+1][0] == "symbol"
                                and line[tokenno+1][1].startswith(u"(")
                                # ) Go home Pythonista paren matching,
                                # you're drunk.
                                # Yes, Pythonista tries to match parens in
                                # string literals and comments.
                            ):
                                macro_args = []
                            else:
                                raise PPSyntaxError(
                                    "Expected whitespace or macro function args",
                                    u"".join(tstr for tname, tstr in line),
                                    lineno, charno+len(tstr),
                                )
                            
                            macro_name = tstr
                        else:
                            raise PPSyntaxError(
                                "Expected an identifier",
                                u"".join(tstr for tname, tstr in line),
                                lineno, charno,
                            )
                    elif macro_args_expect == "start" and tname == "symbol":
                        if tstr == u"(":
                            macro_args_expect = "name"
                        elif tstr == u"(...":
                            macro_args.append(u"...")
                            macro_args_expect = "end"
                        else:
                            raise PPSyntaxError(
                                'Expected whitespace, identifier or "..."',
                                u"".join(tstr for tname, tstr in line),
                                lineno, charno+1,
                            )
                    elif macro_args_expect == "name":
                        if tname == "whitespace":
                            # Ignore whitespace altogether
                            pass
                        elif tname == "identifier" and tstr[0] not in string.digits:
                            macro_args.append(tstr)
                            macro_args_expect = "sep"
                        elif tname == "symbol" and tstr == u"...":
                            macro_args.append(tstr)
                            macro_args_expect = "end"
                        else:
                            raise PPSyntaxError(
                                'Expected whitespace, identifier or "..."',
                                u"".join(tstr for tname, tstr in line),
                                lineno, charno+1,
                            )
                    elif macro_args_expect == "sep":
                        if tname == "whitespace":
                            # Ignore whitespace altogether
                            pass
                        elif tname == "symbol" and tstr == u",":
                            macro_args.append(tstr)
                            macro_args_expect = "name"
                        elif tname == "symbol" and tstr == u",...":
                            macro_args.append(u"...")
                            macro_args_expect = "end"
                        elif tname == "symbol" and str == u")":
                            macro_args_expect = "done"
                        else:
                            raise PPSyntaxError(
                                'Expected whitespace, identifier, "..." or ")"',
                                u"".join(tstr for tname, tstr in line),
                                lineno, charno+1,
                            )
                    elif macro_args_expect == "end":
                        if tname == "whitespace":
                            # Ignore whitespace altogether
                            pass
                        elif tname == "symbol" and tstr == u")":
                            macro_args_expect = "done"
                    elif (
                        not macro_subst
                        and macro_args_expect == "done"
                        and tname == "whitespace"
                    ):
                        # Ignore whitespace between macro name/args and subst
                        pass
                    else:
                        if not (tname == "whitespace" and u"\n" in tstr):
                            macro_subst.append((tname, tstr))
                elif ppdir_name == u"undef":
                    if macro_name is None:
                        if tname == "whitespace":
                            pass # Whitespace between undef and macro name
                        elif tname == "identifier":
                            if tstr[0] in string.digits:
                                raise PPSyntaxError(
                                    "Expected an identifier",
                                    u"".join(tstr for tname, tstr in line),
                                    lineno, charno,
                                )
                            
                            if (
                                line[tokenno+1][0] != "whitespace"
                                or (line[tokenno+1][0] == "whitespace"
                                    and u"\n" not in line[tokenno+1][1])
                            ):
                                raise PPSyntaxError(
                                    "Expected a newline",
                                    u"".join(tstr for tname, tstr in line),
                                    lineno, charno+len(tstr),
                                )
                            
                            macro_name = tstr
                        else:
                            raise PPSyntaxError(
                                "Expected an identifier",
                                u"".join(tstr for tname, tstr in line),
                                lineno, charno,
                            )
                else:
                    raise PPSyntaxError(
                        'Unknown preprocessor directive "{}"'
                        .format(ppdir_name),
                        u"".join(tstr for tname, tstr in line),
                        lineno, charno,
                    )
            
            else:
                # TODO: Macro functions, respect #if etc.
                lineparts.append(_expand_macro_constant(tstr))
                srclineno += 1
            
            charno += len(tstr)
        
        if ppdir_name == u"define":
            if macro_args is None:
                macros[macro_name] = macro_subst
            else:
                macros[macro_name] = _make_macro_func(macro_args, macro_subst)
        elif ppdir_name == u"undef":
            del macros[macro_name]
        
        outparts.append(u"".join(lineparts))
    
    return u"".join(outparts), macros

def preprocess(s):
    outs = ""
    macros = {}
    false_if_level = 0
    
    for line in s.splitlines():
        if line.startswith("#"):
            # Some preprocessor instruction
            ls = line[1:].split(None, 1)
            name, args = (ls if len(ls) > 1 else ls + [""])
            if name == "error":
                raise PreprocessError(args)
            elif name == "define":
                ms = args.split(None, 1)
                macros[ms[0]] = (ms[1] if len(ms) > 1 else "")
            elif name == "undef":
                del macros[args.rstrip()]
            else:
                print(
                    "Encountered unrecognized preprocessor instruction " + 
                    name + ", ignoring..."
                )
        elif false_if_level == 0:
            # Regular line, outside of false #if(n?def)? block
            outs += line
    
    assert false_if_level == 0
    
    return outs, macros

def something_something_include():
            # yuck, the indentation
            # include from standard directories
            # Angle-bracketed filenames aren't real string literals,
            # so we need to parse them manually.
            name = u""
            state = "before"
            
            for tname, tstr in args:
                if state == "before":
                    if tname == "symbol" and tstr.startswith(u"<"):
                        if tstr.find(u">") != -1:
                            state = "end"
                            name += tstr[1:tstr.find(u">")]
                        else:
                            state = "in"
                            name += tstr[1:]
                    else:
                        raise PPSyntaxError()
                elif state == "in":
                    if tname == "symbol":
                        if tstr.find(u">") == -1:
                            name += tstr
                        elif tstr.find(u">") == len(tstr)-1:
                            state = "end"
                            name += tstr[:-1]
                        else:
                            raise PPSyntaxError()
                    else:
                        name += tstr
                else:
                    if tname != "whitespace":
                        raise PPSyntaxError()
            
            if state != "end":
                raise PPSyntaxError()

