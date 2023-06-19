#!/usr/bin/python3
import json
import pytest
from brownie import chain
from brownie.project.main import get_loaded_projects

# 3pool,hbtc,link,sbtc2,seth,steth,susd,eurs,eurt,fraxusdc + aeth,reth
PLAIN_POOLS = ['3pool', 'aeth', 'hbtc', 'link', 'reth', 'sbtc2', 'seth', 'steth', 'susd', 'eurs', 'eurt', 'fraxusdc'] + ['aeth', 'reth', 'wbeth']
# aave,saave,ib,usdt,compound,y,busd,pax
LENDING_POOLS = ['aave', 'saave'] + ['ib', 'usdt', 'compound'] + ['y', 'busd', 'pax']
# gusd,husd,usdk,musd,rsv,dusd,usdp + rai
META_POOLS = ['gusd', 'husd', 'usdk', 'musd', 'rsv', 'dusd', 'usdp'] + ['rai']

# factory-v2-283,factory-v2-66,factory-v2-235 + factory-v2-303
FACTORY_PLAIN_POOLS = ['factory-v2-283', 'factory-v2-66', 'factory-v2-235'] + ['factory-v2-303']
# cvxCrv/Crv (2 coins), 3EURpool (3 coins), CRV booster (4 coins) + stETH-ng (pool_type 10)

# tusd + factory-v2-9,factory-v2-144,factory-v2-247
FACTORY_META_POOLS = ['tusd'] + ['factory-v2-9', 'factory-v2-144', 'factory-v2-247']
# OUSD/3Crv, TUSD/FRAXBP, tBTC/sbtc2Crv

pytest_plugins = [
    "fixtures.accounts",
    "fixtures.coins",
    "fixtures.deployments",
    "fixtures.pooldata",
    "fixtures.setup",
]

_NETWORKS = {
    1: "ethereum",
    10: "optimism",
    100: "xdai",
    137: "polygon",
    250: "fantom",
    42161: "arbitrum",
    43114: "avalanche",
}

_POOLDATA = {}

_POOLS = {
    "ethereum": PLAIN_POOLS + LENDING_POOLS + META_POOLS + FACTORY_PLAIN_POOLS + FACTORY_META_POOLS,
    "optimism": ["3pool", "wsteth"],
    "xdai": ["3pool", "rai"],
    "polygon": ["aave", "factory-v2-107", "factory-v2-339"],
    "fantom": ["2pool", "fusdt", "ib", "geist"],
    "arbitrum": ["2pool", "wsteth"],
    "avalanche": ["aave", "aaveV3", "factory-v2-66"],
}

_WETH = {
    "ethereum": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "optimism": "0x4200000000000000000000000000000000000006",
    "xdai": "0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d",
    "polygon": "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",
    "fantom": "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83",
    "arbitrum": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1",
    "avalanche": "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",
}


def pytest_addoption(parser):
    parser.addoption("--pools", help="comma-separated list of pools to target")


def pytest_sessionstart():
    # load `pooldata.json` for each pool
    project = get_loaded_projects()[0]

    for network in _POOLS.keys():
        _POOLDATA[network] = {}
        for path in [i for i in project._path.glob(f"contracts/{network}/*") if i.is_dir()]:
            with path.joinpath("pooldata.json").open() as fp:
                _POOLDATA[network][path.name] = json.load(fp)
                _POOLDATA[network][path.name].update(id=path.name)

        for _, data in _POOLDATA[network].items():
            if "base_pool" in data:
                data["base_pool"] = _POOLDATA[network][data["base_pool"]]


def pytest_generate_tests(metafunc):
    network = metafunc.config.getoption("network")[0].split("-")[0]
    if network == "mainnet":
        network = "ethereum"
    try:
        params = metafunc.config.getoption("pools").split(",")
    except Exception:
        params = _POOLS[network]

    for pool in params:
        if pool not in _POOLS[network]:
            raise ValueError(f"Invalid pool id: {pool}")

    metafunc.parametrize("pool_data", params, indirect=True, scope="session")


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


@pytest.fixture(scope="module")
def pool_data(request):
    return _POOLDATA[_NETWORKS[chain.id]][request.param]


@pytest.fixture(scope="module")
def base_pool_data(pool_data):
    return pool_data.get("base_pool", None)


@pytest.fixture(scope="module")
def network():
    return _NETWORKS[chain.id]


@pytest.fixture(scope="module")
def weth():
    return _WETH
