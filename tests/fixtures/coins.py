import pytest
from brownie import Contract, ETH_ADDRESS, interface, ZERO_ADDRESS
from brownie.convert import to_bytes
from brownie_tokens import MintableForkToken


WRAPPED_COIN_METHODS = {
    "ATokenMock": {"get_rate": "_get_rate", "mint": "mint"},
    "cERC20": {"get_rate": "exchangeRateStored", "mint": "mint"},
    "IdleToken": {"get_rate": "tokenPrice", "mint": "mintIdleToken"},
    "renERC20": {"get_rate": "exchangeRateCurrent"},
    "yERC20": {"get_rate": "getPricePerFullShare", "mint": "deposit"},
    "aETH": {"get_rate": "ratio"},
    "rETH": {"get_rate": "getExchangeRate"},
    "WETH": {"mint": "deposit"},
}


# public fixtures - these can be used when testing

@pytest.fixture(scope="module")
def max_coins():
    return 5


@pytest.fixture(scope="module")
def wrapped_coins(pool_data, _underlying_coins, network):
    return _wrapped(pool_data, _underlying_coins, network)


@pytest.fixture(scope="module")
def underlying_coins(_underlying_coins, _base_coins):
    if _base_coins:
        return _underlying_coins[:1] + _base_coins
    else:
        return _underlying_coins


@pytest.fixture(scope="module")
def lp_token(pool_data):
    return Contract.from_explorer(pool_data['lp_token_address'])


# private API below


class _MintableTestTokenEthereum(MintableForkToken):
    def __init__(self, address, pool_data=None):
        super().__init__(address)

        # standardize mint / rate methods
        if pool_data is not None and "wrapped_contract" in pool_data:
            fn_names = WRAPPED_COIN_METHODS[pool_data["wrapped_contract"]]
            for target, attr in fn_names.items():
                if hasattr(self, attr) and target != attr:
                    setattr(self, target, getattr(self, attr))


class _MintableTestTokenOptimism(Contract):
    def __init__(self, address, interface_name):
        abi = getattr(interface, interface_name).abi
        self.from_abi(interface_name, address, abi)

        super().__init__(address)

    def _mint_for_testing(self, target, amount, kwargs=None):
        if self.address.lower() == "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1".lower():  # DAI
            self.transfer(target, amount, {"from": "0xd08cd45925132537ea241179b19ab3a33ad97f3d"})
        elif hasattr(self, "l2Bridge"):  # OptimismBridgeToken
            self.mint(target, amount, {"from": self.l2Bridge()})
        elif hasattr(self, "bridge"):  # OptimismBridgeToken2
            self.bridgeMint(target, amount, {"from": self.bridge()})
        elif hasattr(self, "mint") and hasattr(self, "owner"):  # renERC20
            self.mint(target, amount, {"from": self.owner()})
        elif hasattr(self, "mint") and hasattr(self, "minter"):  # CurveLpTokenV5
            self.mint(target, amount, {"from": self.minter()})
        else:
            raise ValueError("Unsupported Token")


class _MintableTestTokenXdai(Contract):
    wrapped = "0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d".lower()

    def __init__(self, address, interface_name):
        abi = getattr(interface, interface_name).abi
        self.from_abi(interface_name, address, abi)

        super().__init__(address)

    def _mint_for_testing(self, target, amount, kwargs=None):
        if self.address.lower() == self.wrapped:  # WXDAI
            self.transfer(target, amount, {"from": "0xd4e420bBf00b0F409188b338c5D87Df761d6C894"})  # Agave interest bearing WXDAI (agWXDAI)
        elif hasattr(self, "mint") and hasattr(self, "owner"):  # renERC20
            self.mint(target, amount, {"from": self.owner()})
        elif hasattr(self, "mint") and hasattr(self, "minter"):  # CurveLpTokenV5
            self.mint(target, amount, {"from": self.minter()})
        else:
            raise ValueError("Unsupported Token")


