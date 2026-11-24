import ast
import operator

_ALLOWED = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}

def safe_calculate(expression):
    if len(expression) > 120:
        raise ValueError("Expressão muito longa.")
    tree = ast.parse(expression, mode="eval")
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED:
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 8:
                raise ValueError("Expoente muito alto.")
            result = _ALLOWED[type(node.op)](left, right)
            if abs(result) > 1e100:
                raise ValueError("Resultado fora do limite.")
            return result
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED:
            return _ALLOWED[type(node.op)](walk(node.operand))
        raise ValueError("Expressão contém operação não permitida.")
    return walk(tree)
