from colorlog import ColoredFormatter
import logging

logger = logging.getLogger(__name__)

LOGFORMAT = "%(log_color)s%(asctime)s  %(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
formatter = ColoredFormatter(LOGFORMAT, datefmt='%H:%M:%S')

fh = logging.StreamHandler()
# fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s： %(message)s', datefmt='%H:%M:%S')
fh.setFormatter(formatter)
logger.addHandler(fh)
