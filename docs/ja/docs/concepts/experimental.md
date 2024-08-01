{% include-markdown "../warning.md" %}

# Experimental Features

<!-- In this section you will find documentation for new, experimental features in Pydantic. These features are subject to change or removal, and we are looking for feedback and suggestions before making them a permanent part of Pydantic. -->
このセクションには、Pydanticの新しい実験的な機能に関するドキュメントがあります。これらの機能は変更または削除される可能性があり、Pydanticの恒久的な一部にする前にフィードバックと提案を求めています。

<!-- See our [Version Policy](../version-policy.md#experimental-features) for more information on experimental features. -->
試験的な機能の詳細については、[Version Policy](../version-policy.md#experimental-features)を参照してください。

## Feedback

<!-- We welcome feedback on experimental features! Please open an issue on the [Pydantic GitHub repository](https://github.com/pydantic/pydantic/issues/new/choose) to share your thoughts, requests, or suggestions. -->
実験的な機能に関するフィードバックを歓迎します![Pydantic GitHub repository](https://GitHub.com/pydantic/pydantic/issues/new/choose)でIssueを開いて、考え、要望、提案を共有してください。

<!-- We also encourage you to read through existing feedback and add your thoughts to existing issues. -->
また、既存のフィードバックを読み、既存の問題に自分の考えを追加することもお勧めします。

## Warnings on Import

<!-- When you import an experimental feature from the `experimental` module, you'll see a warning message that the feature is experimental. You can disable this warning with the following: -->
`experimental`モジュールから試験的な機能をインポートすると、その機能が試験的であることを示す警告メッセージが表示されます。この警告を無効にするには、次のようにします。

```python
import warnings

from pydantic import PydanticExperimentalWarning

warnings.filterwarnings('ignore', category=PydanticExperimentalWarning)
```

## Pipeline API

<!-- Pydantic v2.8.0 introduced an experimental "pipeline" API that allows composing of parsing (validation), constraints and transformations in a more type-safe manner than existing APIs.
This API is subject to change or removal, we are looking for feedback and suggestions before making it a permanent part of Pydantic. -->
Pydantic v2.8.0では、既存のAPIよりも型安全な方法でパース(バリデーション)、制約、変換を構成できる実験的な"パイプライン"APIが導入されました。
このAPIは変更または削除される可能性があります。Pydanticの恒久的な一部にする前に、フィードバックと提案を求めています。

??? api "API Documentation"
    [`pydantic.experimental.pipeline`][pydantic.experimental.pipeline]<br>

<!-- Generally, the pipeline API is used to define a sequence of steps to apply to incoming data during validation.
The pipeline API is designed to be more type-safe and composable than the existing Pydantic API. -->
一般に、パイプラインAPIは、検証中に入力データに適用する一連のステップを定義するために使用されます。
パイプラインAPIは、既存のPydantic APIよりも型安全で構成可能なように設計されています。

<!-- Each step in the pipeline can be: -->
パイプラインの各ステップは次のとおりです。

<!-- * A validation step that runs pydantic validation on the provided type
* A transformation step that modifies the data
* A constraint step that checks the data against a condition
* A predicate step that checks the data against a condition and raises an error if it returns `False` -->
* 指定された型に対してpydantic検証を実行する検証ステップ
* データを変更する変換ステップ
* 条件に対してデータをチェックする制約ステップ
* 条件に対してデータをチェックし、`False`が返された場合にエラーを発生させる述部ステップ

<!-- TODO: (@sydney-runkle) add more documentation once we solidify the API during the experimental phase -->

<!-- Note that the following example attempts to be exhaustive at the cost of complexity: if you find yourself writing this many transformations in type annotations you may want to consider having a `UserIn` and `UserOut` model (example below) or similar where you make the transformations via idomatic plain Python code. -->
以下の例は、複雑さを犠牲にして網羅的にしようとするものであることに注意してください。型アノテーションでこれだけ多くの変換を記述している場合は、`UserIn`モデルと`UserOut`モデル(以下の例)を使用するか、または同様の変換をidomaticプレーンPythonコードで行うことを検討してください。

<!-- These APIs are meant for situations where the code savings are significant and the added complexity is relatively small. -->
これらのAPIは、コードの節約が大きく、追加される複雑さが比較的小さい状況を対象としています。

```python
from __future__ import annotations

from datetime import datetime

from typing_extensions import Annotated

from pydantic import BaseModel
from pydantic.experimental.pipeline import validate_as, validate_as_deferred


class User(BaseModel):
    name: Annotated[str, validate_as(str).str_lower()]  # (1)!
    age: Annotated[int, validate_as(int).gt(0)]  # (2)!
    username: Annotated[str, validate_as(str).str_pattern(r'[a-z]+')]  # (3)!
    password: Annotated[
        str,
        validate_as(str)
        .transform(str.lower)
        .predicate(lambda x: x != 'password'),  # (4)!
    ]
    favorite_number: Annotated[  # (5)!
        int,
        (validate_as(int) | validate_as(str).str_strip().validate_as(int)).gt(
            0
        ),
    ]
    friends: Annotated[list[User], validate_as(...).len(0, 100)]  # (6)!
    family: Annotated[  # (7)!
        list[User],
        validate_as_deferred(lambda: list[User]).transform(lambda x: x[1:]),
    ]
    bio: Annotated[
        datetime,
        validate_as(int)
        .transform(lambda x: x / 1_000_000)
        .validate_as(...),  # (8)!
    ]
```

<!-- 1. Lowercase a string.
2. Constrain an integer to be greater than zero.
3. Constrain a string to match a regex pattern.
4. You can also use the lower level transform, constrain and predicate methods.
5. Use the `|` or `&` operators to combine steps (like a logical OR or AND).
6. Calling `validate_as(...)` with `Ellipsis`, `...` as the first positional argument implies `validate_as(<field type>)`. Use `validate_as(Any)` to accept any type.
7. For recursive types you can use `validate_as_deferred` to reference the type itself before it's defined.
8. You can call `validate_as()` before or after other steps to do pre or post processing. -->
1. 文字列を小文字にします。
2. 整数がゼロより大きくなるように制約します。
3. 正規表現パターンに一致するように文字列を制約します。
4. 下位レベルのtransform、constrain、predicateメソッドも使用できます。
5. ``or`&`演算子を使ってステップを結合します(論理ORやAND)。
6. 最初の位置引数として`Ellipsis`、`...`を指定して`validate_as(...)`を呼び出すことは、`validate_as(<field type>)`を意味します。任意の型を受け入れるには`validate_as(Any)`を使用してください。
7. 再帰型の場合、`validate_as_deferred`を使用して、型を定義する前に型自体を参照できます。
8. 他のステップの前または後に`validate_as()`を呼び出して、前処理または後処理を行うことができます。

### Mapping from `BeforeValidator`, `AfterValidator` and `WrapValidator`

<!-- The `validate_as` method is a more type-safe way to define `BeforeValidator`, `AfterValidator` and `WrapValidator`: -->
`validate_as`メソッドは、`BeforeValidator`、`AfterValidator`および`WrapValidator`を定義するための、より型安全な方法です。

```python
from typing_extensions import Annotated

from pydantic.experimental.pipeline import transform, validate_as

# BeforeValidator
Annotated[int, validate_as(str).str_strip().validate_as(...)]  # (1)!
# AfterValidator
Annotated[int, transform(lambda x: x * 2)]  # (2)!
# WrapValidator
Annotated[
    int,
    validate_as(str)
    .str_strip()
    .validate_as(...)
    .transform(lambda x: x * 2),  # (3)!
]
```

<!-- 1. Strip whitespace from a string before parsing it as an integer.
2. Multiply an integer by 2 after parsing it.
3. Strip whitespace from a string, validate it as an integer, then multiply it by 2. -->
1. 文字列を整数として解析する前に、文字列から空白を取り除きます。
2. 整数を解析した後、2を掛けます。
3. 文字列から空白を取り除き、整数として検証してから、2を掛けます。

### Alternative patterns

<!-- There are many alternative patterns to use depending on the scenario.
Just as an example, consider the `UserIn` and `UserOut` pattern mentioned above: -->
シナリオに応じて、さまざまな代替パターンを使用できます。
一例として、上記の`UserIn`と`UserOut`パターンを考えてみましょう。

```python
from __future__ import annotations

from pydantic import BaseModel


class UserIn(BaseModel):
    favorite_number: int | str


class UserOut(BaseModel):
    favorite_number: int


def my_api(user: UserIn) -> UserOut:
    favorite_number = user.favorite_number
    if isinstance(favorite_number, str):
        favorite_number = int(user.favorite_number.strip())

    return UserOut(favorite_number=favorite_number)


assert my_api(UserIn(favorite_number=' 1 ')).favorite_number == 1
```

<!-- This example uses plain idiomatic Python code that may be easier to understand, type-check, etc. than the examples above.
The approach you choose should really depend on your use case.
You will have to compare verbosity, performance, ease of returning meaningful errors to your users, etc. to choose the right pattern.
Just be mindful of abusing advanced patterns like the pipeline API just because you can. -->
この例では、上記の例よりも理解しやすく、型チェックなども簡単な慣用的なPythonコードを使用しています。
選択するアプローチは、実際にはユース・ケースによって異なります。
適切なパターンを選択するためには、冗長性、パフォーマンス、ユーザーに意味のあるエラーを返すことの容易さなどを比較する必要があります。
可能だからといって、パイプラインAPIのような高度なパターンを乱用することに注意してください。
