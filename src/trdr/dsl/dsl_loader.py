from typing import Optional
import os
from .lexer import Lexer
from .parser import Parser, ParserError
from .dsl_ast import StrategyAST


class StrategyDSLLoader:
    """
    Loads and parses trading strategy files written in the TRDR domain-specific language.

    This class is responsible for:
    1. Finding strategy files in the strategies directory
    2. Reading their contents
    3. Passing the content through the lexer and parser
    4. Returning the abstract syntax tree (AST) representing the strategy

    The DSL loader provides useful error messages when parsing fails,
    including line numbers and suggestions for fixing common syntax issues.

    Attributes:
        strategies_dir: Directory where .trdr strategy files are located
    """

    def __init__(self, strategies_dir: Optional[str] = None):
        """
        Initialize the DSL loader with an optional custom strategies directory.

        Args:
            strategies_dir: Custom directory for strategy files, defaults to ./strategies
        """
        # Allow customization of the strategies directory.
        self.strategies_dir = strategies_dir or os.path.join(os.getcwd(), "strategies")

    def load(self, filename: str) -> StrategyAST:
        """
        Load a strategy DSL file, parse it, and return the StrategyAST.

        This method handles the entire process of loading a strategy from file to
        executable abstract syntax tree. It automatically appends the .trdr extension
        if not provided in the filename.

        Args:
            filename: Name of the strategy file (with or without .trdr extension)

        Returns:
            StrategyAST: Abstract syntax tree representing the parsed strategy

        Raises:
            FileNotFoundError: If the strategy file cannot be found
            ParserError: If there are syntax errors in the strategy file
            Various lexer errors for tokenization issues
        """
        file_path = self._get_file_path(filename)
        file_content = self._read_file(file_path)
        return self._parse_dsl(file_content, file_path)

    def _get_file_path(self, filename: str) -> str:
        if not filename.endswith(".trdr"):
            filename += ".trdr"
        return os.path.join(self.strategies_dir, filename)

    def _read_file(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Strategy file not found: {file_path}")
        with open(file_path, "r") as file:
            return file.read()

    def _parse_dsl(self, file_content: str, file_path: str) -> StrategyAST:
        try:
            lexer = Lexer(file_content)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            return ast
        except ParserError as pe:
            # Here you can format the error message, include the file path,
            # the error line, a snippet of the content, plus suggestions
            error_line = getattr(pe, "line", None)
            snippet = None
            if error_line is not None:
                file_lines = file_content.splitlines()
                if 0 < error_line <= len(file_lines):
                    snippet = file_lines[error_line - 1]
            suggestion = (
                "Double-check your DSL syntax near the indicated line. Common issues "
                "include missing quotes, incorrect indentation, or misused composite operators (all_of/any_of)."
            )
            error_message = f"Error parsing DSL in '{file_path}' at line {error_line}:\n"
            if snippet:
                error_message += f">> {snippet}\n"
            error_message += suggestion
            raise ParserError(error_message, pe.line) from pe


if __name__ == "__main__":
    loader = StrategyDSLLoader(strategies_dir="src/trdr/test_utils/strategies")
    ast = loader.load("test_strat")
    print(ast)
