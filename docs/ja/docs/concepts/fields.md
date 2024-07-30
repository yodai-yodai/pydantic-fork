{% include-markdown "../warning.md" %}

??? api "API Documentation"
    [`pydantic.fields.Field`][pydantic.fields.Field]<br>

<!-- The [`Field`][pydantic.fields.Field] function is used to customize and add metadata to fields of models. -->
[`Field`][pydantic.fields.Field]関数は、モデルのフィールドをカスタマイズし、メタデータを追加するために使用されます。

## Default values

<!-- The `default` parameter is used to define a default value for a field. -->
`default`パラメータは、フィールドのデフォルト値を定義するために使用されます。

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(default='John Doe')


user = User()
print(user)
#> name='John Doe'
```

<!-- You can also use `default_factory` to define a callable that will be called to generate a default value. -->
`default_factory`を使用して、デフォルト値を生成するために呼び出される呼び出し可能オブジェクトを定義することもできます。

```py
from uuid import uuid4

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
```

!!! info
    <!-- The `default` and `default_factory` parameters are mutually exclusive. -->
    `default`パラメータと`default_factory`パラメータは互いに排他的です。

!!! note
    <!-- If you use `typing.Optional`, it doesn't mean that the field has a default value of `None`! -->
    `typing.Optional`を使用しても、フィールドのデフォルト値が`None`になるわけではありません。

## Using `Annotated`

<!-- The [`Field`][pydantic.fields.Field] function can also be used together with [`Annotated`][annotated]. -->
[`Field`][pydantic.fields.Field]関数は、[`Annotated`][annotated]と一緒に使用することもできます。

```py
from uuid import uuid4

from typing_extensions import Annotated

from pydantic import BaseModel, Field


class User(BaseModel):
    id: Annotated[str, Field(default_factory=lambda: uuid4().hex)]
```

!!! note
    <!-- Defaults can be set outside [`Annotated`][annotated] as the assigned value or with `Field.default_factory` inside [`Annotated`][annotated]. The `Field.default` argument is not supported inside [`Annotated`][annotated]. -->
    デフォルトは、割り当てられた値として[`Annotated`][annotated]の外に設定するか、[`Annotated`][annotated]内の`Field.default_factory`で設定できます。`Field.default`引数は[`Annotated`][annotated]内ではサポートされていません。

## Field aliases

<!-- For validation and serialization, you can define an alias for a field. -->
検証とシリアライゼーションのために、フィールドのエイリアスを定義できます。

<!-- There are three ways to define an alias: -->
エイリアスを定義するには、次の3つの方法があります。

* `Field(..., alias='foo')`
* `Field(..., validation_alias='foo')`
* `Field(..., serialization_alias='foo')`

<!-- The `alias` parameter is used for both validation _and_ serialization. If you want to use _different_ aliases for validation and serialization respectively, you can use the`validation_alias` and `serialization_alias` parameters, which will apply only in their respective use cases. -->
`alias`パラメータは、validation_と_serializationの両方に使用されます。検証とシリアライゼーションにそれぞれ_different_aliasesを使用する場合は、それぞれのユースケースにのみ適用される`validation_alias`パラメータと`serialization_alias`パラメータを使用できます。

<!-- Here is an example of using the `alias` parameter: -->
以下に`alias`パラメータの使用例を示します。

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(..., alias='username')


user = User(username='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'username': 'johndoe'}
```

<!-- 1. The alias `'username'` is used for instance creation and validation. -->
1. エイリアス「username」`は、インスタンスの作成と検証に使用されます。
<!-- 2. We are using `model_dump` to convert the model into a serializable format. -->
2. モデルをシリアライズ可能なフォーマットに変換するために`model_dump`を使用しています。

    <!-- You can see more details about [`model_dump`][pydantic.main.BaseModel.model_dump] in the API reference. -->
    [`model_dump`][pydantic.main.BaseModel.model_dump]の詳細については、APIリファレンスを参照してください。

    <!-- Note that the `by_alias` keyword argument defaults to `False`, and must be specified explicitly to dump  models using the field (serialization) aliases. -->
    `by_alias`キーワード引数のデフォルトは`False`であり、フィールド(シリアライゼーション)エイリアスを使用してモデルをダンプするには明示的に指定する必要があることに注意してください。

    <!-- When `by_alias=True`, the alias `'username'` is also used during serialization. -->
    `by_alias=True`の場合、シリアル化の際にエイリアス`'username'`も使用されます。

<!-- If you want to use an alias _only_ for validation, you can use the `validation_alias` parameter: -->
検証にalias_only_を使用する場合は、`validation_alias`パラメータを使用します。

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(..., validation_alias='username')


user = User(username='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'name': 'johndoe'}
```

