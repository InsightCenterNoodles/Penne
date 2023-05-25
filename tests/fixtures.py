
import pytest

from rigatoni import Server, StartingComponent, Method, Entity, Material
from penne.core import Client
from .test_delegates import TableDelegate


def print_method():
    print("Method on server called!")
    return "Method on server called!"


starting_components = [
    StartingComponent(Method, {"name": "test_method"}, print_method),
    StartingComponent(Entity, {}),
    StartingComponent(Material, {"name": "test_material"})
]


@pytest.fixture
def rig_base_server():
    with Server(50000, starting_components) as server:
        yield server


@pytest.fixture
def base_client(rig_base_server):
    with Client("ws://localhost:50000", strict=True) as client:
        yield client


@pytest.fixture
def delegate_client(rig_base_server):
    with Client("ws://localhost:50000", custom_delegate_hash={"tables": TableDelegate}, strict=True) as client:
        yield client


@pytest.fixture
def mock_socket(mocker):
    return mocker.MagicMock()
