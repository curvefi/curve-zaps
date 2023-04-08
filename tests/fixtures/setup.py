import pytest
from brownie import ETH_ADDRESS, accounts, Contract


def _approve(owner, spender, *coins):
    for coin in set(x for i in coins for x in i):
        if coin == ETH_ADDRESS or coin.allowance(owner, spender) > 2 ** 255:
            continue
        coin.approve(spender, 2 ** 256 - 1, {"from": owner})


# pool setup fixtures

@pytest.fixture(scope="module")
def mint_margo(margo, lp_token, swap_address, underlying_coins, wrapped_coins, wrapped_amounts_to_mint, underlying_amounts_to_mint, is_meta, weth, network):

    # --- UNDERLYING ---

    for coin, amount in zip(underlying_coins, underlying_amounts_to_mint):
        if coin in wrapped_coins:
            balance = margo.balance()
            if coin != ETH_ADDRESS:
                balance = coin.balanceOf(margo)
            if balance >= amount:
                continue
        if coin == ETH_ADDRESS:
            _weth = accounts.at(weth[network], True)
            _weth.transfer(margo, amount)
            continue
        if network == "ethereum":
            if coin.address.lower() == "0xE95A203B1a91a908F9B9CE46459d101078c2c3cb".lower():  # ankrETH
                coin.transfer(margo, amount, {"from": "0x13e252Df0caFe34116cEc052177b7540aFc75F76"})  # steal
                continue
        coin._mint_for_testing(margo, amount, {"from": margo})

    # --- WRAPPED ---

    if lp_token.address.lower() == "0x5282a4eF67D9C33135340fB3289cc1711c13638C".lower():  # ib on ethereum
        mint_amount = sum(wrapped_amounts_to_mint) * 10**10 * 2
        lp_token.transfer(margo, mint_amount, {"from": "0x6c904b3Bb57865516a0d054CCfE7449e01B85421"})  # steal
        swap_contract = Contract(swap_address)
        swap_contract.remove_liquidity_imbalance(wrapped_amounts_to_mint, 2**256 - 1, {"from": margo})
        lp_token.transfer("0x6c904b3Bb57865516a0d054CCfE7449e01B85421", lp_token.balanceOf(margo), {"from": margo})  # send back excess
        return

    if lp_token.address.lower() == "0xD905e2eaeBe188fc92179b6350807D8bd91Db0D8".lower():  # pax on ethereum
        mint_amount = (wrapped_amounts_to_mint[0] + wrapped_amounts_to_mint[3]) + (wrapped_amounts_to_mint[1] + wrapped_amounts_to_mint[2]) * 10**12 * 2
        lp_token.transfer(margo, mint_amount, {"from": "0x3c43e281787687590E819e8720F9bC64D94Bb7CB"})  # steal
        swap_contract = Contract(swap_address)
        swap_contract.remove_liquidity_imbalance(wrapped_amounts_to_mint, 2**256 - 1, {"from": margo})
        lp_token.transfer("0x3c43e281787687590E819e8720F9bC64D94Bb7CB", lp_token.balanceOf(margo), {"from": margo})  # send back excess
        return

    for coin, amount in zip(wrapped_coins, wrapped_amounts_to_mint):
        if coin == ETH_ADDRESS:
            # in fork mode, we steal ETH from the wETH contract
            _weth = accounts.at(weth[network], True)
            _weth.transfer(margo, amount)
            continue
        if network == "ethereum":
            if coin.address.lower() == "0xE95A203B1a91a908F9B9CE46459d101078c2c3cb".lower():  # ankrETH
                coin.transfer(margo, amount, {"from": "0x13e252Df0caFe34116cEc052177b7540aFc75F76"})  # steal
                continue
        coin._mint_for_testing(margo, amount, {"from": margo})


@pytest.fixture(scope="module")
def approve_margo(margo, swap_address, deposit_address, underlying_coins, wrapped_coins, lp_token):
    _approve(margo, swap_address, underlying_coins, wrapped_coins)
    if deposit_address != swap_address:
        _approve(margo, deposit_address, underlying_coins + [lp_token])
