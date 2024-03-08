from AST import *
import os
import re

MAX_LENGTH = 1000000    # 最大行数
constant_type = ['number_literal', 'string_literal', 'character_literal', 'preproc_arg', 'true', 'false', 'null']   # 常量类型

def Array(node, type):
    '''
    目的-为了获取int a[m][n];声明中的变量名a和类型int **
    输入-节点node和类型type，例如node: a[m][n], type: int
    输出-变量名和类型，例如a, int**
    '''
    dim = 0
    node_type = node.type
    while node and node.type == node_type:
        dim += 1
        node = node.children[0]
    name = text(node)
    type = f'{type}{"*"*dim}'
    return name, type

def Pointer(node, type):
    '''
    目的-为了获取int *a[m];声明中的变量名a和类型int *
    输入-节点node和类型type，例如node: *a[m], type: int
    输出-变量名和类型，例如a, int**
    '''
    dim = 0
    node_type = node.type
    while node and node.type == node_type:
        dim += 1
        node = node.children[1]
    if node.type == 'array_declarator': # char* argv[]
        while node and node.type == 'array_declarator':
            dim += 1
            node = node.children[0]
    name = text(node)
    type = f'{type}{"*"*dim}'
    return name, type

class Identifier:
    def __init__(self, type, name, domain, structure_, class_):
        self.type = type                # 变量名类型
        self.name = name                # 变量名
        self.domain = domain            # 作用域:[start line, end line]
        self.structure_ = structure_    # 所属结构体名称
        self.class_ = class_            # 所属类名称
    
    def __str__(self):
        str = f'name: {self.name}\ntype: {self.type}\ndomain: {self.domain}\n'
        if self.structure_:
            str += f'structure: {self.structure_}\n'
        if self.class_:
            str += f'class: {self.class_}\n'
        return str

class Declaration:
    def __init__(self, node):
        '''
        目的-获取int a[m], b=0;声明的变量名和类型: {a: int*, b: int}
        输入-节点node，例如int a[m], b=0;
        输出-变量名和类型，例如{a: int*, b: int}
        '''
        self.identifiers = {}
        if node.type not in ['declaration', 'field_declaration', 'parameter_declaration', 'type_definition']:
            return
        type_node = node.child_by_field_name('type') 
        if type_node.type == 'struct_specifier':      # 结构体类型
            self.type = text(type_node.child_by_field_name('name'))
        else:       # 基本类型
            self.type = text(type_node)
        self.identifiers = {}
        if node.type == 'parameter_declaration':    # 获取函数参数的变量名和类型 
            name, type = self.get_name_and_type(node.child_by_field_name('declarator'))
            if name and type:
                self.identifiers[name] = type
        else:
            for child in node.children[1: -1]:
                name, type = self.get_name_and_type(child)  # 获取声明的变量名和类型
                if name and type:
                    self.identifiers[name] = type
        
    def get_name_and_type(self, node):
        '''
        目的-获取以node为根节点的变量名和类型
        输入-节点node，例如int a[m]
        输出-变量名和类型，例如a, int*
        '''
        if node is None:
            return None, None
        if node.type == 'array_declarator':     # 如果是数组
            return Array(node, self.type)
        elif node.type == 'pointer_declarator': # 如果是指针
            return Pointer(node, self.type)
        elif node.type in ['init_declarator', 'parameter_declaration']:     # 如果是初始化声明，还需要遍历declarator
            return self.get_name_and_type(node.child_by_field_name('declarator'))
        elif node.type in ['identifier', 'field_identifier', 'type_identifier']:    # 一般的变量的类型就是self.type
            return text(node), self.type
        else:
            return None, None

    def __call__(self):
        '''return {identifier: type}'''
        return self.identifiers

