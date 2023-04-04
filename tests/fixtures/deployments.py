import pytest
import brownie
INIT_DATA = {
    "ethereum": {
        "use_int128": [
            "0xA2B47E3D5c44877cca798226B7B8118F9BFb7A56",  # compound
            "0x52EA46506B9CC5Ef470C5bf89f17Dc28bB35D85C",  # usdt
            "0x45F783CCE6B7FF23B2ab2D70e416cdb7D6055f51",  # y
            "0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27",  # busd
            "0xA5407eAE9Ba41422680e2e00537571bcC53efBfD",  # susd
            "0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714",  # sbtc
            "0x93054188d876f558f4a66B2EF1d97d16eDf0895B",  # ren
        ],
        "pool_type_addresses": [
            "0x618788357D0EBd8A37e763ADab3bc575D54c2C7d",  # rai

            "0xeb16ae0052ed37f479f7fe63849198df1765a733",  # saave
            "0xDeBF20617708857ebe4F679508E7b7863a8A8EeE",  # aave

            "0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF",  # ib
            "0x52EA46506B9CC5Ef470C5bf89f17Dc28bB35D85C",  # usdt
            "0xA2B47E3D5c44877cca798226B7B8118F9BFb7A56",  # compound

            "0x45F783CCE6B7FF23B2ab2D70e416cdb7D6055f51",  # y
            "0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27",  # busd
            "0x06364f10B501e868329afBc005b3492902d6C763",  # pax

            "0xA96A65c051bF88B4095Ee1f2451C2A9d43F53Ae2",  # ankrETH

            "0xF9440930043eb3997fc70e1339dBb11F341de7A8",  # rETH
        ],
        "pool_types": [
            2,  # rai

            3,  # saave
            3,  # aave

            4,  # ib
            4,  # usdt
            4,  # compound

            6,  # y
            6,  # busd
            6,  # pax

            7,  # ankrETH

            8,  # rETH
        ],
        "use_rate": [
            [True, False, False, False],  # rai

            [False, False, False, False],  # saave
            [False, False, False, False],  # aave

            [True, True, True, False],     # ib
            [True, True, False, False],    # usdt
            [True, True, False, False],    # compound

            [True, True, True, True],      # y
            [True, True, True, True],      # busd
            [True, True, True, False],     # pax

            [False, True, False, False],   # ankrETH

            [False, True, False, False],   # rETH
        ],
    },
    "optimism": {
        "use_int128": [],
        "pool_type_addresses": [
            "0xB90B9B1F91a01Ea22A182CD84C1E22222e39B415",  # wstETH
        ],
        "pool_types": [
            9,  # wstETH
        ],
        "use_rate": [
            [False, True, False, False],   # wstETH
        ],
    },
    "polygon": {
        "use_int128": [],
        "pool_type_addresses": [
            "0x445FE580eF8d70FF569aB36e80c647af338db351",  # aave
        ],
        "pool_types": [
            3,  # aave
        ],
        "use_rate": [
            [False, False, False, False],   # aave
        ],
    },
    "fantom": {
        "use_int128": [],
        "pool_type_addresses": [
            "0x0fa949783947Bf6c1b171DB13AEACBB488845B3f",  # geist

            "0x4FC8D635c3cB1d0aa123859e2B2587d0FF2707b1",  # ib
        ],
        "pool_types": [
            3,  # geist

            5,  # ib
        ],
        "use_rate": [
            [False, False, False, False],  # geist

            [True, True, True, False],     # ib
        ],
    },
    "arbitrum": {
        "use_int128": [],
        "pool_type_addresses": [
            "0x6eB2dc694eB516B16Dc9FBc678C60052BbdD7d80",  # wstETH
        ],
        "pool_types": [
            9,  # wstETH
        ],
        "use_rate": [
            [False, True, False, False],   # wstETH
        ],
    },
    "avalanche": {
        "use_int128": [],
        "pool_type_addresses": [
            "0x7f90122BF0700F9E7e1F688fe926940E8839F353",  # aave
            "0xD2AcAe14ae2ee0f6557aC6C6D0e407a92C36214b",  # aaveV3
        ],
        "pool_types": [
            3,  # aave
            3,  # aaveV3
        ],
        "use_rate": [
            [False, False, False, False],   # aave
            [False, False, False, False],   # aaveV3
        ],
    },
}




@pytest.fixture(scope="module")
def zap(CalcTokenAmountZap, alice, network):
    use_int128 = INIT_DATA[network]["use_int128"]
    pool_type_addresses = INIT_DATA[network]["pool_type_addresses"]
    pool_types = INIT_DATA[network]["pool_types"]
    use_rate = INIT_DATA[network]["use_rate"]

    use_int128 += [brownie.ZERO_ADDRESS] * (20 - len(use_int128))
    pool_type_addresses += [brownie.ZERO_ADDRESS] * (20 - len(pool_type_addresses))
    pool_types += [0] * (20 - len(pool_types))
    use_rate += [[False] * 4] * (20 - len(use_rate))

    return CalcTokenAmountZap.deploy(use_int128, pool_type_addresses, pool_types, use_rate, {'from': alice})
