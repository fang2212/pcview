from parsers.parser import parsers_dict
import os
import matplotlib.pyplot as plt

def new_run(log):

    q4_key = "q4_100.5"

    bin_rf = open(os.path.join(os.path.dirname(log), "%s/%s.bin" % (q4_key, q4_key)), "rb")

    axs = {}

    ars_ctx = {}
    ctx = {}
    j2_ctx = {}

    key_mp = {
        "CAN6": "j2",
        "CAN2": "x1_fusion",
        "CAN0": "ars",
        q4_key: q4_key
    }

    with open(log, "r") as rf:
        for line in rf:
            line = line.strip()
            cols = line.split()

            ts = float(cols[0]) + float(cols[1]) / 1000000

            if cols[2] == q4_key:

                sz = int(cols[3])
                bts = bin_rf.read(sz)
                ret = parsers_dict.get("q4_100", "default")(0, bts)
                if ret is None:
                    continue
                if type(ret) == dict:
                    ret = [ret]

                if "q4_100" not in axs:
                    axs["q4_100"] = [[], []]
                    axs["q4_speed"] = [[], []]
                    axs["q4_l_lane"] = [[], []]
                    axs["q4_r_lane"] = [[], []]

                for obs in ret:
                    if obs["type"] == "obstacle" and obs["cipo"]:
                        axs["q4_100"][0].append(ts)
                        axs["q4_100"][1].append(obs["pos_lon"] - 1.58)
                    elif obs["type"] == "vehicle_state":
                        axs["q4_speed"][0].append(ts)
                        axs["q4_speed"][1].append(obs["speed"])

                    elif obs["type"] == "lane":
                        if obs["id"] == 0:
                            axs["q4_l_lane"][0].append(ts)
                            axs["q4_l_lane"][1].append(obs["range"])
                        elif obs["id"] == 1:
                            axs["q4_r_lane"][0].append(ts)
                            axs["q4_r_lane"][1].append(obs["range"])

            elif key_mp.get(cols[2]) == "x1_fusion":
                data = bytes().fromhex(cols[4])
                can_id = int(cols[3], 16)
                ret = parsers_dict.get("x1_fusion")(can_id, data, ctx)

                if ret is None:
                    continue
                if type(ret) == dict:
                    ret = [ret]

                if "x1_fusion" not in axs:
                    axs["x1_fusion"] = [[], []]

                for obs in ret:
                    if "type" in obs and obs["type"] == "obstacle" and "cipo" in obs and obs["cipo"] and obs["sensor"] == "x1_fusion":
                        axs["x1_fusion"][0].append(ts)
                        axs["x1_fusion"][1].append(obs["pos_lon"])

            elif key_mp.get(cols[2]) == "j2":
                data = bytes().fromhex(cols[4])
                can_id = int(cols[3], 16)
                ret = parsers_dict.get("j2")(can_id, data, j2_ctx)
                if ret is None:
                    continue

                if type(ret) == dict:
                    ret = [ret]

                if "j2" not in axs:
                    axs["j2"] = [[], []]

                for obs in ret:
                    if obs["type"] == "obstacle" and obs["cipo"]:
                        axs["j2"][0].append(ts)
                        axs["j2"][1].append(obs["pos_lon"] - 3.5)

            elif key_mp.get(cols[2]) == "ars":
                data = bytes().fromhex(cols[4])
                can_id = int(cols[3], 16)
                ret = parsers_dict.get("ars")(can_id, data, ars_ctx)
                if ret is None:
                    continue

                if type(ret) == dict:
                    ret = [ret]

                if "ars" not in axs:
                    axs["ars"] = [[], []]

                for obs in ret:
                    if obs["type"] == "obstacle" and "cipo" in obs and obs["cipo"]:
                        axs["ars"][0].append(ts)
                        axs["ars"][1].append(obs["pos_lon"])

    fig, figs = plt.subplots(3, 1, sharex=True)
    for key in axs:
        if "lane" not in key and "speed" not in key:
            c = None
            if "j2" in key:
                c = "yellow"
            elif "q4" in key:
                c = "blue"
            figs[0].plot(axs[key][0], axs[key][1], label=key, color=c)
            figs[0].legend()
        else:
            figs[2].plot(axs[key][0], axs[key][1], label=key)
            figs[2].legend()

    i, j = 0, 0
    x, y = [], []
    q4_com_key = "x1_fusion"
    ars_len = len(axs[q4_com_key][0])
    q4_len = len(axs["q4_100"][0])

    print(q4_len, ars_len)
    while i < ars_len and j < q4_len:
        while j < q4_len and axs["q4_100"][0][j] < axs[q4_com_key][0][i]:
            j += 1

        if j >= q4_len:
            break

        x.append(axs["q4_100"][0][j])
        y.append(axs["q4_100"][1][j] - axs[q4_com_key][1][i])
        i += 1

    figs[1].plot(x, y, label="q4_error", color="blue")

    i, j = 0, 0
    x, y = [], []
    ars_len = len(axs["ars"][0])

    # if "j2" in axs:
    #     j2_len = len(axs["j2"][0])
    #     print(j2_len, ars_len)
    #     while i < ars_len and j < j2_len:
    #         while j < j2_len and axs["j2"][0][j] < axs["ars"][0][i]:
    #             j += 1
    #
    #         if j >= j2_len:
    #             break
    #
    #         x.append(axs["j2"][0][j])
    #         y.append(axs["j2"][1][j] - axs["ars"][1][i])
    #         i += 1
    #
    #     figs[1].plot(x, y, label="j2_error", color="yellow")
    #
    #     figs[1].set_ylim((-5, 5))


    # axes.set_ylim([ymin, ymax])
    figs[1].grid()
    figs[1].legend()
    # plt.get_current_fig_manager().full_screen_toggle()
    plt.savefig(log + ".png")
    plt.show()

    pass


