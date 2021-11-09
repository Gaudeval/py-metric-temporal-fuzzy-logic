import mtfl

import hypothesis.strategies as st
from hypothesis import given


@given(st.integers(), st.integers(), st.integers())
def test_params1(a, b, c):
    phi = mtfl.parse('G[a, b] x')
    assert {x.name for x in phi.params} == {'a', 'b'}

    phi2 = phi[{'a': a, 'b': b}]
    assert phi2.params == set()
    assert phi2 == mtfl.parse(f'G[{a}, {b}](x)')
