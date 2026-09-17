from .base import BaseContext


class ChoreomapContext(BaseContext):
    @abstractmethod
    def __init__(self, parent: BaseContext):
        self.parent = parent
        self.status = ContextStatus.INACTIVE
    
    def __len__(self) -> int:
        return len(self.parent)
    
    def __enter__(self) -> Self:
        if self.status is not ContextStatus.INACTIVE:
            raise ValueError('Match context has already been entered.')
        self.status = ContextStatus.ACTIVE
        return self
    
    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        if self.status is not ContextStatus.ACTIVE:
            raise ValueError('Match context is not active.')
        self.status = ContextStatus.FINISHED
    
    @property
    def is_async(self) -> bool:
        return self.parent.is_async
    
    def add_event(self, event: BaseEvent) -> None:
        self.parent.add_event(event)
    
    def replace_event(self, index: int, event: BaseEvent) -> None:
        self.parent.replace_event(index, event)
    
    def lookup(self, name: str) -> tuple[int, VarType]:
        return self.parent.lookup(name)
    
    def allocate_temp(self) -> tuple[int, int]:
        return self.parent.allocate_temp()
    
    def push_stack(self, instruction: BaseInstruction) -> None:
        self.parent.push_stack(instruction)
    
    def pop_stack(self) -> BaseInstruction:
        return self.parent.pop_stack()
    
    def get_parent_instruction(self) -> type[BaseInstruction]:
        return self.parent.get_parent_instruction()
    
    def wait(self, seconds: Value) -> None:
        self.parent.wait(seconds)
    
    def begin_control_flow(self) -> None:
        self.parent.begin_control_flow()
    
    def return_value(self, tag: Value, value: Value) -> None:
        self.parent.return_value(tag, value)
