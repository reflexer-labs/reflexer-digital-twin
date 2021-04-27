import rai_digital_twin.models.system_model_v2.model.parts.debt_market as debt_market

eth_price = 300
redemption_price = 2.0

liquidation_ratio = 1.5
liquidation_buffer = 2.0

lock = 100
draw = lock * eth_price / (redemption_price * liquidation_buffer)

cdps = [
    debt_market.open_cdp_lock(lock, eth_price, redemption_price, liquidation_ratio * liquidation_buffer),
    debt_market.open_cdp_lock(lock, eth_price, redemption_price, liquidation_ratio),
    debt_market.open_cdp_lock(lock, eth_price, redemption_price, liquidation_ratio * 0.8),
]

def test_is_cdp_at_liquidation_ratio():
    cdp_1 = cdps[1]
    assert debt_market.is_cdp_at_liquidation_ratio(cdp_1, eth_price, redemption_price, liquidation_ratio)

def test_is_cdp_above_liquidation_ratio():
    cdp_0 = cdps[0]
    assert debt_market.is_cdp_above_liquidation_ratio(cdp_0, eth_price, redemption_price, liquidation_ratio * liquidation_buffer)
    cdp_1 = cdps[1]
    assert debt_market.is_cdp_above_liquidation_ratio(cdp_1, eth_price, redemption_price, liquidation_ratio)
    cdp_2 = cdps[2]
    assert not debt_market.is_cdp_above_liquidation_ratio(cdp_2, eth_price, redemption_price, liquidation_ratio)

def test_open_cdp():
    draw = lock * eth_price / (redemption_price * liquidation_ratio * liquidation_buffer)
    result_open_cdp_lock = debt_market.open_cdp_lock(lock, eth_price, redemption_price, liquidation_ratio * liquidation_buffer)
    assert result_open_cdp_lock == {
        'open': 1,
        'time': 0,
        'locked': lock,
        'drawn': draw,
        'wiped': 0.0,
        'freed': 0.0,
        'w_wiped': 0.0,
        'dripped': 0.0,
        'v_bitten': 0.0,
        'u_bitten': 0.0,
        'w_bitten': 0.0
    }

    assert debt_market.open_cdp_draw(draw, eth_price, redemption_price, liquidation_ratio * liquidation_buffer) == result_open_cdp_lock

def test_wipe_to_liquidation_ratio():
    cdp_unbalanced = debt_market.open_cdp_lock(lock, eth_price, redemption_price, liquidation_ratio * 0.8)
    wipe = debt_market.wipe_to_liquidation_ratio(cdp_unbalanced, eth_price, redemption_price, liquidation_ratio)

    assert debt_market.is_cdp_at_liquidation_ratio({
        **cdp_unbalanced,
        'wiped': wipe
    }, eth_price, redemption_price, liquidation_ratio)

def test_draw_to_liquidation_ratio():
    cdp_unbalanced = debt_market.open_cdp_lock(lock, eth_price, redemption_price, liquidation_ratio * 1.3)
    draw = debt_market.draw_to_liquidation_ratio(cdp_unbalanced, eth_price, redemption_price, liquidation_ratio)

    assert debt_market.is_cdp_at_liquidation_ratio({
        **cdp_unbalanced,
        'drawn': cdp_unbalanced['drawn'] + draw
    }, eth_price, redemption_price, liquidation_ratio)

def test_lock_to_liquidation_ratio():
    cdp_unbalanced = debt_market.open_cdp_draw(100, eth_price, redemption_price, liquidation_ratio * 0.8)
    lock = debt_market.lock_to_liquidation_ratio(cdp_unbalanced, eth_price, redemption_price, liquidation_ratio)

    assert debt_market.is_cdp_at_liquidation_ratio({
        **cdp_unbalanced,
        'locked': cdp_unbalanced['locked'] + lock
    }, eth_price, redemption_price, liquidation_ratio)

def test_free_to_liquidation_ratio():
    cdp_unbalanced = debt_market.open_cdp_draw(100, eth_price, redemption_price, liquidation_ratio * 1.3)
    free = debt_market.free_to_liquidation_ratio(cdp_unbalanced, eth_price, redemption_price, liquidation_ratio)

    assert debt_market.is_cdp_at_liquidation_ratio({
        **cdp_unbalanced,
        'freed': free
    }, eth_price, redemption_price, liquidation_ratio)
