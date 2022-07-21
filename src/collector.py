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
from prompt_toolkit import prompt
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.completion import WordCompleter, NestedCompleter

from main import Graph

class Collector():

    def __init__(self, fn):

        self.graph = Graph(fn=fn)


    def run(self):
        # need to construct the completer from the schema sort of?
        completer = NestedCompleter.from_nested_dict(
            {"[person:": {"Elon_Musk]": {"founder_of": {"[company:": {"X.com]": None}}, "invested_in": {"[company:": {"Facebook]": None}}}}},
        )

        type_completer = WordCompleter(["[person: ", "[city: ", "[state: "])
        text = prompt('>>> ', completer=completer)

        self.parse_prompt_text(text)

    def text_is_node_only(self, text):
        return text.count("[") == 1

    def parse_prompt_text(self, text):
        text = text.replace(" ", "")

        if self.text_is_node_only(text):
            text = text.replace("[", "")
            text = text.replace("]", "")
            type = text.split(":")[0]
            name = text.split(":")[1]
            name = name.replace("_", " ")

            node_guid = self.graph.create_node(type=type)
            name_guid = self.graph.create_node(datatype="str", value=name)
            self.graph.create_edge(left=node_guid, right=name_guid, type="name")


            # create node with name
        else:
            raise Exception("Not supporting edges yet bro!")
            # check if node with this name exists
            # if it does,
                # get its ID and make an edge to it
            # if it does not,
                # create the node
                # then create the edge

        #print(text)
        # trim whitespace from either side
        # if it is just a node, create the node
        # if it is an edge, create the edge
        # if it is edge pointing to a non-existent node, create the node, then the edge



# "[" should set off a list of selectable node types + ": "
# and completer for precedence names of that type + "]"



def main():

    Collector(fn="data/startup_graph.json").run()

if __name__ == "__main__":
    main()
