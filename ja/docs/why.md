# Why use Pydantic?

{% include-markdown "./warning.md" %}

<!-- Today, Pydantic is downloaded <span id="download-count">many</span> times a month and used by some of the largest and most recognisable organisations in the world. -->
現在、Pydanticは月に<span id="download-count">何度も</span>ダウンロードされており、世界で最も大きく、最も有名な組織によって使用されています。

<!-- It's hard to know why so many people have adopted Pydantic since its inception six years ago, but here are a few guesses. -->
Pydanticが6年前に開始されて以来、なぜ多くの人がPydanticを採用しているのかを知るのは難しいですが、いくつか考えられることがあります。

{% raw %}
## Type hints powering schema validation {#type-hints}
{% endraw %}

<!-- The schema that Pydantic validates against is generally defined by Python type hints. -->
Pydanticが検証するスキーマは、一般にPythonの型ヒントによって定義されます。

<!-- Type hints are great for this since, if you're writing modern Python, you already know how to use them.
Using type hints also means that Pydantic integrates well with static typing tools like mypy and pyright and IDEs like pycharm and vscode. -->
最近のPythonを作成している人であれば、すでに使い方を知っているはずなので、型のヒントはこの目的には最適です。
型ヒントを使用することは、Pydanticがmypyやpyrightのような静的型付けツールやpycharmやvscodeのようなIDEとうまく統合されることも意味します。

