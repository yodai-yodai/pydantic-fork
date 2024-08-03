{% include-markdown "../warning.md" %}

<!-- You may have types that are not `BaseModel`s that you want to validate data against.
Or you may want to validate a `List[SomeModel]`, or dump it to JSON. -->
`BaseModel`ではない型に対してデータを検証したい場合があります。
あるいは`List[SomeModel]`を検証したり、JSONにダンプしたりすることもできます。

??? api "API Documentation"
    [`pydantic.type_adapter.TypeAdapter`][pydantic.type_adapter.TypeAdapter]<br>

<!-- For use cases like this, Pydantic provides [`TypeAdapter`][pydantic.type_adapter.TypeAdapter], which can be used for type validation, serialization, and JSON schema generation without needing to create a [`BaseModel`][pydantic.main.BaseModel]. -->
このようなユースケースのために、Pydanticは[`BaseModel`][pydantic.main.BaseModel]を作成することなく、型検証、シリアライゼーション、JSONスキーマ生成に使用できる[`TypeAdapter`][pydantic.type_adapter.TypeAdapter]を提供しています。

<!-- A [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] instance exposes some of the functionality from [`BaseModel`][pydantic.main.BaseModel] instance methods for types that do not have such methods (such as dataclasses, primitive types, and more): -->
[`TypeAdapter`][pydantic.type_adapter.TypeAdapter]インスタンスは、[`BaseModel`][pydantic.main.BaseModel]インスタンスメソッドの機能の一部を、そのようなメソッドを持たない型(データクラス、プリミティブ型など)に対して公開します。

```py
from typing import List

from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError


class User(TypedDict):
    name: str
    id: int


user_list_adapter = TypeAdapter(List[User])
user_list = user_list_adapter.validate_python([{'name': 'Fred', 'id': '3'}])
print(repr(user_list))
#> [{'name': 'Fred', 'id': 3}]

try:
    user_list_adapter.validate_python(
        [{'name': 'Fred', 'id': 'wrong', 'other': 'no'}]
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for list[typed-dict]
    0.id
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='wrong', input_type=str]
    """

print(repr(user_list_adapter.dump_json(user_list)))
#> b'[{"name":"Fred","id":3}]'
```

!!! info "`dump_json` returns `bytes`"
    <!-- `TypeAdapter`'s `dump_json` methods returns a `bytes` object, unlike the corresponding method for `BaseModel`, `model_dump_json`, which returns a `str`.
    The reason for this discrepancy is that in V1, model dumping returned a str type, so this behavior is retained in V2 for backwards compatibility.
    For the `BaseModel` case, `bytes` are coerced to `str` types, but `bytes` are often the desired end type.
    Hence, for the new `TypeAdapter` class in V2, the return type is simply `bytes`, which can easily be coerced to a `str` type if desired. -->
    `TypeAdapter`の`dump_json`メソッドは`bytes`オブジェクトを返しますが、これに対応する`BaseModel`の`model_dump_json`メソッドは`str`を返します。
    この不一致の理由は、V1ではモデルダンプがstr型を返したため、この動作は下位互換性のためにV2でも保持されているためです。
    `BaseModel`の場合、`bytes`は`str`型に強制的に変換されますが、多くの場合`bytes`が望ましい終了型です。
    したがって、V2の新しい`TypeAdapter`クラスでは、戻り値の型は単に`bytes`であり、必要に応じて`str`型に簡単に強制できます。

!!! note
    <!-- Despite some overlap in use cases with [`RootModel`][pydantic.root_model.RootModel], [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] should not be used as a type annotation for specifying fields of a `BaseModel`, etc. -->
    [`RootModel`][pydantic.root_model.RootModel]とユースケースが重複していますが、[`TypeAdapter`][pydantic.type_adapter.TypeAdapter]は`BaseModel`などのフィールドを指定するための型注釈として使用すべきではありません。

## Parsing data into a specified type

<!-- [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] can be used to apply the parsing logic to populate Pydantic models in a more ad-hoc way. This function behaves similarly to [`BaseModel.model_validate`][pydantic.main.BaseModel.model_validate], but works with arbitrary Pydantic-compatible types. -->
[`TypeAdapter`][pydantic.type_adapter.TypeAdapter]を使用すると、解析ロジックを適用して、よりアドホックな方法でPydanticモデルを作成できます。この関数は[`BaseModel.model_validate`][pydantic.main.BaseModel.model_validate]と同じように動作しますが、任意のPydantic互換型で動作します。

<!-- This is especially useful when you want to parse results into a type that is not a direct subclass of [`BaseModel`][pydantic.main.BaseModel]. For example: -->
これは、[`BaseModel`][pydantic.main.BaseModel]の直接のサブクラスではない型に結果を解析したい場合に特に便利です。例えば:

```py
from typing import List

from pydantic import BaseModel, TypeAdapter


class Item(BaseModel):
    id: int
    name: str


# `item_data` could come from an API call, eg., via something like:
# item_data = requests.get('https://my-api.com/items').json()
item_data = [{'id': 1, 'name': 'My Item'}]

items = TypeAdapter(List[Item]).validate_python(item_data)
print(items)
#> [Item(id=1, name='My Item')]
```

[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] is capable of parsing data into any of the types Pydantic can handle as fields of a [`BaseModel`][pydantic.main.BaseModel].
[`TypeAdapter`][pydantic.type_adapter.TypeAdapter]は、Pydanticが[`BaseModel`][pydantic.main.BaseModel]のフィールドとして処理できる任意の型にデータを解析することができます。

!!! info "Performance considerations"
    <!-- When creating an instance of `TypeAdapter`, the provided type must be analyzed and converted into a pydantic-core schema. This comes with some non-trivial overhead, so it is recommended to create a `TypeAdapter` for a given type just once and reuse it in loops or other performance-critical code. -->
    `TypeAdapter`のインスタンスを作成する場合、提供された型を解析し、pydantic-coreスキーマに変換する必要があります。これにはいくつかの重要なオーバーヘッドが伴うため、特定の型に対して`TypeAdapter`を一度だけ作成し、ループやその他のパフォーマンスが重要なコードで再利用することをお勧めします。