class Structure:
    def __init__(self, node):
        '''
        目的-获取结构体属性的类型field_vars，以及结构体声明的变量def_vars
        输入-节点node，例如struct A{int a; int b;}a;
        输出-结构体属性的类型field_vars={a:int, b:int}，以及结构体声明的变量def_vars{a:A}
        '''
        self.field_vars = {} 
        self.def_vars = {}
        if node.type != 'struct_specifier':
            print('Error: not a struct_specifier')
            return
        if not node.child_by_field_name('name') and node.type == 'struct_specifier':
            self.name = text(node.parent.child_by_field_name('declarator'))
        else:
            self.name = text(node.child_by_field_name('name'))
            declaration = Declaration(node.parent)
            self.def_vars = declaration()
        body = node.child_by_field_name('body')
        if body:
            for field_declaration in body.children:
                if text(field_declaration) not in ['{', '}']:
                    declaration = Declaration(field_declaration)
                    self.field_vars.update(declaration())

class IdType:
    def __init__(self, file_path):
        self.file_path = file_path
        self.vars = {}  # 存放变量名的定义信息{a: [Identifier, Identifier], b: [Identifier]}
        self.macro = {} # 存放宏定义的类型{ll: long long, ull: unsigned long long}

    def add_def_var(self, identifier, domain, structure_, class_):
        '''
        目的-将声明的变量加入到vars中
        输入-声明的变量identifier，例如{a: int*, b: int}，作用域domain=[start line, end line]， structure_和class_
        '''
        for name, type in identifier.items():
            self.vars.setdefault(name, [])
            self.vars[name].append(Identifier(type, name, domain, structure_, class_))

    def add_macro(self, name, type):
        self.macro[name] = type

    def query_type(self, id, line):
        '''
        目的-查询变量id在line行的类型
        输入-变量id和行号line
        输出-变量id在line行的类型
        '''
        if id not in self.vars:
            return 'unknown'
        match_info = [] # 存放符合作用域的变量信息
        for info in self.vars[id]:
            if info.domain[0] <= line <= info.domain[1]:
                match_info.append(info)
        if not match_info:
            return 'unknown'
        # 将match_info按照domain的长度排序，找出来最局部变量的类型
        match_info.sort(key=lambda x: x.domain[1] - x.domain[0])
        type = match_info[0].type
        dim = type.count('*')
        new_type = type.replace('*', '')
        if new_type in self.macro:
            type = self.macro[new_type] + '*' * dim
        return type

    def __str__(self):
        str = []
        for var, info in self.vars.items():
            str.append(f"{var:=^40}")
            for i in info:
                str.append(i.__str__())
        return '\n'.join(str)

class Func:
    def __init__(self, node, file_path):
        '''
        目的-获取函数的返回类型，函数名，参数类型
        输入-节点node，例如int main(int argc, char* argv[]), 文件路径file_path
        输出-type = int, name = main, signature = {'return': int, 'name': main, 'parameters': [{'argc': int}, {'argv': char**}]}
        '''
        self.func_node = node
        self.file_path = file_path
        self.type = text(node.child_by_field_name('type'))
        self.id = node.start_point[0] + 1
        while node.type not in ['function_declarator', 'parenthesized_declarator']: # parenthesized_declarator: 例如main(){}, void省略了
            node = node.child_by_field_name('declarator')
        if node.type == 'function_declarator':
            self.name = text(node.child_by_field_name('declarator'))
            parameters = node.child_by_field_name('parameters')
            param_list = []
            for param in parameters.children:
                if text(param) not in [',', '(', ')']:
                    declaration = Declaration(param)
                    for name, type in declaration().items():
                        param_list.append((name, type))
        else:
            self.name = self.type
            self.type = 'void'
            param_list = []
        self.signature = {'return': self.type, 'name': self.name, 'parameters': param_list}

    def __eq__(self, other):
        return self.signature == other.signature

    def __str__(self):
        param_str = ''
        for param in self.signature['parameters']:
            param_str += f"({param[0]}: {param[1]}) "
        return f"function name: {self.signature['name']}\nreturn type: {self.signature['return']}\nparameters: {param_str}\nfile path: {self.file_path}\n\n"

