from pyrift.jobj import JList, JObj

from .expression import BaseExpression


class BaseInstruction(JObj):
    pass

class IfInstruction(BaseInstruction):
    condition: BaseExpression
    yes: JList[BaseInstruction]
    no: JList[BaseInstruction]

class SetVariableInstruction(BaseInstruction):
    name: str
    expr: BaseExpression

class CreateObjectInstruction(BaseInstruction):
    pass

class GetAttributeInstruction(BaseInstruction):
    pass

class SetAttributeInstruction(BaseInstruction):
    pass

class ReturnInstruction(BaseInstruction):
    expr: BaseExpression
