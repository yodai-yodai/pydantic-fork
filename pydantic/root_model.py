"""RootModelクラスとタイプの定義。"""

from __future__ import annotations as _annotations

import typing
from copy import copy, deepcopy

from pydantic_core import PydanticUndefined

from . import PydanticUserError
from ._internal import _model_construction, _repr
from .main import BaseModel, _object_setattr

if typing.TYPE_CHECKING:
    from typing import Any

    from typing_extensions import Literal, Self, dataclass_transform

    from .fields import Field as PydanticModelField
    from .fields import PrivateAttr as PydanticModelPrivateAttr

    # dataclass_transform could be applied to RootModel directly, but `ModelMetaclass`'s dataclass_transform
    # takes priority (at least with pyright). We trick type checkers into thinking we apply dataclass_transform
    # on a new metaclass.
    @dataclass_transform(kw_only_default=False, field_specifiers=(PydanticModelField, PydanticModelPrivateAttr))
    class _RootModelMetaclass(_model_construction.ModelMetaclass): ...
else:
    _RootModelMetaclass = _model_construction.ModelMetaclass

__all__ = ('RootModel',)

RootModelRootType = typing.TypeVar('RootModelRootType')


class RootModel(BaseModel, typing.Generic[RootModelRootType], metaclass=_RootModelMetaclass):
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/models/#rootmodel-and-custom-root-types

    モデルのルートオブジェクト用のPydantic`BaseModel`です。

    Attributes:
        root: モデルのルートオブジェクト。
        __pydantic_root_model__: モデルがRootModelであるかどうか。
        __pydantic_private__: モデル内のprivateフィールド。
        __pydantic_extra__: モデル内の追加フィールド。
    """

    __pydantic_root_model__ = True
    __pydantic_private__ = None
    __pydantic_extra__ = None

    root: RootModelRootType

    def __init_subclass__(cls, **kwargs):
        extra = cls.model_config.get('extra')
        if extra is not None:
            raise PydanticUserError(
                "`RootModel` does not support setting `model_config['extra']`", code='root-model-extra'
            )
        super().__init_subclass__(**kwargs)

    def __init__(self, /, root: RootModelRootType = PydanticUndefined, **data) -> None:  # type: ignore
        __tracebackhide__ = True
        if data:
            if root is not PydanticUndefined:
                raise ValueError(
                    '"RootModel.__init__" accepts either a single positional argument or arbitrary keyword arguments'
                )
            root = data  # type: ignore
        self.__pydantic_validator__.validate_python(root, self_instance=self)

    __init__.__pydantic_base_init__ = True  # pyright: ignore[reportFunctionMemberAccess]

    @classmethod
    def model_construct(cls, root: RootModelRootType, _fields_set: set[str] | None = None) -> Self:  # type: ignore
        """指定されたルートオブジェクトを使用して新しいモデルを作成し、フィールドセットを更新します。

        Args:
            root: モデルのルートオブジェクト。
            _fields_set: 更新されるフィールドのセット。

        Returns:
            新しいモデル。

        Raises:
            NotImplemented: モデルが`RootModel`のサブクラスでない場合。
        """
        return super().model_construct(root=root, _fields_set=_fields_set)

    def __getstate__(self) -> dict[Any, Any]:
        return {
            '__dict__': self.__dict__,
            '__pydantic_fields_set__': self.__pydantic_fields_set__,
        }

    def __setstate__(self, state: dict[Any, Any]) -> None:
        _object_setattr(self, '__pydantic_fields_set__', state['__pydantic_fields_set__'])
        _object_setattr(self, '__dict__', state['__dict__'])

    def __copy__(self) -> Self:
        """モデルのシャローコピーを返します。"""
        cls = type(self)
        m = cls.__new__(cls)
        _object_setattr(m, '__dict__', copy(self.__dict__))
        _object_setattr(m, '__pydantic_fields_set__', copy(self.__pydantic_fields_set__))
        return m

    def __deepcopy__(self, memo: dict[int, Any] | None = None) -> Self:
        """モデルのディープコピーを返します。"""
        cls = type(self)
        m = cls.__new__(cls)
        _object_setattr(m, '__dict__', deepcopy(self.__dict__, memo=memo))
        # This next line doesn't need a deepcopy because __pydantic_fields_set__ is a set[str],
        # and attempting a deepcopy would be marginally slower.
        _object_setattr(m, '__pydantic_fields_set__', copy(self.__pydantic_fields_set__))
        return m

    if typing.TYPE_CHECKING:

        def model_dump(  # type: ignore
            self,
            *,
            mode: Literal['json', 'python'] | str = 'python',
            include: Any = None,
            exclude: Any = None,
            context: dict[str, Any] | None = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            round_trip: bool = False,
            warnings: bool | Literal['none', 'warn', 'error'] = True,
            serialize_as_any: bool = False,
        ) -> Any:
            """このメソッドは、型チェッカーの戻り値の型をより正確に取得するためだけに含まれています。
            実際には上書きが必要ないので、この`if TYPE_CHECKING:`ブロックに含まれています。

            引数の詳細については、`BaseModel.model_dump`のドキュメントを参照してください。

            一般に、`RootModelRootType`が`BaseModel`サブクラスではないと仮定すると、このメソッドの戻り値の型は`RootModelRootType`になります。`RootModelRootType`が`BaseModel`サブクラスである場合、戻り値の型は`dict[str, Any]`になります。これは`model_dump`呼び出しが再帰的であるためです。カスタムシリアライザの場合、戻り値の型は別のものになることもあります。
            したがって、ここでは"Any"を使用して、これらのケースをすべてキャッチします。
            """
            ...

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RootModel):
            return NotImplemented
        return self.model_fields['root'].annotation == other.model_fields['root'].annotation and super().__eq__(other)

    def __repr_args__(self) -> _repr.ReprArgs:
        yield 'root', self.root
