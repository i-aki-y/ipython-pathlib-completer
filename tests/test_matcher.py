from unittest.mock import MagicMock, patch
import pytest
from pathlib import Path

from ipython_pathlib_completer.matcher import preprocess_context, create_pathlib_matcher


@pytest.mark.parametrize(
    "line_with_cursor, token",
    [
        ("p / 'docs' / re", "re"),
        ("p / 'docs'/re", "re"),
        ("p / 'docs'/", "/"),
        ("p / '[f", "[f"),
        ("p / ", ""),
    ],
)
def test_preprocess_context(line_with_cursor, token):
    """Tests that preprocess_context correctly separates code from the token."""
    mock_context = MagicMock()
    mock_context.line_with_cursor = line_with_cursor
    mock_context.cursor_position = len(line_with_cursor)
    mock_context.token = token

    expected_token = token
    if token.endswith("/"):
        expected_code = line_with_cursor
        expected_token = ""
    else:
        expected_code = line_with_cursor[: (len(line_with_cursor) - len(token))]

    code, resulting_token = preprocess_context(mock_context)

    assert code == expected_code
    assert resulting_token == expected_token


@patch("ipython_pathlib_completer.matcher.resolve_path_from_code")
def test_matcher_with_no_path_resolved(mock_resolve_path):
    """Tests that the matcher returns no completions if the path cannot be resolved."""
    mock_resolve_path.return_value = None
    matcher = create_pathlib_matcher()
    mock_context = MagicMock()
    mock_context.line_with_cursor = "p / "
    mock_context.cursor_position = 4
    mock_context.token = ""

    result = matcher(mock_context)

    # The @context_matcher decorator returns a dict
    assert result["completions"] == []


@patch("ipython_pathlib_completer.matcher.resolve_path_from_code")
def test_matcher_completions(mock_resolve_path, tmp_path: Path):
    """Tests basic file and directory completions."""
    # Setup: Create a dummy directory structure
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").touch()
    (test_dir / "another_file.log").touch()
    (test_dir / "subdir").mkdir()

    mock_resolve_path.return_value = test_dir

    # --- Test Case 1: Complete all entries ---
    matcher = create_pathlib_matcher()
    mock_context = MagicMock()
    mock_context.line_with_cursor = "p / "
    mock_context.cursor_position = 4
    mock_context.token = ""

    result = matcher(mock_context)

    expected_texts = {
        '"file1.txt"',
        '"another_file.log"',
        '"subdir" /',  # Corrected: removed trailing space
    }
    actual_texts = {c.text for c in result["completions"]}
    assert actual_texts == expected_texts

    # --- Test Case 2: Complete with a partial token "file" ---
    mock_context.line_with_cursor = "p / 'file"
    mock_context.cursor_position = 9
    mock_context.token = "file"

    result = matcher(mock_context)

    assert len(result["completions"]) == 1
    assert result["completions"][0].text == '"file1.txt"'


@patch("ipython_pathlib_completer.matcher.resolve_path_from_code")
def test_matcher_with_quotes(mock_resolve_path, tmp_path: Path):
    """Tests that the matcher respects the quote character setting."""
    test_dir = tmp_path / "test_dir_quotes"
    test_dir.mkdir()
    (test_dir / "a_file.txt").touch()

    mock_resolve_path.return_value = test_dir

    matcher = create_pathlib_matcher(quote="'")
    mock_context = MagicMock()
    mock_context.line_with_cursor = "p / "
    mock_context.cursor_position = 4
    mock_context.token = ""

    result = matcher(mock_context)

    assert len(result["completions"]) == 1
    assert result["completions"][0].text == "'a_file.txt'"