<!-- 1. The validation alias `'username'` is used during validation. -->
1. 検証エイリアス`'username'`は、検証中に使用されます。
<!-- 2. The field name `'name'` is used during serialization. -->
2. フィールド名`'name'`はシリアル化の際に使用されます。

<!-- If you only want to define an alias for _serialization_, you can use the `serialization_alias` parameter: -->
_serialization_のエイリアスのみを定義する場合は、`serialization_alias`パラメータを使用できます。

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(..., serialization_alias='username')


user = User(name='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'username': 'johndoe'}
```

1. The field name `'name'` is used for validation.
<!-- 1. フィールド名「name」は検証に使用されます。 -->
<!-- 2. The serialization alias `'username'` is used for serialization. -->
2. シリアル化には、シリアル化エイリアス`'username'`が使用されます。



<!-- !!! note "Alias precedence and priority" -->
!!! note "エイリアスの優先順位"

    <!-- In case you use `alias` together with `validation_alias` or `serialization_alias` at the same time, the `validation_alias` will have priority over `alias` for validation, and `serialization_alias` will have priority over `alias` for serialization. -->
    `alias`を`validation_alias`または`serialization_alias`と同時に使用した場合、検証では`validation_alias`が`alias`より優先され、シリアライズでは`serialization_alias`が`alias`より優先されます。

    <!-- If you use an `alias_generator` in the [Model Config][pydantic.config.ConfigDict.alias_generator], you can control     the order of precedence for specified field vs generated aliases via the `alias_priority` setting. You can read more about alias precedence [here](../concepts/alias.md#alias-precedence). -->
    [Model Config][pydantic.config.ConfigDict.alias_generator]で`alias_generator`を使用する場合、`alias_priority`設定を使用して、指定されたフィールドと生成されたエイリアスの優先順位を制御できます。エイリアスの優先順位の詳細については、[ここ](../concepts/alias.md#alias-precedence)を参照してください。

<!-- ??? tip "VSCode and Pyright users" -->
??? tip "VSCodeとPyrightのユーザ"

    <!-- In VSCode, if you use the [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) extension, you won't see a warning when instantiating a model using a field's alias: -->
    VSCodeでは、[Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.VSCode-pylance)拡張を使用すると、フィールドのエイリアスを使用してモデルをインスタンス化するときに警告が表示されません。

    ```py
    from pydantic import BaseModel, Field


    class User(BaseModel):
        name: str = Field(..., alias='username')


    user = User(username='johndoe')  # (1)!
    ```

    <!-- 1. VSCode will NOT show a warning here. -->
    1. VSCodeはここでは警告を表示しません。

    <!-- When the `'alias'` keyword argument is specified, even if you set `populate_by_name` to `True` in the [Model Config][pydantic.config.ConfigDict.populate_by_name], VSCode will show a warning when instantiating a model using the field name (though it will work at runtime) — in this case, `'name'`: -->
    `'alias'`キーワード引数が指定されている場合、[Model Config][pydantic.config.ConfigDict.populate_by_name]で`populate_by_name`を`True`に設定しても、VSCodeはフィールド名を使用してモデルをインスタンス化するときに警告を表示します(ただし、実行時には機能します)。この場合は`'name'`:

    ```py
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        name: str = Field(..., alias='username')


    user = User(name='johndoe')  # (1)!
    ```

    <!-- 1. VSCode will show a warning here. -->
    1. VSCodeはここに警告を表示します。

    <!-- To "trick" VSCode into preferring the field name, you can use the `str` function to wrap the alias value. -->
    VSCodeを「だまして」フィールド名を優先させるには、`str`関数を使用してエイリアス値をラップします。
    <!-- With this approach, though, a warning is shown when instantiating a model using the alias for the field: -->
    ただし、この方法では、フィールドのエイリアスを使用してモデルをインスタンス化するときに警告が表示されます。

    ```py
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        name: str = Field(..., alias=str('username'))  # noqa: UP018


    user = User(name='johndoe')  # (1)!
    user = User(username='johndoe')  # (2)!
    ```

    <!-- 1. Now VSCode will NOT show a warning -->
    1. VSCodeは警告を表示しません。
    <!-- 2. VSCode will show a warning here, though -->
    2. VSCodeはここで警告を表示します。

    <!-- This is discussed in more detail in [this issue](https://github.com/pydantic/pydantic/issues/5893). -->
    この問題については、[ここ](https://github.com/pydantic/pydantic/issues/5893)でより詳細に議論されています。

    ### Validation Alias

    <!-- Even though Pydantic treats `alias` and `validation_alias` the same when creating model instances, VSCode will not use the `validation_alias` in the class initializer signature. If you want VSCode to use the `validation_alias` in the class initializer, you can instead specify both an `alias` and `serialization_alias`, as the `serialization_alias` will override the `alias` during serialization: -->
    Pydanticはモデルインスタンスを作成するときに`alias`と`validation_alias`を同じように扱いますが、VSCodeはクラスイニシャライザシグネチャで`validation_alias`を使用しません。VSCodeがクラスイニシャライザで`validation_alias`を使用するようにしたい場合は、代わりに`alias`と`serialization_alias`の両方を指定できます。これは、`serialization_alias`がシリアライゼーション中に`alias`をオーバーライドするためです。

    ```py
    from pydantic import BaseModel, Field


    class MyModel(BaseModel):
        my_field: int = Field(..., validation_alias='myValidationAlias')
    ```
    <!-- with: -->
    ここで:
    ```py
    from pydantic import BaseModel, Field


    class MyModel(BaseModel):
        my_field: int = Field(
            ...,
            alias='myValidationAlias',
            serialization_alias='my_serialization_alias',
        )


    m = MyModel(myValidationAlias=1)
    print(m.model_dump(by_alias=True))
    #> {'my_serialization_alias': 1}
    ```

    <!-- All of the above will likely also apply to other tools that respect the [`@typing.dataclass_transform`](https://docs.python.org/3/library/typing.html#typing.dataclass_transform)decorator, such as Pyright. -->
    上記のすべては、Pyrightなど、[`@typing.dataclass_transform`](https://docs.python.org/3/library/typing.html#typing.dataclass_transform)デコレータを尊重する他のツールにも適用される可能性があります。

<!-- For more information on alias usage, see the [Alias] concepts page. -->
エイリアスの使用方法の詳細については、[Alias]conceptsページを参照してください。

## Numeric Constraints

<!-- There are some keyword arguments that can be used to constrain numeric values: -->
数値の制約に使用できるキーワード引数がいくつかあります。



<!-- * `gt` - greater than
* `lt` - less than
* `ge` - greater than or equal to
* `le` - less than or equal to
* `multiple_of` - a multiple of the given number
* `allow_inf_nan` - allow `'inf'`, `'-inf'`, `'nan'` values -->
* `gt` - より大きい
* `lt` - より小さい
* `ge` - より大きいか等しい
* `le` - より小さいか等しい
* `multiple_of` - 与えられた数の倍数
* `allow_inf_nan` - `'inf'`、`'-inf'`、`'nan'`の値を許可します。

<!-- Here's an example: -->
次に例を示します。

```py
from pydantic import BaseModel, Field


class Foo(BaseModel):
    positive: int = Field(gt=0)
    non_negative: int = Field(ge=0)
    negative: int = Field(lt=0)
    non_positive: int = Field(le=0)
    even: int = Field(multiple_of=2)
    love_for_pydantic: float = Field(allow_inf_nan=True)


foo = Foo(
    positive=1,
    non_negative=0,
    negative=-1,
    non_positive=0,
    even=2,
    love_for_pydantic=float('inf'),
)
print(foo)
"""
positive=1 non_negative=0 negative=-1 non_positive=0 even=2 love_for_pydantic=inf
"""
```

??? info "JSON Schema"
    <!-- In the generated JSON schema: -->
    生成されたJSONスキーマでは、次のようになります。

    <!-- - `gt` and `lt` constraints will be translated to `exclusiveMinimum` and `exclusiveMaximum`.
    - `ge` and `le` constraints will be translated to `minimum` and `maximum`.
    - `multiple_of` constraint will be translated to `multipleOf`. -->
    - `gt`と`lt`の制約は`exclusiveMinimum`と`exclusiveMaximum`に変換されます。
    - `ge`と`le`の制約は`minimum`と`maximum`に変換されます。
    - `multiple_of`制約は`multipleOf`に変換されます。

    <!-- The above snippet will generate the following JSON Schema: -->
    上記のスニペットは、次のJSONスキーマを生成します。

    ```json
    {
      "title": "Foo",
      "type": "object",
      "properties": {
        "positive": {
          "title": "Positive",
          "type": "integer",
          "exclusiveMinimum": 0
        },
        "non_negative": {
          "title": "Non Negative",
          "type": "integer",
          "minimum": 0
        },
        "negative": {
          "title": "Negative",
          "type": "integer",
          "exclusiveMaximum": 0
        },
        "non_positive": {
          "title": "Non Positive",
          "type": "integer",
          "maximum": 0
        },
        "even": {
          "title": "Even",
          "type": "integer",
          "multipleOf": 2
        },
        "love_for_pydantic": {
          "title": "Love For Pydantic",
          "type": "number"
        }
      },
      "required": [
        "positive",
        "non_negative",
        "negative",
        "non_positive",
        "even",
        "love_for_pydantic"
      ]
    }
    ```

    <!-- See the [JSON Schema Draft 2020-12] for more details. -->
    詳細については、[JSON Schema Draft 2020-12]を参照してください。

!!! warning "Constraints on compound types"

    <!-- In case you use field constraints with compound types, an error can happen in some cases. To avoid potential issues, you can use `Annotated`: -->
    複合型でフィールド制約を使用すると、場合によってはエラーが発生することがあります。潜在的な問題を避けるために、`Annotated`を使用することができます。

    ```py
    from typing import Optional

    from typing_extensions import Annotated

    from pydantic import BaseModel, Field


    class Foo(BaseModel):
        positive: Optional[Annotated[int, Field(gt=0)]]
        # Can error in some cases, not recommended:
        non_negative: Optional[int] = Field(ge=0)
    ```

## String Constraints

??? api "API Documentation"
    [`pydantic.types.StringConstraints`][pydantic.types.StringConstraints]<br>

<!-- There are fields that can be used to constrain strings: -->
文字列の制約に使用できるフィールドは次のとおりです。

<!-- * `min_length`: Minimum length of the string.
* `max_length`: Maximum length of the string.
* `pattern`: A regular expression that the string must match. -->
* `min_length`: 文字列の最小の長さ。
* `max_length`: 文字列の最大長。
* `pattern`: 文字列が一致しなければならない正規表現。

<!-- Here's an example: -->
次に例を示します。

```py
from pydantic import BaseModel, Field


class Foo(BaseModel):
    short: str = Field(min_length=3)
    long: str = Field(max_length=10)
    regex: str = Field(pattern=r'^\d*$')  # (1)!


foo = Foo(short='foo', long='foobarbaz', regex='123')
print(foo)
#> short='foo' long='foobarbaz' regex='123'
```

<!-- 1. Only digits are allowed. -->
1. 数字のみを使用できます。

??? info "JSON Schema"
    <!-- In the generated JSON schema: -->
    生成されたJSONスキーマでは、次のようになります。

    <!--
    - `min_length` constraint will be translated to `minLength`.
    - `max_length` constraint will be translated to `maxLength`.
    - `pattern` constraint will be translated to `pattern`.
    -->
    - `min_length`制約は`minLength`に変換されます。
    - `max_length`制約は`maxLength`に変換されます。
    - `pattern`制約は`pattern`に変換されます。

    <!-- The above snippet will generate the following JSON Schema: -->
    上記のスニペットは、次のJSONスキーマを生成します。

    ```json
    {
      "title": "Foo",
      "type": "object",
      "properties": {
        "short": {
          "title": "Short",
          "type": "string",
          "minLength": 3
        },
        "long": {
          "title": "Long",
          "type": "string",
          "maxLength": 10
        },
        "regex": {
          "title": "Regex",
          "type": "string",
          "pattern": "^\\d*$"
        }
      },
      "required": [
        "short",
        "long",
        "regex"
      ]
    }
    ```

## Decimal Constraints

There are fields that can be used to constrain decimals:
小数点以下の桁数を制限するために使用できるフィールドがあります。

<!--
* `max_digits`: Maximum number of digits within the `Decimal`. It does not include a zero before the decimal point or trailing decimal zeroes.
* `decimal_places`: Maximum number of decimal places allowed. It does not include trailing decimal zeroes.
-->
* `max_digits`: `Decimal`内の最大桁数。小数点の前のゼロや小数点以下のゼロは含まれません。
* `decimal_places`: 小数点以下の最大桁数です。小数点以下のゼロは含まれません。

<!-- Here's an example: -->
次に例を示します。

```py
from decimal import Decimal

from pydantic import BaseModel, Field


class Foo(BaseModel):
    precise: Decimal = Field(max_digits=5, decimal_places=2)


foo = Foo(precise=Decimal('123.45'))
print(foo)
#> precise=Decimal('123.45')
```

## Dataclass Constraints

<!-- There are fields that can be used to constrain dataclasses: -->
データクラスの制約に使用できるフィールドは次のとおりです。

<!--
* `init`: Whether the field should be included in the `__init__` of the dataclass.
* `init_var`: Whether the field should be seen as an [init-only field] in the dataclass.
* `kw_only`: Whether the field should be a keyword-only argument in the constructor of the dataclass.
 -->
* `init`: フィールドをデータクラスの`__init__`に含めるかどうか。
* `init_var`: そのフィールドをデータクラスの[init-onlyフィールド]として見るかどうか。
* `kw_only`: フィールドがデータクラスのコンストラクタでキーワードのみの引数であるべきかどうか。

<!-- Here's an example: -->
次に例を示します。

```py
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass


@dataclass
class Foo:
    bar: str
    baz: str = Field(init_var=True)
    qux: str = Field(kw_only=True)


class Model(BaseModel):
    foo: Foo


model = Model(foo=Foo('bar', baz='baz', qux='qux'))
print(model.model_dump())  # (1)!
#> {'foo': {'bar': 'bar', 'qux': 'qux'}}
```

<!-- 1. The `baz` field is not included in the `model_dump()` output, since it is an init-only field. -->
1. `baz`フィールドはinit-onlyフィールドなので、`model_dump()`の出力には含まれません。

## Validate Default Values

<!-- The parameter `validate_default` can be used to control whether the default value of the field should be validated. -->
パラメータ`validate_default`を使用して、フィールドのデフォルト値を検証するかどうかを制御できます。

<!-- By default, the default value of the field is not validated. -->
デフォルトでは、フィールドのデフォルト値は検証されません。

```py
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    age: int = Field(default='twelve', validate_default=True)


try:
    user = User()
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    age
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='twelve', input_type=str]
    """
```

## Field Representation

<!-- The parameter `repr` can be used to control whether the field should be included in the string representation of the model. -->
パラメータ`repr`を使用して、フィールドをモデルの文字列表現に含めるかどうかを制御できます。

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(repr=True)  # (1)!
    age: int = Field(repr=False)


user = User(name='John', age=42)
print(user)
#> name='John'
```

<!-- 1. This is the default value. -->
1. これがデフォルト値です。

## Discriminator

<!-- The parameter `discriminator` can be used to control the field that will be used to discriminate between different models in a union. It takes either the name of a field or a `Discriminator` instance. The `Discriminator` approach can be useful when the discriminator fields aren't the same for all the models in the `Union`. -->
パラメータ`discriminator`を使用して、共用体の異なるモデルを区別するために使用されるフィールドを制御できます。これは、フィールドの名前または`Discriminator`インスタンスのいずれかを取ります。`Discriminator`アプローチは、`Union`内のすべてのモデルに対して識別子フィールドが同じでない場合に便利です。

<!-- The following example shows how to use `discriminator` with a field name: -->
次の例は、フィールド名と共に`discriminator`を使用する方法を示しています。

```py requires="3.8"
from typing import Literal, Union

from pydantic import BaseModel, Field


class Cat(BaseModel):
    pet_type: Literal['cat']
    age: int


class Dog(BaseModel):
    pet_type: Literal['dog']
    age: int


class Model(BaseModel):
    pet: Union[Cat, Dog] = Field(discriminator='pet_type')


print(Model.model_validate({'pet': {'pet_type': 'cat', 'age': 12}}))  # (1)!
#> pet=Cat(pet_type='cat', age=12)
```

<!-- 1. See more about [Helper Functions] in the [Models] page. -->
1. [Helper Functions]の詳細については、[Models]ページを参照してください。

<!-- The following example shows how to use the `discriminator` keyword argument with a `Discriminator` instance: -->
次の例は、`Discriminator`インスタンスで`discriminator`キーワード引数を使用する方法を示しています。

```py requires="3.8"
from typing import Literal, Union

from typing_extensions import Annotated

from pydantic import BaseModel, Discriminator, Field, Tag


class Cat(BaseModel):
    pet_type: Literal['cat']
    age: int


class Dog(BaseModel):
    pet_kind: Literal['dog']
    age: int


def pet_discriminator(v):
    if isinstance(v, dict):
        return v.get('pet_type', v.get('pet_kind'))
    return getattr(v, 'pet_type', getattr(v, 'pet_kind', None))


class Model(BaseModel):
    pet: Union[Annotated[Cat, Tag('cat')], Annotated[Dog, Tag('dog')]] = Field(
        discriminator=Discriminator(pet_discriminator)
    )


print(repr(Model.model_validate({'pet': {'pet_type': 'cat', 'age': 12}})))
#> Model(pet=Cat(pet_type='cat', age=12))

print(repr(Model.model_validate({'pet': {'pet_kind': 'dog', 'age': 12}})))
#> Model(pet=Dog(pet_kind='dog', age=12))
```

<!-- You can also take advantage of `Annotated` to define your discriminated unions.
See the [Discriminated Unions] docs for more details. -->
`Annotated`を利用して、区別された共用体を定義することもできます。
詳細については、[Discriminated Unions]ドキュメントを参照してください。

## Strict Mode

<!-- The `strict` parameter on a [`Field`][pydantic.fields.Field] specifies whether the field should be validated in "strict mode".
In strict mode, Pydantic throws an error during validation instead of coercing data on the field where `strict=True`. -->
[`Field`][pydantic.fields.Field]の`strict`パラメータは、そのフィールドを"strictモード"で検証するかどうかを指定します。
strictモードでは、Pydanticは検証中に`strict=True`のフィールドにデータを強制するのではなく、エラーをスローします。

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(strict=True)  # (1)!
    age: int = Field(strict=False)


user = User(name='John', age='42')  # (2)!
print(user)
#> name='John' age=42
```

<!-- 1. This is the default value. -->
1. これがデフォルト値です。
<!-- 2. The `age` field is not validated in the strict mode. Therefore, it can be assigned a string. -->
2. `age`フィールドはstrictモードでは検証されません。したがって、文字列を割り当てることができます。

See [Strict Mode](strict_mode.md) for more details.
詳細については、[Strict Mode](strict_mode.md)を参照してください。

<!-- See [Conversion Table](conversion_table.md) for more details on how Pydantic converts data in both strict and lax modes. -->
Pydanticがstrictモードとlaxモードの両方でデータを変換する方法の詳細については、[Conversion Table](conversion_table.md)を参照してください。

## Immutability

<!-- The parameter `frozen` is used to emulate the frozen dataclass behaviour. It is used to prevent the field from being assigned a new value after the model is created (immutability). -->
パラメータ`frozen`は、凍結されたデータクラスの動作をエミュレートするために使用されます。これは、モデルが作成された後にフィールドに新しい値が割り当てられないようにするために使用されます(不変性)。

<!-- See the [frozen dataclass documentation] for more details. -->
詳細については、[frozen dataclass documentation]を参照してください。

```py
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    name: str = Field(frozen=True)
    age: int


user = User(name='John', age=42)

try:
    user.name = 'Jane'  # (1)!
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      Field is frozen [type=frozen_field, input_value='Jane', input_type=str]
    """