???+ example "Example - just type hints"
    _(This example requires Python 3.9+)_
    ```py requires="3.9"
    from typing import Annotated, Dict, List, Literal, Tuple

    from annotated_types import Gt

    from pydantic import BaseModel


    class Fruit(BaseModel):
        name: str  # (1)!
        color: Literal['red', 'green']  # (2)!
        weight: Annotated[float, Gt(0)]  # (3)!
        bazam: Dict[str, List[Tuple[int, bool, float]]]  # (4)!


    print(
        Fruit(
            name='Apple',
            color='red',
            weight=4.2,
            bazam={'foobar': [(1, True, 0.1)]},
        )
    )
    #> name='Apple' color='red' weight=4.2 bazam={'foobar': [(1, True, 0.1)]}
    ```

    1. The `name` field is simply annotated with `str` - any string is allowed.
    2. The [`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal) type is used to enforce that `color` is either `'red'` or `'green'`.
    3. Even when we want to apply constraints not encapsulated in python types, we can use [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated) and [`annotated-types`](https://github.com/annotated-types/annotated-types) to enforce constraints without breaking type hints.
    4. I'm not claiming "bazam" is really an attribute of fruit, but rather to show that arbitrarily complex types can easily be validated.

!!! tip "さらなる学習"
    <!-- See the [documentation on supported types](concepts/types.md)を参照してください。 -->
    [documentation on supported types](concepts/types.md)を参照してください。

## Performance

<!-- Pydantic's core validation logic is implemented in a separate package [`pydantic-core`](https://github.com/pydantic/pydantic-core), where validation for most types is implemented in Rust. -->
Pydanticのコア検証ロジックは、別のパッケージ[`pydantic-core`](https://github.com/pydantic/pydantic-core)に実装されており、ほとんどのタイプの検証はRustで実装されています。

<!-- As a result, Pydantic is among the fastest data validation libraries for Python. -->
その結果、PydanticはPython用の最も高速なデータ検証ライブラリの1つになっています。

??? example "Performance Example - Pydantic vs. dedicated code"
    In general, dedicated code should be much faster than a general-purpose validator, but in this example
    Pydantic is >300% faster than dedicated code when parsing JSON and validating URLs.

    ```py title="Performance Example" test="skip"
    import json
    import timeit
    from urllib.parse import urlparse

    import requests

    from pydantic import HttpUrl, TypeAdapter

    reps = 7
    number = 100
    r = requests.get('https://api.github.com/emojis')
    r.raise_for_status()
    emojis_json = r.content


    def emojis_pure_python(raw_data):
        data = json.loads(raw_data)
        output = {}
        for key, value in data.items():
            assert isinstance(key, str)
            url = urlparse(value)
            assert url.scheme in ('https', 'http')
            output[key] = url


    emojis_pure_python_times = timeit.repeat(
        'emojis_pure_python(emojis_json)',
        globals={
            'emojis_pure_python': emojis_pure_python,
            'emojis_json': emojis_json,
        },
        repeat=reps,
        number=number,
    )
    print(f'pure python: {min(emojis_pure_python_times) / number * 1000:0.2f}ms')
    #> pure python: 5.32ms

    type_adapter = TypeAdapter(dict[str, HttpUrl])
    emojis_pydantic_times = timeit.repeat(
        'type_adapter.validate_json(emojis_json)',
        globals={
            'type_adapter': type_adapter,
            'HttpUrl': HttpUrl,
            'emojis_json': emojis_json,
        },
        repeat=reps,
        number=number,
    )
    print(f'pydantic: {min(emojis_pydantic_times) / number * 1000:0.2f}ms')
    #> pydantic: 1.54ms

    print(
        f'Pydantic {min(emojis_pure_python_times) / min(emojis_pydantic_times):0.2f}x faster'
    )
    #> Pydantic 3.45x faster
    ```

<!-- Unlike other performance-centric libraries written in compiled languages, Pydantic also has excellent support for customizing validation via [functional validators](#customisation). -->
コンパイル言語で記述された他のパフォーマンス中心のライブラリとは異なり、Pydanticは[functional validators](#customisation)による検証のカスタマイズにも優れたサポートを提供しています。

!!! tip "さらなる学習"
    <!-- Samuel Colvin's [talk at PyCon 2023](https://youtu.be/pWZw7hYoRVU) explains how `pydantic-core` works and how it integrates with Pydantic. -->
    Samuel Colvinの[talk at PyCon 2023](https://youtu.be/pWZw7hYoRVU)は、`pydantic-core`がどのように機能し、どのようにPydanticと統合されているか解説しています。

## Serialization

<!-- Pydantic provides functionality to serialize model in three ways: -->
Pydanticは、次の3つの方法でモデルをシリアライズする機能を提供します。

<!--
1. To a Python `dict` made up of the associated Python objects
2. To a Python `dict` made up only of "jsonable" types
3. To a JSON string
-->
1. Pythonの`dict`に、関連付けられたPythonオブジェクトに構成する
2. Pythonの`dict`に、"jsonable"な型だけで構成する
3. JSON文字列への変換

<!-- In all three modes, the output can be customized by excluding specific fields, excluding unset fields, excluding default values, and excluding `None` values -->
3つのモードすべてにおいて、特定のフィールドを除外し、未設定のフィールドを除外し、デフォルト値を除外し、`None`値を除外することによって、出力をカスタマイズすることができます。

??? example "Example - Serialization 3 ways"
    ```py
    from datetime import datetime

    from pydantic import BaseModel


    class Meeting(BaseModel):
        when: datetime
        where: bytes
        why: str = 'No idea'


    m = Meeting(when='2020-01-01T12:00', where='home')
    print(m.model_dump(exclude_unset=True))
    #> {'when': datetime.datetime(2020, 1, 1, 12, 0), 'where': b'home'}
    print(m.model_dump(exclude={'where'}, mode='json'))
    #> {'when': '2020-01-01T12:00:00', 'why': 'No idea'}
    print(m.model_dump_json(exclude_defaults=True))
    #> {"when":"2020-01-01T12:00:00","where":"home"}
    ```

!!! tip "さらなる学習"
    <!-- See the [documentation on serialization](concepts/serialization.md). -->
    [documentation on serialization](concepts/serialization.md)を参照してください。

## JSON Schema

<!-- [JSON Schema](https://json-schema.org/) can be generated for any Pydantic schema &mdash; allowing self-documenting APIs and integration with a wide variety of tools which support JSON Schema. -->
[JSON Schema](https://json-schema.org/)は、任意のPydanticスキーマに対して生成することができ、APIの自己文書化と、JSONスキーマをサポートするさまざまなツールとの統合できます。

??? example "Example - JSON Schema"
    ```py
    from datetime import datetime

    from pydantic import BaseModel


    class Address(BaseModel):
        street: str
        city: str
        zipcode: str


    class Meeting(BaseModel):
        when: datetime
        where: Address
        why: str = 'No idea'


    print(Meeting.model_json_schema())
    """
    {
        '$defs': {
            'Address': {
                'properties': {
                    'street': {'title': 'Street', 'type': 'string'},
                    'city': {'title': 'City', 'type': 'string'},
                    'zipcode': {'title': 'Zipcode', 'type': 'string'},
                },
                'required': ['street', 'city', 'zipcode'],
                'title': 'Address',
                'type': 'object',
            }
        },
        'properties': {
            'when': {'format': 'date-time', 'title': 'When', 'type': 'string'},
            'where': {'$ref': '#/$defs/Address'},
            'why': {'default': 'No idea', 'title': 'Why', 'type': 'string'},
        },
        'required': ['when', 'where'],
        'title': 'Meeting',
        'type': 'object',
    }
    """
    ```

<!-- Pydantic generates [JSON Schema version 2020-12](https://json-schema.org/draft/2020-12/release-notes.html), the latest version of the standard which is compatible with [OpenAPI 3.1](https://www.openapis.org/blog/2021/02/18/openapi-specification-3-1-released). -->
Pydanticは、[OpenAPI 3.1](https://www.openapis.org/blog/2021/02/18/openapi-specification-3-1-released)と互換性のある標準の最新バージョンである[JSON Schema version 2020-12](https://json-schema.org/draft/02-12/release-notes.html)を生成します。

!!! tip "さらなる額十"
    <!-- See the [documentation on JSON Schema](concepts/json_schema.md). -->
    [documentation on JSON Schema](concepts/json_schema.md)を参照ください。

{% raw %}
## Strict mode and data coercion {#strict-lax}
{% endraw %}

<!-- By default, Pydantic is tolerant to common incorrect types and coerces data to the right type &mdash; e.g. a numeric string passed to an `int` field will be parsed as an `int`. -->
デフォルトでは、Pydanticは一般的な不正な型に対して耐性があり、データを正しい型に強制します。例えば、`int`フィールドに渡された数値文字列は`int`として解析します。

<!-- Pydantic also has `strict=True` mode &mdash; also known as "Strict mode" &mdash; where types are not coerced and a validation error is raised unless the input data exactly matches the schema or type hint. -->
Pydanticには"strict=True"モードもあります。これは"Strictモード"とも呼ばれ、型が強制されず、入力データがスキーマや型のヒントと正確に一致しない限り、検証エラーが発生します。

<!-- But strict mode would be pretty useless when validating JSON data since JSON doesn't have types matching many common python types like `datetime`, `UUID` or `bytes`. -->
しかし、strictモードはJSONデータを検証するときにはほとんど役に立たないでしょう。なぜなら、JSONには`datetime`、`UUID`、`bytes`のような多くの一般的なpython型と一致する型がないからです。

<!-- To solve this, Pydantic can parse and validate JSON in one step. This allows sensible data conversion like RFC3339 (aka ISO8601) strings to `datetime` objects. Since the JSON parsing is implemented in Rust, it's also very performant. -->
これを解決するために、Pydanticは1つのステップでJSONを解析して検証することができます。これにより、RFC3339(別名ISO8601)文字列のような適切なデータ変換を`datetime`オブジェクトにすることができます。JSON解析はRustで実装されているため、非常にパフォーマンスに優れています。

??? example "Example - Strict mode that's actually useful"
    ```py
    from datetime import datetime

    from pydantic import BaseModel, ValidationError


    class Meeting(BaseModel):
        when: datetime
        where: bytes


    m = Meeting.model_validate({'when': '2020-01-01T12:00', 'where': 'home'})
    print(m)
    #> when=datetime.datetime(2020, 1, 1, 12, 0) where=b'home'
    try:
        m = Meeting.model_validate(
            {'when': '2020-01-01T12:00', 'where': 'home'}, strict=True
        )
    except ValidationError as e:
        print(e)
        """
        2 validation errors for Meeting
        when
          Input should be a valid datetime [type=datetime_type, input_value='2020-01-01T12:00', input_type=str]
        where
          Input should be a valid bytes [type=bytes_type, input_value='home', input_type=str]
        """

    m_json = Meeting.model_validate_json(
        '{"when": "2020-01-01T12:00", "where": "home"}'
    )
    print(m_json)
    #> when=datetime.datetime(2020, 1, 1, 12, 0) where=b'home'
    ```

!!! tip "さらなる学習"
    <!-- See the [documentation on strict mode](concepts/strict_mode.md). -->
    [documentation on strict mode](concepts/strict_mode.md)を参照してください。

{% raw %}
## Dataclasses, TypedDicts, and more {#typeddict}
{% endraw %}

<!-- Pydantic provides four ways to create schemas and perform validation and serialization: -->
Pydanticは、スキーマを作成し、検証とシリアライズを実行するための4つの方法を提供しています。

<!-- 1. [`BaseModel`](concepts/models.md) &mdash; Pydantic's own super class with many common utilities available via instance methods.
2. [`pydantic.dataclasses.dataclass`](concepts/dataclasses.md) &mdash; a wrapper around standard dataclasses which performs validation when a dataclass is initialized.
3. [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] &mdash; a general way to adapt any type for validation and serialization. This allows types like [`TypedDict`](api/standard_library_types.md#typeddict) and [`NamedTuple`](api/standard_library_types.md#typingnamedtuple) to be validated as well as simple scalar values like `int` or `timedelta` &mdash; [all types](concepts/types.md) supported can be used with `TypeAdapter`.
4. [`validate_call`](concepts/validation_decorator.md) &mdash; a decorator to perform validation when calling a function. -->

1. [`BaseModel`](concepts/models.md) &mdash; Pydantic独自のスーパークラスには、インスタンスメソッドを介して利用できる多くの共通ユーティリティがあります。
2. [`pydantic.dataclasses.dataclass`](concepts/dataclasses.md) &mdash; データクラスの初期化時に検証を実行する標準データクラスのラッパです。
3. [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] &mdash; 任意の型を検証とシリアライゼーションに適応させる一般的な方法です。これにより、[`TypedDict`](api/standard_library_types.md#TypedDict)や[`NamedTuple`](api/standard_library_types.md#typingnamedtuple)のような型を検証することができます。また、`int`や`timedelta` &mdash; [all types](concepts/types.md)サポートを`TypeAdapter`で使用することもできます。
4. [`validate_call`](concepts/validation_decorator.md) &mdash; 関数を呼び出すときに検証を実行するデコレータです。

??? example "Example - schema based on TypedDict"
    ```py
    from datetime import datetime

    from typing_extensions import NotRequired, TypedDict

    from pydantic import TypeAdapter


    class Meeting(TypedDict):
        when: datetime
        where: bytes
        why: NotRequired[str]


    meeting_adapter = TypeAdapter(Meeting)
    m = meeting_adapter.validate_python(  # (1)!
        {'when': '2020-01-01T12:00', 'where': 'home'}
    )
    print(m)
    #> {'when': datetime.datetime(2020, 1, 1, 12, 0), 'where': b'home'}
    meeting_adapter.dump_python(m, exclude={'where'})  # (2)!

    print(meeting_adapter.json_schema())  # (3)!
    """
    {
        'properties': {
            'when': {'format': 'date-time', 'title': 'When', 'type': 'string'},
            'where': {'format': 'binary', 'title': 'Where', 'type': 'string'},
            'why': {'title': 'Why', 'type': 'string'},
        },
        'required': ['when', 'where'],
        'title': 'Meeting',
        'type': 'object',
    }
    """
    ```

    <!--
    1. `TypeAdapter` for a `TypedDict` performing validation, it can also validate JSON data directly with `validate_json`
    2. `dump_python` to serialise a `TypedDict` to a python object, it can also serialise to JSON with `dump_json`
    3. `TypeAdapter` can also generate JSON Schema
    -->
    1. `TypeAdapter`は`TypedDict`が検証を行うためのもので、`validate_json`を使ってJSONデータを直接検証することもできます。
    2. `dump_python`は`TypedDict`をpythonオブジェクトにシリアライズしますが、`dump_json`でJSONにシリアライズすることもできます。
    3. `TypeAdapter`はJSONスキーマも生成できます。

## Customisation

<!-- Functional validators and serializers, as well as a powerful protocol for custom types, means the way Pydantic operates can be customized on a per-field or per-type basis. -->
関数型バリデーターとシリアライザ、そしてカスタム型用の強力なプロトコルは、Pydanticの動作方法をフィールド単位または型単位でカスタマイズできます。

??? example "Customisation Example - wrap validators"
    "wrap validators" are new in Pydantic V2 and are one of the most powerful ways to customize Pydantic validation.
    ```py
    from datetime import datetime, timezone

    from pydantic import BaseModel, field_validator


    class Meeting(BaseModel):
        when: datetime

        @field_validator('when', mode='wrap')
        def when_now(cls, input_value, handler):
            if input_value == 'now':
                return datetime.now()
            when = handler(input_value)
            # in this specific application we know tz naive datetimes are in UTC
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            return when


    print(Meeting(when='2020-01-01T12:00+01:00'))
    #> when=datetime.datetime(2020, 1, 1, 12, 0, tzinfo=TzInfo(+01:00))
    print(Meeting(when='now'))
    #> when=datetime.datetime(2032, 1, 2, 3, 4, 5, 6)
    print(Meeting(when='2020-01-01T12:00'))
    #> when=datetime.datetime(2020, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    ```

!!! tip "さらなる学習"
    <!-- See the documentation on [validators](concepts/validators.md), [custom serializers](concepts/serialization.md#custom-serializers), and [custom types](concepts/types.md#custom-types). -->
    [validators](concepts/validators.md), [custom serializers](concepts/serialization.md#custom-serializers), and [custom types](concepts/types.md#custom-types)を参照ください。

## Ecosystem

<!-- At the time of writing there are 214,100 repositories on GitHub and 8,119 packages on PyPI that depend on Pydantic. -->
この記事の執筆時点で、GitHubには214,100のリポジトリがあり、PyPIにはPydanticに依存する8,119のパッケージがあります。

<!-- Some notable libraries that depend on Pydantic: -->
Pydanticに依存している注目すべきライブラリをいくつか紹介します。

!!! warning "私家版訳注"

    以下は、翻訳時点のものです。(2024/07)

{{ libraries }}

<!-- More libraries using Pydantic can be found at [`Kludex/awesome-pydantic`](https://github.com/Kludex/awesome-pydantic). -->
Pydanticを使用している他のライブラリは、[`Kludex/awesome-pydantic`](https://github.com/Kludex/awesome-pydantic)にあります。

{% raw %}
<!-- ## Organisations using Pydantic {#using-pydantic} -->
## Pydanticを使用している組織 {#using-pydantic}

<!-- Some notable companies and organisations using Pydantic together with comments on why/how we know they're using Pydantic. -->
Pydanticを使用しているいくつかの有名な企業や組織と、彼らがPydanticを使用していることを私たちが知っている理由/方法についてコメントします。

<!-- The organisations below are included because they match one or more of the following criteria: -->
以下の組織は、以下の基準の1つ以上に一致しています。

<!--
* Using pydantic as a dependency in a public repository
* Referring traffic to the pydantic documentation site from an organization-internal domain - specific referrers are not included since they're generally not in the public domain
* Direct communication between the Pydantic team and engineers employed by the organization about usage of Pydantic within the organization
-->
* pydanticをパブリックリポジトリの依存関係として使用していること。
* 組織からpydanticドキュメントサイトへの参照トラフィック-一般的にパブリックドメインではないため、内部のドメイン固有の参照者は含まれません。
* 組織内でのPydanticの使用に関する、Pydanticチームと組織に属するエンジニアとの間で直接的なコミュニケーションを行っていること

We've included some extra detail where appropriate and already in the public domain.
必要に応じて詳細を追加しましたが、すでにパブリック・ドメインになっています。

!!! warning "私家版訳注"

    以下は、翻訳時点のものです。(2024/07)

{{ organisations }}
{% endraw %}
