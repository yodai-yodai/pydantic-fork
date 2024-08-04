{% include-markdown "../warning.md" %}

??? api "API Documentation"
    [`pydantic.types.Strict`][pydantic.types.Strict]<br>

<!-- By default, Pydantic will attempt to coerce values to the desired type when possible.
For example, you can pass the string `"123"` as the input to an `int` field, and it will be converted to `123`.
This coercion behavior is useful in many scenarios — think: UUIDs, URL parameters, HTTP headers, environment variables, user input, etc. -->
デフォルトでは、Pydanticは可能であれば値を目的の型に強制しようとします。
例えば、文字列`"123"`を入力として`int`フィールドに渡すと、`123`に変換されます。
この強制動作は、UUID、URLパラメータ、HTTPヘッダー、環境変数、ユーザ入力など、さまざまなシナリオで役立ちます。

<!-- However, there are also situations where this is not desirable, and you want Pydantic to error instead of coercing data. -->
しかし、これが望ましくない状況もあり、Pydanticにデータを強制するのではなくエラーを発生させたい場合もあります。

<!-- To better support this use case, Pydantic provides a "strict mode" that can be enabled on a per-model, per-field, or even per-validation-call basis. When strict mode is enabled, Pydantic will be much less lenient when coercing data, and will instead error if the data is not of the correct type. -->
このユースケースをよりよくサポートするために、Pydanticは、モデルごと、フィールドごと、または検証呼び出しごとに有効にできる"strictモード"を提供している。strictモードが有効になると、Pydanticはデータを強制する際の甘さを大幅に減らし、データが正しいタイプでない場合はエラーを発生させる。

<!-- Here is a brief example showing the difference between validation behavior in strict and the default/"lax" mode: -->
次に、strictモードとdefault/"lax"モードの検証動作の違いを示す簡単な例を示します。

```py
from pydantic import BaseModel, ValidationError


class MyModel(BaseModel):
    x: int


print(MyModel.model_validate({'x': '123'}))  # lax mode
#> x=123

try:
    MyModel.model_validate({'x': '123'}, strict=True)  # strict mode
except ValidationError as exc:
    print(exc)
    """
    1 validation error for MyModel
    x
      Input should be a valid integer [type=int_type, input_value='123', input_type=str]
    """
```

<!-- There are various ways to get strict-mode validation while using Pydantic, which will be discussed in more detail below: -->
Pydanticを使用しながらstrictモードの検証を行うには、さまざまな方法があります。これについては、以下で詳しく説明します。

