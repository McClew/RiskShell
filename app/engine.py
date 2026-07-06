import ast
import math
import operator
import os
import yaml

class SafeFormulaEvaluator:
    """
    A safe mathematical formula evaluator using Python's Abstract Syntax Tree (AST).
    This evaluator prevents arbitrary code execution and tracks step-by-step
    operations for auditing and transparency.
    """
    OPERATORS = {
        ast.Add: (operator.add, '+'),
        ast.Sub: (operator.sub, '-'),
        ast.Mult: (operator.mul, '*'),
        ast.Div: (operator.truediv, '/'),
        ast.Pow: (operator.pow, '**'),
        ast.USub: (operator.neg, '-'),
        ast.UAdd: (lambda x: x, '+'),
    }

    FUNCTIONS = {
        'log': math.log,
        'ln': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'sqrt': math.sqrt,
        'abs': abs,
        'ceil': math.ceil,
        'floor': math.floor,
        'round': round,
        'str': str,
        'print': lambda *args: " ".join(str(a) for a in args),
    }

    def __init__(self, variables):
        """
        Initialise the evaluator with variable bindings.
        :param variables: Dictionary of variable name (str) to numeric value (float/int)
        """
        self.variables = variables
        self.steps = []

    def evaluate(self, formula_str):
        """
        Evaluate the formula and return the result along with the execution steps.
        :param formula_str: Math expression string
        :return: Tuple of (float/int result, list of step strings)
        """
        self.steps = []
        try:
            tree = ast.parse(formula_str.strip(), mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Syntax error in formula: {e}")
        
        result, _ = self._eval_node(tree.body)
        return result, self.steps

    def _eval_node(self, node):
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)
        
        elif isinstance(node, ast.Constant):
            val = node.value
            if not isinstance(val, (int, float, str)):
                raise TypeError(f"Constant value must be numeric or string, got {type(val).__name__}")
            if isinstance(val, str):
                return val, repr(val)
            return val, str(val)
        
        elif isinstance(node, ast.Name):
            var_name = node.id
            if var_name not in self.variables:
                raise ValueError(f"Variable '{var_name}' is not defined in the module context.")
            val = self.variables[var_name]
            if val is None:
                raise ValueError(f"Variable '{var_name}' is required but has not been set.")
            return val, var_name
        
        elif isinstance(node, ast.BinOp):
            left_val, left_repr = self._eval_node(node.left)
            right_val, right_repr = self._eval_node(node.right)
            
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise TypeError(f"Unsupported operator: {op_type.__name__}")
            
            op_func, op_symbol = self.OPERATORS[op_type]
            
            try:
                result = op_func(left_val, right_val)
            except ZeroDivisionError:
                raise ZeroDivisionError(f"Mathematical division by zero: {left_val} {op_symbol} {right_val}")
            except OverflowError:
                raise OverflowError(f"Calculation overflowed: {left_val} {op_symbol} {right_val}")
            
            # Format numbers cleanly
            left_val_str = repr(left_val) if isinstance(left_val, str) else f"{left_val:.4f}".rstrip('0').rstrip('.') if isinstance(left_val, float) else str(left_val)
            right_val_str = repr(right_val) if isinstance(right_val, str) else f"{right_val:.4f}".rstrip('0').rstrip('.') if isinstance(right_val, float) else str(right_val)
            result_str = repr(result) if isinstance(result, str) else f"{result:.4f}".rstrip('0').rstrip('.') if isinstance(result, float) else str(result)
            
            expr_repr = f"({left_repr} {op_symbol} {right_repr})"
            val_repr = f"({left_val_str} {op_symbol} {right_val_str})"
            
            if expr_repr != val_repr:
                step_str = f"Evaluate {expr_repr} -> {val_repr} = {result_str}"
            else:
                step_str = f"Evaluate {val_repr} = {result_str}"
                
            self.steps.append(step_str)
            return result, result_str
        
        elif isinstance(node, ast.UnaryOp):
            operand_val, operand_repr = self._eval_node(node.operand)
            
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise TypeError(f"Unsupported unary operator: {op_type.__name__}")
            
            op_func, op_symbol = self.OPERATORS[op_type]
            result = op_func(operand_val)
            
            operand_val_str = repr(operand_val) if isinstance(operand_val, str) else f"{operand_val:.4f}".rstrip('0').rstrip('.') if isinstance(operand_val, float) else str(operand_val)
            result_str = repr(result) if isinstance(result, str) else f"{result:.4f}".rstrip('0').rstrip('.') if isinstance(result, float) else str(result)
            
            expr_repr = f"{op_symbol}{operand_repr}"
            val_repr = f"{op_symbol}{operand_val_str}"
            
            if expr_repr != val_repr:
                step_str = f"Evaluate {expr_repr} -> {val_repr} = {result_str}"
            else:
                step_str = f"Evaluate {val_repr} = {result_str}"
                
            self.steps.append(step_str)
            return result, result_str
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise TypeError("Function call must be a direct function name.")
            
            func_name = node.func.id
            if func_name not in self.FUNCTIONS:
                raise NameError(f"Unsupported or forbidden function call: '{func_name}'")
            
            if node.keywords:
                raise TypeError(f"Keyword arguments are not supported in function '{func_name}'")
                
            args_evaluated = [self._eval_node(arg) for arg in node.args]
            arg_vals = [val for val, _ in args_evaluated]
            arg_reprs = [r for _, r in args_evaluated]
            
            func = self.FUNCTIONS[func_name]
            try:
                result = func(*arg_vals)
            except ValueError as e:
                raise ValueError(f"Math domain error or invalid argument in {func_name}: {e}")
            except TypeError as e:
                raise TypeError(f"Invalid arguments for function {func_name}: {e}")
            except OverflowError:
                raise OverflowError(f"Calculation overflowed in function {func_name}")
                
            # Format numbers cleanly
            arg_val_strs = [
                repr(val) if isinstance(val, str) else f"{val:.4f}".rstrip('0').rstrip('.') if isinstance(val, float) else str(val)
                for val in arg_vals
            ]
            result_str = repr(result) if isinstance(result, str) else f"{result:.4f}".rstrip('0').rstrip('.') if isinstance(result, float) else str(result)
            
            expr_repr = f"{func_name}({', '.join(arg_reprs)})"
            val_repr = f"{func_name}({', '.join(arg_val_strs)})"
            
            if expr_repr != val_repr:
                step_str = f"Evaluate {expr_repr} -> {val_repr} = {result_str}"
            else:
                step_str = f"Evaluate {val_repr} = {result_str}"
                
            self.steps.append(step_str)
            return result, result_str
        
        else:
            raise TypeError(f"Forbidden or unsupported expression element: {type(node).__name__}")


