from pyrift.choreomaps.enum import BinaryOperator, UnaryOperator
from pyrift.jobj import JList, JObj


class BaseExpression(JObj):
    pass

class NumberExpression(BaseExpression):
    value: float

class BooleanExpression(BaseExpression):
    value: bool

class StringExpression(BaseExpression):
    value: str

class NullExpression(BaseExpression):
    pass

class VariableExpression(BaseExpression):
    name: str

class IfExpression(BaseExpression):
    condition: BaseExpression
    yes: BaseExpression
    no: BaseExpression

class CallExpression(BaseExpression):
    func: BaseExpression
    args: JList[BaseExpression]

class AndExpression(BaseExpression):
    conditions: JList[BaseExpression]

class OrExpression(BaseExpression):
    conditions: JList[BaseExpression]

class FormatExpression(BaseExpression):
    text: str
    args: JList[BaseExpression]

class UnaryExpression(BaseExpression):
    value: BaseExpression
    operator: UnaryOperator

class BinaryExpression(BaseExpression):
    left: BaseExpression
    operator: BinaryOperator
    right: BaseExpression
