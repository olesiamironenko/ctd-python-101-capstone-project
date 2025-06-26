import pandas as pd
import numpy as np
import warnings
from pandas.errors import ParserWarning

warnings.simplefilter(action='ignore', category=ParserWarning)
# ------------------------------------------------------------ #

#  Load CSV files
hitting_stats = pd.read_csv('last_5_ys_hitting_stats.csv')

