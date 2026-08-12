from pyrift.jobj import JList, JObj

from .instruction import BaseInstruction


class Script(JObj):
    instructions: JList[BaseInstruction]
