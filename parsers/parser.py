from parsers.x1 import parse_x1
from parsers.x1l import parse_x1l
from parsers.x1j import parse_x1j
from parsers.mobileye_q3 import parse_ifv300, parse_q3
from parsers.mobileye_q2 import parse_mobileye
from parsers.mqb_esp import parse_mqb
from parsers.radar import *
from parsers.drtk import parse_rtk
from parsers.mobileye_q4 import parser_mbq4
from parsers.ublox import decode_nmea
from parsers.df_d530 import parse_dfd530
from parsers.x1d3 import parse_x1d3
from parsers.novatel import parse_novatel
from parsers.pim222 import parse_pim222
from parsers.j2 import parser_j2
from parsers.rt_range import parser_rt
from parsers.q4_100 import parser_q4_100
from parsers.gs4_debug import parser_gs4

def default_parser(id, data, type=None):
    return None


parsers_dict = {
    "mbq3":     parse_q3,
    "ifv300":   parse_ifv300,
    "mbq2":     parse_mobileye,
    "mbq4":     parser_mbq4,
    # "mbq4_lane": parser_mbq4_lane_tsr,
    "esr":      parse_esr,
    "ars":      parse_ars,
    "mqb":      parse_mqb,
    "mrr":      parse_bosch_mrr,
    "lmr":      parse_hawkeye_lmr,
    "hmb":      parse_hmb,
    "x1":       parse_x1,
    "x1j":      parse_x1j,
    "x1_fusion": parse_x1,
    "d1_fusion": parse_x1,
    "j2_fusion": parse_x1,
    "a1j_fusion": parse_x1,
    "x1l":      parse_x1l,
    "x1d3":     parse_x1d3,
    "drtk":     parse_rtk,
    "mrr_fusion": parse_fusion_mrr,
    "sta77":    parse_sta77,
    "sta77_3":  parse_sta77_3,
    "xyd2":     parse_xyd2,
    "anc":      parse_anc,
    "vfr":      parse_vfr,
    "ctlrr":    parse_ctlrr,
    "d530":     parse_dfd530,
    "novatel":  parse_novatel,
    "pim222":   parse_pim222,
    "j2": parser_j2,
    "ars410": parse_ars410,
    "rt_range": parser_rt,
    "q4_100": parser_q4_100,
    "gs4_debug": parser_gs4,
    "default":  default_parser
}

from multiprocessing import Queue, Process
import time
class MiniDecoder(Process):
    def __init__(self, parsers=parsers_dict, can_types={}, oq=None):
        super(MiniDecoder, self).__init__()
        self.parsers = parsers
        self.inq = Queue(maxsize=200)
        self.oq = oq
        self.can_types = can_types

    def run(self):
        ctx = {}
        while True:
            if not self.inq.empty():
                ts, src, msg, msg_id = self.inq.get()
                if 'CAN' in src:
                    kw = self.can_types.get(src)
                else:
                    kw = src.split('.')[0]

                if kw:
                    parser = self.parsers.get(kw)
                    if parser:
                        r = parser(msg_id, msg, ctx)
                        if r and self.oq:
                            r['source'] = src
                            if 'ts' not in r:
                                r['ts'] = ts
                            self.oq.put(r)

            else:
                time.sleep(0.01)


