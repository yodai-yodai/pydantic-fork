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

__all__ = ('ConfigDict', 'with_config')


JsonValue: TypeAlias = Union[int, float, str, bool, None, List['JsonValue'], 'JsonDict']
JsonDict: TypeAlias = Dict[str, JsonValue]

JsonEncoder = Callable[[Any], Any]

JsonSchemaExtraCallable: TypeAlias = Union[
    Callable[[JsonDict], None],
    Callable[[JsonDict, Type[Any]], None],
]

ExtraValues = Literal['allow', 'ignore', 'forbid']


class ConfigDict(TypedDict, total=False):
    """Pydanticの動作を設定するためのTypedDict"""

    title: str | None
    """生成されたJSONスキーマのタイトル。デフォルトはモデルの名前です"""

    model_title_generator: Callable[[type], str] | None
    """モデルクラスを受け取り、そのタイトルを返す呼び出し可能オブジェクト。デフォルトは`None`です。"""

    field_title_generator: Callable[[str, FieldInfo | ComputedFieldInfo], str] | None
    """フィールドの名前と情報を受け取り、そのタイトルを返す呼び出し可能オブジェクト。デフォルトは`None`です。"""

    str_to_lower: bool
    """str型のすべての文字を小文字に変換するかどうか。デフォルトは`False`です。"""

    str_to_upper: bool
    """str型のすべての文字を大文字に変換するかどうか。デフォルトは`False`です。"""

    str_strip_whitespace: bool
    """str型の先頭と末尾の空白を削除するかどうか。"""

    str_min_length: int
    """str型の最小長。デフォルトは`None`です。"""

    str_max_length: int | None
    """str型の最大長。デフォルトは`None`です。"""

    extra: ExtraValues | None
    """
    モデルの初期化中に追加属性を無視するか、許可するか、禁止するか。デフォルトは`'ignore'`です。

    モデルで定義されていない属性をpydanticが処理する方法を設定できます。

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

    1. これがデフォルトの動作です。
    2. `age`引数は無視されます。

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

    1. `age`引数が含まれます。

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
    モデルが疑似不変かどうか、つまり`__setattr__`が許可されているかどうか。また、モデルの`__hash__()`メソッドを生成します。これにより、すべての属性がハッシュ可能であれば、モデルのインスタンスがハッシュ可能になります。デフォルトは`False`です。

    Note:
        V1では、この設定の逆は`allow_mutation`と呼ばれ、デフォルトでは`True`でした。
    """

    populate_by_name: bool
    """
    別名フィールドに、モデル属性で指定された名前と別名を入力できるかどうかを指定します。既定値は`False`です。

    Note:
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

    1. フィールド"name"にはエイリアス"full_name"があります。
    2. モデルは、エイリアス`'full_name'`によって作成されます。
    3. モデルには、フィールド名"name"が入力されます。
    """

    use_enum_values: bool
    """
    生の列挙型ではなく、列挙型の`value`プロパティをモデルに設定するかどうか。
    これは`model.model_dump()`を後でシリアライズしたい場合に便利です。デフォルトは`False`です。

    !!! note
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
    モデルが変更されたときにデータを検証するかどうか。デフォルトは`False`です。

    Pydanticのデフォルトの動作は、モデルの作成時にデータを検証することです。

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

    1. 検証は、モデルの作成時にのみ行われます。
    2. データが変更されても、検証は行われません。

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

    1. クラスキーワード引数を使用するか、`model_config`を使用して`validate_assignment=True`を設定できます。
    2. モデルの作成時に検証が行われます。
    3. データが変更されると、validation_also_が発生します。
    """

    arbitrary_types_allowed: bool
    """
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
    モデルを構築し、Pythonオブジェクトアトリビュートを使用してタグ付き共用体の識別子を検索するかどうかを指定します。
    """

    loc_by_alias: bool
    """エラー`loc`に対して、フィールド名ではなく、データ内で提供された実際のキー(エイリアスなど)を使用するかどうか。デフォルトは`True`です。"""

    alias_generator: Callable[[str], str] | AliasGenerator | None
    """
    フィールド名を受け取り、そのエイリアスを返す呼び出し可能オブジェクト
    または[`AliasGenerator`][pydantic.aliases.AliasGenerator]のインスタンスです。デフォルトは`None`です。

    呼び出し可能オブジェクトを使用する場合、検証とシリアライゼーションの両方にエイリアスジェネレータが使用されます。
    検証とシリアライゼーションに異なるエイリアスジェネレータを使用したい場合は、代わりに[`AliasGenerator`][pydantic.aliases.AliasGenerator]を使用できます。

    データソースのフィールド名がコードスタイルと一致しない場合(CamelCaseフィールドなど)、`alias_generator`を使用してエイリアスを自動的に生成できます。
    基本的な呼び出し方:

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
        Pydanticには、[`to_pascal`][pydantic.alias_generators.to_pascal]、[`to_camel`][pydantic.alias_generators.to_camel]、[`to_snake`][pydantic.alias_generators.to_snake]という3つのエイリアスジェネレータが組み込まれています。
    """

    ignored_types: tuple[type, ...]
    """注釈なしでクラス属性の値として発生する可能性のある型のタプル。
    これは通常、カスタム記述子(`property`のように動作するクラス)に使用されます。
    属性がアノテーションなしでクラスに設定され、その型がこのタプルにない(または_pydantic_で認識されない)場合、エラーが発生します。デフォルトは`()`です。
    """

    allow_inf_nan: bool
    """無限値(`+inf`an`-inf`)とNaN値を浮動小数点フィールドと小数フィールドに許可するかどうか。デフォルトは`True`。"""

    json_schema_extra: JsonDict | JsonSchemaExtraCallable | None
    """追加のJSONスキーマプロパティを提供するためのdictまたはcallable。デフォルトは`None`です。"""

    json_encoders: dict[type[object], JsonEncoder] | None
    """
    特定の型用のカスタムJSONエンコーダの`dict`です。デフォルトは`None`です。

    !!! warning "Deprecated"
        このconfigオプションはv1からの繰り越しです。
        当初はv2で削除する予定でしたが、1:1の置き換えがなかったので、今のところそのままにしています。
        これはまだ推奨されておらず、将来削除される可能性があります。
    """

    # new in V2
    strict: bool
    """
    _(V2の新機能)_`True`の場合、モデルのすべてのフィールドに厳密な検証が適用されます。

    デフォルトでは、Pydanticは可能であれば値を正しい型に強制しようとします。

    場合によっては、この動作を無効にして、値の型がフィールドの型注釈と一致しない場合にエラーを発生させることができます。

    モデルのすべてのフィールドにstrictモードを設定するには、モデルに`strict=True`を設定します。

    ```py
    from pydantic import BaseModel, ConfigDict

    class Model(BaseModel):
        model_config = ConfigDict(strict=True)

        name: str
        age: int
    ```

    詳細については、[Strict Mode](https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/strict_mode.md)を参照してください。

    Pydanticがstrictモードとlaxモードの両方でデータを変換する方法の詳細については、[Conversion Table](https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/conversion_table.md)を参照してください。
    """
    revalidate_instances: Literal['always', 'never', 'subclass-instances']
    """
    検証中にモデルとデータクラスをいつ、どのように再検証するか。"never"、"always"、"subclass-instances"の文字列値を受け入れます。デフォルトは"never"です。

    - `'never'`は、検証中にモデルとデータクラスを再検証しません。
    - "always"は、検証中にモデルとデータクラスを再検証します。
    - `'subclass-instances'`は、インスタンスがモデルまたはデータクラスのサブクラスである場合、検証中にモデルとデータクラスを再検証します。

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

    1. `revalidate_instances`は**デフォルトで`'never'`に設定されています。
    2. モデルの設定で`validate_assignment`を`True`に設定しない限り、割り当ては検証されません。
    3. `revalidate_instances`は`never`に設定されているので、これは再検証されません。

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

    1. `revalidate_instances`が`'always'`に設定されている。
    2. `revalidate_instances`が`'always'`に設定されているので、モデルは再検証されます。
    3. "never"を使用すると、"user=SubUser(hobbies=['scuba diving'],sins=['lying'])"が得られます。

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

    1. `revalidate_instances`は`'subclass-instances'`に設定されます。
    2. `my_user`は`User`のサブクラスではないので、これは再検証されません。
    3. "never"を使用すると、"user=SubUser(hobbies=['scuba diving'],sins=['lying'])"が得られます。

    """

    ser_json_timedelta: Literal['iso8601', 'float']
    """
    JSONシリアライズされたタイムデルタのフォーマット。`'iso8601'`および`'float'`の文字列値を受け入れます。デフォルトは`'iso8601'`です。

    - `'iso8601'`はtimedeltasをiso8601 durationにシリアライズします。
    - `'float'`はtimedeltaを合計秒数にシリアライズします。
    """

    ser_json_bytes: Literal['utf8', 'base64']
    """
    JSONシリアライズされたバイトのエンコーディング。`'utf8'`と`'base64'`の文字列値を受け入れます。
    デフォルトは`'utf8'`です。

    - `'utf8'`はバイトをUTF-8文字列にシリアライズします。
    - `'base64'`はバイトをURLセーフなbase64文字列にシリアライズします。
    """

    ser_json_inf_nan: Literal['null', 'constants', 'strings']
    """
    JSONシリアライズされたinfinityおよびNaN float値のエンコーディング。デフォルトは`'null'`です。

    - `'null'`は無限大とNaNの値を`null`としてシリアライズします。
    - `'constants'`は無限大とNaNの値を`Infinity`と`NaN`としてシリアライズします。
    - `'strings'`は無限を文字列`"Infinity"`として、NaNを文字列`"NaN"`としてシリアライズします。
    """

    # whether to validate default values during validation, default False
    validate_default: bool
    """検証中にデフォルト値を検証するかどうか。デフォルトは`False`です。"""

    validate_return: bool
    """呼び出しバリデータからの戻り値を検証するかどうか。デフォルトは`False`です。"""

    protected_namespaces: tuple[str, ...]
    """
    モデルが競合するフィールドを持たないようにする文字列の"タプル"。
    デフォルトは`('model_',)`)です。

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
    エラーを印刷するときに入力を非表示にするかどうかを指定します。既定値は`False`です。

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
    モデルバリデータとシリアライザの構築を、最初のモデル検証まで延期するかどうかを指定します。既定値はFalseです。

    これは、他のモデル内でネストされてのみ使用されるモデルを構築するオーバーヘッドを回避する場合や、[`Model.model_rebuild(_types_namespace=.)`][pydantic.BaseModel.model_rebuild]を使用して型の名前空間を手動で定義する場合に便利です。

    [`experimental_defer_build_mode`][pydantic.config.ConfigDict.experimental_defer_build_mode]も参照してください。

    !!! note
        `defer_build`は、FastAPI Pydanticモデルではデフォルトで動作しません。
        デフォルトでは、このモデルのバリデータとシリアライザは、FastAPIルートに対して即座に構築されます。
        また、`defer_build=True`を有効にするには、FastAPIモデルで[`experimental_defer_build_mode=('model','type_adapter')`][pydantic.config.ConfigDict.experimental_defer_build_mode]を定義する必要があります。
        この追加の(実験的な)パラメータは、FastAPIが`TypeAdapter`に依存しているため、遅延ビルドに必要です。
    """

    experimental_defer_build_mode: tuple[Literal['model', 'type_adapter'], ...]
    """
    [`defer_build`][pydantic.config.ConfigDict.defer_build]が適用される場合を制御します。デフォルトは`('model',)`です。

    下位互換性の理由から、[`TypeAdapter`][pydantic.type_adapter.TypeAdapter]はデフォルトでは`defer_build`を考慮しません。
    つまり、`defer_build`が`True`で`experimental_defer_build_mode`がデフォルトの`('model',)`の場合、`TypeAdapter`は最初のモデル検証までその構築を延期するのではなく、すぐにバリデータとシリアライザを構築します。
    これを`('model','type_adapter')`に設定すると、`TypeAdapter`は`defer_build`を尊重し、バリデータとシリアライザの構築を最初の検証またはシリアライゼーションまで延期します。

    !!! note
        `experimental_defer_build_mode`パラメータには、これが実験的な機能であることを示すアンダースコアが付いています。
        将来のマイナーリリースで削除または変更される可能性があります。
    """

    plugin_settings: dict[str, object] | None
    # """A `dict` of settings for plugins. Defaults to `None`.
    """プラグインの設定の`dict`です。デフォルトは`None`です。

    詳細については、[Pydantic Plugins](https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/plugins.md)を参照してください。
    """

    schema_generator: type[_GenerateSchema] | None
    """
    JSONスキーマを生成するときに使用するカスタムコアスキーマジェネレータクラス。
    モデル/スキーマ全体で型を検証する方法を変更したい場合に便利です。デフォルトは`None`です。

    `GenerateSchema`インターフェースは変更される可能性がありますが、現在は`string_schema`メソッドのみが公開されています。

    詳細については、[#6737](https://github.com/pydantic/pydantic/pull/6737)を参照してください。
    """

    json_schema_serialization_defaults_required: bool
    """
    デフォルト値を持つフィールドがシリアライゼーションスキーマで必要とマークされるかどうか。デフォルトは`False`です。

    これにより、検証に必要でなくても、モデルを直列化するときにデフォルトのフィールドが常に存在するという事実が、直列化スキーマに反映されます。

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

    json_schema_mode_override: Literal['validation', 'serialization', None]
    """
    `None`でない場合、関数呼び出しに渡された`mode`に関係なく、指定されたモードがJSONスキーマの生成に使用されます。デフォルトは`None`です。

    これは、JSONスキーマ生成に特定のモードを強制的に反映させる方法を提供します。

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
    `True`の場合、任意の`Number`型を`str`に"lax"(非strict)モードで自動的に強制します。デフォルトは`False`です。

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

    regex_engine: Literal['rust-regex', 'python-re']
    """
    パターン検証に使用される正規表現エンジン。
    デフォルトは`'rust-regex'`です。

    - `rust-regex`は[`regex`](https://docs.rs/regex)Rustクレートを使用します。これは非バックトラックであり、したがってよりDDoS耐性がありますが、すべてのregex機能をサポートしているわけではありません。
    - `python-re`は[`re`](https://docs.python.org/3/library/re.html)モジュールを使用します。このモジュールはすべての正規表現機能をサポートしていますが、速度が遅くなる可能性があります。

    !!! note
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
    `True`の場合、検証エラーの一部であったPython例外は、原因として例外グループとして表示されます。デバッグに役立ちます。デフォルトは`False`です。

    Note:
        Python 3.10以前は、例外グループをネイティブにサポートしていません。<=3.10、backportをインストールする必要があります:`pip install exceptiongroup`。

    Note:
        検証エラーの構造は、将来のPydanticバージョンで変更される可能性があります。Pydanticはその構造について保証していません。視覚的なトレースバックデバッグにのみ使用する必要があります。


    """

    use_attribute_docstrings: bool
    '''
    属性のdocstring(属性宣言の直後の空の文字列リテラル)をフィールドの説明に使用するかどうか。デフォルトは`False`です。

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
    そのためには、クラスのソースコードが実行時に使用可能である必要があります。

    !!! warning "Usage with `TypedDict`"
        現在の制限により、`TypedDict`を使用すると、属性のドキュメント文字列の検出が期待通りに動作しない可能性があります(特に、同じソースファイル内で複数の`TypedDict`クラスが同じ名前を持つ場合)。
        この動作は、使用するPythonのバージョンによって異なります。
    '''

    cache_strings: bool | Literal['all', 'keys', 'none']
    """
    新しいPythonオブジェクトの構築を回避するために文字列をキャッシュするかどうかを指定します。既定値はTrueです。

    この設定を有効にすると、検証のパフォーマンスが大幅に向上し、メモリ使用量がわずかに増加します。

    - `True`または`'all'`(デフォルト): すべての文字列をキャッシュします。
    - `'keys'`: ディクショナリキーのみをキャッシュします。
    - `False`または`'none'`: キャッシュしません。



    !!! note
        `True`または`'all'`は、一般的な検証中に文字列をキャッシュするために必要です。なぜなら、バリデータはそれらがキー内にあるのか値内にあるのかを知らないからです。



    !!! tip
        文字列の繰り返しが少ない場合は、メモリー使用量を減らすために"keys"または"none"を使用することをお勧めします。
    """


_TypeT = TypeVar('_TypeT', bound=type)


def with_config(config: ConfigDict) -> Callable[[_TypeT], _TypeT]:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/config/#configuration-with-dataclass-from-the-standard-library-or-typeddict

    標準ライブラリの`TypedDict`または`dataclass`に[Pydantic configuration](config.md)を設定するための便利なデコレータです。

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
                f'Cannot use `with_config` on {class_.__name__} as it is a Pydantic model',
                code='with-config-on-model',
            )
        class_.__pydantic_config__ = config
        return class_

    return inner


__getattr__ = getattr_migration(__name__)
