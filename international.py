from re import search

in_key_bindings = {
    'f': 'agrave',
    ',': 'aacute',
    'd': 'acircumflex',
    'u': 'atilde',
    'l': 'adiaeresis',
    't': 'aring',
    '`': 'cedilla',
    ';': 'ae',
    'p': 'ccedilla',
    'b': 'egrave',
    'q': 'eacute',
    'r': 'ecircumflex',
    'k': 'ediaeresis',
    'v': 'igrave',
    'y': 'iacute',
    'j': 'icircumflex',
    'g': 'idiaeresis',
    'h': 'eth',
    'c': 'ntilde',
    'n': 'ograve',
    'e': 'oacute',
    'a': 'ocircumflex',
    '[': 'otilde',
    'w': 'odiaeresis',
    'x': 'division',
    'i': 'oslash',
    'o': 'ugrave',
    ']': 'uacute',
    's': 'ucircumflex',
    'S': 'Ucircumflex',
    'm': 'udiaeresis',
    '\'': 'yacute',
    '.': 'thorn',
    'z': 'ydiaeresis'
}


def bind_int(event, func, handler):
    result = search('<Control-(.)>', event)
    func(event, handler)
    if result is not None:
        key = result.group(1)
        russian = in_key_bindings[key]
        new_bind = '<Control-{}>'.format(russian)
        func(new_bind, handler)
