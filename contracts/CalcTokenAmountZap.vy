# @version 0.3.7

# A "zap" to calc_token amount precisely fo Compound pool
# (c) Curve.Fi, 2023

from vyper.interfaces import ERC20

interface Pool:
    def balances(i: uint256) -> uint256: view
    def coins(i: uint256) -> address: view
    def fee() -> uint256: view
    def offpeg_fee_multiplier() -> uint256: view
    def admin_fee() -> uint256: view
    def A() -> uint256: view
    def get_virtual_price() -> uint256: view

interface LemdingPool:
    def balances(i: int128) -> uint256: view
    def coins(i: int128) -> address: view

interface wstETHPool:
    def oracle() -> address: view

interface Oracle:
    def latestAnswer() -> int256: view

interface cERC20:
    def decimals() -> uint256: view
    def underlying() -> address: view
    def exchangeRateStored() -> uint256: view
    def supplyRatePerBlock() -> uint256: view
    def accrualBlockNumber() -> uint256: view

interface yERC20:
    def decimals() -> uint256: view
    def token() -> address: view
    def getPricePerFullShare() -> uint256: view

interface aETH:
    def ratio() -> uint256: view

interface rETH:
    def getExchangeRate() -> uint256: view


MAX_COINS: constant(uint256) = 4
PRECISION: constant(uint256) = 10 ** 18  # The precision to convert to
FEE_DENOMINATOR: constant(uint256) = 10 ** 10

USE_INT128: public(HashMap[address, bool])
POOL_TYPE: public(HashMap[address, uint8])
USE_RATE: public(HashMap[address, bool[MAX_COINS]])

@external
def __init__(
        _use_int128: address[20],
        _pool_type_addresses: address[20],
        _pool_types: uint8[20],
        _use_rate: bool[MAX_COINS][20],
    ):
    """
    @notice CalcTokenAmountZap constructor
    @param _use_int128 Addresses of pools which take indexes as int128 in coins(i) and balances(i) methods
    """
    for addr in _use_int128:
        if addr == empty(address):
            break
        self.USE_INT128[addr] = True

    for i in range(20):
        if _pool_type_addresses[i] == empty(address):
            break
        self.POOL_TYPE[_pool_type_addresses[i]] = _pool_types[i]
        self.USE_RATE[_pool_type_addresses[i]] = _use_rate[i]

@internal
@view
def get_decimals(coin: address) -> uint256:
    if coin == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        return 18
    else:
        return cERC20(coin).decimals()


@internal
@view
def _rates_plain(coins: address[MAX_COINS], n_coins: uint256) -> uint256[MAX_COINS]:
    result: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    for i in range(MAX_COINS):
        if i >= n_coins:
            break
        result[i] = PRECISION * PRECISION / 10 ** self.get_decimals(coins[i])
    return result


@internal
@view
def _rates_meta(coin1: address, base_pool: address) -> uint256[MAX_COINS]:
    return [PRECISION * PRECISION / 10 ** self.get_decimals(coin1), Pool(base_pool).get_virtual_price(), 0, 0]


@internal
@view
def _rates_compound(coins: address[MAX_COINS], n_coins: uint256, use_rate: bool[MAX_COINS]) -> uint256[MAX_COINS]:
    # exchangeRateStored * (1 + supplyRatePerBlock * (getBlockNumber - accrualBlockNumber) / 1e18)
    result: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    for i in range(MAX_COINS):
        if i >= n_coins:
            break
        rate: uint256 = PRECISION  # Used with no lending
        underlying_coin: address = coins[i]
        if use_rate[i]:
            underlying_coin = cERC20(coins[i]).underlying()
            rate = cERC20(coins[i]).exchangeRateStored()
            supply_rate: uint256 = cERC20(coins[i]).supplyRatePerBlock()
            old_block: uint256 = cERC20(coins[i]).accrualBlockNumber()
            rate += rate * supply_rate * (block.number - old_block) / PRECISION
        result[i] = rate * PRECISION / 10 ** self.get_decimals(underlying_coin)
    return result


@internal
@view
def _rates_y(coins: address[MAX_COINS], n_coins: uint256, use_rate: bool[MAX_COINS]) -> uint256[MAX_COINS]:
    result: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    for i in range(MAX_COINS):  # All 4 coins are wrapped
        if i >= n_coins:
            break
        underlying_coin: address = coins[i]
        rate: uint256 = PRECISION  # Used with no lending
        if use_rate[i]:
            underlying_coin = yERC20(coins[i]).token()
            rate = yERC20(coins[i]).getPricePerFullShare()
        result[i] = rate * PRECISION / 10 ** self.get_decimals(underlying_coin)
    return result


