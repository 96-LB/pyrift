from typing import TYPE_CHECKING

from pyrift.jobj import JList, JObj

from ..vars import VarType

if TYPE_CHECKING:
    from .expression import BaseExpression


class BaseInstruction(JObj):
    pass

class NullInstruction(BaseInstruction):
    pass

class IfInstruction(BaseInstruction):
    condition: BaseExpression
    yes: JList[BaseInstruction]
    no: JList[BaseInstruction]

class WhileInstruction(BaseInstruction):
    condition: BaseExpression
    body: JList[BaseInstruction]

class SetVariableInstruction(BaseInstruction):
    name: str
    expr: BaseExpression

class DeclareVariablesInstruction(BaseInstruction):
    name: JList[str]
    type: VarType

class CreateObjectInstruction(BaseInstruction):
    pass

class GetAttributeInstruction(BaseInstruction):
    pass

class SetAttributeInstruction(BaseInstruction):
    pass

class ReturnInstruction(BaseInstruction):
    expr: BaseExpression

class BreakInstruction(BaseInstruction):
    should_continue: bool
