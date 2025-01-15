from trdr.core.rule import Rule

class Strategy:
    def __init__(self, name: str):
        self.name = name
        self.entry_rule = None
        self.exit_rule = None
        self.position_rule = None
        self.risk_rule = None

    def entry(self, rule: Rule) -> 'Strategy':
        self.entry_rules = rule
        return self

    def exit(self, rule: Rule) -> 'Strategy':
        self.exit_rules = rule
        return self

    def position(self, rule: Rule) -> 'Strategy':
        self.position_rules = rule
        return self

    def risk(self, rule: Rule) -> 'Strategy':
        self.risk_rules = rule
        return self

    def validate(self) -> bool:
        return all([
            self.entry_rule,
            self.exit_rule,
            self.position_rule,
            self.risk_rule
        ])
