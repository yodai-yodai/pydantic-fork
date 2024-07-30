{% include-markdown "../warning.md" %}

<!-- Beyond accessing model attributes directly via their field names (e.g. `model.foobar`), models can be converted, dumped, serialized, and exported in a number of ways. -->
フィールド名(例えば`model.foobar`)から直接モデル属性にアクセスする以外にも、モデルはさまざまな方法で変換、ダンプ、シリアライズ、エクスポートすることができます。

!!! tip "Serialize versus dump"

    <!-- Pydantic uses the terms "serialize" and "dump" interchangeably. Both refer to the process of converting a model to a dictionary or JSON-encoded string. -->
    Pydanticでは、「serialize」と「dump」という用語を同じ意味で使用しています。どちらも、モデルを辞書またはJSONでエンコードされた文字列に変換するプロセスを指します。

    <!-- Outside of Pydantic, the word "serialize" usually refers to converting in-memory data into a string or bytes. -->
    Pydantic以外では、「シリアライズ」という言葉は通常、メモリ内のデータを文字列やバイトに変換することを意味します。
    However, in the context of Pydantic, there is a very close relationship between converting an object from a more structured form &mdash; such as a Pydantic model, a dataclass, etc. &mdash; into a less structured form comprised of Python built-ins such as dict.
    しかし、Pydanticのコンテキストでは、オブジェクトをPydanticモデルやデータクラスなどのより構造化された形式から、dictなどのPython組み込みで構成されたより構造化されていない形式に変換することには、非常に密接な関係があります。

    <!-- While we could (and on occasion, do) distinguish between these scenarios by using the word "dump" when converting to primitives and "serialize" when converting to string, for practical purposes, we frequently use the word "serialize" to refer to both of these situations, even though it does not always imply conversion to a string or bytes. -->
    プリミティブへの変換時には「dump」、文字列への変換時には「serialize」という単語を使用することで、これらのシナリオを区別することができます(場合によっては区別します)が、実際には、必ずしも文字列やバイトへの変換を意味するわけではありませんが、「serialize」という単語を両方の状況を指すためによく使用します。



## `model.model_dump(...)` <a name="model_dump"></a>

??? api "API Documentation"
    [`pydantic.main.BaseModel.model_dump`][pydantic.main.BaseModel.model_dump]<br>

<!-- This is the primary way of converting a model to a dictionary. Sub-models will be recursively converted to dictionaries. -->
これは、モデルを辞書に変換する主要な方法です。サブモデルは再帰的に辞書に変換されます。

