import unittest
import dynetx.algorithms as al
import dynetx as dn
import numpy as np
import json
import random
import os


class ConformityTestCase(unittest.TestCase):

    def test_delta_conformity(self):
        g = dn.DynGraph()

        labels = ['SI', 'NO']
        nodes = ['A', 'B', 'C', 'D']

        for node in nodes:
            g.add_node(node, labels=random.choice(labels))

        g.add_interaction("A", "B", 1, 4)
        g.add_interaction("B", "D", 2, 5)
        g.add_interaction("A", "C", 4, 8)
        g.add_interaction("B", "D", 2, 4)
        g.add_interaction("B", "C", 6, 10)
        g.add_interaction("B", "D", 2, 4)
        g.add_interaction("A", "B", 7, 9)

        res = al.delta_conformity(g, 1, 5, list(np.arange(1, 4, 0.2)), ['labels'], profile_size=1)

        with open(f"conformity.json", "w") as o:
            json.dump(res, o)

        for k, v in res.items():
            for z, t in v.items():
                for _, val in t.items():
                    self.assertTrue(-1 <= float("{:.4f}".format(val)) <= 1)

        os.remove("conformity.json")

    def test_delta_annotated_conformity(self):
        g = dn.DynGraph()

        labels = ['SI', 'NO']
        nodes = ['A', 'B', 'C', 'D']

        for node in nodes:
            g.add_node(node, labels=random.choice(labels))

        g.add_interaction("A", "B", 1, 4)
        g.add_interaction("B", "D", 2, 5)
        g.add_interaction("A", "C", 4, 8)
        g.add_interaction("B", "D", 2, 4)
        g.add_interaction("B", "C", 6, 10)
        g.add_interaction("B", "D", 2, 4)
        g.add_interaction("A", "B", 7, 9)

        res = al.delta_conformity(g, 1, 10, list(np.arange(1, 4, 0.2)), ['labels'], profile_size=1, path_type="fastest")

        with open(f"conformity_annotated.json", "w") as o:
            json.dump(res, o)

        for k, v in res.items():
            for z, t in v.items():
                for _, val in t.items():
                    self.assertTrue(-1 <= float("{:.4f}".format(val)) <= 1)

        os.remove("conformity_annotated.json")

    def test_hierarchical_delta_conformity(self):

        g = dn.DynGraph()

        nodes = ['A', 'B', 'C', 'D']

        labels = ['one', 'two', 'three', 'four']
        age = ["A", "B", "C"]
        hierarchy = {'labels': {'one': 1, 'two': 2, 'three': 3, 'four': 4}}

        for node in nodes:
            g.add_node(node, labels=random.choice(labels), age=random.choice(age))

        g.add_interaction("A", "B", 1, 4)
        g.add_interaction("B", "D", 2, 5)
        g.add_interaction("A", "C", 4, 8)
        g.add_interaction("B", "D", 2, 4)
        g.add_interaction("B", "C", 6, 10)
        g.add_interaction("B", "D", 2, 4)
        g.add_interaction("A", "B", 7, 9)

        res = al.delta_conformity(g, 1, 5, list(np.arange(1, 4, 0.2)), ['labels', 'age'], profile_size=2,
                                  hierarchies=hierarchy)

        with open(f"conformity_hierarchy.json", "w") as o:
            json.dump(res, o)

        for k, v in res.items():
            for z, t in v.items():
                for _, val in t.items():
                    self.assertTrue(-1 <= float("{:.4f}".format(val)) <= 1)

        os.remove("conformity_hierarchy.json")

    def test_sliding_delta_conformity(self):
        g = dn.DynGraph()

        labels = ['SI', 'NO']
        nodes = ['A', 'B', 'C', 'D']

        for node in nodes:
            g.add_node(node, labels=random.choice(labels))

        g.add_interaction("A", "B", 1, 4)
        g.add_interaction("B", "D", 2, 5)
        g.add_interaction("A", "C", 4, 8)
        g.add_interaction("B", "D", 2, 4)
        g.add_interaction("B", "C", 6, 10)
        g.add_interaction("B", "D", 2, 4)
        g.add_interaction("A", "B", 7, 9)

        res = al.sliding_delta_conformity(g, 2, list(np.arange(1, 4, 0.2)), ['labels'], profile_size=1)

        with open(f"sliding_conformity.json", "w") as o:
            json.dump(res, o)

        for k, v in res.items():
            for z, t in v.items():
                for _, val in t.items():
                    self.assertIsInstance(val, list)
                    for _, c in val:
                        self.assertTrue(-1 <= float("{:.4f}".format(c)) <= 1)

        os.remove("sliding_conformity.json")

    def test_delta_conformity_dynamic_attributes(self):
        g = dn.DynGraph()

        labels = ['SI', 'NO']

        g.add_interaction("A", "B", 1, 4)
        g.add_interaction("B", "D", 2, 5)
        g.add_interaction("A", "C", 4, 8)
        g.add_interaction("B", "D", 2, 4)
        g.add_interaction("B", "C", 6, 10)
        g.add_interaction("B", "D", 2, 4)
        g.add_interaction("A", "B", 7, 9)

        for node in g.nodes():
            g.add_node(node,
                       labels={k: random.choices(labels, weights=[0.7, 0.3], k=1)[0] for k in g.node_presence(node)})

        res = al.delta_conformity(g, 1, 5, list(np.arange(1, 4, 0.2)), ['labels'], profile_size=1)

        with open(f"conformity.json", "w") as o:
            json.dump(res, o)

        for k, v in res.items():
            for z, t in v.items():
                for _, val in t.items():
                    self.assertTrue(-1 <= float("{:.4f}".format(val)) <= 1)

        os.remove("conformity.json")

    def test_sliding_delta_conformity_dynamic_attributes(self):
        g = dn.DynGraph()

        labels = ['SI', 'NO']

        g.add_interaction("A", "B", 1, 4)
        g.add_interaction("B", "D", 2, 5)
        g.add_interaction("A", "C", 4, 8)
        g.add_interaction("B", "D", 2, 4)
        g.add_interaction("B", "C", 6, 10)
        g.add_interaction("B", "D", 2, 4)
        g.add_interaction("A", "B", 7, 9)

        for node in g.nodes():
            g.add_node(node,
                       labels={k: random.choices(labels, weights=[0.5, 0.5], k=1)[0] for k in g.node_presence(node)})

        res = al.sliding_delta_conformity(g, 2, list(np.arange(1, 4, 0.2)), ['labels'], profile_size=1)

        with open(f"sliding_conformity.json", "w") as o:
            json.dump(res, o)

        for k, v in res.items():
            for z, t in v.items():
                for _, val in t.items():
                    self.assertIsInstance(val, list)
                    for _, c in val:
                        self.assertTrue(-1 <= float("{:.4f}".format(c)) <= 1)

        os.remove("sliding_conformity.json")


if __name__ == '__main__':
    unittest.main()
