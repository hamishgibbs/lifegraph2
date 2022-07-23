"""
Graph primitives:

{
guid: 128-bit GUID :
    {
    left: 128-bit GUID
    right: 128-bit GUID
    type: 64-bit UTF-8
    prev: 128-bit GUID
    timestamp: 64-bit millisecond timestamp
    datatype: 64-bit UTF-8
    value: variable-length UTF-8
    live: 1-bit boolean
    }
}
"""
import json
import time
from collections import ChainMap
from collections import defaultdict

class Graph:

    def __init__(self, fn):

        self.fn = fn

    def flat(self, ll):
        return [x for xs in ll for x in xs]

    def graph(self):

        with open(self.fn, "r") as f:
            return json.load(f)

    def current_state_graph(self):
        """Prunes edit/deletion history to include only live primitives."""
        graph = self.graph()

        changes = [[k, graph[k]["prev"]] for k in graph.keys() if graph[k]["prev"]]
        sets = [frozenset(i+j) for i in changes for j in changes if i!=j and (set(i) & set(j))]

        edited = self.flat([list(x) for x in set().union(sets)])
        active_edited = set(max(x) for x in sets if graph[max(x)]["live"])
        active_unedited = [k for k in graph.keys() if k not in edited]
        active = active_unedited + list(active_edited)

        return dict((k, graph[k]) for k in active)

    def append_json(self, primitive):
        graph = self.graph()
        graph.update(primitive)
        with open(self.fn, "w") as f:
            f.write(json.dumps(graph, indent=4))

    def clear_json(self):
        with open(self.fn, "w") as f:
            f.write("{}")

    def increment_guid(self):

        graph = self.graph()

        graph_keys = [int(x) for x in graph.keys()] if graph else []

        return max(graph_keys) + 1 if graph_keys else 1

    def new_primitive(self,
        left: int = None,
        right: int = None,
        type: str = None,
        prev: int = None,
        datatype: str = None,
        value: str = None,
        live: bool = None
    ):

        guid = self.increment_guid()

        return {guid: {
            "left": left,
            "right": right,
            "type": type,
            "prev": prev,
            "timestamp": time.time() * 1000,
            "datatype": datatype,
            "value": value,
            "live": live
        }}

    def create_node(self, type: str = None, datatype: str = None, value: str = None):

        node = self.new_primitive(type=type, datatype=datatype, value=value, live=True)

        self.append_json(node)

        return list(node.keys())[0]

    def create_edge(self,
        left: int,
        right: int,
        type: str):

        edge = self.new_primitive(
            left=left,
            right=right,
            type=type,
            live=True)

        self.append_json(edge)

        return list(edge.keys())[0]

    def edit(self, guid, **kwargs):
        new_guid = self.increment_guid()
        kwargs.update({
            "prev": guid,
            "timestamp": time.time() * 1000,
            })
        old = self.graph()[guid]
        new_primitive = {new_guid: old | kwargs}
        self.append_json(new_primitive)
        return new_guid

    def delete(self, guid):
        new_guid = self.increment_guid()
        deletion = {
            "prev": guid,
            "timestamp": time.time() * 1000,
            "live": False
            }
        old = self.graph()[guid]
        new_primitive = {new_guid: old | deletion}
        self.append_json(new_primitive)
        return new_guid

    def derive_schema(self):
        graph = self.current_state_graph()

        all_edge_guids = [k for k in graph.keys() if graph[k]["left"] and graph[k]["right"]]
        edge_edge_guids = [k for k in graph.keys() if str(graph[k]["left"]) in all_edge_guids]
        node_edge_guids = set(all_edge_guids).difference(set(edge_edge_guids))
        node_guids = set(graph.keys()).difference(set(all_edge_guids))

        schema = {}

        for k in node_guids:
            if graph[k]["type"]:
                schema[graph[k]["type"]] = set()

        for k in node_edge_guids:
            left_type = graph[str(graph[k]["left"])]["type"]
            schema[left_type].update([graph[k]["type"]])

        for type in schema.keys():
            properties = schema[type]
            data = {k: set() for k in properties}
            schema[type] = data

        for k in edge_edge_guids:
            edge_edge_type = graph[k]["type"]
            left_edge_guid = graph[k]["left"]
            left_edge_type = graph[str(left_edge_guid)]["type"]
            left_node_guid = graph[str(left_edge_guid)]["left"]
            left_node_type = graph[str(left_node_guid)]["type"]
            schema[left_node_type][left_edge_type].update([edge_edge_type])

        for type in schema.keys():
            for property in schema[type].keys():
                schema[type][property] = list(schema[type][property])

        return schema

    def name_node_by_precedence(self, guid, precedence=["name", "title", "date"]):
        """Names a node by some precedence of edges pointing to values."""
        graph = self.current_state_graph()

        outward_edges = [{graph[k]["type"]: graph[k]["right"]} for k in graph.keys() if graph[k]["left"] == guid]
        outward_edges = dict(ChainMap(*outward_edges))

        if not len(outward_edges.keys()):
            return (guid, graph[str(guid)]["datatype"], graph[str(guid)]["value"])

        for name in precedence:
            if name in outward_edges.keys():
                if graph[str(outward_edges[name])]["value"]:
                    # if there is a value, return it with the property name
                    return (guid, name, graph[str(outward_edges[name])]["value"])

    def guids_for_node_of_type(self, type):
        graph = self.current_state_graph()
        return [k for k in graph.keys() if graph[k]["type"] == type]

    def guids_for_value_of_datatype(self, datatype):
        graph = self.current_state_graph()
        return [k for k in graph.keys() if graph[k]["datatype"] == datatype]

    def precedence_names_for_node_of_type(self, type):
        type_guids = self.guids_for_node_of_type(type=type)
        return [self.name_node_by_precedence(guid=int(k)) for k in type_guids]

    def precedence_names_for_value_of_datatype(self, datatype):
        type_guids = self.guids_for_value_of_datatype(datatype=datatype)
        return [self.name_node_by_precedence(guid=int(k)) for k in type_guids]

    def get_guid_from_precedence_name(self, name, type=None, datatype=None):
        """Returns a list of nodes of this type with the given precedence name."""
        if type:
            return [x[0] for x in self.precedence_names_for_node_of_type(type=type) if x[2] == name]
        elif datatype:
            return [x[0] for x in self.precedence_names_for_value_of_datatype(datatype=datatype) if x[2] == name]

    def guid_to_concise_json(self, guid):
        # This is chicken scratch! clean it up!
        graph = self.current_state_graph()
        concise = {guid: {}}
        # get edges leaving this node
        out_edges = [k for k in graph.keys() if graph[k]["left"] == guid]

        for out_edge in out_edges:

            # get edges leaving from these edges
            out_edge_edges = [k for k in graph.keys() if str(graph[k]["left"]) == out_edge]
            if not len(out_edge_edges):
                concise[guid].update({graph[out_edge]["type"]: self.name_node_by_precedence(graph[out_edge]["right"])[2]})
            else:
                concise[guid].update({graph[out_edge]["type"]: {self.name_node_by_precedence(graph[out_edge]["right"])[2]: {}}})
                for out_edge_edge in out_edge_edges:
                    concise[guid][graph[out_edge]["type"]][self.name_node_by_precedence(graph[out_edge]["right"])[2]].update({
                        graph[out_edge_edge]["type"]: self.name_node_by_precedence(graph[out_edge_edge]["right"])[2]
                    })

        return concise

    # now add speedy data collection (i.e. Arnold Schwarzenneger height 6' 1")
    # (i.e. Zaifeng, Prince Chun, appointed Qing Emperor, year: 1901)
        # second one is an example of an edge edge
    # [zaifeng, appointed, Qing Emperor [year: 1901, location: China]]
    # fuzzy_match_by_precedence() # match a string to some entity by appromximate name on decending precedence keys
    # create_from_freetext(text) # match subject, predicate, object, with any n edge edges

