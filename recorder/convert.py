def load_log_defs(def_file):
    defs = dict()
    with open(def_file) as rf:
        for line in rf:
            fields = line.split(' ')
            defs[fields[0]] = dict()
            defs[fields[0]]['items'] = list()
            defs[fields[0]]['string'] = ' '.join(fields[1:]).strip()
            for fi in fields[1:]:
                name, vtype = fi[1:-1].split(':')
                defs[fields[0]]['items'].append((vtype, name))
    return defs


def compose_from_def(defs, r):
    if 'type' not in r or r['type'] not in defs:
        return None

    return defs[r['type']]['string'].format(**r)


def decode_with_def(defs, line):
    fields = line.split(' ')
    kw = fields[2].split('.')[-1]
    if kw not in defs:
        print(kw, 'not in defs')
        return None
    if len(defs[kw]['items']) < len(fields) - 3:
        print('log line length grater than def', kw)
        print(len(defs[kw]['items']), len(fields)-3)
        return None
    r = dict()
    for idx, fi in enumerate(fields[3:]):
        vtype, name = defs[kw]['items'][idx]
        if vtype[-1] == 'f':
            value = float(fi)
        elif vtype[-1] == 'd':
            value = int(fi)
        elif vtype[-1] == 's':
            value = fi
        elif vtype[-1] in {'x', 'X'}:
            value = int(fi, 16)
        else:
            value = fi
        r[name] = value
    return r


ub482_defs = load_log_defs('config/logdefs/ub482.logdef')
