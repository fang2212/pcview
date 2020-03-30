from parsers.x1 import parse_x1
from parsers.x1l import parse_x1l
from parsers.mobileye_q3 import parse_ifv300, parse_q3
from parsers.mobileye_q2 import parse_mobileye
from parsers.mqb_esp import parse_mqb
from parsers.radar import *
from parsers.drtk import parse_rtk
from parsers.mobileye_q4 import parser_mbq4
from parsers.ublox import decode_nmea
from parsers.df_d530 import parse_dfd530
from parsers.x1d3 import parse_x1d3


def default_parser(id, data, type=None):
    return None


parsers_dict = {
    "mbq3":     parse_q3,
    "ifv300":   parse_ifv300,
    "mbq2":     parse_mobileye,
    "mbq4":     parser_mbq4,
    "esr":      parse_esr,
    "ars":      parse_ars,
    "mqb":      parse_mqb,
    "mrr":      parse_bosch_mrr,
    "lmr":      parse_hawkeye_lmr,
    "hmb":      parse_hmb,
    "x1":       parse_x1,
    "x1_fusion": parse_x1,
    "x1l":      parse_x1l,
    "x1d3":     parse_x1d3,
    "drtk":     parse_rtk,
    "mrr_fusion": parse_fusion_mrr,
    "sta77":    parse_sta77,
    "sta77_3":  parse_sta77_3,
    "xyd2":     parse_xyd2,
    "anc":      parse_anc,
    "ctlrr":    parse_ctlrr,
    "d530":     parse_dfd530,
    "default":  default_parser
}
