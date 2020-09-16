
gyro_scale = 2000
accl_scale = 16
bit_length = 2 ^ 16
accl_rt = accl_scale / bit_length
gyro_rt = gyro_scale / bit_length


def get_gyro_accl(raw_data):
    """
    input raw data: acclx accly acclz gyrox gyroy gyroz
    gyro output in deg/s
    accl output in g
    """

    a_x = raw_data[0] * accl_rt
    a_y = raw_data[1] * accl_rt
    a_z = raw_data[2] * accl_rt

    w_x = raw_data[3] * gyro_rt
    w_y = raw_data[4] * gyro_rt
    w_z = raw_data[5] * gyro_rt

    return a_x, a_y, a_z, w_x, w_y, w_z


def ahrs_update(imu_data):
    """
    input raw data acclx accly acclz gyrox gyroy gyroz
    """