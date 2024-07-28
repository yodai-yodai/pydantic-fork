# Pydantic

<!--
[![CI](https://img.shields.io/github/actions/workflow/status/pydantic/pydantic/ci.yml?branch=main&logo=github&label=CI)](https://github.com/pydantic/pydantic/actions?query=event%3Apush+branch%3Amain+workflow%3ACI)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/pydantic/pydantic.svg)](https://github.com/pydantic/pydantic/actions?query=event%3Apush+branch%3Amain+workflow%3ACI)<br>
[![pypi](https://img.shields.io/pypi/v/pydantic.svg)](https://pypi.python.org/pypi/pydantic)
[![CondaForge](https://img.shields.io/conda/v/conda-forge/pydantic.svg)](https://anaconda.org/conda-forge/pydantic)
[![downloads](https://static.pepy.tech/badge/pydantic/month)](https://pepy.tech/project/pydantic)<br>
[![license](https://img.shields.io/github/license/pydantic/pydantic.svg)](https://github.com/pydantic/pydantic/blob/main/LICENSE)
-->

<!-- {{ version }}. -->

{% include-markdown "./warning.md" %}

<!-- Pydantic is the most widely used data validation library for Python. -->
Pydanticは、Pythonで最も広く使用されているデータ検証ライブラリです。

<!-- Fast and extensible, Pydantic plays nicely with your linters/IDE/brain. Define how data should be in pure, canonical Python 3.8+; validate it with Pydantic. -->
高速で拡張可能なPydanticは、リンター/IDE/あなたの頭脳とうまく連携します。純粋で標準的なPython 3.8+でのデータのあり方を定義し、Pydanticで検証します。

!!! success "Migrating to Pydantic V2"
    <!-- Using Pydantic V1? See the [Migration Guide](migration.md) for notes on upgrading to Pydantic V2 in your applications! -->
    Pydantic V1の使用?アプリケーションでのPydantic V2へのアップグレードに関する注意事項については、[Migration Guide](migration.md)を参照してください。

```py title="Pydantic Example" requires="3.10"
from datetime import datetime
from typing import Tuple

from pydantic import BaseModel


class Delivery(BaseModel):
    timestamp: datetime
    dimensions: Tuple[int, int]


m = Delivery(timestamp='2020-01-02T03:04:05Z', dimensions=['10', '20'])
print(repr(m.timestamp))
#> datetime.datetime(2020, 1, 2, 3, 4, 5, tzinfo=TzInfo(UTC))
print(m.dimensions)
#> (10, 20)
```

!!! question "Why is Pydantic named the way it is?"

    <!-- The name "Pydantic" is a portmanteau of "Py" and "pedantic." The "Py" part indicates that the library is associated with Python, and
    "pedantic" refers to the library's meticulous approach to data validation and type enforcement. -->
    「Pydantic」という名前は、「Py」と「pedantic」の合成語です。「Py」の部分は、ライブラリがPythonに関連付けられていることを示します。
    「pedantic」とは、データ検証と型強制に対するライブラリの細心の注意を払ったアプローチを指します。

    <!-- Combining these elements, "Pydantic" describes our Python library that provides detail-oriented, rigorous data validation. -->
    これらの要素を組み合わせて、「Pydantic」は、詳細指向で厳密なデータ検証を提供するPythonライブラリを提供している。

    <!-- We’re aware of the irony that Pydantic V1 was not strict in its validation, so if we're being pedantic, "Pydantic" was a misnomer until V2 😉. -->
    私たちは、Pydantic V1がその検証において厳密ではなかったという皮肉を認識しているので、私たちは物知り顔で、「Pydantic」はV2が登場するまでは誤った名称であったと言えたはずです。

<!-- ## Why use Pydantic? -->
## Pydanticを使う理由

<!-- - **Powered by type hints** &mdash; with Pydantic, schema validation and serialization are controlled by type annotations; less to learn, less code to write, and integration with your IDE and static analysis tools. [Learn more…](why.md#type-hints) -->
- **型ヒントを使用** &mdash; Pydanticでは、スキーマの検証とシリアライゼーションは型アノテーションによって制御されます。学習するコードが少なくなり、作成するコードも少なくなり、IDEや静的解析ツールと統合されます。[詳細はこちら](why.md#type-hints)
<!-- - **Speed** &mdash; Pydantic's core validation logic is written in Rust. As a result, Pydantic is among the fastest data validation libraries for Python. [Learn more…](why.md#performance) -->
- **スピード** &mdash; Pydanticのコア検証ロジックはRustで記述されています。その結果、PydanticはPython用の最速のデータ検証ライブラリの1つになっています。[詳細はこちら](why.md#performance)
<!-- - **JSON Schema** &mdash; Pydantic models can emit JSON Schema, allowing for easy integration with other tools. [Learn more…](why.md#json-schema) -->
- **JSONスキーマ** &mdash; PydanticモデルはJSONスキーマを生成できるため、他のツールと簡単に統合できます。[詳細はこちら](why.md#json-schema)
<!-- - **Strict** and **Lax** mode &mdash; Pydantic can run in either `strict=True` mode (where data is not converted) or `strict=False` mode where Pydantic tries to coerce data to the correct type where appropriate. [Learn more…](why.md#strict-lax) -->
- **Strict**と**Lax**モード &mdash; Pydanticは、`strict=True`モード(データが変換されない)または`strict=False`モード(Pydanticがデータを適切な型に強制的に変換しようとする)のいずれかで実行できます。[詳細はこちら](why.md#strict-lax)
<!-- - **Dataclasses**, **TypedDicts** and more &mdash; Pydantic supports validation of many standard library types including `dataclass` and `TypedDict`. [Learn more…](why.md#typeddict) -->
- **Dataclasses**,**TypedDitcs**など &mdash; Pydanticは`dataclass`や`TypedDict`を含む多くの標準ライブラリ型の検証をサポートしています。[詳細はこちら](why.md#typedict)
<!-- - **Customisation** &mdash; Pydantic allows custom validators and serializers to alter how data is processed in many powerful ways. [Learn more…](why.md#customisation) -->
- **カスタマイズ** &mdash; Pydanticを使用すると、カスタムバリデータとシリアライザを使用して、さまざまな強力な方法でデータの処理方法を変更できます。[詳細はこちら](why.md#customisation)
<!-- - **Ecosystem** &mdash; around 8,000 packages on PyPI use Pydantic, including massively popular libraries like
  _FastAPI_, _huggingface_, _Django Ninja_, _SQLModel_, & _LangChain_. [Learn more…](why.md#ecosystem) -->
- **Ecosystem** &mdash; PyPI上の約8,000のパッケージがPydanticを使用しており、その中には以下のような非常に人気のあるライブラリが含まれています。
_FastAPI_,_hugggingface_,_Django Ninja_,_SQLModel_,_LangChain_.[詳細はこちら](why.md#ecosystem)
<!-- - **Battle tested** &mdash; Pydantic is downloaded over 70M times/month and is used by all FAANG companies and 20 of the 25 largest companies on NASDAQ. If you're trying to do something with Pydantic, someone else has probably already done it. [Learn more…](why.md#using-pydantic) -->
- **実戦テスト済み** &mdash; Pydanticは7,000万回/月以上ダウンロードされ、すべてのFAANG企業とNASDAQの上位25社のうち20社で使用されています。Pydanticで何かをしようとしているのであれば、おそらく他の誰かがすでにそれをしています。
[Learn more…](why.md#using-pydantic)

[Installing Pydantic](install.md) is as simple as: `pip install pydantic`
[Installing Pydantic](install.md)とてもシンプルです: `pip install pydantic`


<!-- ## Pydantic examples -->
## Pydanticの例

<!-- To see Pydantic at work, let's start with a simple example, creating a custom class that inherits from `BaseModel`: -->
Pydanticの動作を確認するために、`BaseModel`から継承するカスタムクラスを作成する簡単な例から始めましょう。

```py upgrade="skip" title="Validation Successful" requires="3.10"
from datetime import datetime

from pydantic import BaseModel, PositiveInt


class User(BaseModel):
    id: int  # (1)!
    name: str = 'John Doe'  # (2)!
    signup_ts: datetime | None  # (3)!
    tastes: dict[str, PositiveInt]  # (4)!


external_data = {
    'id': 123,
    'signup_ts': '2019-06-01 12:22',  # (5)!
    'tastes': {
        'wine': 9,
        b'cheese': 7,  # (6)!
        'cabbage': '1',  # (7)!
    },
}

user = User(**external_data)  # (8)!

print(user.id)  # (9)!
#> 123
print(user.model_dump())  # (10)!
"""
{
    'id': 123,
    'name': 'John Doe',
    'signup_ts': datetime.datetime(2019, 6, 1, 12, 22),
    'tastes': {'wine': 9, 'cheese': 7, 'cabbage': 1},
}
"""
```

<!-- 1. `id` is of type `int`; the annotation-only declaration tells Pydantic that this field is required. Strings, bytes, or floats will be coerced to ints if possible; otherwise an exception will be raised. -->
1. `id`は`int`型です。注釈のみの宣言は、このフィールドが必須であることをPydanticに伝えます。文字列、バイト、または浮動小数点は、可能であればintに強制されます。そうでない場合は例外が発生します。
<!-- 2. `name` is a string; because it has a default, it is not required. -->
2. `name`は文字列です。デフォルトがあるので、必須ではありません。
<!-- 3. `signup_ts` is a `datetime` field that is required, but the value `None` may be provided; -->
3. `signup_ts`は`datetime`フィールドで必須ですが、値`None`を指定することもできます。
PydanticはUNIXのタイムスタンプint(例えば`1496498400`)か、日付と時刻を表す文字列を処理します。
  <!-- Pydantic will process either a unix timestamp int (e.g. `1496498400`) or a string representing the date and time. -->
  PydanticはUNIXのタイムスタンプint(例えば`1496498400`)か、日付と時刻を表す文字列を処理します。
<!-- 4. `tastes` is a dictionary with string keys and positive integer values. The `PositiveInt` type is shorthand for `Annotated[int, annotated_types.Gt(0)]`. -->
4. `taste`は文字列キーと正の整数値を持つ辞書です。`PositiveInt`型は`Annotated[int, annotated_types.Gt(0)]`の省略形です。
<!-- 5. The input here is an ISO8601 formatted datetime, Pydantic will convert it to a `datetime` object. -->
5. ここでの入力はISO8601フォーマットのdatetimeで、Pydanticはこれを`datetime`オブジェクトに変換します。
<!-- 6. The key here is `bytes`, but Pydantic will take care of coercing it to a string. -->
6. ここで重要なのは`bytes`ですが、Pydanticはこれを文字列に強制的に変換します。
<!-- 7. Similarly, Pydantic will coerce the string `'1'` to an integer `1`. -->
7. 同様に、Pydanticは文字列「1」を整数「1」に強制的に変換します。
<!-- 8. Here we create instance of `User` by passing our external data to `User` as keyword arguments -->
8. ここでは、外部データをキーワード引数として`User`に渡すことによって`User`のインスタンスを作成します。
<!-- 9. We can access fields as attributes of the model -->
9. モデルの属性としてフィールドにアクセスできます。
<!-- 10. We can convert the model to a dictionary with `model_dump()` -->
10. モデルを辞書に変換するには`model_dump()`を使用します。

<!-- If validation fails, Pydantic will raise an error with a breakdown of what was wrong: -->
検証が失敗した場合、Pydanticは何が間違っていたかの詳細を示すエラーを発生させます:

```py upgrade="skip" title="Validation Error" test="skip" lint="skip"
# continuing the above example...

from pydantic import ValidationError


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: datetime | None
    tastes: dict[str, PositiveInt]


external_data = {'id': 'not an int', 'tastes': {}}  # (1)!

try:
    User(**external_data)  # (2)!
except ValidationError as e:
    print(e.errors())
    """
    [
        {
            'type': 'int_parsing',
            'loc': ('id',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not an int',
            'url': 'https://errors.pydantic.dev/2/v/int_parsing',
        },
        {
            'type': 'missing',
            'loc': ('signup_ts',),
            'msg': 'Field required',
            'input': {'id': 'not an int', 'tastes': {}},
            'url': 'https://errors.pydantic.dev/2/v/missing',
        },
    ]
    """
```

<!-- 1. The input data is wrong here &mdash; `id` is not a valid integer, and `signup_ts` is missing -->
1. 入力データが間違っています&mdash;`id`は有効な整数ではなく、`signup_ts`がありません。
<!-- 2. `User(...)` will raise a `ValidationError` with a list of errors -->
2. `User(...)`はエラーのリストと共に`ValidationError`を発生させます。

<!-- ## Who is using Pydantic? -->
## Pydanticユーザ

<!-- Hundreds of organisations and packages are using Pydantic. Some of the prominent companies and organizations around the world who are using Pydantic include: -->
何百もの組織やパッケージがPydanticを使用しています。こちらがPydanticを使用している世界中の著名な企業や組織です。

!!! warning "私家版訳注"

    以下は、翻訳時点のものです。(2024/07)

{{ organisations }}

<!-- For a more comprehensive list of open-source projects using Pydantic see the [list of dependents on github](https://github.com/pydantic/pydantic/network/dependents), or you can find some awesome projects using Pydantic in [awesome-pydantic](https://github.com/Kludex/awesome-pydantic).
-->
Pydanticを使用したオープンソースプロジェクトのより包括的なリストについては
[list of dependents on github](https://github.com/pydantic/pydantic/network/dependents)、または[awesome-pydantic](https://github.com/Kludex/awesome-pydantic)でPydanticを使用している素晴らしいプロジェクトを見つけることができます。
