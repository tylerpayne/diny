"""Tests for @singleton / @factory class decorators and interaction with site annotations."""

from diny import Factory, Singleton, factory, inject, singleton


def test_singleton_decorator(di):
    @singleton
    class S:
        pass

    @inject
    def grab(s: S):
        return s

    assert grab() is grab()


def test_factory_decorator(di):
    @factory
    class F:
        pass

    @inject
    def grab(f: F):
        return f

    assert grab() is not grab()


def test_singleton_decorator_with_deps(di):
    class Dep:
        pass

    @singleton
    class S:
        def __init__(self, dep: Singleton[Dep]):
            self.dep = dep

    @inject
    def grab(s: S):
        return s

    s = grab()
    assert isinstance(s.dep, Dep)
    assert grab() is s


def test_factory_decorator_with_deps(di):
    class Dep:
        pass

    @factory
    class F:
        def __init__(self, dep: Singleton[Dep]):
            self.dep = dep

    @inject
    def grab(f: F):
        return f

    a, b = grab(), grab()
    assert a is not b
    assert a.dep is b.dep  # shared singleton dep


def test_site_singleton_overrides_factory_decorator(di):
    @factory
    class F:
        pass

    @inject
    def grab(f: Singleton[F]):
        return f

    assert grab() is grab()


def test_site_factory_overrides_singleton_decorator(di):
    @singleton
    class S:
        pass

    @inject
    def grab(s: Factory[S]):
        return s

    assert grab() is not grab()


def test_undecorated_class_not_injected(di):
    class Plain:
        pass

    @inject
    def grab(p: Plain):
        return p

    p = Plain()
    assert grab(p) is p


def test_undecorated_with_singleton_annotation(di):
    class Plain:
        pass

    @inject
    def grab(p: Singleton[Plain]):
        return p

    assert grab() is grab()


def test_undecorated_with_factory_annotation(di):
    class Plain:
        pass

    @inject
    def grab(p: Factory[Plain]):
        return p

    assert grab() is not grab()


def test_mixed_decorators_in_one_function(di):
    @singleton
    class S:
        pass

    @factory
    class F:
        pass

    @inject
    def grab(s: S, f: F):
        return s, f

    s1, f1 = grab()
    s2, f2 = grab()
    assert s1 is s2
    assert f1 is not f2
