# TODO: figure out how to deduplicate this with robustness
# - Abstract as working on distributive lattice
import operator as op
from collections import defaultdict
from functools import reduce, singledispatch

import funcy as fn
from discrete_signals import signal

from mtl import ast


OO = float('inf')


def to_signal(ts_mapping):
    start = min(fn.pluck(0, fn.cat(ts_mapping.values())))
    assert start >= 0
    signals = (signal(v, start, OO, tag=k) for k, v in ts_mapping.items())
    return reduce(op.or_, signals)


def interp(sig, t, tag=None):
    # TODO: return function that interpolates the whole signal.
    sig = sig.project({tag})
    idx = sig.data.bisect_right(t) - 1
    if idx < 0:
        return None
    else:
        key = sig.data.keys()[idx]
    return sig[key][tag]


def dense_compose(sig1, sig2, init=None):
    sig12 = sig1 | sig2
    tags = sig12.tags

    def _dense_compose():
        state = {tag: init for tag in tags}
        for t, val in sig12.items():
            state = {k: val.get(k, state[k]) for k in tags}
            yield t, state

    data = list(_dense_compose())
    return sig12.evolve(data=data)


def booleanize_signal(sig):
    return sig.transform(lambda mapping: defaultdict(
        lambda: None, {k: 2*int(v) - 1 for k, v in mapping.items()}
    ))


def pointwise_sat(phi, dt=0.1, logic=None):
    if logic is None:
        from mtl import connective
        logic = connective.default
    f = eval_mtl(phi, dt, logic)

    def _eval_mtl(x, t=0, quantitative=False):
        sig = to_signal(x)
        if not quantitative:
            sig = booleanize_signal(sig)

        start_time = sig.items()[0][0]

        if t is None:
            res = [(t, v[phi]) for t, v in f(sig).items() if t >= start_time]
            return res if quantitative else [(t, v > 0) for t, v in res]

        if t is False:  # Use original signals starting time.
            t = start_time

        res = interp(f(sig), t, phi)
        return res if quantitative else res > 0

    return _eval_mtl


@singledispatch
def eval_mtl(phi, dt, logic):
    raise NotImplementedError


@eval_mtl.register(ast.And)
def eval_mtl_and(phi, dt, logic):
    fs = [eval_mtl(arg, dt, logic) for arg in phi.args]

    def _eval(x):
        sigs = [f(x) for f in fs]
        sig = reduce(lambda x, y: dense_compose(x, y, init=OO), sigs)
        return sig.map(lambda v: logic.tnorm(v.values()), tag=phi)

    return _eval


@eval_mtl.register(ast.Or)
def eval_mtl_or(phi, dt, logic):
    fs = [eval_mtl(arg, dt, logic) for arg in phi.args]

    def _eval(x):
        sigs = [f(x) for f in fs]
        sig = reduce(lambda x, y: dense_compose(x, y, init=OO), sigs)
        return sig.map(lambda v: logic.tconorm(v.values()), tag=phi)

    return _eval


def apply_weak_until(left_key, right_key, sig, logic):
    ut, ga = -OO, OO

    for t in reversed(sig.times()):
        left, right = interp(sig, t, left_key), interp(sig, t, right_key)

        ga = logic.tnorm(ga, left)
        ut = max(right, logic.tnorm(left, ut))
        yield (t, logic.tconorm(ut, ga))


@eval_mtl.register(ast.WeakUntil)
def eval_mtl_until(phi, dt, logic):
    f1, f2 = eval_mtl(phi.arg1, dt, logic), eval_mtl(phi.arg2, dt, logic)

    def _eval(x):
        sig = dense_compose(f1(x), f2(x), init=-OO)
        data = apply_weak_until(phi.arg1, phi.arg2, sig, logic)
        # FIXME signal removes entries outside [start:end] w/o interpolation
        d = list(data)
        s = signal(d, min(u for (u, _) in d), OO, tag=phi)
        d.append((x.start, interp(s, x.start, phi)))
        return signal(d, x.start, OO, tag=phi)

    return _eval


def apply_implies(left_key, right_key, sig, logic):
    for t in sig.times():
        left, right = interp(sig, t, left_key), interp(sig, t, right_key)
        yield (t, logic.implication(left, right))


@eval_mtl.register(ast.Implies)
def eval_mtl_implies(phi, dt, logic):
    f1, f2 = eval_mtl(phi.arg1, dt, logic), eval_mtl(phi.arg2, dt, logic)

    def _eval(x):
        sig = dense_compose(f1(x), f2(x), init=-OO)
        data = apply_implies(phi.arg1, phi.arg2, sig, logic)
        # FIXME signal removes entries outside [start:end] w/o interpolation
        d = list(data)
        s = signal(d, min(u for (u, _) in d), OO, tag=phi)
        d.append((x.start, interp(s, x.start, phi)))
        return signal(d, x.start, OO, tag=phi)

    return _eval


@eval_mtl.register(ast.G)
def eval_mtl_g(phi, dt, logic):
    f = eval_mtl(phi.arg, dt, logic)
    a, b = phi.interval
    if b < a:
        return lambda x: logic.const_true.retag({ast.TOP: phi})

    def _min(val):
        return logic.tnorm(val[phi.arg])

    def _eval(x):
        tmp = f(x)
        assert b >= a
        if b > a:
            return tmp.rolling(a, b).map(_min, tag=phi)

        return tmp.retag({phi.arg: phi})

    return _eval


@eval_mtl.register(ast.Neg)
def eval_mtl_neg(phi, dt, logic):
    f = eval_mtl(phi.arg, dt, logic)

    def _eval(x):
        return f(x).map(lambda v: logic.negation(v[phi.arg]), tag=phi)

    return _eval


@eval_mtl.register(ast.Next)
def eval_mtl_next(phi, dt, logic):
    f = eval_mtl(phi.arg, dt, logic)

    def _eval(x):
        return (f(x) << dt).retag({phi.arg: phi})

    return _eval


@eval_mtl.register(ast.AtomicPred)
def eval_mtl_ap(phi, _, _2):
    def _eval(x):
        return x.project({phi.id}).retag({phi.id: phi})

    return _eval


@eval_mtl.register(type(ast.BOT))
def eval_mtl_bot(_, _1, logic):
    return lambda x: logic.const_false
