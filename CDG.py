from CFG import *
from utils import *
from graphviz import Graph

class Tree:
    def __init__(self, V, children, root):  # 输入节点集合，children为字典，key为节点，value为子节点列表，根节点
        self.vertex = V
        self.children = children
        self.root = root
        self.parent = {}
        for node in children:   # 初始化parent字典
            for each in children[node]:
                self.parent[each] = node
        self.parent[root] = root
        for v in V:
            if v not in self.children:
                self.children[v] = []
        self.depth = self.get_nodes_depth(root, {root:0})    

    def get_nodes_depth(self, root, depth):
        # 递归计算每个节点的深度
        for child in self.children[root]:
            depth[child] = depth[root] + 1
            depth = self.get_nodes_depth(child, depth)
        return depth

    def get_lca(self, a, b):
        # 计算a,b的最近公共祖先
        if self.depth[a] > self.depth[b]:
            diff = self.depth[a] - self.depth[b]
            while diff > 0:
                a = self.parent[a]
                diff -= 1
        elif self.depth[a] < self.depth[b]:
            diff = self.depth[b] - self.depth[a]
            while diff > 0:
                b = self.parent[b]
                diff -= 1
        while a != b:
            a = self.parent[a]
            b = self.parent[b]
        return a

    def reset_by_parent(self):
        # 根据parent字典重置children字典
        self.children = {v:[] for v in self.vertex}
        for node in self.parent:
            if node != self.parent[node]:
                self.children[self.parent[node]].append(node)

    def see_tree(self):
        dot = Graph(comment='Tree')
        for node in self.vertex:
            dot.node(str(node), shape='rectangle', label=str(node), fontname='fangsong')
        for node in self.children:
            for child in self.children[node]:
                dot.edge(str(node), str(child))
        dot.view()

class CDG(CFG):
    def get_subTree(self, cfg):
        # 按照广度优先遍历，找出一个子树
        V, E, Exit, r = cfg.nodes, cfg.edges, cfg.Exit, cfg.r
        visited = {v:False for v in V}
        queue = [Exit]
        visited[Exit] = True
        subTree = {}
        while queue:
            node = queue.pop()
            if node not in E:
                continue
            for edge in E[node]:
                v = edge.id
                if not visited[v]:
                    queue.append(v)
                    visited[v] = True
                    subTree.setdefault(node, [])
                    subTree[node].append(v)
        return subTree
        
    def get_prev(self, cfgs):
        # 计算每个节点的前驱节点
        prev = {}
        for cfg in cfgs:
            for node, edges in cfg.edges.items():
                prev.setdefault(node, [])
                for next_node in edges:
                    prev.setdefault(next_node.id, [])
                    prev[next_node.id].append(node)
        return prev

    def post_dominator_tree(self, cfgs, prev):
        # 生成后支配树
        PDT = []
        for cfg in cfgs:    # 遍历每一个函数的CFG
            subTree = self.get_subTree(cfg)   # 找出一个子树
            V, root = cfg.nodes, cfg.Exit
            tree = Tree(V, subTree, root)  # 生成树
            changed = True
            while changed:
                changed = False
                for v in V: # dominator tree算法
                    if v != root:
                        for u in prev[v]:
                            parent_v = tree.parent[v]
                            if u != parent_v and parent_v != tree.get_lca(u, parent_v):
                                tree.parent[v] = tree.get_lca(u, parent_v)
                                changed = True
            tree.reset_by_parent()  # 根据parent字典重置children字典
            PDT.append(tree)
        return PDT

    def dominance_frontier(self, code):
        # 输入代码，返回CFG和支配边界
        cfgs = self.see_cfg(code)
        reverse_cfgs = [cfg.reverse() for cfg in cfgs]  # 计算逆向CFG
        prev = self.get_prev(reverse_cfgs)  # 计算每个节点的前驱节点
        PDT = self.post_dominator_tree(reverse_cfgs, prev)  # 输入逆向CFG，输出后支配树
        DF = []
        for cfg, tree in zip(reverse_cfgs, PDT):
            V = cfg.nodes
            DF.append({v:[] for v in V})
            for v in V:
                if len(prev[v]) > 1:
                    for p in prev[v]:
                        runner = p
                        while runner != tree.parent[v]:
                            DF[-1][runner].append(v)
                            runner = tree.parent[runner]
        return cfgs, DF

    def construct_cdg(self, code):
        # 输入代码，返回CDG
        cfgs, DF = self.dominance_frontier(code)
        self.cdgs = []
        for cfg, df in zip(cfgs, DF):
            for v in df:
                df[v] = [Edge(u, type='CDG') for u in df[v]]
            cfg.edges = df
            self.cdgs.append(cfg)
        return self.cdgs

    def see_cdg(self, code, filename='CDG', pdf=True, view=False):
        self.construct_cdg(code)
        dot = Digraph(comment=filename, strict=True)
        for cdg in self.cdgs:
            for v in cdg.edges:
                if v < 0:
                    continue
                node = cdg.id_to_nodes[v]
                label = f"<({node.type}, {html.escape(node.text)})<SUB>{node.line}</SUB>>"
                if node.is_branch:
                    dot.node(str(node.id), shape='diamond', label=label, fontname='fangsong')
                elif node.type == 'function_definition':
                    dot.node(str(node.id), label=label, fontname='fangsong')
                else:
                    dot.node(str(node.id), shape='rectangle', label=label, fontname='fangsong')
                for u in cdg.edges[v]:
                    dot.edge(str(u.id), str(v))
        if pdf:
            dot.render(filename, view=view, cleanup=True)

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
    cdg = CDG('c')
    # cdg.see_cfg(code, view=True)
    cdg.see_cdg(code, view=True)

