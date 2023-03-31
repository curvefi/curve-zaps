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
    if network == "arbitrum":
        if pool_data["id"] == "wsteth":
            amt = 10 ** 5
    if network == "optimism":
        if pool_data["id"] == "wsteth":
            amt = 10 ** 4

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
def pool_type(pool_data, is_meta):
    if is_meta:
        return 1
    wrapped_contract = pool_data.get("wrapped_contract", "Plain")
    return {
        "Plain": 0,
        "ATokenMock": 2,
        "cERC20": 3,
        "yERC20": 4,
        "aETH": 5,
        "rETH": 6,
    }.get(wrapped_contract, 0)


@pytest.fixture(scope="module")
def use_lending(n_coins_underlying, n_coins_wrapped, underlying_coins, wrapped_coins):
    use_lending = [False] * 4
    if n_coins_underlying == n_coins_wrapped:
        for i in range(n_coins_wrapped):
            use_lending[i] = underlying_coins[i] != wrapped_coins[i]
    return use_lending


@pytest.fixture(scope="module")
def use_rate(pool_data, use_lending, n_coins_underlying, n_coins_wrapped):
    use_rate = [False] * 4
    if n_coins_underlying == n_coins_wrapped:
        for i in range(n_coins_wrapped):
            use_rate[i] = use_lending[i] or pool_data["coins"][i].get("use_rate", False)
    return use_rate
