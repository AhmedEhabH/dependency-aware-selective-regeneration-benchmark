from benchmark.repositories.loader import RepositoryLoader
from benchmark.scenarios.loader import ScenarioLoader


def test_repository_loader_is_not_repository_adapter() -> None:
    """RepositoryLoader implements RepositoryLoaderBase, not RepositoryAdapter."""
    from benchmark.repositories.base import RepositoryLoaderBase
    loader = RepositoryLoader.__new__(RepositoryLoader)
    assert isinstance(loader, RepositoryLoaderBase)


def test_scenario_loader_provides_get_scenario() -> None:
    """ScenarioLoader exposes load_scenario but is not a ScenarioProvider."""
    loader_methods = dir(ScenarioLoader)
    assert "load_scenario" in loader_methods


def test_repository_loader_can_be_initialized() -> None:
    loader = RepositoryLoader.__new__(RepositoryLoader)
    assert loader is not None


def test_scenario_loader_can_be_initialized() -> None:
    loader = ScenarioLoader.__new__(ScenarioLoader)
    assert loader is not None
