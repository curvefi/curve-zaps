from brownie import Contract, project
from brownie.test import given, strategy
from hypothesis import settings
from datetime import timedelta


@given(wrapped_amounts=strategy('uint256[5]', min_value=10**16, max_value=10**6 * 10**18))
@settings(deadline=timedelta(seconds=1000))
def test_wrapped(crypto_calc_zap, pool_data, swap_address, n_coins_wrapped, wrapped_amounts, wrapped_decimals, is_crypto):
    if not is_crypto:
        raise Exception(f"{pool_data['id']} is not a crypto pool")
    _wrapped_amounts = [int(x // 10 ** (18 - d)) for x, d in zip(wrapped_amounts, wrapped_decimals)]
    swap_contract = Contract(swap_address)

    for i in range(n_coins_wrapped):
        for j in range(n_coins_wrapped):
            if i == j:
                continue

            desired = min(_wrapped_amounts[j], int(swap_contract.balances(j) * 0.5))
            desired = max(desired, 10**6)
            dx = crypto_calc_zap.get_dx(swap_address, i, j, desired, n_coins_wrapped)
            if dx == 0:
                continue
            dy = swap_contract.get_dy(i, j, dx)

            precision = 2
            assert abs(dy - desired) / desired < 10**(-precision) or abs(dy - desired) == 1


@given(underlying_amounts=strategy('uint256[5]', min_value=10**18, max_value=10**6 * 10**18))
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
):
    if not is_crypto or not  is_meta:
        raise Exception(f"{pool_data['id']} is not a crypto-meta pool")
    _underlying_amounts = [int(x // 10 ** (18 - d)) for x, d in zip(underlying_amounts, underlying_decimals)]
    swap_contract = Contract(swap_address)
    try:
        pool_zap_contract = Contract.from_explorer(deposit_address)
    except:
        pool_zap_contract = Contract.from_abi('Coin', deposit_address, project.get_loaded_projects()[0].interface.CryptoMetaZap.abi)

    for i in range(n_coins_underlying):
        for j in range(n_coins_underlying):
            if i == j:
                continue

            base_pool = base_pool_data.get("swap_address")
            base_token = base_pool_data.get("lp_token_address")
            base_n_coins = len(base_pool_data["coins"])
            if n_coins_underlying - base_n_coins == 1:  # 2-crypto
                if j == 0:
                    desired = min(_underlying_amounts[j], int(swap_contract.balances(j) * 0.5))
                else:
                    desired = min(_underlying_amounts[j], int(swap_contract.balances(1) * 0.2) // 10 ** (18 - underlying_decimals[j]))
                dx = crypto_calc_zap.get_dx_meta_underlying(swap_address, i, j, desired, n_coins_underlying, base_pool, base_token)
            else:  # tricrypto
                if j >= base_n_coins:
                    desired = min(_underlying_amounts[j], int(swap_contract.balances(j - base_n_coins + 1) * 0.5))
                else:
                    desired = min(_underlying_amounts[j], int(swap_contract.balances(0) * 0.2) // 10 ** (18 - underlying_decimals[j]))
                dx = crypto_calc_zap.get_dx_tricrypto_meta_underlying(swap_address, i, j, desired, n_coins_underlying, base_pool, base_token)

            if dx == 0:
                continue
            if is_factory:
                dy = pool_zap_contract.get_dy(swap_address, i, j, dx)
            else:
                dy = pool_zap_contract.get_dy_underlying(i, j, dx)

            precision = 2
            assert abs(dy - desired) / desired < 10**(-precision) or abs(dy - desired) == 1
