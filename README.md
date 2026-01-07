# IPython Pathlib Completer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An extension for IPython that provides shell-like path autocompletion for `pathlib.Path` objects.

## Overview

This completer enables to interactively explore filesystem when using `pathlib` expressions in IPython sessions, including those in Jupyter and JupyterLab environments. It triggers after the division (`/`) operator on a `Path` object, suggesting the next possible file or directory, like tab-completion in a Unix shell.

For example, typing `Path('/usr')  / 'bin' / <TAB>` will provide completions for files and directories within `/usr/bin/`.

## Features

-   **Handles Variables and Constructors**: Works with existing `Path` objects stored in variables (e.g., `my_path / ...`) and new `Path` constructors (e.g., `Path('~') / ...`).
-   **Easy to Enable/Disable**: Can be toggled on and off within an active IPython session.
-   **Safe**: Uses IPython's `guarded_eval` to safely evaluate expressions without side effects.

## Installation

You can install the package directly from the source directory:

```bash
pip install .
```

## Usage

To use the completer in an IPython session, simply import and run the `enable_pathlib_completer` function.

```python
from ipython_pathlib_completer import enable_pathlib_completer

# Enable the completer
enable_pathlib_completer()
```

### Example

Once enabled, you can use tab completion on `pathlib.Path` expressions.

```python
from pathlib import Path

# Create a Path object
p = Path.home()

# Type the following and press <TAB> after the final slash
p / 'Documents' / 

# IPython will suggest files and directories inside your Documents folder.
# -> p / 'Documents' / 'reports' / 
# -> p / 'Documents' / 'presentation.pptx'
```

To disable the completer at any time:

```python
from ipython_pathlib_completer import disable_pathlib_completer

disable_pathlib_completer()
```

## Debugging

If you need to debug the completer's behavior, you can enable file-based logging.

```python
from ipython_pathlib_completer.utils import enable_debug_log

enable_debug_log("completer-debug.log")
```
This will write detailed debug information to `completer-debug.log`.

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
