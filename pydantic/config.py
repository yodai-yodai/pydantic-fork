# """Configuration for Pydantic models."""
"""Pydanticモデルの設定"""

from __future__ import annotations as _annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Type, TypeVar, Union

from typing_extensions import Literal, TypeAlias, TypedDict

from ._migration import getattr_migration
from .aliases import AliasGenerator
from .errors import PydanticUserError

if TYPE_CHECKING:
    from ._internal._generate_schema import GenerateSchema as _GenerateSchema
    from .fields import ComputedFieldInfo, FieldInfo

__all__ = ("ConfigDict", "with_config")


JsonValue: TypeAlias = Union[int, float, str, bool, None, List["JsonValue"], "JsonDict"]
JsonDict: TypeAlias = Dict[str, JsonValue]

JsonEncoder = Callable[[Any], Any]

JsonSchemaExtraCallable: TypeAlias = Union[
    Callable[[JsonDict], None],
    Callable[[JsonDict, Type[Any]], None],
]

ExtraValues = Literal["allow", "ignore", "forbid"]


class ConfigDict(TypedDict, total=False):
    # """A TypedDict for configuring Pydantic behaviour."""
    """Pydanticの動作を設定するためのTypedDict"""

    title: str | None
    # """The title for the generated JSON schema, defaults to the model's name"""
    """生成されたJSONスキーマのタイトル。デフォルトはモデルの名前です"""

    model_title_generator: Callable[[type], str] | None
    # """A callable that takes a model class and returns the title for it. Defaults to `None`."""
    """モデルクラスを受け取り、そのタイトルを返す呼び出し可能オブジェクト。デフォルトは`None`です。"""

    field_title_generator: Callable[[str, FieldInfo | ComputedFieldInfo], str] | None
    # """A callable that takes a field's name and info and returns title for it. Defaults to `None`."""
    """フィールドの名前と情報を受け取り、そのタイトルを返す呼び出し可能オブジェクト。デフォルトは`None`です。"""

    str_to_lower: bool
    # """Whether to convert all characters to lowercase for str types. Defaults to `False`."""
    """str型のすべての文字を小文字に変換するかどうか。デフォルトは`False`です。"""

    str_to_upper: bool
    # """Whether to convert all characters to uppercase for str types. Defaults to `False`."""
    """str型のすべての文字を大文字に変換するかどうか。デフォルトは`False`です。"""

    str_strip_whitespace: bool
    # """Whether to strip leading and trailing whitespace for str types."""
    """str型の先頭と末尾の空白を削除するかどうか。"""

    str_min_length: int
    # """The minimum length for str types. Defaults to `None`."""
    """str型の最小長。デフォルトは`None`です。"""

    str_max_length: int | None
    # """The maximum length for str types. Defaults to `None`."""
    """str型の最大長。デフォルトは`None`です。"""

    extra: ExtraValues | None
    """
    # Whether to ignore, allow, or forbid extra attributes during model initialization. Defaults to `'ignore'`.
    モデルの初期化中に追加属性を無視するか、許可するか、禁止するか。デフォルトは`'ignore'`です。

    # You can configure how pydantic handles the attributes that are not defined in the model:
    モデルで定義されていない属性をpydanticが処理する方法を設定できます。

    # * `allow` - Allow any extra attributes.
    # * `forbid` - Forbid any extra attributes.
    # * `ignore` - Ignore any extra attributes.
    * `allow` - 追加の属性を許可します。
    * `forbid` - 余分な属性を禁止します。
    * `ignore` - 余分な属性を無視します。

    ```py
    from pydantic import BaseModel, ConfigDict


    class User(BaseModel):
        model_config = ConfigDict(extra='ignore')  # (1)!

        name: str


    user = User(name='John Doe', age=20)  # (2)!
    print(user)
    #> name='John Doe'
    ```

    # 1. This is the default behaviour.
    # 2. The `age` argument is ignored.
    1. これがデフォルトの動作です。
    2. `age`引数は無視されます。

    # Instead, with `extra='allow'`, the `age` argument is included:
    代わりに、`extra='allow'`を指定すると`age`引数が含まれます。

    ```py
    from pydantic import BaseModel, ConfigDict


    class User(BaseModel):
        model_config = ConfigDict(extra='allow')

        name: str


    user = User(name='John Doe', age=20)  # (1)!
    print(user)
    #> name='John Doe' age=20
    ```

    # 1. The `age` argument is included.
    1. `age`引数が含まれます。

    # With `extra='forbid'`, an error is raised:
    `extra='forbid'`を指定すると、エラーが発生します。

    ```py
    from pydantic import BaseModel, ConfigDict, ValidationError


    class User(BaseModel):
        model_config = ConfigDict(extra='forbid')

        name: str


    try:
        User(name='John Doe', age=20)
    except ValidationError as e:
        print(e)
        '''
        1 validation error for User
        age
        Extra inputs are not permitted [type=extra_forbidden, input_value=20, input_type=int]
        '''
    ```
    """

    frozen: bool
    """
    # Whether models are faux-immutable, i.e. whether `__setattr__` is allowed, and also generates a `__hash__()` method for the model. This makes instances of the model potentially hashable if all the attributes are hashable. Defaults to `False`.
    モデルが疑似不変かどうか、つまり`__setattr__`が許可されているかどうか。また、モデルの`__hash__()`メソッドを生成します。これにより、すべての属性がハッシュ可能であれば、モデルのインスタンスがハッシュ可能になります。デフォルトは`False`です。

    Note:
        # On V1, the inverse of this setting was called `allow_mutation`, and was `True` by default.
        V1では、この設定の逆は`allow_mutation`と呼ばれ、デフォルトでは`True`でした。
    """

    populate_by_name: bool
    """
    # Whether an aliased field may be populated by its name as given by the model attribute, as well as the alias. Defaults to `False`.
    別名フィールドに、モデル属性で指定された名前と別名を入力できるかどうかを指定します。既定値は`False`です。

    Note:
        # The name of this configuration setting was changed in **v2.0** from `allow_population_by_field_name` to `populate_by_name`.
        この構成設定の名前は、**v2.0**で`allow_population_by_field_name`から`populate_by_name`に変更されました。

    ```py
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        name: str = Field(alias='full_name')  # (1)!
        age: int


    user = User(full_name='John Doe', age=20)  # (2)!
    print(user)
    #> name='John Doe' age=20
    user = User(name='John Doe', age=20)  # (3)!
    print(user)
    #> name='John Doe' age=20
    ```

    # 1. The field `'name'` has an alias `'full_name'`.
    # 2. The model is populated by the alias `'full_name'`.
    # 3. The model is populated by the field name `'name'`.
    1. フィールド"name"にはエイリアス"full_name"があります。
    2. モデルは、エイリアス`'full_name'`によって作成されます。
    3. モデルには、フィールド名"name"が入力されます。
    """

    use_enum_values: bool
    """
    # Whether to populate models with the `value` property of enums, rather than the raw enum.
    # This may be useful if you want to serialize `model.model_dump()` later. Defaults to `False`.
    生の列挙型ではなく、列挙型の`value`プロパティをモデルに設定するかどうか。
    これは`model.model_dump()`を後でシリアライズしたい場合に便利です。デフォルトは`False`です。

    !!! note
        # If you have an `Optional[Enum]` value that you set a default for, you need to use `validate_default=True` for said Field to ensure that the `use_enum_values` flag takes effect on the default, as extracting an enum's value occurs during validation, not serialization.
        デフォルトを設定する`Optional[Enum]`値がある場合は、そのフィールドに`validate_default=True`を使用して、`use_enum_values`フラグがデフォルトに対して有効になるようにする必要があります。これは、列挙型の値の抽出はシリアライゼーションではなく検証中に行われるためです。

    ```py
    from enum import Enum
    from typing import Optional

    from pydantic import BaseModel, ConfigDict, Field


    class SomeEnum(Enum):
        FOO = 'foo'
        BAR = 'bar'
        BAZ = 'baz'


    class SomeModel(BaseModel):
        model_config = ConfigDict(use_enum_values=True)

        some_enum: SomeEnum
        another_enum: Optional[SomeEnum] = Field(default=SomeEnum.FOO, validate_default=True)


    model1 = SomeModel(some_enum=SomeEnum.BAR)
    print(model1.model_dump())
    # {'some_enum': 'bar', 'another_enum': 'foo'}

    model2 = SomeModel(some_enum=SomeEnum.BAR, another_enum=SomeEnum.BAZ)
    print(model2.model_dump())
    #> {'some_enum': 'bar', 'another_enum': 'baz'}
    ```
    """

    validate_assignment: bool
    """
    # Whether to validate the data when the model is changed. Defaults to `False`.
    モデルが変更されたときにデータを検証するかどうか。デフォルトは`False`です。

    # The default behavior of Pydantic is to validate the data when the model is created.
    Pydanticのデフォルトの動作は、モデルの作成時にデータを検証することです。

    # In case the user changes the data after the model is created, the model is _not_ revalidated.
    モデルの作成後にユーザーがデータを変更した場合、モデルは再検証されません。

    ```py
    from pydantic import BaseModel

    class User(BaseModel):
        name: str

    user = User(name='John Doe')  # (1)!
    print(user)
    #> name='John Doe'
    user.name = 123  # (1)!
    print(user)
    #> name=123
    ```

    # 1. The validation happens only when the model is created.
    # 2. The validation does not happen when the data is changed.
    1. 検証は、モデルの作成時にのみ行われます。
    2. データが変更されても、検証は行われません。

    # In case you want to revalidate the model when the data is changed, you can use `validate_assignment=True`:
    データが変更されたときにモデルを再検証したい場合は、`validate_assignment=True`を使用します。

    ```py
    from pydantic import BaseModel, ValidationError

    class User(BaseModel, validate_assignment=True):  # (1)!
        name: str

    user = User(name='John Doe')  # (2)!
    print(user)
    #> name='John Doe'
    try:
        user.name = 123  # (3)!
    except ValidationError as e:
        print(e)
        '''
        1 validation error for User
        name
          Input should be a valid string [type=string_type, input_value=123, input_type=int]
        '''
    ```

    # 1. You can either use class keyword arguments, or `model_config` to set `validate_assignment=True`.
    # 2. The validation happens when the model is created.
    # 3. The validation _also_ happens when the data is changed.
    1. クラスキーワード引数を使用するか、`model_config`を使用して`validate_assignment=True`を設定できます。
    2. モデルの作成時に検証が行われます。
    3. データが変更されると、validation_also_が発生します。
    """

    arbitrary_types_allowed: bool
    """
    # Whether arbitrary types are allowed for field types. Defaults to `False`.
    フィールド型に任意の型を許可するかどうか。デフォルトは`False`です。

    ```py
    from pydantic import BaseModel, ConfigDict, ValidationError

    # This is not a pydantic model, it's an arbitrary class
    class Pet:
        def __init__(self, name: str):
            self.name = name

    class Model(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

        pet: Pet
        owner: str

    pet = Pet(name='Hedwig')
    # A simple check of instance type is used to validate the data
    model = Model(owner='Harry', pet=pet)
    print(model)
    #> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
    print(model.pet)
    #> <__main__.Pet object at 0x0123456789ab>
    print(model.pet.name)
    #> Hedwig
    print(type(model.pet))
    #> <class '__main__.Pet'>
    try:
        # If the value is not an instance of the type, it's invalid
        Model(owner='Harry', pet='Hedwig')
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        pet
          Input should be an instance of Pet [type=is_instance_of, input_value='Hedwig', input_type=str]
        '''

    # Nothing in the instance of the arbitrary type is checked
    # Here name probably should have been a str, but it's not validated
    pet2 = Pet(name=42)
    model2 = Model(owner='Harry', pet=pet2)
    print(model2)
    #> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
    print(model2.pet)
    #> <__main__.Pet object at 0x0123456789ab>
    print(model2.pet.name)
    #> 42
    print(type(model2.pet))
    #> <class '__main__.Pet'>
    ```
    """

    from_attributes: bool
    """
    # Whether to build models and look up discriminators of tagged unions using python object attributes.
    モデルを構築し、Pythonオブジェクトアトリビュートを使用してタグ付き共用体の識別子を検索するかどうかを指定します。
    """

    loc_by_alias: bool
    # """Whether to use the actual key provided in the data (e.g. alias) for error `loc`s rather than the field's name. Defaults to `True`."""
    """エラー`loc`に対して、フィールド名ではなく、データ内で提供された実際のキー(エイリアスなど)を使用するかどうか。デフォルトは`True`です。"""

    alias_generator: Callable[[str], str] | AliasGenerator | None
    """
    # A callable that takes a field name and returns an alias for it
    # or an instance of [`AliasGenerator`][pydantic.aliases.AliasGenerator]. Defaults to `None`.
    フィールド名を受け取り、そのエイリアスを返す呼び出し可能オブジェクト
    または[`AliasGenerator`][pydantic.aliases.AliasGenerator]のインスタンスです。デフォルトは`None`です。

    # When using a callable, the alias generator is used for both validation and serialization.
    # If you want to use different alias generators for validation and serialization, you can use [`AliasGenerator`][pydantic.aliases.AliasGenerator] instead.
    呼び出し可能オブジェクトを使用する場合、検証とシリアライゼーションの両方にエイリアスジェネレータが使用されます。
    検証とシリアライゼーションに異なるエイリアスジェネレータを使用したい場合は、代わりに[`AliasGenerator`][pydantic.aliases.AliasGenerator]を使用できます。

    # If data source field names do not match your code style (e. g. CamelCase fields), you can automatically generate aliases using `alias_generator`. Here's an example with
    データソースのフィールド名がコードスタイルと一致しない場合(CamelCaseフィールドなど)、`alias_generator`を使用してエイリアスを自動的に生成できます。
    # a basic callable:
    基本呼び出し可能:

    ```py
    from pydantic import BaseModel, ConfigDict
    from pydantic.alias_generators import to_pascal

    class Voice(BaseModel):
        model_config = ConfigDict(alias_generator=to_pascal)

        name: str
        language_code: str

    voice = Voice(Name='Filiz', LanguageCode='tr-TR')
    print(voice.language_code)
    #> tr-TR
    print(voice.model_dump(by_alias=True))
    #> {'Name': 'Filiz', 'LanguageCode': 'tr-TR'}
    ```

    # If you want to use different alias generators for validation and serialization, you can use [`AliasGenerator`][pydantic.aliases.AliasGenerator].
    検証とシリアライゼーションに別のエイリアスジェネレータを使用する場合は、[`AliasGenerator`][pydantic.aliases.AliasGenerator]を使用します。

    ```py
    from pydantic import AliasGenerator, BaseModel, ConfigDict
    from pydantic.alias_generators import to_camel, to_pascal

    class Athlete(BaseModel):
        first_name: str
        last_name: str
        sport: str

        model_config = ConfigDict(
            alias_generator=AliasGenerator(
                validation_alias=to_camel,
                serialization_alias=to_pascal,
            )
        )

    athlete = Athlete(firstName='John', lastName='Doe', sport='track')
    print(athlete.model_dump(by_alias=True))
    #> {'FirstName': 'John', 'LastName': 'Doe', 'Sport': 'track'}
    ```

    Note:
        # Pydantic offers three built-in alias generators: [`to_pascal`][pydantic.alias_generators.to_pascal], [`to_camel`][pydantic.alias_generators.to_camel], and [`to_snake`][pydantic.alias_generators.to_snake].
        Pydanticには、[`to_pascal`][pydantic.alias_generators.to_pascal]、[`to_camel`][pydantic.alias_generators.to_camel]、[`to_snake`][pydantic.alias_generators.to_snake]という3つのエイリアスジェネレータが組み込まれています。
    """

    ignored_types: tuple[type, ...]
    # """A tuple of types that may occur as values of class attributes without annotations.
    # This is typically used for custom descriptors (classes that behave like `property`).
    # If an attribute is set on a class without an annotation and has a type that is not in this tuple (or otherwise recognized by _pydantic_), an error will be raised. Defaults to `()`.
    # ""
    """注釈なしでクラス属性の値として発生する可能性のある型のタプル。
    これは通常、カスタム記述子(`property`のように動作するクラス)に使用されます。
    属性がアノテーションなしでクラスに設定され、その型がこのタプルにない(または_pydantic_で認識されない)場合、エラーが発生します。デフォルトは`()`です。
    """

    allow_inf_nan: bool
    # """Whether to allow infinity (`+inf` an `-inf`) and NaN values to float and decimal fields. Defaults to `True`."""
    """無限値(`+inf`an`-inf`)とNaN値を浮動小数点フィールドと小数フィールドに許可するかどうか。デフォルトは`True`。"""

    json_schema_extra: JsonDict | JsonSchemaExtraCallable | None
    # """A dict or callable to provide extra JSON schema properties. Defaults to `None`."""
    """追加のJSONスキーマプロパティを提供するためのdictまたはcallable。デフォルトは`None`です。"""

    json_encoders: dict[type[object], JsonEncoder] | None
    """
    # A `dict` of custom JSON encoders for specific types. Defaults to `None`.
    特定の型用のカスタムJSONエンコーダの`dict`です。デフォルトは`None`です。

    !!! warning "Deprecated"
        # This config option is a carryover from v1.
        # We originally planned to remove it in v2 but didn't have a 1:1 replacement so we are keeping it for now.
        # It is still deprecated and will likely be removed in the future.
        このconfigオプションはv1からの繰り越しです。
        当初はv2で削除する予定でしたが、1:1の置き換えがなかったので、今のところそのままにしています。
        これはまだ推奨されておらず、将来削除される可能性があります。
    """

    # new in V2
    strict: bool
    """
    # _(new in V2)_ If `True`, strict validation is applied to all fields on the model.
    _(V2の新機能)_`True`の場合、モデルのすべてのフィールドに厳密な検証が適用されます。

    # By default, Pydantic attempts to coerce values to the correct type, when possible.
    デフォルトでは、Pydanticは可能であれば値を正しい型に強制しようとします。

    # There are situations in which you may want to disable this behavior, and instead raise an error if a value's type does not match the field's type annotation.
    場合によっては、この動作を無効にして、値の型がフィールドの型注釈と一致しない場合にエラーを発生させることができます。

    # To configure strict mode for all fields on a model, you can set `strict=True` on the model.
    モデルのすべてのフィールドにstrictモードを設定するには、モデルに`strict=True`を設定します。

    ```py
    from pydantic import BaseModel, ConfigDict

    class Model(BaseModel):
        model_config = ConfigDict(strict=True)

        name: str
        age: int
    ```

    # See [Strict Mode](../concepts/strict_mode.md) for more details.
    詳細については、[Strict Mode](../concepts/strict_mode.md)を参照してください。

    See the [Conversion Table](../concepts/conversion_table.md) for more details on how Pydantic converts data in both strict and lax modes.
    Pydanticがstrictモードとlaxモードの両方でデータを変換する方法の詳細については、[Conversion Table](../concepts/conversion_table.md)を参照してください。
    """
    # whether instances of models and dataclasses (including subclass instances) should re-validate, default 'never'
    revalidate_instances: Literal["always", "never", "subclass-instances"]
    """
    # When and how to revalidate models and dataclasses during validation. Accepts the string values of `'never'`, `'always'` and `'subclass-instances'`. Defaults to `'never'`.
    検証中にモデルとデータクラスをいつ、どのように再検証するか。"never"、"always"、"subclass-instances"の文字列値を受け入れます。デフォルトは"never"です。

    # - `'never'` will not revalidate models and dataclasses during validation
    # - `'always'` will revalidate models and dataclasses during validation
    # - `'subclass-instances'` will revalidate models and dataclasses during validation if the instance is a subclass of the model or dataclass
    - `'never'`は、検証中にモデルとデータクラスを再検証しません。
    - "always"は、検証中にモデルとデータクラスを再検証します。
    - `'subclass-instances'`は、インスタンスがモデルまたはデータクラスのサブクラスである場合、検証中にモデルとデータクラスを再検証します。

    # By default, model and dataclass instances are not revalidated during validation.
    デフォルトでは、モデルとデータクラスのインスタンスは検証中に再検証されません。

    ```py
    from typing import List

    from pydantic import BaseModel

    class User(BaseModel, revalidate_instances='never'):  # (1)!
        hobbies: List[str]

    class SubUser(User):
        sins: List[str]

    class Transaction(BaseModel):
        user: User

    my_user = User(hobbies=['reading'])
    t = Transaction(user=my_user)
    print(t)
    #> user=User(hobbies=['reading'])

    my_user.hobbies = [1]  # (2)!
    t = Transaction(user=my_user)  # (3)!
    print(t)
    #> user=User(hobbies=[1])

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])
    t = Transaction(user=my_sub_user)
    print(t)
    #> user=SubUser(hobbies=['scuba diving'], sins=['lying'])
    ```

    # 1. `revalidate_instances` is set to `'never'` by **default.
    # 2. The assignment is not validated, unless you set `validate_assignment` to `True` in the model's config.
    # 3. Since `revalidate_instances` is set to `never`, this is not revalidated.
    1. `revalidate_instances`は**デフォルトで`'never'`に設定されています。
    2. モデルの設定で`validate_assignment`を`True`に設定しない限り、割り当ては検証されません。
    3. `revalidate_instances`は`never`に設定されているので、これは再検証されません。

    # If you want to revalidate instances during validation, you can set `revalidate_instances` to `'always'` in the model's config.
    検証中にインスタンスを再検証したい場合は、モデルの設定で`revalidate_instances`を`'always'`に設定します。

    ```py
    from typing import List

    from pydantic import BaseModel, ValidationError

    class User(BaseModel, revalidate_instances='always'):  # (1)!
        hobbies: List[str]

    class SubUser(User):
        sins: List[str]

    class Transaction(BaseModel):
        user: User

    my_user = User(hobbies=['reading'])
    t = Transaction(user=my_user)
    print(t)
    #> user=User(hobbies=['reading'])

    my_user.hobbies = [1]
    try:
        t = Transaction(user=my_user)  # (2)!
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Transaction
        user.hobbies.0
          Input should be a valid string [type=string_type, input_value=1, input_type=int]
        '''

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])
    t = Transaction(user=my_sub_user)
    print(t)  # (3)!
    #> user=User(hobbies=['scuba diving'])
    ```

    # 1. `revalidate_instances` is set to `'always'`.
    # 2. The model is revalidated, since `revalidate_instances` is set to `'always'`.
    # 3. Using `'never'` we would have gotten `user=SubUser(hobbies=['scuba diving'], sins=['lying'])`.
    1. `revalidate_instances`が`'always'`に設定されている。
    2. `revalidate_instances`が`'always'`に設定されているので、モデルは再検証されます。
    3. "never"を使用すると、"user=SubUser(hobbies=['scuba diving'],sins=['lying'])"が得られます。

    # It's also possible to set `revalidate_instances` to `'subclass-instances'` to only revalidate instances of subclasses of the model.
    `revalidate_instances`を`'subclass-instances'`に設定して、モデルのサブクラスのインスタンスのみを再検証することもできます。

    ```py
    from typing import List

    from pydantic import BaseModel

    class User(BaseModel, revalidate_instances='subclass-instances'):  # (1)!
        hobbies: List[str]

    class SubUser(User):
        sins: List[str]

    class Transaction(BaseModel):
        user: User

    my_user = User(hobbies=['reading'])
    t = Transaction(user=my_user)
    print(t)
    #> user=User(hobbies=['reading'])

    my_user.hobbies = [1]
    t = Transaction(user=my_user)  # (2)!
    print(t)
    #> user=User(hobbies=[1])

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])
    t = Transaction(user=my_sub_user)
    print(t)  # (3)!
    #> user=User(hobbies=['scuba diving'])
    ```

    # 1. `revalidate_instances` is set to `'subclass-instances'`.
    # 2. This is not revalidated, since `my_user` is not a subclass of `User`.
    # 3. Using `'never'` we would have gotten `user=SubUser(hobbies=['scuba diving'], sins=['lying'])`.
    1. `revalidate_instances`は`'subclass-instances'`に設定されます。
    2. `my_user`は`User`のサブクラスではないので、これは再検証されません。
    3. "never"を使用すると、"user=SubUser(hobbies=['scuba diving'],sins=['lying'])"が得られます。

    """

    ser_json_timedelta: Literal["iso8601", "float"]
    """
    # The format of JSON serialized timedeltas. Accepts the string values of `'iso8601'` and `'float'`. Defaults to `'iso8601'`.
    JSONシリアライズされたタイムデルタのフォーマット。`'iso8601'`および`'float'`の文字列値を受け入れます。デフォルトは`'iso8601'`です。

    # - `'iso8601'` will serialize timedeltas to ISO 8601 durations.
    # - `'float'` will serialize timedeltas to the total number of seconds.
    - `'iso8601'`はtimedeltasをiso8601 durationにシリアライズします。
    - `'float'`はtimedeltaを合計秒数にシリアライズします。
    """

    ser_json_bytes: Literal["utf8", "base64"]
    """
    # The encoding of JSON serialized bytes. Accepts the string values of `'utf8'` and `'base64'`.
    # Defaults to `'utf8'`.
    JSONシリアライズされたバイトのエンコーディング。`'utf8'`と`'base64'`の文字列値を受け入れます。
    デフォルトは`'utf8'`です。

    # - `'utf8'` will serialize bytes to UTF-8 strings.
    # - `'base64'` will serialize bytes to URL safe base64 strings.
    - `'utf8'`はバイトをUTF-8文字列にシリアライズします。
    - `'base64'`はバイトをURLセーフなbase64文字列にシリアライズします。
    """

    ser_json_inf_nan: Literal["null", "constants", "strings"]
    """
    # The encoding of JSON serialized infinity and NaN float values. Defaults to `'null'`.
    JSONシリアライズされたinfinityおよびNaN float値のエンコーディング。デフォルトは`'null'`です。

    # - `'null'` will serialize infinity and NaN values as `null`.
    # - `'constants'` will serialize infinity and NaN values as `Infinity` and `NaN`.
    # - `'strings'` will serialize infinity as string `"Infinity"` and NaN as string `"NaN"`.
    - `'null'`は無限大とNaNの値を`null`としてシリアライズします。
    - `'constants'`は無限大とNaNの値を`Infinity`と`NaN`としてシリアライズします。
    - `'strings'`は無限を文字列`"Infinity"`として、NaNを文字列`"NaN"`としてシリアライズします。
    """

    # whether to validate default values during validation, default False
    validate_default: bool
    # """Whether to validate default values during validation. Defaults to `False`."""
    """検証中にデフォルト値を検証するかどうか。デフォルトは`False`です。"""

    validate_return: bool
    # """whether to validate the return value from call validators. Defaults to `False`."""
    """呼び出しバリデータからの戻り値を検証するかどうか。デフォルトは`False`です。"""

    protected_namespaces: tuple[str, ...]
    """
    # A `tuple` of strings that prevent model to have field which conflict with them.
    # Defaults to `('model_', )`).
    モデルが競合するフィールドを持たないようにする文字列の"タプル"。
    デフォルトは`('model_',)`)です。

    # Pydantic prevents collisions between model attributes and `BaseModel`'s own methods by namespacing them with the prefix `model_`.
    Pydanticは、モデル属性と`BaseModel`自身のメソッドの間の衝突を、それらに接頭辞`model_`を付けて名前空間を設定することで防止します。

    ```py
    import warnings

    from pydantic import BaseModel

    warnings.filterwarnings('error')  # Raise warnings as errors

    try:

        class Model(BaseModel):
            model_prefixed_field: str

    except UserWarning as e:
        print(e)
        '''
        Field "model_prefixed_field" in Model has conflict with protected namespace "model_".

        You may be able to resolve this warning by setting `model_config['protected_namespaces'] = ()`.
        '''
    ```

    # You can customize this behavior using the `protected_namespaces` setting:
    この動作は、`protected_namespaces`設定を使用してカスタマイズできます。

    ```py
    import warnings

    from pydantic import BaseModel, ConfigDict

    warnings.filterwarnings('error')  # Raise warnings as errors

    try:

        class Model(BaseModel):
            model_prefixed_field: str
            also_protect_field: str

            model_config = ConfigDict(
                protected_namespaces=('protect_me_', 'also_protect_')
            )

    except UserWarning as e:
        print(e)
        '''
        Field "also_protect_field" in Model has conflict with protected namespace "also_protect_".

        You may be able to resolve this warning by setting `model_config['protected_namespaces'] = ('protect_me_',)`.
        '''
    ```

    # While Pydantic will only emit a warning when an item is in a protected namespace but does not actually have a collision, an error _is_ raised if there is an actual collision with an existing attribute:
    Pydanticは、項目が保護された名前空間にあり、実際に衝突がない場合にのみ警告を発するが、既存の属性と実際に衝突がある場合にはerror_is_raisedが発生する。

    ```py
    from pydantic import BaseModel

    try:

        class Model(BaseModel):
            model_validate: str

    except NameError as e:
        print(e)
        '''
        Field "model_validate" conflicts with member <bound method BaseModel.model_validate of <class 'pydantic.main.BaseModel'>> of protected namespace "model_".
        '''
    ```
    """

    hide_input_in_errors: bool
    """
    # Whether to hide inputs when printing errors. Defaults to `False`.
    エラーを印刷するときに入力を非表示にするかどうかを指定します。既定値は`False`です。

    # Pydantic shows the input value and type when it raises `ValidationError` during the validation.
    Pydanticは、検証中に`ValidationError`が発生した場合、入力値とタイプを表示します。

    ```py
    from pydantic import BaseModel, ValidationError

    class Model(BaseModel):
        a: str

    try:
        Model(a=123)
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        a
          Input should be a valid string [type=string_type, input_value=123, input_type=int]
        '''
    ```

    # You can hide the input value and type by setting the `hide_input_in_errors` config to `True`.
    `hide_input_in_errors`構成を`True`に設定すると、入力値とタイプを非表示にできます。

    ```py
    from pydantic import BaseModel, ConfigDict, ValidationError

    class Model(BaseModel):
        a: str
        model_config = ConfigDict(hide_input_in_errors=True)

    try:
        Model(a=123)
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        a
          Input should be a valid string [type=string_type]
        '''
    ```
    """

    defer_build: bool
    """
    # Whether to defer model validator and serializer construction until the first model validation. Defaults to False.
    モデルバリデータとシリアライザの構築を、最初のモデル検証まで延期するかどうかを指定します。既定値はFalseです。

    # This can be useful to avoid the overhead of building models which are only  used nested within other models, or when you want to manually define type namespace via [`Model.model_rebuild(_types_namespace=...)`][pydantic.BaseModel.model_rebuild].
    これは、他のモデル内でネストされてのみ使用されるモデルを構築するオーバーヘッドを回避する場合や、[`Model.model_rebuild(_types_namespace=.)`][pydantic.BaseModel.model_rebuild]を使用して型の名前空間を手動で定義する場合に便利です。

    # See also [`experimental_defer_build_mode`][pydantic.config.ConfigDict.experimental_defer_build_mode].
    [`experimental_defer_build_mode`][pydantic.config.ConfigDict.experimental_defer_build_mode]も参照してください。

    !!! note
        # `defer_build` does not work by default with FastAPI Pydantic models.
        # By default, the validator and serializer for said models is constructed immediately for FastAPI routes.
        # You also need to define [`experimental_defer_build_mode=('model', 'type_adapter')`][pydantic.config.ConfigDict.experimental_defer_build_mode] with FastAPI models in order for `defer_build=True` to take effect.
        # This additional (experimental) parameter is required for the deferred building due to FastAPI relying on `TypeAdapter`s.
        `defer_build`は、FastAPI Pydanticモデルではデフォルトで動作しません。
        デフォルトでは、このモデルのバリデータとシリアライザは、FastAPIルートに対して即座に構築されます。
        また、`defer_build=True`を有効にするには、FastAPIモデルで[`experimental_defer_build_mode=('model','type_adapter')`][pydantic.config.ConfigDict.experimental_defer_build_mode]を定義する必要があります。
        この追加の(実験的な)パラメータは、FastAPIが`TypeAdapter`に依存しているため、遅延ビルドに必要です。
    """

    experimental_defer_build_mode: tuple[Literal["model", "type_adapter"], ...]
    """
    # Controls when [`defer_build`][pydantic.config.ConfigDict.defer_build] is applicable. Defaults to `('model',)`.
    [`defer_build`][pydantic.config.ConfigDict.defer_build]が適用される場合を制御します。デフォルトは`('model',)`です。

    # Due to backwards compatibility reasons [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] does not by default respect `defer_build`.
    # Meaning when `defer_build` is `True` and `experimental_defer_build_mode` is the default `('model',)` then `TypeAdapter` immediately constructs its validator and serializer instead of postponing said construction until the first model validation.
    # Set this to `('model', 'type_adapter')` to make `TypeAdapter` respect the `defer_build` so it postpones validator and serializer construction until the first validation or serialization.
    下位互換性の理由から、[`TypeAdapter`][pydantic.type_adapter.TypeAdapter]はデフォルトでは`defer_build`を考慮しません。
    つまり、`defer_build`が`True`で`experimental_defer_build_mode`がデフォルトの`('model',)`の場合、`TypeAdapter`は最初のモデル検証までその構築を延期するのではなく、すぐにバリデータとシリアライザを構築します。
    これを`('model','type_adapter')`に設定すると、`TypeAdapter`は`defer_build`を尊重し、バリデータとシリアライザの構築を最初の検証またはシリアライゼーションまで延期します。

    !!! note
        # The `experimental_defer_build_mode` parameter is named with an underscore to suggest this is an experimental feature.
        # It may be removed or changed in the future in a minor release.
        `experimental_defer_build_mode`パラメータには、これが実験的な機能であることを示すアンダースコアが付いています。
        将来のマイナーリリースで削除または変更される可能性があります。
    """

    plugin_settings: dict[str, object] | None
    # """A `dict` of settings for plugins. Defaults to `None`.
    """プラグインの設定の`dict`です。デフォルトは`None`です。

    # See [Pydantic Plugins](../concepts/plugins.md) for details.
    詳細については、[Pydantic Plugins](../concepts/plugins.md)を参照してください。
    """

    schema_generator: type[_GenerateSchema] | None
    """
    # A custom core schema generator class to use when generating JSON schemas.
    # Useful if you want to change the way types are validated across an entire model/schema. Defaults to `None`.
    JSONスキーマを生成するときに使用するカスタムコアスキーマジェネレータクラス。
    モデル/スキーマ全体で型を検証する方法を変更したい場合に便利です。デフォルトは`None`です。

    # The `GenerateSchema` interface is subject to change, currently only the `string_schema` method is public.
    `GenerateSchema`インターフェースは変更される可能性がありますが、現在は`string_schema`メソッドのみが公開されています。

    See [#6737](https://github.com/pydantic/pydantic/pull/6737) for details.
    詳細については、[#6737](https://github.com/pydantic/pydantic/pull/6737)を参照してください。
    """

    json_schema_serialization_defaults_required: bool
    """
    # Whether fields with default values should be marked as required in the serialization schema. Defaults to `False`.
    デフォルト値を持つフィールドがシリアライゼーションスキーマで必要とマークされるかどうか。デフォルトは`False`です。

    # This ensures that the serialization schema will reflect the fact a field with a default will always be present when serializing the model, even though it is not required for validation.
    これにより、検証に必要でなくても、モデルを直列化するときにデフォルトのフィールドが常に存在するという事実が、直列化スキーマに反映されます。

    # However, there are scenarios where this may be undesirable — in particular, if you want to share the schema between validation and serialization, and don't mind fields with defaults being marked as not required during serialization. See [#7209](https://github.com/pydantic/pydantic/issues/7209) for more details.
    ただし、これが望ましくないシナリオもあります。特に、検証とシリアライゼーションの間でスキーマを共有したい場合や、シリアライゼーション中にデフォルトのフィールドが不要とマークされても気にしない場合です。詳細については、[#7209](https://github.com/pydantic/pydantic/issues/7209)を参照してください。

    ```py
    from pydantic import BaseModel, ConfigDict

    class Model(BaseModel):
        a: str = 'a'

        model_config = ConfigDict(json_schema_serialization_defaults_required=True)

    print(Model.model_json_schema(mode='validation'))
    '''
    {
        'properties': {'a': {'default': 'a', 'title': 'A', 'type': 'string'}},
        'title': 'Model',
        'type': 'object',
    }
    '''
    print(Model.model_json_schema(mode='serialization'))
    '''
    {
        'properties': {'a': {'default': 'a', 'title': 'A', 'type': 'string'}},
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }
    '''
    ```
    """

    json_schema_mode_override: Literal["validation", "serialization", None]
    """
    # If not `None`, the specified mode will be used to generate the JSON schema regardless of what `mode` was passed to the function call. Defaults to `None`.
    `None`でない場合、関数呼び出しに渡された`mode`に関係なく、指定されたモードがJSONスキーマの生成に使用されます。デフォルトは`None`です。

    # This provides a way to force the JSON schema generation to reflect a specific mode, e.g., to always use the validation schema.
    これは、JSONスキーマ生成に特定のモードを強制的に反映させる方法を提供します。

    # It can be useful when using frameworks (such as FastAPI) that may generate different schemas for validation and serialization that must both be referenced from the same schema;
    # when this happens, we automatically append `-Input` to the definition reference for the validation schema and `-Output` to the definition reference for the serialization schema.
    # By specifying a `json_schema_mode_override` though, this prevents the conflict between the validation and serialization schemas (since both will use the specified schema), and so prevents the suffixes from being added to the definition references.
    これは、検証とシリアライゼーションのために異なるスキーマを生成する可能性があり、両方とも同じスキーマから参照されなければならないフレームワーク(FastAPIなど)を使用する場合に便利です。
    この場合、検証スキーマの定義参照には自動的に`-Input`が追加され、直列化スキーマの定義参照には`-Output`が追加されます。
    ただし、`json_schema_mode_override`を指定することで、検証スキーマとシリアライゼーションスキーマの間の競合を防ぎ(どちらも指定されたスキーマを使用するため)、接尾辞が定義参照に追加されないようにします。

    ```py
    from pydantic import BaseModel, ConfigDict, Json

    class Model(BaseModel):
        a: Json[int]  # requires a string to validate, but will dump an int

    print(Model.model_json_schema(mode='serialization'))
    '''
    {
        'properties': {'a': {'title': 'A', 'type': 'integer'}},
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }
    '''

    class ForceInputModel(Model):
        # the following ensures that even with mode='serialization', we
        # will get the schema that would be generated for validation.
        model_config = ConfigDict(json_schema_mode_override='validation')

    print(ForceInputModel.model_json_schema(mode='serialization'))
    '''
    {
        'properties': {
            'a': {
                'contentMediaType': 'application/json',
                'contentSchema': {'type': 'integer'},
                'title': 'A',
                'type': 'string',
            }
        },
        'required': ['a'],
        'title': 'ForceInputModel',
        'type': 'object',
    }
    '''
    ```
    """

    coerce_numbers_to_str: bool
    """
    # If `True`, enables automatic coercion of any `Number` type to `str` in "lax" (non-strict) mode. Defaults to `False`.
    `True`の場合、任意の`Number`型を`str`に"lax"(非strict)モードで自動的に強制します。デフォルトは`False`です。

    # Pydantic doesn't allow number types (`int`, `float`, `Decimal`) to be coerced as type `str` by default.
    Pydanticでは、デフォルトで数値型(`int`、`float`、`Decimal`)を`str`型として強制することはできません。

    ```py
    from decimal import Decimal

    from pydantic import BaseModel, ConfigDict, ValidationError

    class Model(BaseModel):
        value: str

    try:
        print(Model(value=42))
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        value
          Input should be a valid string [type=string_type, input_value=42, input_type=int]
        '''

    class Model(BaseModel):
        model_config = ConfigDict(coerce_numbers_to_str=True)

        value: str

    repr(Model(value=42).value)
    #> "42"
    repr(Model(value=42.13).value)
    #> "42.13"
    repr(Model(value=Decimal('42.13')).value)
    #> "42.13"
    ```
    """

    regex_engine: Literal["rust-regex", "python-re"]
    """
    # The regex engine to be used for pattern validation.
    # Defaults to `'rust-regex'`.
    パターン検証に使用される正規表現エンジン。
    デフォルトは`'rust-regex'`です。

    # - `rust-regex` uses the [`regex`](https://docs.rs/regex) Rust crate, which is non-backtracking and therefore more DDoS resistant, but does not support all regex features.
    # - `python-re` use the [`re`](https://docs.python.org/3/library/re.html) module, which supports all regex features, but may be slower.
    - `rust-regex`は[`regex`](https://docs.rs/regex)Rustクレートを使用します。これは非バックトラックであり、したがってよりDDoS耐性がありますが、すべてのregex機能をサポートしているわけではありません。
    - `python-re`は[`re`](https://docs.python.org/3/library/re.html)モジュールを使用します。このモジュールはすべての正規表現機能をサポートしていますが、速度が遅くなる可能性があります。

    !!! note
        # If you use a compiled regex pattern, the python-re engine will be used regardless of this setting.
        # This is so that flags such as `re.IGNORECASE` are respected.
        コンパイルされたregexパターンを使用する場合は、この設定に関係なくpython-reエンジンが使用されます。
        これは、`re.IGNORECASE`のようなフラグが尊重されるようにするためです。

    ```py
    from pydantic import BaseModel, ConfigDict, Field, ValidationError

    class Model(BaseModel):
        model_config = ConfigDict(regex_engine='python-re')

        value: str = Field(pattern=r'^abc(?=def)')

    print(Model(value='abcdef').value)
    #> abcdef

    try:
        print(Model(value='abxyzcdef'))
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        value
          String should match pattern '^abc(?=def)' [type=string_pattern_mismatch, input_value='abxyzcdef', input_type=str]
        '''
    ```
    """

    validation_error_cause: bool
    """
    # If `True`, Python exceptions that were part of a validation failure will be shown as an exception group as a cause. Can be useful for debugging. Defaults to `False`.
    `True`の場合、検証エラーの一部であったPython例外は、原因として例外グループとして表示されます。デバッグに役立ちます。デフォルトは`False`です。

    Note:
        # Python 3.10 and older don't support exception groups natively. <=3.10, backport must be installed: `pip install exceptiongroup`.
        Python 3.10以前は、例外グループをネイティブにサポートしていません。<=3.10、backportをインストールする必要があります:`pip install exceptiongroup`。

    Note:
        # The structure of validation errors are likely to change in future Pydantic versions. Pydantic offers no guarantees about their structure. Should be used for visual traceback debugging only.
        検証エラーの構造は、将来のPydanticバージョンで変更される可能性があります。Pydanticはその構造について保証していません。視覚的なトレースバックデバッグにのみ使用する必要があります。


    """

    use_attribute_docstrings: bool
    '''
    # Whether docstrings of attributes (bare string literals immediately following the attribute declaration) should be used for field descriptions. Defaults to `False`.
    属性のdocstring(属性宣言の直後の空の文字列リテラル)をフィールドの説明に使用するかどうか。デフォルトは`False`です。

    # Available in Pydantic v2.7+.
    Pydantic v2.7+で利用可能。

    ```py
    from pydantic import BaseModel, ConfigDict, Field


    class Model(BaseModel):
        model_config = ConfigDict(use_attribute_docstrings=True)

        x: str
        """
        Example of an attribute docstring
        """

        y: int = Field(description="Description in Field")
        """
        Description in Field overrides attribute docstring
        """


    print(Model.model_fields["x"].description)
    # > Example of an attribute docstring
    print(Model.model_fields["y"].description)
    # > Description in Field
    ```
    # This requires the source code of the class to be available at runtime.
    そのためには、クラスのソースコードが実行時に使用可能である必要があります。

    !!! warning "Usage with `TypedDict`"
        # Due to current limitations, attribute docstrings detection may not work as expected when using `TypedDict` (in particular when multiple `TypedDict` classes have the same name in the same source file).
        # The behavior can be different depending on the Python version used.
        現在の制限により、`TypedDict`を使用すると、属性のドキュメント文字列の検出が期待通りに動作しない可能性があります(特に、同じソースファイル内で複数の`TypedDict`クラスが同じ名前を持つ場合)。
        この動作は、使用するPythonのバージョンによって異なります。
    '''

    cache_strings: bool | Literal["all", "keys", "none"]
    """
    # Whether to cache strings to avoid constructing new Python objects. Defaults to True.
    新しいPythonオブジェクトの構築を回避するために文字列をキャッシュするかどうかを指定します。既定値はTrueです。

    # Enabling this setting should significantly improve validation performance while increasing memory usage slightly.
    この設定を有効にすると、検証のパフォーマンスが大幅に向上し、メモリ使用量がわずかに増加します。

    # - `True` or `'all'` (the default): cache all strings
    # - `'keys'`: cache only dictionary keys
    # - `False` or `'none'`: no caching
    - `True`または`'all'`(デフォルト): すべての文字列をキャッシュします。
    - `'keys'`: ディクショナリキーのみをキャッシュします。
    - `False`または`'none'`: キャッシュしません。



    !!! note
        # `True` or `'all'` is required to cache strings during general validation because validators don't know if they're in a key or a value.
        `True`または`'all'`は、一般的な検証中に文字列をキャッシュするために必要です。なぜなら、バリデータはそれらがキー内にあるのか値内にあるのかを知らないからです。



    !!! tip
        # If repeated strings are rare, it's recommended to use `'keys'` or `'none'` to reduce memory usage, as the performance difference is minimal if repeated strings are rare.
        文字列の繰り返しが少ない場合は、メモリー使用量を減らすために"keys"または"none"を使用することをお勧めします。
    """


