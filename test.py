def detect_cycles(graph):
    visited = set()
    stack = []
    cycles = []

    def dfs(node):
        if node in stack:
            cycle = stack[stack.index(node):]
            cycles.append(cycle)
            return
        if node in visited:
            return

        visited.add(node)
        stack.append(node)

        for neighbor in graph.get(node, []):
            dfs(neighbor)

        stack.pop()

    for node in graph:
        dfs(node)

    return cycles

# 字典表示的图，键是文件名，值是包含的文件列表
file_graph = {
    '3rd/lua/lapi.c': ['3rd/lua/lapi.h', '3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lgc.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h', '3rd/lua/ltm.h', '3rd/lua/lvm.h'],
    '3rd/lua/lapi.h': ['3rd/lua/lstate.h'],
    '3rd/lua/lcode.c': ['3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lgc.h', '3rd/lua/lstring.h', '3rd/lua/lvm.h'],
    '3rd/lua/ldebug.c': ['3rd/lua/lapi.h', '3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h', '3rd/lua/ltm.h', '3rd/lua/lvm.h'],
    '3rd/lua/ldebug.h': ['3rd/lua/lstate.h'],
    '3rd/lua/ldo.c': ['3rd/lua/lapi.h', '3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lgc.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h', '3rd/lua/ltm.h', '3rd/lua/lvm.h'],
    '3rd/lua/ldo.h': ['3rd/lua/lstate.h'],
    '3rd/lua/ldump.c': ['3rd/lua/lstate.h'],
    '3rd/lua/lfunc.c': ['3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lgc.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h'],
    '3rd/lua/lgc.c': ['3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lgc.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h', '3rd/lua/ltm.h'],
    '3rd/lua/lgc.h': ['3rd/lua/lstate.h'],
    '3rd/lua/llex.c': ['3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lgc.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h'],
    '3rd/lua/lmem.c': ['3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lgc.h', '3rd/lua/lstate.h'],
    '3rd/lua/lobject.c': ['3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h', '3rd/lua/lvm.h'],
    '3rd/lua/lparser.c': ['3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h'],
    '3rd/lua/lstate.c': ['3rd/lua/lapi.h', '3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lgc.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h', '3rd/lua/ltm.h'],
    '3rd/lua/lstate.h': ['3rd/lua/ltm.h'],
    '3rd/lua/lstring.c': ['3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h'],
    '3rd/lua/lstring.h': ['3rd/lua/lgc.h', '3rd/lua/lstate.h'],
    '3rd/lua/ltable.c': ['3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lgc.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h', '3rd/lua/lvm.h'],
    '3rd/lua/ltests.c': ['3rd/lua/lapi.h', '3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h'],
    '3rd/lua/ltm.c': ['3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lgc.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h', '3rd/lua/ltm.h', '3rd/lua/lvm.h'],
    '3rd/lua/ltm.h': ['3rd/lua/lstate.h'],
    '3rd/lua/luac.c': ['3rd/lua/ldebug.h', '3rd/lua/lstate.h'],
    '3rd/lua/lundump.c': ['3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lstring.h'],
    '3rd/lua/lvm.c': ['3rd/lua/ldebug.h', '3rd/lua/ldo.h', '3rd/lua/lgc.h', '3rd/lua/lstate.h', '3rd/lua/lstring.h', '3rd/lua/ltm.h', '3rd/lua/lvm.h'],
    '3rd/lua/lvm.h': ['3rd/lua/ldo.h', '3rd/lua/ltm.h'],
    'A': ['B'],
    'B': ['C'],
    'C': ['A']
}


cycle = detect_cycles(file_graph)
if cycle:
    print("存在环路:", cycle)
else:
    print("不存在环路")
