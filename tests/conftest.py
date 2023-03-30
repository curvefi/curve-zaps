#!/usr/bin/python3
import json
import pytest
from brownie import chain
from brownie.project.main import get_loaded_projects


POOLS = ['3pool', 'aave', 'aeth', 'bbtc', 'busd', 'compound', 'dusd', 'gusd', 'hbtc', 'husd', 'ib', 'link', 'musd', 'obtc',
         'pax', 'pbtc', 'ren', 'reth', 'rsv', 'saave', 'sbtc', 'seth', 'steth', 'susd', 'tbtc', 'usdk', 'usdn', 'usdp', 'usdt',
         'ust', 'y', 'eurt', 'tusd']
LENDING_POOLS = ['compound', 'usdt', 'y', 'busd', 'pax', 'aave', 'saave', 'ib']
META_POOLS = ['gusd', 'husd', 'usdk', 'usdn', 'musd', 'rsv', 'tbtc', 'dusd', 'pbtc', 'bbtc', 'obtc', 'ust', 'usdp']
FACTORY_POOOLS = ['tusd']  # 'frax', 'lusd', 'busdv2', 'alusd', 'mim'

pytest_plugins = [
    "fixtures.accounts",
    "fixtures.coins",
    "fixtures.deployments",
    "fixtures.pooldata",
    "fixtures.setup",
]

_NETWORKS = {
    1: "ethereum",
    42161: "arbitrum",
}

_POOLDATA = {
    "ethereum": {},
    "arbitrum": {},
}

_POOLS = {
    "ethereum": POOLS + LENDING_POOLS + META_POOLS + FACTORY_POOOLS,
    "arbitrum": ["wsteth"],
}

_WETH = {
    "ethereum": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "arbitrum": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1",
}


def pytest_addoption(parser):
    parser.addoption("--pools", help="comma-separated list of pools to target")
    parser.addoption("--chain_id", help="chain id")


def pytest_sessionstart():
    # load `pooldata.json` for each pool
    project = get_loaded_projects()[0]

    for network in ["ethereum", "arbitrum"]:
        for path in [i for i in project._path.glob(f"contracts/{network}/*") if i.is_dir()]:
            with path.joinpath("pooldata.json").open() as fp:
                _POOLDATA[network][path.name] = json.load(fp)
                _POOLDATA[network][path.name].update(name=path.name)

        for _, data in _POOLDATA[network].items():
            if "base_pool" in data:
                data["base_pool"] = _POOLDATA[network][data["base_pool"]]


def pytest_generate_tests(metafunc):
    try:
        params = metafunc.config.getoption("pools").split(",")
    except Exception:
        raise ValueError(f"No --pool key")

    metafunc.parametrize("pool_data", params, indirect=True, scope="session")


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


def get_pools_by_types():
    for pool_id in _POOLDATA[_NETWORKS[chain.id]]:
        _pool_data = _POOLDATA[_NETWORKS[chain.id]][pool_id]
        pool_type = {
            "Plain": 0,
            "ATokenMock": 2,
            "cERC20": 3,
            "yERC20": 4,
            "aETH": 5,
            "rETH": 6,
        }.get(_pool_data.get("wrapped_contract", "Plain"), -1)
        if pool_type == 6:
            print(pool_id)
            print(_pool_data["swap_address"])
            use_rate = [False] * 4
            for i in range(len(_pool_data["coins"])):
                use_lending = "wrapped_address" in _pool_data["coins"][i] and \
                              "underlying_address" in _pool_data["coins"][i] and \
                              _pool_data["coins"][i]["wrapped_address"] != _pool_data["coins"][i]["underlying_address"]
                use_rate[i] = use_lending or _pool_data["coins"][i].get("use_rate", False)
            print(use_rate)
            print("\n")
    raise Exception("Success")


@pytest.fixture(scope="module")
def pool_data(request):
    _POOLDATA[_NETWORKS[chain.id]][request.param]["id"] = request.param
    return _POOLDATA[_NETWORKS[chain.id]][request.param]


@pytest.fixture(scope="module")
def base_pool_data(pool_data):
    return pool_data.get("base_pool", None)


@pytest.fixture(scope="module")
def networks():
    return _NETWORKS


@pytest.fixture(scope="module")
def weth():
    return _WETH
