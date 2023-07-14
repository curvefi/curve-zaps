from brownie import Contract
from brownie.test import given, strategy
from hypothesis import settings
from datetime import timedelta


def _min_amounts(swap_contract, decimals, is_meta_underlying=False, base_n_coins=3):
    # Min amount for coins = min(100, coin_balance / 10000)
    # Min amount for meta coins = min(100, LP_balance / 30000)
    # But >= 10**6

    min_amounts = [100] * len(decimals)
    if is_meta_underlying:
        min_amounts[0] = min(min_amounts[0], swap_contract.balances(0) / 10 ** decimals[0] / 10_000)
        min_amounts[1] = min(min_amounts[1], swap_contract.balances(1) / 10 ** 18 / 30_000)
        for i in range(base_n_coins - 1):
            min_amounts.append(min_amounts[len(min_amounts) - 1])
    else:
        for i, d in enumerate(decimals):
            min_amounts[i] = min(min_amounts[i], swap_contract.balances(i) / 10 ** d / 10_000)

    return [max(int(a * 10**d), 10**6) for a, d in zip(min_amounts, decimals)]


def _max_amounts(swap_contract, decimals, is_meta_underlying=False):
    # Max pure coin amount = coin_balance * 0.9
    # Max meta coin amount = LP_balance * 0.3
    max_amounts = []
    if is_meta_underlying:
        for i in range(len(decimals)):
            # just coins
            if i == 0:
                max_amounts.append(int(swap_contract.balances(i) * 0.9))
            # meta coins
            else:
                max_amounts.append(int(swap_contract.balances(1) * 0.3) // 10 ** (18 - decimals[i]))
    else:
        for i in range(len(decimals)):
            max_amounts.append(int(swap_contract.balances(i) * 0.9))

    return max_amounts


@given(wrapped_amounts=strategy('uint256[5]', min_value=10**16, max_value=10**6 * 10**18))
@settings(deadline=timedelta(seconds=1000))
def test_wrapped(
        stable_calc_zap,
        pool_data,
        swap_address,
        margo,
        n_coins_wrapped,
        wrapped_coins,
        wrapped_amounts,
        wrapped_decimals,
        is_meta,
        base_pool_data,
        use_lending,
        use_rate,
):
    swap_contract = Contract(swap_address)
    min_amounts = _min_amounts(swap_contract, wrapped_decimals)
    max_amounts = _max_amounts(swap_contract, wrapped_decimals)
    _wrapped_amounts = [int(x // 10 ** (18 - d)) for x, d in zip(wrapped_amounts, wrapped_decimals)]
    _wrapped_amounts = [max(a, min_a) for a, min_a in zip(_wrapped_amounts, min_amounts)]
    _wrapped_amounts = [min(a, max_a) for a, max_a in zip(_wrapped_amounts, max_amounts)]

    for i in range(n_coins_wrapped):
        for j in range(n_coins_wrapped):
            if i == j:
                continue

            desired = _wrapped_amounts[j]
            if is_meta:
                dx = stable_calc_zap.get_dx_meta(swap_address, i, j, desired, n_coins_wrapped, base_pool_data.get("swap_address"))
            else:
                dx = stable_calc_zap.get_dx(swap_address, i, j, desired, n_coins_wrapped)
            if dx == 0:
                continue
            dy = swap_contract.get_dy(i, j, dx)

            precision = 1e-7
            if pool_data["id"] == "usdt" or desired / 10**wrapped_decimals[j] < 10:
                precision = 1e-6
            if wrapped_decimals[i] == 2:
                precision = 1e-4
            assert abs(dy - desired) / desired < precision or abs(dy - desired) <= 10


@given(underlying_amounts=strategy('uint256[5]', min_value=10**16, max_value=10**5 * 10**18))
@settings(deadline=timedelta(seconds=1000))
def test_underlying(
        pool_data,
        stable_calc_zap,
        swap_address,
        deposit_address,
        n_coins_underlying,
        underlying_coins,
        underlying_amounts,
        underlying_decimals,
        base_pool_data,
        is_meta,
        use_lending,
):
    if not is_meta and not (True in use_lending):  # meta + aave,saave,ib,usdt,compound,y,busd,pax
        return

    swap_contract = Contract(swap_address)
    base_n_coins = 0
    if is_meta:
        base_n_coins = len(base_pool_data["coins"])

    if pool_data["id"] == "usdt":
        min_amounts = [100 * 10**18, 100 * 10**6, 100 * 10**6]
        max_amounts = [50_000 * 10**18, 50_000 * 10**6, 50_000 * 10**6]
    elif pool_data["id"] in ["ib", "compound"]:
        min_amounts = [100 * 10**18, 100 * 10**6, 100 * 10**6]
        max_amounts = [500_000 * 10**18, 500_000 * 10**6, 500_000 * 10**6]
    elif pool_data["id"] == "factory-v2-247":
        min_amounts = [int(0.01 * 10 ** 18), int(0.01 * 10 ** 8), int(0.01 * 10 ** 18)]
        max_amounts = [10 * 10 ** 18, 10 * 10 ** 8, 10 * 10 ** 18]
    else:
        min_amounts = _min_amounts(swap_contract, underlying_decimals, is_meta_underlying=is_meta, base_n_coins=base_n_coins)
        max_amounts = _max_amounts(swap_contract, underlying_decimals, is_meta_underlying=is_meta)

    _underlying_amounts = [int(x // 10 ** (18 - d)) for x, d in zip(underlying_amounts, underlying_decimals)]
    _underlying_amounts = [max(a, min_a) for a, min_a in zip(_underlying_amounts, min_amounts)]
    _underlying_amounts = [min(a, max_a) for a, max_a in zip(_underlying_amounts, max_amounts)]

    for i in range(n_coins_underlying):
        for j in range(n_coins_underlying):
            if i == j:
                continue

            desired = _underlying_amounts[j]
            if is_meta:
                base_pool = base_pool_data.get("swap_address")
                base_token = base_pool_data.get("lp_token_address")
                dx = stable_calc_zap.get_dx_meta_underlying(swap_address, i, j, desired, n_coins_underlying, base_pool, base_token)
            else:
                dx = stable_calc_zap.get_dx_underlying(swap_address, i, j, desired, n_coins_underlying)
            if dx == 0:
                continue

            try:
                dy = swap_contract.get_dy_underlying(i, j, dx)
            except:
                continue
            if dy == 0:
                continue

            precision = 1e-7
            if is_meta:
                precision = 2 * 1e-4
            if pool_data["id"] in ["factory-v2-247", "rai", "factory-v2-107", "factory-v2-339", "factory-v2-66"]:
                precision = 1e-3
            assert abs(dy - desired) / desired < precision or abs(dy - desired) <= 10