@internal
@view
def _rates_ankr(coins: address[MAX_COINS], n_coins: uint256, use_rate: bool[MAX_COINS]) -> uint256[MAX_COINS]:
    result: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    for i in range(MAX_COINS):
        if i >= n_coins:
            break
        if use_rate[i]:
            result[i] = PRECISION * PRECISION / aETH(coins[i]).ratio()
        else:
            result[i] = PRECISION * PRECISION / 10 ** self.get_decimals(coins[i])

    return result


@internal
@view
def _rates_reth(coins: address[MAX_COINS], n_coins: uint256, use_rate: bool[MAX_COINS]) -> uint256[MAX_COINS]:
    result: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    for i in range(MAX_COINS):
        if i >= n_coins:
            break
        if use_rate[i]:
            result[i] = rETH(coins[i]).getExchangeRate() * PRECISION / 10 ** self.get_decimals(coins[i])
        else:
            result[i] = PRECISION * PRECISION / 10 ** self.get_decimals(coins[i])

    return result

@view
@internal
def _rates_wsteth(pool: address, coins: address[MAX_COINS], n_coins: uint256, use_rate: bool[MAX_COINS]) -> uint256[MAX_COINS]:
    result: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    for i in range(MAX_COINS):
        if i >= n_coins:
            break
        if use_rate[i]:
            oracle: address = wstETHPool(pool).oracle()
            result[i] = convert(Oracle(oracle).latestAnswer(), uint256) * PRECISION / 10 ** self.get_decimals(coins[i])
        else:
            result[i] = PRECISION * PRECISION / 10 ** self.get_decimals(coins[i])

    return result


@internal
@view
def _rates(pool: address, pool_type: uint8, coins: address[MAX_COINS], n_coins: uint256, use_rate: bool[MAX_COINS], base_pool: address) -> uint256[MAX_COINS]:
    if pool_type == 0:
        return self._rates_plain(coins, n_coins)
    elif pool_type == 1:
        return self._rates_meta(coins[0], base_pool)
    elif pool_type == 2:
        return self._rates_plain(coins, n_coins) # aave
    elif pool_type == 3:
        return self._rates_compound(coins, n_coins, use_rate)
    elif pool_type == 4:
        return self._rates_y(coins, n_coins, use_rate)
    elif pool_type == 5:
        return self._rates_ankr(coins, n_coins, use_rate)
    elif pool_type == 6:
        return self._rates_reth(coins, n_coins, use_rate)
    elif pool_type == 7:
        return self._rates_wsteth(pool, coins, n_coins, use_rate)
    else:
        raise "Bad pool type"


@pure
@internal
def _dynamic_fee(xpi: uint256, xpj: uint256, _fee: uint256, _feemul: uint256) -> uint256:
    if _feemul <= FEE_DENOMINATOR:
        return _fee
    else:
        xps2: uint256 = (xpi + xpj)
        xps2 *= xps2  # Doing just ** 2 can overflow apparently
        return (_feemul * _fee) / ((_feemul - FEE_DENOMINATOR) * 4 * xpi * xpj / xps2 + FEE_DENOMINATOR)


@internal
@view
def _fee(pool: address, pool_type: uint8, n_coins: uint256, xpi: uint256, xpj: uint256) -> uint256:
    _fee: uint256 = Pool(pool).fee() * n_coins / (4 * (n_coins - 1))
    if pool_type == 2:  # aave
        _feemul: uint256 = Pool(pool).offpeg_fee_multiplier()
        return self._dynamic_fee(xpi, xpj, _fee, _feemul)
    else:
        return _fee


@internal
@view
def _xp_mem(rates: uint256[MAX_COINS], _balances: uint256[MAX_COINS], n_coins: uint256) -> uint256[MAX_COINS]:
    result: uint256[MAX_COINS] = rates
    for i in range(MAX_COINS):
        if i >= n_coins:
            break
        result[i] = result[i] * _balances[i] / PRECISION
    return result


@internal
@view
def get_D(pool: address, xp: uint256[MAX_COINS], n_coins: uint256) -> uint256:
    S: uint256 = 0
    for _x in xp:
        S += _x
    if S == 0:
        return 0

    Dprev: uint256 = 0
    D: uint256 = S
    Ann: uint256 = Pool(pool).A() * n_coins
    for _i in range(255):
        D_P: uint256 = D
        for i in range(MAX_COINS):
            if i >= n_coins:
                break
            D_P = D_P * D / (xp[i] * n_coins + 1)  # +1 is to prevent /0
        Dprev = D
        D = (Ann * S + D_P * n_coins) * D / ((Ann - 1) * D + (n_coins + 1) * D_P)
        # Equality with the precision of 1
        if D > Dprev:
            if D - Dprev <= 1:
                break
        else:
            if Dprev - D <= 1:
                break
    return D