def validate_module_schema(data, file_path):
    """
    Validates that the loaded YAML dictionary conforms to the required risk module schema.
    Raises ValueError if validation fails.
    """
    required_keys = ['title', 'description', 'methodology', 'pros', 'cons', 'variables', 'output_title']
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Module file '{file_path}' is missing required root key: '{key}'")
            
    if 'formula' not in data and 'script' not in data:
        raise ValueError(f"Module file '{file_path}' must contain either a 'formula' or 'script' key.")
            
    if not isinstance(data['variables'], list):
        raise ValueError(f"Module file '{file_path}' contains invalid 'variables' section. It must be a list.")
        
    variable_keys = ['name', 'default', 'required', 'description', 'source']
    for idx, var in enumerate(data['variables']):
        if not isinstance(var, dict):
            raise ValueError(f"Module file '{file_path}' variable at index {idx} is not a key-value mapping.")
        for vkey in variable_keys:
            if vkey not in var:
                raise ValueError(f"Module file '{file_path}' variable '{var.get('name', f'index {idx}')}' is missing sub-key: '{vkey}'")

    if 'visualisation' in data:
        vis = data['visualisation']
        if not isinstance(vis, dict):
            raise ValueError(f"Module file '{file_path}' contains invalid 'visualisation' section. It must be a dictionary.")
        if 'type' not in vis:
            raise ValueError(f"Module file '{file_path}' 'visualisation' is missing required sub-key: 'type'")
        if vis['type'] not in ['histogram', 'scatter', 'plot', 'bar']:
            raise ValueError(f"Module file '{file_path}' 'visualisation' has unsupported type: '{vis['type']}'. Supported types: histogram, scatter, plot, bar")
        if vis['type'] == 'histogram' and 'data_variable' not in vis:
            raise ValueError(f"Module file '{file_path}' 'visualisation' of type 'histogram' is missing required sub-key: 'data_variable'")
        if vis['type'] in ['scatter', 'plot', 'bar'] and ('x_variable' not in vis or 'y_variable' not in vis):
             raise ValueError(f"Module file '{file_path}' 'visualisation' of type '{vis['type']}' requires both 'x_variable' and 'y_variable'")
        
        # Check optional aesthetics
        if 'x_label' in vis and not isinstance(vis['x_label'], str):
            raise ValueError(f"Module file '{file_path}' 'visualisation.x_label' must be a string.")
        if 'y_label' in vis and not isinstance(vis['y_label'], str):
            raise ValueError(f"Module file '{file_path}' 'visualisation.y_label' must be a string.")
        if 'height' in vis and not isinstance(vis['height'], int):
            raise ValueError(f"Module file '{file_path}' 'visualisation.height' must be an integer.")
        if 'width' in vis and not isinstance(vis['width'], int):
            raise ValueError(f"Module file '{file_path}' 'visualisation.width' must be an integer.")
        if 'colour' in vis and not isinstance(vis['colour'], str):
            raise ValueError(f"Module file '{file_path}' 'visualisation.colour' must be a string.")
        if 'theme' in vis and not isinstance(vis['theme'], str):
            raise ValueError(f"Module file '{file_path}' 'visualisation.theme' must be a string.")
        if 'grid' in vis and not isinstance(vis['grid'], bool):
            raise ValueError(f"Module file '{file_path}' 'visualisation.grid' must be a boolean.")

    if 'visualisation_bounds' in data:
        bounds = data['visualisation_bounds']
        if not isinstance(bounds, dict):
            raise ValueError(f"Module file '{file_path}' contains invalid 'visualisation_bounds' section. It must be a dictionary.")
        for k in bounds:
            if k not in ['x_min_clamp', 'x_max_percentile', 'x_max_clamp']:
                raise ValueError(f"Module file '{file_path}' 'visualisation_bounds' has unsupported key: '{k}'")
            if not isinstance(bounds[k], (int, float)):
                raise ValueError(f"Module file '{file_path}' 'visualisation_bounds' key '{k}' must be a number.")


