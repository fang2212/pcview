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
        print(canports)
        return ctx
        # time.sleep(10)
    else:
        ctx['can_port'] = {'x1': 'CAN1', 'esr': 'CAN0'}


def get_connected_sensors(log, can_ports):
    ports = {}
    can_lines = {}
    for s in can_ports:
        ports[can_ports[s]] = s
    with open(log) as rf:
        line_cnt = 0

        for line in rf:
            cols = line.strip().split(' ')
            line_cnt += 1
            if line_cnt > 5000:
                break
            if 'CAN' in cols[2]:
                can_lines[cols[2]] = ports[cols[2]]
    return can_lines