class Function:
    def __init__(self):
        self.funcs = {}
        self.id_to_func = {}

    def add_func(self, node, file_path):
        func = Func(node, file_path)
        if func.name not in self.funcs:
            self.funcs[func.name] = [func]
            self.id_to_func[func.id] = func
        else:
            if func not in self.funcs[func.name]:
                self.funcs[func.name].append(func)
        return func

    def match_func(self, func_name, param_node, expression):
        '''根据函数名和参数匹配函数，返回函数信息'''
        if len(self.funcs[func_name]) == 1: # 没有重构函数
            return self.funcs[func_name][0]
        # 如果有重构函数，如果参数的个数唯一，则返回对应函数
        if param_node.type != 'argument_list':
            print("not a param list")
            return None
        param_types = []
        for param in param_node.children[1: -1]:
            if param.type == ',':
                continue
            param_types.append(expression.traverse(param))
        match_num = 0
        match_func = None
        for func in self.funcs[func_name]:
            if len(func.signature['parameters']) == len(param_types):
                match_func = func
                match_num += 1
        if match_num == 1:
            return match_func
        else:   # 根据参数类型来匹配
            for func in self.funcs[func_name]:
                func_param_types = [x[1] for x in func.signature['parameters']]
                if func_param_types == param_types:
                    return func
        return None

    def __getitem__(self, func_name):
        return self.funcs[func_name]

    def __call__(self):
        return self.funcs

    def __str__(self):
        str = ''
        for func_name in self.funcs:
            for f in self.funcs[func_name]:
                str += f.__str__()
        return str

class Constant:
    def __init__(self, node):
        '''
        目的-获取常量的类型
        输入-节点node，例如1, 1.0, 'a', "abc", TRUE, FALSE, NULL
        输出-常量的类型，例如int, float, char, char*, bool, null
        '''
        if not node or node.type not in constant_type:
            self.type = 'unknown'
            return
        string = text(node)
        if node.type == 'preproc_arg':  # define a const中的const
            # 删除string中的注释"//"和"/* */"
            string = re.sub(r'//.*', '', string)
            string = re.sub(r'/\*.*\*/', '', string)
        if self.is_float(string):
            self.type = 'float'
        elif self.is_int(string):
            self.type = 'int'
        elif self.is_char(string):
            self.type = 'char'
        elif self.is_string(string):
            self.type = 'char*'
        elif self.is_bool(string):
            self.type = 'bool'
        elif self.is_null(string):
            self.type = 'null'
        else:
            self.type = 'unknown'
        self.value = string

    def is_float(self, string):
        return bool(re.match(r'^[-+]?[0-9]*\.[0-9]+$', string))

    def is_int(self, string):
        hex_, oct_, dec_ = False, False, False
        hex_ = bool(re.match(r'^[-+]?0[xX][0-9a-fA-F]+$', string))
        oct_ = bool(re.match(r'^[-+]?0[0-7]+$', string))
        dec_ = bool(re.match(r'^[-+]?[0-9]+$', string))
        return hex_ or oct_ or dec_

    def is_char(self, string):
        return bool(re.match(r'^\'[^\']\'$', string))

    def is_string(self, string):
        return bool(re.match(r'^\"[^\"]*\"$', string))

    def is_bool(self, string):
        return string in ['TURE', 'FALSE']

    def is_null(self, string):
        return string == 'NULL'

