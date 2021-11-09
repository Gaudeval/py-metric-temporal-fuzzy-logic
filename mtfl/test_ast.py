import mtfl
from mtfl.hypothesis import MetricTemporalLogicStrategy

from hypothesis import given


@given(MetricTemporalLogicStrategy)
def test_identities(phi):
    assert mtfl.TOP == mtfl.TOP | phi
    assert mtfl.BOT == mtfl.BOT & phi
    assert mtfl.TOP == phi | mtfl.TOP
    assert mtfl.BOT == phi & mtfl.BOT
    assert phi == phi & mtfl.TOP
    assert phi == phi | mtfl.BOT
    assert mtfl.TOP == mtfl.TOP & mtfl.TOP
    assert mtfl.BOT == mtfl.BOT | mtfl.BOT
    assert mtfl.TOP == mtfl.TOP | mtfl.BOT
    assert mtfl.BOT == mtfl.TOP & mtfl.BOT
    assert ~mtfl.BOT == mtfl.TOP
    assert ~mtfl.TOP == mtfl.BOT
    assert ~~mtfl.BOT == mtfl.BOT
    assert ~~mtfl.TOP == mtfl.TOP
    assert (phi & phi) & phi == phi & (phi & phi)
    assert (phi | phi) | phi == phi | (phi | phi)
    assert ~~phi == phi


def test_walk():
    phi = mtfl.parse(
        '(([ ][0, 1] ap1 & < >[1,2] ap2) | (@ap1 U ap2))')
    assert len(list((~phi).walk())) == 18
