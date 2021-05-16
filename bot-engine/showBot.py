import os
from graphviz import Graph
from graphviz import Digraph, nohtml

# os.environ["PATH"] += os.pathsep + 'C:\\Program Files\\Graphviz\\bin'

box_template = '{<f0> Box {0} |{<f1>1.1|<f2>1.2|<f3>1.3}}'
button_template_open = '|{<f{}>{}.{}'
button_template_mid = '|<f{}>{}.{}'
button_template_close = '|<f{}>{}.{}}'

import random


class bot_edge:
    def __init__(self, box, button, destination):
        self.box = box
        self.button = button
        self.destination = destination


class bot_node:
    def __init__(self, box, num_of_buttons):
        self.box = box
        self.button_list = [i for i in range(1, num_of_buttons + 1, 1)]


edges = [bot_edge(1, 1, 2), bot_edge(2, 1, 1)]
nodes = [bot_node(i, random.randint(0, 3)) for i in range(6)]


def create_edge_render_string(botedge: bot_edge) -> str:
    pass


def create_nodes_render_string(_nodes: [bot_node]):
    node_strings = ['' for _ in _nodes]
    box_strings = []
    for i, node in enumerate(_nodes):
        box = node.box
        box_strings.append(f'box{node.box}')
        last_item_index = len(node.button_list) - 1
        for j, button in enumerate(node.button_list):
            node_strings[i] += node_strings[i]
            if j == 0:
                node_strings[i] += f'|{{<f{j + 1}>{box}.{j + 1}'
                if j == last_item_index:
                    node_strings[i] += '}'
            elif j == last_item_index:
                node_strings[i] += f'|<f{j + 1}>{box}.{j + 1}}}'
            else:
                node_strings[i] += f'|<f{j + 1}>{box}.{j + 1}'
    return list(zip(box_strings, node_strings))  # [('box0', '{<f0> Box 1 |{<f1>1.1|<f2>1.2|<f3>1.3}}')]

def main():
    s = Digraph('structs', node_attr={'shape': 'plaintext'})
    g = Digraph('g', filename='btree.gv',
                node_attr={'shape': 'record'})

    # render_nodes = create_nodes_render_string(nodes)
    # for box,buttons in render_nodes:
    #     g.node()

    g.node('box0', nohtml('{<f0> Box 1 |{<f1>1.1|<f2>1.2|<f3>1.3}}'))
    g.node('box1', nohtml('{<f0> Box 2 |{<f1>1.1|<f2>1.2|<f3>1.3}}'))
    g.edge('box0:f1', 'box1:f0')
    g.edge('box1:f2', 'box0:f0')
    # g.edge('node0:f2', 'node4:f1')
    # g.edge('node0:f0', 'node1:f1')
    # g.edge('node1:f0', 'node2:f1')
    # g.edge('node1:f2', 'node3:f1')
    # g.edge('node2:f2', 'node8:f1')
    # g.edge('node2:f0', 'node7:f1')
    # g.edge('node4:f2', 'node6:f1')
    # g.edge('node4:f0', 'node5:f1')
    g.view()


if __name__ == '__main__':
    main()
