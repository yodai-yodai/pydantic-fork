{% include-markdown "../warning.md" %}

<!-- An alias is an alternative name for a field, used when serializing and deserializing data. -->
エイリアスはフィールドの別名で、データのシリアライズおよびデシリアライズ時に使用されます。

You can specify an alias in the following ways:
エイリアスは次の方法で指定できます。

<!-- * `alias` on the [`Field`][pydantic.fields.Field] -->
* [`Field`][pydantic.fields.Field]の`alias`
    <!-- * must be a `str` -->
    * `str`でなければなりません。
<!-- * `validation_alias` on the [`Field`][pydantic.fields.Field] -->
* [`Field`][pydantic.fields.Field]の*`validation_alias`
    <!-- * can be an instance of `str`, [`AliasPath`][pydantic.aliases.AliasPath], or [`AliasChoices`][pydantic.aliases.AliasChoices] -->
    * `str`のインスタンスで、[`AliasPath`][pydantic.aliases.AliasPath]、または[`AliasChoices`][pydantic.aliases.AliasChoices]となります。
<!-- * `serialization_alias` on the [`Field`][pydantic.fields.Field] -->
* [`Field`][pydantic.fields.Field]の*`serialization_alias`
    <!-- * must be a `str` -->
    * `str`でなければなりません
<!-- * `alias_generator` on the [`Config`][pydantic.config.ConfigDict.alias_generator] -->
* `alias_generator`を[`Config`][pydantic.config.ConfigDict.alias_generator]
    <!-- * can be a callable or an instance of [`AliasGenerator`][pydantic.aliases.AliasGenerator] -->
    * 、[`AliasGenerator`][pydantic.aliases.AliasGenerator]の呼び出し可能オブジェクトまたはインスタンスです。

