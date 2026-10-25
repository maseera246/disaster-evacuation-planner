
import math
import pickle
import networkx as nx

GRAPH_FILE = "pune_road_graph.pkl"
_road_graph = None


def get_road_graph():
    """Load the road graph once and reuse it."""
    global _road_graph

    if _road_graph is None:
        with open(GRAPH_FILE, "rb") as file:
            _road_graph = pickle.load(file)

    return _road_graph


def haversine(lat1, lon1, lat2, lon2):
    """Straight-line distance between GPS coordinates, in metres."""
    radius = 6_371_000

    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    dlat = lat2 - lat1
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * radius * math.asin(math.sqrt(a))


def nearest_road_node(graph, lat, lon):
    """Find the closest graph node to a GPS coordinate."""
    return min(
        graph.nodes,
        key=lambda node: haversine(
            lat, lon,
            graph.nodes[node]["lat"],
            graph.nodes[node]["lon"]
        )
    )


def find_route_between_coordinates(start_lat, start_lon, end_lat, end_lon):
    """Find an A* route between two geographic coordinates."""
    graph = get_road_graph()

    start_node = nearest_road_node(graph, start_lat, start_lon)
    end_node = nearest_road_node(graph, end_lat, end_lon)

    def heuristic(node, goal):
        a = graph.nodes[node]
        b = graph.nodes[goal]

        return haversine(a["lat"], a["lon"], b["lat"], b["lon"])

    try:
        path = nx.astar_path(
            graph,
            start_node,
            end_node,
            heuristic=heuristic,
            weight="length"
        )

        distance = nx.path_weight(graph, path, weight="length")

        coordinates = [
            [graph.nodes[node]["lat"], graph.nodes[node]["lon"]]
            for node in path
        ]

        return {
            "route": path,
            "coordinates": coordinates,
            "distance": distance,
            "start_node": start_node,
            "end_node": end_node
        }

    except nx.NetworkXNoPath:
        raise ValueError(
            "No connected road route was found between these locations."
        )
