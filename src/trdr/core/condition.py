from typing import Callable
import operator
from .indicator import Indicator

class Condition:

    VALID_OPERATORS = {
        operator.lt, operator.le,
        operator.gt, operator.ge,
        operator.eq, operator.ne
    }

    def __init__(self, left: Indicator, operator: Callable, right: Indicator | float | int):
        self._validate_inputs(left, operator, right)
        self.left = left
        self.operator = operator
        self.right = right
    
    def _validate_inputs(self, left, operator, right):
        if not hasattr(left, 'value'):
            raise ValueError("Left side must be an indicator with a value() method")
        
        if operator not in self.VALID_OPERATORS:
            raise ValueError("Invalid operator. Must be a comparison operator")
        
        if not (hasattr(right, 'value') or isinstance(right, (int, float))):
            raise ValueError("Right side must be an indicator or a number")

    def evaluate(self) -> bool:
        left_value = self.left.value()
        right_value = (
            self.right.value() 
            if hasattr(self.right, 'value') 
            else self.right
        )
        return self.operator(left_value, right_value)
