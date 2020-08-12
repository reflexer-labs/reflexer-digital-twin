# reflexer
Reflexer Labs, RAI

# Connecting to the data

Use the following code example for reading in the CSV and creating a time series data frame.

	import pandas as pd
	import numpy as np
	import matplotlib.pyplot as plt

	ts_df = pd.read_csv('./data/ts_rai.csv')

	ts_df.index = pd.to_datetime(ts_df['date'], format = '%m/%d/%Y')
	ts_df = ts_df.drop(columns = ['date'])
	##ts_df.head()

	ts_df['DAI Price'].plot()