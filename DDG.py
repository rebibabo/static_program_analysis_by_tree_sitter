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
            print(f"defs: {defs}")
            print(f"uses: {uses}")
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
                            is_arrival = True
                            for n in path[1:-1]:
                                node = cfg.id_to_nodes[n]
                                if X in node.defs:
                                    is_arrival = False
                                    break
                            if not is_arrival:
                                break
                            edge.setdefault((d, u), set())
                            edge[(d, u)].add(X)
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
                            is_arrival = True
                            for n in path[1:-1]:
                                node = cfg.id_to_nodes[n]
                                if X in node.defs:
                                    is_arrival = False
                                    break
                            if not is_arrival:
                                break
                            edge.setdefault((u, d), set())
                            edge[(u, d)].add(X)
            # def X to def Y
            for X in defs:
                def_ = defs[X]
                for d1 in def_:
                    for d2 in def_:
                        paths = cfg.findAllPath(d1, d2)
                        for path in paths:
                            is_arrival = True
                            for n in path[1:-1]:
                                node = cfg.id_to_nodes[n]
                                if X in node.defs:
                                    is_arrival = False
                                    break
                            if not is_arrival:
                                break
                            edge.setdefault((d1, d2), set())
                            edge[(d1, d2)].add(X)
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
    code = r'{}'.format(open('test.c', 'r', encoding='utf-8').read())
    ddg = DDG('c')
    ddg.see_ddg(code ,view=True)