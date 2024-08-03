"""このモジュールには、シリアル化のための関連クラスと関数が含まれています。"""

from __future__ import annotations

import dataclasses
from functools import partialmethod
from typing import TYPE_CHECKING, Any, Callable, TypeVar, Union, overload

from pydantic_core import PydanticUndefined, core_schema
from pydantic_core import core_schema as _core_schema
from typing_extensions import Annotated, Literal, TypeAlias

from . import PydanticUndefinedAnnotation
from ._internal import _decorators, _internal_dataclass
from .annotated_handlers import GetCoreSchemaHandler


@dataclasses.dataclass(**_internal_dataclass.slots_true, frozen=True)
class PlainSerializer:
    """普通のシリアライザは、シリアライゼーションの出力を変更するために関数を使用します。

    これは特に、アノテーション付き型のシリアライゼーションをカスタマイズしたい場合に役立ちます。
    スペースで区切られた文字列にシリアライズされる`list`の入力を考えてみましょう。

    ```python
    from typing import List

    from typing_extensions import Annotated

    from pydantic import BaseModel, PlainSerializer

    CustomStr = Annotated[
        List, PlainSerializer(lambda x: ' '.join(x), return_type=str)
    ]

    class StudentModel(BaseModel):
        courses: CustomStr

    student = StudentModel(courses=['Math', 'Chemistry', 'English'])
    print(student.model_dump())
    #> {'courses': 'Math Chemistry English'}
    ```

    Attributes:
        func: シリアライザ関数。
        return_type: 関数の戻り型。省略した場合は、型注釈から推測されます。
        when_used: このシリアライザをいつ使用すべきかを決定します。「always」、「unless-none」、「json」、「json-unless-none」の値を持つ文字列を受け入れます。デフォルトは「always」です。
    """

    func: core_schema.SerializerFunction
    return_type: Any = PydanticUndefined
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        """Pydanticコアスキーマを取得します。

        Args:
            source_type: ソース・タイプ。
            handler: `GetCoreSchemaHandler`インスタンスです。

        Returns:
            Pydanticコアスキーマ。
        """
        schema = handler(source_type)
        try:
            return_type = _decorators.get_function_return_type(
                self.func, self.return_type, handler._get_types_namespace()
            )
        except NameError as e:
            raise PydanticUndefinedAnnotation.from_name_error(e) from e
        return_schema = None if return_type is PydanticUndefined else handler.generate_schema(return_type)
        schema['serialization'] = core_schema.plain_serializer_function_ser_schema(
            function=self.func,
            info_arg=_decorators.inspect_annotated_serializer(self.func, 'plain'),
            return_schema=return_schema,
            when_used=self.when_used,
        )
        return schema


@dataclasses.dataclass(**_internal_dataclass.slots_true, frozen=True)
class WrapSerializer:
    """ラップシリアライザは、標準のシリアライゼーションロジックを適用するハンドラ関数とともに生の入力を受け取り、シリアライゼーションの最終出力として返す前に、結果の値を変更できます。

    例えば、ラップシリアライザがタイムゾーンをUTC**に変換し、**が既存の`datetime`シリアライゼーションロジックを利用するシナリオを考えてみましょう。

    ```python
    from datetime import datetime, timezone
    from typing import Any, Dict

    from typing_extensions import Annotated

    from pydantic import BaseModel, WrapSerializer

    class EventDatetime(BaseModel):
        start: datetime
        end: datetime

    def convert_to_utc(value: Any, handler, info) -> Dict[str, datetime]:
        # Note that `helper` can actually help serialize the `value` for further custom serialization in case it's a subclass.
        partial_result = handler(value, info)
        if info.mode == 'json':
            return {
                k: datetime.fromisoformat(v).astimezone(timezone.utc)
                for k, v in partial_result.items()
            }
        return {k: v.astimezone(timezone.utc) for k, v in partial_result.items()}

    UTCEventDatetime = Annotated[EventDatetime, WrapSerializer(convert_to_utc)]

    class EventModel(BaseModel):
        event_datetime: UTCEventDatetime

    dt = EventDatetime(
        start='2024-01-01T07:00:00-08:00', end='2024-01-03T20:00:00+06:00'
    )
    event = EventModel(event_datetime=dt)
    print(event.model_dump())
    '''
    {
        'event_datetime': {
            'start': datetime.datetime(
                2024, 1, 1, 15, 0, tzinfo=datetime.timezone.utc
            ),
            'end': datetime.datetime(
                2024, 1, 3, 14, 0, tzinfo=datetime.timezone.utc
            ),
        }
    }
    '''

    print(event.model_dump_json())
    '''
    {"event_datetime":{"start":"2024-01-01T15:00:00Z","end":"2024-01-03T14:00:00Z"}}
    '''
    ```

    Attributes:
        func: ラップされるシリアライザ関数。
        return_type: 関数の戻り型。省略した場合は、型注釈から推測されます。
        when_used: このシリアライザをいつ使用すべきかを決定します。「always」、「unless-none」、「json」、「json-unless-none」の値を持つ文字列を受け入れます。デフォルトは「always」です。
    """

    func: core_schema.WrapSerializerFunction
    return_type: Any = PydanticUndefined
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        """このメソッドは、クラスのPydanticコアスキーマを取得するために使用されます。

        Args:
            source_type: ソース・タイプ。
            handler: コア・スキーマ・ハンドラー。

        Returns:
            クラスの生成されたコアスキーマ。
        """
        schema = handler(source_type)
        try:
            return_type = _decorators.get_function_return_type(
                self.func, self.return_type, handler._get_types_namespace()
            )
        except NameError as e:
            raise PydanticUndefinedAnnotation.from_name_error(e) from e
        return_schema = None if return_type is PydanticUndefined else handler.generate_schema(return_type)
        schema['serialization'] = core_schema.wrap_serializer_function_ser_schema(
            function=self.func,
            info_arg=_decorators.inspect_annotated_serializer(self.func, 'wrap'),
            return_schema=return_schema,
            when_used=self.when_used,
        )
        return schema


