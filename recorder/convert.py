def load_log_defs(def_file):
    defs = dict()
    with open(def_file) as rf:
        for line in rf:
            fields = line.split(' ')
            defs[fields[0]] = list()
            for fi in fields[1:]:
                vtype, name = fi.split(':')
                defs[fields[0]].append((vtype, name))
    return defs


def compose_from_def(defs, r):
    if 'type' not in r or r['type'] not in defs:
        return None
    fields = defs[r['type']]
    values = [r[fi[1].strip()] for fi in fields]
    # print(values)
    return ' '.join(['{}'.format(value) for value in values])


def decode_with_def(defs, line):
    fields = line.split(' ')
    kw = fields[2].split('.')[-1]
    if kw not in defs:
        print(kw, 'not in defs')
        return None
    if len(defs[kw]) < len(fields) - 3:
        print('log line length grater than def', kw)
        print()
        return None
    r = dict()
    for idx, fi in enumerate(fields[3:]):
        vtype, name = defs[kw][idx]
        if vtype == 'fl':
            value = float(fi)
        elif vtype == 'int':
            value = int(fi)
        elif vtype == 'str':
            value = fi
        elif vtype == 'hex':
            value = int(fi, 16)
        else:
            value = fi
        r[name] = value
    return r


ub482_defs = load_log_defs('config/logdefs/ub482.logdef')
