# @version 0.3.7

# A "zap" for crypto pools to get_dx
# (c) Curve.Fi, 2023

interface Curve:
    def A() -> uint256: view
    def gamma() -> uint256: view
    def price_scale(i: uint256) -> uint256: view
    def balances(i: uint256) -> uint256: view
    def D() -> uint256: view
    def fee_calc(xp: uint256[N_COINS]) -> uint256: view
    def future_A_gamma_time() -> uint256: view

interface Math:
    def newton_D(ANN: uint256, gamma: uint256, x_unsorted: uint256[N_COINS]) -> uint256: view
    def newton_y(ANN: uint256, gamma: uint256, x: uint256[N_COINS], D: uint256, i: uint256) -> uint256: view

N_COINS: constant(uint256) = 3  # <- change
PRECISION: constant(uint256) = 10 ** 18  # The precision to convert to
PRECISIONS: constant(uint256[N_COINS]) = [
    1000000000000,
    10000000000,
    1,
]
math: constant(address) = 0x8F68f4810CcE3194B6cB6F3d50fa58c2c9bDD1d5
views: constant(address) = 0x40745803C2faA8E8402E2Ae935933D07cA8f355c


@external
@view
def get_dx(pool: address, i: uint256, j: uint256, dy: uint256) -> uint256:
    assert i != j and i < N_COINS and j < N_COINS, "coin index out of range"
    assert dy > 0, "do not exchange 0 coins"

    precisions: uint256[N_COINS] = PRECISIONS

    price_scale: uint256[N_COINS-1] = empty(uint256[N_COINS-1])
    for k in range(N_COINS-1):
        price_scale[k] = Curve(pool).price_scale(k)
    xp: uint256[N_COINS] = empty(uint256[N_COINS])
    for k in range(N_COINS):
        xp[k] = Curve(pool).balances(k)

    A: uint256 = Curve(pool).A()
    gamma: uint256 = Curve(pool).gamma()
    D: uint256 = Curve(pool).D()
    _xp: uint256[N_COINS] = xp
    if Curve(pool).future_A_gamma_time() > 0:
        _xp[0] *= precisions[0]
        for k in range(N_COINS-1):
            _xp[k+1] = _xp[k+1] * price_scale[k] * precisions[k+1] / PRECISION
        D = Math(math).newton_D(A, gamma, _xp)

    # Calc new balances without fees

    _xp = xp
    _xp[j] -= dy
    _xp[0] *= precisions[0]
    for k in range(N_COINS-1):
        _xp[k+1] = _xp[k+1] * price_scale[k] * precisions[k+1] / PRECISION

    x: uint256 = Math(math).newton_y(A, gamma, _xp, D, i)
    _xp[i] = x

    # Now we can calc fees with better precision

    _dy: uint256 = dy - Curve(pool).fee_calc(_xp) * dy / 10**10
    xp[j] -= dy
    xp[0] *= precisions[0]
    for k in range(N_COINS - 1):
        xp[k + 1] = xp[k + 1] * price_scale[k] * precisions[k + 1] / PRECISION

    x = Math(math).newton_y(A, gamma, xp, D, i)
    dx: uint256 = x - xp[i] + 1
    if i > 0:
        dx = dx * PRECISION / price_scale[i-1]
    dx /= precisions[i]

    return dx
