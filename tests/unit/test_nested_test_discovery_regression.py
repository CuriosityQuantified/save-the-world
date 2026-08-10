"""
Regression tests for issue #23: a `test_*` function nested inside another
function is unreachable dead code -- pytest only collects module-level
functions and methods of `Test*` classes, so a nested test silently never
runs while masquerading as coverage.

Concretely, `test_create_idea_final_turn_fallback_parsing` had been defined
*inside* `test_create_idea_live_groq_call` in `tests/unit/test_llm_service.py`.
The nested copy was never collected. These tests parse the AST of every
`tests/unit/test_*.py` file (offline, no imports of the scanned files) and
lock in that no `test_*` function is nested inside another function.
"""
import ast
from pathlib import Path

TESTS_UNIT_DIR = Path(__file__).resolve().parent


def _find_nested_test_functions(tree):
    """Return (test_func_name, enclosing_func_name) pairs for nested tests.

    A `test_*` function is a bug when its *nearest enclosing scope* is another
    function (FunctionDef/AsyncFunctionDef). Module-level functions and methods
    of a class (e.g. `class Test...`) are fine -- pytest collects those.
    """
    offenders = []

    def walk(node, enclosing_func):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if enclosing_func is not None and child.name.startswith("test"):
                    offenders.append((child.name, enclosing_func))
                # Descend into the function body; its own nearest enclosing
                # scope is now `child`.
                walk(child, child.name)
            elif isinstance(child, ast.ClassDef):
                # A class body resets the "enclosing function" context: methods
                # of a `Test*` class are collectable by pytest.
                walk(child, None)
            else:
                walk(child, enclosing_func)

    walk(tree, None)
    return offenders


class TestNoNestedTestFunctions:
    """No `test_*` function may hide inside another function in tests/unit."""

    def test_no_test_function_nested_in_another_function(self):
        """Every `test_*` func must be module-level or a class method."""
        all_offenders = []
        # Every collectable `test_*.py` file in tests/unit.
        for path in sorted(TESTS_UNIT_DIR.glob("test_*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for test_name, enclosing in _find_nested_test_functions(tree):
                all_offenders.append((path.name, test_name, enclosing))

        assert not all_offenders, (
            "Found test function(s) nested inside another function -- pytest "
            "never collects these, so they are unreachable dead code:\n"
            + "\n".join(
                f"  {fname}: {test} is nested inside {enclosing}"
                for fname, test, enclosing in all_offenders
            )
        )


class TestFallbackParsingIsTopLevel:
    """Lock in the exact #23 fix in test_llm_service.py."""

    def _llm_service_tree(self):
        path = TESTS_UNIT_DIR / "test_llm_service.py"
        assert path.exists(), f"expected {path} to exist"
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_fallback_parsing_defined_exactly_once_at_module_level(self):
        """`test_create_idea_final_turn_fallback_parsing` is a direct child of Module."""
        tree = self._llm_service_tree()
        module_level = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        count = module_level.count("test_create_idea_final_turn_fallback_parsing")
        assert count == 1, (
            "test_create_idea_final_turn_fallback_parsing must be defined exactly "
            f"once at module level in test_llm_service.py; found {count} "
            f"module-level definition(s)."
        )

    def test_fallback_parsing_not_nested_in_live_groq_call(self):
        """It must not be nested inside test_create_idea_live_groq_call (the #23 bug)."""
        tree = self._llm_service_tree()
        offenders = _find_nested_test_functions(tree)
        bad = [
            (test, enclosing)
            for test, enclosing in offenders
            if test == "test_create_idea_final_turn_fallback_parsing"
        ]
        assert not bad, (
            "test_create_idea_final_turn_fallback_parsing is nested inside "
            f"{bad[0][1]} in test_llm_service.py -- pytest will never collect it. "
            "It must be a top-level function (issue #23)."
        )
