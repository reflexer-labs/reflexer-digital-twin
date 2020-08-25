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
	weth_df.head()
	eth_df = pd.read_csv('./raw_files/dai_price_eth.csv')
	eth_df.head()
	dai_df = pd.read_csv('./raw_files/dai_minted_burnt.csv')
	dai_df.head()
	dune_df = pd.read_json('./raw_files/dune_data.json')
	dune_df['date'] = pd.to_datetime(dune_df['date_trunc'], format = '%Y/%m/%d')
	dune_df.head()
	
	final = weth_df.join(eth_df, lsuffix='__timestamp', rsuffix='__timestamp')
	final = final.join(dai_df, lsuffix='__timestamp', rsuffix='__timestamp')
	final = final.join(dune_df, lsuffix='__timestamp', rsuffix='date')
	final = final[['date', 'Locked Amount', 'Accumulated Lock', 'Accumulated Free', 'DAI price in ETH', 'Daily Change in DAI Supply', 'Minted DAI', 'Burnt DAI', 'debt_payment', 'usd_fee_paid', 'mkr_burned']]

	final.index = pd.to_datetime(final['date'], format = '%Y/%m/%d')
	final = final.drop(columns = ['date'])

	final.head()
	
	final.to_csv('ts_rai.csv')

	