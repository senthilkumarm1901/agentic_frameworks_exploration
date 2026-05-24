"""Safe arithmetic calculator tool."""

import ast
import re


# Regex: only allow digits, decimal points, arithmetic operators, parentheses, and whitespace
_SAFE_PATTERN = re.compile(r"^[\d\s\+\-\*\/\.\(\)\%]+$")


def calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Args:
        expression: Arithmetic expression (e.g., "25.46 / 3.42", "331.9 * 1000000")

    Returns:
        String with the result (e.g., "Result: 7.44")
    """
    # Validate the expression contains only safe characters
    if not _SAFE_PATTERN.match(expression):
        return f"Error: Expression contains invalid characters. Only numbers and +, -, *, /, %, () are allowed."

    try:
        # Use compile + eval with empty namespaces for safe arithmetic evaluation
        # This is safe because we've already validated the input contains only
        # numeric characters and arithmetic operators via regex
        code = compile(expression, "<string>", "eval")

        # Verify the AST only contains safe node types
        for node in ast.walk(ast.parse(expression, mode="eval")):
            if isinstance(node, (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
                                 ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
                                 ast.Mod, ast.Pow, ast.USub, ast.UAdd)):
                continue
            elif isinstance(node, ast.Num):  # Python 3.7 compat
                continue
            else:
                return f"Error: Unsupported operation in expression."

        result = eval(code, {"__builtins__": {}}, {})
        # Round to reasonable precision
        if isinstance(result, float):
            result = round(result, 4)
        return f"Result: {result}"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: {e}"
