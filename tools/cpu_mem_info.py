import psutil
import time

def get_cpu_pct():
    ret = psutil.cpu_percent()
    # time.sleep(0.1)
    return ret

def get_mem_pct():
    ret = psutil.virtual_memory().percent
    # time.sleep(0.1)
    return ret


def get_cpu_temp():

    t = psutil.sensors_temperatures()
    if 'coretemp' in t:
        ret = t['coretemp'][0].current
    elif 'cpu-thermal' in t:
        ret = t['cpu-thermal'][0].current
    else:
        ret = None
    # time.sleep(0.1)
    return ret


def get_fan_speed():
    ret = psutil.sensors_fans()
    # time.sleep(0.1)
    return ret




if __name__ == "__main__":
    cpu_pct = get_cpu_pct()
    mem_pct = get_mem_pct()
    cpu_temp = get_cpu_temp()

    print('cpu percent: {}%'.format(cpu_pct))
    print('memory percent: {}%'.format(mem_pct))
    print('cpu temp: {}c'.format(cpu_temp))