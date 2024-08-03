"""関数呼び出しを検証するためのデコレータ"""

from __future__ import annotations as _annotations

import functools
from typing import TYPE_CHECKING, Any, Callable, TypeVar, overload

from ._internal import _typing_extra, _validate_call

__all__ = ('validate_call',)

if TYPE_CHECKING:
    from .config import ConfigDict

    AnyCallableT = TypeVar('AnyCallableT', bound=Callable[..., Any])


@overload
def validate_call(
    *, config: ConfigDict | None = None, validate_return: bool = False
) -> Callable[[AnyCallableT], AnyCallableT]: ...


@overload
def validate_call(func: AnyCallableT, /) -> AnyCallableT: ...


def validate_call(
    func: AnyCallableT | None = None,
    /,
    *,
    config: ConfigDict | None = None,
    validate_return: bool = False,
) -> AnyCallableT | Callable[[AnyCallableT], AnyCallableT]:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/validation_decorator/

    引数およびオプションで戻り値を検証する関数を囲むデコレートラッパーを返します。

    通常のデコレータ`@validate_call`として、または引数`@validate_call(...)`と共に使用できます。

    Args:
        func: デコレートする関数。
        config: 構成辞書。
        validate_return: 戻り値を検証するかどうか。

    Returns:
        The decorated function.
    """
    local_ns = _typing_extra.parent_frame_namespace()

    def validate(function: AnyCallableT) -> AnyCallableT:
        if isinstance(function, (classmethod, staticmethod)):
            name = type(function).__name__
            raise TypeError(f'The `@{name}` decorator should be applied after `@validate_call` (put `@{name}` on top)')

        validate_call_wrapper = _validate_call.ValidateCallWrapper(function, config, validate_return, local_ns)

        @functools.wraps(function)
        def wrapper_function(*args, **kwargs):
            return validate_call_wrapper(*args, **kwargs)

        wrapper_function.raw_function = function  # type: ignore

        return wrapper_function  # type: ignore

    if func:
        return validate(func)
    else:
        return validate