def run_single_q4(bin_file):
    from parsers.q4_100 import decode_header, parser_q4_100
    bin_rf = open(bin_file, "rb")

    axs = {}
    while True:
        head_buf = bin_rf.read(32)
        if not head_buf:
            break
        head_info = decode_header(head_buf)
        data_buf = bin_rf.read(head_info["streamChunkLen"])
        ret = parser_q4_100(0, head_buf + data_buf)
        if ret is None:
            continue
        if type(ret) == dict:
            ret = [ret]
        ts = head_info["pcTime"]
        if "q4_100" not in axs:
            axs["q4_100"] = [[], []]
            axs["q4_speed"] = [[], []]
            axs["q4_l_lane"] = [[], []]
            axs["q4_r_lane"] = [[], []]

        for obs in ret:
            if obs["type"] == "obstacle" and obs["cipo"]:
                axs["q4_100"][0].append(ts)
                axs["q4_100"][1].append(obs["pos_lon"] - 1.58)
            elif obs["type"] == "vehicle_state":
                axs["q4_speed"][0].append(ts)
                axs["q4_speed"][1].append(obs["speed"])

            elif obs["type"] == "lane":
                if obs["id"] == 0:
                    axs["q4_l_lane"][0].append(ts)
                    axs["q4_l_lane"][1].append(obs["range"])
                elif obs["id"] == 1:
                    axs["q4_r_lane"][0].append(ts)
                    axs["q4_r_lane"][1].append(obs["range"])

    fig, figs = plt.subplots(2, 1, sharex=True)
    for key in axs:
        if "lane" not in key and "speed" not in key:
            figs[0].plot(axs[key][0], axs[key][1], label=key)
            figs[0].legend()
        else:
            figs[1].plot(axs[key][0], axs[key][1], label=key)
            figs[1].legend()
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    import sys
    sys.argv.append("/media/minieye/cve_drive3/cve_data/20210411102318/log.txt")
    # run(sys.argv[1])
    # run_single_q4(sys.argv[1])
    # run_single_q4("/home/minieye/data/download/SGMAEBData_eyeq4_100_vison_only/SGM358HWA_PV016_20201108_v934_AEB_night_155417_001.mudp")

    # p_dir = "/media/minieye/cve_drive01/q4_100_ceju_cipv_test_data/q4_test_ranging_cipv_data_20210412"
    # for f in os.listdir(p_dir):
    #     log_txt = os.path.join(p_dir, f, "log.txt")
    #     if os.path.exists(log_txt):
    #         print(log_txt)
    #         new_run(log_txt)

    new_run(sys.argv[1])