def main():

    g = Graph(fn="data/graph.json")
    print(g.graph())
    print(g.create_node(type="person"))
    print(json.dumps(g.graph(), indent=4))

def test_create_arnold():
    g = Graph(fn="data/graph.json")
    g.clear_json()
    arnold = g.create_node(type="person")
    name_value = g.create_node(datatype="str", value="Arnold Schwarzenneger")
    name = g.create_edge(left=arnold, right=name_value, type="name")
    first_name_value = g.create_node(datatype="str", value="Arnold")
    first_name_edit = g.edit(guid='3', type="first_name", right=first_name_value)
    g.delete(guid=str(first_name_edit))
    print(json.dumps(g.current_state_graph(), indent=4))
    #print(g.derive_schema())

def test_concise_json():
    g = Graph(fn="data/graph.json")
    g.clear_json()
    arnold = g.create_node(type="person")
    name_value = g.create_node(datatype="str", value="Arnold Schwarzenneger")
    name = g.create_edge(left=arnold, right=name_value, type="name")
    book = g.create_node(type="book")
    title_value = g.create_node(datatype="str", value="Total Recall: My Unbelievably True Life Story")
    book_title = g.create_edge(left=book, right=title_value, type="title")
    arnold_authorship = g.create_edge(left=arnold, right=book, type="author_of")
    year_value = g.create_node(datatype="integer", value="2013")
    book_published = g.create_edge(left=book, right=year_value, type="year_published")

    print(json.dumps(g.current_state_graph(), indent=4))
    print(g.to_concise_json())

