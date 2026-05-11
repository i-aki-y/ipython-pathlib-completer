import pytest
import parso
from pathlib import Path
from unittest.mock import Mock, MagicMock
import ipython_pathlib_completer.path_expression_parser as pep_module
from ast import literal_eval

from ipython_pathlib_completer import (
    extract_div_sequence,
    extract_pathlib_path_string,
    validate_pathlib_path_is_defined,
    build_path_object_from_parts,
)


def test_extract_div_sequence():
    code = "Path() / 'a' / 'b' / "
    parts = extract_div_sequence(code)
    assert [p.type for p in parts] == ["atom_expr", "string", "string"]
    assert parts[0].children[0].value == "Path"
    assert parts[1].value == "'a'"
    assert parts[2].value == "'b'"


def test_extract_div_sequence_with_assignment():
    code = "x = Path() / 'a' / 'b' / "
    parts = extract_div_sequence(code)
    assert [p.type for p in parts] == ["atom_expr", "string", "string"]
    assert parts[0].children[0].value == "Path"
    assert parts[1].value == "'a'"
    assert parts[2].value == "'b'"


def test_extract_div_sequence_in_func_call():
    code = "func( Path() / 'a' / 'b' / "
    parts = extract_div_sequence(code)
    assert [p.type for p in parts] == ["atom_expr", "string", "string"]
    assert parts[0].children[0].value == "Path"
    assert parts[1].value == "'a'"
    assert parts[2].value == "'b'"


def test_extract_div_sequence_no_div():
    code = "Path()"
    assert len(extract_div_sequence(code)) == 0


def test_extract_div_sequence_no_parts():
    code = " / "
    assert len(extract_div_sequence(code)) == 0


def test_extract_div_sequence_no_parts_with_prefix():
    code = "func( / "
    assert len(extract_div_sequence(code)) == 0


def test_extract_div_sequence_not_end_with_slash():
    code = "a / b / c "
    assert len(extract_div_sequence(code)) == 0


def _get_atom_expr_node(code):
    module = parso.parse(code)
    return module.children[0]


def test_extract_pathlib_path_string_empty():
    node = _get_atom_expr_node("Path()")
    assert extract_pathlib_path_string(node) == "./"


def test_extract_pathlib_path_string_with_arg():
    node = _get_atom_expr_node('Path("foo/bar")')
    assert extract_pathlib_path_string(node) == '"foo/bar"'


def test_extract_pathlib_path_string_not_path():
    node = _get_atom_expr_node("list()")
    assert extract_pathlib_path_string(node) is None


def test_extract_pathlib_path_string_invalid_node_type():
    node = _get_atom_expr_node("my_var")
    assert node.type == "name"
    assert extract_pathlib_path_string(node) is None


@pytest.fixture
def mock_ipython_shell():
    """Fixture to mock the IPython shell and its namespace."""
    shell = Mock()
    shell.user_ns = {}
    shell.user_global_ns = {}

    mock_get_ipython = Mock(return_value=shell)

    original_get_ipython = pep_module.get_ipython
    pep_module.get_ipython = mock_get_ipython

    yield shell

    pep_module.get_ipython = original_get_ipython


def test_validate_pathlib_path_is_defined_true(mock_ipython_shell):
    mock_ipython_shell.user_ns["Path"] = Path
    assert validate_pathlib_path_is_defined(mock_ipython_shell) is True


def test_validate_pathlib_path_is_defined_false(mock_ipython_shell):
    mock_ipython_shell.user_ns["Path"] = "not a path"
    assert validate_pathlib_path_is_defined(mock_ipython_shell) is False


def test_validate_pathlib_path_is_defined_not_present(mock_ipython_shell):
    assert validate_pathlib_path_is_defined(mock_ipython_shell) is False


def test_build_path_object_from_parts_simple_path_constructor(mock_ipython_shell):
    mock_ipython_shell.user_ns["Path"] = Path
    code = 'Path("foo") / "bar"/'
    parts = extract_div_sequence(code)

    original_guarded_eval = pep_module.guarded_eval

    def side_effect_eval(code, context):
        if code in ["'bar'", '"foo"']:
            return literal_eval(code)
        if code == "Path":
            return Path
        return original_guarded_eval(code, context)

    pep_module.guarded_eval = MagicMock(side_effect=side_effect_eval)

    result = build_path_object_from_parts(parts)
    assert result == Path("foo") / "bar"

    pep_module.guarded_eval = original_guarded_eval


def test_build_path_object_from_parts_from_variable(mock_ipython_shell):
    my_path = Path("/start/dir")
    mock_ipython_shell.user_ns["my_path"] = my_path
    code = "my_path / 'next' / "
    parts = extract_div_sequence(code)

    original_guarded_eval = pep_module.guarded_eval

    def side_effect_eval(code, context):
        if code == "my_path":
            return my_path
        if code == "'next'":
            return literal_eval(code)
        return original_guarded_eval(code, context)

    pep_module.guarded_eval = MagicMock(side_effect=side_effect_eval)

    result = build_path_object_from_parts(parts)
    assert result == my_path / "next"

    pep_module.guarded_eval = original_guarded_eval

def test_build_path_object_from_parts_from_attribute(mock_ipython_shell):

    class Foo:
        def __init__(self):
            self.my_path = Path("/start/dir")

    foo = Foo()
    mock_ipython_shell.user_ns["foo"] = foo
    code = "foo.my_path / 'next' / "
    parts = extract_div_sequence(code)

    original_guarded_eval = pep_module.guarded_eval

    def side_effect_eval(code, context):
        if code == "foo.my_path":
            return foo.my_path
        if code == "'next'":
            return literal_eval(code)
        return original_guarded_eval(code, context)

    pep_module.guarded_eval = MagicMock(side_effect=side_effect_eval)

    result = build_path_object_from_parts(parts)
    assert result == foo.my_path / "next"

    pep_module.guarded_eval = original_guarded_eval


def test_build_path_object_from_parts_invalid_path_keyword(mock_ipython_shell):
    mock_ipython_shell.user_ns["Path"] = "not a path"
    code = 'Path("foo") / "bar" /'
    parts = extract_div_sequence(code)

    result = build_path_object_from_parts(parts)
    assert result is None


def test_build_path_object_from_parts_failure_undefined_var(mock_ipython_shell):
    mock_ipython_shell.user_ns["Path"] = Path
    code = "my_var / 'a' /"
    parts = extract_div_sequence(code)

    original_guarded_eval = pep_module.guarded_eval

    def side_effect_eval(code, context):
        if code == "my_var":
            raise NameError("name 'my_var' is not defined")
        if code == "'a'":
            return literal_eval(code)
        if code == "Path":
            return Path
        return original_guarded_eval(code, context)

    pep_module.guarded_eval = MagicMock(side_effect=side_effect_eval)

    result = build_path_object_from_parts(parts)
    assert result is None

    pep_module.guarded_eval = original_guarded_eval