```

<!-- 1. Since `name` field is frozen, the assignment is not allowed. -->
1. `name`フィールドが凍結されているため、割り当ては許可されません。

## Exclude

<!-- The `exclude` parameter can be used to control which fields should be excluded from the model when exporting the model. -->
`exclude`パラメータを使用して、モデルをエクスポートするときにモデルから除外するフィールドを制御できます。

<!-- See the following example: -->
次の例を参照してください。

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str
    age: int = Field(exclude=True)


user = User(name='John', age=42)
print(user.model_dump())  # (1)!
#> {'name': 'John'}
```

<!-- 1. The `age` field is not included in the `model_dump()` output, since it is excluded. See the [Serialization] section for more details. -->
1. `age`フィールドは除外されているので、`model_dump()`の出力には含まれません。詳細については、[Serialization]セクションを参照してください。

## Deprecated fields

<!-- The `deprecated` parameter can be used to mark a field as being deprecated. Doing so will result in: -->
`deprecated`パラメータは、フィールドを非推奨としてマークするために使用できます。これにより、次のような結果になります。

<!--
* a runtime deprecation warning emitted when accessing the field.
* `"deprecated": true` being set in the generated JSON schema.
 -->
* フィールドへのアクセス時に発行される実行時の非推奨警告。
* `"deprecated": true`が生成されたJSONスキーマに設定されます。