def load_risk_modules(app_dir):
    """
    Recursively scans the modules directory and loads schema-compliant YAML files.
    :param app_dir: Absolute path to the main app/ directory containing 'modules/'
    :return: Dictionary mapping module_path (e.g. 'modules/ale') to parsed module data.
    """
    modules_dir = os.path.join(app_dir, 'modules')
    loaded_modules = {}
    
    if not os.path.exists(modules_dir):
        return loaded_modules
        
    for root, _, files in os.walk(modules_dir):
        for file in files:
            if file.lower().endswith(('.yaml', '.yml')):
                full_path = os.path.join(root, file)
                
                # Compute path relative to app_dir (e.g. modules/microsoft_dread.yaml)
                rel_path = os.path.relpath(full_path, app_dir).replace('\\', '/')
                # Compute module key without extension (e.g. modules/microsoft_dread)
                module_key, _ = os.path.splitext(rel_path)
                
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    
                    if data is None:
                        continue
                        
                    validate_module_schema(data, rel_path)
                    # Add path references and load optional output fields
                    data['file_path'] = rel_path
                    data['module_key'] = module_key
                    data['output_prefix'] = data.get('output_prefix', '')
                    data['output_postfix'] = data.get('output_postfix', '')
                    loaded_modules[module_key] = data
                except Exception as e:
                    # Print error to stdout but proceed loading other modules
                    print(f"\033[91mError loading module {rel_path}: {e}\033[0m")
                    
    return loaded_modules
