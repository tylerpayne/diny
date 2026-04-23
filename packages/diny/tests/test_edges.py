"""Edge cases: circular deps, deep chains, contextvars isolation, etc."""

import asyncio
import threading

import pytest

from diny import Factory, Singleton, aprovide, inject, provide, singleton


# --- Circular dependencies ---


class SelfRef:
    def __init__(self, other: "Singleton[SelfRef]"):
        self.other = other


class CycleA:
    def __init__(self, b: "Singleton[CycleB]"):
        self.b = b


class CycleB:
    def __init__(self, a: Singleton[CycleA]):
        self.a = a


def test_self_cycle(di):
    @inject
    def grab(x: Singleton[SelfRef]):
        return x

    with pytest.raises(RuntimeError, match="Circular"):
        grab()


def test_mutual_cycle(di):
    @inject
    def grab(a: Singleton[CycleA]):
        return a

    with pytest.raises(RuntimeError, match="Circular"):
        grab()


# --- Deep dependency chains ---


class L0:
    pass


class L1:
    def __init__(self, dep: Singleton[L0]):
        self.dep = dep


class L2:
    def __init__(self, dep: Singleton[L1]):
        self.dep = dep


class L3:
    def __init__(self, dep: Singleton[L2]):
        self.dep = dep


class L4:
    def __init__(self, dep: Singleton[L3]):
        self.dep = dep


def test_deep_chain(di):
    @inject
    def grab(x: Singleton[L4]):
        return x

    x = grab()
    assert isinstance(x.dep.dep.dep.dep, L0)


def test_deep_chain_shared_root(di):
    @inject
    def grab(x: Singleton[L4], root: Singleton[L0]):
        return x, root

    x, root = grab()
    assert x.dep.dep.dep.dep is root


# --- Diamond dependencies ---


class Top:
    pass


class Left:
    def __init__(self, t: Singleton[Top]):
        self.t = t


class Right:
    def __init__(self, t: Singleton[Top]):
        self.t = t


class Bottom:
    def __init__(self, left: Singleton[Left], right: Singleton[Right]):
        self.left = left
        self.right = right


def test_diamond_shares_top(di):
    @inject
    def grab(b: Singleton[Bottom]):
        return b

    b = grab()
    assert b.left.t is b.right.t


# --- Thread isolation ---


class ThreadConfig:
    def __init__(self):
        self.url = "default"


def test_threads_get_independent_scopes():
    results = {}

    def worker(name, url):
        cfg = ThreadConfig()
        cfg.url = url
        with provide(cfg):

            @inject
            def grab(c: Singleton[ThreadConfig]):
                return c.url

            results[name] = grab()

    t1 = threading.Thread(target=worker, args=("t1", "url-1"))
    t2 = threading.Thread(target=worker, args=("t2", "url-2"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["t1"] == "url-1"
    assert results["t2"] == "url-2"


# --- Async task isolation ---


def test_async_tasks_get_independent_scopes():
    class Cfg:
        def __init__(self):
            self.url = "default"

    async def worker(url):
        cfg = Cfg()
        cfg.url = url
        async with aprovide(cfg):

            @inject
            async def grab(c: Singleton[Cfg]):
                await asyncio.sleep(0.01)
                return c.url

            return await grab()

    async def main():
        r1, r2 = await asyncio.gather(worker("a"), worker("b"))
        return r1, r2

    r1, r2 = asyncio.run(main())
    assert {r1, r2} == {"a", "b"}


# --- Provide with no args ---


def test_provide_no_args_isolates():
    @inject
    def grab(x: Singleton[L0]):
        return x

    with provide():
        a = grab()
        with provide():
            b = grab()
        c = grab()

    assert a is c
    assert a is not b


# --- Multiple instances in provide ---


def test_provide_multiple_instances():
    class A:
        pass

    class B:
        pass

    a, b = A(), B()

    with provide(a, b):

        @inject
        def grab(x: Singleton[A], y: Singleton[B]):
            return x, y

        x, y = grab()
        assert x is a
        assert y is b


# --- Provider returning subclass ---


def test_callable_returning_subclass():
    class Base:
        pass

    class Sub(Base):
        pass

    with provide(Base=lambda: Sub()):

        @inject
        def grab(b: Singleton[Base]):
            return b

        assert isinstance(grab(), Sub)


# --- Interaction: decorator + provider override ---


def test_provider_overrides_singleton_decorator():
    @singleton
    class S:
        value = "original"

    class Override(S):
        value = "override"

    with provide(S=Override):

        @inject
        def grab(s: S):
            return s.value

        assert grab() == "override"


def test_provider_overrides_factory_decorator():
    @singleton
    class F:
        pass

    class Override(F):
        pass

    with provide(F=Override):

        @inject
        def grab(f: Factory[F]):
            return f

        a, b = grab(), grab()
        assert a is not b
        assert isinstance(a, Override)