if TYPE_CHECKING:
    _PartialClsOrStaticMethod: TypeAlias = Union[classmethod[Any, Any, Any], staticmethod[Any, Any], partialmethod[Any]]
    _PlainSerializationFunction = Union[_core_schema.SerializerFunction, _PartialClsOrStaticMethod]
    _WrapSerializationFunction = Union[_core_schema.WrapSerializerFunction, _PartialClsOrStaticMethod]
    _PlainSerializeMethodType = TypeVar('_PlainSerializeMethodType', bound=_PlainSerializationFunction)
    _WrapSerializeMethodType = TypeVar('_WrapSerializeMethodType', bound=_WrapSerializationFunction)


@overload
def field_serializer(
    field: str,
    /,
    *fields: str,
    return_type: Any = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_PlainSerializeMethodType], _PlainSerializeMethodType]: ...


@overload
def field_serializer(
    field: str,
    /,
    *fields: str,
    mode: Literal['plain'],
    return_type: Any = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_PlainSerializeMethodType], _PlainSerializeMethodType]: ...


@overload
def field_serializer(
    field: str,
    /,
    *fields: str,
    mode: Literal['wrap'],
    return_type: Any = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_WrapSerializeMethodType], _WrapSerializeMethodType]: ...


def field_serializer(
    *fields: str,
    mode: Literal['plain', 'wrap'] = 'plain',
    return_type: Any = PydanticUndefined,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always',
    check_fields: bool | None = None,
) -> Callable[[Any], Any]:
    """カスタムフィールドのシリアル化を可能にするデコレータ。

    以下の例では、重複を避けるために`set`型のフィールドが使用されています。`field_serializer`はソートされたリストとしてデータをシリアライズするために使用されています。

    ```python
    from typing import Set

    from pydantic import BaseModel, field_serializer

    class StudentModel(BaseModel):
        name: str = 'Jane'
        courses: Set[str]

        @field_serializer('courses', when_used='json')
        def serialize_courses_in_order(self, courses: Set[str]):
            return sorted(courses)

    student = StudentModel(courses={'Math', 'Chemistry', 'English'})
    print(student.model_dump_json())
    #> {"name":"Jane","courses":["Chemistry","English","Math"]}
    ```

    詳細については、[Custom serializer](../concepts/serialization.md#custom-serializer)を参照してください。

    4つのシグニチャがサポートされています。

    - `(self, value: Any, info: FieldSerializationInfo)`
    - `(self, value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo)`
    - `(value: Any, info: SerializationInfo)`
    - `(value: Any, nxt: SerializerFunctionWrapHandler, info: SerializationInfo)`

    Args:
        fields: メソッドが呼び出されるフィールド。
        mode: シリアライゼーションモード。
            - `plain`は、デフォルトのシリアライゼーションロジックの代わりに関数が呼び出されることを意味します。
            - `wrap`は、オプションでデフォルトのシリアライゼーションロジックを呼び出すための引数とともに関数が呼び出されることを意味します。
        return_type: 関数のオプションの戻り型です。省略した場合は、型アノテーションから推測されます。
        when_used: シリアライズに使用するシリアライザを指定します。
        check_fields: フィールドがモデル上に実際に存在するかどうかをチェックするかどうか。

    Returns:
        デコレータ関数。
    """

    def dec(
        f: Callable[..., Any] | staticmethod[Any, Any] | classmethod[Any, Any, Any],
    ) -> _decorators.PydanticDescriptorProxy[Any]:
        dec_info = _decorators.FieldSerializerDecoratorInfo(
            fields=fields,
            mode=mode,
            return_type=return_type,
            when_used=when_used,
            check_fields=check_fields,
        )
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    return dec