def mock_governor_of_california_on_date():
    g = Graph(fn="data/graph.json")
    g.clear_json()
    arnold = g.create_node(type="person")
    name_value = g.create_node(datatype="str", value="Arnold Schwarzenneger")
    name = g.create_edge(left=arnold, right=name_value, type="name")
    governor = g.create_node(type="political_office")
    california = g.create_node(type="state")
    title_value = g.create_node(datatype="str", value="Governor")
    california_name_value = g.create_node(datatype="str", value="California")
    governor_title = g.create_edge(left=governor, right=title_value, type="title")
    california_name = g.create_edge(left=california, right=california_name_value, type="name")
    arnold_governor = g.create_edge(left=arnold, right=governor, type="elected_as")
    date_value = g.create_node(datatype="int", value="2003")
    arnold_governor_date = g.create_edge(left=arnold_governor, right=date_value, type="date")
    arnold_governor_state = g.create_edge(left=arnold_governor, right=california, type="state")
    return g


def test_concise_json_edge_edge():
    g = mock_governor_of_california_on_date()
    #year_value = g.create_node(datatype="integer", value="2013")
    #book_published = g.create_edge(left=book, right=year_value, type="year_published")

    #print(json.dumps(g.current_state_graph(), indent=4))
    print(print(json.dumps(g.guid_to_concise_json(1), indent=4)))

def test_concise_json_edge_edge_startup():
    g = mock_governor_of_california_on_date()
    #year_value = g.create_node(datatype="integer", value="2013")
    #book_published = g.create_edge(left=book, right=year_value, type="year_published")

    #print(json.dumps(g.current_state_graph(), indent=4))
    print(print(json.dumps(g.guid_to_concise_json(1), indent=4)))


def test_derive_schema_edge_edge():
    g = Graph(fn="data/wwii_graph_messy.json")
    #year_value = g.create_node(datatype="integer", value="2013")
    #book_published = g.create_edge(left=book, right=year_value, type="year_published")

    #print(json.dumps(g.current_state_graph(), indent=4))
    print(json.dumps(g.derive_schema(), indent=4))

def test_name_node_by_precedence_value_node():
    g = Graph(fn="data/wwii_graph_messy.json")
    #year_value = g.create_node(datatype="integer", value="2013")
    #book_published = g.create_edge(left=book, right=year_value, type="year_published")

    #print(json.dumps(g.current_state_graph(), indent=4))
    #guid = g.create_node(datatype="date", value="Date Today")
    #print(guid)
    #print(json.dumps(g.guid_to_concise_json(94), indent=4))
    #print(g.name_node_by_precedence(94))
    print(g.get_guid_from_precedence_name("Date Today", datatype="date"))


if __name__ == "__main__":
    #test_create_arnold()
    test_name_node_by_precedence_value_node()
