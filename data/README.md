# reflexer
Reflexer Labs, RAI

# Connecting to the data

Use the following code example for reading in the CSV and creating a time series data frame.
	ts_df = pd.read_csv('./data/ts_rai.csv')

	ts_df.index = pd.to_datetime(ts_df['date'], format = '%m/%d/%Y')
	ts_df = ts_df.drop(columns = ['date'])
	##ts_df.head()

	ts_df['DAI Price'].plot()

# ETL for Raw Data

	import pandas as pd
	import numpy as np
	import matplotlib.pyplot as plt

	weth_df = pd.read_csv('./raw_files/dai_weth.csv')
	weth_df.index = pd.to_datetime(weth_df['__timestamp'], format = '%Y/%m/%d')
	weth_df = weth_df.drop(columns = ['__timestamp'])
	weth_df.head()
	
	eth_df = pd.read_csv('./raw_files/dai_price_eth.csv')
	eth_df.index = pd.to_datetime(eth_df['__timestamp'], format = '%Y/%m/%d')
	eth_df = eth_df.drop(columns = ['__timestamp'])
	eth_df.head()
	
	dai_df = pd.read_csv('./raw_files/dai_minted_burnt.csv')
	dai_df.index = pd.to_datetime(dai_df['__timestamp'], format = '%Y/%m/%d')
	dai_df = dai_df.drop(columns = ['__timestamp'])
	dai_df.head()

	dune_df = pd.read_json('./raw_files/dune_data.json')
	dune_df.index = pd.to_datetime(dune_df['date_trunc'], format = '%Y/%m/%d').dt.date
	dune_df = dune_df.drop(columns = ['date_trunc'])
	dune_df.head()
	
	final = weth_df.join(eth_df)
	final = final.join(dai_df)
	final = final.join(dune_df)

	final.head()

	final[(final.index > '2018-07-01') & (final.index < '2019-09-30')].to_csv('ts_rai.csv')

	