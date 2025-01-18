from dataclasses import dataclass
from enum import Enum, auto
from typing import List

class TokenType(Enum):
    INDENT = auto()
    DEDENT = auto()
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    OPERATOR = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    line: int

class LexerError(Exception):
    """Raised when the lexer encounters invalid input"""
    pass

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.indent_stack = [0]  # Stack to track indentation levels
        self.at_line_start = True
        
    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < len(self.text):
            char = self.text[self.pos]
            
            # Handle indentation at start of line
            if self.at_line_start:
                indent_level = self._count_indent()
                tokens.extend(self._handle_indentation(indent_level))
                self.at_line_start = False
                continue
            
            # Skip whitespace
            if char.isspace() and char != '\n':
                self._advance()
                continue
            
            # Handle different token types
            if char == '(':
                tokens.append(Token(TokenType.LEFT_PAREN, '(', self.line))
                self._advance()
            
            elif char == ')':
                tokens.append(Token(TokenType.RIGHT_PAREN, ')', self.line))
                self._advance()
            
            elif char == '"':
                tokens.append(self._tokenize_string())
            
            elif char.isdigit():
                tokens.append(self._tokenize_number())
            
            elif char.isalpha():
                tokens.append(self._tokenize_identifier())
            
            elif char in '><!=*':
                tokens.append(self._tokenize_operator())
            
            elif char == '\n':
                self.line += 1
                self.at_line_start = True
                self._advance()
            
            else:
                raise LexerError(f"Unexpected character '{char}' at line {self.line}")
        
        # Handle any remaining dedents at EOF
        tokens.extend(self._handle_indentation(0))
        tokens.append(Token(TokenType.EOF, '', self.line))
        
        return tokens
    
    def _advance(self):
        """Advance position"""
        self.pos += 1
    
    def _count_indent(self) -> int:
        """Count the indentation level of the current line"""
        indent = 0
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            if self.text[self.pos] == ' ':
                indent += 1
            elif self.text[self.pos] == '\t':
                indent += 8  # Convert tabs to spaces (standard Python behavior)
            self._advance()
        return indent
    
    def _handle_indentation(self, indent_level: int) -> List[Token]:
        """Handle indentation changes and emit INDENT/DEDENT tokens"""
        tokens = []
        current_indent = self.indent_stack[-1]
        
        if indent_level > current_indent:
            tokens.append(Token(TokenType.INDENT, '', self.line))
            self.indent_stack.append(indent_level)
        
        while indent_level < current_indent:
            tokens.append(Token(TokenType.DEDENT, '', self.line))
            self.indent_stack.pop()
            current_indent = self.indent_stack[-1]
            
            if indent_level > current_indent:
                raise LexerError(f"Invalid dedent at line {self.line}")
        
        return tokens
    
    def _tokenize_string(self) -> Token:
        """Tokenize a string literal"""
        start_pos = self.pos
        self._advance()  # Skip opening quote
        
        while self.pos < len(self.text) and self.text[self.pos] != '"':
            if self.text[self.pos] == '\n':
                raise LexerError(f"Unterminated string at line {self.line}")
            self._advance()
        
        if self.pos >= len(self.text):
            raise LexerError(f"Unterminated string at line {self.line}")
        
        self._advance()  # Skip closing quote
        value = self.text[start_pos:self.pos]
        return Token(TokenType.STRING, value, self.line)
    
    def _tokenize_number(self) -> Token:
        """Tokenize a number"""
        start_pos = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] == '.'):
            self._advance()
        
        value = self.text[start_pos:self.pos]
        return Token(TokenType.NUMBER, value, self.line)
    
    def _tokenize_identifier(self) -> Token:
        """Tokenize an identifier"""
        start_pos = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self._advance()
        
        value = self.text[start_pos:self.pos]
        return Token(TokenType.IDENTIFIER, value, self.line)
    
    def _tokenize_operator(self) -> Token:
        """Tokenize an operator"""
        start_pos = self.pos
        while self.pos < len(self.text) and self.text[self.pos] in '><!=*':
            self._advance()
        
        value = self.text[start_pos:self.pos]
        return Token(TokenType.OPERATOR, value, self.line)

if __name__ == "__main__":
    test_input = \
'''
strategy
    name "First Strategy"
    description "Simple moving average crossover strategy"
    entry
        all_of
            any_of
                MA20 > MA50
                MA20 > MA100
            any_of
                RSI < 30
                VOLUME > 1000000
            PORTFOLIO_EXPOSURE < 0.25
            OPEN_POSITIONS < 5
            AVAILABLE_CASH > 1000
            STOCK_VALUE > 100
    exit
        PRICE > (ENTRY * 1.06)
        MA20 < MA50
        PRICE < (ENTRY * 0.98)
    sizing
        PORTFOLIO_PERCENT == 0.05
'''
    
    lexer = Lexer(test_input)
    tokens = lexer.tokenize()
    for token in tokens:
        print(f"{token.type}: '{token.value}' at line {token.line}")
