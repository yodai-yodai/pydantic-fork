!!! warning "🚧 Work in Progress"
    This page is a work in progress.

# JSON

{% include-markdown "../warning.md" %}

## Json Parsing

??? api "API Documentation"
    [`pydantic.main.BaseModel.model_validate_json`][pydantic.main.BaseModel.model_validate_json]
    [`pydantic.type_adapter.TypeAdapter.validate_json`][pydantic.type_adapter.TypeAdapter.validate_json]
    [`pydantic_core.from_json`][pydantic_core.from_json]

<!-- Pydantic provides builtin JSON parsing, which helps achieve: -->
Pydanticは組み込みのJSON解析を提供し、次のことを実現するのに役立ちます。

<!--
* Significant performance improvements without the cost of using a 3rd party library
* Support for custom errors
* Support for `strict` specifications
-->
* サードパーティ製ライブラリを使用せずに、パフォーマンスが大幅に向上
* カスタムエラーのサポート
* 「厳密な」仕様のサポート

<!-- Here's an example of Pydantic's builtin JSON parsing via the [`model_validate_json`][pydantic.main.BaseModel.model_validate_json] method, showcasing the support for `strict` specifications while parsing JSON data that doesn't match the model's type annotations: -->
以下は、[`model_validate_json`][pydantic.main.BaseModel.model_validate_json]メソッドによるPydanticの組み込みJSON解析の例で、モデルの型アノテーションと一致しないJSONデータを解析する際の`strict`仕様のサポートを示しています。

```py
from datetime import date
from typing import Tuple

from pydantic import BaseModel, ConfigDict, ValidationError


class Event(BaseModel):
    model_config = ConfigDict(strict=True)

    when: date
    where: Tuple[int, int]


json_data = '{"when": "1987-01-28", "where": [51, -1]}'
print(Event.model_validate_json(json_data))  # (1)!
#> when=datetime.date(1987, 1, 28) where=(51, -1)

try:
    Event.model_validate({'when': '1987-01-28', 'where': [51, -1]})  # (2)!
except ValidationError as e:
    print(e)
    """
    2 validation errors for Event
    when
      Input should be a valid date [type=date_type, input_value='1987-01-28', input_type=str]
    where
      Input should be a valid tuple [type=tuple_type, input_value=[51, -1], input_type=list]
    """
```

<!-- 1. JSON has no `date` or tuple types, but Pydantic knows that so allows strings and arrays as inputs respectively when parsing JSON directly. -->
1. JSONには`date`型もタプル型もありませんが、Pydanticはそれを知っているので、JSONを直接解析するときには文字列と配列をそれぞれ入力として使用できます。
<!-- 2. If you pass the same values to the [`model_validate`][pydantic.main.BaseModel.model_validate] method, Pydantic will raise a validation error because the `strict` configuration is enabled. -->
2. 同じ値を[`model_validate`][pydantic.main.BaseModel.model_validate]メソッドに渡した場合、`strict`設定が有効になっているため、Pydanticは検証エラーを発生します。

