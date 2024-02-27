import sys
sys.path.append('../AST')
from AST import *

def get_call_nodes(node):
    # 找到node节点中的所有函数调用节点并返回
    call_nodes = []
    if node.child_count == 0:
        return call_nodes
    for child in node.children:
        if child.type == 'call_expression':
            call_nodes.append(child)
        else:
            call_nodes.extend(get_call_nodes(child))
    return call_nodes

class Function:
    def __init__(self, name, type, parametre, id):
        self.name = name
        self.type = type
        self.parametre = parametre
        self.id = id

def get_func_info(node):
    func_name = text(node.child_by_field_name('declarator').child_by_field_name('declarator'))
    func_type = text(node.child_by_field_name('type'))
    func_parametre = text(node.child_by_field_name('declarator').child_by_field_name('parameters'))
    func_id = node.start_point[0]   # 用行号唯一标识函数的id
    return Function(func_name, func_type, func_parametre, func_id)

class CG(AST):
    def __init__(self, language):
        super().__init__(language)
        self.node_set = {}  # 存放每一个节点的信息
        self.cg = []  # 存放每一个函数的CFG图
        self.funcs = {}

    def create_cg(self, root_node):
        func_def_nodes = {}  
        for child in root_node.children:    # 先找到所有的函数定义节点
            if child.type == 'function_definition':
                func_info = get_func_info(child)
                func_def_nodes[func_info.name] = child
                self.funcs[func_info.name] = func_info
        for node in func_def_nodes: # 再依次遍历每一个函数中调用的函数
            func_node = func_def_nodes[node]
            call_nodes = get_call_nodes(func_node)
            cg_call_nodes = []
            for call_node in call_nodes:
                call_name = text(call_node.child_by_field_name('function'))
                if call_name in func_def_nodes:
                    cg_call_nodes.append(self.funcs[call_name].id)
            self.cg.append((get_func_info(func_node), cg_call_nodes))
        return self.cg

    def see_cg(self, code, filename='CG', pdf=True, view=False):
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        CG = self.create_cg(root_node)
        dot = Digraph(comment=filename)
        for node in CG:
            dot.node(str(node[0].id), shape='rectangle', label=node[0].name, fontname='fangsong')
            for call_node in node[1]:
                dot.edge(str(node[0].id), str(call_node))
        if pdf:
            dot.render(filename, view=view, cleanup=True)
            

if __name__ == '__main__':
    code = '''
    int foo(int a);
    int foo(int a){
        return a;
    }
    int bar(int b){
        foo(b);
        for (int i=0;i<2;i++)
            bar(b);
        return b;
    }
    int main(){
        foo(a);
        bar(b);
    }
    '''
    cg = CG('c')
    cg.see_cg(code, view=True)