class Expression:
    def __init__(self, idType, Structure, Function):
        self.idType = idType
        self.structure_ = Structure
        self.function = Function
        
    def type(self, node):
        type = self.traverse(node)
        if type == 'unknown':
            return 'unknown'
        dim = type.count('*')
        new_type = type.replace('*', '').replace(' ', '')
        if new_type in self.idType.macro:
            type = self.idType.macro[new_type] + '*' * dim
        return type

    def traverse(self, node):
        '''
        目的-从上往下遍历node表达式，获取表达式的类型
        输入-idType, Structure, Function，分别表示变量名类型、结构体类型、函数类型
        输出-表达式的类型
        '''
        if node.type in constant_type:  # 常量类型通过Constant查询
            return Constant(node).type
        elif node.type == 'identifier': # 变量名类型通过idType查询
            return self.idType.query_type(text(node), node.start_point[0] + 1)
        elif node.type == 'sizeof_expression':  # sizeof表达式返回int
            return 'int'
        elif node.type in ['unary_expression', 'update_expression']:    # 一元表达式返回本身的类型
            return self.traverse(node.child_by_field_name('argument'))
        elif node.type == 'conditional_expression': # 三元表达式返回两个表达式的类型
            return self.traverse(node.child_by_field_name('consequence'))
        elif node.type == 'subscript_expression':   # 数组类型，例如a[i]，a的类型是int*，那么a[i]的类型是int
            argument_type = self.traverse(node.child_by_field_name('argument'))
            if argument_type == 'unknown':
                return 'unknown'
            return argument_type[:-1]   # 去掉最后一个*号
        elif node.type == 'field_expression':   # 结构体类型，例如a.b，a的类型是A，那么a.b的类型是int
            argument_type = self.traverse(node.child_by_field_name('argument'))
            if argument_type == 'unknown':
                return 'unknown'
            field = text(node.child_by_field_name('field'))
            op = text(node.children[1])
            if op == '->':  # 例如a的类型是A*，那么a->b的时候，要删掉a类型的最后一个*号
                argument_type = argument_type[:-1]
            if argument_type not in self.structure_:
                return 'unknown'
            structure = self.structure_[argument_type]
            if field not in structure.field_vars:
                return 'unknown'
            return structure.field_vars[field]
        elif node.type == 'pointer_expression': # 指针类型，例如*a, &a
            op = text(node.children[0])
            argument_type = self.traverse(node.child_by_field_name('argument'))
            if argument_type == 'unknown':
                return 'unknown'
            if op == '*':   # *a删除a类型的最后一个*号
                return argument_type[:-1]
            else:           # &添加一个*号
                return argument_type + '*'
        elif node.type == 'call_expression':    # 函数类型，例如f(a, b)，f的类型是int(int, int)，那么f(a, b)的类型是int
            callee = text(node.child_by_field_name('function'))
            if callee in self.function(): 
                parameters = node.child_by_field_name('arguments')
                match_func = self.function.match_func(callee, parameters, self)
                if match_func:
                    return match_func.type
            return 'unknown'
        elif node.type == 'parenthesized_expression':   # 括号表达式返回括号内的表达式类型
            return self.traverse(node.children[1])
        elif node.type == 'binary_expression':  # 二元表达式
            op = text(node.children[1])
            if op in ['==', '!=', '>', '>=', '<', '<=', '&&', '||']:
                return 'bool'
            else:   # 除了bool类型的二元表达式，其他的二元表达式返回强制类型转换后的类型
                left_type = self.traverse(node.child_by_field_name('left'))
                right_type = self.traverse(node.child_by_field_name('right'))
                return self.typecasting(left_type, right_type)
        elif node.type == 'assignment_expression':  # 赋值表达式返回左边的表达式类型
            return self.traverse(node.child_by_field_name('left'))
        elif node.type == 'cast_expression':    # 强制类型转换表达式返回强制类型转换后的类型
            return text(node.child_by_field_name('type'))
        else:
            return 'unknown'

    def typecasting(self, type1, type2):
        '''目的-将type1和type2进行强制类型转换'''
        def compare(type_list1, type_list2):
            if type1 in type_list1 and type2 in type_list2:
                return True
            if type1 in type_list2 and type2 in type_list1:
                return True
            return False
        def unsigned(types, copy=True):
            '''增加unsigned修饰'''
            if copy:
                new_types = types.copy()
            else:
                new_types = []
            for type in types:
                if type == 'int':
                    new_types.append('unsigned')
                new_types.append(f'unsigned {type}')
                new_types.append(f'{type} unsigned')
            return new_types
        if type1 == 'bool': # bool强制转换成int
            type1 = 'int'
        if type2 == 'bool':
            type2 = 'int'
        if compare(unsigned(['char', 'short']), unsigned(['char', 'short'])):   # char和short强制转换成int
            return 'int'
        elif compare(['float'], ['float']):   # float强制转换成double
            return 'double'
        elif type1 == type2:    
            return type1
        elif compare(unsigned(['char', 'short']), ['int']):
            return 'int'
        if compare(unsigned(['char', 'short', 'int']), unsigned(['int'], copy=False)):  # unsigned类型优先级高
            return 'unsigned int'
        elif compare(unsigned(['char', 'short', 'int']), ['long']):
            return 'long'
        elif compare(unsigned(['char', 'short', 'int', 'long']), unsigned(['long'], copy=False)):
            return 'unsigned long'
        elif compare(unsigned(['char', 'short', 'int', 'long']), ['long long']):
            return 'long long'
        elif compare(unsigned(['char', 'short', 'int', 'long', 'long long']), unsigned(['long long'], copy=False)):
            return 'unsigned long long'
        elif compare(unsigned(['char', 'short', 'int', 'long', 'long long']), ['float']):
            return 'float'
        elif compare(unsigned(['char', 'short', 'int', 'long', 'long long']) + ['float'], ['double']):
            return 'double'
        elif '*' in type1:  # 如果type1是指针类型，返回type1
            return type1
        elif '*' in type2:
            return type2
        else:
            return 'unknown'

