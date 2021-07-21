from parsers.a1j import parse_a1j
from parsers.d1_fusion import parse_d1
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
from parsers.x1_jac import parse_x1_jac

def default_parser(id, data, type=None):
    return None


parsers_dict = {
    "a1j":      parse_a1j,
    "a1j_fusion": parse_x1,
    "anc":      parse_anc,
    "ars":      parse_ars,
    "ars410":   parse_ars410,
    "ctlrr":    parse_ctlrr,
    "d1_fusion": parse_d1,
    "d530":     parse_dfd530,
    "default":  default_parser,
    "drtk":     parse_rtk,
    "esr":      parse_esr,
    "gs4_debug": parser_gs4,
    "hmb":      parse_hmb,
    "ifv300":   parse_ifv300,
    "j2":       parser_j2,
    "j2_fusion": parse_x1,
    "lmr":      parse_hawkeye_lmr,
    "mbq2":     parse_mobileye,
    "mbq3":     parse_q3,
    "mbq4":     parser_mbq4,
    "mqb":      parse_mqb,
    "mrr":      parse_bosch_mrr,
    "mrr_fusion": parse_fusion_mrr,
    "novatel":  parse_novatel,
    "pim222":   parse_pim222,
    "q4_100":   parser_q4_100,
    "rt_range": parser_rt,
    "sta77":    parse_sta77,
    "sta77_3":  parse_sta77_3,
    "vfr":      parse_vfr,
    "x1":       parse_x1,
    "x1_fusion": parse_x1,
    "x1_jac":   parse_x1_jac,
    "x1d3":     parse_x1d3,
    "x1j":      parse_x1j,
    "x1l":      parse_x1l,
    "xyd2":     parse_xyd2,
    # "mbq4_lane": parser_mbq4_lane_tsr,
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