<!-- You can set the `deprecated` parameter as one of: -->
`deprecated`パラメータは以下のいずれかに設定できます。

<!--
* A string, which will be used as the deprecation message.
* An instance of the `warnings.deprecated` decorator (or the `typing_extensions` backport).
* A boolean, which will be used to mark the field as deprecated with a default `'deprecated'` deprecation message.
 -->
* 非推奨メッセージとして使用される文字列。
* `warnings.deprecated`デコレータ(または`typing_extensions`バックポート)のインスタンス。
* ブール値。デフォルトの`'deprecated'`非推奨メッセージでフィールドを非推奨としてマークするために使用されます。

### `deprecated` as a string

```py
from typing_extensions import Annotated

from pydantic import BaseModel, Field


class Model(BaseModel):
    deprecated_field: Annotated[int, Field(deprecated='This is deprecated')]


print(Model.model_json_schema()['properties']['deprecated_field'])
#> {'deprecated': True, 'title': 'Deprecated Field', 'type': 'integer'}
```

### `deprecated` via the `warnings.deprecated` decorator

!!! note
    <!-- You can only use the `deprecated` decorator in this way if you have `typing_extensions` >= 4.9.0 installed. -->
    この方法で`deprecated`デコレータを使用できるのは、`typing_extensions`>=4.9.0がインストールされている場合だけです。

