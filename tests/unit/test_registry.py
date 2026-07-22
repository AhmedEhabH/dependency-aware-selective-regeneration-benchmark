import pytest

from benchmark.core.exceptions import DuplicateRegistrationError, UnknownRegistrationError
from benchmark.core.registry import Registry


class TestRegistry:
    def test_register_and_create(self) -> None:
        registry: Registry[object] = Registry()

        class MyService:
            def __init__(self, value: str = "") -> None:
                self.value = value

        registry.register("svc", MyService)
        instance = registry.create("svc", value="hello")
        assert isinstance(instance, MyService)
        assert instance.value == "hello"

    def test_duplicate_registration_raises(self) -> None:
        registry: Registry[object] = Registry()

        class A:
            pass

        class B:
            pass

        registry.register("x", A)
        with pytest.raises(DuplicateRegistrationError, match="Duplicate registration"):
            registry.register("x", B)

    def test_unknown_lookup_raises(self) -> None:
        registry: Registry[object] = Registry()
        with pytest.raises(UnknownRegistrationError, match="Unknown registration"):
            registry.create("nonexistent")

    def test_list_names(self) -> None:
        registry: Registry[object] = Registry()

        class A:
            pass

        class B:
            pass

        registry.register("a", A)
        registry.register("b", B)
        names = registry.list_names()
        assert "a" in names
        assert "b" in names
        assert len(names) == 2

    def test_contains(self) -> None:
        registry: Registry[object] = Registry()

        class A:
            pass

        registry.register("a", A)
        assert "a" in registry
        assert "b" not in registry

    def test_len(self) -> None:
        registry: Registry[object] = Registry()

        class A:
            pass

        assert len(registry) == 0
        registry.register("a", A)
        assert len(registry) == 1

    def test_freeze_prevents_registration(self) -> None:
        registry: Registry[object] = Registry()

        class A:
            pass

        registry.freeze()
        with pytest.raises(RuntimeError, match="frozen"):
            registry.register("a", A)

    def test_get_returns_class(self) -> None:
        registry: Registry[object] = Registry()

        class A:
            pass

        registry.register("a", A)
        cls = registry.get("a")
        assert cls is A

    def test_registration_order_independence(self) -> None:
        registry: Registry[object] = Registry()

        class A:
            pass

        class B:
            pass

        registry.register("a", A)
        registry.register("b", B)
        assert registry.create("a") is not None
        assert registry.create("b") is not None
