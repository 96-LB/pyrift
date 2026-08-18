from pyrift.choreomaps.enum import BinaryOperator, ComparisonMode, UnaryOperator
from pyrift.jobj import JList

from .instruction import BaseInstruction


class BaseExpression(BaseInstruction):
    pass

class NullExpression(BaseExpression):
    pass

class NumberExpression(BaseExpression):
    value: float

class BooleanExpression(BaseExpression):
    value: bool

class StringExpression(BaseExpression):
    value: str

class FunctionExpression(BaseExpression):
    args: JList[str]
    body: JList[BaseInstruction]
    is_async: bool

class VariableExpression(BaseExpression):
    name: str

class IfExpression(BaseExpression):
    condition: BaseExpression
    yes: BaseExpression
    no: BaseExpression

class CallExpression(BaseExpression):
    func: BaseExpression
    args: JList[BaseExpression]

class NotExpression(BaseExpression):
    condition: BaseExpression

class AndExpression(BaseExpression):
    conditions: JList[BaseExpression]

class OrExpression(BaseExpression):
    conditions: JList[BaseExpression]

class FormatExpression(BaseExpression):
    text: str
    args: JList[BaseExpression]

class UnaryExpression(BaseExpression):
    expr: BaseExpression
    operator: UnaryOperator

class BinaryExpression(BaseExpression):
    left: BaseExpression
    operator: BinaryOperator
    right: BaseExpression

class CompareExpression(BaseExpression):
    first: BaseExpression
    operands: JList[BaseExpression]
    operators: JList[ComparisonMode]

class JoinExpression(BaseExpression):
    strings: JList[BaseExpression]

class AwaitExpression(BaseExpression):
    expr: BaseExpression
