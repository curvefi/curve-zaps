# @version 0.3.7

# A "zap" for crypto pools to get_dx
# (c) Curve.Fi, 2023

interface ERC20:
    def decimals() -> uint256: view

interface Curve:
    def A() -> uint256: view
    def gamma() -> uint256: view
    def price_scale(i: uint256) -> uint256: view
    def coins(i: uint256) -> address: view
    def balances(i: uint256) -> uint256: view
    def D() -> uint256: view
    def fee_calc(xp: uint256[3]) -> uint256: view
    def future_A_gamma_time() -> uint256: view

interface Curve2:
    def price_scale() -> uint256: view

interface Math3:
    def newton_D(ANN: uint256, gamma: uint256, x_unsorted: uint256[3]) -> uint256: view
    def newton_y(ANN: uint256, gamma: uint256, x: uint256[3], D: uint256, i: uint256) -> uint256: view

interface Math2:
    def newton_D(ANN: uint256, gamma: uint256, x_unsorted: uint256[2]) -> uint256: view
    def newton_y(ANN: uint256, gamma: uint256, x: uint256[2], D: uint256, i: uint256) -> uint256: view
    def fee_calc(pool: address, xp: uint256[2]) -> uint256: view

interface StablePool:
    def calc_withdraw_one_coin(_token_amount: uint256, i: int128) -> uint256: view

interface StableCalcZap:
    def calc_token_amount(pool: address, token: address, amounts: uint256[MAX_COINS], n_coins: uint256, deposit: bool, use_underlying: bool) -> uint256: view
    def get_dx_underlying(pool: address, i: int128, j: int128, dy: uint256, n_coins: uint256) -> uint256: view


STABLE_CALC_ZAP: constant(address) = 0x0fE38dCC905eC14F6099a83Ac5C93BF2601300CF
MAX_COINS: constant(uint256) = 10
PRECISION: constant(uint256) = 10**18  # The precision to convert to
math2: immutable(address)
math3: immutable(address)


@external
def __init__(_math2: address, _math3: address):
    math2 = _math2
    math3 = _math3


@internal
@view
def _get_dx_2_coins(
        pool: address,
        i: uint256,
        j: uint256,
        dy: uint256,
        xp: DynArray[uint256, MAX_COINS],
        precisions: DynArray[uint256, MAX_COINS],
        price_scale: DynArray[uint256, MAX_COINS],
) -> uint256:
    A: uint256 = Curve(pool).A()
    gamma: uint256 = Curve(pool).gamma()
    D: uint256 = Curve(pool).D()
    _xp: uint256[2] = [xp[0], xp[1]]
    if Curve(pool).future_A_gamma_time() > 0:
        _xp[0] *= precisions[0]
        _xp[1] = _xp[1] * price_scale[0] * precisions[1] / PRECISION
        D = Math2(math2).newton_D(A, gamma, _xp)

    # Calc new balances without fees

    _xp = [xp[0], xp[1]]
    _xp[j] -= dy
    _xp[0] *= precisions[0]
    _xp[1] = _xp[1] * price_scale[0] * precisions[1] / PRECISION
    x: uint256 = Math2(math2).newton_y(A, gamma, _xp, D, i)
    _xp[i] = x

    # Now we can calc fees with better precision

    _dy: uint256 = dy - Math2(math2).fee_calc(pool, _xp) * dy / 10**10
    _xp = [xp[0], xp[1]]
    _xp[j] -= dy
    _xp[0] *= precisions[0]
    _xp[1] = _xp[1] * price_scale[0] * precisions[1] / PRECISION
    x = Math2(math2).newton_y(A, gamma, _xp, D, i)
    dx: uint256 = x - _xp[i] + 1
    if i > 0:
        dx = dx * PRECISION / price_scale[i - 1]
    dx /= precisions[i]

    return dx


