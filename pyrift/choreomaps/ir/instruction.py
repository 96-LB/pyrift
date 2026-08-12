from pyrift.jobj import JList, JObj

from .expression import BaseExpression


class BaseInstruction(JObj):
    pass

class IfInstruction(BaseInstruction):
    condition: BaseExpression
    yes: JList[BaseInstruction]
    no: JList[BaseInstruction]

class SetVariableInstruction(BaseInstruction):
    var: BaseExpression
    value: BaseExpression

class FunctionInstruction(BaseInstruction):
    name: str
    args: JList[str]
    instructions: JList[BaseInstruction]

class CreateObjectInstruction(BaseInstruction):
    pass

class GetAttributeInstruction(BaseInstruction):
    pass

class SetAttributeInstruction(BaseInstruction):
    pass

class ReturnInstruction(BaseInstruction):
    value: BaseExpression