```py test="skip"
import importlib.metadata

from packaging.version import Version
from typing_extensions import Annotated, deprecated

from pydantic import BaseModel, Field

if Version(importlib.metadata.version('typing_extensions')) >= Version('4.9'):

    class Model(BaseModel):
        deprecated_field: Annotated[int, deprecated('This is deprecated')]

        # Or explicitly using `Field`:
        alt_form: Annotated[
            int, Field(deprecated=deprecated('This is deprecated'))
        ]
```

### `deprecated` as a boolean

```py
from typing_extensions import Annotated

from pydantic import BaseModel, Field


class Model(BaseModel):
    deprecated_field: Annotated[int, Field(deprecated=True)]


print(Model.model_json_schema()['properties']['deprecated_field'])
#> {'deprecated': True, 'title': 'Deprecated Field', 'type': 'integer'}
```


!!! note "Support for `category` and `stacklevel`"
    <!-- The current implementation of this feature does not take into account the `category` and `stacklevel` arguments to the `deprecated` decorator. This might land in a future version of Pydantic. -->
    この機能の現在の実装では、`deprecated`デコレータの`category`引数と`stacklevel`引数は考慮されていません。これは将来のバージョンのPydanticに導入される可能性があります。

!!! warning "Accessing a deprecated field in validators"
    <!-- When accessing a deprecated field inside a validator, the deprecation warning will be emitted. You can use [`catch_warnings`][warnings.catch_warnings] to explicitly ignore it: -->
    バリデータ内の非推奨フィールドにアクセスすると、非推奨警告が表示されます。[`catch_warnings`][warnings.catch_warnings]を使用して、明示的に無視することができます。

    ```py
    import warnings

    from typing_extensions import Self

    from pydantic import BaseModel, Field, model_validator


    class Model(BaseModel):
        deprecated_field: int = Field(deprecated='This is deprecated')

        @model_validator(mode='after')
        def validate_model(self) -> Self:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', DeprecationWarning)
                self.deprecated_field = self.deprecated_field * 2
    ```

