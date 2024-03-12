text = lambda node: node.text.decode('utf-8')
from graphviz import Digraph

class Node:
    def __init__(self, node):
        self.line = node.start_point[0] + 1
        self.type = node.type
        self.id = hash((node.start_point, node.end_point)) % 1000000
        # self.id = node.start_point[0] + 1
        self.is_branch = False
        if node.type == 'function_definition':
            self.text = text(node.child_by_field_name('declarator').child_by_field_name('declarator'))  # 函数名
        elif node.type in ['if_statement', 'while_statement', 'for_statement', 'switch_statement']:
            if node.type == 'if_statement':
                body = node.child_by_field_name('consequence')
            else:
                body = node.child_by_field_name('body')
            node_text = ''
            for child in node.children:
                if child == body:
                    break
                node_text += text(child)
            self.text = node_text
            if node.type != 'switch_statement':
                self.is_branch = True
        elif node.type == 'do_statement':
            self.text = f'while{text(node.child_by_field_name("condition"))}'
            self.is_branch = True
        elif node.type == 'case_statement':
            node_text = ''
            for child in node.children:
                if child.type == ':':
                    break
                node_text += ' ' + text(child)
            self.text = node_text
            self.is_branch = True
        else:
            self.text = text(node)
        defs, uses = self.get_def_use_info(node)
        self.defs = defs
        self.uses = uses

    def get_all_identifier(self, node):
        ids = []
        def help(node):
            # 获取所有的变量名
            if node is None:
                return
            if node.type == 'identifier' and node.parent.type not in ['call_expression']:
                ids.append(text(node))
            for child in node.children:
                help(child)
        help(node)
        return ids

    def get_def_id(self, node):
        update_ids, assignment_ids = [], []
        def help(node):
            if node.type == 'update_expression':
                update_ids.append(text(node.child_by_field_name('argument')))
            if node.type == 'assignment_expression':
                assignment_ids.append(text(node.child_by_field_name('left')))
            for child in node.children:
                help(child)
        help(node)
        return update_ids, assignment_ids

    def get_node_def_use(self, node):
        uses = self.get_all_identifier(node)
        update_ids, assignment_ids = self.get_def_id(node)
        uses = list(set(uses) - set(assignment_ids) | set(update_ids))
        return update_ids + assignment_ids, uses

    def get_def_use_info(self, node):
        # 获取变量的定义信息
        defi, uses = [], []
        if node.type == 'function_definition':
            defi = self.get_all_identifier(node.child_by_field_name('declarator').child_by_field_name('parameters'))
        elif node.type == 'expression_statement':
            node = node.children[0]
            if node.type == 'call_expression':   # scanf语句
                if text(node.child_by_field_name('function')) == 'scanf':
                    arguments = node.child_by_field_name('arguments')
                    defi = self.get_all_identifier(arguments)
                else:
                    d, u = self.get_def_use_info(node)
                    defi.extend(d)
                    uses.extend(u)
            elif node.type == 'assignment_expression':  # a += b
                d = text(node.child_by_field_name('left'))
                op = text(node.children[1])
                u = self.get_all_identifier(node.child_by_field_name('right'))
                if op != '=':
                    u.append(d)
                defi.append(d)
                uses = u
            elif node.type == 'update_expression':  # a++;
                d = text(node.child_by_field_name('argument'))
                defi.append(d)
                uses.append(d)
            else:
                d, u = self.get_def_use_info(node)
                defi.extend(d)
                uses.extend(u)
        elif 'declaration' in node.type:
            defi.extend(self.get_all_identifier(node))
        elif 'declarator' in node.type:
            d = text(node.child_by_field_name('declarator'))
            u = self.get_all_identifier(node) 
            defi.append(d)
            uses = [i for i in u if i != d]
        elif node.type in ['if_statement', 'while_statement', 'do_statement', 'switch_statement']:
            condition = node.child_by_field_name('condition')
            d2, u2 = self.get_node_def_use(condition)
            defi.extend(d2)
            uses.extend(u2)
        elif node.type == 'for_statement':
            initializer = node.child_by_field_name('initializer')
            condition = node.child_by_field_name('condition')
            update = node.child_by_field_name('update')
            d1, u1 = self.get_node_def_use(initializer)
            d2, u2 = self.get_node_def_use(condition)
            d3, u3 = self.get_node_def_use(update)
            defi.extend(d1 + d2 + d3)
            uses.extend(u1 + u2 + u3)
        else:
            d, u = self.get_node_def_use(node)
            defi.extend(d)
            uses.extend(u)
        defi = list(set(defi))
        uses = list(set(uses))
        return defi, uses

