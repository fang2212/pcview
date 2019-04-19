
import cantools

db_liuqi = cantools.database.load_file('dbc/liuqi_20190110.dbc', strict=False)

def parse_liuqi(id, data):
    '''
    :params id: int
    :params data: bytes
    '''

    ids = [m.frame_id for m in db_liuqi.messages]
    if id not in ids:
        return None
    r = db_liuqi.decode_message(id, data)
    obs = {}
    for k in r:
        if k == 'Camera_State':
            obs['camere'] = r[k]

        if k == 'Rlane_Detect':
            obs['rld'] = r[k]
        elif k == 'Llane_Detect':
            obs['lld'] = r[k]
        elif k == 'LDW_Status':
            obs['ldw_on'] = r[k]
        elif k == 'Buzzing':
            if r[k] == 'NO WARN':
                r[k] = ''
            obs['buzzing'] = r[k]
        elif k == 'HMW_Level':
            obs['hw'] = r[k]
        elif k == 'PCW_warn':
            obs['pcw_on'] = r[k]
        elif k == 'PCW_Detect':
            obs['ped_on'] = r[k]
        elif k == 'HMW_Status':
            obs['hw_on'] = r[k]
        elif k == 'TTC':
            obs['ttc'] = r[k]
        elif k == 'Overspeed':
            obs['overspeed'] = r[k]

        elif k == 'FCW_Warn':
            obs['fcw'] = r[k]
        elif k == 'LLDW_Warn':
            obs['lldw'] = r[k]
        elif k == 'RLDW_Warn':
            obs['rldw'] = r[k]

    return obs
    

    
    
