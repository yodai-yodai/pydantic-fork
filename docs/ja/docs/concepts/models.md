{% include-markdown "../warning.md" %}

??? api "API Documentation"
    [`pydantic.main.BaseModel`][pydantic.main.BaseModel]<br>

<!-- One of the primary ways of defining schema in Pydantic is via models. Models are simply classes which inherit from -->
[`pydantic.BaseModel`][pydantic.main.BaseModel] and define fields as annotated attributes.
Pydanticでスキーマを定義する主な方法の1つは、モデルを使用することです。モデルは単に
[`pydantic.BaseModel`][pydantic.main.BaseModel]フィールドを注釈付き属性として定義します。

<!-- You can think of models as similar to structs in languages like C, or as the requirements of a single endpoint in an API. -->
モデルは、Cなどの言語の構造体に似ていると考えることも、APIの単一エンドポイントの要件と考えることもできます。

<!-- Models share many similarities with Python's dataclasses, but have been designed with some subtle-yet-important differences that streamline certain workflows related to validation, serialization, and JSON schema generation. You can find more discussion of this in the [Dataclasses](dataclasses.md) section of the docs. -->
モデルはPythonのデータクラスと多くの類似点を共有していますが、検証、シリアライゼーション、JSONスキーマ生成に関連する特定のワークフローを合理化するために、いくつかの微妙ではありますが重要な違いを持って設計されています。これについての詳細は、ドキュメントの[Dataclasses](dataclasses.md)セクションを参照してください。

<!-- Untrusted data can be passed to a model and, after parsing and validation, Pydantic guarantees that the fields of the resultant model instance will conform to the field types defined on the model. -->
信頼できないデータをモデルに渡すことができますが、パースと検証の後、Pydanticは、結果のモデルインスタンスのフィールドがモデルで定義されたフィールドタイプに準拠することを保証します。

