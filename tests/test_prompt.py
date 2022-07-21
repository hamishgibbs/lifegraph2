import pytest
from src.collector import Collector

@pytest.fixture()
def mock_empty_collector():
    return Collector(fn="")

def test_text_is_node_only(mock_empty_collector):
    assert mock_empty_collector.text_is_node_only("[person: Thomas Jefferson]")
    assert not mock_empty_collector.text_is_node_only("")
    assert not mock_empty_collector.text_is_node_only("[person: Thomas Jefferson] founder_of [country: United States]")
