from brownie import Contract
from brownie.test import given, strategy
from hypothesis import settings
from datetime import timedelta


@given(wrapped_amounts=strategy('uint256[5]', min_value=10**16, max_value=10**6 * 10**18))
@settings(deadline=timedelta(seconds=1000))
def test_wrapped(
        crypto_calc_zap,
        pool_data,
        swap_address,
        margo,
        n_coins_wrapped,
        wrapped_coins,
        wrapped_amounts,
        wrapped_decimals,
        is_meta,
        is_factory,
        base_pool_data,
        use_lending,
        use_rate,
        is_crypto,
):
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