## Customizing JSON Schema

<!-- Some field parameters are used exclusively to customize the generated JSON schema. The parameters in question are: -->
一部のフィールド・パラメータは、生成されたJSONスキーマをカスタマイズするために排他的に使用されます。問題のパラメータは次のとおりです。

* `title`
* `description`
* `examples`
* `json_schema_extra`

<!-- Read more about JSON schema customization / modification with fields in the [Customizing JSON Schema] section of the JSON schema docs. -->
JSON schema docsの[Customizing JSON Schema]セクションに記載されている、フィールドを使用したJSONスキーマのカスタマイズ/変更の詳細を読んでください。

## The `computed_field` decorator

??? api "API Documentation"
    [`pydantic.fields.computed_field`][pydantic.fields.computed_field]<br>

<!-- The `computed_field` decorator can be used to include `property` or `cached_property` attributes when serializing a model or dataclass. This can be useful for fields that are computed from other fields, or for fields that are expensive to computed (and thus, are cached). -->
`computed_field`デコレータは、モデルまたはデータクラスをシリアライズするときに、`property`または`cached_property`属性を含めるために使用できます。これは、他のフィールドから計算されるフィールドや、計算にコストがかかる(したがってキャッシュされる)フィールドに便利です。

<!-- Here's an example: -->
次に例を示します。

