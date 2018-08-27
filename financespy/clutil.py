import sys

_functions = {}

def _is_parameter(s):
    return s.strip().startswith("-")

def _list_to_dict(l):

    it = iter(l)
    d = {'args': []}
    key = next(it, None)

    while True:
        if key is None:
            break
        if _is_parameter(key):
            value = next(it, None)

            if value is None:
                d[key[1:]] = True
                break

            if _is_parameter(value):
                d[key[1:]] = True
                key = value
            else:
                d[key[1:]] = value
                key = next(it, None)
        else:
            d['args'].append(key)
            break

    for i in it:
        d['args'].append(i)

    return d

def Command( func ):
    _functions[func.__name__] = func
    return func

@Command
def _list_commands( args ):
    commands = list( _functions.keys() )
    commands.remove("_list_commands")
    list.sort(commands)
    print( " ".join(commands) )



def execute():
    it = iter(sys.argv[1:])
    com = next(it, None)

    if com is None:
        print("Command not found")
    else:
        if  com in _functions:
            args = _list_to_dict(it)
            func = _functions[com]
            func(** args)
        else:
            print("Command not found")