<!-- * [Passing `strict=True` to the validation methods](#strict-mode-in-method-calls), such as `BaseModel.model_validate`, `TypeAdapter.validate_python`, and similar for JSON
* [Using `Field(strict=True)`](#strict-mode-with-field) with fields of a `BaseModel`, `dataclass`, or `TypedDict`
* [Using `pydantic.types.Strict` as a type annotation](#strict-mode-with-annotated-strict) on a field
  * Pydantic provides some type aliases that are already annotated with `Strict`, such as `pydantic.types.StrictInt`
* [Using `ConfigDict(strict=True)`](#strict-mode-with-configdict) -->
* [Passing `strict=True` to the validation methods](#strict-mode-in-method-calls)、例えば`BaseModel.model_validate`、`TypeAdapter.validate_python`など、JSONの場合も同様です。
* `BaseModel`、`dataclass`、または`TypedDict`のフィールドと共に使用する[Using `Field(strict=True)`](#strict-mode-with-field)
* フィールドへの[Using `pydantic.types.Strict` as a type annotation](#strict-mode-with-annotated-strict)
  * Pydanticには、`pydantic.types.StrictInt`など、すでに`Strict`で注釈が付けられている型エイリアスがいくつか用意されています。
* [Using `ConfigDict(strict=True)`](#strict-mode-with-configdict)を使用する

## Type coercions in strict mode

<!-- For most types, when validating data from python in strict mode, only the instances of the exact types are accepted.
For example, when validating an `int` field, only instances of `int` are accepted; passing instances of `float` or `str` will result in raising a `ValidationError`. -->
ほとんどの型では、strictモードでpythonからのデータを検証する場合、正確な型のインスタンスのみが受け入れられます。
たとえば、`int`フィールドを検証する場合、`int`のインスタンスのみが受け入れられます。`float`または`str`のインスタンスを渡すと、`ValidationError`が発生します。

<!-- Note that we are looser when validating data from JSON in strict mode. For example, when validating a `UUID` field, instances of `str` will be accepted when validating from JSON, but not from python: -->
strictモードでJSONからのデータを検証する場合は、より緩いことに注意してください。例えば、`UUID`フィールドを検証する場合、`str`のインスタンスはJSONからの検証では受け入れられますが、pythonからの検証では受け入れられません。

```py
import json
from uuid import UUID

from pydantic import BaseModel, ValidationError


class MyModel(BaseModel):
    guid: UUID


data = {'guid': '12345678-1234-1234-1234-123456789012'}

print(MyModel.model_validate(data))  # OK: lax
#> guid=UUID('12345678-1234-1234-1234-123456789012')

print(
    MyModel.model_validate_json(json.dumps(data), strict=True)
)  # OK: strict, but from json
#> guid=UUID('12345678-1234-1234-1234-123456789012')

try:
    MyModel.model_validate(data, strict=True)  # Not OK: strict, from python
except ValidationError as exc:
    print(exc.errors(include_url=False))
    """
    [
        {
            'type': 'is_instance_of',
            'loc': ('guid',),
            'msg': 'Input should be an instance of UUID',
            'input': '12345678-1234-1234-1234-123456789012',
            'ctx': {'class': 'UUID'},
        }
    ]
    """
```

<!-- For more details about what types are allowed as inputs in strict mode, you can review the [Conversion Table](conversion_table.md). -->
strictモードで入力として許可されるタイプの詳細については、[Conversion Table](conversion_table.md)を参照してください。

## Strict mode in method calls

<!-- All the examples included so far get strict-mode validation through the use of `strict=True` as a keyword argument to the validation methods. While we have shown this for `BaseModel.model_validate`, this also works with arbitrary types through the use of `TypeAdapter`: -->
これまでに紹介したすべての例では、検証メソッドへのキーワード引数として`strict=True`を使用することで、strictモードの検証を行います。これは`BaseModel.model_validate`で示しましたが、`TypeAdapter`を使用することで任意の型でも動作します。

```python
from pydantic import TypeAdapter, ValidationError

print(TypeAdapter(bool).validate_python('yes'))  # OK: lax
#> True

try:
    TypeAdapter(bool).validate_python('yes', strict=True)  # Not OK: strict
except ValidationError as exc:
    print(exc)
    """
    1 validation error for bool
      Input should be a valid boolean [type=bool_type, input_value='yes', input_type=str]
    """
```

<!-- Note this also works even when using more "complex" types in `TypeAdapter`: -->
これは、`TypeAdapter`でより"複雑な"型を使用する場合でも機能することに注意してください。

```python
from dataclasses import dataclass

from pydantic import TypeAdapter, ValidationError


@dataclass
class MyDataclass:
    x: int


try:
    TypeAdapter(MyDataclass).validate_python({'x': '123'}, strict=True)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for MyDataclass
      Input should be an instance of MyDataclass [type=dataclass_exact_type, input_value={'x': '123'}, input_type=dict]
    """
```

<!-- This also works with the `TypeAdapter.validate_json` and `BaseModel.model_validate_json` methods: -->
これは`TypeAdapter.validate_json`と`BaseModel.model_validate_json`メソッドでも動作します。

```python
import json
from typing import List
from uuid import UUID

from pydantic import BaseModel, TypeAdapter, ValidationError

try:
    TypeAdapter(List[int]).validate_json('["1", 2, "3"]', strict=True)
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for list[int]
    0
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    2
      Input should be a valid integer [type=int_type, input_value='3', input_type=str]
    """


class Model(BaseModel):
    x: int
    y: UUID


data = {'x': '1', 'y': '12345678-1234-1234-1234-123456789012'}
try:
    Model.model_validate(data, strict=True)
except ValidationError as exc:
    # Neither x nor y are valid in strict mode from python:
    print(exc)
    """
    2 validation errors for Model
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    y
      Input should be an instance of UUID [type=is_instance_of, input_value='12345678-1234-1234-1234-123456789012', input_type=str]
    """

json_data = json.dumps(data)
try:
    Model.model_validate_json(json_data, strict=True)
except ValidationError as exc:
    # From JSON, x is still not valid in strict mode, but y is:
    print(exc)
    """
    1 validation error for Model
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```


## Strict mode with `Field`

<!-- For individual fields on a model, you can [set `strict=True` on the field](../api/fields.md#pydantic.fields.Field).
This will cause strict-mode validation to be used for that field, even when the validation methods are called without `strict=True`. -->
モデルの個々のフィールドに対しては、[フィールドに`strict=True`を設定する]ことができます(./api/fields.md#pydantic.fields.Field)。
これにより、検証メソッドが`strict=True`なしで呼び出された場合でも、そのフィールドに対してstrictモードの検証が使用されます。

<!-- Only the fields for which `strict=True` is set will be affected: -->
`strict=True`が設定されているフィールドのみが影響を受けます。

```python
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    name: str
    age: int
    n_pets: int


user = User(name='John', age='42', n_pets='1')
print(user)
#> name='John' age=42 n_pets=1


class AnotherUser(BaseModel):
    name: str
    age: int = Field(strict=True)
    n_pets: int


try:
    anotheruser = AnotherUser(name='John', age='42', n_pets='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for AnotherUser
    age
      Input should be a valid integer [type=int_type, input_value='42', input_type=str]
    """
```

<!-- Note that making fields strict will also affect the validation performed when instantiating the model class: -->
フィールドを厳密にすると、モデルクラスをインスタンス化するときに実行される検証にも影響することに注意してください。

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(strict=True)
    y: int = Field(strict=False)


try:
    Model(x='1', y='2')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```

### Using `Field` as an annotation

<!-- Note that `Field(strict=True)` (or with any other keyword arguments) can be used as an annotation if necessary, e.g., when working with `TypedDict`: -->
`Field(strict=True)`(または他のキーワード引数とともに)は、必要に応じて注釈として使用できます。たとえば、`TypedDict`を使用する場合は次のようになります。

```python
from typing_extensions import Annotated, TypedDict

from pydantic import Field, TypeAdapter, ValidationError


class MyDict(TypedDict):
    x: Annotated[int, Field(strict=True)]


try:
    TypeAdapter(MyDict).validate_python({'x': '1'})
except ValidationError as exc:
    print(exc)
    """
    1 validation error for typed-dict
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```

## Strict mode with `Annotated[..., Strict()]`

??? api "API Documentation"
    [`pydantic.types.Strict`][pydantic.types.Strict]<br>

<!-- Pydantic also provides the [`Strict`](../api/types.md#pydantic.types.Strict) class, which is intended for use as metadata with [`typing.Annotated`][] class; this annotation indicates that the annotated field should be validated in strict mode: -->
Pydanticは[`Strict`](../api/types.md#pydantic.types.Strict)クラスも提供しており、これは[`typing.Annotated`][]クラスでメタデータとして使用することを目的としています。この注釈は、注釈付きフィールドがstrictモードで検証される必要があることを示します。

```python
from typing_extensions import Annotated

from pydantic import BaseModel, Strict, ValidationError


class User(BaseModel):
    name: str
    age: int
    is_active: Annotated[bool, Strict()]


User(name='David', age=33, is_active=True)
try:
    User(name='David', age=33, is_active='True')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for User
    is_active
      Input should be a valid boolean [type=bool_type, input_value='True', input_type=str]
    """
```

<!-- This is, in fact, the method used to implement some of the strict-out-of-the-box types provided by Pydantic, such as [`StrictInt`](../api/types.md#pydantic.types.StrictInt). -->
これは実際、[`StrictInt`](../api/types.md#pydantic.types.StrictInt)のような、Pydanticが提供する厳密な初期状態の型を実装するために使用されるメソッドです。

## Strict mode with `ConfigDict`

### `BaseModel`

<!-- If you want to enable strict mode for all fields on a complex input type, you can use [`ConfigDict(strict=True)`](../api/config.md#pydantic.config.ConfigDict) in the `model_config`: -->
複雑な入力タイプのすべてのフィールドに対してstrictモードを有効にしたい場合は、`model_config`で[`ConfigDict(strict=True)`](../api/config.md#pydantic.config.ConfigDict)を使用します。

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class User(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    age: int
    is_active: bool


try:
    User(name='David', age='33', is_active='yes')
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for User
    age
      Input should be a valid integer [type=int_type, input_value='33', input_type=str]
    is_active
      Input should be a valid boolean [type=bool_type, input_value='yes', input_type=str]
    """
```

!!! note
    <!-- When using `strict=True` through a model's `model_config`, you can still override the strictness of individual fields by setting `strict=False` on individual fields: -->
    モデルの`model_config`で`strict=True`を使用している場合でも、個々のフィールドに`strict=False`を設定することで、個々のフィールドの厳密さを上書きできます。



    ```py
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(strict=True)

        name: str
        age: int = Field(strict=False)
    ```

<!-- Note that strict mode is not recursively applied to nested model fields: -->
strictモードは、ネストされたモデルフィールドに再帰的に適用されないことに注意してください。

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Inner(BaseModel):
    y: int


class Outer(BaseModel):
    model_config = ConfigDict(strict=True)

    x: int
    inner: Inner


print(Outer(x=1, inner=Inner(y='2')))
#> x=1 inner=Inner(y=2)

try:
    Outer(x='1', inner=Inner(y='2'))
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Outer
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```

<!-- (This is also the case for dataclasses and `TypedDict`.) -->
(これはデータクラスや`TypedDict`にも当てはまります)

<!-- If this is undesirable, you should make sure that strict mode is enabled for all the types involved.
For example, this can be done for model classes by using a shared base class with `model_config = ConfigDict(strict=True)`: -->
これが望ましくない場合は、関係するすべてのタイプに対してstrictモードが有効になっていることを確認してください。
たとえば、モデルクラスに対してこれを行うには、`model_config=ConfigDict(strict=True)`で共有基底クラスを使用します。

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class MyBaseModel(BaseModel):
    model_config = ConfigDict(strict=True)


class Inner(MyBaseModel):
    y: int


class Outer(MyBaseModel):
    x: int
    inner: Inner


try:
    Outer.model_validate({'x': 1, 'inner': {'y': '2'}})
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Outer
    inner.y
      Input should be a valid integer [type=int_type, input_value='2', input_type=str]
    """
```

### Dataclasses and `TypedDict`

<!-- Pydantic dataclasses behave similarly to the examples shown above with `BaseModel`, just that instead of `model_config` you should use the `config` keyword argument to the `@pydantic.dataclasses.dataclass` decorator. -->
Pydanticのデータクラスは、上記の`BaseModel`の例と同じように動作しますが、`model_config`の代わりに、`@pydantic.dataclasses.dataclass`デコレータの`config`キーワード引数を使用する必要があります。

<!-- When possible, you can achieve nested strict mode for vanilla dataclasses or `TypedDict` subclasses by annotating fields with the [`pydantic.types.Strict` annotation](#strict-mode-with-annotated-strict). -->
可能であれば、[`pydantic.types.Strict`annotation](#strict-mode-with-annotated-strict)でフィールドに注釈を付けることで、バニラデータクラスや`TypedDict`サブクラスに対してネストされたstrictモードを実現できます。

<!-- However, if this is _not_ possible (e.g., when working with third-party types), you can set the config that Pydantic should use for the type by setting the `__pydantic_config__` attribute on the type: -->
しかし、これが不可能な場合(例えば、サードパーティの型を扱う場合)は、その型に`__pydantic_config__`属性を設定することで、Pydanticがその型に使用する設定を行うことができます。

```python
from typing_extensions import TypedDict

from pydantic import ConfigDict, TypeAdapter, ValidationError


class Inner(TypedDict):
    y: int


Inner.__pydantic_config__ = ConfigDict(strict=True)


class Outer(TypedDict):
    x: int
    inner: Inner


adapter = TypeAdapter(Outer)
print(adapter.validate_python({'x': '1', 'inner': {'y': 2}}))
#> {'x': 1, 'inner': {'y': 2}}


try:
    adapter.validate_python({'x': '1', 'inner': {'y': '2'}})
except ValidationError as exc:
    print(exc)
    """
    1 validation error for typed-dict
    inner.y
      Input should be a valid integer [type=int_type, input_value='2', input_type=str]
    """
```

### `TypeAdapter`

<!-- You can also get strict mode through the use of the config keyword argument to the [`TypeAdapter`](../api/type_adapter.md) class: -->
[`TypeAdapter`](../api/type_adapter.md)クラスのconfigキーワード引数を使用してstrictモードを取得することもできます。

```python
from pydantic import ConfigDict, TypeAdapter, ValidationError

adapter = TypeAdapter(bool, config=ConfigDict(strict=True))

try:
    adapter.validate_python('yes')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for bool
      Input should be a valid boolean [type=bool_type, input_value='yes', input_type=str]
    """
```

### `@validate_call`

<!-- Strict mode is also usable with the [`@validate_call`](../api/validate_call.md#pydantic.validate_call_decorator.validate_call) decorator by passing the `config` keyword argument: -->
strictモードは、[`@validate_call`](../api/validate_call.md#pydantic.validate_call_decorator.validate_call)デコレータで`config`キーワード引数を渡すことによっても使用できます。

```python
from pydantic import ConfigDict, ValidationError, validate_call


@validate_call(config=ConfigDict(strict=True))
def foo(x: int) -> int:
    return x


try:
    foo('1')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for foo
    0
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```
