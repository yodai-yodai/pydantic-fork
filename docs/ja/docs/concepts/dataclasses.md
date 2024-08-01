{% include-markdown "../warning.md" %}

??? api "API Documentation"
    [`pydantic.dataclasses.dataclass`][pydantic.dataclasses.dataclass]<br>

<!-- If you don't want to use Pydantic's `BaseModel` you can instead get the same data validation on standard [dataclasses](https://docs.python.org/3/library/dataclasses.html) (introduced in Python 3.7). -->
Pydanticの`BaseModel`を使用したくない場合は、代わりに標準の[dataclasses](https://docs.python.org/3/library/dataclasses.html)(Python 3.7で導入)で同じデータ検証を行うことができます。

```py
from datetime import datetime

from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    signup_ts: datetime = None


user = User(id='42', signup_ts='2032-06-21T12:00')
print(user)
"""
User(id=42, name='John Doe', signup_ts=datetime.datetime(2032, 6, 21, 12, 0))
"""
```

!!! note
    <!-- Keep in mind that `pydantic.dataclasses.dataclass` is **not** a replacement for `pydantic.BaseModel`.
    `pydantic.dataclasses.dataclass` provides a similar functionality to `dataclasses.dataclass` with the addition of Pydantic validation.
    There are cases where subclassing `pydantic.BaseModel` is the better choice. -->
    `pydantic.dataclasses.dataclass`は`pydantic.BaseModel`の置き換え**では**ないことに注意してください。
    `pydantic.dataclasses.dataclass`は、`dataclasses.dataclass`と同様の機能を提供しますが、Pydantic検証が追加されています。
    `pydantic.BaseModel`をサブクラス化した方が良い場合もあります。

    <!-- For more information and discussion see [pydantic/pydantic#710](https://github.com/pydantic/pydantic/issues/710). -->
    詳細な情報と議論については、[pydantic/pydantic#710](https://github.com/pydantic/pydantic/issues/710)を参照。

<!-- Some differences between Pydantic dataclasses and `BaseModel` include: -->
Pydanticのデータクラスと`BaseModel`の違いは以下のとおりです。

<!-- *  How [initialization hooks](#initialization-hooks) work
*  [JSON dumping](#json-dumping) -->
* [initialization hooks](#initialization-hooks)の動作
* [JSON dumping](#json-dumping)

<!-- You can use all the standard Pydantic field types. Note, however, that arguments passed to constructor will be copied in order to perform validation and, where necessary coercion. -->
標準のPydanticフィールド型をすべて使用することができます。ただし、コンストラクタに渡された引数は、検証や必要に応じて強制を実行するためにコピーされることに注意してください。

<!-- To perform validation or generate a JSON schema on a Pydantic dataclass, you should now wrap the dataclass with a [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] and make use of its methods. -->
Pydanticデータクラスの検証やJSONスキーマの生成を行うには、データクラスを[`TypeAdapter`][pydantic.type_adapter.TypeAdapter]でラップし、そのメソッドを利用する必要があります。

<!-- Fields that require a `default_factory` can be specified by either a `pydantic.Field` or a `dataclasses.field`. -->
`default_factory`を必要とするフィールドは、`pydantic.Field`または`dataclasses.field`で指定できます。

```py
import dataclasses
from typing import List, Optional

from pydantic import Field, TypeAdapter
from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    friends: List[int] = dataclasses.field(default_factory=lambda: [0])
    age: Optional[int] = dataclasses.field(
        default=None,
        metadata=dict(title='The age of the user', description='do not lie!'),
    )
    height: Optional[int] = Field(None, title='The height in cm', ge=50, le=300)


user = User(id='42')
print(TypeAdapter(User).json_schema())
"""
{
    'properties': {
        'id': {'title': 'Id', 'type': 'integer'},
        'name': {'default': 'John Doe', 'title': 'Name', 'type': 'string'},
        'friends': {
            'items': {'type': 'integer'},
            'title': 'Friends',
            'type': 'array',
        },
        'age': {
            'anyOf': [{'type': 'integer'}, {'type': 'null'}],
            'default': None,
            'description': 'do not lie!',
            'title': 'The age of the user',
        },
        'height': {
            'anyOf': [
                {'maximum': 300, 'minimum': 50, 'type': 'integer'},
                {'type': 'null'},
            ],
            'default': None,
            'title': 'The height in cm',
        },
    },
    'required': ['id'],
    'title': 'User',
    'type': 'object',
}
"""
```

<!-- `pydantic.dataclasses.dataclass`'s arguments are the same as the standard decorator, except one extra keyword argument `config` which has the same meaning as [model_config][pydantic.config.ConfigDict]. -->
`pydantic.dataclasses.dataclass`の引数は標準デコレータと同じですが、[model_config][pydantic.config.ConfigDict]と同じ意味を持つキーワード引数`config`が1つ追加されています。

!!! warning
    <!-- After v1.2, [The Mypy plugin](../integrations/mypy.md) must be installed to type check _pydantic_ dataclasses. -->
    v1.2以降では、[The Mypy plugin](../integrations/mypy.md)をcheck_pydantic_dataclasses型にインストールする必要があります。



For more information about combining validators with dataclasses, see [dataclass validators](validators.md#dataclass-validators).
バリデータとデータクラスの組み合わせの詳細については、[dataclass validators](validators.md#dataclass-validators)を参照してください。

## Dataclass config

<!-- If you want to modify the `config` like you would with a `BaseModel`, you have two options: -->
`config`を`BaseModel`のように変更したい場合は、2つのオプションがあります。

<!-- * Apply config to the dataclass decorator as a dict
* Use `ConfigDict` as the config -->
* configをデータクラスデコレータにdictとして適用します
* `ConfigDict`を設定として使用します

```py
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


# Option 1 - use directly a dict
# Note: `mypy` will still raise typo error
@dataclass(config=dict(validate_assignment=True))  # (1)!
class MyDataclass1:
    a: int


# Option 2 - use `ConfigDict`
# (same as before at runtime since it's a `TypedDict` but with intellisense)
@dataclass(config=ConfigDict(validate_assignment=True))
class MyDataclass2:
    a: int
```

<!-- 1. You can read more about `validate_assignment` in [API reference][pydantic.config.ConfigDict.validate_assignment]. -->
1. `validate_assignment`の詳細については、[API reference][pydantic.config.ConfigDict.validate_assignment]を参照してください。
!!! note
    <!-- Pydantic dataclasses support [`extra`][pydantic.config.ConfigDict.extra] configuration to `ignore`, `forbid`, or `allow` extra fields passed to the initializer. However, some default behavior of stdlib dataclasses may prevail.
    For example, any extra fields present on a Pydantic dataclass using `extra='allow'` are omitted when the dataclass is `print`ed. -->
    Pydanticデータクラスは、イニシャライザに渡される追加フィールドを`ignore`、`forbid`、`allow`するための[`extra`][pydantic.config.ConfigDict.extra]設定をサポートしています。ただし、stdlibデータクラスのデフォルトの動作が優先される場合があります。
    例えば、`extra='allow'`を使用するPydanticデータクラスに存在する余分なフィールドは、データクラスが`print`されるときに省略されます。

## Nested dataclasses

<!-- Nested dataclasses are supported both in dataclasses and normal models. -->
ネストされたデータクラスは、データクラスと通常のモデルの両方でサポートされます。

```py
from pydantic import AnyUrl
from pydantic.dataclasses import dataclass


@dataclass
class NavbarButton:
    href: AnyUrl


@dataclass
class Navbar:
    button: NavbarButton


navbar = Navbar(button={'href': 'https://example.com'})
print(navbar)
#> Navbar(button=NavbarButton(href=Url('https://example.com/')))
```

<!-- When used as fields, dataclasses (Pydantic or vanilla) should use dicts as validation inputs. -->
フィールドとして使用する場合、データ・クラス(Pydanticまたはvanilla)は検証入力としてディクテーションを使用する必要があります。

## Generic dataclasses

<!-- Pydantic supports generic dataclasses, including those with type variables. -->
Pydanticは、型変数を持つものを含む汎用データクラスをサポートしています。

```py
from typing import Generic, TypeVar

from pydantic import TypeAdapter
from pydantic.dataclasses import dataclass

T = TypeVar('T')


@dataclass
class GenericDataclass(Generic[T]):
    x: T


validator = TypeAdapter(GenericDataclass)

assert validator.validate_python({'x': None}).x is None
assert validator.validate_python({'x': 1}).x == 1
assert validator.validate_python({'x': 'a'}).x == 'a'
```

<!-- Note that, if you use the dataclass as a field of a `BaseModel` or via FastAPI you don't need a `TypeAdapter`. -->
`BaseModel`のフィールドとして、またはFastAPI経由でデータクラスを使用する場合、`TypeAdapter`は必要ないことに注意してください。

## Stdlib dataclasses and Pydantic dataclasses

### Inherit from stdlib dataclasses

<!-- Stdlib dataclasses (nested or not) can also be inherited and Pydantic will automatically validate all the inherited fields. -->
Stdlibデータクラス(ネストされているかどうかにかかわらず)も継承でき、Pydanticは継承されたすべてのフィールドを自動的に検証します。

```py
import dataclasses

import pydantic


@dataclasses.dataclass
class Z:
    z: int


@dataclasses.dataclass
class Y(Z):
    y: int = 0


@pydantic.dataclasses.dataclass
class X(Y):
    x: int = 0


foo = X(x=b'1', y='2', z='3')
print(foo)
#> X(z=3, y=2, x=1)

try:
    X(z='pika')
except pydantic.ValidationError as e:
    print(e)
    """
    1 validation error for X
    z
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='pika', input_type=str]
    """
```

### Use of stdlib dataclasses with `BaseModel`

<!-- Bear in mind that stdlib dataclasses (nested or not) are **automatically converted** into Pydantic dataclasses when mixed with `BaseModel`! Furthermore the generated Pydantic dataclass will have the **exact same configuration** (`order`, `frozen`, ...) as the original one. -->
stdlibデータクラス(ネストされているかどうかにかかわらず)は、`BaseModel`と混合されると、Pydanticデータクラスに**自動的に変換**されることに注意してください!
さらに、生成されたPydanticデータクラスは、元のものと**まったく同じ構成**(`order`、`frozen`、...)になります。

```py
import dataclasses
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, ValidationError


@dataclasses.dataclass(frozen=True)
class User:
    name: str


@dataclasses.dataclass
class File:
    filename: str
    last_modification_time: Optional[datetime] = None


class Foo(BaseModel):
    # Required so that pydantic revalidates the model attributes
    model_config = ConfigDict(revalidate_instances='always')

    file: File
    user: Optional[User] = None


file = File(
    filename=['not', 'a', 'string'],
    last_modification_time='2020-01-01T00:00',
)  # nothing is validated as expected
print(file)
"""
File(filename=['not', 'a', 'string'], last_modification_time='2020-01-01T00:00')
"""

try:
    Foo(file=file)
except ValidationError as e:
    print(e)
    """
    1 validation error for Foo
    file.filename
      Input should be a valid string [type=string_type, input_value=['not', 'a', 'string'], input_type=list]
    """

foo = Foo(file=File(filename='myfile'), user=User(name='pika'))
try:
    foo.user.name = 'bulbi'
except dataclasses.FrozenInstanceError as e:
    print(e)
    #> cannot assign to field 'name'
```

### Use custom types

<!-- Since stdlib dataclasses are automatically converted to add validation, using custom types may cause some unexpected behavior. -->
<!-- In this case you can simply add `arbitrary_types_allowed` in the config! -->
stdlibデータクラスは検証を追加するために自動的に変換されるため、カスタム型を使用すると予期しない動作が発生する可能性があります。
この場合は単に`arbitrary_types_allowed`を設定に追加すればよいのです!

```py
import dataclasses

from pydantic import BaseModel, ConfigDict
from pydantic.errors import PydanticSchemaGenerationError


class ArbitraryType:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'ArbitraryType(value={self.value!r})'


@dataclasses.dataclass
class DC:
    a: ArbitraryType
    b: str


# valid as it is a builtin dataclass without validation
my_dc = DC(a=ArbitraryType(value=3), b='qwe')

try:

    class Model(BaseModel):
        dc: DC
        other: str

    # invalid as it is now a pydantic dataclass
    Model(dc=my_dc, other='other')
except PydanticSchemaGenerationError as e:
    print(e.message)
    """
    Unable to generate pydantic-core schema for <class '__main__.ArbitraryType'>. Set `arbitrary_types_allowed=True` in the model_config to ignore this error or implement `__get_pydantic_core_schema__` on your type to fully support it.

    If you got this error by calling handler(<some type>) within `__get_pydantic_core_schema__` then you likely need to call `handler.generate_schema(<some type>)` since we do not call `__get_pydantic_core_schema__` on `<some type>` otherwise to avoid infinite recursion.
    """


class Model(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dc: DC
    other: str


m = Model(dc=my_dc, other='other')
print(repr(m))
#> Model(dc=DC(a=ArbitraryType(value=3), b='qwe'), other='other')
```

### Checking if a dataclass is a pydantic dataclass

<!-- Pydantic dataclasses are still considered dataclasses, so using `dataclasses.is_dataclass` will return `True`. To check if a type is specifically a pydantic dataclass you can use `pydantic.dataclasses.is_pydantic_dataclass`. -->
Pydanticデータクラスは今でもデータクラスとみなされるので、`dataclasses.is_dataclass`を使用すると`True`が返されます。型が特にpydanticデータクラスであるかどうかを確認するには、`pydantic.dataclasses.is_pydantic_dataclass`を使用します。

```py
import dataclasses

import pydantic


@dataclasses.dataclass
class StdLibDataclass:
    id: int


PydanticDataclass = pydantic.dataclasses.dataclass(StdLibDataclass)

print(dataclasses.is_dataclass(StdLibDataclass))
#> True
print(pydantic.dataclasses.is_pydantic_dataclass(StdLibDataclass))
#> False

print(dataclasses.is_dataclass(PydanticDataclass))
#> True
print(pydantic.dataclasses.is_pydantic_dataclass(PydanticDataclass))
#> True
```

## Initialization hooks

<!-- When you initialize a dataclass, it is possible to execute code *before* or *after* validation with the help of the [`@model_validator`](validators.md#model-validators) decorator `mode` parameter. -->
データクラスを初期化する場合、[`@model_validator`](validators.md#model-validators)デコレータの`mode`パラメータを使用して、検証の*前*または*後*にコードを実行できます。

```py
from typing import Any, Dict

from typing_extensions import Self

from pydantic import model_validator
from pydantic.dataclasses import dataclass


@dataclass
class Birth:
    year: int
    month: int
    day: int


@dataclass
class User:
    birth: Birth

    @model_validator(mode='before')
    @classmethod
    def pre_root(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        print(f'First: {values}')
        """
        First: ArgsKwargs((), {'birth': {'year': 1995, 'month': 3, 'day': 2}})
        """
        return values

    @model_validator(mode='after')
    def post_root(self) -> Self:
        print(f'Third: {self}')
        #> Third: User(birth=Birth(year=1995, month=3, day=2))
        return self

    def __post_init__(self):
        print(f'Second: {self.birth}')
        #> Second: Birth(year=1995, month=3, day=2)


user = User(**{'birth': {'year': 1995, 'month': 3, 'day': 2}})
```

<!-- The `__post_init__` in Pydantic dataclasses is called in the _middle_ of validators. -->
<!-- Here is the order: -->
Pydanticデータクラスの`__post_init__`はバリデータの_middle_で呼び出されます。
オーダーは以下の通りです。

* `model_validator(mode='before')`
* `field_validator(mode='before')`
* `field_validator(mode='after')`
<!-- * Inner validators. e.g. validation for types like `int`, `str`, ... -->
*内部バリデータ。例えば、`int`、`str`、..のような型の検証。
* `__post_init__`.
* `model_validator(mode='after')`


```py requires="3.8"
from dataclasses import InitVar
from pathlib import Path
from typing import Optional

from pydantic.dataclasses import dataclass


@dataclass
class PathData:
    path: Path
    base_path: InitVar[Optional[Path]]

    def __post_init__(self, base_path):
        print(f'Received path={self.path!r}, base_path={base_path!r}')
        #> Received path=PosixPath('world'), base_path=PosixPath('/hello')
        if base_path is not None:
            self.path = base_path / self.path


path_data = PathData('world', base_path='/hello')
# Received path='world', base_path='/hello'
assert path_data.path == Path('/hello/world')
```

### Difference with stdlib dataclasses

<!-- Note that the `dataclasses.dataclass` from Python stdlib implements only the `__post_init__` method since it doesn't run a validation step. -->
Python stdlibの`dataclasses.dataclass`は検証ステップを実行しないので、`__post_init__`メソッドしか実装していないことに注意してください。

## JSON dumping

<!-- Pydantic dataclasses do not feature a `.model_dump_json()` function. To dump them as JSON, you will need to make use of the [RootModel](models.md#rootmodel-and-custom-root-types) as follows: -->
Pydanticデータクラスには`.model_dump_json()`関数がありません。JSONとしてダンプするには、次のように[RootModel](models.md#RootModel-and-custom-root-types)を使用する必要があります。

```py output="json"
import dataclasses
from typing import List

from pydantic import RootModel
from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    friends: List[int] = dataclasses.field(default_factory=lambda: [0])


user = User(id='42')
print(RootModel[User](User(id='42')).model_dump_json(indent=4))
"""
{
    "id": 42,
    "name": "John Doe",
    "friends": [
        0
    ]
}
"""
```
