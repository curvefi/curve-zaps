import pytest
from brownie import Contract, chain, ETH_ADDRESS
from brownie.test import given, strategy
from hypothesis import settings
from datetime import timedelta

pytestmark = pytest.mark.usefixtures("mint_margo", "approve_margo")


def _get_balance(coin, margo) -> int:
    return margo.balance() if coin == ETH_ADDRESS else coin.balanceOf(margo)


def _format_amounts(coins, amounts, decimals, margo, n, max_n):
    amounts = [int(x // 10 ** (18 - d)) for x, d in zip(amounts, decimals)]
    return [min(a, _get_balance(c, margo)) for a, c in zip(amounts, coins)] + [0] * (max_n - n)


@given(wrapped_amounts=strategy('uint256[5]', min_value=10**16, max_value=10**6 * 10**18))
@settings(deadline=timedelta(seconds=1000))
def test_wrapped(
        stable_calc_zap,
        swap_address,
        lp_token,
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
        max_coins,
):
    wrapped_amounts = _format_amounts(wrapped_coins, wrapped_amounts, wrapped_decimals, margo, n_coins_wrapped, max_coins)
    value = wrapped_amounts[wrapped_coins.index(ETH_ADDRESS)] if ETH_ADDRESS in wrapped_coins else 0
    swap_contract = Contract(swap_address)

    # Deposit
    if is_meta:
        base_pool_address = base_pool_data.get("swap_address")
        base_pool_token = base_pool_data.get("lp_token_address")
        expected = stable_calc_zap.calc_token_amount_meta(swap_address, lp_token.address, wrapped_amounts, n_coins_wrapped, base_pool_address, base_pool_token, True, False)
    else:
        expected = stable_calc_zap.calc_token_amount(swap_address, lp_token.address, wrapped_amounts, n_coins_wrapped, True, False)
    swap_contract.add_liquidity(wrapped_amounts[:n_coins_wrapped], 0, {"from": margo, "value": value})

    lp_balance = lp_token.balanceOf(margo)
    if True in use_lending or is_meta and base_pool_data["id"] == "aave":
        assert abs(expected - lp_balance) / lp_balance < 2 * 1e-7
    elif True in use_rate:
        assert abs(expected - lp_balance) <= 100
    else:
        assert abs(expected - lp_balance) <= 10

    # Withdraw
    withdraw_amounts = list(map(lambda x: int(x / 1.02), wrapped_amounts))
    if is_meta:
        base_pool_address = base_pool_data.get("swap_address")
        base_pool_token = base_pool_data.get("lp_token_address")
        expected = stable_calc_zap.calc_token_amount_meta(swap_address, lp_token.address, withdraw_amounts, n_coins_wrapped, base_pool_address, base_pool_token, False, False)
    else:
        expected = stable_calc_zap.calc_token_amount(swap_address, lp_token.address, withdraw_amounts, n_coins_wrapped, False, False)
    swap_contract.remove_liquidity_imbalance(withdraw_amounts[:n_coins_wrapped], 2**256 - 1, {"from": margo})
    lp_balance_diff = lp_balance - lp_token.balanceOf(margo)

    if True in use_lending or is_meta and base_pool_data["id"] == "aave":
        assert abs(expected - lp_balance_diff) / lp_balance_diff < 1e-7
    elif True in use_rate:
        assert abs(expected - lp_balance_diff) <= 100
    else:
        assert abs(expected - lp_balance_diff) <= 10


@given(underlying_amounts=strategy('uint256[5]', min_value=10**16, max_value=10**5 * 10**18))
@settings(deadline=timedelta(seconds=1000))
def test_underlying(
        pool_data,
        stable_calc_zap,
        swap_address,
        deposit_address,
        lp_token,
        margo,
        n_coins_underlying,
        underlying_coins,
        underlying_amounts,
        underlying_decimals,
        base_pool_data,
        is_meta,
        is_factory,
        use_lending,
        max_coins,
):
    if not is_meta and not (True in use_lending):  # meta + aave,saave,ib,usdt,compound,y,busd,pax
        return

    if not is_meta:
        base_pool_data = {"id": ""}

    underlying_amounts = _format_amounts(underlying_coins, underlying_amounts, underlying_decimals, margo, n_coins_underlying, max_coins)
    value = underlying_amounts[underlying_coins.index(ETH_ADDRESS)] if ETH_ADDRESS in underlying_coins else 0
    deposit_contract = Contract(deposit_address)

    deposit_contract_lp_balance = lp_token.balanceOf(deposit_contract)  # zap can have some dust

    # Deposit
    if is_meta:
        base_pool_address = base_pool_data.get("swap_address")
        base_pool_token = base_pool_data.get("lp_token_address")
        expected = stable_calc_zap.calc_token_amount_meta(swap_address, lp_token.address, underlying_amounts, n_coins_underlying, base_pool_address, base_pool_token, True, True)
    else:
        expected = stable_calc_zap.calc_token_amount(swap_address, lp_token.address, underlying_amounts, n_coins_underlying, True, True)
    if is_factory:
        deposit_contract.add_liquidity(swap_address, underlying_amounts[:n_coins_underlying], 0, {"from": margo, "value": value})
    elif pool_data["id"] in ["aave", "saave", "ib", "geist"]:
        deposit_contract.add_liquidity(underlying_amounts[:n_coins_underlying], 0, True, {"from": margo, "value": value})
    else:
        deposit_contract.add_liquidity(underlying_amounts[:n_coins_underlying], 0, {"from": margo, "value": value})

    lp_balance = lp_token.balanceOf(margo)
    lp_balance_no_dust = lp_balance - deposit_contract_lp_balance if deposit_address != swap_address else lp_balance
    if True in use_lending or chain.id == 43114 or chain.id == 1 and base_pool_data["id"] == "sbtc2":  # Avalanche, Ethereum
        assert abs(expected - lp_balance_no_dust) / lp_balance_no_dust < 1e-5
    elif chain.id == 100 or chain.id == 137 or chain.id == 250:  # xDai or Polygon or Fantom
        assert abs(expected - lp_balance_no_dust) / lp_balance_no_dust < 1e-6
    else:
        assert abs(expected - lp_balance_no_dust) / lp_balance_no_dust < 1e-8

    # Withdraw
    withdraw_amounts = list(map(lambda x: int(x / 1.02), underlying_amounts))
    if base_pool_data["id"] == "aave":  # too unbalanced withdraw breaks aave zap
        withdraw_amounts_float = [x / 10**d for x, d in zip(withdraw_amounts, underlying_decimals)]
        min_amount = min(withdraw_amounts_float)
        withdraw_amounts = [int(min(x, min_amount * 5) * 10**d) for x, d in zip(withdraw_amounts_float, underlying_decimals)]
        withdraw_amounts += [0] * (max_coins - len(withdraw_amounts))
    if is_meta:
        base_pool_address = base_pool_data.get("swap_address")
        base_pool_token = base_pool_data.get("lp_token_address")
        expected = stable_calc_zap.calc_token_amount_meta(swap_address, lp_token.address, withdraw_amounts, n_coins_underlying, base_pool_address, base_pool_token, False, True)
    else:
        expected = stable_calc_zap.calc_token_amount(swap_address, lp_token.address, withdraw_amounts, n_coins_underlying, False, True)
    if is_factory:
        deposit_contract.remove_liquidity_imbalance(swap_address, withdraw_amounts[:n_coins_underlying], lp_balance, {"from": margo})
    elif pool_data["id"] in ["aave", "saave", "ib", "geist"]:
        deposit_contract.remove_liquidity_imbalance(withdraw_amounts[:n_coins_underlying], lp_balance, True, {"from": margo})
    else:
        deposit_contract.remove_liquidity_imbalance(withdraw_amounts[:n_coins_underlying], lp_balance, {"from": margo})
    lp_balance_diff = lp_balance - lp_token.balanceOf(margo)

    assert abs(expected - lp_balance_diff) / lp_balance_diff < 3 * 1e-7
