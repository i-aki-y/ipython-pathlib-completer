import logging
import glob
import itertools  # Import itertools module
from IPython.core.completer import (
    context_matcher,
    SimpleMatcherResult,
    SimpleCompletion,
)
from .path_expression_parser import resolve_path_from_code

logger = logging.getLogger(__name__)


def create_pathlib_matcher(suppress=True, quote='"'):
    """
    Factory for creating a pathlib-aware completer matcher for IPython.

    This function returns a context-aware matcher that provides completions
    for `pathlib.Path` objects after a division (`/`) operator.

    Args:
        suppress (bool): If True, suppresses other IPython completers if this
                         matcher provides any completions. Defaults to True.
        quote (str): The quote character to use when generating completion
                     suggestions (e.g., `'` for single quotes, `"` for double quotes).
                     Defaults to `"`.

    Returns:
        A function decorated with `@context_matcher` that can be registered
        with IPython's completer.
    """

    @context_matcher()
    def pathlib_division_matcher(context):
        """
        Provides path completions for `pathlib.Path` division expressions.

        This matcher triggers when the cursor is at the end of a line
        containing a `pathlib.Path` object followed by a `/`. It evaluates
        the expression to get the base path, then uses IPython's built-in
        file completer to find matching sub-paths, and formats the results
        as executable Python code.

        For example, after `Path("~") / "dev" /`, it would suggest `"my_project" / `
        if `~/dev/my_project` exists.

        Args:
            context (CompletionContext): The context for the completion request,
                                         containing information about the cursor
                                         position and the line content.

        Returns:
            SimpleMatcherResult: A container for the completion results.
        """
        logger.debug(f"input context: {context}")
        code, token = preprocess_context(context)
        path_obj = resolve_path_from_code(code)
        if path_obj is None:
            return SimpleMatcherResult(completions=[], suppress=False)

        def format_entry_name(path, quote):
            dir_mark = " /" if path.is_dir() else ""
            name = path.name.replace(quote, f"\\{quote}")
            return f"{quote}{name}{quote}" + dir_mark

        # Use glob.escape() for robustness
        paths_generator = path_obj.expanduser().resolve().glob(f"{glob.escape(token)}*")

        # Limit to first 500 completions for performance
        limited_paths = itertools.islice(paths_generator, 500)

        entries = (
            format_entry_name(p, quote) for p in limited_paths
        )  # Generator expression
        completions = []
        for entry in entries:
            completions.append(SimpleCompletion(text=entry, type="pathlib"))
        return SimpleMatcherResult(completions=completions, suppress=suppress)

    return pathlib_division_matcher


def preprocess_context(context):
    """
    Preprocesses the IPython completion context.

    This function separates the code to be parsed from the token being completed.
    For an expression like `Path() / "some/path/to/fi` where tab is pressed
    after `fi`, this function will return the code part `Path() / "some/path/to/`
    and the token part `'fi'`.

    Args:
        context (CompletionContext): The completion context from IPython.

    Returns:
        tuple[str, str]: A tuple containing the code string to be parsed and
                     the token being completed.
    """
    cur_pos = context.cursor_position
    token = context.token
    if token.endswith("/"):
        token = ""
    else:
        cur_pos = cur_pos - len(token)
    code = context.line_with_cursor[:cur_pos]
    return code, token