_TypeT = TypeVar("_TypeT", bound=type)


def with_config(config: ConfigDict) -> Callable[[_TypeT], _TypeT]:
    """Usage docs: ../concepts/config/#configuration-with-dataclass-from-the-standard-library-or-typeddict

    # A convenience decorator to set a [Pydantic configuration](config.md) on a `TypedDict` or a `dataclass` from the standard library.
    標準ライブラリの`TypedDict`または`dataclass`に[Pydantic configuration](config.md)を設定するための便利なデコレータです。

    # Although the configuration can be set using the `__pydantic_config__` attribute, it does not play well with type checkers, especially with `TypedDict`.
    この設定は`__pydantic_config__`属性を使って設定できますが、型チェッカー、特に`TypedDict`ではうまく動作しません。

    !!! example "Usage"

        ```py
        from typing_extensions import TypedDict

        from pydantic import ConfigDict, TypeAdapter, with_config

        @with_config(ConfigDict(str_to_lower=True))
        class Model(TypedDict):
            x: str

        ta = TypeAdapter(Model)

        print(ta.validate_python({'x': 'ABC'}))
        #> {'x': 'abc'}
        ```
    """

    def inner(class_: _TypeT, /) -> _TypeT:
        # Ideally, we would check for `class_` to either be a `TypedDict` or a stdlib dataclass.
        # However, the `@with_config` decorator can be applied *after* `@dataclass`. To avoid
        # common mistakes, we at least check for `class_` to not be a Pydantic model.
        from ._internal._utils import is_model_class

        if is_model_class(class_):
            raise PydanticUserError(
                f"Cannot use `with_config` on {class_.__name__} as it is a Pydantic model",
                code="with-config-on-model",
            )
        class_.__pydantic_config__ = config
        return class_

    return inner


__getattr__ = getattr_migration(__name__)
