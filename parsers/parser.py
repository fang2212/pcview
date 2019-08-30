from parsers.x1 import parse_x1
from parsers.mobileye_q3 import parse_ifv300, parse_q3
from parsers.mobileye_q2 import parse_mobileye
from parsers.mqb_esp import parse_mqb
from parsers.radar import parse_esr, parse_ars, parse_hmb, parse_bosch_mrr, parse_hawkeye_lmr, parse_fusion_mrr
from parsers.drtk import parse_rtk


def default_parser(id, data, type=None):
    return None


parsers_dict = {
    "mbq3":     parse_q3,
    "ifv300":   parse_ifv300,
    "mbq2":     parse_mobileye,
    "esr":      parse_esr,
    "ars":      parse_ars,
    "mqb":      parse_mqb,
    "mrr":      parse_bosch_mrr,
    "lmr":      parse_hawkeye_lmr,
    "hmb":      parse_hmb,
    "x1":       parse_x1,
    "rtk":      parse_rtk,
    "mrr_fusion": parse_fusion_mrr,
    "default":  default_parser
}
