"""Top-level package"""

__version__ = "0.1.0"

from .path_expression_parser import *
from .matcher import *
from .utils import *
from IPython import get_ipython


def enable_pathlib_completer(suppress=True, overwrite=False, quote='"'):
    """
    Enables and registers the pathlib completer with the current IPython instance.

    This function retrieves the pathlib completer matcher and adds it to
    IPython's list of custom matchers. If a matcher with the same function
    name (`path_after_slash`) already exists, its behavior depends on the
    `overwrite` parameter.

    Args:
        suppress (bool): If True, the pathlib completer will suppress other
                         matchers when it provides completions. Passed to `create_pathlib_matcher`.
                         Defaults to True.
        overwrite (bool): If True, an existing pathlib completer will be
                          replaced with the new one. If False and a completer
                          already exists, a message is printed and no action
                          is taken. Defaults to False.
        quote (str): The quote character to use when generating completion
                     suggestions (e.g., `'` for single quotes, `"` for double quotes).
                     Defaults to `"`.
    """
    ip = get_ipython()
    if not ip:
        return

    pathlib_matcher = create_pathlib_matcher(suppress, quote=quote)
    idx = -1
    for i, m in enumerate(ip.Completer.custom_matchers):
        if m.__name__ == pathlib_matcher.__name__:
            idx = i
            break
    if overwrite and idx >= 0:
        print("update pathlib_completer")
        ip.Completer.custom_matchers[idx] = pathlib_matcher
    elif not overwrite and idx >= 0:
        print("pathlib_completer has already been enabled")
    else:
        ip.Completer.custom_matchers.append(pathlib_matcher)


def disable_pathlib_completer():
    """
    Disables and unregisters the pathlib completer from the current IPython instance.

    This function removes the custom pathlib completer (identified by its
    function name `path_after_slash`) from IPython's list of custom matchers.
    If the completer is not found, no action is taken.
    """
    ip = get_ipython()
    if not ip:
        return

    matcher_name = (
        create_pathlib_matcher().__name__
    )  # Get the expected name of the matcher
    idx = -1
    for i, m in enumerate(ip.Completer.custom_matchers):
        if m.__name__ == matcher_name:
            idx = i
            break
    if idx >= 0:
        print("remove matcher:", ip.Completer.custom_matchers[idx].__name__)
        del ip.Completer.custom_matchers[idx]
