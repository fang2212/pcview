from parsers.x1 import parse_x1
from parsers.mobileye_q3 import parse_ifv300, parse_q3
from parsers.mobileye_q2 import parse_mobileye
from parsers.mqb_esp import parse_mqb
from parsers.radar import parse_esr, parse_ars, parse_hmb, parse_bosch_mrr, parse_hawkeye_lmr, parse_fusion_mrr, parse_sta77, parse_xyd2
from parsers.drtk import parse_rtk
from parsers.mobileye_q4 import parser_mbq4
from parsers.ublox import decode_nmea


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
    "drtk":     parse_rtk,
    "mrr_fusion": parse_fusion_mrr,
    "sta77":    parse_sta77,
    "xyd2":     parse_xyd2,
    "default":  default_parser
}
