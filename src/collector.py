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
        "edge_edge_names": edge_edge_names
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
        try:
            return sorted(self.index["name_index"][parsed["type_1"]])
        except:
            return []

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
        try:
            return sorted(self.index["name_index"][parsed["type_2"]])
        except:
            return []

    def get_type_edge_edge_suggestions(self, text):
        # simple types of all edge edges
        return sorted(self.index["edge_edge_type_index"])

    def get_edge_edge_name_suggestions(self, text):
        parsed = parse_prompt_text(text)
        try:
            return sorted(self.index["edge_edge_name_index"][parsed["edge_edge_types"][-1]])
        except:
            return []

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
        graph = self.graph.current_state_graph()
        all_edge_guids = [k for k in graph.keys() if graph[k]["left"] and graph[k]["right"]]
        edge_edge_guids = [k for k in graph.keys() if str(graph[k]["left"]) in all_edge_guids]
        node_edge_guids = set(all_edge_guids).difference(set(edge_edge_guids))
        node_guids = set(graph.keys()).difference(set(all_edge_guids))

        type_index = [
            (
                graph[str(graph[k]["left"])]["type"],
                graph[k]["type"],
                graph[str(graph[k]["right"])]["type"] if graph[str(graph[k]["right"])]["type"] else graph[str(graph[k]["right"])]["datatype"]
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
        while True:
            completer_index = self.build_completer_index()

            text = prompt('>>> ', completer=CustomCompleter(completer_index=completer_index))

            self.interpret_prompt_text(text)

    def text_is_node_only(self, text):
        return text.count("[") == 1

    def node_guid_from_precedence_name(self, type, name):
        # check if either a named node or a value node exists with this precedence name
        # first search for a named node, then a value node
        # Could this be changed deeper in Graph?
        named_node_guids = self.graph.get_guid_from_precedence_name(
            name=name,
            type=type)
        value_node_guids = self.graph.get_guid_from_precedence_name(
            name=name,
            datatype=type)
        if len(named_node_guids):
            return named_node_guids
        else:
            return value_node_guids

    def create_named_or_value_node(self, type, name, datatype_names, error):
        # This currently does more than one thing (you can turn an error on and off with `error`)
        existing_node_guids = self.node_guid_from_precedence_name(type=type, name=name)

        if len(existing_node_guids) > 0 and error:
            raise Exception(f"Existing node of type '{type}' with name '{name}'")
        elif len(existing_node_guids) > 0 and not error:
            return existing_node_guids[0]

        if type in datatype_names:
            node_guid = self.graph.create_node(datatype=type, value=name)
        else:
            node_guid = self.graph.create_node(type=type)
            name_guid = self.graph.create_node(datatype="str", value=name)
            self.graph.create_edge(left=node_guid, right=name_guid, type="name")

        return node_guid


    def interpret_prompt_text(self, text, datatype_names = ["date", "int", "str"]):

        #text = "[person: Thomas Jefferson] founder_of [country: United States] (date: 1776)" # TESTING
        parsed = parse_prompt_text(text=text)

        # create only a single node (either a named node or value node)
        if not parsed["edge_type"]:
            self.create_named_or_value_node(
                type=parsed["type_1"],
                name=parsed["name_1"],
                datatype_names=datatype_names,
                error=True)
        else:
            self.create_named_or_value_node(
                type=parsed["type_1"],
                name=parsed["name_1"],
                datatype_names=datatype_names,
                error=False)

            self.create_named_or_value_node(
                type=parsed["type_2"],
                name=parsed["name_2"],
                datatype_names=datatype_names,
                error=False)

            left_guid = self.node_guid_from_precedence_name(
                type=parsed["type_1"],
                name=parsed["name_1"])
            right_guid = self.node_guid_from_precedence_name(
                type=parsed["type_2"],
                name=parsed["name_2"])

            if len(left_guid) > 1:
                raise Exception(f"Found {len(left_guid)} nodes with type '{parsed['type_1']}' and name '{parsed['name_1']}'")
            if len(right_guid) > 1:
                raise Exception(f"Found {len(right_guid)} nodes with type '{parsed['type_2']}' and name '{parsed['name_2']}'")

            edge_guid = self.graph.create_edge(left=left_guid[0], right=right_guid[0], type=parsed['edge_type'])

            # add edge edges value node (if needed) and edge from edge to value
            for edge_edge_type, edge_edge_name in zip(parsed["edge_edge_types"], parsed["edge_edge_names"]):

                self.create_named_or_value_node(
                    type=edge_edge_type,
                    name=edge_edge_name,
                    datatype_names=datatype_names,
                    error=False)

                right_guid = self.node_guid_from_precedence_name(
                    type=edge_edge_type,
                    name=edge_edge_name)

                if len(right_guid) > 1:
                    raise Exception(f"Found {len(right_guid)} nodes with type '{edge_edge_type}' and name '{edge_edge_name}'")

                self.graph.create_edge(left=edge_guid, right=right_guid[0], type=edge_edge_type)



# TODO could have better management of the difference between a named entity and a value
#   as it stands, all values are named entities X

# Will including data types fuck up the completions just as they are working? yes. maybe.
# now fix completions

# output as network tuple or CSV

# How to manage edge names and do summarising / generalising

# choosing not to have auto completion for datatype types because it isn't really helpful to have a list of every single number inputted
# In future - it would be nice to prevent duplication of exactly identical edges (including based on edge edges)


def main():

    Collector(fn="data/zf_graph.json").run()
    # attempt collection of ZF data

if __name__ == "__main__":
    main()