FuncType = TypeVar('FuncType', bound=Callable[..., Any])


@overload
def model_serializer(__f: FuncType) -> FuncType: ...


@overload
def model_serializer(
    *,
    mode: Literal['plain', 'wrap'] = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always',
    return_type: Any = ...,
) -> Callable[[FuncType], FuncType]: ...


def model_serializer(
    f: Callable[..., Any] | None = None,
    /,
    *,
    mode: Literal['plain', 'wrap'] = 'plain',
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always',
    return_type: Any = PydanticUndefined,
) -> Callable[[Any], Any]:
    """カスタムモデルのシリアライゼーションを可能にするデコレータ。

    これは、モデルをカスタマイズされた方法でシリアライズする必要がある場合に便利で、特定のフィールド以外にも柔軟性を持たせることができます。

    たとえば、温度を摂氏などの同じ温度スケールに直列化することができます。

    ```python
    from typing import Literal

    from pydantic import BaseModel, model_serializer

    class TemperatureModel(BaseModel):
        unit: Literal['C', 'F']
        value: int

        @model_serializer()
        def serialize_model(self):
            if self.unit == 'F':
                return {'unit': 'C', 'value': int((self.value - 32) / 1.8)}
            return {'unit': self.unit, 'value': self.value}

    temperature = TemperatureModel(unit='F', value=212)
    print(temperature.model_dump())
    #> {'unit': 'C', 'value': 100}
    ```

    詳細については、[Custom serializer](../concepts/serialization.md#custom-serializer)を参照してください。

    Args:
        f: 装飾される関数。
        mode: シリアライゼーションモード。

            - `'plain'`は、デフォルトのシリアライゼーションロジックの代わりに関数が呼び出されることを意味します。
            - `'wrap'`は、デフォルトのシリアライゼーションロジックをオプションで呼び出すための引数を指定して関数が呼び出されることを意味します。

        when_used: このシリアライザをいつ使用すべきかを決定します。
        return_type: 関数の戻り型。省略した場合は、型注釈から推測されます。

    Returns:
        デコレータ関数。
    """

    def dec(f: Callable[..., Any]) -> _decorators.PydanticDescriptorProxy[Any]:
        dec_info = _decorators.ModelSerializerDecoratorInfo(mode=mode, return_type=return_type, when_used=when_used)
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    if f is None:
        return dec
    else:
        return dec(f)  # type: ignore


AnyType = TypeVar('AnyType')


if TYPE_CHECKING:
    SerializeAsAny = Annotated[AnyType, ...]  # SerializeAsAny[list[str]] will be treated by type checkers as list[str]
    """スキーマで定義されているものを無視し、代わりにオブジェクト自体にどのようにシリアライズすべきかを尋ねるようにシリアライズを強制します。
    特に、これは、モデルサブクラスがシリアライズされるとき、サブクラスに存在するが元のスキーマには存在しないフィールドが含まれることを意味します。
    """
else:

    @dataclasses.dataclass(**_internal_dataclass.slots_true)
    class SerializeAsAny:  # noqa: D101
        def __class_getitem__(cls, item: Any) -> Any:
            return Annotated[item, SerializeAsAny()]

        def __get_pydantic_core_schema__(
            self, source_type: Any, handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            schema = handler(source_type)
            schema_to_update = schema
            while schema_to_update['type'] == 'definitions':
                schema_to_update = schema_to_update.copy()
                schema_to_update = schema_to_update['schema']
            schema_to_update['serialization'] = core_schema.wrap_serializer_function_ser_schema(
                lambda x, h: h(x), schema=core_schema.any_schema()
            )
            return schema

        __hash__ = object.__hash__