<!-- For examples of how to use `alias`, `validation_alias`, and `serialization_alias`, see [Field aliases](../concepts/fields.md#field-aliases). -->
`alias`、`validation_alias`、および`serialization_alias`の使用例については、[Field aliases](./concepts/fields.md#field-aliases)を参照してください。

## `AliasPath` and `AliasChoices`

??? api "API Documentation"

    [`pydantic.aliases.AliasPath`][pydantic.aliases.AliasPath]<br>
    [`pydantic.aliases.AliasChoices`][pydantic.aliases.AliasChoices]<br>

<!-- Pydantic provides two special types for convenience when using `validation_alias`: `AliasPath` and `AliasChoices`. -->
Pydanticは`validation_alias`を使用する際の利便性のために、`AliasPath`と`AliasChoices`という2つの特別な型を提供しています。

<!-- The `AliasPath` is used to specify a path to a field using aliases. For example: -->
`AliasPath`は、エイリアスを使用してフィールドへのパスを指定するために使用されます。次に例を示します。

```py lint="skip"
from pydantic import BaseModel, Field, AliasPath


class User(BaseModel):
    first_name: str = Field(validation_alias=AliasPath('names', 0))
    last_name: str = Field(validation_alias=AliasPath('names', 1))

user = User.model_validate({'names': ['John', 'Doe']})  # (1)!
print(user)
#> first_name='John' last_name='Doe'
```

<!-- 1. We are using `model_validate` to validate a dictionary using the field aliases. -->
1. フィールドエイリアスを使用して辞書を検証するために`model_validate`を使用しています。
    <!-- You can see more details about [`model_validate`][pydantic.main.BaseModel.model_validate] in the API reference. -->
    [`model_validate`][pydantic.main.BaseModel.model_validate]の詳細については、APIリファレンスを参照してください。

<!-- In the `'first_name'` field, we are using the alias `'names'` and the index `0` to specify the path to the first name.
In the `'last_name'` field, we are using the alias `'names'` and the index `1` to specify the path to the last name. -->
"first_name"フィールドでは、エイリアス"names"とインデックス"0"を使用して、名へのパスを指定しています。
"last_name"フィールドでは、エイリアス"names"とインデックス"1"を使用して、姓へのパスを指定しています。

<!-- `AliasChoices` is used to specify a choice of aliases. For example: -->
`AliasChoices`は、エイリアスの選択を指定するために使用されます。次に例を示します。

```py lint="skip"
from pydantic import BaseModel, Field, AliasChoices


class User(BaseModel):
    first_name: str = Field(validation_alias=AliasChoices('first_name', 'fname'))
    last_name: str = Field(validation_alias=AliasChoices('last_name', 'lname'))

user = User.model_validate({'fname': 'John', 'lname': 'Doe'})  # (1)!
print(user)
#> first_name='John' last_name='Doe'
user = User.model_validate({'first_name': 'John', 'lname': 'Doe'})  # (2)!
print(user)
#> first_name='John' last_name='Doe'
```

<!-- 1. We are using the second alias choice for both fields. -->
1. 両方のフィールドに2番目のエイリアスを使用しています。
<!-- 2. We are using the first alias choice for the field `'first_name'` and the second alias choice for the field `'last_name'`. -->
2. フィールド`'first_name'`に最初のエイリアス選択を使用し、フィールド`'last_name'`に2番目のエイリアス選択を使用しています。

<!-- You can also use `AliasChoices` with `AliasPath`: -->
`AliasChoices`は`AliasPath`と一緒に使用することもできます。

```py lint="skip"
from pydantic import BaseModel, Field, AliasPath, AliasChoices


class User(BaseModel):
    first_name: str = Field(validation_alias=AliasChoices('first_name', AliasPath('names', 0)))
    last_name: str = Field(validation_alias=AliasChoices('last_name', AliasPath('names', 1)))


user = User.model_validate({'first_name': 'John', 'last_name': 'Doe'})
print(user)
#> first_name='John' last_name='Doe'
user = User.model_validate({'names': ['John', 'Doe']})
print(user)
#> first_name='John' last_name='Doe'
user = User.model_validate({'names': ['John'], 'last_name': 'Doe'})
print(user)
#> first_name='John' last_name='Doe'
```

## Using alias generators

<!-- You can use the `alias_generator` parameter of [`Config`][pydantic.config.ConfigDict.alias_generator] to specify a callable (or group of callables, via `AliasGenerator`) that will generate aliases for all fields in a model.
This is useful if you want to use a consistent naming convention for all fields in a model, but do not want to specify the alias for each field individually. -->
[`Config`][pydantic.config.ConfigDict.alias_generator]の`alias_generator`パラメータを使用して、モデル内のすべてのフィールドのエイリアスを生成する呼び出し可能オブジェクト(または`AliasGenerator`による呼び出し可能オブジェクトのグループ)を指定できます。
これは、モデル内のすべてのフィールドに対して一貫した命名規則を使用し、各フィールドに個別にエイリアスを指定しない場合に便利です。

!!! note
    <!-- Pydantic offers three built-in alias generators that you can use out of the box: -->
    Pydanticには、すぐに使用できる3つの組み込みエイリアスジェネレータが用意されています。

    [`to_pascal`][pydantic.alias_generators.to_pascal]<br>
    [`to_camel`][pydantic.alias_generators.to_camel]<br>
    [`to_snake`][pydantic.alias_generators.to_snake]<br>


### Using a callable

<!-- Here's a basic example using a callable: -->
次に、callableを使用した基本的な例を示します。

```py
from pydantic import BaseModel, ConfigDict


class Tree(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda field_name: field_name.upper()
    )

    age: int
    height: float
    kind: str


t = Tree.model_validate({'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'})
print(t.model_dump(by_alias=True))
#> {'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'}
```

### Using an `AliasGenerator`

??? api "API Documentation"

    [`pydantic.aliases.AliasGenerator`][pydantic.aliases.AliasGenerator]<br>


<!-- `AliasGenerator` is a class that allows you to specify multiple alias generators for a model.
You can use an `AliasGenerator` to specify different alias generators for validation and serialization. -->
`AliasGenerator`は、1つのモデルに複数のエイリアスジェネレータを指定できるクラスです。
`AliasGenerator`を使用して、検証とシリアライゼーションのために異なるエイリアスジェネレータを指定できます。

<!-- This is particularly useful if you need to use different naming conventions for loading and saving data, but you don't want to specify the validation and serialization aliases for each field individually. -->
これは、データのロードと保存に異なる命名規則を使用する必要がありますが、各フィールドに個別に検証エイリアスとシリアル化エイリアスを指定したくない場合に特に便利です。

<!-- For example: -->
次に例を示します。

```py
from pydantic import AliasGenerator, BaseModel, ConfigDict


class Tree(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: field_name.upper(),
            serialization_alias=lambda field_name: field_name.title(),
        )
    )

    age: int
    height: float
    kind: str


t = Tree.model_validate({'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'})
print(t.model_dump(by_alias=True))
#> {'Age': 12, 'Height': 1.2, 'Kind': 'oak'}
```

## Alias Precedence

If you specify an `alias` on the [`Field`][pydantic.fields.Field], it will take precedence over the generated alias by default:
<!-- [`Field`][pydantic.fields.Field]に`alias`を指定すると、デフォルトでは生成されたエイリアスよりも優先されます。 -->

```py
from pydantic import BaseModel, ConfigDict, Field


def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))


class Voice(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    name: str
    language_code: str = Field(alias='lang')


voice = Voice(Name='Filiz', lang='tr-TR')
print(voice.language_code)
#> tr-TR
print(voice.model_dump(by_alias=True))
#> {'Name': 'Filiz', 'lang': 'tr-TR'}
```

### Alias Priority

<!-- You may set `alias_priority` on a field to change this behavior: -->
この動作を変更するには、フィールドに`alias_priority`を設定します。

<!-- * `alias_priority=2` the alias will *not* be overridden by the alias generator. -->
* `alias_priority=2`エイリアスはエイリアスジェネレータによって上書き*されません*。
<!-- * `alias_priority=1` the alias *will* be overridden by the alias generator. -->
* `alias_priority=1`エイリアスはエイリアスジェネレータによって上書きされます。
<!-- * `alias_priority` not set:
    * alias is set: the alias will *not* be overridden by the alias generator.
    * alias is not set: the alias *will* be overridden by the alias generator. -->
* `alias_priority`が設定されない:
    * aliasの設定: エイリアスはエイリアスジェネレータによって上書き*されません*。
    * aliasの未設定: エイリアスはエイリアスジェネレータによって*オーバーライド*されます。

<!-- The same precedence applies to `validation_alias` and `serialization_alias`.
See more about the different field aliases under [field aliases](../concepts/fields.md#field-aliases). -->
同じ優先順位が`validation_alias`と`serialization_alias`にも適用されます。
さまざまなフィールドエイリアスの詳細については、[field aliases](../concepts/fields.md#field-aliases)を参照してください。
