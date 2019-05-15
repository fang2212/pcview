from tools.match import CIPOFilter
from parsers.x1 import parse_x1
from parsers.mobileye_q3 import parse_ifv300, parse_q3
from parsers.mobileye_q2 import parse_mobileye
from parsers.mqb_esp import parse_mqb
from parsers.radar import parse_esr, parse_hmb, parse_bosch_mrr, parse_hawkeye_lmr


class Parser(object):
    def __init__(self):
        self.filter = CIPOFilter()

    def parse(self):
        pass


def default_parser(id, data):
    return None


parsers_dict = {
    "mbq3":     parse_q3,
    "ifv300":   parse_ifv300,
    "mbq2":     parse_mobileye,
    "esr":      parse_esr,
    "mqb":      parse_mqb,
    "mrr":      parse_bosch_mrr,
    "lmr":      parse_hawkeye_lmr,
    "hmb":      parse_hmb,
    "x1":       parse_x1,
    "default":  default_parser
}
