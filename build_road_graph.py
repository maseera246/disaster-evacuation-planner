
import math
import osmium
import networkx as nx
import pickle

PBF_FILE = "pune-highways.osm.pbf"
OUTPUT_FILE = "pune_road_graph.pkl"


def haversine(lat1, lon1, lat2, lon2):
    """Calculate approximate distance between two GPS coordinates in metres."""
    earth_radius = 6_371_000

    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    dlat = lat2 - lat1
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )

    return 2 * earth_radius * math.asin(math.sqrt(a))


class RoadHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.graph = nx.MultiDiGraph()
        self.way_count = 0

    def way(self, way):
        # Ignore objects that are not tagged as roads.
        if "highway" not in way.tags:
            return

        nodes = list(way.nodes)
        if len(nodes) < 2:
            return

        road_name = way.tags.get("name", "Unnamed road")
        oneway = way.tags.get("oneway", "no")
        speed = way.tags.get("maxspeed", "unknown")

        # Add coordinates for each road node and connect consecutive nodes.
        for node in nodes:
            if not node.location.valid():
                continue

            self.graph.add_node(
                node.ref,
                lat=node.location.lat,
                lon=node.location.lon
            )

        for first, second in zip(nodes, nodes[1:]):
            if first.ref not in self.graph or second.ref not in self.graph:
                continue

            if not first.location.valid() or not second.location.valid():
                continue

            distance = haversine(
                first.location.lat, first.location.lon,
                second.location.lat, second.location.lon
            )

            if distance <= 0:
                continue

            edge_data = {
                "length": distance,
                "name": road_name,
                "highway": way.tags.get("highway", "unknown"),
                "maxspeed": speed
            }

            self.graph.add_edge(first.ref, second.ref, **edge_data)

            # Respect explicit one-way roads.
            if oneway not in ("yes", "1", "true"):
                self.graph.add_edge(second.ref, first.ref, **edge_data)

        self.way_count += 1


def main():
    print("Reading Pune road data...")
    handler = RoadHandler()
    handler.apply_file(PBF_FILE, locations=True)

    graph = handler.graph

    # Remove isolated nodes that have no usable road connections.
    graph.remove_nodes_from(list(nx.isolates(graph)))

    print(f"Road ways processed: {handler.way_count:,}")
    print(f"Graph nodes: {graph.number_of_nodes():,}")
    print(f"Graph edges: {graph.number_of_edges():,}")

    with open(OUTPUT_FILE, "wb") as file:
        pickle.dump(graph, file, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"Saved graph to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
