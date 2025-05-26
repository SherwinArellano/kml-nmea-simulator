from typing import TypeVar, Type


class CallParams: ...


T = TypeVar("T", bound=CallParams)


class CallContext:
    def __init__(self):
        self.params: dict[type[CallParams], CallParams] = {}

    def set(self, arg: CallParams):
        self.params[type(arg)] = arg

    def get(self, arg_type: Type[T]) -> T:
        val = self.params.get(arg_type)
        if not isinstance(val, arg_type):
            raise TypeError(f"Expected {arg_type}, got {type(val)}")
        return val