<!-- In v2.5.0 and above, Pydantic uses [`jiter`](https://docs.rs/jiter/latest/jiter/), a fast and iterable JSON parser, to parse JSON data.
Using `jiter` compared to `serde` results in modest performance improvements that will get even better in the future. -->
v2.5.0以降では、Pydanticは高速で反復可能なJSONパーサーである[`jiter`](https://docs.rs/jiter/latest/jiter/)を使用してJSONデータを解析します。
`serde`と比較して`jeter`を使用すると、将来さらに良くなるであろう適度なパフォーマンスの改善が得られます。

<!-- The `jiter` JSON parser is almost entirely compatible with the `serde` JSON parser, with one noticeable enhancement being that `jiter` supports deserialization of `inf` and `NaN` values. -->
<!-- In the future, `jiter` is intended to enable support validation errors to include the location in the original JSON input which contained the invalid value. -->
`jeter`JSONパーサーは`serde`JSONパーサーとほぼ完全に互換性がありますが、注目すべき改良点の1つは`jeter`が`inf`値と`NaN`値のデシリアライズをサポートしていることです。
将来、`jeter`は、サポート検証エラーが、無効な値を含む元のJSON入力内の場所を含むことを可能にすることを意図しています。

### Partial JSON Parsing

<!-- **Starting in v2.7.0**, Pydantic's [JSON parser](https://docs.rs/jiter/latest/jiter/) offers support for partial JSON parsing, which is exposed via [`pydantic_core.from_json`][pydantic_core.from_json]. Here's an example of this feature in action: -->
**v2.7.0から**、Pydanticの[JSON parser](https://docs.rs/jiter/latest/jiter/)は、[`pydantic_core.from_json`][pydantic_core.from_json]で公開されている部分的なJSON解析をサポートしています。この機能の動作例を次に示します。

```py
from pydantic_core import from_json

partial_json_data = '["aa", "bb", "c'  # (1)!

try:
    result = from_json(partial_json_data, allow_partial=False)
except ValueError as e:
    print(e)  # (2)!
    #> EOF while parsing a string at line 1 column 15

result = from_json(partial_json_data, allow_partial=True)
print(result)  # (3)!
#> ['aa', 'bb']
```

<!-- 1. The JSON list is incomplete - it's missing a closing `"]` -->
1. JSONリストが不完全です - `"]`で閉じられていません。
<!-- 2. When `allow_partial` is set to `False` (the default), a parsing error occurs. -->
2. `allow_partial`が`False`(デフォルト)に設定されている場合、解析エラーが発生します。
<!-- 3. When `allow_partial` is set to `True`, part of the input is deserialized successfully. -->
3. `allow_partial`が`True`に設定されている場合、入力の一部が正常にデシリアライズされます。

<!-- This also works for deserializing partial dictionaries. For example: -->
これは、部分的な辞書をデシリアライズする場合にも有効です。

```py
from pydantic_core import from_json

partial_dog_json = '{"breed": "lab", "name": "fluffy", "friends": ["buddy", "spot", "rufus"], "age'
dog_dict = from_json(partial_dog_json, allow_partial=True)
print(dog_dict)
#> {'breed': 'lab', 'name': 'fluffy', 'friends': ['buddy', 'spot', 'rufus']}
```

!!! tip "Validating LLM Output"
    <!-- This feature is particularly beneficial for validating LLM outputs.
    We've written some blog posts about this topic, which you can find [here](https://blog.pydantic.dev/blog/category/llms/). -->
    この機能は、LLM出力の検証に特に有効です。
    私たちはこのトピックについていくつかのブログ記事を書いており、[ここ](https://blog.pydantic.dev/blog/category/llms/)で見ることができます。

<!-- In future versions of Pydantic, we expect to expand support for this feature through either Pydantic's other JSON validation functions ([`pydantic.main.BaseModel.model_validate_json`][pydantic.main.BaseModel.model_validate_json] and [`pydantic.type_adapter.TypeAdapter.validate_json`][pydantic.type_adapter.TypeAdapter.validate_json]) or model configuration. Stay tuned 🚀! -->
Pydanticの将来のバージョンでは、Pydanticの他のJSON検証関数([`pydantic.main.BaseModel.model_validate_json`][pydantic.main.BaseModel.model_validate_json]および[`pydantic.type_adapter.TypeAdapter.validate_json`][pydantic.type_adapter.TypeAdapter.validate_json])またはモデル構成のいずれかを使用して、この機能のサポートを拡張する予定です🚀!

<!-- For now, you can use [`pydantic_core.from_json`][pydantic_core.from_json] in combination with [`pydantic.main.BaseModel.model_validate`][pydantic.main.BaseModel.model_validate] to achieve the same result. Here's an example: -->
今のところ、[`pydantic_core.from_json`][pydantic_core.from_json]を[`pydantic.main.BaseModel.model_validate`][pydantic.main.BaseModel.model_validate]と組み合わせて使用しても同じ結果が得られます。以下に例を示します。

```py
from pydantic_core import from_json

from pydantic import BaseModel


class Dog(BaseModel):
    breed: str
    name: str
    friends: list


partial_dog_json = '{"breed": "lab", "name": "fluffy", "friends": ["buddy", "spot", "rufus"], "age'
dog = Dog.model_validate(from_json(partial_dog_json, allow_partial=True))
print(repr(dog))
#> Dog(breed='lab', name='fluffy', friends=['buddy', 'spot', 'rufus'])
```

!!! tip
    <!-- For partial JSON parsing to work reliably, all fields on the model should have default values. -->
    部分的なJSON解析が確実に動作するためには、モデル上のすべてのフィールドにデフォルト値が必要です。

<!-- Check out the following example for a more in-depth look at how to use default values with partial JSON parsing: -->
部分的なJSON解析でデフォルト値を使用する方法の詳細については、次の例を参照してください。

!!! example "Using default values with partial JSON parsing"

    ```py
    from typing import Any, Optional, Tuple

    import pydantic_core
    from typing_extensions import Annotated

    from pydantic import BaseModel, ValidationError, WrapValidator


    def default_on_error(v, handler) -> Any:
        """
        Raise a PydanticUseDefault exception if the value is missing.

        This is useful for avoiding errors from partial
        JSON preventing successful validation.
        """
        try:
            return handler(v)
        except ValidationError as exc:
            # there might be other types of errors resulting from partial JSON parsing
            # that you allow here, feel free to customize as needed
            if all(e['type'] == 'missing' for e in exc.errors()):
                raise pydantic_core.PydanticUseDefault()
            else:
                raise


    class NestedModel(BaseModel):
        x: int
        y: str


    class MyModel(BaseModel):
        foo: Optional[str] = None
        bar: Annotated[
            Optional[Tuple[str, int]], WrapValidator(default_on_error)
        ] = None
        nested: Annotated[
            Optional[NestedModel], WrapValidator(default_on_error)
        ] = None


    m = MyModel.model_validate(
        pydantic_core.from_json('{"foo": "x", "bar": ["world",', allow_partial=True)
    )
    print(repr(m))
    #> MyModel(foo='x', bar=None, nested=None)


    m = MyModel.model_validate(
        pydantic_core.from_json(
            '{"foo": "x", "bar": ["world", 1], "nested": {"x":', allow_partial=True
        )
    )
    print(repr(m))
    #> MyModel(foo='x', bar=('world', 1), nested=None)
    ```

### Caching Strings

<!-- **Starting in v2.7.0**, Pydantic's [JSON parser](https://docs.rs/jiter/latest/jiter/) offers support for configuring how Python strings are cached during JSON parsing and validation (when Python strings are constructed from Rust strings during Python validation, e.g. after `strip_whitespace=True`). -->
**v2.7.0**から、Pydanticの[JSONパーサ](https://docs.rs/jiter/latest/jiter/)は、JSONの解析と検証中にPython文字列をキャッシュする方法の設定をサポートしています(Python検証中にPython文字列がRust文字列から構築される場合、例えば`strip_whitespace=True`の後など)。

<!-- The `cache_strings` setting is exposed via both [model config][pydantic.config.ConfigDict] and [`pydantic_core.from_json`][pydantic_core.from_json]. -->
`cache_strings`の設定は、[model config][pydantic.config.ConfigDict]と[`pydantic_core.from_json`][pydantic_core.from_json]の両方で公開されています。

<!-- The `cache_strings` setting can take any of the following values: -->
`cache_strings`設定には、次のいずれかの値を指定できます。

<!--
* `True` or `'all'` (the default): cache all strings
* `'keys'`: cache only dictionary keys, this **only** applies when used with [`pydantic_core.from_json`][pydantic_core.from_json] or when parsing JSON using [`Json`][pydantic.types.Json]
* `False` or `'none'`: no caching
 -->
* `True`または`'all'`(デフォルト): すべての文字列をキャッシュします。
* `'keys'`: 辞書キーのみをキャッシュします。これは[`pydantic_core.from_json`][pydantic_core.from_json]と一緒に使用する場合、または[`Json`][pydantic.types.Json]を使用してJSONを解析する場合に**のみ**適用されます。
* `False`または`'none'`: キャッシュしない

<!-- Using the string caching feature results in performance improvements, but increases memory usage slightly. -->
文字列キャッシング機能を使用すると、パフォーマンスが向上しますが、メモリ使用量が若干増加します。

!!! note "String Caching Details"

    <!-- 1. Strings are cached using a fully associative cache with a size of [16,384](https://github.com/pydantic/jiter/blob/5bbdcfd22882b7b286416b22f74abd549c7b2fd7/src/py_string_cache.rs#L113). -->
    1. 文字列は、サイズ[16,384](https://github.com/pydantic/jiter/blob/5bbdcfd22882b7b286416b22f74abd549c7b2fd7/src/py_string_cache.rs#L113)のフルアソシアティブ方式を使用してキャッシュされます。
    <!-- 2. Only strings where `len(string) < 64` are cached. -->
    2. `len(string)<64`の文字列のみがキャッシュされます。
    <!-- 3. There is some overhead to looking up the cache, which is normally worth it to avoid constructing strings. However, if you know there will be very few repeated strings in your data, you might get a performance boost by disabling this setting with `cache_strings=False`. -->
    3. キャッシュの検索には多少のオーバーヘッドがありますが、これは通常、文字列の構築を避けるために行う価値があります。ただし、データ内に繰り返される文字列がほとんどないことがわかっている場合は、`cache_strings=False`でこの設定を無効にすることでパフォーマンスが向上する可能性があります。


## JSON Serialization

??? api "API Documentation"
    [`pydantic.main.BaseModel.model_dump_json`][pydantic.main.BaseModel.model_dump_json]<br>
    [`pydantic.type_adapter.TypeAdapter.dump_json`][pydantic.type_adapter.TypeAdapter.dump_json]<br>
    [`pydantic_core.to_json`][pydantic_core.to_json]<br>

<!-- For more information on JSON serialization, see the [Serialization Concepts](./serialization.md#modelmodel_dump_json) page. -->
JSONシリアライゼーションの詳細については、[Serialization Concepts](./serialization.md#modelmodel_dump_json)ページを参照してください。
