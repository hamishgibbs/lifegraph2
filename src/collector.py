"""
Analysis of startup founders

Peter Theil founder_of Confinity, Palantir Technologies, Founders Fund
invested_in Facebook

Elon Musk founder_of X.com, SpaceX, The Boring Company, Neuralink, OpenAI
ceo_of Tesla

Max Levchin founder_of Confinity, Slide.com, HVF, Affirm,
invested_in Yelp

Confinity merged_with X.com
    became PayPal

"""

{
    "type": "person",
    "name": "Peter Theil",
    "founder_of": ["(company) Confinity", "(company) Palantir Technologies", "(venture_capital_firm) Founders Fund"],
    "early_investor_in": "(company) Facebook"
}

{
    "type": "person",
    "name": "Elon Musk",
    "founder_of": ["(company) X.com", "(company) SpaceX", "(company) The Boring Company", "(company) Neuralink", "(company) OpenAI"],
    "ceo_of": "(company) Tesla"
}

"""
[person: "Elon Musk"]
[pe/rson: "El/on Musk"] fou/nder_of [company: "X.com"]
[pe/rson: "El/on Musk"] fou/nder_of [company: "SpaceX"]

create node with name property

autocomplete for current graph types (this can come from schema)

autocomplete for precedence name of this type

autocomplete for current edge names for this type (this can also come from schema)

create edge pointing to appropriate entity (create if doesn't exist)

no fuzzy bullshit!
"""

import re

from prompt_toolkit import prompt
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.completion import WordCompleter, NestedCompleter, Completer, Completion

from main import Graph

def parse_prompt_text(text):
    """Parses input text to a dictionary, None if missing."""
    types = re.findall(r"\[([^\s]+):", text)
    names = re.findall(r": (.*?)\]", text)
    edge_type = re.findall(r"\] (.*?) \[", text)
    edge_edges = re.findall(r"\((.*?): (.*?)\)", text)
    edge_edge_types = re.findall(r"\((.*?):", text)
    edge_edge_names = re.findall(r"\(.*?: (.*?)\)", text)

    return {
        "type_1": types[0] if len(types) > 0 else None,
        "name_1": names[0] if len(names) > 0 else None,
        "edge_type": edge_type[0] if len(edge_type) else None,
        "type_2": types[1] if len(types) > 1 else None,
        "name_2": names[1] if len(names) > 1 else None,
        "edge_edge_types": edge_edge_types,
        "edge_edge_names": edge_edge_types
    }

class CustomCompleter(Completer):

    def __init__(self, completer_index):
        self.index = completer_index

    def get_type_1_suggestions(self):
        # these are all types in the graph
        return sorted(set([i[0] for i in self.index["type_index"]]))

    def get_name_1_suggestions(self, text):
        # these are all the precedence names of all primitives of this type
        parsed = parse_prompt_text(text)
        return sorted(self.index["name_index"][parsed["type_1"]])

    def get_type_edge_suggestions(self, text):
        parsed = parse_prompt_text(text)
        return sorted(set([i[1] for i in self.index["type_index"] if i[0] == parsed["type_1"]]))

    def get_type_2_suggestions(self, text):
        # these are the types pointed to by objects of type_1 with type_edge
        # so, select all edges with left in types(type_1)
        # then get all types of right of these edges
        parsed = parse_prompt_text(text)
        return sorted(set([i[2] for i in self.index["type_index"] if i[0] == parsed["type_1"] and i[1] == parsed["edge_type"]]))

    def get_name_2_suggestions(self, text):
        # these are all names of objects of type_2
        parsed = parse_prompt_text(text)
        return sorted(self.index["name_index"][parsed["type_2"]])

    def get_type_edge_edge_suggestions(self, text):
        # simple types of all edge edges
        return sorted(self.index["edge_edge_type_index"])

    def get_edge_edge_name_suggestions(self, text):
        parsed = parse_prompt_text(text)
        return sorted(self.index["edge_edge_name_index"][parsed["edge_edge_types"][-1]])

    def get_text_input_state(self, text):
        if text == "[":
            return "type_1"
        elif text.count("[") == 1 and text.count(":") == 1 and not text.count("]") == 1:
            return "name_1"
        elif text.count("[") == 1 and text.count(":") == 1 and text.count("]") == 1:
            return "type_edge"
        elif text.count("[") == 2 and text.count(":") == 1:
            return "type_2"
        elif text.count("[") == 2 and text.count(":") == 2 and text.count("(") == 0:
            return "name_2"
        elif text.count("(") >= 1 and text.count(":")-2 < text.count("("):
            return "type_edge_edge"
        elif text.count("(") >= 1 and text.count(":")-2 == text.count("("):
            return "name_edge_edge"

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        word = word.replace("[", "")
        word = word.replace("(", "")

        if self.get_text_input_state(document.text) == "type_1":
            types = self.get_type_1_suggestions()
        elif self.get_text_input_state(document.text) == "name_1":
            types = self.get_name_1_suggestions(text=document.text)
        elif self.get_text_input_state(document.text) == "type_edge":
            types = self.get_type_edge_suggestions(document.text)
        elif self.get_text_input_state(document.text) == "type_2":
            types = self.get_type_2_suggestions(document.text)
        elif self.get_text_input_state(document.text) == "name_2":
            types = self.get_name_2_suggestions(document.text)
        elif self.get_text_input_state(document.text) == "type_edge_edge":
            types = self.get_type_edge_edge_suggestions(document.text)
        elif self.get_text_input_state(document.text) == "name_edge_edge":
            types = self.get_edge_edge_name_suggestions(document.text)
        else:
            types = []

        for type in types:
            if type.startswith(word):
                yield Completion(type, start_position=-1*len(word))

