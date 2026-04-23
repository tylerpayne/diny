"""Tests for Factory annotation and @factory decorator."""

from diny import Factory, Singleton, factory, inject


class Counter:
    n = 0

    def __init__(self):
        Counter.n += 1
        self.value = Counter.n


@factory
class DecoratedCounter:
    n = 0

    def __init__(self):
        DecoratedCounter.n += 1
        self.value = DecoratedCounter.n


def test_distinct_instances(di):
    @inject
    def grab(a: Factory[Counter], b: Factory[Counter]):
        return a, b

    a, b = grab()
    assert a is not b
    assert a.value != b.value


def test_distinct_across_calls(di):
    @inject
    def grab(c: Factory[Counter]):
        return c

    assert grab() is not grab()


def test_decorator_gives_factory(di):
    @inject
    def grab(a: DecoratedCounter, b: DecoratedCounter):
        return a, b

    a, b = grab()
    assert a is not b
    assert a.value != b.value


def test_factory_with_deps(di):
    class Dep:
        pass

    class NeedsDep:
        def __init__(self, dep: Singleton[Dep]):
            self.dep = dep

    @inject
    def grab(a: Factory[NeedsDep], b: Factory[NeedsDep]):
        return a, b

    a, b = grab()
    assert a is not b
    assert a.dep is b.dep  # dep is singleton, shared


def test_factory_does_not_pollute_cache(di):
    @inject
    def grab_factory(c: Factory[Counter]):
        return c

    @inject
    def grab_singleton(c: Singleton[Counter]):
        return c

    f = grab_factory()
    s = grab_singleton()
    assert f is not s
    # singleton should now be cached
    assert grab_singleton() is s


def test_mixed_singleton_and_factory(di):
    @inject
    def grab(
        s1: Singleton[Counter],
        s2: Singleton[Counter],
        f1: Factory[Counter],
        f2: Factory[Counter],
    ):
        return s1, s2, f1, f2

    s1, s2, f1, f2 = grab()
    assert s1 is s2
    assert f1 is not f2
    assert f1 is not s1
    assert f2 is not s1
