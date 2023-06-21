from brownie import Contract, chain
from brownie.test import given, strategy
from hypothesis import settings
from datetime import timedelta


@given(wrapped_amounts=strategy('uint256[5]', min_value=10**16, max_value=10**6 * 10**18))
@settings(deadline=timedelta(seconds=1000))
def test_wrapped(
        zap,
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
):
    _wrapped_amounts = [int(x // 10 ** (18 - d)) for x, d in zip(wrapped_amounts, wrapped_decimals)]
    swap_contract = Contract(swap_address)

    for i in range(n_coins_wrapped):
        for j in range(n_coins_wrapped):
            if i == j:
                continue

            desired = min(_wrapped_amounts[j], int(swap_contract.balances(j) * 0.99))
            if is_meta:
                dx = zap.get_dx_meta(swap_address, i, j, desired, n_coins_wrapped, base_pool_data.get("swap_address"))
            else:
                dx = zap.get_dx(swap_address, i, j, desired, n_coins_wrapped)
            if dx == 0:
                continue
            dy = swap_contract.get_dy(i, j, dx)

            precision = 3
            if min(wrapped_decimals[i], wrapped_decimals[j]) < 6 or wrapped_amounts[j] <= 10**17:
                precision = 2
                if is_meta:
                    precision = 1
            assert abs(dy - desired) / desired < 10**(-precision) or abs(dy - desired) == 1


@given(underlying_amounts=strategy('uint256[5]', min_value=10**16, max_value=10**5 * 10**18))
@settings(deadline=timedelta(seconds=1000))
def test_underlying(
        pool_data,
        zap,
        swap_address,
        deposit_address,
        n_coins_underlying,
        underlying_coins,
        underlying_amounts,
        underlying_decimals,
        base_pool_data,
        is_meta,
        is_factory,
        use_lending,
):
    if not is_meta and not (True in use_lending):  # meta + aave,saave,ib,usdt,compound,y,busd,pax
        return

    underlying_amounts = [int(x // 10 ** (18 - d)) for x, d in zip(underlying_amounts, underlying_decimals)]
    swap_contract = Contract(swap_address)

    for i in range(n_coins_underlying):
        for j in range(n_coins_underlying):
            if i == j:
                continue


            desired = underlying_amounts[j]
            if pool_data["id"] in ["ib"]:
                desired = min(desired, 10**3 * 10**underlying_decimals[j])
            if pool_data["id"] in ["usdt"]:
                desired = min(desired, 10**4 * 10**underlying_decimals[j])
            if is_meta:
                if j == 0:
                    desired = min(desired, int(swap_contract.balances(0) / 2))
                else:
                    desired = min(desired, int(swap_contract.balances(1) * 10**underlying_decimals[j] / 10**18 / ((len(underlying_decimals) - 1) * 2)))

            if is_meta:
                base_pool = base_pool_data.get("swap_address")
                base_token = base_pool_data.get("lp_token_address")
                dx = zap.get_dx_meta_underlying(swap_address, i, j, desired, n_coins_underlying, base_pool, base_token)
            else:
                dx = zap.get_dx_underlying(swap_address, i, j, desired, n_coins_underlying)
            if dx == 0:
                continue

            try:
                dy = swap_contract.get_dy_underlying(i, j, dx)
            except:
                continue
            if dy == 0:
                continue

            if min(underlying_decimals[i], underlying_decimals[j]) < 10 or pool_data["id"] in ["factory-v2-247"]:
                assert abs(dy - desired) / desired < 0.01 or abs(dy - desired) <= 1
            else:
                assert abs(dy - desired) / desired < 0.001
