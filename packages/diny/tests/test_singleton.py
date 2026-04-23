"""Tests for Singleton annotation and @singleton decorator."""

from diny import Singleton, inject, provide, singleton


class A:
    pass


class B:
    def __init__(self, a: Singleton[A]):
        self.a = a


class C:
    def __init__(self, a: Singleton[A], b: Singleton[B]):
        self.a = a
        self.b = b


@singleton
class Decorated:
    pass


@singleton
class DecoratedWithDep:
    def __init__(self, a: Singleton[A]):
        self.a = a


def test_returns_same_instance(di):
    @inject
    def grab(a: Singleton[A]):
        return a

    assert grab() is grab()


def test_shared_across_params(di):
    @inject
    def grab(a: Singleton[A], b: Singleton[B]):
        return a, b

    a, b = grab()
    assert a is b.a


def test_transitive_sharing(di):
    @inject
    def grab(c: Singleton[C]):
        return c

    c = grab()
    assert c.a is c.b.a


def test_different_scopes_get_different_instances():
    with provide():

        @inject
        def grab(a: Singleton[A]):
            return a

        first = grab()

    with provide():
        second = grab()

    assert first is not second


def test_decorator_gives_singleton(di):
    @inject
    def grab(d: Decorated):
        return d

    assert grab() is grab()


def test_decorator_with_dep(di):
    @inject
    def grab(d: DecoratedWithDep):
        return d

    d = grab()
    assert isinstance(d.a, A)
    assert grab() is d


def test_multiple_singleton_params_same_type(di):
    @inject
    def grab(a1: Singleton[A], a2: Singleton[A]):
        return a1, a2

    a1, a2 = grab()
    assert a1 is a2
