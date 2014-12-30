
# Retrieved from ansible. It's better to use the original one, but its package recentry
# changed, so decided to have another one.
def json_dict_unicode_to_bytes(d):
    ''' Recursively convert dict keys and values to byte str

        Specialized for json return because this only handles, lists, tuples,
        and dict container types (the containers that the json module returns)
    '''

    if isinstance(d, unicode):
        return d.encode('utf-8')
    elif isinstance(d, dict):
        return dict(map(json_dict_unicode_to_bytes, d.iteritems()))
    elif isinstance(d, list):
        return list(map(json_dict_unicode_to_bytes, d))
    elif isinstance(d, tuple):
        return tuple(map(json_dict_unicode_to_bytes, d))
    else:
        return d
