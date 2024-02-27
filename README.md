这是一个基于tree-sitter编译工具进行静态程序分析的demo, 并使用可视化工具graphviz，能够生成抽象语法树AST、控制流图CFG、数据依赖DFG、数据依赖图CDG、程序依赖图PDG、函数调用图CG等。
tree-sitter网址：https://tree-sitter.github.io/tree-sitter/

## 环境配置
确保已经安装了graphviz，在windows上，官网https://www.graphviz.org/ 下载graphviz之后，配置环境变量为安装路径下的bin文件夹，例如D:\graphviz\bin\，注意末尾的'\\'不能省略，如果是linux上，运行下面命令安装：
```
sudo apt-get install graphviz graphviz-doc
```
接着运行
```
pip install -r requirements.txt
```

## 生成AST树
AST.py能够生成AST树以及tokens，首先构造类，参数为代码语言，目前tree-sitter能够编译的语言都能够生成。
```
ast = AST('c')
```
接着运行下面代码可以显示AST树
```
ast.see_tree(code, view=True)
```
![AST](https://github.com/rebibabo/TSA/assets/80667434/6d1aae84-3c46-4978-844e-6006e8623718)

运行完成之后，会在当前目录下生成ast_tree.pdf，为可视化的ast树，可以通过设置参数view=False在生成pdf文件的同时不查看文件，pdf=False不生成可视化的pdf文件，设置参数filename="filename"来更改输出文件的名称。
获得代码的tokens可以运行下面的代码，返回值为token的列表。
```
ast.tokenize(code)
#['int', 'main', '(', ')', '{', 'int', 'abc', '=', '1', ';', 'int', 'b', '=', '2', ';', 'int', 'c', '=', 'a', '+', 'b', ';', 'while', '(', 'i', '<', '10', ')', '{', 'i', '++', ';', '}', '}']
```

## 生成CFG
CFG.py继承自AST类，能够生成控制流图，运行下面命令可以获得代码的CFG：
```
cfg = CFG('c')
cfg.see_cfg(code, view=True)
```
生成的CFG图样例：
![CFG](https://github.com/rebibabo/TSA/assets/80667434/d1c05e69-f1e0-4b59-82c4-1073cbaaf913)
see_cfg的参数和see_tree的参数一样

## 生成CDG
CDG.py继承自CFG类，能够生成控制依赖图，运行下面代码能够获得CDG图：
```
cdg = CDG('c')
cdg.see_cdg(code, view=True)
```
生成的CDG图样例：
![CDG](https://github.com/rebibabo/TSA/assets/80667434/cafe9bed-d65c-4d3d-b948-b8829983258a)


