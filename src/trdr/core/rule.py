class Rule:
    def __init__(self):
        self.conditions = []
    
    def and_(self, condition: 'Rule') -> 'Rule':
        self.conditions.append(('AND', condition))
        return self
        
    def or_(self, condition: 'Rule') -> 'Rule':
        self.conditions.append(('OR', condition))
        return self

    def evaluate(self) -> bool:
        # This will be interesting - we'll need to evaluate
        # all conditions based on market data
        pass
