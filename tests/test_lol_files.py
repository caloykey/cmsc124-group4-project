import argparse
import re
import sys
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
SRC_DIR = TESTS_DIR.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from errors import format_error
from lexer.lexer import tokenize
from parser.syntax import check_syntax


# These programs should be rejected before execution.
# Each entry gives the expected phase and a pattern for the diagnostic.
EXPECTED_ERRORS = {
    "2_var_decl_outside_wazzup": ("SYNTAX ERROR", r"declar|WAZZUP"),
    "6_elseif_without_if": ("SYNTAX ERROR", r"MEBBE"),
    "7_else_without_if": ("SYNTAX ERROR", r"NO WAI"),
    "8_nested_all_of_any_of": ("SYNTAX ERROR", r"nest"),
    "9_nested_smoosh": ("SYNTAX ERROR", r"nest"),
    "11_loop_mismatched_closing_name": ("SYNTAX ERROR", r"label|looper|counter"),
    "13_obtw_not_on_own_line": ("LEXICAL ERROR", r"OBTW|TLDR|block comment"),
}

# Case 20 passes syntax. Calling a two-parameter function with zero
# arguments should produce a semantic error during execution.
MISSING_ARGUMENTS = "20_function_call_missing_parameters"

# Each string is one expected line of console output.
EXPECTED_OUTPUT = {
    "1.1_simple_program_no_wazzup": [
        "Hello, World!",
        "No WAZZUP BUHBYE block here",
    ],
    "1.2_simple_program_empty_wazzup": [
        "Empty WAZZUP BUHBYE is fine",
    ],
    "1.3_var_decl_no_initial_value": [
        "Declared x and name without values",
        "7",
        "Juan",
    ],
    "1.4_var_reassignment": ["5", "before", "11", "after", "now a string"],
    "3_if_elseif_else": ["A", "B", "C", "F"],
    "4_if_without_else": ["x is ten", "done"],
    "5_elseif_without_else": ["x is seven", "end"],
    "10_loop_increment_no_til": ["0", "1", "2", "3", "4", "done"],
    "12_btw_shares_line_with_statement": ["5", "6", "visible"],
    "14_visible_multiple_args_plus": [
        "Name: Juan",
        "Name: Juan, Age: 20",
        "Sum: 3",
        "single argument",
    ],
    "15_function_outside_hai_kthxbye": ["hello"],
    "16_function_no_parameters": ["Hello from a function!"],
    "17_function_two_parameters": ["7"],
    "18_function_call_no_parameters": ["HEY!", "HEY!", "5", "5"],
    "19_function_call_two_parameters": ["12", "42", "16"],
    "20.1_function_return_as_argument": ["25", "9"],
    "21_switch_case": ["Tuesday", "Unknown day"],
    "22_switch_case_no_breaks": ["two", "three", "default"],
    "23_switch_case_no_default": ["Tuesday", "end"],
    "24_comparison_statements": [
        "WIN", "FAIL", "WIN", "FAIL", "WIN", "FAIL",
        "WIN", "FAIL", "WIN", "FAIL",
        "WIN", "WIN",
        "FAIL", "WIN", "FAIL",
    ],
    "25_arithmetic_statements": [
        "10", "4", "21", "3", "3.5", "1", "7", "3", "-7", "3.75",
        "12", "21", "2", "2", "42",
    ],
}

PROFESSOR_CASES = set(EXPECTED_OUTPUT) | set(EXPECTED_ERRORS) | {MISSING_ARGUMENTS}

# The repository sample is checked separately from the professor's 29 cases.
EXPECTED_OUTPUT["sample"] = [
    "Hello, Carlos",
    "Current age: 20",
    "Next age: 21",
    "You are twenty.",
]


def case_sort_key(path):
    """Sort numbered files as 1.1, 1.2, 2, 3, ..., 20, 20.1."""
    prefix = path.stem.split("_")[0]

    if re.fullmatch(r"\d+(\.\d+)*", prefix):
        number = tuple(int(part) for part in prefix.split("."))
        return (0, number, path.as_posix())

    return (1, (), path.as_posix())


def find_cases():
    """Find all .lol files and include missing professor files as failures."""
    paths = list(TESTS_DIR.rglob("*.lol"))
    found_names = {path.stem for path in paths}

    for name in PROFESSOR_CASES - found_names:
        paths.append(TESTS_DIR / f"{name}.lol")

    return sorted(paths, key=case_sort_key)


