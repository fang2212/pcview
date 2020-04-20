import cantools


db_mqb = cantools.database.load_file('dbc/MQB_ECAN_ACC.dbc', strict=False)


def parse_mqb(id, buf, ctx=None):
    if id == 0xfd or id == 0x101:
        r = db_mqb.decode_message(id, buf)
        if ctx and ctx.get('parser_mode') == 'direct':
            return r
        # print('0x%x'%id, r)
        if 'ESP_v_Signal' in r:
            # return
            # print("speed: {}".format(r['ESP_v_Signal']))

            return {'type': 'vehicle_state', 'sensor': 'mqb', 'speed': r['ESP_v_Signal']}

        if 'ESP_Gierrate' in r:
            if r['ESP_VZ_Gierrate'] == 'negative':
                pass
            return
            # print("gear rate: {} {}".format(r['ESP_Gierrate'], r['ESP_VZ_Gierrate']))
    # except Exception as e:
    #     print('0x%x'%id, buf)