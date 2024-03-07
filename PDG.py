from utils import *
from CFG import *
from CDG import *
from DDG import *
from graphviz import Digraph

class PDG(CFG):
    def construct_pdg(self, code):
        cdg = CDG(self.language)
        ddg = DDG(self.language)
        cdg.construct_cdg(code)
        ddg.construct_ddg(code)
        self.pdgs = []
        for cdg, ddg in zip(cdg.cdgs, ddg.ddgs):
            pdg = cdg
            for node, edges in ddg.edges.items():
                pdg.edges.setdefault(node, [])
                for edge in edges:
                    pdg.edges[node].append(edge)
            self.pdgs.append(pdg)
        return self.pdgs

    def see_pdg(self, code, filename='PDG', pdf=True, view=False):
        self.construct_pdg(code)
        dot = Digraph(comment='PDG', strict=True)
        for pdg in self.pdgs:
            for v in pdg.nodes:
                if v < 0:
                    continue
                node = pdg.id_to_nodes[v]
                label = f"<({node.type}, {html.escape(node.text)})<SUB>{node.line}</SUB>>"
                if node.is_branch:
                    dot.node(str(node.id), shape='diamond', label=label, fontname='fangsong')
                elif node.type == 'function_definition':
                    dot.node(str(node.id), label=label, fontname='fangsong')
                else:
                    dot.node(str(node.id), shape='rectangle', label=label, fontname='fangsong')
                for u in pdg.edges[v]:
                    dot.edge(str(u.id), str(v))
            for v in pdg.edges:
                for u in pdg.edges[v]:
                    if u.type == 'DDG':
                        dot.edge(str(v), str(u.id), label=', '.join(u.token), style='dotted')
                    else:
                        dot.edge(str(u.id), str(v))
        if pdf:
            dot.render(filename, view=view, cleanup=True)

if __name__ == '__main__':
    code = r'{}'.format(open('test.c', 'r', encoding='utf-8').read())
    pdg = PDG('c')
    pdg.see_pdg(code, view=True)