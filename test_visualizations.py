import unittest

from Node import Node
from Visualize import build_branch_histogram_figure, build_piano_roll_figure, build_tree_figure


def build_sample_tree():
    root = Node(0, None)
    first = root.create_child(3, 2)
    second = root.create_child(2, -1)
    first.create_child(1, 4)
    branch = first.create_child(1, 5)
    branch.create_child(1, 7)
    second.create_child(1, 0)
    return root


class NodeVisualizationHelperTests(unittest.TestCase):
    def test_path_ids_are_stable(self):
        root = build_sample_tree()
        first_child = root.children[0]
        grandchild = first_child.children[1]

        self.assertEqual(root.get_path_id(), "root")
        self.assertEqual(first_child.get_path_id(), "root/0")
        self.assertEqual(grandchild.get_path_id(), "root/0/1")
        self.assertIs(root.get_node_by_path("root/0/1"), grandchild)

    def test_child_summaries_match_structure(self):
        root = build_sample_tree()
        summaries = root.get_child_summaries("root/0")

        self.assertEqual(len(summaries), 2)
        self.assertEqual([item["symbol"] for item in summaries], [4, 5])
        self.assertEqual(summaries[0]["path"], "root/0/0")
        self.assertTrue(summaries[0]["is_leaf"])
        self.assertFalse(summaries[1]["is_leaf"])

    def test_branch_lengths_match_existing_logic(self):
        root = build_sample_tree()
        self.assertEqual(sorted(root.get_branch_lengths()), sorted(root.find_leaf_distances()))


class FigureSmokeTests(unittest.TestCase):
    def test_tree_figure_builds(self):
        root = build_sample_tree()
        figure = build_tree_figure(root, active_path_ids=["root", "root/0", "root/0/1"])
        self.assertEqual(len(figure.axes), 1)

    def test_histogram_figure_builds(self):
        root = build_sample_tree()
        figure = build_branch_histogram_figure([root])
        self.assertEqual(len(figure.axes), 1)

    def test_piano_roll_handles_notes_and_chords(self):
        figure = build_piano_roll_figure([60, [64, 67], 69])
        self.assertEqual(len(figure.axes), 1)
        self.assertGreaterEqual(len(figure.axes[0].patches), 4)


if __name__ == "__main__":
    unittest.main()
