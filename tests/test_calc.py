import brownie
import pytest
from brownie import Contract, chain
from brownie.test import given, strategy
from hypothesis import settings
from datetime import timedelta

pytestmark = pytest.mark.usefixtures("mint_margo", "approve_margo")


@given(wrapped_amounts=strategy('uint256[4]', min_value=10**16, max_value=10**6 * 10**18))
@settings(deadline=timedelta(seconds=1000))
def test_wrapped(
        zap,
        swap_address,
        lp_token,
        margo,
        n_coins_wrapped,
        wrapped_amounts_to_mint,
        wrapped_coins,
        wrapped_amounts,
        wrapped_decimals,
        is_meta,
        base_pool_data,
        use_lending,
        use_rate,
):
    wrapped_amounts = [int(x // 10 ** (18 - d)) for x, d in zip(wrapped_amounts, wrapped_decimals)]
    wrapped_amounts = [min(x, y) for x, y in zip(wrapped_amounts, wrapped_amounts_to_mint)] + [0] * (4 - n_coins_wrapped)
    value = wrapped_amounts[wrapped_coins.index(brownie.ETH_ADDRESS)] if brownie.ETH_ADDRESS in wrapped_coins else 0
    swap_contract = Contract(swap_address)

    # Deposit
    if is_meta:
        base_pool_address = base_pool_data.get("swap_address")
        base_pool_token = base_pool_data.get("lp_token_address")
        expected = zap.calc_token_amount_meta(swap_address, lp_token.address, wrapped_amounts, n_coins_wrapped, base_pool_address, base_pool_token, True, False)
    else:
        expected = zap.calc_token_amount(swap_address, lp_token.address, wrapped_amounts, n_coins_wrapped, True)
    swap_contract.add_liquidity(wrapped_amounts[:n_coins_wrapped], 0, {"from": margo, "value": value})

    lp_balance = lp_token.balanceOf(margo)
    if True in use_lending:
        assert abs(expected - lp_balance) / lp_balance < 1e-7
    elif True in use_rate:
        assert abs(expected - lp_balance) <= 100
    else:
        assert abs(expected - lp_balance) <= 2

    # Withdraw
    withdraw_amounts = list(map(lambda x: int(x / 1.02), wrapped_amounts))
    if is_meta:
        base_pool_address = base_pool_data.get("swap_address")
        base_pool_token = base_pool_data.get("lp_token_address")
        expected = zap.calc_token_amount_meta(swap_address, lp_token.address, withdraw_amounts, n_coins_wrapped, base_pool_address, base_pool_token, False, False)
    else:
        expected = zap.calc_token_amount(swap_address, lp_token.address, withdraw_amounts, n_coins_wrapped, False)
    swap_contract.remove_liquidity_imbalance(withdraw_amounts[:n_coins_wrapped], 2**256 - 1, {"from": margo})
    lp_balance_diff = lp_balance - lp_token.balanceOf(margo)
    if True in use_lending:
        assert abs(expected - lp_balance_diff) < 10 ** 15
    elif True in use_rate:
        assert abs(expected - lp_balance_diff) <= 100
    else:
        assert abs(expected - lp_balance_diff) <= 2


@given(underlying_amounts=strategy('uint256[4]', min_value=10**16, max_value=10**5 * 10**18))
@settings(deadline=timedelta(seconds=1000))
def test_underlying(
        zap,
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
):
    if not is_meta:
        return

    underlying_amounts = [int(x // 10 ** (18 - d)) for x, d in zip(underlying_amounts, underlying_decimals)] + [0] * (4 - n_coins_underlying)
    value = underlying_amounts[underlying_coins.index(brownie.ETH_ADDRESS)] if brownie.ETH_ADDRESS in underlying_coins else 0
    zap_contract = Contract(deposit_address)

    # Deposit
    base_pool_address = base_pool_data.get("swap_address")
    base_pool_token = base_pool_data.get("lp_token_address")
    expected = zap.calc_token_amount_meta(swap_address, lp_token.address, underlying_amounts, n_coins_underlying, base_pool_address, base_pool_token, True, True)
    zap_contract.add_liquidity(underlying_amounts[:n_coins_underlying], 0, {"from": margo, "value": value})

    lp_balance = lp_token.balanceOf(margo)
    if chain.id == 250:  # Fantom
        assert abs(expected - lp_balance) / lp_balance < 1e-6
    else:
        assert abs(expected - lp_balance) / lp_balance < 1e-8

    # Withdraw
    withdraw_amounts = list(map(lambda x: int(x / 1.02), underlying_amounts))
    expected = zap.calc_token_amount_meta(swap_address, lp_token.address, withdraw_amounts, n_coins_underlying, base_pool_address, base_pool_token, False, True)
    zap_contract.remove_liquidity_imbalance(withdraw_amounts[:n_coins_underlying], lp_balance, {"from": margo})
    lp_balance_diff = lp_balance - lp_token.balanceOf(margo)
    assert abs(expected - lp_balance_diff) / lp_balance_diff < 1e-7