!!! note
    <!-- The one exception to sub-models being converted to dictionaries is that [`RootModel`](models.md#rootmodel-and-custom-root-types) and its subclasses will have the `root` field value dumped directly, without a wrapping dictionary. This is also done recursively. -->
    辞書に変換されるサブモデルの1つの例外は、[`RootModel`](models.md#RootModel-and-custom-root-types)とそのサブクラスが、ラッピング辞書なしで直接ダンプされる`root`フィールド値を持つことです。これも再帰的に行われます。

!!! note
    <!-- You can use [computed fields](../api/fields.md#pydantic.fields.computed_field) to include `property` and `cached_property` data in the `model.model_dump(...)` output. -->
    [computed fields](../api/fields.md#pydantic.fields.computed_field)を使用して、`property`および`cached_property`データを`model.model_dump(...)`出力に含めることができます。

<!-- Example: -->
次に例を示します。

```py
from typing import Any, List, Optional

from pydantic import BaseModel, Field, Json


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: Optional[float] = 1.1
    foo: str = Field(serialization_alias='foo_alias')
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

# returns a dictionary:
print(m.model_dump())
#> {'banana': 3.14, 'foo': 'hello', 'bar': {'whatever': 123}}
print(m.model_dump(include={'foo', 'bar'}))
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(m.model_dump(exclude={'foo', 'bar'}))
#> {'banana': 3.14}
print(m.model_dump(by_alias=True))
#> {'banana': 3.14, 'foo_alias': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(foo='hello', bar={'whatever': 123}).model_dump(
        exclude_unset=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(banana=1.1, foo='hello', bar={'whatever': 123}).model_dump(
        exclude_defaults=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(foo='hello', bar={'whatever': 123}).model_dump(
        exclude_defaults=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(banana=None, foo='hello', bar={'whatever': 123}).model_dump(
        exclude_none=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}


class Model(BaseModel):
    x: List[Json[Any]]


print(Model(x=['{"a": 1}', '[1, 2]']).model_dump())
#> {'x': [{'a': 1}, [1, 2]]}
print(Model(x=['{"a": 1}', '[1, 2]']).model_dump(round_trip=True))
#> {'x': ['{"a":1}', '[1,2]']}
```

## `model.model_dump_json(...)` <a name="model_dump_json"></a>

??? api "API Documentation"
    [`pydantic.main.BaseModel.model_dump_json`][pydantic.main.BaseModel.model_dump_json]<br>

<!-- The `.model_dump_json()` method serializes a model directly to a JSON-encoded string that is equivalent to the result produced by [`.model_dump()`](#modelmodel_dump). -->
`.model_dump_json()`メソッドは、[`.model_dump()`](#modelmodel_dump)で生成された結果と等価なJSONエンコードされた文字列にモデルを直接シリアライズします。

<!-- See [arguments][pydantic.main.BaseModel.model_dump_json] for more information. -->
詳細については、[arguments][pydantic.main.BaseModel.model_dump_json]を参照してください。

!!! note
    <!-- Pydantic can serialize many commonly used types to JSON that would otherwise be incompatible with a simple `json.dumps(foobar)` (e.g. `datetime`, `date` or `UUID`) . -->
    Pydanticは、一般的に使用されている多くの型を、単純な`json.dumps(foobar)`(例えば`datetime`、`date`、`UUID`)と互換性のないJSONにシリアライズすることができます。

```py
from datetime import datetime

from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    foo: datetime
    bar: BarModel


m = FooBarModel(foo=datetime(2032, 6, 1, 12, 13, 14), bar={'whatever': 123})
print(m.model_dump_json())
#> {"foo":"2032-06-01T12:13:14","bar":{"whatever":123}}
print(m.model_dump_json(indent=2))
"""
{
  "foo": "2032-06-01T12:13:14",
  "bar": {
    "whatever": 123
  }
}
"""
```

## `dict(model)` and iteration

<!-- Pydantic models can also be converted to dictionaries using `dict(model)`, and you can also iterate over a model's fields using `for field_name, field_value in model:`. With this approach the raw field values are returned, so sub-models will not be converted to dictionaries. -->
Pydanticモデルは`dict(model)`を使って辞書に変換することもできますし、`for field_name, field_value in model:`を使ってモデルのフィールドを繰り返し処理することもできます。この方法では生のフィールド値が返されるので、サブモデルは辞書に変換されません。

<!-- Example: -->
次に例を示します。

```py
from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

print(dict(m))
#> {'banana': 3.14, 'foo': 'hello', 'bar': BarModel(whatever=123)}
for name, value in m:
    print(f'{name}: {value}')
    #> banana: 3.14
    #> foo: hello
    #> bar: whatever=123
```

<!-- Note also that [`RootModel`](models.md#rootmodel-and-custom-root-types) _does_ get converted to a dictionary with the key `'root'`. -->
[`RootModel`](models.md#RootModel-and-custom-root-types)_does_が`'root'`キーを持つ辞書に変換されることにも注意してください。

## Custom serializers

<!-- Pydantic provides several [functional serializers][pydantic.functional_serializers] to customise how a model is serialized to a dictionary or JSON. -->
Pydanticには、モデルを辞書やJSONにシリアライズする方法をカスタマイズするための[functional serializer][pydantic.functional_serializers]がいくつか用意されています。

- [`@field_serializer`][pydantic.functional_serializers.field_serializer]
- [`@model_serializer`][pydantic.functional_serializers.model_serializer]
- [`PlainSerializer`][pydantic.functional_serializers.PlainSerializer]
- [`WrapSerializer`][pydantic.functional_serializers.WrapSerializer]

<!-- Serialization can be customised on a field using the [`@field_serializer`][pydantic.functional_serializers.field_serializer] decorator, and on a model using the [`@model_serializer`][pydantic.functional_serializers.model_serializer] decorator. -->
シリアライゼーションは、[`@field_serializer`][pydantic.functional_serializers.field_serializer]デコレータを使用してフィールド上で、また[`@model_serializer`][pydantic.functional_serializers.model_serializer]デコレータを使用してモデル上でカスタマイズできます。

```py
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, field_serializer, model_serializer


class WithCustomEncoders(BaseModel):
    model_config = ConfigDict(ser_json_timedelta='iso8601')

    dt: datetime
    diff: timedelta

    @field_serializer('dt')
    def serialize_dt(self, dt: datetime, _info):
        return dt.timestamp()


m = WithCustomEncoders(
    dt=datetime(2032, 6, 1, tzinfo=timezone.utc), diff=timedelta(hours=100)
)
print(m.model_dump_json())
#> {"dt":1969660800.0,"diff":"P4DT4H"}


class Model(BaseModel):
    x: str

    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {'x': f'serialized {self.x}'}


print(Model(x='test value').model_dump_json())
#> {"x":"serialized test value"}
```

!!! note
    <!-- A single serializer can also be called on all fields by passing the special value '*' to the [`@field_serializer`][pydantic.functional_serializers.field_serializer] decorator. -->
    [`@field_serializer`][pydantic.functional_serializers.field_serializer]デコレータに特別な値'*'を渡すことで、すべてのフィールドで単一のシリアライザを呼び出すこともできます。

<!-- In addition, [`PlainSerializer`][pydantic.functional_serializers.PlainSerializer] and [`WrapSerializer`][pydantic.functional_serializers.WrapSerializer] enable you to use a function to modify the output of serialization. -->
さらに、[`PlainSerializer`][pydantic.functional_serializers.PlainSerializer]と[`WrapSerializer`][pydantic.functional_serializers.WrapSerializer]では、シリアライゼーションの出力を変更する関数を使うことができます。

<!-- Both serializers accept optional arguments including: -->
どちらのシリアライザも、以下のようなオプションの引数を受け付けます。

<!-- - `return_type` specifies the return type for the function. If omitted it will be inferred from the type annotation. -->
- `return_type`は、関数の戻り値の型を指定します。省略すると、型の注釈から推測されます。
<!-- - `when_used` specifies when this serializer should be used. Accepts a string with values 'always', 'unless-none', 'json', and 'json-unless-none'. Defaults to 'always'. -->
- `when_used`は、このシリアライザをいつ使用すべきかを指定します。'always'、'unless-none'、'json'、および'json-unless-none'の値を持つ文字列を受け入れます。デフォルトは'always'です。

<!-- `PlainSerializer` uses a simple function to modify the output of serialization. -->
`PlainSerializer`は、単純な関数を使用してシリアライゼーションの出力を変更します。

```py
from typing_extensions import Annotated

from pydantic import BaseModel
from pydantic.functional_serializers import PlainSerializer

FancyInt = Annotated[
    int, PlainSerializer(lambda x: f'{x:,}', return_type=str, when_used='json')
]


class MyModel(BaseModel):
    x: FancyInt


print(MyModel(x=1234).model_dump())
#> {'x': 1234}

print(MyModel(x=1234).model_dump(mode='json'))
#> {'x': '1,234'}
```

<!-- `WrapSerializer` receives the raw inputs along with a handler function that applies the standard serialization logic, and can modify the resulting value before returning it as the final output of serialization. -->
`WrapSerializer`は、標準のシリアライゼーションロジックを適用するハンドラ関数とともに生の入力を受け取り、シリアライゼーションの最終出力として返す前に結果の値を変更できます。

```py
from typing import Any

from typing_extensions import Annotated

from pydantic import BaseModel, SerializerFunctionWrapHandler
from pydantic.functional_serializers import WrapSerializer


def ser_wrap(v: Any, nxt: SerializerFunctionWrapHandler) -> str:
    return f'{nxt(v + 1):,}'


FancyInt = Annotated[int, WrapSerializer(ser_wrap, when_used='json')]


class MyModel(BaseModel):
    x: FancyInt


print(MyModel(x=1234).model_dump())
#> {'x': 1234}

print(MyModel(x=1234).model_dump(mode='json'))
#> {'x': '1,235'}
```

### Overriding the return type when dumping a model

<!-- While the return value of `.model_dump()` can usually be described as `dict[str, Any]`, through the use of `@model_serializer` you can actually cause it to return a value that doesn't match this signature: -->
`.model_dump()`の戻り値は通常`dict[str, Any]`と記述できますが、実際には`@model_serializer`を使用することで、このシグネチャと一致しない値を返すようにすることができます。

```py
from pydantic import BaseModel, model_serializer


class Model(BaseModel):
    x: str

    @model_serializer
    def ser_model(self) -> str:
        return self.x


print(Model(x='not a dict').model_dump())
#> not a dict
```

<!-- If you want to do this and still get proper type-checking for this method, you can override `.model_dump()` in an `if TYPE_CHECKING:` block: -->
これを行いながら、このメソッドに対して適切な型チェックを行いたい場合は、`if TYPE_CHECKING:`ブロック内の`.model_dump()`をオーバーライドすることができます。

```py
from typing import TYPE_CHECKING, Any

from typing_extensions import Literal

from pydantic import BaseModel, model_serializer


class Model(BaseModel):
    x: str

    @model_serializer
    def ser_model(self) -> str:
        return self.x

    if TYPE_CHECKING:
        # Ensure type checkers see the correct return type
        def model_dump(
            self,
            *,
            mode: Literal['json', 'python'] | str = 'python',
            include: Any = None,
            exclude: Any = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            round_trip: bool = False,
            warnings: bool = True,
        ) -> str: ...
```

<!-- This trick is actually used in [`RootModel`](models.md#rootmodel-and-custom-root-types) for precisely this purpose. -->
このトリックは、実際には[`RootModel`](models.md#RootModel-and-custom-root-types)でまさにこの目的のために使われています。

## Serializing subclasses

### Subclasses of standard types

<!-- Subclasses of standard types are automatically dumped like their super-classes: -->
標準タイプのサブクラスは、スーパークラスと同様に自動的にダンプされます。

```py
from datetime import date, timedelta
from typing import Any, Type

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler


class DayThisYear(date):
    """
    Contrived example of a special type of date that
    takes an int and interprets it as a day in the current year
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.int_schema(),
            serialization=core_schema.format_ser_schema('%Y-%m-%d'),
        )

    @classmethod
    def validate(cls, v: int):
        return date(2023, 1, 1) + timedelta(days=v)


class FooModel(BaseModel):
    date: DayThisYear


m = FooModel(date=300)
print(m.model_dump_json())
#> {"date":"2023-10-28"}
```

### Subclass instances for fields of `BaseModel`, dataclasses, `TypedDict`

<!-- When using fields whose annotations are themselves struct-like types (e.g., `BaseModel` subclasses, dataclasses, etc.), the default behavior is to serialize the attribute value as though it was an instance of the annotated type, even if it is a subclass. More specifically, only the fields from the _annotated_ type will be included in the dumped object: -->
構造体に似た型(例えば`BaseModel`のサブクラスやデータクラスなど)のアノテーションを持つフィールドを使用する場合、デフォルトの動作では、サブクラスであっても、属性値をアノテーション付き型のインスタンスであるかのようにシリアライズします。具体的には、_annotated_typeのフィールドのみがダンプされたオブジェクトに含まれます。

```py
from pydantic import BaseModel


class User(BaseModel):
    name: str


class UserLogin(User):
    password: str


class OuterModel(BaseModel):
    user: User


user = UserLogin(name='pydantic', password='hunter2')

m = OuterModel(user=user)
print(m)
#> user=UserLogin(name='pydantic', password='hunter2')
print(m.model_dump())  # note: the password field is not included
#> {'user': {'name': 'pydantic'}}
```
!!! warning "Migration Warning"
    <!-- This behavior is different from how things worked in Pydantic V1, where we would always include all (subclass) fields when recursively dumping models to dicts. -->
    この動作は、モデルをディクテーションに再帰的にダンプするときに常にすべての(サブクラス)フィールドを含めるPydantic V1での動作とは異なります。
    <!-- The motivation behind this change in behavior is that it helps ensure that you know precisely which fields could be included when serializing, even if subclasses get passed when instantiating the object. -->
    この動作変更の背後にあるモチベーションは、オブジェクトのインスタンス化時にサブクラスが渡された場合でも、シリアライズ時にどのフィールドが含まれるかを正確に把握できるようにするためです。
    <!-- In particular, this can help prevent surprises when adding sensitive information like secrets as fields of subclasses. -->
    特に、これは、サブクラスのフィールドとして秘密などの機密情報を追加するときに、不測の事態を防ぐのに役立ちます。

### Serializing with duck-typing 🦆

!!! question "What is serialization with duck typing?"

    <!-- Duck-typing serialization is the behavior of serializing an object based on the fields present in the object itself, rather than the fields present in the schema of the object. -->
    ダック型シリアライゼーションとは、オブジェクトのスキーマに存在するフィールドではなく、オブジェクト自体に存在するフィールドに基づいてオブジェクトをシリアライズする動作のことです。
    <!-- This means that when an object is serialized, fields present in a subclass, but not in the original schema, will be included in the serialized output. -->
    つまり、オブジェクトがシリアライズされると、サブクラスに存在するが元のスキーマには存在しないフィールドが、シリアライズされた出力に含まれます。

    This behavior was the default in Pydantic V1, but was changed in V2 to help ensure that you know precisely which fields would be included when serializing, even if subclasses get passed when instantiating the object.
    この動作はPydantic V1ではデフォルトでしたが、V2では、オブジェクトのインスタンス化時にサブクラスが渡された場合でも、シリアライズ時にどのフィールドが含まれるかを正確に把握できるように変更されました。
    <!-- This helps prevent security risks when serializing subclasses with sensitive information, for example. -->
    これにより、たとえば機密情報を含むサブクラスをシリアライズする際のセキュリティリスクを防ぐことができます。

<!-- If you want v1-style duck-typing serialization behavior, you can use a runtime setting, or annotate individual types. -->
v1スタイルのduck-typingシリアライゼーション動作が必要な場合は、ランタイム設定を使用するか、個々の型にアノテーションを付けることができます。

<!--
* Field / type level: use the `SerializeAsAny` annotation
* Runtime level: use the `serialize_as_any` flag when calling `model_dump()` or `model_dump_json()`
 -->
* フィールド/型レベル:`SerializeAsAny`アノテーションを使用します。
* 実行時レベル:`model_dump()`または`model_dump_json()`を呼び出すときに`serialize_as_any`フラグを使用してください。

<!-- We discuss these options below in more detail: -->
これらのオプションについては、以下で詳しく説明します。

#### `SerializeAsAny` annotation:

<!-- If you want duck-typing serialization behavior, this can be done using the `SerializeAsAny` annotation on a type: -->
型指定のシリアライズ動作を省略したい場合は、型に対して`SerializeAsAny`アノテーションを使用します。

```py
from pydantic import BaseModel, SerializeAsAny


class User(BaseModel):
    name: str


class UserLogin(User):
    password: str


class OuterModel(BaseModel):
    as_any: SerializeAsAny[User]
    as_user: User


user = UserLogin(name='pydantic', password='password')

print(OuterModel(as_any=user, as_user=user).model_dump())
"""
{
    'as_any': {'name': 'pydantic', 'password': 'password'},
    'as_user': {'name': 'pydantic'},
}
"""
```

<!-- When a field is annotated as `SerializeAsAny[<SomeType>]`, the validation behavior will be the same as if it was annotated as `<SomeType>`, and type-checkers like mypy will treat the attribute as having the appropriate type as well. -->
フィールドに`SerializeAsAny[<SomeType>]`という注釈が付けられた場合、検証の動作は`<SomeType>`という注釈が付けられた場合と同じになり、mypyのような型チェッカーも属性を適切な型として扱います。
<!-- But when serializing, the field will be serialized as though the type hint for the field was `Any`, which is where the name comes from. -->
しかし、シリアライズすると、フィールドの型ヒントが「Any」であるかのようにフィールドがシリアライズされます。これが名前の由来です。

#### `serialize_as_any` runtime setting

<!-- The `serialize_as_any` runtime setting can be used to serialize model data with or without duck typed serialization behavior. -->
`serialize_as_any`ランタイム設定は、duck型のシリアライゼーション動作の有無にかかわらず、モデルデータをシリアライズするために使用できます。
<!-- `serialize_as_any` can be passed as a keyword argument to the `model_dump()` and `model_dump_json` methods of `BaseModel`s and `RootModel`s. It can also be passed as a keyword argument to the `dump_python()` and `dump_json()` methods of `TypeAdapter`s. -->
`serialize_as_any`は、`BaseModel`および`RootModel`の`model_dump()`および`model_dump_json`メソッドにキーワード引数として渡すことができます。また、`TypeAdapter`の`dump_python()`および`dump_json()`メソッドにキーワード引数として渡すこともできます。

<!-- If `serialize_as_any` is set to `True`, the model will be serialized using duck typed serialization behavior, which means that the model will ignore the schema and instead ask the object itself how it should be serialized. -->
`serialize_as_any`が`True`に設定されている場合、モデルはduck型の直列化動作を使用して直列化されます。つまり、モデルはスキーマを無視し、代わりにオブジェクト自体にどのように直列化されるべきかを尋ねます。
<!-- In particular, this means that when model subclasses are serialized, fields present in the subclass but not in the original schema will be included. -->
特に、これは、モデルサブクラスがシリアライズされるとき、サブクラスに存在するが元のスキーマには存在しないフィールドが含まれることを意味します。

<!-- If `serialize_as_any` is set to `False` (which is the default), the model will be serialized using the schema, which means that fields present in a subclass but not in the original schema will be ignored. -->
`serialize_as_any`が`False`(デフォルト)に設定されている場合、モデルはスキーマを使用してシリアライズされます。つまり、サブクラスに存在するが元のスキーマには存在しないフィールドは無視されます。

!!! question "Why is this flag useful?"
    <!-- Sometimes, you want to make sure that no matter what fields might have been added in subclasses, the serialized object will only have the fields listed in the original type definition. -->
    場合によっては、サブクラスに追加されたフィールドが何であっても、直列化されたオブジェクトには元の型定義にリストされたフィールドしかないことを確認したいことがあります。
    <!-- This can be useful if you add something like a `password: str` field in a subclass that you don't want to accidentally include in the serialized output. -->
    これは、シリアル化された出力に誤って含めたくない`password:str`フィールドのようなものをサブクラスに追加する場合に便利です。

<!-- For example: -->
次に例を示します。

```py
from pydantic import BaseModel


class User(BaseModel):
    name: str


class UserLogin(User):
    password: str


class OuterModel(BaseModel):
    user1: User
    user2: User


user = UserLogin(name='pydantic', password='password')

outer_model = OuterModel(user1=user, user2=user)
print(outer_model.model_dump(serialize_as_any=True))  # (1)!
"""
{
    'user1': {'name': 'pydantic', 'password': 'password'},
    'user2': {'name': 'pydantic', 'password': 'password'},
}
"""

print(outer_model.model_dump(serialize_as_any=False))  # (2)!
#> {'user1': {'name': 'pydantic'}, 'user2': {'name': 'pydantic'}}
```

<!--
1. With `serialize_as_any` set to `True`, the result matches that of V1.
2. With `serialize_as_any` set to `False` (the V2 default), fields present on the subclass, but not the base class, are not included in serialization.
-->
1. `serialize_as_any`が`True`に設定されている場合、結果はV1の結果と一致します。
2. `serialize_as_any`を`False`(V2のデフォルト)に設定すると、サブクラスに存在するが基本クラスには存在しないフィールドはシリアライゼーションに含まれません。

<!-- This setting even takes effect with nested and recursive patterns as well. For example: -->
この設定は、ネストされた再帰的なパターンに対しても有効です。次に例を示します。

```py
from typing import List

from pydantic import BaseModel


class User(BaseModel):
    name: str
    friends: List['User']


class UserLogin(User):
    password: str


class OuterModel(BaseModel):
    user: User


user = UserLogin(
    name='samuel',
    password='pydantic-pw',
    friends=[UserLogin(name='sebastian', password='fastapi-pw', friends=[])],
)

print(OuterModel(user=user).model_dump(serialize_as_any=True))  # (1)!
"""
{
    'user': {
        'name': 'samuel',
        'friends': [
            {'name': 'sebastian', 'friends': [], 'password': 'fastapi-pw'}
        ],
        'password': 'pydantic-pw',
    }
}
"""

print(OuterModel(user=user).model_dump(serialize_as_any=False))  # (2)!
"""
{'user': {'name': 'samuel', 'friends': [{'name': 'sebastian', 'friends': []}]}}
"""
```

<!--
1. Even nested `User` model instances are dumped with fields unique to `User` subclasses.
2. Even nested `User` model instances are dumped without fields unique to `User` subclasses.
 -->
1. ネストされた`User`モデルインスタンスであっても、`User`サブクラスに固有のフィールドでダンプされます。
2. ネストされた`User`モデルインスタンスであっても、`User`サブクラスに固有のフィールドなしでダンプされます。

!!! note
    <!-- The behavior of the `serialize_as_any` runtime flag is almost the same as the behavior of the `SerializeAsAny` annotation.
    There are a few nuanced differences that we're working to resolve, but for the most part, you can expect the same behavior from both.
    See more about the differences in this [active issue](https://github.com/pydantic/pydantic/issues/9049) -->
    `serialize_as_any`実行時フラグの動作は、`SerializeAsAny`アノテーションの動作とほとんど同じです。
    私たちが解決しようとしている微妙な違いがいくつかありますが、ほとんどの場合、両方から同じ動作が期待できます。
    このの違いについては[active issue](https://github.com/pydantic/pydantic/issues/9049)を参照してください。

#### Overriding the `serialize_as_any` default (False)

<!-- You can override the default setting for `serialize_as_any` by configuring a subclass of `BaseModel` that overrides the default for the `serialize_as_any` argument to `model_dump()` and `model_dump_json()`, and then use that as the base class (instead of `pydantic.BaseModel`) for any model you want to have this default behavior. -->
`serialize_as_any`のデフォルト設定を上書きするには、`model_dump()`と`model_dump_json()`の`serialize_as_any`引数のデフォルトを上書きする`BaseModel`のサブクラスを設定し、このデフォルトの動作をさせたいモデルの基本クラスとして(`pydantic.BaseModel`の代わりに)それを使用します。

<!-- For example, you could do the following if you want to use duck-typing serialization by default: -->
たとえば、デフォルトでduck-typingシリアライゼーションを使用する場合は、次のようにします。

```py
from typing import Any, Dict

from pydantic import BaseModel, SecretStr


class MyBaseModel(BaseModel):
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        return super().model_dump(serialize_as_any=True, **kwargs)

    def model_dump_json(self, **kwargs) -> str:
        return super().model_dump_json(serialize_as_any=True, **kwargs)


class User(MyBaseModel):
    name: str


class UserInfo(User):
    password: SecretStr


class OuterModel(MyBaseModel):
    user: User


u = OuterModel(user=UserInfo(name='John', password='secret_pw'))
print(u.model_dump_json())  # (1)!
#> {"user":{"name":"John","password":"**********"}}
```

<!-- 1. By default, `model_dump_json` will use duck-typing serialization behavior, which means that the `password` field is included in the output. -->
1. デフォルトでは、`model_dump_json`はduck-typingシリアライゼーション動作を使用します。つまり、`password`フィールドが出力に含まれます。


## `pickle.dumps(model)`

<!-- Pydantic models support efficient pickling and unpickling. -->
Pydanticモデルは、効率的なピクルとアンピクルをサポートします。

<!-- TODO need to get pickling doctest to work -->
```py test="skip"
import pickle

from pydantic import BaseModel


class FooBarModel(BaseModel):
    a: str
    b: int


m = FooBarModel(a='hello', b=123)
print(m)
#> a='hello' b=123
data = pickle.dumps(m)
print(data[:20])
#> b'\x80\x04\x95\x95\x00\x00\x00\x00\x00\x00\x00\x8c\x08__main_'
m2 = pickle.loads(data)
print(m2)
#> a='hello' b=123
```

## Advanced include and exclude

<!-- The `model_dump` and `model_dump_json` methods support `include` and `exclude` arguments which can either be sets or dictionaries. This allows nested selection of which fields to export: -->
`model_dump`および`model_dump_json`メソッドは、セットまたはディクショナリのいずれかである`include`および`exclude`引数をサポートします。これにより、エクスポートするフィールドをネストして選択できます。

```py
from pydantic import BaseModel, SecretStr


class User(BaseModel):
    id: int
    username: str
    password: SecretStr


class Transaction(BaseModel):
    id: str
    user: User
    value: int


t = Transaction(
    id='1234567890',
    user=User(id=42, username='JohnDoe', password='hashedpassword'),
    value=9876543210,
)

# using a set:
print(t.model_dump(exclude={'user', 'value'}))
#> {'id': '1234567890'}

# using a dict:
print(t.model_dump(exclude={'user': {'username', 'password'}, 'value': True}))
#> {'id': '1234567890', 'user': {'id': 42}}

print(t.model_dump(include={'id': True, 'user': {'id'}}))
#> {'id': '1234567890', 'user': {'id': 42}}
```

<!-- The `True` indicates that we want to exclude or include an entire key, just as if we included it in a set.
This can be done at any depth level. -->
「True」は、キー全体をセットに含めたかのように、キー全体を除外または含めたいことを示します。
これは、任意の深さのレベルで実行できます。

<!-- Special care must be taken when including or excluding fields from a list or tuple of submodels or dictionaries.
In this scenario, `model_dump` and related methods expect integer keys for element-wise inclusion or exclusion.
To exclude a field from **every** member of a list or tuple, the dictionary key `'__all__'` can be used, as shown here: -->
サブモデルまたはディクショナリのリストまたはタプルからフィールドを含めたり除外したりする場合は、特別な注意が必要です。
このシナリオでは、`model_dump`および関連するメソッドは、要素ごとの包含または除外に整数キーを必要とします。
リストまたはタプルの**すべての**メンバーからフィールドを除外するには、次に示すように、辞書キー`__all__'`を使用できます。

```py
import datetime
from typing import List

from pydantic import BaseModel, SecretStr


class Country(BaseModel):
    name: str
    phone_code: int


class Address(BaseModel):
    post_code: int
    country: Country


class CardDetails(BaseModel):
    number: SecretStr
    expires: datetime.date


class Hobby(BaseModel):
    name: str
    info: str


class User(BaseModel):
    first_name: str
    second_name: str
    address: Address
    card_details: CardDetails
    hobbies: List[Hobby]


user = User(
    first_name='John',
    second_name='Doe',
    address=Address(
        post_code=123456, country=Country(name='USA', phone_code=1)
    ),
    card_details=CardDetails(
        number='4212934504460000', expires=datetime.date(2020, 5, 1)
    ),
    hobbies=[
        Hobby(name='Programming', info='Writing code and stuff'),
        Hobby(name='Gaming', info='Hell Yeah!!!'),
    ],
)

exclude_keys = {
    'second_name': True,
    'address': {'post_code': True, 'country': {'phone_code'}},
    'card_details': True,
    # You can exclude fields from specific members of a tuple/list by index:
    'hobbies': {-1: {'info'}},
}

include_keys = {
    'first_name': True,
    'address': {'country': {'name'}},
    'hobbies': {0: True, -1: {'name'}},
}

# would be the same as user.model_dump(exclude=exclude_keys) in this case:
print(user.model_dump(include=include_keys))
"""
{
    'first_name': 'John',
    'address': {'country': {'name': 'USA'}},
    'hobbies': [
        {'name': 'Programming', 'info': 'Writing code and stuff'},
        {'name': 'Gaming'},
    ],
}
"""

# To exclude a field from all members of a nested list or tuple, use "__all__":
print(user.model_dump(exclude={'hobbies': {'__all__': {'info'}}}))
"""
{
    'first_name': 'John',
    'second_name': 'Doe',
    'address': {
        'post_code': 123456,
        'country': {'name': 'USA', 'phone_code': 1},
    },
    'card_details': {
        'number': SecretStr('**********'),
        'expires': datetime.date(2020, 5, 1),
    },
    'hobbies': [{'name': 'Programming'}, {'name': 'Gaming'}],
}
"""
```

<!-- The same holds for the `model_dump_json` method. -->
同じことが`model_dump_json`メソッドにも当てはまります。

### Model- and field-level include and exclude

<!-- In addition to the explicit arguments `exclude` and `include` passed to `model_dump` and `model_dump_json` methods, we can also pass the `exclude: bool` arguments directly to the `Field` constructor: -->
`model_dump`および`model_dump_json`メソッドに渡される明示的な引数`exclude`および`include`に加えて、`exclude:bool`引数を`Field`コンストラクタに直接渡すこともできます。

Setting `exclude` on the field constructor (`Field(..., exclude=True)`) takes priority over the `exclude`/`include` on `model_dump` and `model_dump_json`:
フィールドコンストラクタ(`Field(... ,exclude=True)`)に`exclude`を設定すると、`model_dump`と`model_dump_json`の`exclude`/`include`よりも優先されます。

```py
from pydantic import BaseModel, Field, SecretStr


class User(BaseModel):
    id: int
    username: str
    password: SecretStr = Field(..., exclude=True)


class Transaction(BaseModel):
    id: str
    value: int = Field(exclude=True)


t = Transaction(
    id='1234567890',
    value=9876543210,
)

print(t.model_dump())
#> {'id': '1234567890'}
print(t.model_dump(include={'id': True, 'value': True}))  # (1)!
#> {'id': '1234567890'}
```

<!-- 1. `value` excluded from the output because it excluded in `Field`. -->
1. `value`は`Field`で除外されているため、出力から除外されます。

<!-- That being said, setting `exclude` on the field constructor (`Field(..., exclude=True)`) does not take priority over the `exclude_unset`, `exclude_none`, and `exclude_default` parameters on `model_dump` and `model_dump_json`: -->
とはいうものの、フィールドコンストラクタ(`Field(...,exclude=True)`)に`exclude`を設定しても、`model_dump`と`model_dump_json`の`exclude_unset`、`exclude_none`、`exclude_default`パラメータよりも優先されません。

```py
from typing import Optional

from pydantic import BaseModel, Field


class Person(BaseModel):
    name: str
    age: Optional[int] = Field(None, exclude=False)


person = Person(name='Jeremy')

print(person.model_dump())
#> {'name': 'Jeremy', 'age': None}
print(person.model_dump(exclude_none=True))  # (1)!
#> {'name': 'Jeremy'}
print(person.model_dump(exclude_unset=True))  # (2)!
#> {'name': 'Jeremy'}
print(person.model_dump(exclude_defaults=True))  # (3)!
#> {'name': 'Jeremy'}
```

<!--
1. `age` excluded from the output because `exclude_none` was set to `True`, and `age` is `None`.
2. `age` excluded from the output because `exclude_unset` was set to `True`, and `age` was not set in the Person constructor.
3. `age` excluded from the output because `exclude_defaults` was set to `True`, and `age` takes the default value of `None`.
-->
1. `exclude_none`が`True`に設定され、`age`が`None`であるため、`age`は出力から除外されます。
2. `exclude_unset`が`True`に設定され、`age`がPersonコンストラクタで設定されなかったため、`age`は出力から除外されました。
3. `exclude_defaults`が`True`に設定されているため、`age`は出力から除外され、`age`はデフォルト値の`None`を取ります。

## Serialization Context

<!-- You can pass a context object to the serialization methods which can be accessed from the `info` argument to decorated serializer functions. -->
デコレートされたシリアライザ関数への`info`引数からアクセスできるシリアライゼーションメソッドにコンテキストオブジェクトを渡すことができます。
<!-- This is useful when you need to dynamically update the serialization behavior during runtime. -->
これは、実行時にシリアル化の動作を動的に更新する必要がある場合に便利です。
For example, if you wanted a field to be dumped depending on a dynamically controllable set of allowed values, this could be done by passing the allowed values by context:
<!-- たとえば、動的に制御可能な許可された値のセットに応じてフィールドをダンプする場合は、コンテキスト別に許可された値を渡すことで実行できます。 -->

```python
from pydantic import BaseModel, SerializationInfo, field_serializer


class Model(BaseModel):
    text: str

    @field_serializer('text')
    def remove_stopwords(self, v: str, info: SerializationInfo):
        context = info.context
        if context:
            stopwords = context.get('stopwords', set())
            v = ' '.join(w for w in v.split() if w.lower() not in stopwords)
        return v


model = Model.model_construct(**{'text': 'This is an example document'})
print(model.model_dump())  # no context
#> {'text': 'This is an example document'}
print(model.model_dump(context={'stopwords': ['this', 'is', 'an']}))
#> {'text': 'example document'}
print(model.model_dump(context={'stopwords': ['document']}))
#> {'text': 'This is an example'}
```

<!-- Similarly, you can [use a context for validation](../concepts/validators.md#validation-context). -->
同様に、[use a context for validation]することもできます。(../concepts/validators.md#validation-context)

## `model_copy(...)` <a name="model_copy">

??? api "API Documentation"
    [`pydantic.main.BaseModel.model_copy`][pydantic.main.BaseModel.model_copy]<br>

<!-- `model_copy()` allows models to be duplicated (with optional updates), which is particularly useful when working with frozen models. -->
`model_copy()`を使用すると、モデルを複製することができます(オプションの更新を使用)。これは、フリーズされたモデルを操作する場合に特に便利です。

<!-- Example: -->
次に例を示します。

```py
from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

print(m.model_copy(update={'banana': 0}))
#> banana=0 foo='hello' bar=BarModel(whatever=123)
print(id(m.bar) == id(m.model_copy().bar))
#> True
# normal copy gives the same object reference for bar
print(id(m.bar) == id(m.model_copy(deep=True).bar))
#> False
# deep copy gives a new object reference for `bar`
```
