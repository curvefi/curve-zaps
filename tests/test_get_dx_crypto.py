from brownie import Contract, project
from brownie.test import given, strategy
from hypothesis import settings
from datetime import timedelta


def _min_amounts(swap_contract, decimals, is_tricrypto, is_meta_underlying=False, base_n_coins=3):
    # Min amount for the cheapest coin = 100, for other coins = 100 * rate
    # Min amount for meta coins = min amount for LP
    if is_tricrypto:
        prices = [10**18, swap_contract.price_scale(0), swap_contract.price_scale(1)]
    else:
        prices = [10**18, swap_contract.price_scale()]

    min_amounts = [100] * len(prices)
    for i, p in enumerate(prices):
        min_amounts[i] = min_amounts[i] * min(prices) / p

    if is_meta_underlying:
        if is_tricrypto:
            for i in range(base_n_coins - 1):
                min_amounts.insert(0, min_amounts[0])
        else:
            for i in range(base_n_coins - 1):
                min_amounts.append(min_amounts[len(min_amounts) - 1])

    return [int(a * 10**d) for a, d in zip(min_amounts, decimals)]


def _max_amounts(swap_contract, decimals, is_tricrypto=False, is_meta_underlying=False, base_n_coins=3):
    # Max pure coin amount = coin_balance * 0.5
    # Max meta coin amount = LP_balance * 0.2
    max_amounts = []
    if is_meta_underlying:
        if is_tricrypto:
            for i in range(len(decimals)):
                # just coins
                if i >= base_n_coins:
                    max_amounts.append(int(swap_contract.balances(i - base_n_coins + 1) * 0.5))
                # meta coins
                else:
                    max_amounts.append(int(swap_contract.balances(0) * 0.2) // 10 ** (18 - decimals[i]))
        else:
            for i in range(len(decimals)):
                # just coins
                if i == 0:
                    max_amounts.append(int(swap_contract.balances(i) * 0.5))
                # meta coins
                else:
                    max_amounts.append(int(swap_contract.balances(1) * 0.2) // 10 ** (18 - decimals[i]))
    else:
        for i in range(len(decimals)):
            max_amounts.append(int(swap_contract.balances(i) * 0.5))

    return max_amounts


@given(wrapped_amounts=strategy('uint256[5]', min_value=10**16, max_value=10**6 * 10**18))
@settings(deadline=timedelta(seconds=1000))
def test_wrapped(crypto_calc_zap, pool_data, swap_address, n_coins_wrapped, wrapped_amounts, wrapped_decimals, is_crypto, math_2_coins, math_3_coins):
    if not is_crypto:
        return

    swap_contract = Contract(swap_address)
    is_tricrypto = n_coins_wrapped == 3
    min_amounts = _min_amounts(swap_contract, wrapped_decimals, is_tricrypto)
    max_amounts = _max_amounts(swap_contract, wrapped_decimals, is_tricrypto)
    _wrapped_amounts = [int(x // 10 ** (18 - d)) for x, d in zip(wrapped_amounts, wrapped_decimals)]
    _wrapped_amounts = [max(a, min_a) for a, min_a in zip(_wrapped_amounts, min_amounts)]
    _wrapped_amounts = [min(a, max_a) for a, max_a in zip(_wrapped_amounts, max_amounts)]

    for i in range(n_coins_wrapped):
        for j in range(n_coins_wrapped):
            if i == j:
                continue

            desired = _wrapped_amounts[j]
            dx = crypto_calc_zap.get_dx(swap_address, i, j, desired, n_coins_wrapped)
            if dx == 0:
                continue
            dy = swap_contract.get_dy(i, j, dx)

            precision = 4 if (wrapped_decimals[i] == 2 or wrapped_decimals[j] == 2) else 5
            assert abs(dy - desired) / desired < 10**(-precision) or abs(dy - desired) == 1


@given(underlying_amounts=strategy('uint256[5]', min_value=10**16, max_value=10**6 * 10**18))
@settings(deadline=timedelta(seconds=1000))
def test_underlying(
        crypto_calc_zap,
        pool_data,
        swap_address,
        deposit_address,
        n_coins_underlying,
        underlying_amounts,
        underlying_decimals,
        is_meta,
        is_factory,
        base_pool_data,
        is_crypto,
        math_2_coins,
        math_3_coins,
):
    if not is_crypto or not is_meta:
        return

    swap_contract = Contract(swap_address)
    try:
        pool_zap_contract = Contract.from_explorer(deposit_address)
    except:
        pool_zap_contract = Contract.from_abi('Coin', deposit_address, project.get_loaded_projects()[0].interface.CryptoMetaZap.abi)

    base_pool = base_pool_data.get("swap_address")
    base_token = base_pool_data.get("lp_token_address")
    base_n_coins = len(base_pool_data["coins"])
    is_tricrypto = n_coins_underlying - base_n_coins + 1 == 3

    _underlying_amounts = [int(x // 10 ** (18 - d)) for x, d in zip(underlying_amounts, underlying_decimals)]
    min_amounts = _min_amounts(swap_contract, underlying_decimals, is_tricrypto, is_meta_underlying=True, base_n_coins=base_n_coins)
    max_amounts = _max_amounts(swap_contract, underlying_decimals, is_tricrypto, is_meta_underlying=True, base_n_coins=base_n_coins)
    _underlying_amounts = [max(a, min_a) for a, min_a in zip(_underlying_amounts, min_amounts)]
    _underlying_amounts = [min(a, max_a) for a, max_a in zip(_underlying_amounts, max_amounts)]

    for i in range(n_coins_underlying):
        for j in range(n_coins_underlying):
            if i == j:
                continue

            desired = _underlying_amounts[j]
            if is_tricrypto:
                dx = crypto_calc_zap.get_dx_tricrypto_meta_underlying(swap_address, i, j, desired, n_coins_underlying, base_pool, base_token)
            else:
                dx = crypto_calc_zap.get_dx_meta_underlying(swap_address, i, j, desired, n_coins_underlying, base_pool, base_token)
            if dx == 0:
                continue

            if is_factory:
                dy = pool_zap_contract.get_dy(swap_address, i, j, dx)
            else:
                dy = pool_zap_contract.get_dy_underlying(i, j, dx)

            precision = 4 if (underlying_decimals[i] == 2 or underlying_decimals[j] == 2) else 5
            assert abs(dy - desired) / desired < 10**(-precision) or abs(dy - desired) == 1
