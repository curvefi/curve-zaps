import pytest


@pytest.fixture(scope="module")
def swap_address(pool_data):
    return pool_data['swap_address']


@pytest.fixture(scope="module")
def deposit_address(pool_data):
    return pool_data['zap_address'] if 'zap_address' in pool_data else pool_data['swap_address']


@pytest.fixture(scope="module")
def underlying_decimals(pool_data, base_pool_data):
    # number of decimal places for each underlying coin in the active pool
    decimals = [i.get("decimals", i.get("wrapped_decimals")) for i in pool_data["coins"]]

    if base_pool_data is None:
        return decimals
    base_decimals = [i.get("decimals", i.get("wrapped_decimals")) for i in base_pool_data["coins"]]
    return decimals[:-1] + base_decimals


@pytest.fixture(scope="module")
def wrapped_decimals(pool_data):
    # number of decimal places for each wrapped coin in the active pool
    yield [i.get("wrapped_decimals", i.get("decimals")) for i in pool_data["coins"]]


@pytest.fixture(scope="module")
def wrapped_amounts_to_mint(pool_data, wrapped_decimals, network):
    amt = 10 ** 6
    if network == "ethereum":
        if pool_data["id"] in ["busd", "dusd"]:
            amt = 10 ** 5
        if pool_data["id"] in ["sbtc", "ren"]:
            amt = 10 ** 2
        if pool_data["id"] == "aeth":
            amt = 10 ** 2
        if "btc" in pool_data["id"] or pool_data["id"] == "factory-v2-247":
            amt = 10
        if pool_data["id"] == "factory-v2-235":  # Just because it's a very small pool
            amt = 50
    if network == "optimism":
        if pool_data["id"] == "wsteth":
            amt = 10 ** 4
    if network == "xdai":
        if pool_data["id"] == "rai":  # Just because it's a very small pool
            amt = 1000
    if network == "arbitrum":
        if pool_data["id"] == "wsteth":
            amt = 10 ** 5
    if network == "avalanche":
        if pool_data["id"] == "aaveV3":  # Just because it's a very small pool
            amt = 100

    return [amt * 10 ** d for d in wrapped_decimals]


@pytest.fixture(scope="module")
def underlying_amounts_to_mint(pool_data, underlying_decimals):
    amt = 10 ** 6
    if pool_data["id"] == "aeth":
        amt = 10 ** 2
    return [amt * 10 ** d for d in underlying_decimals]


@pytest.fixture(scope="module")
def n_coins_wrapped(wrapped_decimals):
    return len(wrapped_decimals)


@pytest.fixture(scope="module")
def n_coins_underlying(underlying_decimals):
    yield len(underlying_decimals)


@pytest.fixture(scope="module")
def is_meta(pool_data):
    return "meta" in pool_data.get("pool_types", [])


@pytest.fixture(scope="module")
def is_factory(pool_data):
    return "factory" in pool_data.get("pool_types", [])


@pytest.fixture(scope="module")
def use_lending(n_coins_underlying, n_coins_wrapped, underlying_coins, wrapped_coins, max_coins):
    use_lending = [False] * max_coins
    if n_coins_underlying == n_coins_wrapped:
        for i in range(n_coins_wrapped):
            use_lending[i] = underlying_coins[i] != wrapped_coins[i]
    return use_lending


@pytest.fixture(scope="module")
def use_rate(pool_data, use_lending, n_coins_underlying, n_coins_wrapped, max_coins):
    use_rate = [False] * max_coins
    if pool_data["id"] == "rai":
        return [True] + [False] * (max_coins - 1)
    if n_coins_underlying == n_coins_wrapped:
        for i in range(n_coins_wrapped):
            use_rate[i] = use_lending[i] or pool_data["coins"][i].get("use_rate", False)
    return use_rate
