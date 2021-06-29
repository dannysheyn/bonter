from graphviz import Digraph, nohtml


class bot_edge:
    def __init__(self, box, button, destination):
        self.box = box
        self.button = button
        self.destination = destination

    def __hash__(self):
        return hash(f'{self.box}{self.button}{self.destination}')

    def __eq__(self, other):
        if not isinstance(other, bot_edge):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.box == other.box and self.button == other.button \
            and self.destination == other.destination


class bot_node:
    def __init__(self, box, msg=''):
        self.box = box
        self.msg = msg
        self.button_list = []

    def __eq__(self, other):
        if not isinstance(other, bot_node):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.box == other.box and self.msg == other.msg

    def __hash__(self):
        # necessary for instances to behave sanely in dicts and sets.
        return hash((self.box, self.msg))


class botToPicture:
    def __init__(self, bot_nodes={}, bot_edges=set()):
        self.bot_nodes = bot_nodes
        self.bot_edges = bot_edges
        self.graph = None

    def render_graph(self, bot_nodes, bot_edges, bot_user_name):
        self.graph = Digraph('g', filename=bot_user_name, node_attr={'shape': 'record'}, format='png')
        graph_string_nodes = self.create_nodes_render_string(bot_nodes)
        graph_string_edges = self.create_edge_render_list(bot_edges)
        for node, buttons in graph_string_nodes:
            self.graph.node(node, nohtml(buttons))
        for from_box, dest_box in graph_string_edges:
            self.graph.edge(from_box, dest_box)
        pic_path = self.graph.render(filename=bot_user_name, view=False, format='png')
        return pic_path

    # g.edge('box0:f1', 'box1:f0')
    @staticmethod
    def create_edge_render_string(edge) -> (str, str):
        return f'box{edge.box}:f{edge.button + 1}', f'box{edge.destination}:f0'

    def create_edge_render_list(self, bot_edges):
        edges_render_string = \
            [
                self.create_edge_render_string(edge) for edge in bot_edges
            ]
        return edges_render_string

    @staticmethod
    def create_nodes_render_string(_nodes: [bot_node]):
        node_strings = ['' for _ in _nodes]
        box_strings = []
        for i, node in enumerate(_nodes):
            box = node.box
            box_strings.append(f'box{node.box}')
            last_item_index = len(node.button_list) - 1
            node_strings[i] += f'{{<f0> Box {box + 1}:{node.msg}'  # maybe node.action?
            if last_item_index == -1:
                node_strings[i] += '}'
            for j, button in enumerate(node.button_list):
                box_text = f'<f{j + 1}>{box + 1}.{j + 1}:{button}'
                if j == 0:
                    node_strings[i] += f'|{{{box_text}'
                    if j == last_item_index:
                        node_strings[i] += '}}'
                        break
                elif j == last_item_index:
                    node_strings[i] += f'|{box_text}}}}}'
                else:
                    node_strings[i] += f'|{box_text}'
        return list(zip(box_strings, node_strings))  # [('box0', '{<f0> Box 1 |{<f1>1.1|<f2>1.2|<f3>1.3}}')]
