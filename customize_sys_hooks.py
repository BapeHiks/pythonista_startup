"""Register a custom sys.displayhook and sys.excepthook.

The colors will use your current theme, with an average value between the text color and the error color, so that you can distinguish in the console where you entered something and where an exception occurred.

Features of the displayhook:
* Basic IPython-style output history. There is a global list named Out (technically added to the builtins/__builtin__ module) which contains the results of all expressions run in the interactive console.
* The result lines show at which position in the Out list the result can be found, for later reference.
* Like the default displayhook, expressions that return None are ignored - nothing is printed, and the value of _ is not changed. This can be changed so that None is displayed and stored in _ and Out, by uncommmenting a line in the displayhook definition.

Features of the excepthook:
* A little more whitespace to make the traceback more readable.
* The traceback uses different colors for text, file paths, line numbers, etc.
* Syntax errors use Unicode magic and color changing to mark at which character the syntax error occurred.
* Source file paths are shortened and do not show the long path of the app sandbox.
* is the link that runs "pythonista3://?exec=" where the code to import the editor and open the file in a new tab and add an annotation to the line in which the exception occurred.
* Python 3 chained exceptions *should* work. No, that cannot be backported to Python 2.
"""

from __future__ import absolute_import, division, print_function

def run():
    try:
        import builtins
    except ImportError:
        import __builtin__ as builtins
    import console
    import os
    import sys
    import traceback
    try:
        from urllib.parse import quote
    except ImportError:
        from urllib import quote
    from objc_util import ObjCClass, UIColor
    
    print(u"Customizing sys hooks...")
    
    APP_GROUP_DIR = os.path.expanduser(u"~")
    if os.path.basename(APP_GROUP_DIR) == u"Pythonista3":
        APP_GROUP_DIR = os.path.dirname(APP_GROUP_DIR)
    APP_GROUP_DIR += os.sep
    APP_DIR = u"" + os.path.dirname(os.path.dirname(sys.executable)) + os.sep
    
    REMOVE_PREFIXES = (APP_GROUP_DIR, APP_DIR)
    
    DOCUMENTS = os.path.expanduser("~/Documents")
    
    def write_filename(path, lineno):
        if path.startswith(u"<") and path.endswith(u">"):
            print(path, end=u"")
        else:
            short_path = path
            
            for prefix in REMOVE_PREFIXES:
                if short_path.startswith(prefix):
                    short_path = path[len(prefix):]
                    break

            console.write_link(
                short_path,
                (u"pythonista3://"
                 if os.path.basename(sys.executable) == "Pythonista3" else
                 u"pythonista://") +
                u"?exec=import editor;%20editor.open_file('{p}', new_tab %3D True); editor.annotate_line({l})".
                format(p=os.path.realpath(path), l=lineno).replace(' ', '%20'))
            #u"pythonista://") + quote(os.path.relpath(path, DOCUMENTS)))

    theme_dict = ObjCClass('PA2UITheme').sharedTheme().themeDict()

    #default_error_color = [round(float(str(l)), 2) for l in UIColor.colorWithHexString_(theme_dict["error_text"]).arrayFromRGBAComponents()][:3]
    def hex2rgb(hexcolor):
        return [
            round(float(str(l)), 2)
            for l in UIColor.colorWithHexString_(hexcolor)
            .arrayFromRGBAComponents()
        ][:3]

    def set_color(type_text='default'):
        default_error_color = hex2rgb(theme_dict["error_text"])
        if type_text == 'default':  ####
            console.set_color(*default_error_color)
            return
        elif type_text == 'default_text':
            console.set_color(*hex2rgb(theme_dict["default_text"]))
            return
        elif type_text == 'filename':
            thcolor = 'default'
        elif type_text == 'lineno':
            thcolor = 'number'
        elif type_text == 'funcname':
            thcolor = 'function'
        dtrgb = hex2rgb(theme_dict["scopes"][thcolor]['color'])

        mean_color = [
            round((dtrgb[i] + default_error_color[i]) / 2, 2) for i in range(3)
        ]
        console.set_color(*mean_color)


    def displayhook(obj):
        # Uncomment the next line if you want None to be "visible" like any other object.
        #"""
        if obj is None:
            return
        #"""
        
        try:
            builtins.Out
        except AttributeError:
            builtins.Out = []
        
        builtins._ = obj
        builtins.Out.append(obj)
        console.set_color(0.0, 0.5, 0.0)
        print(u"Out[{}]".format(len(builtins.Out) - 1), end=u"")
        set_color('default_text')
        print(u" = ", end=u"")
        console.set_color(*hex2rgb(theme_dict["text_selection_tint"]))
        print(repr(obj))
        set_color('default_text')
    sys.displayhook = displayhook
    
    def _excepthook(exc_type, exc_value, exc_traceback):
        set_color()
        print(u"Traceback (most recent call last):")

        for filename, lineno, funcname, text in traceback.extract_tb(
                exc_traceback):

            set_color()
            print(u"\tFile ", end=u"")
            set_color('filename')
            write_filename(filename, lineno)
            set_color()
            print(u", line ", end=u"")
            set_color('lineno')
            print(lineno, end=u"")
            set_color()
            print(u", in ", end=u"")
            set_color('funcname')
            print(funcname, end=u"")
            set_color()
            print(u":")
            set_color()
            if isinstance(text, bytes):
                text = text.decode(u"utf-8", u"replace")
            print(u"\t\t" + (text or u"# Source code unavailable"))
            print()
        
        if issubclass(exc_type, SyntaxError):
            set_color()
            print(u"\tFile ", end=u"")
            set_color('filename')
            write_filename(exc_value.filename)
            set_color()
            print(u", line ", end=u"")
            set_color('lineno')
            print(exc_value.lineno, end=u"")
            set_color()
            print(u":")
            
            if exc_value.text is None:
                set_color()
                print(u"\t\t# Source code unavailable")
            else:
                etext = exc_value.text
                if isinstance(etext, bytes):
                    etext = etext.decode(u"utf-8", u"replace")
                set_color()  #####
                print(u"\t\t" + etext[:exc_value.offset], end=u"")
                console.set_color(0.75, 0.0, 0.0)
                print(u"\N{COMBINING LOW LINE}" + etext[exc_value.offset:].rstrip())
        set_color('filename')
        print(exc_type.__module__, end=u"")
        set_color()
        print(u".", end=u"")
        set_color('funcname')
        print(getattr(exc_type, "__qualname__", exc_type.__name__), end=u"")

        msg = exc_value.msg if issubclass(exc_type,
                                          SyntaxError) else str(exc_value)

        if msg:
            set_color()
            print(u": ", end=u"")
            #set_color()
            print(msg, end=u"")
        #console.set_color(0.2, 0.2, 0.2)
        print()
    
    def excepthook(exc_type, exc_value, exc_traceback):
        try:
            # On Python 2, exceptions have no __cause__, __context__ or __supress_context__.
            if getattr(exc_value, "__cause__", None) is not None:
                excepthook(exc_value.__cause__.__class__, exc_value.__cause__,
                           exc_value.__cause__.__traceback__)
                console.set_color(0.75, 0.0, 0.0)
                print()
                print(u"The above exception was the direct cause of the following exception:")
                print()
            elif getattr(
                    exc_value, "__context__",
                    None) is not None and not exc_value.__suppress_context__:
                excepthook(exc_value.__context__.__class__,
                           exc_value.__context__,
                           exc_value.__context__.__traceback__)
                console.set_color(0.75, 0.0, 0.0)
                print()
                print(u"During handling of the above exception, another exception occurred:")
                print()
            
            _excepthook(exc_type, exc_value, exc_traceback)
        except Exception as err:
            traceback.print_exc()
        finally:
            set_color("default_text")
    # sys.excepthook can't be customized, Pythonista overrides it on every script run.
    # So we need to override sys.__excepthook__ instead.
    
    sys.__excepthook__ = excepthook
    
    print(u"Done customizing sys hooks.")

if __name__ == "__main__":
    run()