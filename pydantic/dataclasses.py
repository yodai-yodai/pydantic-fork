"""Provide an enhanced dataclass that performs validation."""

from __future__ import annotations as _annotations

import dataclasses
import sys
import types
from typing import TYPE_CHECKING, Any, Callable, Generic, NoReturn, TypeVar, overload

from typing_extensions import Literal, TypeGuard, dataclass_transform

from ._internal import _config, _decorators, _typing_extra
from ._internal import _dataclasses as _pydantic_dataclasses
from ._migration import getattr_migration
from .config import ConfigDict
from .errors import PydanticUserError
from .fields import Field, FieldInfo, PrivateAttr

if TYPE_CHECKING:
    from ._internal._dataclasses import PydanticDataclass

__all__ = 'dataclass', 'rebuild_dataclass'

_T = TypeVar('_T')

if sys.version_info >= (3, 10):

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    @overload
    def dataclass(
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
        kw_only: bool = ...,
        slots: bool = ...,
    ) -> Callable[[type[_T]], type[PydanticDataclass]]:  # type: ignore
        ...

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    @overload
    def dataclass(
        _cls: type[_T],  # type: ignore
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
        kw_only: bool = ...,
        slots: bool = ...,
    ) -> type[PydanticDataclass]: ...

else:

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    @overload
    def dataclass(
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
    ) -> Callable[[type[_T]], type[PydanticDataclass]]:  # type: ignore
        ...

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    @overload
    def dataclass(
        _cls: type[_T],  # type: ignore
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
    ) -> type[PydanticDataclass]: ...


@dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
def dataclass(
    _cls: type[_T] | None = None,
    *,
    init: Literal[False] = False,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    config: ConfigDict | type[object] | None = None,
    validate_on_init: bool | None = None,
    kw_only: bool = False,
    slots: bool = False,
) -> Callable[[type[_T]], type[PydanticDataclass]] | type[PydanticDataclass]:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/dataclasses

    Pydanticで強化されたデータクラスを作成するために使用されるデコレータで、標準のPython`dataclass`に似ていますが、検証が追加されています。

    この関数は`dataclasses.dataclass`と同じように使用してください。

    Args:
        _cls:ターゲットの`dataclass`です。
        init: `dataclasses.dataclass`を参照してください。
        repr: フィールドを`__repr__`出力に含めるかどうかを示すブール値です。
        eq: クラスに対して`__eq__`メソッドを生成するかどうかを決定します。
        order: `__lt__`のような比較マジック・メソッドを生成すべきかどうかを決定します。
        unsafe_hash: `dataclasses.dataclass`のように、クラスに`__hash__`メソッドを含めるかどうかを決定します。
        frozen: 生成されたクラスが'frozen'な`dataclass`であるべきかどうかを決定します。これは、初期化された後に属性を変更できないようにします。
        config: `dataclass`に使用するPydanticの設定です。
        validate_on_init: 後方互換性のために廃止されたパラメーターです。V2では、すべてのPydanticデータクラスがinitで検証されます。
        kw_only: `__init__`メソッドのパラメータをキーワードのみで指定する必要があるかどうかを決定します。デフォルトは`False`です。
        slots: 生成されたクラスが、インスタンス化後に新しい属性を追加できない'slots'`dataclass`であるかどうかを決定します。

    Returns:
        引数としてクラスを受け入れ、Pydanticの`dataclass`を返すデコレータ。

    Raises:
        AssertionError: `init`が`False`でない場合、または`validate_on_init`が`False`の場合に発生します。
    """
    assert init is False, 'pydantic.dataclasses.dataclass only supports init=False'
    assert validate_on_init is not False, 'validate_on_init=False is no longer supported'

    if sys.version_info >= (3, 10):
        kwargs = dict(kw_only=kw_only, slots=slots)
    else:
        kwargs = {}

    def make_pydantic_fields_compatible(cls: type[Any]) -> None:
        """stdlib`dataclasses`が`kw_only`のような`Field`kwargsを処理することを確認してください。
        そのためには、単に`x:int=pydantic.Field(.,kw_only=True)`を`x:int=dataclasses.field(default=pydantic.Field(.,kw_only=True),kw_only=True)`に変更します。
        """
        for annotation_cls in cls.__mro__:
            # In Python < 3.9, `__annotations__` might not be present if there are no fields.
            # we therefore need to use `getattr` to avoid an `AttributeError`.
            annotations = getattr(annotation_cls, '__annotations__', [])
            for field_name in annotations:
                field_value = getattr(cls, field_name, None)
                # Process only if this is an instance of `FieldInfo`.
                if not isinstance(field_value, FieldInfo):
                    continue

                # Initialize arguments for the standard `dataclasses.field`.
                field_args: dict = {'default': field_value}

                # Handle `kw_only` for Python 3.10+
                if sys.version_info >= (3, 10) and field_value.kw_only:
                    field_args['kw_only'] = True

                # Set `repr` attribute if it's explicitly specified to be not `True`.
                if field_value.repr is not True:
                    field_args['repr'] = field_value.repr

                setattr(cls, field_name, dataclasses.field(**field_args))
                # In Python 3.8, dataclasses checks cls.__dict__['__annotations__'] for annotations,
                # so we must make sure it's initialized before we add to it.
                if cls.__dict__.get('__annotations__') is None:
                    cls.__annotations__ = {}
                cls.__annotations__[field_name] = annotations[field_name]

    def create_dataclass(cls: type[Any]) -> type[PydanticDataclass]:
        """通常のデータクラスからPydanticデータクラスを作成します。

        Args:
            cls: Pydanticデータ・クラスの作成元のクラス。

        Returns:
            Pydanticデータクラス。
        """
        from ._internal._utils import is_model_class

        if is_model_class(cls):
            raise PydanticUserError(
                f'Cannot create a Pydantic dataclass from {cls.__name__} as it is already a Pydantic model',
                code='dataclass-on-model',
            )

        original_cls = cls

        # if config is not explicitly provided, try to read it from the type
        config_dict = config if config is not None else getattr(cls, '__pydantic_config__', None)
        config_wrapper = _config.ConfigWrapper(config_dict)
        decorators = _decorators.DecoratorInfos.build(cls)

        # Keep track of the original __doc__ so that we can restore it after applying the dataclasses decorator
        # Otherwise, classes with no __doc__ will have their signature added into the JSON schema description,
        # since dataclasses.dataclass will set this as the __doc__
        original_doc = cls.__doc__

        if _pydantic_dataclasses.is_builtin_dataclass(cls):
            # Don't preserve the docstring for vanilla dataclasses, as it may include the signature
            # This matches v1 behavior, and there was an explicit test for it
            original_doc = None

            # We don't want to add validation to the existing std lib dataclass, so we will subclass it
            #   If the class is generic, we need to make sure the subclass also inherits from Generic
            #   with all the same parameters.
            bases = (cls,)
            if issubclass(cls, Generic):
                generic_base = Generic[cls.__parameters__]  # type: ignore
                bases = bases + (generic_base,)
            cls = types.new_class(cls.__name__, bases)

        make_pydantic_fields_compatible(cls)

        cls = dataclasses.dataclass(  # type: ignore[call-overload]
            cls,
            # the value of init here doesn't affect anything except that it makes it easier to generate a signature
            init=True,
            repr=repr,
            eq=eq,
            order=order,
            unsafe_hash=unsafe_hash,
            frozen=frozen,
            **kwargs,
        )

        cls.__pydantic_decorators__ = decorators  # type: ignore
        cls.__doc__ = original_doc
        cls.__module__ = original_cls.__module__
        cls.__qualname__ = original_cls.__qualname__
        pydantic_complete = _pydantic_dataclasses.complete_dataclass(
            cls, config_wrapper, raise_errors=False, types_namespace=None
        )
        cls.__pydantic_complete__ = pydantic_complete  # type: ignore
        return cls

    return create_dataclass if _cls is None else create_dataclass(_cls)


__getattr__ = getattr_migration(__name__)

if (3, 8) <= sys.version_info < (3, 11):
    # Monkeypatch dataclasses.InitVar so that typing doesn't error if it occurs as a type when evaluating type hints
    # Starting in 3.11, typing.get_type_hints will not raise an error if the retrieved type hints are not callable.

    def _call_initvar(*args: Any, **kwargs: Any) -> NoReturn:
        """この関数は、このmonkeypatchなしで`InitVar[int]()`を呼び出した場合に発生するエラーと可能な限り類似したエラーを発生させるだけです。
        全体の目的は、型指定を確実にすることだけです。型ヒントが`InitVar[<parameter>]`と評価された場合、_type_checkはエラーになりません。
        """
        raise TypeError("'InitVar' object is not callable")

    dataclasses.InitVar.__call__ = _call_initvar


def rebuild_dataclass(
    cls: type[PydanticDataclass],
    *,
    force: bool = False,
    raise_errors: bool = True,
    _parent_namespace_depth: int = 2,
    _types_namespace: dict[str, Any] | None = None,
) -> bool | None:
    """データクラスのpydantic-coreスキーマを再構築してみてください。

    これは、最初にスキーマを構築しようとしたときに解決できなかったForwardRefが注釈の1つであり、自動再構築が失敗した場合に必要になることがあります。

    これは`BaseModel.model_rebuild`と似ています。

    Args:
        cls: pydantic-coreスキーマを再構築するクラス。
        force: スキーマの再構築を強制するかどうか。デフォルトは`False`です。
        raise_errors: エラーを発生させるかどうか。デフォルトは`True`です。
        _parent_namespace_depth: 親ネームスペースのデプスレベル。デフォルトは2です。
        _types_namespace: タイプの名前空間で、デフォルトは`None`です。

    Returns:
        スキーマが既に"完了"していて、再構築が必要なかった場合は`None`を返します。
        rebuilding_was_requiredの場合、再構築が成功した場合は`True`を返し、それ以外の場合は`False`を返します。
    """
    if not force and cls.__pydantic_complete__:
        return None
    else:
        if _types_namespace is not None:
            types_namespace: dict[str, Any] | None = _types_namespace.copy()
        else:
            if _parent_namespace_depth > 0:
                frame_parent_ns = _typing_extra.parent_frame_namespace(parent_depth=_parent_namespace_depth) or {}
                # Note: we may need to add something similar to cls.__pydantic_parent_namespace__ from BaseModel
                #   here when implementing handling of recursive generics. See BaseModel.model_rebuild for reference.
                types_namespace = frame_parent_ns
            else:
                types_namespace = {}

            types_namespace = _typing_extra.get_cls_types_namespace(cls, types_namespace)
        return _pydantic_dataclasses.complete_dataclass(
            cls,
            _config.ConfigWrapper(cls.__pydantic_config__, check=False),
            raise_errors=raise_errors,
            types_namespace=types_namespace,
        )


def is_pydantic_dataclass(class_: type[Any], /) -> TypeGuard[type[PydanticDataclass]]:
    """クラスが暗号化されたデータクラスかどうか。

    Args:
        class_: クラス。

    Returns:
        クラスがpydanticデータクラスであれば`True`、そうでなければ`False`です。
    """
    try:
        return '__pydantic_validator__' in class_.__dict__ and dataclasses.is_dataclass(class_)
    except AttributeError:
        return False