class _MintableTestTokenPolygon(Contract):
    WMATIC = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"

    def __init__(self, address, interface_name):
        abi = getattr(interface, interface_name).abi
        self.from_abi("PolygonToken", address, abi)

        super().__init__(address)

    def _mint_for_testing(self, target, amount, kwargs=None):
        if self.address.lower() == self.WMATIC.lower():  # WMATIC
            self.transfer(target, amount, {"from": "0xadbf1854e5883eb8aa7baf50705338739e558e5b"})
        elif self.address.lower() == "0xb5dfabd7ff7f83bab83995e72a52b97abb7bcf63".lower():  # USDR
            self.transfer(target, amount, {"from": "0xaf0d9d65fc54de245cda37af3d18cbec860a4d4b"})
        elif hasattr(self, "getRoleMember"):  # BridgeToken
            role = "0x8f4f2da22e8ac8f11e15f9fc141cddbb5deea8800186560abb6e68c5496619a9"
            minter = self.getRoleMember(role, 0)
            amount = to_bytes(amount, "bytes32")
            self.deposit(target, amount, {"from": minter})
        elif hasattr(self, "POOL"):  # AToken
            token = _MintableTestTokenPolygon(self.UNDERLYING_ASSET_ADDRESS(), "BridgeToken")
            lending_pool = interface.AaveLendingPool(self.POOL())
            token._mint_for_testing(target, amount)
            token.approve(lending_pool, amount, {"from": target})
            lending_pool.deposit(token, amount, target, 0, {"from": target})
        elif hasattr(self, "set_minter"):  # CurveLpToken
            pool = interface.CurvePool(self.minter())

            amDAI = _MintableTestTokenPolygon(pool.coins(0), "AToken")
            amUSDC = _MintableTestTokenPolygon(pool.coins(1), "AToken")
            amUSDT = _MintableTestTokenPolygon(pool.coins(2), "AToken")

            amounts = [int(amount / 3 * 1.2), int(amount / 10**12 / 3 * 1.2), int(amount / 10**12 / 3 * 1.2)]

            amDAI._mint_for_testing(target, amounts[0])
            amUSDC._mint_for_testing(target, amounts[1])
            amUSDT._mint_for_testing(target, amounts[2])

            amDAI.approve(pool, amounts[0], {"from": target})
            amUSDC.approve(pool, amounts[1], {"from": target})
            amUSDT.approve(pool, amounts[2], {"from": target})

            pool.add_liquidity(amounts, 0, {"from": target})
            if self.balanceOf(target) < amount:
                raise Exception("Not enough aave LP minted")
        elif hasattr(self, "mint"):  # renERC20
            self.mint(target, amount, {"from": self.owner()})
        else:
            raise ValueError("Unsupported Token")