class File(AST):
    def __init__(self, language, file_path):
        super().__init__(language)
        self.structure_ = {}    # {structure_name: structure}
        self.function = Function()      # {function_name: [function]} 可能重构
        self.file_path = os.path.join(os.path.abspath('.'), file_path)      # 文件路径
        self.idType = IdType(file_path)    # 变量名类型
        self.CG = {}    # 存放函数调用图
        self.unknown_call = {}  # 存放未知函数调用
        self.unknown_id = {}    # 存放未知函数名id
        code = r'{}'.format(open(self.file_path, 'r', encoding='utf-8', errors='ignore').read())
        tree = self.parser.parse(bytes(code, 'utf8'))
        self.root_node = tree.root_node 

    def construct_file(self, node=None):
        '''
        构建文件的信息，包括全局信息：结构体、全局变量类型、函数、宏定义
        '''
        if node is not None:
            root_node = node
        else:
            root_node = self.root_node
        for child in root_node.children:
            if child.type == 'preproc_ifdef':   # 如果是ifdef，则遍历ifdef内部的节点
                self.construct_file(child)
            if child.type in ['declaration', 'struct_specifier']:    # 结构体定义
                if child.type == 'struct_specifier':    # struct A{int a; int b;};
                    type_node = child
                else:           # struct A{int a; int b;} a; 在定义的时候多了声明
                    type_node = child.child_by_field_name('type')
                if type_node.type == 'struct_specifier' and type_node.child_by_field_name('body'):  # 结构体类型,不是函数指针
                    structure = Structure(type_node)
                    self.structure_[structure.name] = structure
                    domain = [child.end_point[0] + 1, MAX_LENGTH]   # 作用域全局
                    self.idType.add_def_var(structure.def_vars, domain, structure.name, None)
                if type_node.type in ['primitive_type', 'type_identifier']: # 全局变量类型
                    declaration = Declaration(child)
                    domain = [child.start_point[0] + 1, MAX_LENGTH]
                    self.idType.add_def_var(declaration(), domain, None, None)
            elif child.type == 'type_definition':   # 宏定义typedef
                type_node = child.child_by_field_name('type')
                if type_node.type == 'struct_specifier':
                    structure = Structure(type_node)
                    self.structure_[structure.name] = structure
                    domain = [child.end_point[0] + 1, MAX_LENGTH]
                    self.idType.add_def_var(structure.def_vars, domain, structure.name, None)
                    for name, type in structure.def_vars.items():
                        self.idType.add_macro(name, type)
                else:
                    type = text(type_node)
                    declaration = Declaration(child)
                    for name, type in declaration().items():
                        self.idType.add_macro(name, type)
            elif child.type == 'preproc_def':   # 宏定义#define，根据常量确定类型
                name = text(child.child_by_field_name('name'))
                const = Constant(child.child_by_field_name('value'))
                domain = [child.start_point[0] + 1, MAX_LENGTH]
                self.idType.add_def_var({name: const.type}, domain, None, None)
            elif child.type == 'function_definition':   # 获取函数内部的变量类型
                func_node = child
                func_info = self.function.add_func(func_node, self.file_path)
                for name, type in func_info.signature['parameters']:
                    domain = [func_node.start_point[0] + 1, func_node.end_point[0] + 1]
                    self.idType.add_def_var({name: type}, domain, None, None)
                body = func_node.child_by_field_name('body')
                self.get_local_type(body)   # 获取函数复合语句内部的变量类型
        self.construct_call_graph()
        self.query_type(self.root_node)
        # print(self.idType)
        # print(self.structure_)

    def construct_call_graph(self):
        '''构建函数调用图'''
        self.expression = Expression(self.idType, self.structure_, self.function)   # 定义表达式类，用来求表达式的类型
        def query_callee(node, caller):
            '''目的-查询调用者caller调用的函数callee'''
            if node.type == 'call_expression':
                callee = text(node.child_by_field_name('function'))
                arguments = node.child_by_field_name('arguments')
                if callee in self.function():
                    match_func = self.function.match_func(callee, arguments, self.expression)
                    if match_func:
                        self.CG.setdefault(match_func.id, set())
                        self.CG[match_func.id].add(caller)
                else:   # 不是自己定义的函数
                    self.unknown_call.setdefault(callee, set())
                    self.unknown_call[callee].add(caller)
                    if callee not in self.unknown_id:
                        self.unknown_id[callee] = -len(self.unknown_id) - 1
            for child in node.children:
                query_callee(child, caller)
        for func_name in self.function(): # 变量文件内的所有函数，查询各个函数内部调用的函数
            for func in self.function[func_name]:
                query_callee(func.func_node, func.id)

    def get_local_type(self, node):
        '''获取函数内部变量名的类型'''
        if node.type not in ['compound_statement', 'else_clause']:  # 如果不是复合语句或者else从句，直接pass
            return
        for statement in node.children:     # 遍历复合语句（花括号）内的每一个语句
            if statement.type == 'compound_statement':
                self.get_local_type(statement)
            if statement.type == 'declaration':     # 如果是声明语句，获取声明的变量名和类型
                declaration = Declaration(statement)
                domain = [statement.start_point[0] + 1, node.end_point[0] + 1]
                self.idType.add_def_var(declaration(), domain, None, None)
            elif statement.type in ['for_statement', 'while_statement', 'do_statement']:    # 如果是循环语句，则循环语句内定义的变量的作用域是循环语句内
                if statement.type == 'for_statement':   # for循环额外有一个初始化表达式
                    initializer = statement.child_by_field_name('initializer')
                    if initializer:
                        declaration = Declaration(initializer)
                        domain = [statement.start_point[0] + 1, statement.end_point[0] + 1]
                        self.idType.add_def_var(declaration(), domain, None, None)
                self.get_local_type(statement.child_by_field_name('body'))
            elif statement.type == 'if_statement':  # 如果是if语句，获取if语句内部的变量类型
                self.get_local_type(statement.child_by_field_name('consequence'))
                alternative = statement.child_by_field_name('alternative')
                if alternative:
                    self.get_local_type(alternative)

    def query_type(self, root_node, id_types={}):
        '''以root_node节点为根节点，往下遍历AST树，获取变量名的类型'''
        self.expression = Expression(self.idType, self.structure_, self.function)
        for child in root_node.children:
            if 'expression' in child.type and child.type != 'expression_statement':
                exp = self.expression.type(child)
                print((text(child), exp))
            self.query_type(child)
        return id_types

    def see_cg(self, pdf=True, view=False):
        '''可视化函数调用图'''
        self.construct_call_graph()
        dot = Digraph(comment=self.file_path)
        for funcs in self.function().values():
            for f in funcs:
                file_path = f.file_path.replace('\\', '/')
                label = f'name: {f.name}\\ntype: {f.type}\\nparameters: {list(f.signature["parameters"])}\\nfile path: {file_path}'
                # label = f.name
                dot.node(str(f.id), shape='rectangle', label=label, fontname='fangsong')
        for func in self.unknown_id:
            dot.node(str(self.unknown_id[func]), shape='rectangle', label=func, fontname='fangsong')
        for caller, callees in self.CG.items():
            for callee in callees:
                dot.edge(str(callee), str(caller))
        for caller, callees in self.unknown_call.items():
            for callee in callees:
                dot.edge(str(callee), str(self.unknown_id[caller]))
        if pdf:
            dot.render('_'.join(self.file_path.split('.')), view=view, cleanup=True)

    def merge(self, other):
        self.structure_.update(other.structure_)
        self.idType.vars.update(other.idType.vars)
        for func_name, funcs in other.function().items():
            self.function().setdefault(func_name, [])
            self.function()[func_name].extend(funcs)
            self.function.id_to_func.update(other.function.id_to_func)

