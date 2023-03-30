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
            2,  # saave
            2,  # aave

            3,  # ib
            3,  # usdt
            3,  # compound

            4,  # y
            4,  # busd
            4,  # pax

            5,  # ankrETH

            6,  # rETH
        ],
        "use_rate": [
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
    "arbitrum": {
        "use_int128": [],
        "pool_type_addresses": [
            "0x6eB2dc694eB516B16Dc9FBc678C60052BbdD7d80",  # wstETH
        ],
        "pool_types": [
            7,  # wstETH
        ],
        "use_rate": [
            [False, True, False, False],   # wstETH
        ],
    }
}


@pytest.fixture(scope="module")
def zap(CalcTokenAmountZap, alice, networks):
    use_int128 = INIT_DATA[networks[brownie.chain.id]]["use_int128"]
    pool_type_addresses = INIT_DATA[networks[brownie.chain.id]]["pool_type_addresses"]
    pool_types = INIT_DATA[networks[brownie.chain.id]]["pool_types"]
    use_rate = INIT_DATA[networks[brownie.chain.id]]["use_rate"]

    use_int128 += [brownie.ZERO_ADDRESS] * (20 - len(use_int128))
    pool_type_addresses += [brownie.ZERO_ADDRESS] * (20 - len(pool_type_addresses))
    pool_types += [0] * (20 - len(pool_types))
    use_rate += [[False] * 4] * (20 - len(use_rate))

    return CalcTokenAmountZap.deploy(use_int128, pool_type_addresses, pool_types, use_rate, {'from': alice})