class Collector():

    def __init__(self, fn):

        self.fn = fn

        self.graph = Graph(fn=fn)

    def build_completer_index(self):

        # type index is the unique of all edges (not edge edges)
        graph = self.graph.current_state_graph()
        all_edge_guids = [k for k in graph.keys() if graph[k]["left"] and graph[k]["right"]]
        edge_edge_guids = [k for k in graph.keys() if str(graph[k]["left"]) in all_edge_guids]
        node_edge_guids = set(all_edge_guids).difference(set(edge_edge_guids))
        node_guids = set(graph.keys()).difference(set(all_edge_guids))

        type_index = [
            (
                graph[str(graph[k]["left"])]["type"],
                graph[k]["type"],
                graph[str(graph[k]["right"])]["type"]
            )
            for k in graph.keys() if k in node_edge_guids
        ]

        name_index = {k: [] for k in self.graph.derive_schema().keys()}
        [name_index[graph[k]["type"]].append(
            self.graph.name_node_by_precedence(int(k))[2])
            for k in node_guids if graph[k]["type"]]

        edge_edge_type_index = set([graph[k]["type"] for k in edge_edge_guids])

        edge_edge_name_index = {k: [] for k in edge_edge_type_index}
        [edge_edge_name_index[graph[k]["type"]].append(
            self.graph.name_node_by_precedence(int(graph[k]["right"]))[2])
            for k in edge_edge_guids]
        edge_edge_name_index = dict(zip(edge_edge_name_index.keys(), map(set, edge_edge_name_index.values())))

        return {
            "type_index": type_index,
            "name_index": name_index,
            "edge_edge_type_index": edge_edge_type_index,
            "edge_edge_name_index": edge_edge_name_index,
        }

    def run(self):
        # need to construct the completer from the schema sort of?

        # build completer indices here
        completer_index = self.build_completer_index()


        text = prompt('>>> ', completer=CustomCompleter(completer_index=completer_index))

        self.interpret_prompt_text(text)

    def text_is_node_only(self, text):
        return text.count("[") == 1

    def named_node_exists(self, type, name):
        return len(self.graph.get_guid_from_precedence_name(
            type=type,
            name=name)) > 0

    def interpret_prompt_text(self, text):

        parsed = parse_prompt_text(text=text)

        if not parsed["edge_type"]:
            if self.named_node_exists(type=parsed["type_1"],
                    name=parsed["name_1"]):
                raise Exception(f"Existing node of type '{parsed['type_1']}' with name '{parsed['name_1']}'")
            else:
                node_guid = self.graph.create_node(type=parsed["type_1"])
                name_guid = self.graph.create_node(datatype="str", value=parsed["name_1"])
                self.graph.create_edge(left=node_guid, right=name_guid, type="name")
        else:

            # Both below can be abstracted
            # create a node if one doesn't yet exist
            if not self.named_node_exists(type=parsed["type_1"],
                    name=parsed["name_1"]):
                node_guid = self.graph.create_node(type=parsed["type_1"])
                name_guid = self.graph.create_node(datatype="str", value=parsed["name_1"])
                self.graph.create_edge(left=node_guid, right=name_guid, type="name")

            # create a node if one doesn't yet exist
            if not self.named_node_exists(type=parsed["type_2"],
                    name=parsed["name_2"]):
                node_guid = self.graph.create_node(type=parsed["type_2"])
                name_guid = self.graph.create_node(datatype="str", value=parsed["name_2"])
                self.graph.create_edge(left=node_guid, right=name_guid, type="name")

            # Both below can be abstracted?
            # check that name only refers to one node
            left_guid = self.graph.get_guid_from_precedence_name(
                type=parsed["type_1"],
                name=parsed["name_1"])
            right_guid = self.graph.get_guid_from_precedence_name(
                type=parsed["type_2"],
                name=parsed["name_2"])

            if len(left_guid) > 1:
                raise Exception(f"Found {len(left_guid)} nodes with type '{parsed['type_1']}' and name '{parsed['name_1']}'")
            if len(right_guid) > 1:
                raise Exception(f"Found {len(right_guid)} nodes with type '{parsed['type_2']}' and name '{parsed['name_2']}'")

            edge_guid = self.graph.create_edge(left=left_guid[0], right=right_guid[0], type=parsed['edge_type'])

            # add edge edges value node (if needed) and edge from edge to value
            for edge_edge_type, edge_edge_name in zip(parsed["edge_edge_types"], parsed["edge_edge_names"]):

                if not self.named_node_exists(type=edge_edge_type,
                        name=edge_edge_name):
                    node_guid = self.graph.create_node(type=edge_edge_type)
                    name_guid = self.graph.create_node(datatype="str", value=edge_edge_name)
                    self.graph.create_edge(left=node_guid, right=name_guid, type="name")

                right_guid = self.graph.get_guid_from_precedence_name(
                    type=edge_edge_type,
                    name=edge_edge_name)

                if len(right_guid) > 1:
                    raise Exception(f"Found {len(right_guid)} nodes with type '{edge_edge_type}' and name '{edge_edge_name}'")

                self.graph.create_edge(left=edge_guid, right=edge_edge_type, type=edge_edge_name)


# TODO could have better management of the difference between a named entity and a value
#   as it stands, all values are named entities
# TODO edge type suggestions don't seem to be working
# TODO edge edge suggestions also don't seem to be working

# great fucking job

# output as network tuple or CSV

# "[" should set off a list of selectable node types + ": "
# and completer for precedence names of that type + "]"

# this syntax should support arbitrary edge edges? Or should it? It is really simple right now
# maybe it is a whole other syntax for that

# give this a spin on the founders or a war or something - it is rocking.


def main():

    Collector(fn="data/wwii_graph.json").run()

if __name__ == "__main__":
    main()
