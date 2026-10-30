from .backend import (
    ArrayValue,
    FinishLevelEvent,
    GraphicCreateEvent,
    JoinString,
    LogEvent,
    MathValue,
    SetArrayEvent,
    SetVariableEvent,
    SpriteEvent,
    SpriteIDValue,
    SpriteStringEvent,
    String,
    TaggedValue,
    VariableValue,
)
from .builtin import Builtin, builtin
from .compiler import ChoreomapCompiler
from .enum import (
    BinaryOperator,
    GraphicType,
    SpriteAttribute,
    SpriteStringAttribute,
    VisualType,
)
from .vars import Tag


@builtin
def print(compiler: ChoreomapCompiler, arg: String) -> None:
    compiler.add_event(LogEvent(arg))

@builtin
def wait(compiler: ChoreomapCompiler, seconds: TaggedValue) -> Builtin:
    def wait_seconds(compiler: ChoreomapCompiler) -> None:
        compiler.context.wait(seconds[1])
    
    with compiler.match(seconds[0]) as case:
        with case(Tag.NUMBER):
            pass
        with case():
            # TODO: compile-time error for typechecking
            compiler.raise_exception('wait() argument must be a number.')
    
    return Builtin('wait', wait_seconds, is_async=True)


def create_graphic(compiler: ChoreomapCompiler, type: GraphicType) -> TaggedValue:
    ref = VariableValue('$GRAPHIC')
    id = SpriteIDValue(VisualType.GRAPHIC, ref)
    # increment the heap counter
    compiler.add_event(SetVariableEvent('$GRAPHIC', MathValue(ref, 1, BinaryOperator.ADD)))
    # create the text graphic
    compiler.add_event(GraphicCreateEvent(ref, None, type))
    compiler.add_event(SpriteEvent(id, SpriteAttribute.POSITION, None, 0, 0, 0, 0))
    # return a pointer to the text graphic
    tag_index, value_index = compiler.context.allocate_temp()
    compiler.add_event(SetArrayEvent(None, tag_index, Tag.NUMBER))
    compiler.add_event(SetArrayEvent(None, value_index, id))
    return ArrayValue(None, tag_index), ArrayValue(None, value_index)

@builtin
def text(compiler: ChoreomapCompiler) -> TaggedValue:
    return create_graphic(compiler, GraphicType.CANVAS_TEXT)

@builtin
def set_text(compiler: ChoreomapCompiler, id: TaggedValue, text: String) -> None:
    # TODO: type-checking on id parameter
    with compiler.match(id[0]) as case:
        with case(Tag.STRING):
            compiler.add_event(SpriteStringEvent(id[1], SpriteStringAttribute.TEXT, text))
        with case():
            compiler.raise_exception('set_text() argument must be a string.')

@builtin
def sprite(compiler: ChoreomapCompiler) -> TaggedValue:
    return create_graphic(compiler, GraphicType.CANVAS)

@builtin
def set_sprite(compiler: ChoreomapCompiler, sprite: TaggedValue, texture: String) -> None:
    # TODO: type-checking on texture parameter
    with compiler.match(sprite[0]) as case:
        with case(Tag.STRING):
            id = VariableValue(JoinString(('TEXTURE$', texture)))
            compiler.add_event(SpriteEvent(sprite[1], SpriteAttribute.TEXTURE, None, id))
        with case():
            compiler.raise_exception('set_sprite() argument must be a string.')


@builtin
def exit(compiler: ChoreomapCompiler) -> None:
    compiler.add_event(FinishLevelEvent(False))


@builtin
def win(compiler: ChoreomapCompiler) -> None:
    compiler.add_event(FinishLevelEvent(True))