```py
from pydantic import BaseModel, computed_field


class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    def volume(self) -> float:
        return self.width * self.height * self.depth


b = Box(width=1, height=2, depth=3)
print(b.model_dump())
#> {'width': 1.0, 'height': 2.0, 'depth': 3.0, 'volume': 6.0}
```

<!-- As with regular fields, computed fields can be marked as being deprecated: -->
通常のフィールドと同様に、計算フィールドは非推奨としてマークできます。

```py
from typing_extensions import deprecated

from pydantic import BaseModel, computed_field


class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    @deprecated("'volume' is deprecated")
    def volume(self) -> float:
        return self.width * self.height * self.depth
```


[JSON Schema Draft 2020-12]: https://json-schema.org/understanding-json-schema/reference/numeric.html#numeric-types
[Discriminated Unions]: ../concepts/unions.md#discriminated-unions
[Helper Functions]: models.md#helper-functions
[Models]: models.md
[init-only field]: https://docs.python.org/3/library/dataclasses.html#init-only-variables
[frozen dataclass documentation]: https://docs.python.org/3/library/dataclasses.html#frozen-instances
[Validate Assignment]: models.md#validate-assignment
[Serialization]: serialization.md#model-and-field-level-include-and-exclude
[Customizing JSON Schema]: json_schema.md#field-level-customization
[annotated]: https://docs.python.org/3/library/typing.html#typing.Annotated
[Alias]: ../concepts/alias.md
