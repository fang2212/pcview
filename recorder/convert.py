
def load_log_defs(def_file):
    defs = dict()
    with open(def_file) as rf:
        for line in rf:
            fields = line.split(' ')
            defs[fields[0]] = list()
            for fi in fields[1:]:
                defs[fields[0]].append(fi)
    return defs


def compose_from_def(defs, r):
    if 'type' not in r or r['type'] not in defs:
        return None
    fields = defs[r['type']]
    values = [r[fi.strip()] for fi in fields]
    # print(values)
    return ' '.join(['{}'.format(value) for value in values])


ub482_defs = load_log_defs('config/logdefs/ub482.logdef')