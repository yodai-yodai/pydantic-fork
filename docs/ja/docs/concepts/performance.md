{% include-markdown "../warning.md" %}

# Performance tips

<!-- In most cases Pydantic won't be your bottle neck, only follow this if you're sure it's necessary. -->
ほとんどの場合、Pydanticはボトルネックにはならないので、それが必要だと確信している場合にのみ利用してください。

## In general, use `model_validate_json()` not `model_validate(json.loads(...))`

<!-- On `model_validate(json.loads(...))`, the JSON is parsed in Python, then converted to a dict, then it's validated internally.
On the other hand, `model_validate_json()` already performs the validation internally. -->
`model_validate(json.loads(...))`では、JSONがPythonで解析され、dictに変換されてから内部で検証されます。
一方、`model_validate_json()`はすでに内部で検証を実行しています。

<!-- There are a few cases where `model_validate(json.loads(...))` may be faster. Specifically, when using a `'before'` or `'wrap'` validator on a model, validation may be faster with the two step method.
You can read more about these special cases in [this discussion](https://github.com/pydantic/pydantic/discussions/6388#discussioncomment-8193105). -->
`model_validate(json.loads(...))`の方が高速な場合がいくつかあります。具体的には、モデルに対して`'before'`または`'wrap'`バリデータを使用する場合、2ステップ法の方が検証が高速になる可能性があります。
これらの特殊なケースの詳細については、[this discussion](https://github.com/pydantic/pydantic/discussion/6388#discussioncomment-8193105)を参照してください。

<!-- Many performance improvements are currently in the works for `pydantic-core`, as discussed [here](https://github.com/pydantic/pydantic/discussions/6388#discussioncomment-8194048).
Once these changes are merged, we should be at the point where `model_validate_json()` is always faster than `model_validate(json.loads(...))`. -->
現在、`pydantic-core`では、[here]で議論されているように、多くのパフォーマンス改善が行われている(https://github.com/pydantic/pydantic/discussion/6388#discussioncomment-8194048)。
これらの変更がマージされれば、`model_validate_json()`が常に`model_validate(json.loads(...))`よりも高速になるはずです。

## `TypeAdapter` instantiated once

<!-- The idea here is to avoid constructing validators and serializers more than necessary.
Each time a `TypeAdapter` is instantiated, it will construct a new validator and serializer.
If you're using a `TypeAdapter` in a function, it will be instantiated each time the function is called. Instead, instantiate it once, and reuse it. -->
ここでの考え方は、必要以上にバリデーターとシリアライザーを構築しないようにすることです。
`TypeAdapter`がインスタンス化されるたびに、新しいバリデータとシリアライザが構築されます。
関数で`TypeAdapter`を使用している場合、関数が呼び出されるたびにインスタンス化されます。代わりに、一度インスタンス化してから再利用してください。

=== ":x: Bad"

    ```py lint="skip"
    from typing import List

    from pydantic import TypeAdapter


    def my_func():
        adapter = TypeAdapter(List[int])
        # do something with adapter
    ```

=== ":white_check_mark: Good"

    ```py lint="skip"
    from typing import List

    from pydantic import TypeAdapter

    adapter = TypeAdapter(List[int])

    def my_func():
        ...
        # do something with adapter
    ```

## `Sequence` vs `list` or `tuple` - `Mapping` vs `dict`

<!-- When using `Sequence`, Pydantic calls `isinstance(value, Sequence)` to check if the value is a sequence.
Also, Pydantic will try to validate against different types of sequences, like `list` and `tuple`.
If you know the value is a `list` or `tuple`, use `list` or `tuple` instead of `Sequence`. -->
`Sequence`を使用する場合、Pydanticは`isinstance(value, Sequence)`を呼び出して、値がシーケンスかどうかをチェックします。
また、Pydanticは`list`や`tuple`のような異なるタイプのシーケンスに対して検証を試みます。
値が`list`または`tuple`であることがわかっている場合は、`Sequence`の代わりに`list`または`tuple`を使用してください。

<!-- The same applies to `Mapping` and `dict`.
If you know the value is a `dict`, use `dict` instead of `Mapping`. -->
同じことが`Mapping`と`dict`にも当てはまります。
値が`dict`であることがわかっている場合は、`Mapping`の代わりに`dict`を使用してください。

## Don't do validation when you don't have to - use `Any` to keep the value unchanged

<!-- If you don't need to validate a value, use `Any` to keep the value unchanged. -->
値を検証する必要がない場合は、`Any`を使用して値を変更しないようにします。

```py
from typing import Any

from pydantic import BaseModel


class Model(BaseModel):
    a: Any


model = Model(a=1)
```

## Avoid extra information via subclasses of primitives

=== "Don't do this"

    ```py
    class CompletedStr(str):
        def __init__(self, s: str):
            self.s = s
            self.done = False
    ```

=== "Do this"

    ```py
    from pydantic import BaseModel


    class CompletedModel(BaseModel):
        s: str
        done: bool = False
    ```

## Use tagged union, not union

<!-- Tagged union (or discriminated union) is a union with a field that indicates which type it is. -->
タグ付きユニオン(または識別されたユニオン)は、それがどのタイプであるかを示すフィールドを持つユニオンです。

```py test="skip"
from typing import Any

from typing_extensions import Literal

from pydantic import BaseModel, Field


class DivModel(BaseModel):
    el_type: Literal['div'] = 'div'
    class_name: str | None = None
    children: list[Any] | None = None


class SpanModel(BaseModel):
    el_type: Literal['span'] = 'span'
    class_name: str | None = None
    contents: str | None = None


class ButtonModel(BaseModel):
    el_type: Literal['button'] = 'button'
    class_name: str | None = None
    contents: str | None = None


class InputModel(BaseModel):
    el_type: Literal['input'] = 'input'
    class_name: str | None = None
    value: str | None = None


class Html(BaseModel):
    contents: DivModel | SpanModel | ButtonModel | InputModel = Field(
        discriminator='el_type'
    )
```

<!-- See [Discriminated Unions] for more details. -->
詳細については、[Discriminated Unions]を参照してください。

## Use `TypedDict` over nested models

<!-- Instead of using nested models, use `TypedDict` to define the structure of the data. -->
ネストされたモデルを使用する代わりに、`TypedDict`を使用してデータの構造を定義してください。

??? info "Performance comparison"
    <!-- With a simple benchmark, `TypedDict` is about ~2.5x faster than nested models: -->
    単純なベンチマークでは、`TypedDict`はネストされたモデルよりも約2.5倍高速です。

    ```py test="skip"
    from timeit import timeit

    from typing_extensions import TypedDict

    from pydantic import BaseModel, TypeAdapter


    class A(TypedDict):
        a: str
        b: int


    class TypedModel(TypedDict):
        a: A


    class B(BaseModel):
        a: str
        b: int


    class Model(BaseModel):
        b: B


    ta = TypeAdapter(TypedModel)
    result1 = timeit(
        lambda: ta.validate_python({'a': {'a': 'a', 'b': 2}}), number=10000
    )
    result2 = timeit(
        lambda: Model.model_validate({'b': {'a': 'a', 'b': 2}}), number=10000
    )
    print(result2 / result1)
    ```

## Avoid wrap validators if you really care about performance

<!-- Wrap validators are generally slower than other validators.
This is because they require that data is materialized in Python during validation. Wrap validators can be incredibly useful for complex validation logic, but if you're looking for the best performance, you should avoid them. -->
一般に、ラップ・バリデーターは他のバリデーターよりも低速です。
これは、検証時にPythonでデータを実体化する必要があるためです。ラップ・バリデーターは複雑な検証ロジックには非常に便利ですが、最高のパフォーマンスを求めるのであれば、ラップ・バリデーターは避けるべきです。

## Failing early with `FailFast`

<!-- Starting in v2.8+, you can apply the `FailFast` annotation to sequence types to fail early if any item in the sequence fails validation.
If you use this annotation, you won't get validation errors for the rest of the items in the sequence if one fails, so you're effectively trading off visibility for performance. -->
v2.8以降では、シーケンス内のいずれかの項目が検証に失敗した場合に早期に失敗するように、シーケンスタイプに`FailFast`アノテーションを適用できるようになりました。
このアノテーションを使用すると、シーケンス内の残りの項目が失敗しても検証エラーが発生しないため、可視性とパフォーマンスを効果的にトレードオフすることができます。

```py
from typing import List

from typing_extensions import Annotated

from pydantic import FailFast, TypeAdapter, ValidationError

ta = TypeAdapter(Annotated[List[bool], FailFast()])
try:
    ta.validate_python([True, 'invalid', False, 'also invalid'])
except ValidationError as exc:
    print(exc)
    """
    1 validation error for list[bool]
    1
      Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value='invalid', input_type=str]
    """
```

<!-- Read more about `FailFast` [here][pydantic.types.FailFast]. -->
`FailFast`についての詳細はこちら[here][pydantic.types.FailFast]をご覧ください。

[Discriminated Unions]: ../concepts/unions.md#discriminated-unions