class Dir(AST):
    def __init__(self, path, language='c'):
        super().__init__(language)
        self.path = path
        filenames = os.listdir(self.path)
        self.filenames = []
        for f in filenames:
            if f.split('.')[-1] in ['c', 'cpp', 'h', 'hpp', 'cc']:
                self.filenames.append(f)
        self.Include = {f: [] for f in self.filenames}
        self.Indegree = {f: 0 for f in self.filenames}
        self.Included = {f: [] for f in self.filenames}
        self.files = {f: None for f in self.filenames}
        self.load = {f: False for f in self.filenames}
        for f in self.filenames:
            self.files[f] = File('c', os.path.join(self.path, f))
            code = r'{}'.format(open(os.path.join(self.path, f), 'r', encoding='utf-8', errors='ignore').read())
            tree = self.parser.parse(bytes(code, 'utf8'))
            root_node = tree.root_node
            for child in root_node.children:
                if child.type == 'preproc_include':
                    path = child.child_by_field_name('path')
                    if path.type == 'string_literal':
                        include = text(path)[1:-1]
                        if include in self.Included:
                            self.Included[include].append(f)
                            self.Include[f].append(include)
                        self.Indegree[f] += 1
                        
        while True:
            finish_load = True
            for f in self.Indegree:
                if self.Indegree[f] == 0 and not self.load[f]:
                    finish_load = False
                    self.load[f] = True
                    for include_file in self.Include[f]:
                        self.files[f].merge(self.files[include_file])
                    self.files[f].construct_file()
                    for included_file in self.Included[f]:
                        self.Indegree[included_file] -= 1
            if finish_load:
                break
        for file in self.files.values():
            file.construct_call_graph()
            file.see_cg(view=True)

if __name__ == '__main__':
    # file = File('cpp', 'test/quadTree.cpp')
    # file.construct_file()
    # file.see_cg(view=True)
    dir = Dir('./test')
