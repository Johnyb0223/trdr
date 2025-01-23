from typing import List, Optional
from trdr.core.strategy.interfaces import ILogicalExpression, IIndicator
from typing import Callable
import operator

class LogicalGroup(ILogicalExpression):
    """Represents a group of conditions combined with AND/OR"""
    def __init__(self, type: str):
        if type not in ['all_of', 'any_of']:
            raise ValueError("Type must be 'all_of' or 'any_of'")
        self.type = type
        self.expressions: List[ILogicalExpression] = []
    
    def all_of(self, expression: ILogicalExpression) -> 'LogicalGroup':
        """Start a new all_of group nested under this group"""
        new_group = LogicalGroup('all_of')
        self.expressions.append(new_group)
        return new_group
    
    def any_of(self, expression: ILogicalExpression) -> 'LogicalGroup':
        """Start a new any_of group nested under this group"""
        new_group = LogicalGroup('any_of')
        self.expressions.append(new_group)
        return new_group
    
    def condition(self, expression: ILogicalExpression) -> 'LogicalGroup':
        """Add a condition to this group"""
        self.expressions.append(expression)
        return self
    
    def end(self) -> Optional['LogicalGroup']:
        """End this group and return to parent"""
        return self.parent
    
    def evaluate(self) -> bool:
        if self.type == 'all_of':
            return all(expr.evaluate() for expr in self.expressions)
        return any(expr.evaluate() for expr in self.expressions)

class LogicalCondition(ILogicalExpression):
    VALID_OPERATORS = {
        operator.lt, operator.le,
        operator.gt, operator.ge,
        operator.eq, operator.ne
    }

    def __init__(self, left: IIndicator, operator: Callable, right: IIndicator | float | int):
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