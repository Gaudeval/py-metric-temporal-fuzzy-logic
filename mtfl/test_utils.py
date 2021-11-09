import mtfl
from mtfl import utils
from mtfl import sugar
from mtfl.hypothesis import MetricTemporalLogicStrategy

from hypothesis import given

CONTEXT = {
    'ap1': mtfl.parse('x'),
    'ap2': mtfl.parse('(y U z)'),
    'ap3': mtfl.parse('x'),
    'ap4': mtfl.parse('(x -> y -> z)'),
    'ap5': mtfl.parse('(ap1 <-> y <-> z)'),
}
APS = set(CONTEXT.keys())


def test_inline_context_rigid():
    phi = mtfl.parse('G ap1')
    assert phi[CONTEXT] == mtfl.parse('G x')

    phi = mtfl.parse('G ap5')
    assert phi[CONTEXT] == mtfl.parse('G(x <-> y <-> z)')


@given(MetricTemporalLogicStrategy)
def test_inline_context(phi):
    assert not (APS & phi[CONTEXT].atomic_predicates)


@given(MetricTemporalLogicStrategy, MetricTemporalLogicStrategy)
def test_timed_until_smoke_test(phi1, phi2):
    sugar.timed_until(phi1, phi2, lo=2, hi=20)


def test_discretize():
    dt = 0.3

    phi = mtfl.parse('@ ap1')
    assert utils.is_discretizable(phi, dt)
    phi2 = utils.discretize(phi, dt)
    phi3 = utils.discretize(phi2, dt)
    assert phi2 == phi3

    phi = mtfl.parse('G[0.3, 1.2] F[0.6, 1.5] ap1')
    assert utils.is_discretizable(phi, dt)
    phi2 = utils.discretize(phi, dt)
    phi3 = utils.discretize(phi2, dt)
    assert phi2 == phi3

    phi = mtfl.parse('G[0.3, 1.4] F[0.6, 1.5] ap1')
    assert not utils.is_discretizable(phi, dt)

    phi = mtfl.parse('G[0.3, 1.2] F ap1')
    assert not utils.is_discretizable(phi, dt)

    phi = mtfl.parse('G[0.3, 1.2] (ap1 U ap2)')
    assert not utils.is_discretizable(phi, dt)

    phi = mtfl.parse('G[0.3, 0.6] ~F[0, 0.3] a')
    assert utils.is_discretizable(phi, dt)
    phi2 = utils.discretize(phi, dt, distribute=True)
    phi3 = utils.discretize(phi2, dt, distribute=True)
    assert phi2 == phi3

    phi = mtfl.TOP
    assert utils.is_discretizable(phi, dt)
    phi2 = utils.discretize(phi, dt)
    phi3 = utils.discretize(phi2, dt)
    assert phi2 == phi3

    phi = mtfl.BOT
    assert utils.is_discretizable(phi, dt)
    phi2 = utils.discretize(phi, dt)
    phi3 = utils.discretize(phi2, dt)
    assert phi2 == phi3


def test_scope():
    dt = 0.3

    phi = mtfl.parse('@ap1')
    assert utils.scope(phi, dt) == 0.3

    phi = mtfl.parse('(@@ap1 | ap2)')
    assert utils.scope(phi, dt) == 0.6

    phi = mtfl.parse('G[0.3, 1.2] F[0.6, 1.5] ap1')
    assert utils.scope(phi, dt) == 1.2 + 1.5

    phi = mtfl.parse('G[0.3, 1.2] F ap1')
    assert utils.scope(phi, dt) == float('inf')

    phi = mtfl.parse('G[0.3, 1.2] (ap1 U ap2)')
    assert utils.scope(phi, dt) == float('inf')
