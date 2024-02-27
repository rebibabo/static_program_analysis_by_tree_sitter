from CFG import *
from utils import *
from graphviz import Graph

class DDG(CFG):
    def construct_ddg(self, code):
        # 参考https://home.cs.colorado.edu/~kena/classes/5828/s99/lectures/lecture25.pdf 中19页的算法
        if self.check_syntax(code):
            print('Syntax Error')
            exit(1)
        cfgs = self.see_cfg(code)
        self.ddgs = []
        for cfg in cfgs:
            edge = {} 
            ddg = {}
            defs = cfg.defs
            uses = cfg.uses
            # There is a data dependence from X to Y with respect to a variable v iff 
            # there is a non-null path p from X to Y with no intervening definition of v either:
            #   X contains a definition of v and Y a use of v;
            #   X contains a use of v and Y a definition of v; or
            #   X contains a definition of v and Y a definition of v

            # def X to use Y
            for X in defs:
                if X not in uses:
                    continue
                def_ = defs[X]
                use_ = uses[X]
                for d in def_:
                    for u in use_:
                        paths = cfg.findAllPath(d, u)
                        for path in paths:
                            for n in path:
                                node = cfg.id_to_nodes[n]
                                if X in node.defs:
                                    break
                            edge.setdefault((d, u), [])
                            edge[(d, u)].append(X)
            # use X to def Y
            for X in uses:
                if X not in defs:
                    continue
                use_ = uses[X]
                def_ = defs[X]
                for u in use_:
                    for d in def_:
                        paths = cfg.findAllPath(u, d)
                        for path in paths:
                            for n in path:
                                node = cfg.id_to_nodes[n]
                                if X in node.defs:
                                    break
                            edge.setdefault((u, d), [])
                            edge[(u, d)].append(X)
            # def X to def Y
            for X in defs:
                def_ = defs[X]
                for d1 in def_:
                    for d2 in def_:
                        paths = cfg.findAllPath(d1, d2)
                        for path in paths:
                            for n in path:
                                node = cfg.id_to_nodes[n]
                                if X in node.defs:
                                    break
                            edge.setdefault((d1, d2), [])
                            edge[(d1, d2)].append(X)
            for (u, v), Xs in edge.items():
                ddg.setdefault(u, [])
                ddg[u].append(Edge(v, type='DDG', token=Xs))
            cfg.edges = ddg
            self.ddgs.append(cfg)
        return self.ddgs

    def see_ddg(self, code, filename='DDG', pdf=True, view=False):
        self.construct_ddg(code)
        dot = Digraph(comment=filename, strict=True)
        for ddg in self.ddgs:
            for node in ddg.nodes:
                label = f"<({node.type}, {html.escape(node.text)})<SUB>{node.line}</SUB>>"
                if node.is_branch:
                    dot.node(str(node.id), shape='diamond', label=label, fontname='fangsong')
                elif node.type == 'function_definition':
                    dot.node(str(node.id), label=label, fontname='fangsong')
                else:
                    dot.node(str(node.id), shape='rectangle', label=label, fontname='fangsong')
            for v in ddg.edges:
                for u in ddg.edges[v]:
                    dot.edge(str(v), str(u.id), label=', '.join(u.token), style='dotted')
        if pdf:
            dot.render(filename, view=view, cleanup=True)

if __name__ == '__main__':
    code = '''
int main( )
{
    long a,b,c,d,e,x;
    printf("请输入 5 位数字：");
    scanf("%ld",&x);
    a=x/10000;        /*分解出万位*/
    b=x%10000/1000;   /*分解出千位*/
    c=x%1000/100;     /*分解出百位*/
    d=x%100/10;       /*分解出十位*/
    e=x%10;           /*分解出个位*/
    if (a!=0){
        printf("为 5 位数,逆序为： %ld %ld %ld %ld %ld\n",e,d,c,b,a);
    } else if(b!=0) {
         printf("为 4 位数,逆序为： %ld %ld %ld %ld\n",e,d,c,b);
    } else if(c!=0) {
         printf("为 3 位数,逆序为：%ld %ld %ld\n",e,d,c);
    } else if(d!=0) {
         printf("为 2 位数,逆序为： %ld %ld\n",e,d);
    } else if(e!=0) {
         printf("为 1 位数,逆序为：%ld\n",e);
    }
}
    '''
    ddg = DDG('c')
    ddg.see_ddg(code ,view=True)