class _MintableTestTokenFantom(Contract):
    wrapped = "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83"
    underlyingTokens =[
        '0x8D11eC38a3EB5E956B052f67Da8Bdc9bef8Abf3E'.lower(),
        '0x04068DA6C83AFCFA0e13ba15A6696662335D5B75'.lower(),
        '0x049d68029688eAbF473097a2fC38ef61633A3C7A'.lower(),
    ]
    iTokens = [
        '0x04c762a5dF2Fa02FE868F25359E0C259fB811CfE'.lower(),
        '0x328A7b4d538A2b3942653a9983fdA3C12c571141'.lower(),
        '0x70faC71debfD67394D1278D98A29dea79DC6E57A'.lower(),
    ]

    def __init__(self, address, interface_name):
        abi = getattr(interface, interface_name).abi
        self.from_abi(interface_name, address, abi)

        super().__init__(address)

    def _mint_for_testing(self, target, amount, kwargs=None):
        if self.address == self.wrapped:
            # Wrapped Fantom, send from SpookySwap
            self.transfer(target, amount, {"from": "0x2a651563c9d3af67ae0388a5c8f89b867038089e"})
        elif self.address.lower() in self.iTokens:
            idx = self.iTokens.index(self.address.lower())
            underlying_token = _MintableTestTokenFantom(self.underlyingTokens[idx], "AnyswapERC20")
            underlying_amount = int(amount * 10**(underlying_token.decimals() - 8))
            underlying_token._mint_for_testing(target, underlying_amount)
            underlying_token.approve(self.address, underlying_amount, {'from': target})
            self.mint(underlying_amount, {'from': target})
        elif self.address.lower() == "0x27e611fd27b276acbd5ffd632e5eaebec9761e40".lower():  # 2pool LP
            amount = amount // 10**18
            DAI = _MintableTestTokenFantom("0x8d11ec38a3eb5e956b052f67da8bdc9bef8abf3e", "AnyswapERC20")
            USDC = _MintableTestTokenFantom("0x04068da6c83afcfa0e13ba15a6696662335d5b75", "AnyswapERC20")
            DAI._mint_for_testing(target, (amount // 2) * 10 ** 18)
            USDC._mint_for_testing(target, (amount // 2) * 10 ** 6)

            pool_address = "0x27e611fd27b276acbd5ffd632e5eaebec9761e40"
            DAI.approve(pool_address, 2 ** 256 - 1, {'from': target})
            USDC.approve(pool_address, 2 ** 256 - 1, {'from': target})

            pool = Contract.from_explorer(pool_address)
            pool.add_liquidity([(amount // 2) * 10 ** 18, (amount // 2) * 10 ** 6], 0, {'from': target})
        elif hasattr(self, "Swapin"):  # AnyswapERC20
            tx_hash = to_bytes("0x4475636b204475636b20476f6f7365")
            self.Swapin(tx_hash, target, amount, {"from": self.owner()})
        elif hasattr(self, "POOL"):  # AToken (gToken)
            token = _MintableTestTokenFantom(self.UNDERLYING_ASSET_ADDRESS(), "AnyswapERC20")
            lending_pool = interface.AaveLendingPool(self.POOL())
            token._mint_for_testing(target, amount)
            token.approve(lending_pool, amount, {"from": target})
            lending_pool.deposit(token, amount, target, 0, {"from": target})
        elif hasattr(self, "mint") and hasattr(self, "owner"):  # renERC20
            self.mint(target, amount, {"from": self.owner()})
        elif hasattr(self, "mint") and hasattr(self, "minter"):  # CurveLpTokenV5
            self.mint(target, amount, {"from": self.minter()})
        else:
            raise ValueError("Unsupported Token")


class _MintableTestTokenArbitrum(Contract):
    wrapped = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"

    def __init__(self, address, interface_name):
        if interface_name:
            abi = getattr(interface, interface_name).abi
            self.from_abi(interface_name, address, abi)

        super().__init__(address)

    def _mint_for_testing(self, target, amount, kwargs=None):
        if self.address == self.wrapped:  # WETH
            self.transfer(target, amount, {"from": "0x0c1cf6883efa1b496b01f654e247b9b419873054"})
        elif hasattr(self, "l2Gateway"):  # ArbitrumERC20
            self.bridgeMint(target, amount, {"from": self.l2Gateway()})
        elif hasattr(self, "gatewayAddress"):  # ArbitrumUSDC
            self.bridgeMint(target, amount, {"from": self.gatewayAddress()})
        elif hasattr(self, "bridge"):  # OptimismBridgeToken2
            self.bridgeMint(target, amount, {"from": self.bridge()})
        elif hasattr(self, "POOL"):  # AToken
            token = _MintableTestTokenArbitrum(self.UNDERLYING_ASSET_ADDRESS(), "ArbitrumERC20")
            lending_pool = interface.AaveLendingPool(self.POOL())
            token._mint_for_testing(target, amount)
            token.approve(lending_pool, amount, {"from": target})
            lending_pool.deposit(token, amount, target, 0, {"from": target})
        elif hasattr(self, "mint") and hasattr(self, "owner"):  # renERC20
            self.mint(target, amount, {"from": self.owner()})
        elif hasattr(self, "mint") and hasattr(self, "minter"):  # CurveLpTokenV5
            self.mint(target, amount, {"from": self.minter()})
        else:
            raise ValueError("Unsupported Token")


class _MintableTestTokenAvalanche(Contract):
    WAVAX = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7"
    USDCT = ["0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E".lower(), "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7".lower()]

    def __init__(self, address, interface_name):
        abi = getattr(interface, interface_name).abi
        self.from_abi(interface_name, address, abi)

        super().__init__(address)

    def _mint_for_testing(self, target, amount, kwargs=None):
        if self.address.lower() == self.WAVAX.lower():  # WAVAX
            # Wrapped Avax, send from Iron Bank
            self.transfer(target, amount, {"from": "0xb3c68d69e95b095ab4b33b4cb67dbc0fbf3edf56"})
        elif self.address.lower() in self.USDCT:  # USDC, USDt
            self.transfer(target, amount, {"from": "0x9f8c163cba728e99993abe7495f06c0a3c8ac8b9"})  # Binance: C-Chain Hot Wallet
        elif hasattr(self, "POOL"):  # AToken
            token = _MintableTestTokenAvalanche(self.UNDERLYING_ASSET_ADDRESS(), "AvalancheERC20")
            lending_pool = interface.AaveLendingPool(self.POOL())
            token._mint_for_testing(target, amount)
            token.approve(lending_pool, amount, {"from": target})
            lending_pool.deposit(token, amount, target, 0, {"from": target})
        elif hasattr(self, "mint") and hasattr(self, "owner"):  # renERC20
            self.mint(target, amount, {"from": self.owner()})
        elif hasattr(self, "mint") and hasattr(self, "minter"):  # Curve LP Token
            self.mint(target, amount, {"from": self.minter()})
        elif hasattr(self, "mint"):  # AvalancheERC20 (bridge token)
            self.mint(target, amount, ZERO_ADDRESS, 0, 0x0, {"from": "0xEb1bB70123B2f43419d070d7fDE5618971cc2F8f"})
        else:
            raise ValueError("Unsupported Token")


def _get_coin_object(coin_address, coin_interface, pool_data, network):
    if network == "ethereum":
        return _MintableTestTokenEthereum(coin_address, pool_data)
    elif network == "optimism":
        return _MintableTestTokenOptimism(coin_address, coin_interface)
    elif network == "xdai":
        return _MintableTestTokenXdai(coin_address, coin_interface)
    elif network == "polygon":
        return _MintableTestTokenPolygon(coin_address, coin_interface)
    elif network == "fantom":
        return _MintableTestTokenFantom(coin_address, coin_interface)
    elif network == "arbitrum":
        return _MintableTestTokenArbitrum(coin_address, coin_interface)
    elif network == "avalanche":
        return _MintableTestTokenAvalanche(coin_address, coin_interface)


def _wrapped(pool_data, underlying_coins, network):
    coins = []

    if not pool_data.get("wrapped_contract"):
        return underlying_coins

    for i, coin_data in enumerate(pool_data["coins"]):
        if not coin_data.get("wrapped_address"):
            coins.append(underlying_coins[i])
        else:
            coins.append(_get_coin_object(coin_data.get("wrapped_address"), coin_data.get("wrapped_interface"), pool_data, network))
    return coins


def _underlying(pool_data, network):
    coins = []

    for coin_data in pool_data["coins"]:
        if coin_data.get("underlying_address") == ETH_ADDRESS:
            coins.append(ETH_ADDRESS)
        else:
            coins.append(
                _get_coin_object(
                    coin_data.get("underlying_address", coin_data.get("wrapped_address")),
                    coin_data.get("underlying_interface", coin_data.get("wrapped_interface")),
                    pool_data,
                    network,
                )
            )

    return coins


# private fixtures used for setup in other fixtures - do not use in tests!


@pytest.fixture(scope="module")
def _underlying_coins(pool_data, network):
    return _underlying(pool_data, network)


@pytest.fixture(scope="module")
def _base_coins(base_pool_data, network):
    if base_pool_data is None:
        return []
    return _underlying(base_pool_data, network)
