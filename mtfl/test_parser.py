# -*- coding: utf-8 -*-
from hypothesis import given

import mtfl
from mtfl.hypothesis import MetricTemporalLogicStrategy


@given(MetricTemporalLogicStrategy)
def test_stablizing_repr(phi):
    for _ in range(10):
        phi, phi2 = mtfl.parse(str(phi)), phi

    assert phi == phi2


def test_sugar_smoke():
    mtfl.parse('(x <-> x)')
    mtfl.parse('(x -> x)')
    mtfl.parse('(x ^ x)')