class Edge:
    def __init__(self, id, label='', type='', token=[]):
        self.id = id
        self.label = label
        self.type = type  # CDG/DDG
        self.token = token # DDG的变量名

class Graph:
    def __init__(self):
        self.nodes = set()
        self.edges = {}
        self.prev_nodes = {}
        self.id_to_nodes = {}
        self.r = self.Exit = None
        self.defs = {}  # 存放每一个函数的变量定义信息
        self.uses = {}  # 存放每一个函数的变量使用信息

    def add_edge(self, edge):
        node = edge[0]
        edges = edge[1]
        self.nodes.add(node)
        self.id_to_nodes[node.id] = node
        self.edges.setdefault(node.id, [])
        for prev_node, label in edges:
            self.edges.setdefault(prev_node, [])
            self.edges[prev_node].append(Edge(node.id, label))

    def see_graph(self):
        dot = Digraph(comment='CFG', strict=True)
        for node, edges in self.edges.items():
            for next_node in edges:
                left = 'Exit' if node == self.Exit else str(node)
                right = 'r' if next_node.id == self.r else str(next_node.id)
                dot.edge(left, right)
        dot.view()

    def reverse(self):
        # 返回反向的CFG图，添加了Exit节点
        E = {}
        V = set()
        for node, edges in self.edges.items():
            V.add(node)
            if self.id_to_nodes[node].type == 'function_definition':    # 函数入口
                self.r = node
                self.Exit = -node
                V.add(-node)    # 增加一个Exit节点，该节点的id为函数节点的相反数
                E[self.Exit] = [Edge(self.r)]  # 将Exit节点连接到函数节点
        for node, edges in self.edges.items():
            if edges == [] or (len(edges) == 1 and edges[0].label == 'Y'):  # 没有出节点或者出节点只有一个且是Y（没有N）
                E[self.Exit].append(Edge(node))   # 将Exit节点连接到没有出节点的节点
            for edge in edges:
                # node -> edge.id 变成 edge.id -> node
                E.setdefault(edge.id, [])
                E[edge.id].append(Edge(node))
        self.nodes = V
        self.edges = E
        return self

    def Adj(self, node):
        adjs = []
        if node in self.edges:
            for edge in self.edges[node]:
                adjs.append(edge.id)
        return adjs

    def get_def_use_info(self):
        for node in self.nodes:
            for each in node.defs:
                self.defs.setdefault(each, [])
                self.defs[each].append(node.id)
            for each in node.uses:
                self.uses.setdefault(each, [])
                self.uses[each].append(node.id)

    def findAllPath(self, start, end):
        # 算法参考：https://zhuanlan.zhihu.com/p/84437102
        # 输入两点，输出所有的路径列表
        paths, s1, s2 = [], [], []  # 存放所有路径，主栈，辅助栈
        s1.append(start)    
        s2.append(self.Adj(start))
        while s1:   # 主栈不为空
            s2_top = s2[-1]
            if s2_top:  # 邻接节点列表不为空
                s1.append(s2_top[0])    # 将邻接节点列表首个元素添加到主栈
                s2[-1] = s2_top[1:]     # 将辅助栈的邻接节点列表首个元素删除
                temp = []               # 建栈，需要判断邻接节点是否在主栈中
                for each in self.Adj(s2_top[0]):
                    if each not in s1:
                        temp.append(each)
                s2.append(temp)
            else:   # 削栈
                s1.pop()
                s2.pop()
                continue
            if s1[-1] == end:   # 找到一条路径
                paths.append(s1.copy())
                s1.pop()    # 回溯
                s2.pop()
        return paths