from parsers.bosch import bosch_mrr
from parsers.a1j import parse_a1j, parse_a1j_fusion, parse_a1j_vision
from parsers.d1_fusion import parse_d1
from parsers.muniu import parser_mu_f, parser_mu_r, parser_mu_fl, parser_mu_fr, parser_mu_rl, parser_mu_rr
from parsers.q4_52 import parser_q4_52
from parsers.x1 import parse_x1, parse_x1_fusion, parse_x1_vision
from parsers.x1l import parse_x1l
from parsers.x1j import parse_x1j
from parsers.mobileye_q3 import parse_ifv300, parse_q3, parse_ifv300_vision, parse_ifv300_fusion
from parsers.mobileye_q2 import parse_mobileye
from parsers.mqb_esp import parse_mqb
from parsers.radar import *
from parsers.drtk import parse_rtk
from parsers.mobileye_q4 import parser_mbq4
from parsers.df_d530 import parse_dfd530
from parsers.x1d3 import parse_x1d3
from parsers.novatel import parse_novatel
from parsers.pim222 import parse_pim222
from parsers.j2 import parser_j2
from parsers.rt_range import parser_rt
from parsers.q4_100 import parser_q4_100
from parsers.gs4_debug import parser_gs4
from parsers.x1_jac import parse_x1_jac
from parsers.cgi220_can import parse_cgi220pro


def default_parser(id, data, type=None):
    return None


parsers_dict = {
    "a1j":      parse_a1j,
    "a1j_fusion": parse_a1j_fusion,
    "a1j_vision": parse_a1j_vision,
    "anc":      parse_anc,
    "ars":      parse_ars,
    "ars410":   parse_ars410,
    "bosch_mrr": bosch_mrr,
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
    "mbq3":     parse_ifv300,
    "mbq3_vision": parse_ifv300_vision,
    "mbq3_fusion": parse_ifv300_fusion,
    "mbq4":     parser_mbq4,
    "mqb":      parse_mqb,
    "mrr":      parse_bosch_mrr,
    "mrr_fusion": parse_fusion_mrr,
    "mu_f":     parser_mu_f,
    "mu_r":     parser_mu_r,
    "mu_fl":    parser_mu_fl,
    "mu_fr":    parser_mu_fr,
    "mu_rl":    parser_mu_rl,
    "mu_rr":    parser_mu_rr,
    "novatel":  parse_novatel,
    "pim222":   parse_pim222,
    "q4_100":   parser_q4_100,
    "q4_52":    parser_q4_52,
    "q3":       parse_q3,
    "rt_range": parser_rt,
    "sta77":    parse_sta77,
    "sta77_3":  parse_sta77_3,
    "vfr":      parse_vfr,
    "wsk":      parse_ars,
    "x1":       parse_x1,
    "x1_fusion": parse_x1_fusion,
    "x1_vision": parse_x1_vision,
    "x1_jac":   parse_x1_jac,
    "x1d3":     parse_x1d3,
    "x1j":      parse_x1j,
    "x1l":      parse_x1l,
    "xyd2":     parse_xyd2,
    "huace":    parse_cgi220pro
    # "mbq4_lane": parser_mbq4_lane_tsr,
}


