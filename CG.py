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
    func_type = text(node.child_by_field_name('type'))
    func_id = node.start_point[0]   # 用行号唯一标识函数的id
    while node.type != 'function_declarator':
        node = node.child_by_field_name('declarator')
    func_name = text(node.child_by_field_name('declarator'))
    func_parametre = text(node.child_by_field_name('parameters'))
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
            cg_call_nodes = set()
            for call_node in call_nodes:
                call_name = text(call_node.child_by_field_name('function'))
                if call_name in func_def_nodes:
                    cg_call_nodes.add(self.funcs[call_name].id)
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
void insertEle(struct QuadTreeNode *node, struct ElePoint ele) { 
    if (1 == node->is_leaf) {
        if (node->ele_num + 1 > MAX_ELE_NUM) {
            splitNode(node);
            insertEle(node, ele); 
        } else {
            struct ElePoint *ele_ptr = (struct ElePoint *) malloc(sizeof(struct ElePoint));
            ele_ptr->lat = ele.lat;
            ele_ptr->lng = ele.lng;
            strcpy(ele_ptr->desc, ele.desc);
            node->ele_list[node->ele_num] = ele_ptr;
            node->ele_num++;
        }
 
        return; 
    } 

    double mid_vertical = (node->region.up + node->region.bottom) / 2;
    double mid_horizontal = (node->region.left + node->region.right) / 2;
    if (ele.lat > mid_vertical) {
        if (ele.lng > mid_horizontal) {
            insertEle(node->RU, ele);
        } else {
            insertEle(node->LU, ele);
        }
    } else {
        if (ele.lng > mid_horizontal) {
            insertEle(node->RB, ele);
        } else {
            insertEle(node->LB, ele);
        }
    }
}

void splitNode(struct QuadTreeNode *node) {
    double mid_vertical = (node->region.up + node->region.bottom) / 2;
    double mid_horizontal = (node->region.left + node->region.right) / 2;

    node->is_leaf = 0;
    node->RU = createChildNode(node, mid_vertical, node->region.up, mid_horizontal, node->region.right);
    node->LU = createChildNode(node, mid_vertical, node->region.up, node->region.left, mid_horizontal);
    node->RB = createChildNode(node, node->region.bottom, mid_vertical, mid_horizontal, node->region.right);
    node->LB = createChildNode(node, node->region.bottom, mid_vertical, node->region.left, mid_horizontal);

    for (int i = 0; i < node->ele_num; i++) {
        insertEle(node, *node->ele_list[i]);
        free(node->ele_list[i]);
        node->ele_num--;
    }
}

struct QuadTreeNode *createChildNode(struct QuadTreeNode *node, double bottom, double up, double left, double right) {
    int depth = node->depth + 1;
    struct QuadTreeNode *childNode = (struct QuadTreeNode *) malloc(sizeof(struct QuadTreeNode));
    struct Region *region = (struct Region *) malloc(sizeof(struct Region));
    initRegion(region, bottom, up, left, right);
    initNode(childNode, depth, *region);

    return childNode;
}

void queryEle(struct QuadTreeNode node, struct ElePoint ele) {
    if (node.is_leaf == 1) {
        for (int j = 0; j < node.ele_num; j++) {
            printf("%f,%f\n", node.ele_list[j]->lng, node.ele_list[j]->lat);
        }
        return;
    }

    double mid_vertical = (node.region.up + node.region.bottom) / 2;
    double mid_horizontal = (node.region.left + node.region.right) / 2;

    if (ele.lat > mid_vertical) {
        if (ele.lng > mid_horizontal) {
            queryEle(*node.RU, ele);
        } else {
            queryEle(*node.LU, ele);
        }
    } else {
        if (ele.lng > mid_horizontal) {
            queryEle(*node.RB, ele);
        } else {
            queryEle(*node.LB, ele);
        }
    }
}

void initNode(struct QuadTreeNode *node, int depth, struct Region region) {
    node->depth = depth;
    node->is_leaf = 1;
    node->ele_num = 0;
    node->region = region;
}

void initRegion(struct Region *region, double bottom, double up, double left, double right) {
    region->bottom = bottom;
    region->up = up;
    region->left = left;
    region->right = right;
}

int main() {
    struct QuadTreeNode root;
    struct Region root_region;

    struct ElePoint ele;
    initRegion(&root_region, -90, 90, -180, 180);
    initNode(&root, 1, root_region);

    srand((int)time(NULL));
    for (int i = 0; i < 100000; i++) {
        ele.lng = (float)(rand() % 360 - 180 + (float)(rand() % 1000) / 1000);
        ele.lat = (float)(rand() % 180 - 90 + (float)(rand() % 1000) / 1000);
        insertEle(&root, ele);
    }

    struct ElePoint test;
    test.lat = -24;
    test.lng = -45.4;
    queryEle(root, test);
}
    '''
    cg = CG('c')
    cg.see_cg(code, view=True)
