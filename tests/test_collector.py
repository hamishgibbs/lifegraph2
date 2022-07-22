import pytest
from src.collector import Collector, CustomCompleter, parse_prompt_text

@pytest.fixture()
def mock_empty_collector():
    return Collector(fn="")

@pytest.fixture()
def mock_custom_completer():
    return CustomCompleter(completer_index={})

def test_text_is_node_only(mock_empty_collector):
    assert mock_empty_collector.text_is_node_only("[person: Thomas Jefferson]")
    assert not mock_empty_collector.text_is_node_only("")
    assert not mock_empty_collector.text_is_node_only("[person: Thomas Jefferson] founder_of [country: United States]")

def test_get_text_input_state(mock_custom_completer):
    m = mock_custom_completer
    assert m.get_text_input_state("[") == "type_1"
    assert m.get_text_input_state("[person: ") == "name_1"
    assert m.get_text_input_state("[person: Thomas Jefferson]") == "type_edge"
    assert m.get_text_input_state("[person: Thomas Jefferson] founder_of [") == "type_2"
    assert m.get_text_input_state("[person: Thomas Jefferson] founder_of [country: ") == "name_2"
    assert m.get_text_input_state("[person: Thomas Jefferson] founder_of [country: United States]") == "name_2"
    assert m.get_text_input_state("[person: Thomas Jefferson] founder_of [country: United States] (") == "type_edge_edge"
    assert m.get_text_input_state("[person: Thomas Jefferson] founder_of [country: United States] (date: ") == "name_edge_edge"
    assert m.get_text_input_state("[person: Thomas Jefferson] founder_of [country: United States] (date: 4th July 1776) (state") == "type_edge_edge"
    assert m.get_text_input_state("[person: Thomas Jefferson] founder_of [country: United States] (date: 4th July 1776) (state: ") == "name_edge_edge"

def test_parse_prompt_text():
    res = parse_prompt_text("")
    assert res == {
        "type_1": None,
        "name_1": None,
        "edge_type": None,
        "type_2": None,
        "name_2": None,
        "edge_edges": []
    }
    res = parse_prompt_text("[person: Elon Musk] founder_of [company: Facebook]")
    assert res == {
        "type_1": "person",
        "name_1": "Elon Musk",
        "edge_type": "founder_of",
        "type_2": "company",
        "name_2": "Facebook",
        "edge_edges": []
    }
    res = parse_prompt_text("[person: Elon Musk]")
    assert res == {
        "type_1": "person",
        "name_1": "Elon Musk",
        "edge_type": None,
        "type_2": None,
        "name_2": None,
        "edge_edges": []
    }

def test_parse_prompt_text_edge_edge():
    res = parse_prompt_text("[person: Elon Musk] founder_of [company: Facebook] (date: 12th June 2003) (location: California)")
    assert res == {
        "type_1": "person",
        "name_1": "Elon Musk",
        "edge_type": "founder_of",
        "type_2": "company",
        "name_2": "Facebook",
        "edge_edges": [("date", "12th June 2003"), ("location", "California")]
    }
