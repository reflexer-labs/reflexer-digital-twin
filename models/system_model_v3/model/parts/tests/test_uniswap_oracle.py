from models.system_model_v3.model.parts.uniswap_oracle import UniswapOracle

def test_oracle_init():
    type(UniswapOracle()) == UniswapOracle


def test_oracle_update_obs():
    granularity = 20
    window_size = 100
    oracle = UniswapOracle(granularity=granularity,
                           window_size=window_size,
                           max_window_size=2*window_size)

    N = window_size * 3 + 1

    for i in range(1, N + 1):
        state = {'cumulative_time': i,
                 'eth_price': i,
                 'ETH_balance': i,
                 'RAI_balance': i}
        oracle.update_result(state)
    
    assert oracle.updates - 1 == (N - 1) / (window_size / granularity)
    assert oracle.last_update_time == N

    oracle.update_result(state, update=False)