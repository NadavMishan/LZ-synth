import math


class Node:
    """
    Probability binary tree
    :param
    prob: The probability of the tree (sum of all leaves under it)
    letter: symbol associated with the node
    code: source code for the letter
    """

    def __init__(self, freq, symbol):
        self.children = []
        self.parent = None
        self.freq = freq
        self.symbol = symbol
        self.children_symbols = []

    def create_child(self, freq, symbol=None):
        child = Node(freq, symbol)
        self.children.append(child)
        child.parent = self
        self.freq += freq
        self.children_symbols.append(symbol)
        return child

    def find_child_by_symbol(self, symbol):
        for child in self.children:
            if child.symbol == symbol:
                return child
        return None

    def is_leaf(self):
        return len(self.children) == 0

    def _get_leaf_metrics(self, current_depth=0):
        """
        Helper function to recursively collect (frequency, depth) for all leaves.
        """
        if self.is_leaf():
            return [(self.freq, current_depth)]

        metrics = []
        for child in self.children:
            metrics.extend(child._get_leaf_metrics(current_depth + 1))
        return metrics

    def analyze_tree_metrics(self):
        """
        Calculates and returns several metrics for the subtree rooted at this node:
        1. Number of leaves.
        2. Average distance (depth) to a leaf (unweighted).
        3. Longest path (maximum depth) to a leaf (unweighted).
        4. Weighted longest path (max(frequency * depth)) to a leaf.
        5. Average weighted path (sum(frequency * depth) / total_frequency) to a leaf.

        Returns: A dictionary of calculated metrics.
        """
        leaf_metrics = self._get_leaf_metrics(current_depth=0)
        num_leaves = len(leaf_metrics)

        if num_leaves == 0:
            return {
                "num_leaves": 0,
                "avg_distance": 0.0,
                "longest_path": 0,
                "weighted_longest_path": 0.0,
                "avg_weighted_path": 0.0
            }

        total_depth = 0
        total_weighted_path = 0.0
        max_depth = 0
        max_weighted_path = 0.0
        total_leaf_frequency = 0.0

        for freq, depth in leaf_metrics:
            weighted_path = freq * depth

            total_depth += depth
            total_weighted_path += weighted_path
            total_leaf_frequency += freq

            max_depth = max(max_depth, depth)
            max_weighted_path = max(max_weighted_path, weighted_path)

        avg_distance = total_depth / num_leaves if num_leaves > 0 else 0.0
        avg_weighted_path = total_weighted_path / \
            total_leaf_frequency if total_leaf_frequency > 0 else 0.0

        return {
            "num_leaves": num_leaves,
            "avg_distance": avg_distance,
            "longest_path": max_depth,
            "weighted_longest_path": max_weighted_path,
            "avg_weighted_path": avg_weighted_path
        }

    def find_leaf_distances(self):
        """
        Finds the distance (number of edges) from the current node to each 
        leaf node in its subtree and returns a list of (symbol, distance) tuples.
        """
        distances = []

        if self.is_leaf():
            # If the current node is a leaf, the distance from itself is 0.
            if self.symbol is not None:
                distances.append(0)
            return distances

        # Recursively call the method on all children
        for child in self.children:
            child_distances = child.find_leaf_distances()

            # Increment the distance for all results found in the child's subtree
            for distance in child_distances:
                # The distance is 1 (to the child) + distance from child to leaf
                distances.append(distance + 1)

        return distances

    def get_path_id(self):
        """
        Returns a stable, path-based identifier for this node within its tree.
        The root node is identified as 'root' and each child appends its index.
        """
        if self.parent is None:
            return "root"

        path_parts = []
        current = self
        while current.parent is not None:
            try:
                index = current.parent.children.index(current)
            except ValueError:
                break
            path_parts.append(str(index))
            current = current.parent

        return "root/" + "/".join(reversed(path_parts))

    def get_node_by_path(self, path_id):
        """
        Resolves a node from a path id produced by get_path_id().
        Returns None when the path does not exist below the current node.
        """
        if path_id in (None, "", "root"):
            return self

        if isinstance(path_id, str):
            parts = [part for part in path_id.split("/") if part]
        else:
            return None

        if not parts or parts[0] != "root":
            return None

        current = self
        for part in parts[1:]:
            try:
                index = int(part)
            except ValueError:
                return None

            if index < 0 or index >= len(current.children):
                return None
            current = current.children[index]

        return current

    def iter_nodes_with_paths(self):
        """
        Recursively enumerates the subtree as dictionaries containing path ids
        and parent relationships for visualization purposes.
        """
        nodes = []

        def walk(node):
            node_id = node.get_path_id()
            parent_id = node.parent.get_path_id() if node.parent is not None else None
            nodes.append(
                {
                    "id": node_id,
                    "parent_id": parent_id,
                    "symbol": node.symbol,
                    "freq": node.freq,
                    "is_leaf": node.is_leaf(),
                    "child_count": len(node.children),
                }
            )
            for child in node.children:
                walk(child)

        walk(self)
        return nodes

    def get_child_summaries(self, path_id="root"):
        """
        Returns child metadata for the node at path_id.
        """
        node = self.get_node_by_path(path_id)
        if node is None:
            return []

        summaries = []
        for child in node.children:
            summaries.append(
                {
                    "id": child.get_path_id(),
                    "path": child.get_path_id(),
                    "symbol": child.symbol,
                    "freq": child.freq,
                    "is_leaf": child.is_leaf(),
                    "child_count": len(child.children),
                }
            )
        return summaries

    def get_branch_lengths(self):
        """
        Returns the list of root-to-leaf branch lengths for this subtree.
        """
        return self.find_leaf_distances()
