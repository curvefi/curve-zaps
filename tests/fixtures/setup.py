import pytest
from brownie import ETH_ADDRESS, accounts, chain


def _approve(owner, spender, *coins):
    for coin in set(x for i in coins for x in i):
        if coin == ETH_ADDRESS or coin.allowance(owner, spender) > 2 ** 255:
            continue
        coin.approve(spender, 2 ** 256 - 1, {"from": owner})


# pool setup fixtures

@pytest.fixture(scope="module")
def mint_margo(margo, underlying_coins, wrapped_coins, wrapped_amounts_to_mint, underlying_amounts_to_mint, is_meta, weth, network):
    for coin, amount in zip(wrapped_coins, wrapped_amounts_to_mint):
        if coin == ETH_ADDRESS:
            # in fork mode, we steal ETH from the wETH contract
            weth = accounts.at(weth[network], True)
            weth.transfer(margo, amount)
            continue
        if coin.address == "0xE95A203B1a91a908F9B9CE46459d101078c2c3cb":
            coin.transfer(margo, amount, {"from": "0x13e252Df0caFe34116cEc052177b7540aFc75F76"})  # steal
            continue
        coin._mint_for_testing(margo, amount, {"from": margo})

    for coin, amount in zip(underlying_coins, underlying_amounts_to_mint):
        if coin in wrapped_coins:
            continue
        if coin == ETH_ADDRESS:
            weth = accounts.at(weth[network], True)
            weth.transfer(margo, amount)
            continue
        if coin.address == "0xE95A203B1a91a908F9B9CE46459d101078c2c3cb":
            coin.transfer(margo, amount, {"from": "0x13e252Df0caFe34116cEc052177b7540aFc75F76"})  # steal
            continue
        coin._mint_for_testing(margo, amount, {"from": margo})


@pytest.fixture(scope="module")
def approve_margo(margo, swap_address, deposit_address, underlying_coins, wrapped_coins, lp_token):
    _approve(margo, swap_address, underlying_coins, wrapped_coins)
    if deposit_address != swap_address:
        _approve(margo, deposit_address, underlying_coins + [lp_token])