@internal
@view
def _get_dx_3_coins(
        pool: address,
        i: uint256,
        j: uint256,
        dy: uint256,
        xp: DynArray[uint256, MAX_COINS],
        precisions: DynArray[uint256, MAX_COINS],
        price_scale: DynArray[uint256, MAX_COINS],
) -> uint256:
    A: uint256 = Curve(pool).A()
    gamma: uint256 = Curve(pool).gamma()
    D: uint256 = Curve(pool).D()
    _xp: uint256[3] = [xp[0], xp[1], xp[2]]
    if Curve(pool).future_A_gamma_time() > 0:
        _xp[0] *= precisions[0]
        _xp[1] = _xp[1] * price_scale[0] * precisions[1] / PRECISION
        _xp[2] = _xp[2] * price_scale[1] * precisions[2] / PRECISION
        D = Math3(math3).newton_D(A, gamma, _xp)

    # Calc new balances without fees

    _xp = [xp[0], xp[1], xp[2]]
    _xp[j] -= dy
    _xp[0] *= precisions[0]
    _xp[1] = _xp[1] * price_scale[0] * precisions[1] / PRECISION
    _xp[2] = _xp[2] * price_scale[1] * precisions[2] / PRECISION
    x: uint256 = Math3(math3).newton_y(A, gamma, _xp, D, i)
    _xp[i] = x

    # Now we can calc fees with better precision

    _dy: uint256 = dy - Curve(pool).fee_calc(_xp) * dy / 10**10
    _xp = [xp[0], xp[1], xp[2]]
    _xp[j] -= dy
    _xp[0] *= precisions[0]
    _xp[1] = _xp[1] * price_scale[0] * precisions[1] / PRECISION
    _xp[2] = _xp[2] * price_scale[1] * precisions[2] / PRECISION
    x = Math3(math3).newton_y(A, gamma, _xp, D, i)
    dx: uint256 = x - _xp[i] + 1
    if i > 0:
        dx = dx * PRECISION / price_scale[i - 1]
    dx /= precisions[i]

    return dx


@internal
@view
def _get_dx(pool: address, i: uint256, j: uint256, dy: uint256, n_coins: uint256) -> uint256:
    assert i != j and i < MAX_COINS and j < MAX_COINS, "coin index out of range"
    assert dy > 0, "do not exchange 0 coins"

    precisions: DynArray[uint256, MAX_COINS] = []
    for k in range(MAX_COINS):
        if k == n_coins:
            break
        coin: address = Curve(pool).coins(k)
        precisions.append(10**(18 - ERC20(coin).decimals()))

    price_scale: DynArray[uint256, MAX_COINS] = []
    for k in range(MAX_COINS):
        if k == n_coins - 1:
            break
        if n_coins == 2:
            price_scale.append(Curve2(pool).price_scale())
            break
        price_scale.append(Curve(pool).price_scale(k))
    xp: DynArray[uint256, MAX_COINS] = []
    for k in range(MAX_COINS):
        if k == n_coins:
            break
        xp.append(Curve(pool).balances(k))

    if n_coins == 3:
        return self._get_dx_3_coins(pool, i, j, dy, xp, precisions, price_scale)
    else:
        return self._get_dx_2_coins(pool, i, j, dy, xp, precisions, price_scale)


@external
@view
def get_dx(pool: address, i: uint256, j: uint256, dy: uint256, n_coins: uint256) -> uint256:
    return self._get_dx(pool, i, j, dy, n_coins)


@external
@view
def get_dx_meta_underlying(pool: address, i: uint256, j: uint256, dy: uint256, n_coins: uint256, base_pool: address, base_token: address) -> uint256:
    if i > 0 and j > 0:  # meta_coin1 -> meta_coin2
        return StableCalcZap(STABLE_CALC_ZAP).get_dx_underlying(base_pool, convert(i - 1, int128), convert(j - 1, int128), dy, n_coins - 1)
    elif i == 0:  # coin -> meta_coin
        # coin -(swap)-> LP -(remove)-> meta_coin (dy - meta_coin)
        # 1. lp_amount = calc_token_amount([..., dy, ...], deposit=False)
        # 2. dx = get_dx(0, 1, lp_amount)
        base_amounts: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
        base_amounts[j - 1] = dy
        lp_amount: uint256 = StableCalcZap(STABLE_CALC_ZAP).calc_token_amount(base_pool, base_token, base_amounts, n_coins - 1, False, True)
        return self._get_dx(pool, 0, 1, lp_amount, 2)
    else:  # j == 0, meta_coin -> coin
        # meta_coin -(add)-> LP -(swap)-> coin (dy - coin)
        # 1. lp_amount = get_dx(1, 0, dy)
        # 2. dx = calc_withdraw_one_coin(lp_amount, i - 1)
        lp_amount: uint256 = self._get_dx(pool, 1, 0, dy, 2)
        return StablePool(base_pool).calc_withdraw_one_coin(lp_amount, convert(i - 1, int128))
