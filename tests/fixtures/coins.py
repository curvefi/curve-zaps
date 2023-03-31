import pytest
from brownie import Contract, ETH_ADDRESS, interface, chain
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
def wrapped_coins(pool_data, _underlying_coins):
    return _wrapped(pool_data, _underlying_coins)


@pytest.fixture(scope="module")
def underlying_coins(_underlying_coins, _base_coins):
    if _base_coins:
        return _underlying_coins[:1] + _base_coins
    else:
        return _underlying_coins


@pytest.fixture(scope="module")
def lp_token(pool_data):
    return Contract(pool_data['lp_token_address'])


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


class _MintableTestTokenPolygon(Contract):
    WMATIC = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"

    def __init__(self, address, interface_name):
        abi = getattr(interface, interface_name).abi
        self.from_abi("PolygonToken", address, abi)

        super().__init__(address)

    def _mint_for_testing(self, target, amount, kwargs=None):
        if self.address.lower() == self.WMATIC.lower():  # WMATIC
            self.transfer(target, amount, {"from": "0xadbf1854e5883eb8aa7baf50705338739e558e5b"})
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

            amounts = [int(amount / 3), int(amount / 10**12 / 3), int(amount / 10**12 / 3)]

            amDAI._mint_for_testing(target, amounts[0])
            amUSDC._mint_for_testing(target, amounts[1])
            amUSDT._mint_for_testing(target, amounts[2])

            amDAI.approve(pool, amounts[0], {"from": target})
            amUSDC.approve(pool, amounts[1], {"from": target})
            amUSDT.approve(pool, amounts[2], {"from": target})

            pool.add_liquidity(amounts, 0, {"from": target})
        elif hasattr(self, "mint"):  # renERC20
            self.mint(target, amount, {"from": self.owner()})
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
            token.approve(lending_pool, amount, {"from": target})
            lending_pool.deposit(token, amount, target, 0, {"from": target})
        elif hasattr(self, "mint") and hasattr(self, "owner"):  # renERC20
            self.mint(target, amount, {"from": self.owner()})
        elif hasattr(self, "mint") and hasattr(self, "minter"):  # CurveLpTokenV5
            self.mint(target, amount, {"from": self.minter()})
        else:
            raise ValueError("Unsupported Token")


def _get_coin_object(coin_address, coin_interface, pool_data):
    if chain.id == 1:  # ethereum
        return _MintableTestTokenEthereum(coin_address, pool_data)
    elif chain.id == 10:  # optimism
        return _MintableTestTokenOptimism(coin_address, coin_interface)
    elif chain.id == 137:  # polygon
        return _MintableTestTokenPolygon(coin_address, coin_interface)
    elif chain.id == 42161:  # arbitrum
        return _MintableTestTokenArbitrum(coin_address, coin_interface)


def _wrapped(pool_data, underlying_coins):
    coins = []

    if not pool_data.get("wrapped_contract"):
        return underlying_coins

    for i, coin_data in enumerate(pool_data["coins"]):
        if not coin_data.get("wrapped_address"):
            coins.append(underlying_coins[i])
        else:
            coins.append(_get_coin_object(coin_data.get("wrapped_address"), coin_data.get("wrapped_interface"), pool_data))
    return coins


def _underlying(pool_data):
    coins = []

    for coin_data in pool_data["coins"]:
        if coin_data.get("underlying_address") == ETH_ADDRESS:
            coins.append(ETH_ADDRESS)
        else:
            coins.append(
                _get_coin_object(
                    coin_data.get("underlying_address", coin_data.get("wrapped_address")),
                    coin_data.get("underlying_interface", coin_data.get("wrapped_interface")),
                    pool_data
                )
            )

    return coins


# private fixtures used for setup in other fixtures - do not use in tests!


@pytest.fixture(scope="module")
def _underlying_coins(pool_data):
    return _underlying(pool_data)


@pytest.fixture(scope="module")
def _base_coins(base_pool_data):
    if base_pool_data is None:
        return []
    return _underlying(base_pool_data)
