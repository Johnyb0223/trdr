from trdr.core.strategy.interfaces import ILogicalExpression

class Strategy:
    def __init__(self, name: str, description: str = None):
        self.name = name
        self.description = None
        self.entry_expression: ILogicalExpression = None
        self.exit_expression: ILogicalExpression = None
        self.sizing_expression: ILogicalExpression = None

    def entry(self, expression: ILogicalExpression) -> 'Strategy':
        self.entry_expression = expression
        return self

    def exit(self, expression: ILogicalExpression) -> 'Strategy':
        self.exit_expression = expression
        return self

    def sizing(self, expression: ILogicalExpression) -> 'Strategy':
        self.sizing_expression = expression
        return self

    def validate(self) -> bool:
        return all([
            self.entry_expression,
            self.exit_expression,
            self.sizing_expression
        ])