!!! note "Validation — a _deliberate_ misnomer"
    ### TL;DR

    <!-- We use the term "validation" to refer to the process of instantiating a model (or other type) that adheres to specified types and constraints. This task, which Pydantic is well known for, is most widely recognized as "validation" in colloquial terms, even though in other contexts the term "validation" may be more restrictive. -->
    "バリデーション"という用語は、指定されたタイプと制約に従うモデル(または他のタイプ)をインスタンス化するプロセスを指すために使用します。Pydanticでよく知られているこのタスクは、口語では"バリデーション"として最も広く認識されていますが、他の文脈では"バリデーション"という用語はより限定的な可能性があります。

    ---

    ### The long version
    ### 詳しい説明

    <!-- The potential confusion around the term "validation" arises from the fact that, strictly speaking, Pydantic's primary focus doesn't align precisely with the dictionary definition of "validation": -->
    "バリデーション"という用語をめぐる潜在的な混乱は、厳密に言えば、Pydanticの主な焦点が辞書の"バリデーション"の定義と正確に一致していないという事実からきています。

    <!-- ### validation
     _noun_
     the action of checking or proving the validity or accuracy of something.
    -->
    ### バリデーション
    > _名詞_: 何かの有効性または正確さをチェックまたは証明する行為。

    <!-- In Pydantic, the term "validation" refers to the process of instantiating a model (or other type) that adheres to specified types and constraints. Pydantic guarantees the types and constraints of the output, not the input data.
    This distinction becomes apparent when considering that Pydantic's `ValidationError` is raised when data cannot be successfully parsed into a model instance. -->
    Pydanticでは、"バリデーション'という用語は、指定された型と制約に従うモデル(または他の型)をインスタンス化するプロセスを指します。Pydanticは、入力データではなく、出力の型と制約を保証します。
    この区別は、データがモデルインスタンスに正常にパースできない場合にPydanticの`ValidationError`が発生することを考えると明らかになります。

    <!-- While this distinction may initially seem subtle, it holds practical significance.
    In some cases, "validation" goes beyond just model creation, and can include the copying and coercion of data.
    This can involve copying arguments passed to the constructor in order to perform coercion to a new type     without mutating the original input data. For a more in-depth understanding of the implications for your usage, refer to the [Data Conversion](#data-conversion) and [Attribute Copies](#attribute-copies) sections below. -->
    この区別は最初は微妙に見えるかもしれないが、実際には重要です。
    場合によっては、"バリデーション"は単なるモデルの作成にとどまらず、データのコピーや強制的な型変換を含むこともあります。
    これには、元の入力データを変更せずに新しい型への強制的な型変換を実行するために、コンストラクタに渡された引数をコピーすることが含まれます。使用方法への影響の詳細については、以下の[Data Conversion](#data-conversion)および[Attribute Copies](#attribute-copies)のセクションを参照してください。

    <!-- In essence, Pydantic's primary goal is to assure that the resulting structure post-processing (termed "validation") precisely conforms to the applied type hints. Given the widespread adoption of "validation" as the colloquial term for this process, we will consistently use it in our documentation. -->
    本質的に、Pydanticの主な目標は、結果として得られる構造の後処理("バリデーション"と呼ばれる)が、適用された型ヒントに正確に適合することを保証することです。このプロセスの口語として"バリデーション"が広く採用されていることを考慮して、私たちのドキュメントでは一貫して"バリデーション"を使用します。

    <!-- While the terms "parse" and "validation" were previously used interchangeably, moving forward, we aim to exclusively employ "validate",
    with "parse" reserved specifically for discussions related to [JSON parsing](../concepts/json.md). -->
    "パース"と"バリデーション"という用語は以前は互換的に使用されていましたが、今後は"バリデーション"のみを使用します。
    "パース"は特に[JSON parsing](../concepts/json.md)に関連する議論のために予約されています。

## Basic model usage

```py group="basic-model"
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str = 'Jane Doe'
```

<!-- In this example, `User` is a model with two fields: -->
この例では、`User`は2つのフィールドを持つモデルです。

* `id`, which is an integer and is required
* `name`, which is a string and is not required (it has a default value).

* `id`は整数で、必須です。
* `name`は文字列であり、必須ではありません(デフォルト値があります)。

```py group="basic-model"
user = User(id='123')
```

<!-- In this example, `user` is an instance of `User`.
Initialization of the object will perform all parsing and validation.
If no `ValidationError` is raised, you know the resulting model instance is valid. -->
この例では、`user`は`User`のインスタンスです。
オブジェクトを初期化すると、すべてのパースと検証が実行されます。
`ValidationError`が発生しない場合は、結果のモデルインスタンスが有効であることがわかります。

```py group="basic-model"
assert user.id == 123
assert isinstance(user.id, int)
# Note that '123' was coerced to an int and its value is 123
```

<!-- More details on pydantic's coercion logic can be found in [Data Conversion](#data-conversion).
Fields of a model can be accessed as normal attributes of the `user` object.
The string `'123'` has been converted into an int as per the field type. -->
pydanticの強制型変換ロジックの詳細については、[Data Conversion](#data-conversion)を参照してください。
モデルのフィールドは、"user"オブジェクトの通常の属性としてアクセスできます。
文字列`'123'`はフィールド型に従ってintに変換されました。

```py group="basic-model"
assert user.name == 'Jane Doe'
```

<!-- `name` wasn't set when `user` was initialized, so it has the default value. -->
`user`の初期化時に`name`が設定されていなかったため、デフォルト値が設定されています。

```py group="basic-model"
assert user.model_fields_set == {'id'}
```

<!-- The fields which were supplied when user was initialized. -->
このフィールドは、ユーザーが初期化されたときに指定されたフィールドです。

```py group="basic-model"
assert user.model_dump() == {'id': 123, 'name': 'Jane Doe'}
```

<!-- Either `.model_dump()` or `dict(user)` will provide a dict of fields, but `.model_dump()` can take numerous other
arguments. (Note that `dict(user)` will not recursively convert nested models into dicts, but `.model_dump()` will.) -->
`.model_dump()`または`dict(user)`のどちらかがフィールドのdictを提供しますが、`.model_dump()`は他の多くのものを取ることができます。(`dict(user)`はネストされたモデルをディクテーションに再帰的に変換しませんが、`.model_dump()`は変換します。)

```py group="basic-model"
user.id = 321
assert user.id == 321
```

<!-- By default, models are mutable and field values can be changed through attribute assignment. -->
デフォルトでは、モデルは可変であり、フィールド値は属性の割り当てによって変更できます。

### Model methods and properties


<!-- The example above only shows the tip of the iceberg of what models can do.
Models possess the following methods and attributes: -->
上の例は、モデルができることの氷山の一角を示しているにすぎません。
モデルには、次のメソッドと属性があります。

<!-- * [`model_computed_fields`][pydantic.main.BaseModel.model_computed_fields]: a dictionary of the computed fields of this model instance. -->
* [`model_computed_fields`][pydantic.main.BaseModel.model_computed_fields]: このモデルインスタンスの計算済みフィールドの辞書です。
<!-- * [`model_construct()`][pydantic.main.BaseModel.model_construct]: a class method for creating models without running validation. See [Creating models without validation](#creating-models-without-validation). -->
* [`model_construct()`][pydantic.main.BaseModel.model_construct]: 検証を実行せずにモデルを作成するためのクラスメソッドです。[Creating models without validation](#creating-models-without-validation)を参照してください。
<!-- * [`model_copy()`][pydantic.main.BaseModel.model_copy]: returns a copy (by default, shallow copy) of the model. See [Serialization](serialization.md#model_copy). -->
* [`model_copy()`][pydantic.main.BaseModel.model_copy]: モデルのコピー(デフォルトではシャローコピー)を返します。[Serialization](serialization.md#model_copy)を参照してください。
<!-- * [`model_dump()`][pydantic.main.BaseModel.model_dump]: returns a dictionary of the model's fields and values. See  [Serialization](serialization.md#model_dump). -->
*[`model_dump()`][pydantic.main.BaseModel.model_dump]: モデルのフィールドと値の辞書を返します。[Serialization](serialization.md#model_dump)を参照してください。
<!-- * [`model_dump_json()`][pydantic.main.BaseModel.model_dump_json]: returns a JSON string representation of [`model_dump()`][pydantic.main.BaseModel.model_dump]. See [Serialization](serialization.md#model_dump_json). -->
* [`model_dump_json()`][pydantic.main.BaseModel.model_dump_json]: [`model_dump()`][pydantic.main.BaseModel.model_dump]のJSON文字列表現を返します。[Serialization](serialization.md#model_dump_json)を参照してください。
<!-- * [`model_extra`][pydantic.main.BaseModel.model_extra]: get extra fields set during validation. -->
* [`model_extra`][pydantic.main.BaseModel.model_extra]: 検証中に追加フィールドセットを取得します。
<!-- * [`model_fields_set`][pydantic.main.BaseModel.model_fields_set]: set of fields which were set when the model instance was initialized. -->
* [`model_fields_set`][pydantic.main.BaseModel.model_fields_set]: モデルインスタンスが初期化されたときに設定されたフィールドのセットです。
<!-- * [`model_json_schema()`][pydantic.main.BaseModel.model_json_schema]: returns a jsonable dictionary representing the model as JSON Schema. See [JSON Schema](json_schema.md). -->
* [`model_json_schema()`][pydantic.main.BaseModel.model_json_schema]: JSONスキーマとしてモデルを表すJSON化可能な辞書を返します。[JSON Schema](json_schema.md)を参照してください。
<!-- * [`model_parametrized_name()`][pydantic.main.BaseModel.model_parametrized_name]: compute the class name for parametrizations of generic classes. -->
* [`model_parameterized_name()`][pydantic.main.BaseModel.model_parametrized_name]: ジェネリッククラスのパラメータ化のクラス名を計算します。
<!-- * [`model_post_init()`][pydantic.main.BaseModel.model_post_init]: perform additional initialization after the model is initialized. -->
* [`model_post_init()`][pydantic.main.BaseModel.model_post_init]:モデルが初期化された後に追加の初期化を実行します。
<!-- * [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild]: rebuild the model schema, which also supports building recursive generic models. See [Rebuild model schema](#rebuild-model-schema). -->
* [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild]: 再帰的なジェネリックモデルの構築もサポートするモデルスキーマを再構築します。[Rebuild model schema](#rebuild-model-schema)を参照してください。
<!-- * [`model_validate()`][pydantic.main.BaseModel.model_validate]: a utility for loading any object into a model. See [Helper functions](#helper-functions). -->
* [`model_validate()`][pydantic.main.BaseModel.model_validate]: 任意のオブジェクトをモデルにロードするためのユーティリティです。[Helper functions](#helper-functions)を参照してください。
<!-- * [`model_validate_json()`][pydantic.main.BaseModel.model_validate_json]: a utility for validating the given JSON data against the Pydantic model. See [Helper functions](#helper-functions). -->
* [`model_validate_json()`][pydantic.main.BaseModel.model_validate_json]: 指定されたJSONデータをPydanticモデルに対して検証するためのユーティリティです。[Helper functions](#helper-functions)を参照してください。



!!! note
    <!-- See [`BaseModel`][pydantic.main.BaseModel] for the class definition including a full list of methods and attributes. -->
    メソッドと属性の完全なリストを含むクラス定義については、[`BaseModel`][pydantic.main.BaseModel]を参照してください。


!!! tip
    <!-- See [Changes to `pydantic.BaseModel`](../migration.md#changes-to-pydanticbasemodel) in the [Migration Guide](../migration.md) for details on changes from Pydantic V1. -->
    Pydantic V1からの変更の詳細については、[Migration Guide](../migration.md)の[Changes to `pydantic.BaseModel`](../migration.md#changes-to-pydanticbasemodel)を参照してください。

## Nested models

<!-- More complex hierarchical data structures can be defined using models themselves as types in annotations. -->
より複雑な階層データ構造は、モデル自体をアノテーションの型として使用して定義することができます。

```py
from typing import List, Optional

from pydantic import BaseModel


class Foo(BaseModel):
    count: int
    size: Optional[float] = None


class Bar(BaseModel):
    apple: str = 'x'
    banana: str = 'y'


class Spam(BaseModel):
    foo: Foo
    bars: List[Bar]


m = Spam(foo={'count': 4}, bars=[{'apple': 'x1'}, {'apple': 'x2'}])
print(m)
"""
foo=Foo(count=4, size=None) bars=[Bar(apple='x1', banana='y'), Bar(apple='x2', banana='y')]
"""
print(m.model_dump())
"""
{
    'foo': {'count': 4, 'size': None},
    'bars': [{'apple': 'x1', 'banana': 'y'}, {'apple': 'x2', 'banana': 'y'}],
}
"""
```

<!-- For self-referencing models, see [postponed annotations](postponed_annotations.md#self-referencing-or-recursive-models). -->
自己参照モデルについては、[postponed annotations](postponed_annotations.md#self-referencing-or-recursive-models)を参照してください。

!!! note
    <!-- When defining your models, watch out for naming collisions between your field name and its type, a previously defined model, or an imported library. -->
    モデルを定義するときは、フィールド名とそのタイプ、以前に定義されたモデル、または読み込まれたライブラリとの間の名前の衝突に注意してください。

    <!-- For example, the following would yield a validation error: -->
    たとえば、次の例では検証エラーが発生します。
    ```py test="skip"
    from typing import Optional

    from pydantic import BaseModel


    class Boo(BaseModel):
        int: Optional[int] = None


    m = Boo(int=123)  # errors
    ```
    <!-- An error occurs since the field  `int` is set to a default value of `None` and has the exact same name as its type, so both are interpreted to be `None`. -->
    `int`フィールドはデフォルト値`None`に設定されており、そのタイプとまったく同じ名前を持っているため、両方とも`None`と解釈され、エラーが発生します。

## Rebuild model schema

<!-- The model schema can be rebuilt using [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild]. This is useful for building recursive generic models. -->
モデルスキーマは[`model_rebuild()`][pydantic.main.BaseModel.model_rebuild]を使用して再構築できます。これは再帰的なジェネリックモデルを構築するのに便利です。

```py
from pydantic import BaseModel, PydanticUserError


class Foo(BaseModel):
    x: 'Bar'


try:
    Foo.model_json_schema()
except PydanticUserError as e:
    print(e)
    """
    `Foo` is not fully defined; you should define `Bar`, then call `Foo.model_rebuild()`.

    For further information visit https://errors.pydantic.dev/2/u/class-not-fully-defined
    """


class Bar(BaseModel):
    pass


Foo.model_rebuild()
print(Foo.model_json_schema())
"""
{
    '$defs': {'Bar': {'properties': {}, 'title': 'Bar', 'type': 'object'}},
    'properties': {'x': {'$ref': '#/$defs/Bar'}},
    'required': ['x'],
    'title': 'Foo',
    'type': 'object',
}
"""
```

<!-- Pydantic tries to determine when this is necessary automatically and error if it wasn't done, but you may want to call [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild] proactively when dealing with recursive models or generics. -->
Pydanticは、いつこれが必要なのかを自動的に判断しようとし、それが行われなかった場合はエラーになりますが、再帰的なモデルやジェネリックスを扱う場合は、事前に[`model_rebuild()`][pydantic.main.BaseModel.model_rebuild]を呼び出した方がよいでしょう。

<!-- In V2, [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild] replaced `update_forward_refs()` from V1. There are some slight differences with the new behavior. -->
V2では、V1の`update_forward_refs()`が[`model_rebuild()`][pydantic.main.BaseModel.model_rebuild]に置き換えられました。新しい動作には若干の違いがあります。
<!-- The biggest change is that when calling [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild] on the outermost model, it builds a core schema used for validation of the whole model (nested models and all), so all types at all levels need to be ready before [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild] is called. -->
最大の変更点は、最も外側のモデルで[`model_rebuild()`][pydantic.main.BaseModel.model_rebuild]を呼び出すと、モデル全体(ネストされたモデルとすべて)の検証に使用されるコアスキーマが構築されるため、[`model_rebuild()`][pydantic.main.BaseModel.model_rebuild]が呼び出される前に、すべてのレベルのすべての型が準備されている必要があることです。

## Arbitrary class instances

<!-- (Formerly known as "ORM Mode"/`from_orm`.) -->
(以前は"ORM Mode"/`from_orm`と呼ばれていました。)

<!-- Pydantic models can also be created from arbitrary class instances by reading the instance attributes corresponding to the model field names. One common application of this functionality is integration with object-relational mappings (ORMs). -->
Pydanticモデルは、モデルフィールド名に対応するインスタンス属性を読み取ることによって、任意のクラスインスタンスから作成することもできます。この機能の一般的なアプリケーションの1つは、オブジェクトリレーショナルマッピング(ORM)との統合にあります。

<!-- To do this, set the config attribute `model_config['from_attributes'] = True`.
See [Model Config][pydantic.config.ConfigDict.from_attributes] and [ConfigDict][pydantic.config.ConfigDict] for more information. -->
これを行うには、config属性`model_config['from_attributes']=True`を設定します。
詳細については、[Model Config][pydantic.config.ConfigDict.from_attributes]および[ConfigDict][pydantic.config.ConfigDict]を参照してください。

<!-- The example here uses [SQLAlchemy](https://www.sqlalchemy.org/), but the same approach should work for any ORM. -->
ここでの例では[SQLAlchemy](https://www.SQLAlchemy.org/)を使用していますが、どのORMに対しても同じアプローチが有効です。

```py
from typing import List

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base
from typing_extensions import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Base = declarative_base()


class CompanyOrm(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, nullable=False)
    public_key = Column(String(20), index=True, nullable=False, unique=True)
    name = Column(String(63), unique=True)
    domains = Column(ARRAY(String(255)))


class CompanyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_key: Annotated[str, StringConstraints(max_length=20)]
    name: Annotated[str, StringConstraints(max_length=63)]
    domains: List[Annotated[str, StringConstraints(max_length=255)]]


co_orm = CompanyOrm(
    id=123,
    public_key='foobar',
    name='Testing',
    domains=['example.com', 'foobar.com'],
)
print(co_orm)
#> <__main__.CompanyOrm object at 0x0123456789ab>
co_model = CompanyModel.model_validate(co_orm)
print(co_model)
"""
id=123 public_key='foobar' name='Testing' domains=['example.com', 'foobar.com']
"""
```

### Reserved names

<!-- You may want to name a `Column` after a reserved SQLAlchemy field. In that case, `Field` aliases will be convenient: -->
予約されたSQLAlchemyフィールドの後に`Column`という名前を付けたい場合があります。その場合は`Field`という別名が便利です。

```py
import typing

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

from pydantic import BaseModel, ConfigDict, Field


class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metadata: typing.Dict[str, str] = Field(alias='metadata_')


Base = declarative_base()


class SQLModel(Base):
    __tablename__ = 'my_table'
    id = sa.Column('id', sa.Integer, primary_key=True)
    # 'metadata' is reserved by SQLAlchemy, hence the '_'
    metadata_ = sa.Column('metadata', sa.JSON)


sql_model = SQLModel(metadata_={'key': 'val'}, id=1)

pydantic_model = MyModel.model_validate(sql_model)

print(pydantic_model.model_dump())
#> {'metadata': {'key': 'val'}}
print(pydantic_model.model_dump(by_alias=True))
#> {'metadata_': {'key': 'val'}}
```

!!! note
    <!-- The example above works because aliases have priority over field names for field population. Accessing `SQLModel`'s `metadata` attribute would lead to a `ValidationError`. -->
    上記の例が機能するのは、エイリアスがフィールド入力のフィールド名よりも優先されるためです。`SQLModel`の`metadata`属性にアクセスすると`ValidationError`が発生します。

### Nested attributes

<!-- When using attributes to parse models, model instances will be created from both top-level attributes and deeper-nested attributes as appropriate. -->
属性を使用してモデルをパースする場合、モデルインスタンスは、必要に応じて最上位の属性と下位にネストされた属性の両方から作成されます。

<!-- Here is an example demonstrating the principle: -->
この原理を示す例を次に示します。

```py
from typing import List

from pydantic import BaseModel, ConfigDict


class PetCls:
    def __init__(self, *, name: str, species: str):
        self.name = name
        self.species = species


class PersonCls:
    def __init__(self, *, name: str, age: float = None, pets: List[PetCls]):
        self.name = name
        self.age = age
        self.pets = pets


class Pet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    species: str


class Person(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    age: float = None
    pets: List[Pet]


bones = PetCls(name='Bones', species='dog')
orion = PetCls(name='Orion', species='cat')
anna = PersonCls(name='Anna', age=20, pets=[bones, orion])
anna_model = Person.model_validate(anna)
print(anna_model)
"""
name='Anna' age=20.0 pets=[Pet(name='Bones', species='dog'), Pet(name='Orion', species='cat')]
"""
```

## Error handling

<!-- Pydantic will raise `ValidationError` whenever it finds an error in the data it's validating. -->
Pydanticは、検証中のデータにエラーを検出するたびに`ValidationError`を発生させます。

<!-- A single exception of type `ValidationError` will be raised regardless of the number of errors found, and that `ValidationError` will contain information about all of the errors and how they happened. -->
検出されたエラーの数にかかわらず、タイプ`ValidationError`の単一の例外が発生し、`ValidationError`にはすべてのエラーとその発生方法に関する情報が含まれます。

<!-- See [Error Handling](../errors/errors.md) for details on standard and custom errors. -->
標準エラーとカスタムエラーの詳細については、[Error Handling](../errors/errors.md)を参照してください。

<!-- As a demonstration: -->
デモンストレーション:

```py
from typing import List

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    list_of_ints: List[int]
    a_float: float


data = dict(
    list_of_ints=['1', 2, 'bad'],
    a_float='not a float',
)

try:
    Model(**data)
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    list_of_ints.2
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='bad', input_type=str]
    a_float
      Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='not a float', input_type=str]
    """
```

## Helper functions

<!-- *Pydantic* provides three `classmethod` helper functions on models for parsing data: -->
*Pydantic*は、データをパースするための3つの`classmethod`ヘルパー関数をモデルに提供します。

<!-- * [`model_validate()`][pydantic.main.BaseModel.model_validate]: this is very similar to the `__init__` method of the model, except it takes a dict or an object rather than keyword arguments. If the object passed cannot be validated, or if it's not a dictionary or instance of the model in question, a `ValidationError` will be raised. -->
* [`model_validate()`][pydantic.main.BaseModel.model_validate]: これはモデルの`__init__`メソッドと非常によく似ていますが、キーワード引数ではなく辞書またはオブジェクトを取る点が異なります。渡されたオブジェクトが検証できない場合、または問題のモデルの辞書またはインスタンスでない場合、`ValidationError`が発生します。
<!-- * [`model_validate_json()`][pydantic.main.BaseModel.model_validate_json]: this takes a *str* or *bytes* and parses it as *json*, then passes the result to [`model_validate()`][pydantic.main.BaseModel.model_validate]. -->
* [`model_validate_json()`][pydantic.main.BaseModel.model_validate_json]: *str*または*bytes*を受け取って*json*としてパースし、結果を[`model_validate()`][pydantic.main.BaseModel.model_validate]に渡します。
<!-- * [`model_validate_strings()`][pydantic.main.BaseModel.model_validate_strings]: this takes a dict (can be nested) with string keys and values and validates the data in *json* mode so that said strings can be coerced into the correct types. -->
* [`model_validate_strings()`][pydantic.main.BaseModel.model_validate_strings]: 文字列のキーと値を持つdict(ネスト可能)を取得し、*json*モードでデータを検証して、その文字列を強制的に正しい型に変換できるようにします。

```py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ValidationError


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None


m = User.model_validate({'id': 123, 'name': 'James'})
print(m)
#> id=123 name='James' signup_ts=None

try:
    User.model_validate(['not', 'a', 'dict'])
except ValidationError as e:
    print(e)
    """
    1 validation error for User
      Input should be a valid dictionary or instance of User [type=model_type, input_value=['not', 'a', 'dict'], input_type=list]
    """

m = User.model_validate_json('{"id": 123, "name": "James"}')
print(m)
#> id=123 name='James' signup_ts=None

try:
    m = User.model_validate_json('{"id": 123, "name": 123}')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      Input should be a valid string [type=string_type, input_value=123, input_type=int]
    """

try:
    m = User.model_validate_json('invalid JSON')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
      Invalid JSON: expected value at line 1 column 1 [type=json_invalid, input_value='invalid JSON', input_type=str]
    """

m = User.model_validate_strings({'id': '123', 'name': 'James'})
print(m)
#> id=123 name='James' signup_ts=None

m = User.model_validate_strings(
    {'id': '123', 'name': 'James', 'signup_ts': '2024-04-01T12:00:00'}
)
print(m)
#> id=123 name='James' signup_ts=datetime.datetime(2024, 4, 1, 12, 0)

try:
    m = User.model_validate_strings(
        {'id': '123', 'name': 'James', 'signup_ts': '2024-04-01'}, strict=True
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    signup_ts
      Input should be a valid datetime, invalid datetime separator, expected `T`, `t`, `_` or space [type=datetime_parsing, input_value='2024-04-01', input_type=str]
    """
```

<!-- If you want to validate serialized data in a format other than JSON, you should load the data into a dict yourself and then pass it to [`model_validate`][pydantic.main.BaseModel.model_validate]. -->
JSON以外のフォーマットでシリアライズされたデータを検証したい場合は、データを自分でdictにロードしてから、[`model_validate`][pydantic.main.BaseModel.model_validate]に渡してください。

!!! note
    <!-- Depending on the types and model configs involved, [`model_validate`][pydantic.main.BaseModel.model_validate] and [`model_validate_json`][pydantic.main.BaseModel.model_validate_json] may have different validation behavior. -->
    関連する型とモデルの設定によって、[`model_validate`][pydantic.main.BaseModel.model_validate]と[`model_validate_json`][pydantic.main.BaseModel.model_validate_json]の検証動作が異なる場合があります。

    <!-- If you have data coming from a non-JSON source, but want the same validation behavior and errors you'd get from [`model_validate_json`][pydantic.main.BaseModel.model_validate_json], our recommendation for now is to use either use `model_validate_json(json.dumps(data))`, or use [`model_validate_strings`][pydantic.main.BaseModel.model_validate_strings] if the data takes the form of a (potentially nested) dict with string keys and values. -->
    JSON以外のソースからのデータがあり、[`model_validate_json`][pydantic.main.BaseModel.model_validate_json]と同じ検証動作とエラーが必要な場合は、今のところ、`model_validate_json(json.dumps(data))`を使用するか、データが文字列のキーと値を持つ(ネストされている可能性のある)dictの形式をとる場合は[`model_validate_strings`][pydantic.main.BaseModel.model_validate_strings]を使用することをお勧めします。

!!! note
    <!-- Learn more about JSON parsing in the [JSON](../concepts/json.md) section of the docs. -->
    JSONパースの詳細については、ドキュメントの[JSON](../concepts/json.md)セクションを参照してください。

!!! note
    <!-- If you're passing in an instance of a model to [`model_validate`][pydantic.main.BaseModel.model_validate], you will want to consider setting [`revalidate_instances`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.revalidate_instances) in the model's config. -->
    モデルのインスタンスを[`model_validate`][pydantic.main.BaseModel.model_validate]に渡す場合は、モデルの構成に[`revalidate_instances`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.revalidate_instances)を設定することを検討してください。

    <!-- If you don't set this value, then validation will be skipped on model instances. See the below example: -->
    この値を設定しない場合、モデルインスタンスの検証はスキップされます。次の例を参照してください。


=== ":x: `revalidate_instances='never'`"
    ```py
    from pydantic import BaseModel


    class Model(BaseModel):
        a: int


    m = Model(a=0)
    # note: the `model_config` setting validate_assignment=True` can prevent this kind of misbehavior
    m.a = 'not an int'

    # doesn't raise a validation error even though m is invalid
    m2 = Model.model_validate(m)
    ```

=== ":white_check_mark: `revalidate_instances='always'`"
    ```py
    from pydantic import BaseModel, ConfigDict, ValidationError


    class Model(BaseModel):
        a: int

        model_config = ConfigDict(revalidate_instances='always')


    m = Model(a=0)
    # note: the `model_config` setting validate_assignment=True` can prevent this kind of misbehavior
    m.a = 'not an int'

    try:
        m2 = Model.model_validate(m)
    except ValidationError as e:
        print(e)
        """
        1 validation error for Model
        a
          Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not an int', input_type=str]
        """
    ```

### Creating models without validation

<!-- Pydantic also provides the [`model_construct()`][pydantic.main.BaseModel.model_construct] method, which allows models to be created **without validation**. This can be useful in at least a few cases: -->
Pydanticには、[`model_construct()`][pydantic.main.BaseModel.model_construct]メソッドも用意されています。このメソッドを使用すると、**検証なしで**モデルを作成できます。これは、少なくとも次のような場合に便利です。

<!-- * when working with complex data that is already known to be valid (for performance reasons) -->
* すでに有効であることがわかっている複雑なデータを処理する場合(パフォーマンス上の理由から)
<!-- * when one or more of the validator functions are non-idempotent, or -->
* 1つ以上の検証関数がべき等でない場合、または
<!-- * when one or more of the validator functions have side effects that you don't want to be triggered. -->
* 1つ以上のバリデータ関数に、トリガされたくない副作用がある場合。



!!! note
    <!-- In Pydantic V2, the performance gap between `BaseModel.__init__` and `BaseModel.model_construct` has been narrowed considerably. For simple models, calling `BaseModel.__init__` may even be faster. -->
    Pydantic V2では、`BaseModel.__init__`と`BaseModel.model_construct`の間のパフォーマンスの差が大幅に縮小されました。単純なモデルの場合、`BaseModel.__init__`を呼び出す方が高速になる可能性があります。

    <!-- If you are using [`model_construct()`][pydantic.main.BaseModel.model_construct] for performance reasons, you may want to profile your use case before assuming that [`model_construct()`][pydantic.main.BaseModel.model_construct] is faster. -->
    パフォーマンス上の理由から[`model_construct()`][pydantic.main.BaseModel.model_construct]を使用している場合は、[`model_construct()`][pydantic.main.BaseModel.model_construct]の方が高速であると想定する前に、ユースケースをプロファイルすることをお勧めします。

!!! warning
    <!-- [`model_construct()`][pydantic.main.BaseModel.model_construct] does not do any validation, meaning it can create models which are invalid. -->
    [`model_construct()`][pydantic.main.BaseModel.model_construct]は検証を行いません。つまり、無効なモデルを作成する可能性があります。

    <!-- **You should only ever use the [`model_construct()`][pydantic.main.BaseModel.model_construct] method with data which has already been validated, or that you definitely trust.** -->
    **[`model_construct()`][pydantic.main.BaseModel.model_construct]メソッドは、すでに検証済みのデータ、または確実に信頼できるデータに対してのみ使用してください。**

```py
from pydantic import BaseModel


class User(BaseModel):
    id: int
    age: int
    name: str = 'John Doe'


original_user = User(id=123, age=32)

user_data = original_user.model_dump()
print(user_data)
#> {'id': 123, 'age': 32, 'name': 'John Doe'}
fields_set = original_user.model_fields_set
print(fields_set)
#> {'age', 'id'}

# ...
# pass user_data and fields_set to RPC or save to the database etc.
# ...

# you can then create a new instance of User without
# re-running validation which would be unnecessary at this point:
new_user = User.model_construct(_fields_set=fields_set, **user_data)
print(repr(new_user))
#> User(id=123, age=32, name='John Doe')
print(new_user.model_fields_set)
#> {'age', 'id'}

# construct can be dangerous, only use it with validated data!:
bad_user = User.model_construct(id='dog')
print(repr(bad_user))
#> User(id='dog', name='John Doe')
```

<!-- The `_fields_set` keyword argument to [`model_construct()`][pydantic.main.BaseModel.model_construct] is optional, but allows you to be more precise about which fields were originally set and which weren't. If it's omitted [`model_fields_set`][pydantic.main.BaseModel.model_fields_set] will just be the keys of the data provided. -->
[`model_construct()`][pydantic.main.BaseModel.model_construct]の`_fields_set`キーワード引数はオプションですが、どのフィールドが最初に設定され、どのフィールドが設定されなかったかをより正確に知ることができます。これを省略すると、[`model_fields_set`][pydantic.main.BaseModel.model_fields_set]は単に提供されたデータのキーになります。

<!-- For example, in the example above, if `_fields_set` was not provided, `new_user.model_fields_set` would be `{'id', 'age', 'name'}`. -->
例えば、上の例では、`_fields_set`が与えられなかった場合、`new_user.model_fields_set`は`{'id','age','name'}`になります。

<!-- Note that for subclasses of [`RootModel`](#rootmodel-and-custom-root-types), the root value can be passed to [`model_construct()`][pydantic.main.BaseModel.model_construct]positionally, instead of using a keyword argument. -->
[`RootModel`](#rootmodel-and-custom-root-types)サブクラスでは、キーワード引数を使用する代わりに、ルートの値を[`model_construct()`][pydantic.main.BaseModel.model_construct]に位置的に渡すことができることに注意してください。

<!-- Here are some additional notes on the behavior of [`model_construct()`][pydantic.main.BaseModel.model_construct]: -->
[`model_construct()`][pydantic.main.BaseModel.model_construct]の動作に関する追加の注意事項を以下に示します。

<!-- * When we say "no validation is performed" — this includes converting dicts to model instances. So if you have a field with a `Model` type, you will need to convert the inner dict to a model yourself before passing it to [`model_construct()`][pydantic.main.BaseModel.model_construct]. -->
* "検証は実行されません"となる場合、これにはディクテーションをモデルインスタンスに変換することも含まれます。したがって、`Model`型のフィールドがある場合は、[`model_construct()`][pydantic.main.BaseModel.model_construct]に渡す前に、内部辞書を自分でモデルに変換する必要があります。
<!-- * In particular, the [`model_construct()`][pydantic.main.BaseModel.model_construct] method does not support recursively constructing models from dicts. -->
* 特に、[`model_construct()`][pydantic.main.BaseModel.model_construct]メソッドは、ディクテーションからモデルを再帰的に構築することをサポートしていません。
<!-- * If you do not pass keyword arguments for fields with defaults, the default values will still be used. -->
* デフォルト値を持つフィールドにキーワード引数を渡さない場合でも、デフォルト値が使用されます。
<!-- * For models with private attributes, the `__pydantic_private__` dict will be initialized the same as it would be when calling `__init__`. -->
* private属性を持つモデルの場合、`__pydantic_private__`dictは`__init__`を呼び出したときと同じように初期化されます。
<!-- * When constructing an instance using [`model_construct()`][pydantic.main.BaseModel.model_construct], no `__init__` method from the model or any of its parent classes will be called, even when a custom `__init__` method is defined. -->
* [`model_construct()`][pydantic.main.BaseModel.model_construct]を使用してインスタンスを構築する場合、カスタムの`__init__`メソッドが定義されていても、モデルまたはその親クラスから`__init__`メソッドは呼び出されません。

<!-- !!! note "On `extra` behavior with `model_construct`" -->
!!! note "`model_construct`の`extra`の動作について"

    <!-- * For models with `model_config['extra'] == 'allow'`, data not corresponding to fields will be correctly stored in the `__pydantic_extra__` dict and saved to the model's `__dict__`. -->
    * `model_config['extra']=='allow'`を持つモデルの場合、フィールドに対応しないデータは`__pydantic_extra__`dictに正しく保存され、モデルの`__dict__`に保存されます。
    <!-- * For models with `model_config['extra'] == 'ignore'`, data not corresponding to fields will be ignored - that is, not stored in `__pydantic_extra__` or `__dict__` on the instance. -->
    * `model_config['extra']=='ignore'`を持つモデルの場合、フィールドに対応しないデータは無視されます。つまり、インスタンスの`__pydantic_extra__`や`__dict__`には保存されません。
    <!-- * Unlike a call to `__init__`, a call to `model_construct` with `model_config['extra'] == 'forbid'` doesn't raise an error in the presence of data not corresponding to fields. Rather, said input data is simply ignored. -->
    * `__init__`の呼び出しとは異なり、`model_config['extra']=='forbid'`を指定した`model_construct`の呼び出しでは、フィールドに対応しないデータが存在してもエラーになりません。むしろ、その入力データは単に無視されます。



## Generic models

<!-- Pydantic supports the creation of generic models to make it easier to reuse a common model structure. -->
Pydanticは、一般的なモデル構造の再利用を容易にするために、ジェネリックモデルの作成をサポートしています。

<!-- In order to declare a generic model, you perform the following steps: -->
ジェネリックモデルを宣言するには、以下の手順を実行します。

<!-- 1. Declare one or more `typing.TypeVar` instances to use to parameterize your model. -->
1. モデルのパラメータ化に使用する1つ以上の`typing.TypeVar`インスタンスを宣言します。
<!-- 2. Declare a pydantic model that inherits from `pydantic.BaseModel` and `typing.Generic`, where you pass the `TypeVar` instances as parameters to `typing.Generic`. -->
2. `pydantic.BaseModel`と`typing.Generic`を継承するpydanticモデルを宣言し、`TypeVar`インスタンスをパラメータとして`typing.Generic`に渡します。
<!-- 3. Use the `TypeVar` instances as annotations where you will want to replace them with other types or pydantic models. -->
3. `TypeVar`インスタンスをアノテーションとして使用し、他の型やpydanticモデルに置き換えます。

<!-- Here is an example using a generic `BaseModel` subclass to create an easily-reused HTTP response payload wrapper: -->
以下は、`BaseModel`ジェネリックサブクラスを使用して、簡単に再利用できるHTTPレスポンスペイロードラッパーを作成する例です。

```py
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ValidationError

DataT = TypeVar('DataT')


class DataModel(BaseModel):
    numbers: List[int]
    people: List[str]


class Response(BaseModel, Generic[DataT]):
    data: Optional[DataT] = None


print(Response[int](data=1))
#> data=1
print(Response[str](data='value'))
#> data='value'
print(Response[str](data='value').model_dump())
#> {'data': 'value'}

data = DataModel(numbers=[1, 2, 3], people=[])
print(Response[DataModel](data=data).model_dump())
#> {'data': {'numbers': [1, 2, 3], 'people': []}}
try:
    Response[int](data='value')
except ValidationError as e:
    print(e)
    """
    1 validation error for Response[int]
    data
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='value', input_type=str]
    """
```

<!-- If you set the `model_config` or make use of `@field_validator` or other Pydantic decorators in your generic model definition, they will be applied to parametrized subclasses in the same way as when inheriting from a `BaseModel` subclass. Any methods defined on your generic class will also be inherited. -->
ジェネリックモデル定義で`model_config`を設定したり、`@field_validator`やその他のPydanticデコレータを使用したりすると、それらは`BaseModel`サブクラスから継承する場合と同じ方法で、パラメータ化されたサブクラスに適用されます。ジェネリッククラスで定義されたメソッドも継承されます。

<!-- Pydantic's generics also integrate properly with type checkers, so you get all the type checking you would expect if you were to declare a distinct type for each parametrization. -->
Pydanticのジェネリックスは型チェッカーとも適切に統合されているため、パラメーター化ごとに異なる型を宣言した場合に期待されるすべての型チェックを行うことができます。

!!! note
    <!-- Internally, Pydantic creates subclasses of `BaseModel` at runtime when generic models are parametrized. -->
    内部的には、Pydanticはジェネリックモデルがパラメータ化されると、実行時に`BaseModel`のサブクラスを作成します。

    <!-- These classes are cached, so there should be minimal overhead introduced by the use of generics models. -->
    これらのクラスはキャッシュされるため、ジェネリックス・モデルを使用することで生じるオーバーヘッドは最小限に抑えられます。

<!-- To inherit from a generic model and preserve the fact that it is generic, the subclass must also inherit from `typing.Generic`: -->
ジェネリックモデルから継承し、ジェネリックであるという事実を保持するには、サブクラスも`typing.Generic`から継承する必要があります。

```py
from typing import Generic, TypeVar

from pydantic import BaseModel

TypeX = TypeVar('TypeX')


class BaseClass(BaseModel, Generic[TypeX]):
    X: TypeX


class ChildClass(BaseClass[TypeX], Generic[TypeX]):
    # Inherit from Generic[TypeX]
    pass


# Replace TypeX by int
print(ChildClass[int](X=1))
#> X=1
```

<!-- You can also create a generic subclass of a `BaseModel` that partially or fully replaces the type parameters in the superclass: -->
スーパークラスの型パラメータを部分的または完全に置き換える`BaseModel`のジェネリックサブクラスを作成することもできます。

```py
from typing import Generic, TypeVar

from pydantic import BaseModel

TypeX = TypeVar('TypeX')
TypeY = TypeVar('TypeY')
TypeZ = TypeVar('TypeZ')


class BaseClass(BaseModel, Generic[TypeX, TypeY]):
    x: TypeX
    y: TypeY


class ChildClass(BaseClass[int, TypeY], Generic[TypeY, TypeZ]):
    z: TypeZ


# Replace TypeY by str
print(ChildClass[str, int](x='1', y='y', z='3'))
#> x=1 y='y' z=3
```

<!-- If the name of the concrete subclasses is important, you can also override the default name generation: -->
具象サブクラスの名前が重要な場合は、デフォルトの名前生成をオーバーライドすることもできます。

```py
from typing import Any, Generic, Tuple, Type, TypeVar

from pydantic import BaseModel

DataT = TypeVar('DataT')


class Response(BaseModel, Generic[DataT]):
    data: DataT

    @classmethod
    def model_parametrized_name(cls, params: Tuple[Type[Any], ...]) -> str:
        return f'{params[0].__name__.title()}Response'


print(repr(Response[int](data=1)))
#> IntResponse(data=1)
print(repr(Response[str](data='a')))
#> StrResponse(data='a')
```

<!-- You can use parametrized generic models as types in other models: -->
パラメータ化されたジェネリックモデルを他のモデルのタイプとして使用できます。

```py
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    content: T


class Product(BaseModel):
    name: str
    price: float


class Order(BaseModel):
    id: int
    product: ResponseModel[Product]


product = Product(name='Apple', price=0.5)
response = ResponseModel[Product](content=product)
order = Order(id=1, product=response)
print(repr(order))
"""
Order(id=1, product=ResponseModel[Product](content=Product(name='Apple', price=0.5)))
"""
```

!!! tip
    <!-- When using a parametrized generic model as a type in another model (like `product: ResponseModel[Product]`), make sure to parametrize said generic model when you initialize the model instance (like `response = ResponseModel[Product](content=product)`). -->
    パラメータ化されたジェネリックモデルを別のモデルの型として使用する場合(`product:ResponseModel[Product]`など)、モデルインスタンスを初期化するときには必ずそのジェネリックモデルをパラメータ化してください(`response=ResponseModel[Product](content=product)`など)。

    <!-- If you don't, a `ValidationError` will be raised, as Pydantic doesn't infer the type of the generic model based on the data passed to it. -->
    そうしないと、Pydanticは渡されたデータに基づいてジェネリックモデルの型を推測しないので、`ValidationError`が発生します。

<!-- Using the same `TypeVar` in nested models allows you to enforce typing relationships at different points in your model: -->
ネストされたモデルで同じ`TypeVar`を使用すると、モデル内の異なるポイントで型付け関係を強制することができます。

```py
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar('T')


class InnerT(BaseModel, Generic[T]):
    inner: T


class OuterT(BaseModel, Generic[T]):
    outer: T
    nested: InnerT[T]


nested = InnerT[int](inner=1)
print(OuterT[int](outer=1, nested=nested))
#> outer=1 nested=InnerT[int](inner=1)
try:
    nested = InnerT[str](inner='a')
    print(OuterT[int](outer='a', nested=nested))
except ValidationError as e:
    print(e)
    """
    2 validation errors for OuterT[int]
    outer
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    nested
      Input should be a valid dictionary or instance of InnerT[int] [type=model_type, input_value=InnerT[str](inner='a'), input_type=InnerT[str]]
    """
```

<!-- When using bound type parameters, and when leaving type parameters unspecified, Pydantic treats generic models similarly to how it treats built-in generic types like `List` and `Dict`: -->
境界された型パラメータを使用する場合、および型パラメータを指定しないままにしておく場合、Pydanticはジェネリックモデルを`List`や`Dict`のような組み込みジェネリック型と同じように扱います。

<!-- * If you don't specify parameters before instantiating the generic model, they are validated as the bound of the `TypeVar`. -->
* ジェネリックモデルをインスタンス化する前にパラメータを指定しない場合、それらは`TypeVar`の境界として検証されます。
<!-- * If the `TypeVar`s involved have no bounds, they are treated as `Any`. -->
 *関係する`TypeVar`に境界がない場合、それらは`Any`として扱われます。

<!-- Also, like `List` and `Dict`, any parameters specified using a `TypeVar` can later be substituted with concrete types: -->
また、`List`や`Dict`のように、`TypeVar`を使用して指定されたパラメータは、後で具体的な型に置き換えることができます。

```py requires="3.12"
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

AT = TypeVar('AT')
BT = TypeVar('BT')


class Model(BaseModel, Generic[AT, BT]):
    a: AT
    b: BT


print(Model(a='a', b='a'))
#> a='a' b='a'

IntT = TypeVar('IntT', bound=int)
typevar_model = Model[int, IntT]
print(typevar_model(a=1, b=1))
#> a=1 b=1
try:
    typevar_model(a='a', b='a')
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for Model[int, TypeVar]
    a
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    b
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """

concrete_model = typevar_model[int]
print(concrete_model(a=1, b=1))
#> a=1 b=1
```

!!! warning
    <!-- While it may not raise an error, we strongly advise against using parametrized generics in isinstance checks. -->
    エラーになることはありませんが、isinstanceチェックでパラメーター化されたジェネリックスを使用しないことを強くお勧めします。

    <!-- For example, you should not do `isinstance(my_model, MyGenericModel[int])`. However, it is fine to do `isinstance(my_model, MyGenericModel)`. (Note that, for standard generics, it would raise an error to do a subclass check with a parameterized generic.) -->
    例えば、`isinstance(my_model, MyGenericModel[int])`を実行すべきではありませんが、`isinstance(my_model, MyGenericModel)`を実行しても問題ありません(標準のジェネリックスの場合、パラメータ化されたジェネリックスでサブクラスのチェックを行うとエラーが発生することに注意してください)。

    <!-- If you need to perform isinstance checks against parametrized generics, you can do this by subclassing the parametrized generic class. This looks like `class MyIntModel(MyGenericModel[int]): ...` and `isinstance(my_model, MyIntModel)`. -->
    パラメータ化されたジェネリックに対してisinstanceチェックを実行する必要がある場合は、パラメータ化されたジェネリッククラスをサブクラス化することで実行できます。これは`class MyIntModel(MyGenericModel[int]):...`および`isinstance(my_model, MyIntModel)`のようになります。

<!-- If a Pydantic model is used in a `TypeVar` bound and the generic type is never parametrized then Pydantic will use the bound for validation but treat the value as `Any` in terms of serialization: -->
Pydanticモデルが`TypeVar`境界で使用され、ジェネリック型がパラメータ化されていない場合、Pydanticは検証に境界を使用しますが、シリアライゼーションの観点からは値を`Any`として扱います。

```py
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel


class ErrorDetails(BaseModel):
    foo: str


ErrorDataT = TypeVar('ErrorDataT', bound=ErrorDetails)


class Error(BaseModel, Generic[ErrorDataT]):
    message: str
    details: Optional[ErrorDataT]


class MyErrorDetails(ErrorDetails):
    bar: str


# serialized as Any
error = Error(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='var2'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
        'bar': 'var2',
    },
}

# serialized using the concrete parametrization
# note that `'bar': 'var2'` is missing
error = Error[ErrorDetails](
    message='We just had an error',
    details=ErrorDetails(foo='var'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
    },
}
```

Here's another example of the above behavior, enumerating all permutations regarding bound specification and generic type parametrization:
上記の動作の別の例として、境界仕様とジェネリック型のパラメータ化に関するすべての順列を列挙します。

```py
from typing import Generic

from typing_extensions import TypeVar

from pydantic import BaseModel

TBound = TypeVar('TBound', bound=BaseModel)
TNoBound = TypeVar('TNoBound')


class IntValue(BaseModel):
    value: int


class ItemBound(BaseModel, Generic[TBound]):
    item: TBound


class ItemNoBound(BaseModel, Generic[TNoBound]):
    item: TNoBound


item_bound_inferred = ItemBound(item=IntValue(value=3))
item_bound_explicit = ItemBound[IntValue](item=IntValue(value=3))
item_no_bound_inferred = ItemNoBound(item=IntValue(value=3))
item_no_bound_explicit = ItemNoBound[IntValue](item=IntValue(value=3))

# calling `print(x.model_dump())` on any of the above instances results in the following:
#> {'item': {'value': 3}}
```

<!-- If you use a `default=...` (available in Python >= 3.13 or via `typing-extensions`) or constraints (`TypeVar('T', str, int)`;note that you rarely want to use this form of a `TypeVar`) then the default value or constraints will be used for both validation and serialization if the type variable is not parametrized. -->
`default=...`(Python>=3.13または`typing-extensions`で使用可能)または制約(`TypeVar('T',str, int)`;この形式の`TypeVar`を使用することはめったにないことに注意してください)を使用する場合、型変数がパラメータ化されていなければ、検証とシリアライゼーションの両方にデフォルト値または制約が使用されます。
<!-- You can override this behavior using `pydantic.SerializeAsAny`: -->
この動作は`pydantic.SerializeAsAny`を使って上書きできます:



```py
from typing import Generic, Optional

from typing_extensions import TypeVar

from pydantic import BaseModel, SerializeAsAny


class ErrorDetails(BaseModel):
    foo: str


ErrorDataT = TypeVar('ErrorDataT', default=ErrorDetails)


class Error(BaseModel, Generic[ErrorDataT]):
    message: str
    details: Optional[ErrorDataT]


class MyErrorDetails(ErrorDetails):
    bar: str


# serialized using the default's serializer
error = Error(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='var2'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
    },
}


class SerializeAsAnyError(BaseModel, Generic[ErrorDataT]):
    message: str
    details: Optional[SerializeAsAny[ErrorDataT]]


# serialized as Any
error = SerializeAsAnyError(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='baz'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
        'bar': 'baz',
    },
}
```

!!! note
    <!-- Note, you may run into a bit of trouble if you don't parametrize a generic when the case of validating against the generic's bound
    could cause data loss. See the example below: -->
    注意:ジェネリックの境界に対して検証する場合、ジェネリックをパラメータ化しないと、ちょっとしたトラブルに巻き込まれる可能性があります。
    データが失われる可能性があります。次の例を参照してください。

```py
from typing import Generic

from typing_extensions import TypeVar

from pydantic import BaseModel

TItem = TypeVar('TItem', bound='ItemBase')


class ItemBase(BaseModel): ...


class IntItem(ItemBase):
    value: int


class ItemHolder(BaseModel, Generic[TItem]):
    item: TItem


loaded_data = {'item': {'value': 1}}


print(ItemHolder(**loaded_data).model_dump())  # (1)!
#> {'item': {}}

print(ItemHolder[IntItem](**loaded_data).model_dump())  # (2)!
#> {'item': {'value': 1}}
```

<!-- 1. When the generic isn't parametrized, the input data is validated against the generic bound. Given that `ItemBase` has no fields, the `item` field information is lost. -->
1. ジェネリックがパラメータ化されていない場合、入力データはジェネリック境界に対して検証されます。`ItemBase`にフィールドがない場合、`item`フィールドの情報は失われます。
<!-- 2. In this case, the runtime type information is provided explicitly via the generic parametrization, so the input data is validated against the `IntItem` class and the serialization output matches what's expected. -->
2. この場合、実行時の型情報は一般的なパラメータ化によって明示的に提供されるため、入力データは`IntItem`クラスに対して検証され、シリアライゼーションの出力は期待されたものと一致します。

## Dynamic model creation

??? api "API Documentation"
    [`pydantic.main.create_model`][pydantic.main.create_model]<br>

<!-- There are some occasions where it is desirable to create a model using runtime information to specify the fields. -->
<!-- For this Pydantic provides the `create_model` function to allow models to be created on the fly: -->
実行時情報を使用してモデルを作成し、フィールドを指定することが望ましい場合があります。
このために、Pydanticは`create_model`関数を提供して、モデルをオンザフライで作成できるようにします。

```py
from pydantic import BaseModel, create_model

DynamicFoobarModel = create_model(
    'DynamicFoobarModel', foo=(str, ...), bar=(int, 123)
)


class StaticFoobarModel(BaseModel):
    foo: str
    bar: int = 123
```

<!-- Here `StaticFoobarModel` and `DynamicFoobarModel` are identical. -->
ここで、`StaticFoobarModel`と`DynamicFoobarModel`は同一です。

<!-- Fields are defined by one of the following tuple forms: -->
フィールドは、次のタプル形式のいずれかで定義されます。

<!--
* `(<type>, <default value>)`
* `(<type>, Field(...))`
* `typing.Annotated[<type>, Field(...)]`
-->
* `(<type>, <default value>)`
* `(<type>, Field(...))`
* `typing.Annotated[<type>, Field(...)]`

<!-- Using a `Field(...)` call as the second argument in the tuple (the default value) allows for more advanced field configuration. Thus, the following are analogous: -->
タプルの2番目の引数(デフォルト値)として`Field(...)`呼び出しを使用すると、より高度なフィールド設定が可能になります。したがって、次のように類似しています。

```py
from pydantic import BaseModel, Field, create_model

DynamicModel = create_model(
    'DynamicModel',
    foo=(str, Field(..., description='foo description', alias='FOO')),
)


class StaticModel(BaseModel):
    foo: str = Field(..., description='foo description', alias='FOO')
```

<!-- The special keyword arguments `__config__` and `__base__` can be used to customize the new model.
This includes extending a base model with extra fields. -->
特別なキーワード引数`__config__`と`__base__`を使って新しいモデルをカスタマイズすることができます。
これには、フィールドを追加して基本モデルを拡張することも含まれます。



```py
from pydantic import BaseModel, create_model


class FooModel(BaseModel):
    foo: str
    bar: int = 123


BarModel = create_model(
    'BarModel',
    apple=(str, 'russet'),
    banana=(str, 'yellow'),
    __base__=FooModel,
)
print(BarModel)
#> <class '__main__.BarModel'>
print(BarModel.model_fields.keys())
#> dict_keys(['foo', 'bar', 'apple', 'banana'])
```

<!-- You can also add validators by passing a dict to the `__validators__` argument. -->
`__validators__`引数にdictを渡すことでバリデータを追加することもできます。

```py rewrite_assert="false"
from pydantic import ValidationError, create_model, field_validator


def username_alphanumeric(cls, v):
    assert v.isalnum(), 'must be alphanumeric'
    return v


validators = {
    'username_validator': field_validator('username')(username_alphanumeric)
}

UserModel = create_model(
    'UserModel', username=(str, ...), __validators__=validators
)

user = UserModel(username='scolvin')
print(user)
#> username='scolvin'

try:
    UserModel(username='scolvi%n')
except ValidationError as e:
    print(e)
    """
    1 validation error for UserModel
    username
      Assertion failed, must be alphanumeric [type=assertion_error, input_value='scolvi%n', input_type=str]
    """
```

!!! note
    <!-- To pickle a dynamically created model: -->
    動的に作成されたモデルをピクル化するには、次の手順を行います。

    <!--
    - the model must be defined globally
    - it must provide `__module__`
    -->
    - モデルはグローバルに定義する必要があります。
    - `__module__`を提供する必要があります



## `RootModel` and custom root types

??? api "API Documentation"
    [`pydantic.root_model.RootModel`][pydantic.root_model.RootModel]<br>

<!-- Pydantic models can be defined with a "custom root type" by subclassing [`pydantic.RootModel`][pydantic.RootModel]. -->
Pydanticモデルは、[`pydantic.RootModel`][pydantic.RootModel]をサブクラス化することで、"カスタムルートタイプ"で定義できます。

<!-- The root type can be any type supported by Pydantic, and is specified by the generic parameter to `RootModel`.
The root value can be passed to the model `__init__` or [`model_validate`][pydantic.main.BaseModel.model_validate] via the first and only argument. -->
ルート型はPydanticでサポートされている任意の型で、`RootModel`の汎用パラメータで指定されます。
ルート値は、最初で唯一の引数を介してモデル`__init__`または[`model_validate`][pydantic.main.BaseModel.model_validate]に渡すことができます。

<!-- Here's an example of how this works: -->
これがどのように機能するかの例を次に示します。

```py
from typing import Dict, List

from pydantic import RootModel

Pets = RootModel[List[str]]
PetsByName = RootModel[Dict[str, str]]


print(Pets(['dog', 'cat']))
#> root=['dog', 'cat']
print(Pets(['dog', 'cat']).model_dump_json())
#> ["dog","cat"]
print(Pets.model_validate(['dog', 'cat']))
#> root=['dog', 'cat']
print(Pets.model_json_schema())
"""
{'items': {'type': 'string'}, 'title': 'RootModel[List[str]]', 'type': 'array'}
"""

print(PetsByName({'Otis': 'dog', 'Milo': 'cat'}))
#> root={'Otis': 'dog', 'Milo': 'cat'}
print(PetsByName({'Otis': 'dog', 'Milo': 'cat'}).model_dump_json())
#> {"Otis":"dog","Milo":"cat"}
print(PetsByName.model_validate({'Otis': 'dog', 'Milo': 'cat'}))
#> root={'Otis': 'dog', 'Milo': 'cat'}
```

<!-- If you want to access items in the `root` field directly or to iterate over the items, you can implement custom `__iter__` and `__getitem__` functions, as shown in the following example. -->
`root`フィールド内の項目に直接アクセスしたり、項目を繰り返し処理したりしたい場合は、次の例に示すように、カスタムの`__iter__`関数と`__getitem__`関数を実装することができます。

```py
from typing import List

from pydantic import RootModel


class Pets(RootModel):
    root: List[str]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


pets = Pets.model_validate(['dog', 'cat'])
print(pets[0])
#> dog
print([pet for pet in pets])
#> ['dog', 'cat']
```

<!-- You can also create subclasses of the parametrized root model directly: -->
パラメータ化されたルートモデルのサブクラスを直接作成することもできます。

```py
from typing import List

from pydantic import RootModel


class Pets(RootModel[List[str]]):
    def describe(self) -> str:
        return f'Pets: {", ".join(self.root)}'


my_pets = Pets.model_validate(['dog', 'cat'])

print(my_pets.describe())
#> Pets: dog, cat
```


## Faux immutability

<!-- Models can be configured to be immutable via `model_config['frozen'] = True`. When this is set, attempting to change the values of instance attributes will raise errors. See the [API reference][pydantic.config.ConfigDict.frozen] for more details. -->
モデルは`model_config['frozen']=True`で不変に設定できます。これが設定されている場合、インスタンス属性の値を変更しようとするとエラーが発生します。詳細については、[API reference][pydantic.config.ConfigDict.frozen]を参照してください。

!!! note
    <!-- This behavior was achieved in Pydantic V1 via the config setting `allow_mutation = False`.
    This config flag is deprecated in Pydantic V2, and has been replaced with `frozen`. -->
    この動作は、Pydantic V1で`allow_mutation=False`という設定によって実現されました。
    このconfigフラグはPydantic V2では廃止され、`frozen`に置き換えられました。

!!! warning
    <!-- In Python, immutability is not enforced. Developers have the ability to modify objects that are conventionally considered "immutable" if they choose to do so. -->
    Pythonでは、不変性は強制されません。開発者は、従来"不変"と見なされていたオブジェクトを、変更することを選択した場合に変更することができます。

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class FooBarModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    a: str
    b: dict


foobar = FooBarModel(a='hello', b={'apple': 'pear'})

try:
    foobar.a = 'different'
except ValidationError as e:
    print(e)
    """
    1 validation error for FooBarModel
    a
      Instance is frozen [type=frozen_instance, input_value='different', input_type=str]
    """

print(foobar.a)
#> hello
print(foobar.b)
#> {'apple': 'pear'}
foobar.b['apple'] = 'grape'
print(foobar.b)
#> {'apple': 'grape'}
```

<!-- Trying to change `a` caused an error, and `a` remains unchanged. However, the dict `b` is mutable, and the immutability of `foobar` doesn't stop `b` from being changed. -->
`a`を変更しようとするとエラーが発生し、`a`は変更されません。しかし、辞書`b`は変更可能であり、`foobar`の不変性は`b`の変更を止めるものではありません。

## Abstract base classes

<!-- Pydantic models can be used alongside Python's[Abstract Base Classes](https://docs.python.org/3/library/abc.html) (ABCs). -->
Pydanticモデルは、Pythonの[Abstract Base Classes](https://docs.python.org/3/library/abc.html)(ABC)と一緒に使用できます。

```py
import abc

from pydantic import BaseModel


class FooBarModel(BaseModel, abc.ABC):
    a: str
    b: int

    @abc.abstractmethod
    def my_abstract_method(self):
        pass
```

## Field ordering

<!-- Field order affects models in the following ways: -->
フィールドの順序は、モデルに次のような影響を与えます。

<!--
* field order is preserved in the model [schema](json_schema.md)
* field order is preserved in [validation errors](#error-handling)
* field order is preserved by [`.model_dump()` and `.model_dump_json()` etc.](serialization.md#model_dump)
-->
* フィールドの順序はモデル[schema](json_schema.md)で保持されます。
* [validation errors](#error-handling)でフィールドの順序が保持されます。
* フィールドの順序は、[`.model_dump()`および`.model_dump_json()`など](serialization.md#model_dump)によって保持されます。



```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    a: int
    b: int = 2
    c: int = 1
    d: int = 0
    e: float


print(Model.model_fields.keys())
#> dict_keys(['a', 'b', 'c', 'd', 'e'])
m = Model(e=2, a=1)
print(m.model_dump())
#> {'a': 1, 'b': 2, 'c': 1, 'd': 0, 'e': 2.0}
try:
    Model(a='x', b='x', c='x', d='x', e='x')
except ValidationError as err:
    error_locations = [e['loc'] for e in err.errors()]

print(error_locations)
#> [('a',), ('b',), ('c',), ('d',), ('e',)]
```

## Required fields

<!-- To declare a field as required, you may declare it using an annotation, or an annotation in combination with a `Field` specification.
You may also use `Ellipsis`/`...` to emphasize that a field is required, especially when using the `Field` constructor. -->
必要に応じてフィールドを宣言するには、注釈を使用するか、注釈と`Field`仕様を組み合わせて宣言します。
特に`Field`コンストラクタを使用する場合は、`Ellipsis`/`...`を使用して、フィールドが必要であることを強調することもできます。

<!-- The [`Field`](fields.md) function is primarily used to configure settings like `alias` or `description` for an attribute.
The constructor supports `Ellipsis`/`...` as the sole positional argument.
This is used as a way to indicate that said field is mandatory, though it's the type hint that enforces this requirement. -->
[`Field`](fields.md)関数は、主に属性の`alias`や`description`のような設定を行うために使われます。
コンストラクタは`Ellipsis`/`...`を唯一の位置引数としてサポートします。
これは、そのフィールドが必須であることを示す方法として使用されますが、この要件を強制するのは型ヒントです。

```py
from pydantic import BaseModel, Field


class Model(BaseModel):
    a: int
    b: int = ...
    c: int = Field(..., alias='C')
```

<!-- Here `a`, `b` and `c` are all required. However, this use of `b: int = ...` does not work properly with [mypy](../integrations/mypy.md), and as of **v1.0** should be avoided in most cases. -->
ここで`a`、`b`、`c`はすべて必須です。しかし、この`b:int=...`の使用は[mypy](../integrations/mypy.md)では適切に動作せず、**v1.0**ではほとんどの場合避けるべきです。

!!! note
    <!-- In Pydantic V1, fields annotated with `Optional` or `Any` would be given an implicit default of `None` even if no default was explicitly specified. This behavior has changed in Pydantic V2, and there are no longer any type annotations that will result in a field having an implicit default value. -->
    Pydantic V1では、`Optional`または`Any`で注釈されたフィールドには、デフォルトが明示的に指定されていない場合でも、暗黙的なデフォルト`None`が与えられていました。この動作はPydantic V2で変更され、暗黙的なデフォルト値を持つフィールドを生成する型注釈はもはや存在しません。

    <!-- See [the migration guide](../migration.md#required-optional-and-nullable-fields) for more details on changes to required and nullable fields. -->
    必須フィールドとnull許容フィールドの変更の詳細については、[the migration guide](../migration.md#required-optional-and-nullable-fields)を参照してください。

## Fields with non-hashable default values

<!-- A common source of bugs in python is to use a mutable object as a default value for a function or method argument, as the same instance ends up being reused in each call. -->
Pythonの一般的なバグの原因は、関数またはメソッドの引数のデフォルト値として可変オブジェクトを使用することです。これは、各呼び出しで同じインスタンスが再利用されるためです。

<!-- The `dataclasses` module actually raises an error in this case, indicating that you should use the `default_factory` argument to `dataclasses.field`. -->
この場合、`dataclasses`モジュールは実際にはエラーを発生し、`dataclasses.field`に`default_factory`引数を使用する必要があることを示します。

<!-- Pydantic also supports the use of a [`default_factory`](#fields-with-dynamic-default-values) for non-hashable default values, but it is not required. In the event that the default value is not hashable, Pydantic will deepcopy the default value when creating each instance of the model: -->
Pydanticは、ハッシュ不可能なデフォルト値に対して[`default_factory`](#fields-with-dynamic-default-values)の使用もサポートしていますが、必須ではありません。デフォルト値がハッシュ可能でない場合、Pydanticはモデルの各インスタンスを作成するときにデフォルト値をディープコピーします。

```py
from typing import Dict, List

from pydantic import BaseModel


class Model(BaseModel):
    item_counts: List[Dict[str, int]] = [{}]


m1 = Model()
m1.item_counts[0]['a'] = 1
print(m1.item_counts)
#> [{'a': 1}]

m2 = Model()
print(m2.item_counts)
#> [{}]
```

## Fields with dynamic default values

<!-- When declaring a field with a default value, you may want it to be dynamic (i.e. different for each model).
To do this, you may want to use a `default_factory`. -->
デフォルト値を使用してフィールドを宣言する場合は、そのフィールドを動的(つまり、モデルごとに異なる)にすることができます。
これを行うには、`default_factory`を使用します。

<!-- Here is an example: -->
次に例を示します。

```py
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def datetime_now() -> datetime:
    return datetime.now(timezone.utc)


class Model(BaseModel):
    uid: UUID = Field(default_factory=uuid4)
    updated: datetime = Field(default_factory=datetime_now)


m1 = Model()
m2 = Model()
assert m1.uid != m2.uid
```

<!-- You can find more information in the documentation of the [`Field` function](fields.md). -->
詳細については、[`Field` function](fields.md)のドキュメントを参照してください。

## Automatically excluded attributes

### Class vars

<!-- Attributes annotated with `typing.ClassVar` are properly treated by Pydantic as class variables, and will not become fields on model instances: -->
`typing.ClassVar`で注釈が付けられた属性は、Pydanticによってクラス変数として適切に扱われ、モデルインスタンスのフィールドにはなりません。

```py
from typing import ClassVar

from pydantic import BaseModel


class Model(BaseModel):
    x: int = 2
    y: ClassVar[int] = 1


m = Model()
print(m)
#> x=2
print(Model.y)
#> 1
```

### Private model attributes

??? api "API Documentation"
    [`pydantic.fields.PrivateAttr`][pydantic.fields.PrivateAttr]<br>

<!-- Attributes whose name has a leading underscore are not treated as fields by Pydantic, and are not included in the model schema. Instead, these are converted into a "private attribute" which is not validated or even set during calls to `__init__`, `model_validate`, etc. -->
名前の先頭にアンダースコアが付いている属性は、Pydanticではフィールドとして扱われず、モデルスキーマにも含まれません。代わりに、これらは"プライベート属性"に変換されます。この属性は検証されず、`__init__`、`model_validate`などの呼び出し時にも設定されません。

!!! note
    <!--
    As of Pydantic v2.1.0, you will receive a NameError if trying to use the [`Field` function](fields.md) with a private attribute.
    Because private attributes are not treated as fields, the Field() function cannot be applied.
    -->
    Pydantic v2.1.0では、private属性で[`Field`関数](fields.md)を使用しようとすると、NameErrorを受け取ります。
    プライベート属性はフィールドとして扱われないため、Field()関数は適用できません。

<!-- Here is an example of usage: -->
次に使用例を示します。

```py
from datetime import datetime
from random import randint

from pydantic import BaseModel, PrivateAttr


class TimeAwareModel(BaseModel):
    _processed_at: datetime = PrivateAttr(default_factory=datetime.now)
    _secret_value: str

    def __init__(self, **data):
        super().__init__(**data)
        # this could also be done with default_factory
        self._secret_value = randint(1, 5)


m = TimeAwareModel()
print(m._processed_at)
#> 2032-01-02 03:04:05.000006
print(m._secret_value)
#> 3
```

<!-- Private attribute names must start with underscore to prevent conflicts with model fields. However, dunder names (such as `__attr__`) are not supported. -->
モデルフィールドとの競合を避けるため、プライベート属性名はアンダースコアで始める必要があります。ただし、名前(`__attr__`など)はサポートされていません。

## Data conversion

<!-- Pydantic may cast input data to force it to conform to model field types, and in some cases this may result in a loss of information.
For example: -->
Pydanticは入力データをキャストして、モデルのフィールド型に強制的に準拠させることがあり、場合によっては情報が失われることがあります。
次に例を示します。

```py
from pydantic import BaseModel


class Model(BaseModel):
    a: int
    b: float
    c: str


print(Model(a=3.000, b='2.72', c=b'binary data').model_dump())
#> {'a': 3, 'b': 2.72, 'c': 'binary data'}
```

<!-- This is a deliberate decision of Pydantic, and is frequently the most useful approach. See [here](https://github.com/pydantic/pydantic/issues/578) for a longer discussion on the subject. -->
これはPydanticの意図的な決定であり、多くの場合、最も有用なアプローチである。このテーマに関するより長い議論については、[ここ](https://github.com/pydantic/pydantic/issues/578)を参照してください。

<!-- Nevertheless, [strict type checking](strict_mode.md) is also supported. -->
ただし、[strict type checking](strict_mode.md)もサポートされています。

## Model signature

<!-- All Pydantic models will have their signature generated based on their fields: -->
すべてのPydanticモデルは、そのフィールドに基づいて生成されたシグネチャを持ちます。

```py
import inspect

from pydantic import BaseModel, Field


class FooModel(BaseModel):
    id: int
    name: str = None
    description: str = 'Foo'
    apple: int = Field(alias='pear')


print(inspect.signature(FooModel))
#> (*, id: int, name: str = None, description: str = 'Foo', pear: int) -> None
```

<!-- An accurate signature is useful for introspection purposes and libraries like `FastAPI` or `hypothesis`. -->
正確な署名は、イントロスペクションの目的や、`FastAPI`や`hypothesis`のようなライブラリに役立ちます。

<!-- The generated signature will also respect custom `__init__` functions: -->
生成された署名は、カスタムの`__init__`関数も考慮します。

```py
import inspect

from pydantic import BaseModel


class MyModel(BaseModel):
    id: int
    info: str = 'Foo'

    def __init__(self, id: int = 1, *, bar: str, **data) -> None:
        """My custom init!"""
        super().__init__(id=id, bar=bar, **data)


print(inspect.signature(MyModel))
#> (id: int = 1, *, bar: str, info: str = 'Foo') -> None
```

<!-- To be included in the signature, a field's alias or name must be a valid Python identifier.
Pydantic will prioritize a field's alias over its name when generating the signature, but may use the field name if the alias is not a valid Python identifier. -->
シグネチャに含めるフィールドのエイリアスまたは名前は、有効なPython識別子である必要があります。
Pydanticは、シグネチャを生成するときにフィールドの名前よりもエイリアスを優先しますが、エイリアスが有効なPython識別子でない場合はフィールド名を使用することができます。

<!-- If a field's alias and name are _both_ not valid identifiers (which may be possible through exotic use of `create_model`), a `**data` argument will be added. In addition, the `**data` argument will always be present in the signature if `model_config['extra'] == 'allow'`. -->
フィールドの別名と名前の両方が有効な識別子でない場合(これは`create_model`の特殊な使い方によって可能になるかもしれません)、`**data`引数が追加されます。さらに、`model_config['extra']=='allow'`の場合、`**data`引数は常にシグネチャに存在します。

## Structural pattern matching

<!-- Pydantic supports structural pattern matching for models, as introduced by [PEP 636](https://peps.python.org/pep-0636/) in Python 3.10. -->
Pydanticは、Python 3.10の[PEP 636](https://peps.python.org/pep-0636/)で導入されたモデルの構造パターンマッチングをサポートしています。

```py requires="3.10" lint="skip"
from pydantic import BaseModel


class Pet(BaseModel):
    name: str
    species: str


a = Pet(name='Bones', species='dog')

match a:
    # match `species` to 'dog', declare and initialize `dog_name`
    case Pet(species='dog', name=dog_name):
        print(f'{dog_name} is a dog')
#> Bones is a dog
    # default case
    case _:
        print('No dog matched')
```

!!! note
    <!-- A match-case statement may seem as if it creates a new model, but don't be fooled;
    it is just syntactic sugar for getting an attribute and either comparing it or declaring and initializing it. -->
    match-case文は、新しいモデルを作成するように見えますが、騙されてはいけません。
    単にアトリビュートを取得して比較したり、宣言して初期化したりするための糖衣構文です。

## Attribute copies

In many cases, arguments passed to the constructor will be copied in order to perform validation and, where necessary, coercion.
多くの場合、コンストラクタに渡された引数は、検証と、必要に応じて強制型変換を実行するためにコピーされます。

<!-- In this example, note that the ID of the list changes after the class is constructed because it has been copied during validation: -->
この例では、検証中にコピーされたため、クラスの構築後にリストのIDが変更されることに注意してください。

```py
from typing import List

from pydantic import BaseModel


class C1:
    arr = []

    def __init__(self, in_arr):
        self.arr = in_arr


class C2(BaseModel):
    arr: List[int]


arr_orig = [1, 9, 10, 3]


c1 = C1(arr_orig)
c2 = C2(arr=arr_orig)
print('id(c1.arr) == id(c2.arr):', id(c1.arr) == id(c2.arr))
#> id(c1.arr) == id(c2.arr): False
```

!!! note
    <!-- There are some situations where Pydantic does not copy attributes, such as when passing models &mdash; we use the model as is. You can override this behaviour by setting [`model_config['revalidate_instances'] = 'always'`](../api/config.md#pydantic.config.ConfigDict). -->
    モデルを渡すときなど、Pydanticが属性をコピーしない場合があります。モデルをそのまま使用します。この動作は、[`model_config['revalidate_instances'] = 'always'`](../api/config.md#pydantic.config.ConfigDict)を設定することで上書きできます。

## Extra fields

<!-- By default, Pydantic models won't error when you provide data for unrecognized fields, they will just be ignored: -->
デフォルトでは、Pydanticモデルは、認識されないフィールドのデータを提供してもエラーにならず、単に無視されるだけです。

```py
from pydantic import BaseModel


class Model(BaseModel):
    x: int


m = Model(x=1, y='a')
assert m.model_dump() == {'x': 1}
```

<!-- If you want this to raise an error, you can achieve this via `model_config`: -->
これによってエラーを発生させたい場合は、`model_config`を使用してこれを実行できます。

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    x: int

    model_config = ConfigDict(extra='forbid')


try:
    Model(x=1, y='a')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model
    y
      Extra inputs are not permitted [type=extra_forbidden, input_value='a', input_type=str]
    """
```

<!-- To instead preserve any extra data provided, you can set `extra='allow'`.
The extra fields will then be stored in `BaseModel.__pydantic_extra__`: -->
提供された追加データを保持するには、`extra='allow'`と設定します。
追加されたフィールドは`BaseModel.__pydantic_extra__`に保存されます。

```py
from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    x: int

    model_config = ConfigDict(extra='allow')


m = Model(x=1, y='a')
assert m.__pydantic_extra__ == {'y': 'a'}
```

<!-- By default, no validation will be applied to these extra items, but you can set a type for the values by overriding the type annotation for `__pydantic_extra__`: -->
デフォルトでは、これらの追加項目に検証は適用されませんが、`__pydantic_extra__`の型注釈をオーバーライドすることで、値の型を設定できます。

```py
from typing import Dict

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Model(BaseModel):
    __pydantic_extra__: Dict[str, int] = Field(init=False)  # (1)!

    x: int

    model_config = ConfigDict(extra='allow')


try:
    Model(x=1, y='a')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model
    y
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """

m = Model(x=1, y='2')
assert m.x == 1
assert m.y == 2
assert m.model_dump() == {'x': 1, 'y': 2}
assert m.__pydantic_extra__ == {'y': 2}
```

<!-- 1. The `= Field(init=False)` does not have any effect at runtime, but prevents the `__pydantic_extra__` field from being treated as an argument to the model's `__init__` method by type-checkers. -->
1. `=Field(init=False)`は実行時には何の効果もありませんが、`__pydantic_extra__`フィールドが型チェッカーによってモデルの`__init__`メソッドの引数として扱われるのを防ぎます。

<!-- The same configurations apply to `TypedDict` and `dataclass`' except the config is controlled by setting the `__pydantic_config__` attribute of the class to a valid `ConfigDict`. -->
同じ設定が`TypedDict`と`dataclass`'にも適用されますが、クラスの`__pydantic_config__`属性を有効な`ConfigDict`に設定することで設定が制御される点が異なります。
