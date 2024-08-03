"""This module contains related classes and functions for validation."""

from __future__ import annotations as _annotations

import dataclasses
import sys
from functools import partialmethod
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, TypeVar, Union, cast, overload

from pydantic_core import core_schema
from pydantic_core import core_schema as _core_schema
from typing_extensions import Annotated, Literal, TypeAlias

from . import GetCoreSchemaHandler as _GetCoreSchemaHandler
from ._internal import _core_metadata, _decorators, _generics, _internal_dataclass
from .annotated_handlers import GetCoreSchemaHandler
from .errors import PydanticUserError

if sys.version_info < (3, 11):
    from typing_extensions import Protocol
else:
    from typing import Protocol

_inspect_validator = _decorators.inspect_validator


@dataclasses.dataclass(frozen=True, **_internal_dataclass.slots_true)
class AfterValidator:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/validators/#annotated-validators

    内部検証ロジックの**後**に検証を適用する必要があることを示すメタデータクラス。

    Attributes:
        func: バリデーター関数。

    Example:
        ```py
        from typing_extensions import Annotated

        from pydantic import AfterValidator, BaseModel, ValidationError

        MyInt = Annotated[int, AfterValidator(lambda v: v + 1)]

        class Model(BaseModel):
            a: MyInt

        print(Model(a=1).a)
        #> 2

        try:
            Model(a='a')
        except ValidationError as e:
            print(e.json(indent=2))
            '''
            [
              {
                "type": "int_parsing",
                "loc": [
                  "a"
                ],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "a",
                "url": "https://errors.pydantic.dev/2/v/int_parsing"
              }
            ]
            '''
        ```
    """

    func: core_schema.NoInfoValidatorFunction | core_schema.WithInfoValidatorFunction

    def __get_pydantic_core_schema__(self, source_type: Any, handler: _GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = _inspect_validator(self.func, 'after')
        if info_arg:
            func = cast(core_schema.WithInfoValidatorFunction, self.func)
            return core_schema.with_info_after_validator_function(func, schema=schema, field_name=handler.field_name)
        else:
            func = cast(core_schema.NoInfoValidatorFunction, self.func)
            return core_schema.no_info_after_validator_function(func, schema=schema)


@dataclasses.dataclass(frozen=True, **_internal_dataclass.slots_true)
class BeforeValidator:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/validators/#annotated-validators

    内部検証ロジックの**前**に検証を適用する必要があることを示すメタデータクラス。

    Attributes:
        func: バリデーター関数。

    Example:
        ```py
        from typing_extensions import Annotated

        from pydantic import BaseModel, BeforeValidator

        MyInt = Annotated[int, BeforeValidator(lambda v: v + 1)]

        class Model(BaseModel):
            a: MyInt

        print(Model(a=1).a)
        #> 2

        try:
            Model(a='a')
        except TypeError as e:
            print(e)
            #> can only concatenate str (not "int") to str
        ```
    """

    func: core_schema.NoInfoValidatorFunction | core_schema.WithInfoValidatorFunction

    def __get_pydantic_core_schema__(self, source_type: Any, handler: _GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = _inspect_validator(self.func, 'before')
        if info_arg:
            func = cast(core_schema.WithInfoValidatorFunction, self.func)
            return core_schema.with_info_before_validator_function(func, schema=schema, field_name=handler.field_name)
        else:
            func = cast(core_schema.NoInfoValidatorFunction, self.func)
            return core_schema.no_info_before_validator_function(func, schema=schema)


@dataclasses.dataclass(frozen=True, **_internal_dataclass.slots_true)
class PlainValidator:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/validators/#annotated-validators

    内部検証ロジックの**代わりに**検証を適用する必要があることを示すメタデータクラス。

    Attributes:
        func: バリデーター関数。

    Example:
        ```py
        from typing_extensions import Annotated

        from pydantic import BaseModel, PlainValidator

        MyInt = Annotated[int, PlainValidator(lambda v: int(v) + 1)]

        class Model(BaseModel):
            a: MyInt

        print(Model(a='1').a)
        #> 2
        ```
    """

    func: core_schema.NoInfoValidatorFunction | core_schema.WithInfoValidatorFunction

    def __get_pydantic_core_schema__(self, source_type: Any, handler: _GetCoreSchemaHandler) -> core_schema.CoreSchema:
        # Note that for some valid uses of PlainValidator, it is not possible to generate a core schema for the
        # source_type, so calling `handler(source_type)` will error, which prevents us from generating a proper
        # serialization schema. To work around this for use cases that will not involve serialization, we simply
        # catch any PydanticSchemaGenerationError that may be raised while attempting to build the serialization schema
        # and abort any attempts to handle special serialization.
        from pydantic import PydanticSchemaGenerationError

        try:
            schema = handler(source_type)
            serialization = core_schema.wrap_serializer_function_ser_schema(function=lambda v, h: h(v), schema=schema)
        except PydanticSchemaGenerationError:
            serialization = None

        info_arg = _inspect_validator(self.func, 'plain')
        if info_arg:
            func = cast(core_schema.WithInfoValidatorFunction, self.func)
            return core_schema.with_info_plain_validator_function(
                func, field_name=handler.field_name, serialization=serialization
            )
        else:
            func = cast(core_schema.NoInfoValidatorFunction, self.func)
            return core_schema.no_info_plain_validator_function(func, serialization=serialization)


@dataclasses.dataclass(frozen=True, **_internal_dataclass.slots_true)
class WrapValidator:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/validators/#annotated-validators

    内部検証ロジックの**周辺**に検証を適用する必要があることを示すメタデータクラス。

    Attributes:
        func:バリデーター関数。

    ```py
    from datetime import datetime

    from typing_extensions import Annotated

    from pydantic import BaseModel, ValidationError, WrapValidator

    def validate_timestamp(v, handler):
        if v == 'now':
            # we don't want to bother with further validation, just return the new value
            return datetime.now()
        try:
            return handler(v)
        except ValidationError:
            # validation failed, in this case we want to return a default value
            return datetime(2000, 1, 1)

    MyTimestamp = Annotated[datetime, WrapValidator(validate_timestamp)]

    class Model(BaseModel):
        a: MyTimestamp

    print(Model(a='now').a)
    #> 2032-01-02 03:04:05.000006
    print(Model(a='invalid').a)
    #> 2000-01-01 00:00:00
    ```
    """

    func: core_schema.NoInfoWrapValidatorFunction | core_schema.WithInfoWrapValidatorFunction

    def __get_pydantic_core_schema__(self, source_type: Any, handler: _GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = _inspect_validator(self.func, 'wrap')
        if info_arg:
            func = cast(core_schema.WithInfoWrapValidatorFunction, self.func)
            return core_schema.with_info_wrap_validator_function(func, schema=schema, field_name=handler.field_name)
        else:
            func = cast(core_schema.NoInfoWrapValidatorFunction, self.func)
            return core_schema.no_info_wrap_validator_function(func, schema=schema)


if TYPE_CHECKING:

    class _OnlyValueValidatorClsMethod(Protocol):
        def __call__(self, cls: Any, value: Any, /) -> Any: ...

    class _V2ValidatorClsMethod(Protocol):
        def __call__(self, cls: Any, value: Any, info: _core_schema.ValidationInfo, /) -> Any: ...

    class _V2WrapValidatorClsMethod(Protocol):
        def __call__(
            self,
            cls: Any,
            value: Any,
            handler: _core_schema.ValidatorFunctionWrapHandler,
            info: _core_schema.ValidationInfo,
            /,
        ) -> Any: ...

    _V2Validator = Union[
        _V2ValidatorClsMethod,
        _core_schema.WithInfoValidatorFunction,
        _OnlyValueValidatorClsMethod,
        _core_schema.NoInfoValidatorFunction,
    ]

    _V2WrapValidator = Union[
        _V2WrapValidatorClsMethod,
        _core_schema.WithInfoWrapValidatorFunction,
    ]

    _PartialClsOrStaticMethod: TypeAlias = Union[classmethod[Any, Any, Any], staticmethod[Any, Any], partialmethod[Any]]

    _V2BeforeAfterOrPlainValidatorType = TypeVar(
        '_V2BeforeAfterOrPlainValidatorType',
        bound=Union[_V2Validator, _PartialClsOrStaticMethod],
    )
    _V2WrapValidatorType = TypeVar('_V2WrapValidatorType', bound=Union[_V2WrapValidator, _PartialClsOrStaticMethod])


@overload
def field_validator(
    field: str,
    /,
    *fields: str,
    mode: Literal['before', 'after', 'plain'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_V2BeforeAfterOrPlainValidatorType], _V2BeforeAfterOrPlainValidatorType]: ...


@overload
def field_validator(
    field: str,
    /,
    *fields: str,
    mode: Literal['wrap'],
    check_fields: bool | None = ...,
) -> Callable[[_V2WrapValidatorType], _V2WrapValidatorType]: ...


FieldValidatorModes: TypeAlias = Literal['before', 'after', 'wrap', 'plain']


def field_validator(
    field: str,
    /,
    *fields: str,
    mode: FieldValidatorModes = 'after',
    check_fields: bool | None = None,
) -> Callable[[Any], Any]:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/validators/#field-validators

    クラスのメソッドをデコレートして、フィールドの検証に使用する必要があることを示します。

    Example usage:
    ```py
    from typing import Any

    from pydantic import (
        BaseModel,
        ValidationError,
        field_validator,
    )

    class Model(BaseModel):
        a: str

        @field_validator('a')
        @classmethod
        def ensure_foobar(cls, v: Any):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    print(repr(Model(a='this is foobar good')))
    #> Model(a='this is foobar good')

    try:
        Model(a='snap')
    except ValidationError as exc_info:
        print(exc_info)
        '''
        1 validation error for Model
        a
          Value error, "foobar" not found in a [type=value_error, input_value='snap', input_type=str]
        '''
    ```

    詳細な例については、[Field Validators](https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/validators.md#field-validators)を参照してください。

    Args:
        field: `field_validator`が呼び出される最初のフィールドです。これは`fields`とは別のもので、少なくとも1つ渡さないとエラーが発生します。
        *fields: `field_validator`が呼び出される追加フィールドです。
        mode: 検証の前または後にフィールドを検証するかどうかを指定します。
        check_fields: フィールドがモデル上に実際に存在するかどうかをチェックするかどうか。

    Returns:
        field_validatorとして使用する関数を修飾するために使用できるデコレータ。

    Raises:
        PydantictUserError:
            - `@field_validator`が(フィールドなしで)使用されている場合。
            - フィールドとして`@field_validator`に渡された引数が文字列でない場合。
            - `@field_validator`がインスタンスメソッドに適用された場合。
    """
    if isinstance(field, FunctionType):
        raise PydanticUserError(
            '`@field_validator` should be used with fields and keyword arguments, not bare. '
            "E.g. usage should be `@validator('<field_name>', ...)`",
            code='validator-no-fields',
        )
    fields = field, *fields
    if not all(isinstance(field, str) for field in fields):
        raise PydanticUserError(
            '`@field_validator` fields should be passed as separate string args. '
            "E.g. usage should be `@validator('<field_name_1>', '<field_name_2>', ...)`",
            code='validator-invalid-fields',
        )

    def dec(
        f: Callable[..., Any] | staticmethod[Any, Any] | classmethod[Any, Any, Any],
    ) -> _decorators.PydanticDescriptorProxy[Any]:
        if _decorators.is_instance_method_from_sig(f):
            raise PydanticUserError(
                '`@field_validator` cannot be applied to instance methods', code='validator-instance-method'
            )

        # auto apply the @classmethod decorator
        f = _decorators.ensure_classmethod_based_on_signature(f)

        dec_info = _decorators.FieldValidatorDecoratorInfo(fields=fields, mode=mode, check_fields=check_fields)
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    return dec


_ModelType = TypeVar('_ModelType')
_ModelTypeCo = TypeVar('_ModelTypeCo', covariant=True)


class ModelWrapValidatorHandler(_core_schema.ValidatorFunctionWrapHandler, Protocol[_ModelTypeCo]):
    """@model_validatorデコレート関数ハンドラ引数タイプ。これは`mode='wrap'`のときに使用されます。"""

    def __call__(  # noqa: D102
        self,
        value: Any,
        outer_location: str | int | None = None,
        /,
    ) -> _ModelTypeCo:  # pragma: no cover
        ...


class ModelWrapValidatorWithoutInfo(Protocol[_ModelType]):
    """@model_validatorでデコレートされた関数のシグネチャ。
    これは、`mode='wrap'`で関数にinfo引数がない場合に使用されます。
    """

    def __call__(  # noqa: D102
        self,
        cls: type[_ModelType],
        # this can be a dict, a model instance
        # or anything else that gets passed to validate_python
        # thus validators _must_ handle all cases
        value: Any,
        handler: ModelWrapValidatorHandler[_ModelType],
        /,
    ) -> _ModelType: ...


class ModelWrapValidator(Protocol[_ModelType]):
    """@model_validatorでデコレートされた関数のシグネチャ。これは`mode='wrap'`のときに使用されます。"""

    def __call__(  # noqa: D102
        self,
        cls: type[_ModelType],
        # this can be a dict, a model instance
        # or anything else that gets passed to validate_python
        # thus validators _must_ handle all cases
        value: Any,
        handler: ModelWrapValidatorHandler[_ModelType],
        info: _core_schema.ValidationInfo,
        /,
    ) -> _ModelType: ...


class FreeModelBeforeValidatorWithoutInfo(Protocol):
    """@model_validatorでデコレートされた関数のシグネチャ。
    これは、`mode='before'`で関数にinfo引数がない場合に使用されます。
    """

    def __call__(  # noqa: D102
        self,
        # this can be a dict, a model instance
        # or anything else that gets passed to validate_python
        # thus validators _must_ handle all cases
        value: Any,
        /,
    ) -> Any: ...


class ModelBeforeValidatorWithoutInfo(Protocol):
    """@model_validatorデコレータ関数のシグネチャ。
    これは、`mode='before'`で関数にinfo引数がない場合に使用されます。
    """

    def __call__(  # noqa: D102
        self,
        cls: Any,
        # this can be a dict, a model instance
        # or anything else that gets passed to validate_python
        # thus validators _must_ handle all cases
        value: Any,
        /,
    ) -> Any: ...


class FreeModelBeforeValidator(Protocol):
    """`@model_validator`でデコレートされた関数のシグネチャ。これは`mode='before'`のときに使用されます。"""

    def __call__(  # noqa: D102
        self,
        # this can be a dict, a model instance
        # or anything else that gets passed to validate_python
        # thus validators _must_ handle all cases
        value: Any,
        info: _core_schema.ValidationInfo,
        /,
    ) -> Any: ...


class ModelBeforeValidator(Protocol):
    """`@model_validator`でデコレートされた関数のシグネチャ。これは`mode='before'`のときに使用されます。"""

    def __call__(  # noqa: D102
        self,
        cls: Any,
        # this can be a dict, a model instance
        # or anything else that gets passed to validate_python
        # thus validators _must_ handle all cases
        value: Any,
        info: _core_schema.ValidationInfo,
        /,
    ) -> Any: ...


ModelAfterValidatorWithoutInfo = Callable[[_ModelType], _ModelType]
"""`@model_validator`でデコレートされた関数のシグネチャ。これは、`mode='after'`で、関数にinfo引数がない場合に使用されます。
"""

ModelAfterValidator = Callable[[_ModelType, _core_schema.ValidationInfo], _ModelType]
"""`@model_validator`でデコレートされた関数のシグネチャ。これは`mode='after'`のときに使用されます。"""

_AnyModelWrapValidator = Union[ModelWrapValidator[_ModelType], ModelWrapValidatorWithoutInfo[_ModelType]]
_AnyModeBeforeValidator = Union[
    FreeModelBeforeValidator, ModelBeforeValidator, FreeModelBeforeValidatorWithoutInfo, ModelBeforeValidatorWithoutInfo
]
_AnyModelAfterValidator = Union[ModelAfterValidator[_ModelType], ModelAfterValidatorWithoutInfo[_ModelType]]


@overload
def model_validator(
    *,
    mode: Literal['wrap'],
) -> Callable[
    [_AnyModelWrapValidator[_ModelType]], _decorators.PydanticDescriptorProxy[_decorators.ModelValidatorDecoratorInfo]
]: ...


@overload
def model_validator(
    *,
    mode: Literal['before'],
) -> Callable[
    [_AnyModeBeforeValidator], _decorators.PydanticDescriptorProxy[_decorators.ModelValidatorDecoratorInfo]
]: ...


@overload
def model_validator(
    *,
    mode: Literal['after'],
) -> Callable[
    [_AnyModelAfterValidator[_ModelType]], _decorators.PydanticDescriptorProxy[_decorators.ModelValidatorDecoratorInfo]
]: ...


def model_validator(
    *,
    mode: Literal['wrap', 'before', 'after'],
) -> Any:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/validators/#model-validators

    Decorate model methods for validation purposes.
    検証のためにモデルメソッドをデコレートする。

    Example usage:
    ```py
    from typing_extensions import Self

    from pydantic import BaseModel, ValidationError, model_validator

    class Square(BaseModel):
        width: float
        height: float

        @model_validator(mode='after')
        def verify_square(self) -> Self:
            if self.width != self.height:
                raise ValueError('width and height do not match')
            return self

    s = Square(width=1, height=1)
    print(repr(s))
    #> Square(width=1.0, height=1.0)

    try:
        Square(width=1, height=2)
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Square
          Value error, width and height do not match [type=value_error, input_value={'width': 1, 'height': 2}, input_type=dict]
        '''
    ```

    詳細な例については、[Model Validators](https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/validators.md#model-validators)を参照してください。


    Args:
        mode: 検証モードを指定する必須文字列リテラル。'wrap'、'before'、または'after'のいずれかです。

    Returns:
        モデルバリデータとして使用される関数をデコレートするために使用できるデコレータ。
    """

    def dec(f: Any) -> _decorators.PydanticDescriptorProxy[Any]:
        # auto apply the @classmethod decorator
        f = _decorators.ensure_classmethod_based_on_signature(f)
        dec_info = _decorators.ModelValidatorDecoratorInfo(mode=mode)
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    return dec


AnyType = TypeVar('AnyType')


if TYPE_CHECKING:
    # If we add configurable attributes to IsInstance, we'd probably need to stop hiding it from type checkers like this
    InstanceOf = Annotated[AnyType, ...]  # `IsInstance[Sequence]` will be recognized by type checkers as `Sequence`

else:

    @dataclasses.dataclass(**_internal_dataclass.slots_true)
    class InstanceOf:
        '''特定のクラスのインスタンスであるタイプに注釈を付けるための汎用タイプ。

        Example:
            ```py
            from pydantic import BaseModel, InstanceOf

            class Foo:
                ...

            class Bar(BaseModel):
                foo: InstanceOf[Foo]

            Bar(foo=Foo())
            try:
                Bar(foo=42)
            except ValidationError as e:
                print(e)
                """
                [
                │   {
                │   │   'type': 'is_instance_of',
                │   │   'loc': ('foo',),
                │   │   'msg': 'Input should be an instance of Foo',
                │   │   'input': 42,
                │   │   'ctx': {'class': 'Foo'},
                │   │   'url': 'https://errors.pydantic.dev/0.38.0/v/is_instance_of'
                │   }
                ]
                """
            ```
        '''

        @classmethod
        def __class_getitem__(cls, item: AnyType) -> AnyType:
            return Annotated[item, cls()]

        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            from pydantic import PydanticSchemaGenerationError

            # use the generic _origin_ as the second argument to isinstance when appropriate
            instance_of_schema = core_schema.is_instance_schema(_generics.get_origin(source) or source)

            try:
                # Try to generate the "standard" schema, which will be used when loading from JSON
                original_schema = handler(source)
            except PydanticSchemaGenerationError:
                # If that fails, just produce a schema that can validate from python
                return instance_of_schema
            else:
                # Use the "original" approach to serialization
                instance_of_schema['serialization'] = core_schema.wrap_serializer_function_ser_schema(
                    function=lambda v, h: h(v), schema=original_schema
                )
                return core_schema.json_or_python_schema(python_schema=instance_of_schema, json_schema=original_schema)

        __hash__ = object.__hash__


if TYPE_CHECKING:
    SkipValidation = Annotated[AnyType, ...]  # SkipValidation[list[str]] will be treated by type checkers as list[str]
else:

    @dataclasses.dataclass(**_internal_dataclass.slots_true)
    class SkipValidation:
        """これが注釈として適用される場合(例えば、`x:Annotated[int, SkipValidation]`)、検証はスキップされます。`SkipValidation[int]`を`Annotated[int, SkipValidation]`の省略形として使用することもできます。

        これは、ドキュメント/IDE/型チェックの目的で型アノテーションを使用し、1つ以上のフィールドの検証を省略しても安全であることがわかっている場合に便利です。

        これは検証スキーマを`any_schema`に変換するので、後続のアノテーション適用変換は期待された効果を持たない可能性があります。したがって、使用される場合、このアノテーションは通常、型に適用される最後のアノテーションである必要があります。
        """

        def __class_getitem__(cls, item: Any) -> Any:
            return Annotated[item, SkipValidation()]

        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            original_schema = handler(source)
            metadata = _core_metadata.build_metadata_dict(js_annotation_functions=[lambda _c, h: h(original_schema)])
            return core_schema.any_schema(
                metadata=metadata,
                serialization=core_schema.wrap_serializer_function_ser_schema(
                    function=lambda v, h: h(v), schema=original_schema
                ),
            )

        __hash__ = object.__hash__
