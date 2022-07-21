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
    return {
        "type_1": types[0],
        "name_1": names[0],
        "edge_type": edge_type[0] if len(edge_type) else None,
        "type_2": types[1] if len(types) > 1 else None,
        "name_2": names[1] if len(names) > 1 else None
    }

class CustomCompleter(Completer, Graph):

    def get_type_1_suggestions(self):
        # these are all types in the graph
        return list(self.derive_schema().keys())

    def get_name_1_suggestions(self, text):
        # these are all the precedence names of all primitives of this type
        parsed = parse_prompt_text(text)
        return [x[2] for x in self.precedence_names_for_type(type=parsed["type_1"])]

    def get_type_edge_suggestions(self, text):
        parsed = parse_prompt_text(text)
        return list(self.derive_schema()[parsed["type_1"]])

    def get_text_input_state(self, text):
        if text == "[":
            return "type_1"
        elif text.count("[") == 1 and text.count(":") == 1 and not text.count("]") == 1:
            return "name_1"
        elif text.count("[") == 1 and text.count(":") == 1 and text.count("]") == 1:
            return "type_edge"
        elif text.count("[") == 2 and text.count(":") == 1:
            return "type_2"
        elif text.count("[") == 2 and text.count(":") == 2:
            return "name_2"

    def get_completions(self, document, complete_event):
        #print(document.text)
        # if only [ in document.text, yield types
        # if [ and : in document.text, parse and yield names of that type
        # if [ and : and ] in document.text yield all outward
        if self.get_text_input_state(document.text) == "type_1":
            types = self.get_type_1_suggestions()
        elif self.get_text_input_state(document.text) == "name_1":
            types = self.get_name_1_suggestions(text=document.text)
        elif self.get_text_input_state(document.text) == "type_edge":
            types = self.get_type_edge_suggestions(document.text)
        elif self.get_text_input_state(document.text) == "type_2":
            types = ["company"]
        elif self.get_text_input_state(document.text) == "name_2":
            types = ["Facebook", "X.com"]
        else:
            types = []

        word = document.get_word_before_cursor()
        word = word.replace("[", "")
        for type in types:
            if type.startswith(word):
                yield Completion(type, start_position=-1*len(word))

class Collector():

    def __init__(self, fn):

        self.fn = fn

        self.graph = Graph(fn=fn)

    def run(self):
        # need to construct the completer from the schema sort of?

        text = prompt('>>> ', completer=CustomCompleter(fn=self.fn))

        self.interpret_prompt_text(text)

    def text_is_node_only(self, text):
        return text.count("[") == 1

    def named_node_exists(self, type, name):
        return len(self.graph.get_guid_from_precedence_name(
            type=type,
            name=name)) > 0

    def interpret_prompt_text(self, text):

        parsed = self.parse_prompt_text(text=text)

        if not parsed["edge_type"]:
            if self.named_node_exists(type=parsed["type_1"],
                    name=parsed["name_1"]):
                raise Exception(f"Existing node of type '{parsed['type_1']}' with name '{parsed['name_1']}'")
            else:
                node_guid = self.graph.create_node(type=parsed["type_1"])
                name_guid = self.graph.create_node(datatype="str", value=parsed["name_1"])
                self.graph.create_edge(left=node_guid, right=name_guid, type="name")
        else:

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

            self.graph.create_edge(left=left_guid[0], right=right_guid[1], type=parsed['edge_type'])

# "[" should set off a list of selectable node types + ": "
# and completer for precedence names of that type + "]"



def main():

    Collector(fn="data/startup_graph.json").run()

if __name__ == "__main__":
    main()
