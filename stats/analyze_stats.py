import pandas as pd
import sys
sys.path.append('../src/')
from encoder import *

stats = pd.read_csv('results.csv')
print(stats.to_string())

time_fig = stats['Encode time (seconds)'].plot.bar().get_figure()
time_fig.savefig('time_results.png')

data_inflation_fig = stats['Data Inflation Rate (i)'].plot.bar().get_figure()
data_inflation_fig.savefig('data_inflation_results.png')

main_fig = stats.plot.bar(stacked=True).get_figure()
main_fig.savefig('results.png')
