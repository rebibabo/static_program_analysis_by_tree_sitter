from AST import *
from utils import *
import html

def get_break_continue_node(node):
    # 找到node节点循环中的所有break和continue节点并返回
    break_nodes, continue_nodes = [], []
    for child in node.children:
        if child.type == 'break_statement':
            break_nodes.append(child)
        elif child.type == 'continue_statement':
            continue_nodes.append(child)
        elif child.type not in ['for_statement', 'while_statement']:
            b_node, c_nodes = get_break_continue_node(child)
            break_nodes.extend(b_node)
            continue_nodes.extend(c_nodes)
    return break_nodes, continue_nodes

def get_edge(in_nodes):
    # 输入入节点，返回入边的列表，边为(parent_id, label)
    edge = []     
    for in_node in in_nodes:   
        parent, label = in_node
        parent_id = parent.id
        edge.append((parent_id, label))
    return edge

class CFG(AST):
    def __init__(self, language):
        super().__init__(language)
        self.node_set = {}  # 存放每一个节点的信息
        self.cfgs = []  # 存放每一个函数的CFG图

    def create_cfg(self, node, in_nodes=[()]):
        # 输入当前节点，以及入节点，入节点为(node_info, edge_label)的列表，node_info['id']唯一确定一个节点，edge_label为边的标签
        if node.child_count == 0 or in_nodes == []:   # 如果in_nodes为空，说明没有入节点，跳过
            return [], in_nodes
        if node.type == 'function_definition':      # 如果节点是函数，则创建函数节点，并且递归遍历函数的compound_statement
            body = node.child_by_field_name('body')
            node_info = Node(node)
            CFG, _ = self.create_cfg(body, [(node_info, '')])
            return CFG + [(node_info, [])], []
        elif node.type == 'compound_statement':     # 如果是复合语句，则递归遍历复合语句的每一条statement
            CFG = []
            for child in node.children:
                cfg, out_nodes = self.create_cfg(child, in_nodes)
                CFG.extend(cfg)
                in_nodes = out_nodes
            return CFG, in_nodes
        elif node.type not in ['if_statement', 'while_statement', 'for_statement', 'switch_statement', 'case_statement', 'translation_unit', 'do_statement']:  # 如果是普通的语句
            edge = get_edge(in_nodes)
            node_info = Node(node)
            in_nodes = [(node_info, '')]
            if node.type in ['return_statement', 'break_statement', 'continue_statement']:  # return，break，continue语句没有出节点
                return [(node_info, edge)], []
            else:
                return [(node_info, edge)], in_nodes
        elif node.type == 'if_statement':   # if语句
            CFG = []
            edge = get_edge(in_nodes)
            node_info = Node(node)
            CFG.append((node_info, edge))
            body = node.child_by_field_name('consequence')  # 获取if的主体部分
            cfg, out_nodes = self.create_cfg(body, [(node_info, 'Y')])
            CFG.extend(cfg)
            alternate = node.child_by_field_name('alternative') # 获取else的主体部分，可能是else，也可能是else if
            if alternate:       # if else 或者 if else if
                body = alternate.children[1]
                cfg, al_out_nodes = self.create_cfg(body, [(node_info, 'N')])
                CFG.extend(cfg)
                return CFG, out_nodes + al_out_nodes
            else:               # 只有if
                return CFG, out_nodes + [(node_info, 'N')]
        elif node.type in ['for_statement', 'while_statement']:     # for和while循环
            CFG = []
            edge = get_edge(in_nodes)
            node_info = Node(node)
            CFG.append((node_info, edge))
            body = node.child_by_field_name('body')     # 获取循环主体
            cfg, out_nodes = self.create_cfg(body, [(node_info, 'Y')])
            CFG.extend(cfg)
            for out_node in out_nodes:  # 将循环主体的出节点与循环的开始节点相连
                parent, label = out_node
                parent_id = parent.id
                CFG.append((node_info, [(parent_id, label)]))
            break_nodes, continue_nodes = get_break_continue_node(node)     # 求得循环内的break和continue节点
            out_nodes = [(node_info, 'N')]      # 循环体的出节点开始节点，条件为N
            for break_node in break_nodes:      
                out_nodes.append((Node(break_node), ''))   # 将break节点添加到out_nodes中
            for continue_node in continue_nodes:
                CFG.append((node_info, [(Node(continue_node).id, '')]))     # 将continue节点连接到循环的开始节点
            return CFG, out_nodes
        elif node.type == 'do_statement':   # do while循环
            CFG = []
            edge = get_edge(in_nodes)
            node_info = Node(node)
            body = node.child_by_field_name('body')     # 获取循环主体
            cfg, out_nodes = self.create_cfg(body, [(node_info, '')])
            first_node = cfg[0][0]
            CFG.append((first_node, edge))
            CFG.extend(cfg)
            for out_node in out_nodes:  # 将循环主体的出节点与条件节点相连
                parent, label = out_node
                parent_id = parent.id
                CFG.append((node_info, [(parent_id, label)]))
            CFG.append((first_node, [(node_info.id, 'Y')]))   # 将条件节点连接到循环主体的开始节点
            out_nodes = [(node_info, 'N')]      # 循环体的出节点开始节点，条件为N
            break_nodes, continue_nodes = get_break_continue_node(node)     # 求得循环内的break和continue节点
            for break_node in break_nodes:
                out_nodes.append((Node(break_node), ''))
            for continue_node in continue_nodes:
                CFG.append((node_info, [(Node(continue_node).id, '')]))
            return CFG, out_nodes
        elif node.type == 'switch_statement':   # switch语句
            CFG = []
            edge = get_edge(in_nodes)
            node_info = Node(node)
            CFG.append((node_info, edge))
            body = node.child_by_field_name('body')     # 获取switch的主体部分
            cfg, out_nodes = self.create_cfg(body, [(node_info, '')])   # 递归遍历case语句
            CFG.extend(cfg)
            break_nodes, _ = get_break_continue_node(node)      # 将break语句添加到out_nodes当中
            for break_node in break_nodes:
                out_nodes.append((Node(break_node), ''))
            return CFG, out_nodes
        elif node.type == 'case_statement':     # case语句
            CFG = []
            edge = get_edge(in_nodes)
            node_info = Node(node)
            CFG.append((node_info, edge))
            if node.children[0].type == 'case':     # 如果是case语句
                in_nodes = [(node_info, 'Y')]
                for child in node.children[3:]:
                    cfg, out_nodes = self.create_cfg(child, in_nodes)
                    CFG.extend(cfg)
                    in_nodes = out_nodes
                return CFG, in_nodes + [(node_info, 'N')]
            else:   # default
                in_nodes = [(node_info, '')]
                for child in node.children[2:]:
                    cfg, out_nodes = self.create_cfg(child, in_nodes)
                    CFG.extend(cfg)
                    in_nodes = out_nodes
                return CFG, in_nodes
        else:
            CFGs = []   # 存放每一个函数的CFG图
            for child in node.children:
                if child.type == 'function_definition': # 获得每一个函数的CFG图
                    CFG, out_nodes = self.create_cfg(child, in_nodes)
                    CFGs.append(CFG)
            return CFGs, in_nodes

    def construct_cfg(self, code):
        tree = self.parser.parse(bytes(code, 'utf-8'))
        root_node = tree.root_node
        CFGs, _ = self.create_cfg(root_node)
        for func_cfg in CFGs:
            cfg = Graph()
            for each in func_cfg:
                cfg.add_edge(each)
            cfg.get_def_use_info()
            self.cfgs.append(cfg)

    def see_cfg(self, code, filename='CFG', pdf=True, view=False):
        self.construct_cfg(code)
        dot = Digraph(comment=filename, strict=True)
        for cfg in self.cfgs:
            for node in cfg.nodes:
                label = f"<({node.type}, {html.escape(node.text)})<SUB>{node.line}</SUB>>"
                if node.is_branch:
                    dot.node(str(node.id), shape='diamond', label=label, fontname='fangsong')
                elif node.type == 'function_definition':
                    dot.node(str(node.id), label=label, fontname='fangsong')
                else:
                    dot.node(str(node.id), shape='rectangle', label=label, fontname='fangsong')
            for node, edges in cfg.edges.items():
                for edge in edges:
                    next_node, label = edge.id, edge.label
                    dot.edge(str(node), str(next_node), label=label)
        if pdf:
            dot.render(filename, view=view, cleanup=True)
        return self.cfgs

if __name__ == '__main__':
    code = '''
    int main()
    {  int  a[4][4],b[4][4],i,j;       /*a存放原始数组数据，b存放旋转后数组数据*/
    printf("input 16 numbers: ");
    /*输入一组数据存放到数组a中，然后旋转存放到b数组中*/
    for(i=0;i<4;i++)
        for(j=0;j<4;j++)
        {  scanf("%d",&a[i][j]);
            b[3-j][i]=a[i][j];
            }
    printf("array b:\n");
    for(i=0;i<4;i++)
        {  for(j=0;j<4;j++)
            printf("%6d",b[i][j]);
            printf("\n");
        }
    '''
    cfg = CFG('c')
    # cfg.see_tree(code, view=True)
    cfg.see_cfg(code, view=True)
