import cantools
db_cgi220 = cantools.db.load_file('dbc/EP40_CANFD_Matrix_V2.2_IMU_2021-09-16.dbc', strict=False)

bds_offset = 18.0


def parse_cgi220pro(id, buf, ctx=None):
    ids = [m.frame_id for m in db_cgi220.messages]
    if id not in ids or id == 0x304:
        return
    try:
        r = db_cgi220.decode_message(id, buf, decode_choices=False)
    except ValueError as e:
        print('0x{:x}'.format(id), buf)
        raise e

    if id == 0x386: #rawimu
        imu = {}
        week = r['RawIMU_GpsWeek']
        tow = r['RawIMU_GpsTime']
        imu['ts'] = week * 604800.0 + tow + 315964800.0 - bds_offset
        imu['gyro_x'] = r['RawIMU_GyroX']
        imu['gyro_y'] = r['RawIMU_GyroY']
        imu['gyro_z'] = r['RawIMU_GyroZ']
        imu['accel_x'] = r['RawIMU_AccelX']
        imu['accel_y'] = r['RawIMU_AccelY']
        imu['accel_z'] = r['RawIMU_AccelZ']
        imu['temp'] = r['RawIMU_Temp']

        # print(imu)

    elif id == 0x388:  # inspva
        ins = {'type': 'inspva'}
        week = r['INS_GpsWeek']
        tow = r['INS_GpsTime']
        ins['ts'] = week * 604800.0 + tow + 315964800.0 - bds_offset
        ins['lat'] = r['INS_PosLat']
        ins['lon'] = r['INS_PosLon']
        ins['hgt'] = r['INS_PosAlt']
        ins['vel_e'] = r['INS_VelE']
        ins['vel_n'] = r['INS_VelN']
        ins['vel_u'] = r['INS_VelU']
        ins['pitch'] = r['INS_Pitch']
        ins['roll'] = r['INS_Roll']
        ins['yaw'] = r['INS_Yaw']
        ins['lat_std'] = r['INS_StdLat']
        ins['lon_std'] = r['INS_StdLon']
        ins['hgt_std'] = r['INS_StdAlt']
        ins['heading'] = r['INS_Heading']
        ins['speed'] = r['INS_Speed']
        i_s = r['INS_StatIns']
        p_s = r['INS_StatPos']
        if i_s == 0:
            ins['pos_type'] = 'NONE'
        elif i_s == 1:
            if p_s >= 6:
                p_s -= 5
            if p_s == 0:
                ins['pos_type'] = 'NONE'
            elif p_s == 1:
                ins['pos_type'] = 'SINGLE'
            elif p_s == 2:
                ins['pos_type'] = 'PSRDIFF'
            elif p_s == 4:
                ins['pos_type'] = 'NARROW_INT'
            elif p_s == 5:
                ins['pos_type'] = 'NARROW_FLOAT'
            else:
                ins['pos_type'] = 'NONE'
        elif i_s == 2:
            if p_s >= 6:
                p_s -= 5
            if p_s == 0:
                ins['pos_type'] = 'NONE'
            elif p_s == 1:
                ins['pos_type'] = 'SINGLE'
            elif p_s == 2:
                ins['pos_type'] = 'PSRDIFF'
            elif p_s == 3:
                ins['pos_type'] = 'INS'
            elif p_s == 4:
                ins['pos_type'] = 'INS_RTKFIXED'
            elif p_s == 5:
                ins['pos_type'] = 'INS_RTKFLOAT'
            else:
                ins['pos_type'] = 'NONE'

        # print(ins)
        return ins

    elif id == 0x38a:  # time
        pass

    # return r