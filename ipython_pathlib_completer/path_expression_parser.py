from pathlib import Path
import logging
from IPython import get_ipython
from IPython.core.guarded_eval import guarded_eval, EvaluationContext
import parso

logger = logging.getLogger(__name__)


def extract_div_sequence(code):
    """
    Extracts parts of a chained division expression from a code string.

    This function parses code that ends with a forward slash (`/`) to identify
    a sequence of slash-separated tokens. It is designed to interpret expressions
    like `a / b / c /` and return the component parts (`a`, `b`, `c`).

    Args:
        code (str): The code string to parse. It should end with a `/`
                    character, optionally followed by spaces.

    Returns:
        list: A list of parso nodes representing the parts of the division
              sequence. Returns an empty list if the parsing fails or if the
              expression format is not as expected.
    """
    code = code.strip()
    if not code.endswith("/"):
        logger.debug(
            "Input code should ends with a slash followed by zero or more spaces"
        )
        return []

    module = parso.parse(code)
    pos = (1, len(code))
    leaf = module.get_leaf_for_position(pos)
    if leaf.value != "/" or leaf.type != "operator":
        logger.debug("The last token should be `/` operator")
        return []

    parts = []
    items = leaf.parent.children
    if len(items) < 2:
        logger.debug("Slash sequence should have multiple tokens")
        return []

    items = items[::-1]  # ... a / b / c /  --> / c / b / a ...
    parts = []
    for op, part in zip(items[::2], items[1::2]):
        if op.value != "/":
            break
        parts.append(part)

    return parts[::-1]


def validate_pathlib_path_is_defined(shell):
    """
    Validates that 'Path' in the current IPython namespace is `pathlib.Path`.

    This function uses IPython's `guarded_eval` to safely evaluate the 'Path'
    variable in the user's namespace. It then checks if the evaluated object
    is the `Path` class from the `pathlib` module. This is important to ensure
    that the completer is triggered for the correct object.

    Args:
        shell: The IPython shell instance (e.g., from `get_ipython()`).

    Returns:
        bool: True if 'Path' is `pathlib.Path`, False otherwise.
    """
    context = EvaluationContext(
        locals=shell.user_ns,
        globals=shell.user_global_ns,
        evaluation="limited",
    )
    try:
        x = guarded_eval("Path", context)
    except NameError:
        return False
    if not hasattr(x, "__module__") or not hasattr(x, "__name__"):
        return False
    is_valid = (x.__module__, x.__name__) in [("pathlib", "Path")]
    return is_valid


def extract_pathlib_path_string(node):
    """
    Extracts the string argument from a `Path(...)` constructor call node.

    This function analyzes a parso `atom_expr` node to determine if it
    represents a `pathlib.Path` instantiation (e.g., `Path()`, `Path("...")`).
    It supports calls with no arguments, in which case it returns `"./"`,
    or with a single string literal argument, which it extracts and returns.

    Args:
        node: A parso node, expected to be of type `atom_expr`.

    Returns:
        str or None: The string value from the Path constructor, or `"./"` if
                     no argument is provided. Returns None if the node is not
                     a valid `Path(...)` call.
    """
    if node.type != "atom_expr":
        return None

    children = node.children
    if not children or children[0].type != "name" or children[0].value != "Path":
        return None

    trailer = children[1]
    if len(trailer.children) not in (2, 3):
        # support only `()` or `("...")`
        return None

    if trailer.children[0].value != "(" or trailer.children[-1].value != ")":
        return None

    if len(trailer.children) == 2:
        # Path() --> "./"
        return "./"
    else:
        return trailer.children[1].value


def build_path_object_from_parts(parts):
    """
    Evaluates a sequence of parso nodes to reconstruct a pathlib.Path object.

    This function takes a list of nodes representing a path expression
    (e.g., `Path("./foo") / "bar"`) and evaluates it within the user's
    IPython namespace to produce the resulting `pathlib.Path` object.
    The evaluation is performed safely using `guarded_eval`.

    Args:
        parts (list): A list of parso nodes representing the path expression.

    Returns:
        pathlib.Path or None: The reconstructed pathlib.Path object if
                              successful, otherwise None.
    """
    shell = get_ipython()
    context = EvaluationContext(
        locals=shell.user_ns,
        globals=shell.user_global_ns,
        evaluation="limited",
    )
    p = None
    try:
        for i, part in enumerate(parts):
            if i == 0:
                if part.type == "name":
                    code = part.value
                    x = guarded_eval(code, context)
                    if not isinstance(x, Path):
                        logger.debug("The first variable should be pathlib.Path object")
                        return None
                elif part.type == "atom_expr":
                    x = extract_pathlib_path_string(part)
                    if x is not None:
                        # It may be Path constructor
                        if not validate_pathlib_path_is_defined(shell):
                            logger.debug("Path keyword is not pathlib.Path ")
                            return None
                        x = guarded_eval(x, context)
                        if not isinstance(x, str):
                            logger.debug(f"Invalid Path constructor: {part}")
                            return None
                        x = Path(x)
                    else:
                        # It may be a valid Path attribute access, ex: parent.child.my_path.
                        try:
                            x = guarded_eval(part.get_code(), context)
                        except:
                            logger.debug(f"The following evaluation is not allowed in limited mode: {part.get_code}")
                            return None
                        if not isinstance(x, Path):
                            logger.debug("The first variable should be pathlib.Path object")
                            return None
                else:
                    logger.debug("The first part should be pathlib.Path object")
                    return None
                p = x
            else:
                if part.type in ("name", "string"):
                    code = part.value
                    x = guarded_eval(code, context)
                    if not isinstance(x, (Path, str)):
                        logger.debug(f"Variable should be str or Path, got: {type(x)}")
                        return None
                    p = p / x
                else:
                    logger.debug(
                        f"None first part should be str or Path object, got {part}"
                    )
                    return None
            logger.debug(f"Evaluated path at depth {i}: {p}")
    except Exception as e:
        logger.error(e)
        return None
    return p


def resolve_path_from_code(code):
    """
    Resolves a pathlib.Path object from a code string.

    This function serves as the main entry point for parsing a code expression.
    It takes a string of code, extracts the sequence of path-related parts,
    and then builds (evaluates) them to reconstruct the final `pathlib.Path`
    object.

    Args:
        code (str): The code string containing the path expression.

    Returns:
        pathlib.Path or None: The resulting `Path` object if successful,
                          otherwise None.
    """
    parts = extract_div_sequence(code)
    return build_path_object_from_parts(parts)
