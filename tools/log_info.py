import os
import json


def get_can_ports_and_roles(log):
    conf_path = os.path.join(os.path.dirname(log), 'config.json')
    install_path = os.path.join(os.path.dirname(log), 'installation.json')
    ctx = dict()
    if os.path.exists(conf_path):
        configs = json.load(open(conf_path))
        canports = dict()
        ctx['veh_roles'] = dict()
        for idx, collector in enumerate(configs):
            if 'can_types' in collector:
                if 'can0' in collector['can_types']:
                    type0 = collector['can_types']['can0'][0] if collector['can_types']['can0'] else None
                if 'can1' in collector['can_types']:
                    type1 = collector['can_types']['can1'][0] if collector['can_types']['can1'] else None
            elif 'msg_types' not in collector:  # configured not used device
                continue
            elif 'can0' in collector['ports']:
                for msg in collector['msg_types']:
                    ctx['veh_roles'][msg] = collector.get('veh_tag')
                type0 = collector['ports']['can0']['topic']
                type1 = collector['ports']['can1']['topic']

            else:
                for msg in collector['msg_types']:
                    ctx['veh_roles'][msg] = collector.get('veh_tag')
                continue
            if type0 and type0 not in canports:
                canports[type0] = 'CAN{}'.format(idx * 2)

            if type1 and type1 not in canports:
                canports[type1] = 'CAN{}'.format(idx * 2 + 1)
            # if 'can_types' in collector:
            #     for msg in collector['can_types']:
            #         ctx['veh_roles'][msg] = collector.get('veh_tag')
        ctx['can_port'] = canports
        print('can ports:', canports)
        return ctx
        # time.sleep(10)


def audit_can_data(log, canport, sensor, audit_lines=500, thres=0.2):
    from parsers.parser import parsers_dict
    parser = parsers_dict.get(sensor)
    canport = canport.upper()
    line_cnt = 0
    valid_cnt = 0
    ctx = {'parser_mode': 'direct'}
    if not parser:
        print('audit quitting. found no parser for', sensor)
        return
    print('auditing {} for {}... '.format(canport, sensor), end='')
    for line in open(log):
        cols = line.split()
        if len(cols) < 4:
            continue
        if cols[2] == canport:
            line_cnt += 1
            data = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
            can_id = int(cols[3], 16)
            r = parser(can_id, data, ctx)
            if r:
                if isinstance(r, list):
                    valid_cnt += len(r)
                else:
                    valid_cnt += 1

        if line_cnt > audit_lines:
            if valid_cnt > audit_lines * thres:
                print('passed.', '{}/{}'.format(valid_cnt, line_cnt))
                return True
            else:
                print('failed.', '{}/{}'.format(valid_cnt, line_cnt))
                return
    print('failed')


def get_connected_sensors(log, role='ego'):
    """
    acquire the connected devices of specific vehicle.
    :param log: path to log.txt to analyze
    :param role: specific role of the vehicle
    :return: sensors dict
    """
    print('analyzing for present sensors...')
    ports_and_roles = get_can_ports_and_roles(log)
    can_ports = ports_and_roles['can_port']
    roles = ports_and_roles['veh_roles']
    ports = {}
    sensors = {}
    for s in can_ports:
        ports[can_ports[s]] = s
    with open(log) as rf:
        line_cnt = 0

        for line in rf:
            if not line:
                continue
            cols = line.strip().split(' ')
            # print(cols)
            line_cnt += 1
            if len(cols) < 4:
                continue
            if line_cnt > 5000:
                break
            if 'CAN' in cols[2]:
                sensors[cols[2]] = ports[cols[2]]
            elif 'bestpos' in cols[2]:
                dev = '.'.join(cols[2].split('.')[:2])
                if roles.get(dev) != role:
                    continue
                sensors[cols[2]] = 'bestpos'
            elif 'bestvel' in cols[2]:
                dev = '.'.join(cols[2].split('.')[:2])
                if roles.get(dev) != role:
                    continue
                sensors[cols[2]] = 'bestvel'
            elif 'heading' in cols[2]:
                dev = '.'.join(cols[2].split('.')[:2])
                if roles.get(dev) != role:
                    continue
                sensors[cols[2]] = 'heading'
            elif 'gps' in cols[2] or 'NMEA' in cols[2]:
                if 'gps' in cols[2] and roles.get(cols[2]) != role:
                    continue
                sensors[cols[2]] = 'gps'
            elif 'Gsensor' in cols[2]:
                if '.' in cols[2]:
                    if roles.get(cols[2]) != role:
                        continue
                sensors[cols[2]] = 'gsensor'

    for kw in list(sensors):
        if 'CAN' in kw:
            if not audit_can_data(log, kw, sensors[kw]):
                del sensors[kw]
    return sensors


def get_main_index(log):
    cfg_path = os.path.join(os.path.dirname(log), 'config.json')
    if not os.path.exists(cfg_path):
        print('no config.json in', os.path.dirname(log))
        return

    cfg = json.load(open(cfg_path))
    for collector in cfg:
        if collector.get('is_main'):
            return collector['idx']


def get_main_dev(log):
    idx = get_main_index(log)
    if idx is None:
        return
    cfg_path = os.path.join(os.path.dirname(log), 'config.json')
    cfg = json.load(open(cfg_path))
    return cfg[idx]

