# Curve Zaps

- StableCalcZap (precise calc_token_amount + get_dx)
  - Ethereum: [0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF](https://etherscan.io/address/0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF#code)
  - Optimism: [0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF](https://optimistic.etherscan.io/address/0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF#code)
  - Gnosis (xDai): [0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF](https://gnosisscan.io/address/0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF#code)
  - Polygon: [0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF](https://polygonscan.com/address/0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF#code)
  - Fantom: [0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF](https://ftmscan.com/address/0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF#code)
  - Moonbeam: [0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF](https://moonscan.io/address/0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF#code)
  - Kava: [0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF](https://explorer.kava.io/address/0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF/contracts)
  - Arbitrum: [0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF](https://arbiscan.io/address/0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF#code)
  - Celo: [0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF](https://celoscan.io/address/0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF#code)
  - Avalanche: [0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF](https://snowtrace.io/address/0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF#code)
  - Aurora: [0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF](https://explorer.aurora.dev/address/0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF/contracts)

## Testing and Development

### Dependencies

- [python3](https://www.python.org/downloads/release/python-368/) version 3.10 or greater, python3-dev
- [vyper](https://github.com/vyperlang/vyper) version [0.3.7](https://github.com/vyperlang/vyper/releases/tag/v0.3.7)
- [brownie](https://github.com/iamdefinitelyahuman/brownie) - tested with version [1.19.2](https://github.com/eth-brownie/brownie/releases/tag/v1.19.2)
- [brownie-token-tester](https://github.com/iamdefinitelyahuman/brownie-token-tester) - tested with version [0.3.2](https://github.com/iamdefinitelyahuman/brownie-token-tester/releases/tag/v0.3.2)
- [ganache-cli](https://github.com/trufflesuite/ganache-cli) - tested with version [6.12.2](https://github.com/trufflesuite/ganache-cli/releases/tag/v6.12.2)

### Setup

To get started, first create and initialize a Python [virtual environment](https://docs.python.org/3/library/venv.html). Next, clone the repo and install the developer dependencies:

```bash
git clone https://github.com/curvefi/curve-zaps.git
cd curve-zaps
pip install -r requirements.txt
```

### Running the Tests

#### To run the entire suite:

```bash
brownie test --network <network_name>-fork

# network_name: mainnet (ethereum), optimism, xdai, polygon, fantom, arbitrum, avalanche
```

#### To run for particular pools:

```bash
brownie test --pools 3pool,compound,aave --network mainnet-fork
```

#### The list of available pools:

**mainnet (ethereum)**
```bash
PLAIN: 3pool,hbtc,link,sbtc2,seth,steth,susd,eurs,eurt,fraxusdc + aeth,reth (use rate)
LENDING: aave,saave,ib,usdt,compound
META: gusd,usdk,musd,rsv,dusd,usdp + rai (use rate)
FACTORY PLAIN: factory-v2-283,factory-v2-66,factory-v2-235 + factory-v2-303 (pool_type 10)
FACTORY META: tusd + factory-v2-9,factory-v2-144,factory-v2-247
```

**optimism**
```bash
PLAIN: 3pool + wsteth (uses rate)
```

**xdai**
```bash
PLAIN: 3pool
META: rai (uses rate)
```

**polygon**
```bash
LENDING: aave
FACTORY META: factory-v2-107,factory-v2-339
```

**fantom**
```bash
PLAIN: 2pool
META: fusdt
LENDING: ib,geist
```

**arbitrum**
```bash
PLAIN: 2pool + wsteth (uses rate)
```

**avalanche**
```bash
LENDING: aave,aaveV3
FACTORY META: factory-v2-66
```

### Deploy
```bash
brownie run deploy --network <id>
```

## License

This project is licensed under the [MIT license](LICENSE).
