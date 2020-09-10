SELECT 
  date_trunc('day', MKR_BURN.evt_block_time)
, SUM(SAI_BURN.wad*10^(-18))                                    AS debt_payment
, SUM(MKR_BURN.wad*10^(-18))                                 AS mkr_burned
, SUM(bytea2numeric(TRACES.output)*MKR_BURN.wad*10^(-36) )   AS USD_fee_paid
FROM maker."MKR_evt_Transfer" MKR_BURN
    JOIN maker."SAI_evt_Burn" SAI_BURN
		ON MKR_BURN.evt_tx_hash = SAI_BURN.evt_tx_hash
    JOIN ethereum."traces" TRACES
		ON MKR_BURN.evt_tx_hash = TRACES.tx_hash
		AND (TRACES.to = '\x5c1fc813d9c1b5ebb93889b3d63ba24984ca44b7' OR TRACES.to = '\x99041f808d598b782d5a3e498681c2452a31da08') -- pep - oracle for MKR
		AND TRACES.from = '\x448a5065aebb8e423f0896e6c5d525c040f59af3' -- SAI tap queries MKR oracle
WHERE 1 = 1
	AND MKR_BURN.dst = '\x69076e44a9c70a67d5b79d95795aba299083c275' -- assume MKR transferred to gem pit are burnt
	AND date_trunc('day', MKR_BURN.evt_block_time) > '12/01/2017'
	AND date_trunc('day', MKR_BURN.evt_block_time) < '10/01/2019' -- ignore events occuring after november/2019 (~ MCD) because migration works differently

GROUP BY 1