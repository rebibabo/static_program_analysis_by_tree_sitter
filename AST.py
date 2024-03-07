from tree_sitter import Parser, Language
from graphviz import Digraph
import os

text = lambda node: node.text.decode('utf-8')

class Node:
    '''用于存储AST树的节点信息，将tree-sitter.Node类型转换为Node类型，tree-sitter不能序列化'''
    def __init__(self, node, id):
        self.type = node.type
        self.start_byte = node.start_byte
        self.end_byte = node.end_byte
        self.start_point = node.start_point
        self.end_point = node.end_point
        self.text = text(node)
        self.id = id

    def __eq__(self, other):
        return self.id == other.id

class TreeNode:
    '''用于存储AST树'''
    def __init__(self, root):
        '''输入: root，树的根节点，为tree-sitter.Node类型'''
        self.nodes = [Node(root, 0)]
        self.id_to_node = {0: root}
        self.edges = {}
        self.traverse_tree(root)

    def traverse_tree(self, node, pid=0):     # python递归函数想要修改函数参数的值，只能通过列表等方式
        '''输入: node，当前节点，为tree-sitter.Node类型'''
        children = []
        for child in node.children:
            id = len(self.nodes)    # 唯一标记节点的id
            child_node = Node(child, id)    
            self.nodes.append(child_node)
            self.id_to_node[id] = child_node
            children.append(id)
            self.traverse_tree(child, id)
        self.edges[pid] = children

    def print_tree(self):
        '''打印AST树'''
        def dfs(node, depth):
            if self.edges[node.id] == [] and node.type != node.text:
                print('   ' * depth + node.type + ': ' + node.text)
            else:
                print('   ' * depth + node.type)
            for child in self.edges[node.id]:
                dfs(self.nodes[child], depth + 1)
        dfs(self.nodes[0], 0)

    def get_node(self, id):
        return self.id_to_node[id]

class AST:
    def __init__(self, language):
        self.language = language
        if not os.path.exists(f'./build/{language}-languages.so'):
            if not os.path.exists(f'./tree-sitter-{language}'):
                os.system(f'git clone https://github.com/tree-sitter/tree-sitter-{language}')
            Language.build_library(
                f'./build/{language}-languages.so',
                [
                    f'./tree-sitter-{language}',
                ]
            )
        LANGUAGE = Language(f'./build/{language}-languages.so', language)
        parser = Parser()
        parser.set_language(LANGUAGE)
        self.parser = parser

    def see_tree(self, code, filename='ast_tree', pdf=True, view=False):
        '''
        生成AST树的可视化图
        code: 输入的代码
        filename: 生成的文件名
        pdf: 是否生成pdf文件
        view: 是否打开pdf文件
        '''
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        tree = TreeNode(root_node)
        dot = Digraph(comment='AST Tree', strict=True)
        for edge, children in tree.edges.items():
            node = tree.get_node(edge)
            dot.node(str(edge), shape='rectangle', label=node.type, fontname='fangsong')
            dot.edges([(str(edge), str(child)) for child in children])
            if children == []:
                dot.node(str(-edge), shape='ellipse', label=node.text, fontname='fangsong')
                dot.edges([(str(edge), str(-edge))])
        if pdf:
            dot.render(filename, view=view, cleanup=True)

    def tokenize(self, code):
        '''输入代码code，返回token列表'''
        def tokenize_help(node, tokens):
            # 遍历整个AST树，返回符合func的节点列表results
            if not node.children:
                tokens.append(text(node))
                return
            for n in node.children:
                tokenize_help(n, tokens)
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        print(type(root_node))
        tokens = []
        tokenize_help(root_node, tokens)
        return tokens

    def check_syntax(self, code):
        '''检查代码是否有语法错误'''
        tree = self.parser.parse(bytes(code, 'utf8'))
        # 找出来Error的位置
        root_node = tree.root_node
        error_nodes = []
        def find_error(node):
            if node.type == 'ERROR':
                error_nodes.append(node)
            for child in node.children:
                find_error(child)
        find_error(root_node)
        for i, node in enumerate(error_nodes):
            print(f"error {i:>3} : line {node.start_point[0]:>3} row {node.start_point[1]:>3} -to- line {node.end_point[0]:>3} row {node.end_point[1]:>3}")
        return tree.root_node.has_error

if __name__ == '__main__':
    code = r'{}'.format(open('test.c', 'r', encoding='utf-8').read())
    ast = AST('cpp')
    print(ast.tokenize(code))
    ast.see_tree(code, view=True)
    # node = Node(1, 0, 'A', 0, 0, 0, 0, 'A')
    # print(node())