def get_expectation(name, execute):
    if name in EXPECTED_ERRORS:
        return EXPECTED_ERRORS[name]

    if execute and name == MISSING_ARGUMENTS:
        return "SEMANTIC ERROR", r"argument|parameter|arity"

    if execute:
        return "RUN", None

    return "ACCEPT", None


def format_errors(errors):
    return "\n".join(format_error(error) for error in errors)


def check_output(path, actual):
    """Compare all printed text, including the final newline."""
    output_file = path.with_suffix(".out")

    if output_file.is_file():
        expected = output_file.read_text(encoding="utf-8-sig")
    elif path.stem in EXPECTED_OUTPUT:
        lines = EXPECTED_OUTPUT[path.stem]
        expected = "".join(line + "\n" for line in lines)

        # Accept either common display of the NUMBAR result 7.0 / 2.
        if path.stem == "25_arithmetic_statements":
            if actual == expected.replace("3.5\n", "3.50\n"):
                return "RUN", ""
    else:
        return "NO EXPECTATION", f"Add the expected output to {output_file.name}."

    if actual != expected:
        return "WRONG OUTPUT", f"Expected: {expected!r}\nActual:   {actual!r}"

    return "RUN", ""


def run_case(path, runtime=None):
    if not path.is_file():
        return "MISSING FILE", f"Could not find {path.name} under tests/."

    source = path.read_text(encoding="utf-8-sig")
    tokens, errors = tokenize(source)

    if errors:
        return "LEXICAL ERROR", format_errors(errors)

    if runtime is None:
        errors = check_syntax(tokens)
        if errors:
            return "SYNTAX ERROR", format_errors(errors)
        return "ACCEPT", ""

    parse_program, execute_program = runtime
    program, errors = parse_program(tokens)

    if errors:
        return "SYNTAX ERROR", format_errors(errors)

    output = []

    def read_input(variable_name):
        raise AssertionError(f"Unexpected input request for {variable_name}.")

    _, errors = execute_program(program, output.append, read_input)
    actual_output = "".join(output)

    if errors:
        if path.stem == MISSING_ARGUMENTS and actual_output:
            return "UNEXPECTED OUTPUT", repr(actual_output)
        return "SEMANTIC ERROR", format_errors(errors)

    if path.stem in EXPECTED_ERRORS or path.stem == MISSING_ARGUMENTS:
        return "RUN", "The program finished without the expected error."

    return check_output(path, actual_output)


def compare_case(path, runtime=None):
    expected, pattern = get_expectation(path.stem, execute=runtime is not None)

    try:
        actual, detail = run_case(path, runtime)
    except Exception as error:
        # Report a crash for this file and continue checking the others.
        actual = "CRASH"
        detail = f"{type(error).__name__}: {error}"

    passed = actual == expected

    if passed and pattern and not re.search(pattern, detail, re.IGNORECASE):
        passed = False
        detail = f"The error was about the wrong issue:\n{detail}"

    return expected, actual, passed, detail


def load_tests(loader, tests, pattern):
    """Also support python -m unittest discover -s tests."""
    suite = unittest.TestSuite()

    for path in find_cases():
        def check(current_path=path):
            expected, actual, passed, detail = compare_case(current_path)
            if not passed:
                raise AssertionError(
                    f"{current_path.name}: expected {expected}, got {actual}\n{detail}"
                )

        check.__name__ = path.relative_to(TESTS_DIR).as_posix()
        suite.addTest(unittest.FunctionTestCase(check))

    return suite


def main():
    parser = argparse.ArgumentParser(description="Compare LOLCODE test results.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run programs and check console output and semantic errors.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show diagnostics even when the expected error matched.",
    )
    args = parser.parse_args()

    runtime = None
    if args.execute:
        try:
            from parser.syntax import parse_program
            from semantics.interpreter import execute_program
        except ImportError as error:
            parser.exit(
                2,
                f"Execution needs parse_program() and execute_program().\n{error}\n",
            )
        runtime = (parse_program, execute_program)

    passed_cases = []
    failed_cases = []

    for path in find_cases():
        _, _, passed, _ = compare_case(path, runtime)
        case_id = path.stem.split("_", 1)[0]
        label = f"Test case {case_id}:"

        if passed:
            passed_cases.append(label)
        else:
            failed_cases.append(label)

    for label in passed_cases:
        print(f"{label:<16}PASS")

    if passed_cases and failed_cases:
        print()

    for label in failed_cases:
        print(f"{label:<16}FAIL")

    return int(bool(failed_cases))

if __name__ == "__main__":
    sys.exit(main())