@internal
@view
def get_D_mem(pool: address, rates: uint256[MAX_COINS], _balances: uint256[MAX_COINS], n_coins: uint256) -> uint256:
    return self.get_D(pool, self._xp_mem(rates, _balances, n_coins), n_coins)


@internal
@view
def _calc_token_amount(
        pool: address,
        token: address,
        amounts: uint256[MAX_COINS],
        n_coins: uint256,
        pool_type: uint8,
        use_rate: bool[MAX_COINS],
        base_pool: address,
        deposit: bool,
) -> uint256:
    """
    Method to calculate addition or reduction in token supply at
    deposit or withdrawal TAKING FEES INTO ACCOUNT.
    """
    coins: address[MAX_COINS] = empty(address[MAX_COINS])
    old_balances: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    for i in range(MAX_COINS):
        if i >= n_coins:
            break
        if self.USE_INT128[pool]:
            coins[i] = LemdingPool(pool).coins(convert(i, int128))
            old_balances[i] = LemdingPool(pool).balances(convert(i, int128))
        else:
            coins[i] = Pool(pool).coins(i)
            old_balances[i] = Pool(pool).balances(i)
    new_balances: uint256[MAX_COINS] = old_balances
    token_supply: uint256 = ERC20(token).totalSupply()
    fees: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    rates: uint256[MAX_COINS] = self._rates(pool, pool_type, coins, n_coins, use_rate, base_pool)
    D0: uint256 = self.get_D_mem(pool, rates, old_balances, n_coins)

    for i in range(MAX_COINS):
        if i >= n_coins:
            break
        if deposit:
            new_balances[i] += amounts[i]
        else:
            new_balances[i] -= amounts[i]
    D1: uint256 = self.get_D_mem(pool, rates, new_balances, n_coins)

    # We need to recalculate the invariant accounting for fees
    # to calculate fair user's share
    D2: uint256 = D1
    if token_supply > 0:
        # Only account for fees if we are not the first to deposit
        ys: uint256 = (D0 + D1) / n_coins  # only for aave
        for i in range(MAX_COINS):
            if i >= n_coins:
                break
            ideal_balance: uint256 = D1 * old_balances[i] / D0
            difference: uint256 = 0
            if ideal_balance > new_balances[i]:
                difference = ideal_balance - new_balances[i]
            else:
                difference = new_balances[i] - ideal_balance
            xs: uint256 = old_balances[i] + new_balances[i]  # only for aave
            fees[i] = self._fee(pool, pool_type, n_coins, ys, xs) * difference / FEE_DENOMINATOR
            new_balances[i] -= fees[i]
        D2 = self.get_D_mem(pool, rates, new_balances, n_coins)

    # Calculate, how much pool tokens to mint
    if token_supply == 0:
        return D1  # Take the dust if there was any
    else:
        diff: uint256 = 0
        if deposit:
            diff = D2 - D0
        else:
            diff = D0 - D2
        return token_supply * diff / D0


@external
@view
def calc_token_amount(
        pool: address,
        token: address,
        amounts: uint256[MAX_COINS],
        n_coins: uint256,
        deposit: bool,
) -> uint256:
    return self._calc_token_amount(pool, token, amounts, n_coins, self.POOL_TYPE[pool], self.USE_RATE[pool], empty(address), deposit)


@external
@view
def calc_token_amount_meta(
        pool: address,
        token: address,
        amounts: uint256[MAX_COINS],
        n_coins: uint256,
        base_pool: address,
        base_token: address,
        deposit: bool,
        use_underlying: bool,
) -> uint256:
    if not use_underlying:
        return self._calc_token_amount(pool, token, amounts, n_coins, 1, [False, False, False, False], base_pool, deposit)

    meta_amounts: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    base_amounts: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    meta_amounts[0] = amounts[0]
    for i in range(MAX_COINS - 1):
        base_amounts[i] = amounts[i + 1]
    _base_tokens: uint256 = self._calc_token_amount(base_pool, base_token, base_amounts, n_coins - 1, 0, [False, False, False, False], empty(address), deposit)
    meta_amounts[1] = _base_tokens

    return self._calc_token_amount(pool, token, meta_amounts, 2, 1, [False, False, False, False], base_pool, deposit)
