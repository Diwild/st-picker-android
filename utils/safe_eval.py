"""
ST选股工具 - 安全表达式解析器
替代 eval，防止代码注入攻击
"""

import ast
import operator
from typing import Any, Dict, Set, Optional
from dataclasses import dataclass

from utils.logger import logger


@dataclass
class EvalResult:
    """表达式执行结果"""
    success: bool
    value: Any = None
    error: Optional[str] = None


class SafeExpressionEvaluator:
    """
    安全的策略表达式解析器
    
    支持的运算符:
    - 算术: +, -, *, /, //, %, **
    - 比较: ==, !=, <, <=, >, >=
    - 逻辑: and, or, not
    - 成员: in, not in
    
    支持的函数:
    - abs, round, min, max, sum
    """
    
    # 允许的二元运算符
    BINARY_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
    }
    
    # 允许的布尔运算符
    BOOL_OPERATORS = {
        ast.And: lambda a, b: a and b,
        ast.Or: lambda a, b: a or b,
    }
    
    # 允许的一元运算符
    UNARY_OPERATORS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
        ast.Not: operator.not_,
        ast.Invert: operator.invert,
    }
    
    # 允许的函数
    ALLOWED_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'len': len,
        'float': float,
        'int': int,
        'str': str,
        'bool': bool,
    }
    
    # 允许的常量
    ALLOWED_NAMES = {'True', 'False', 'None'}
    
    def __init__(self):
        self.banned_names: Set[str] = {
            '__import__', 'eval', 'exec', 'compile',
            'open', 'file', 'input', 'raw_input',
            'os', 'sys', 'subprocess', 'importlib',
        }
    
    def eval(self, expr: str, context: Dict[str, Any]) -> EvalResult:
        """
        安全执行表达式
        
        Args:
            expr: 表达式字符串，例如 "price < 3 and score > 50"
            context: 变量上下文，例如 {'price': 2.5, 'score': 60}
        
        Returns:
            EvalResult: 执行结果
        """
        if not expr or not expr.strip():
            return EvalResult(success=True, value=True)
        
        try:
            # 解析表达式
            tree = ast.parse(expr.strip(), mode='eval')
            result = self._eval_node(tree.body, context)
            return EvalResult(success=True, value=result)
        except SyntaxError as e:
            return EvalResult(success=False, error=f"语法错误: {e}")
        except ValueError as e:
            return EvalResult(success=False, error=str(e))
        except Exception as e:
            logger.error(f"表达式执行失败: {e}", 'SAFE_EVAL')
            return EvalResult(success=False, error=f"执行错误: {e}")
    
    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """递归计算AST节点"""
        
        # 常量
        if isinstance(node, ast.Constant):
            return node.value
        
        # Python 3.7 兼容：Num, Str 等
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Str):
            return node.s
        if isinstance(node, ast.NameConstant):
            return node.value
        
        # 变量名
        if isinstance(node, ast.Name):
            if node.id in self.banned_names:
                raise ValueError(f"禁止使用名称: {node.id}")
            if node.id in self.ALLOWED_NAMES:
                return {'True': True, 'False': False, 'None': None}[node.id]
            if node.id in context:
                return context[node.id]
            raise ValueError(f"未定义的变量: {node.id}")
        
        # 二元运算
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            op_type = type(node.op)
            if op_type not in self.BINARY_OPERATORS:
                raise ValueError(f"不支持的运算符: {op_type.__name__}")
            return self.BINARY_OPERATORS[op_type](left, right)
        
        # 布尔运算 (and/or)
        if isinstance(node, ast.BoolOp):
            values = [self._eval_node(v, context) for v in node.values]
            op_type = type(node.op)
            if op_type not in self.BOOL_OPERATORS:
                raise ValueError(f"不支持的布尔运算符: {op_type.__name__}")
            
            # 短路求值
            if op_type == ast.And:
                return all(values)
            else:  # ast.Or
                return any(values)
        
        # 比较运算
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, context)
                op_type = type(op)
                if op_type not in self.BINARY_OPERATORS:
                    raise ValueError(f"不支持的比较运算符: {op_type.__name__}")
                if not self.BINARY_OPERATORS[op_type](left, right):
                    return False
                left = right
            return True
        
        # 一元运算
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            op_type = type(node.op)
            if op_type not in self.UNARY_OPERATORS:
                raise ValueError(f"不支持的一元运算符: {op_type.__name__}")
            return self.UNARY_OPERATORS[op_type](operand)
        
        # 函数调用
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("只允许简单函数调用")
            
            func_name = node.func.id
            if func_name not in self.ALLOWED_FUNCTIONS:
                raise ValueError(f"不允许的函数: {func_name}")
            
            args = [self._eval_node(arg, context) for arg in node.args]
            kwargs = {
                kw.arg: self._eval_node(kw.value, context)
                for kw in node.keywords
            }
            
            return self.ALLOWED_FUNCTIONS[func_name](*args, **kwargs)
        
        # 条件表达式 (if else)
        if isinstance(node, ast.IfExp):
            test = self._eval_node(node.test, context)
            if test:
                return self._eval_node(node.body, context)
            else:
                return self._eval_node(node.orelse, context)
        
        # 元组
        if isinstance(node, ast.Tuple):
            return tuple(self._eval_node(elt, context) for elt in node.elts)
        
        # 列表
        if isinstance(node, ast.List):
            return [self._eval_node(elt, context) for elt in node.elts]
        
        # 成员运算 (in/not in)
        if isinstance(node, ast.In):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.comparator, context)
            return left in right
        
        if isinstance(node, ast.NotIn):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.comparator, context)
            return left not in right
        
        raise ValueError(f"不支持的表达式类型: {type(node).__name__}")
    
    def validate_syntax(self, expr: str) -> EvalResult:
        """仅验证表达式语法是否正确"""
        if not expr or not expr.strip():
            return EvalResult(success=True, value=True)
        
        try:
            tree = ast.parse(expr.strip(), mode='eval')
            # 遍历检查是否有不允许的节点
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if node.id in self.banned_names:
                        return EvalResult(
                            success=False,
                            error=f"包含禁止使用的名称: {node.id}"
                        )
            return EvalResult(success=True, value=True)
        except SyntaxError as e:
            return EvalResult(success=False, error=f"语法错误: {e}")
    
    def validate_expression(self, expr: str) -> tuple:
        """
        验证表达式，返回 (is_valid, error_message) 元组
        兼容 filter_panel 的调用方式
        """
        result = self.validate_syntax(expr)
        if result.success:
            return (True, None)
        else:
            return (False, result.error)


# 全局实例
safe_evaluator = SafeExpressionEvaluator()


def safe_eval(expr: str, context: Dict[str, Any]) -> bool:
    """
    快捷函数：安全执行表达式，返回布尔结果
    
    Args:
        expr: 表达式字符串
        context: 变量上下文
    
    Returns:
        bool: 表达式结果，失败时返回False
    """
    result = safe_evaluator.eval(expr, context)
    if result.success:
        return bool(result.value)
    return False
