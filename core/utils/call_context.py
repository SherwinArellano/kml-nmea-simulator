from typing import TypeVar, Type, cast, Sequence


class CallParams: ...


T = TypeVar("T", bound=CallParams)


class CallContext:
    def __init__(self):
        self.params: dict[type[CallParams], CallParams] = {}

    def set(self, params: CallParams):
        self.params[type(params)] = params

    def get(self, cls_params: Type[T]) -> T:
        if cls_params not in self.params:
            raise KeyError(f"{cls_params.__name__} missing in context")
        val = self.params.get(cls_params)
        if not isinstance(val, cls_params):
            raise TypeError(f"Expected {cls_params}, got {type(val)}")
        return cast(T, val)

    def validate(self, EXPECTS: Sequence[type[CallParams]]):
        for expected in EXPECTS:
            if expected not in self.params:
                raise RuntimeError(f"Missing required param: {expected.__name__}")
