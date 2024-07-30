{% include-markdown "../warning.md" %}

<!-- Unions are fundamentally different to all other types Pydantic validates - instead of requiring all fields/items/values to be valid, unions require only one member to be valid. -->
Unionは、Pydanticが検証する他のすべてのタイプとは根本的に異なります。すべてのフィールド/アイテム/値が有効であることを要求するのではなく、Unionは1つのメンバーのみが有効であることを要求します。

<!-- This leads to some nuance around how to validate unions: -->
これは、Unionの検証方法に関するいくつかのニュアンスにつながります。

<!--
* which member(s) of the union should you validate data against, and in which order?
* which errors to raise when validation fails?
-->
* Unionのどのメンバーに対して、どのような順序でデータを検証する必要がありますか?
* 検証が失敗した場合に発生するエラー

<!-- Validating unions feels like adding another orthogonal dimension to the validation process. -->
Unionの検証は、検証プロセスに別の直交次元を追加するように感じられます。

<!-- To solve these problems, Pydantic supports three fundamental approaches to validating unions: -->
これらの問題を解決するために、PydanticはUnionを検証するための3つの基本的なアプローチをサポートしています。

<!-- 1. [left to right mode](#left-to-right-mode) - the simplest approach, each member of the union is tried in order and the first match is returned -->
1. [left-to-right mode](#left-to-right-mode) - 最も簡単な方法で、Unionの各メンバーが順番に試行され、最初の一致が返されます。
<!-- 2. [smart mode](#smart-mode) - similar to "left to right mode" members are tried in order; however, validation will proceed past the first match to attempt to find a better match, this is the default mode for most union validation -->
2. [smart mode](#smart-mode) - 「左から右へのモード」と同様に、メンバーは順番に試行されます。ただし、検証は最初の一致を超えて進行し、より適切な一致を見つけようとします。これは、ほとんどのUnion検証のデフォルトモードです。
<!-- 3. [discriminated unions](#discriminated-unions) - only one member of the union is tried, based on a discriminator -->
3. [識別されたUnion](#discriminated-unions) - 識別子に基づいて、Unionの1つのメンバーのみが試行されます。

!!! tip

    <!-- In general, we recommend using [discriminated unions](#discriminated-unions). They are both more performant and more predictable than untagged unions, as they allow you to control which member of the union to validate against. -->
    一般的に、[discriminatedUnion](#discriminated-unions)を使用することをお薦めします。これらは、どのUnionのメンバーに対して検証するかを制御できるため、タグなしUnionよりもパフォーマンスが高く、予測可能です。

    <!-- For complex cases, if you're using untagged unions, it's recommended to use `union_mode='left_to_right'` if you need guarantees about the order of validation attempts against the union members. -->
    複雑なケースでは、タグなしUnionを使用している場合、Unionメンバーに対する検証試行の順序を保証する必要がある場合は、`union_mode='left_to_right'`を使用することをお勧めします。

    <!-- If you're looking for incredibly specialized behavior, you can use a [custom validator](../concepts/validators.md#field-validators). -->
    非常に特殊な動作を探している場合は、[custom validator](../concepts/validators.md#field-validators)を使用できます。

## Union Modes

### Left to Right Mode

!!! note
    <!-- Because this mode often leads to unexpected validation results, it is not the default in Pydantic >=2, instead `union_mode='smart'` is the default. -->
    このモードは予期しない検証結果をもたらすことが多いため、Pydantic>=2ではデフォルトではなく、`union_mode='smart'`がデフォルトです。

<!-- With this approach, validation is attempted against each member of the union in their order they're defined, and the first successful validation is accepted as input. -->
この手法では、Unionの各メンバーに対して、定義された順序で検証が試行され、最初に成功した検証が入力として受け入れられます。

<!-- If validation fails on all members, the validation error includes the errors from all members of the union. -->
すべてのメンバーで検証が失敗した場合、検証エラーにはUnionのすべてのメンバーからのエラーが含まれます。

<!-- `union_mode='left_to_right'` must be set as a [`Field`](../concepts/fields.md) parameter on union fields where you want to use it. -->
`union_mode='left_to_right'`は、使用するUnionフィールドの[`Field`](../concepts/fields.md)パラメータとして設定する必要があります。

```py title="Union with left to right mode"
from typing import Union

from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    id: Union[str, int] = Field(union_mode='left_to_right')


print(User(id=123))
#> id=123
print(User(id='hello'))
#> id='hello'

try:
    User(id=[])
except ValidationError as e:
    print(e)
    """
    2 validation errors for User
    id.str
      Input should be a valid string [type=string_type, input_value=[], input_type=list]
    id.int
      Input should be a valid integer [type=int_type, input_value=[], input_type=list]
    """
```

<!-- The order of members is very important in this case, as demonstrated by tweak the above example: -->
この場合、メンバーの順序が非常に重要になります。これは、上記の例を微調整して示しています。

```py title="Union with left to right - unexpected results"
from typing import Union

from pydantic import BaseModel, Field


class User(BaseModel):
    id: Union[int, str] = Field(union_mode='left_to_right')


print(User(id=123))  # (1)
#> id=123
print(User(id='456'))  # (2)
#> id=456
```

<!-- 1. As expected the input is validated against the `int` member and the result is as expected. -->
1. 予想通り、入力は`int`メンバーに対して検証され、結果は予想通りです。
<!-- 2. We're in lax mode and the numeric string `'123'` is valid as input to the first member of the union, `int`. Since that is tried first, we get the surprising result of `id` being an `int` instead of a `str`. -->
2. laxモードになっていて、数値文字列`'123'`がUnionの最初のメンバー`int`への入力として有効です。これが最初に試行されるので、`id`が`str`ではなく`int`であるという驚くべき結果が得られます。

### Smart Mode

<!-- Because of the potentially surprising results of `union_mode='left_to_right'`, in Pydantic >=2 the default mode for `Union` validation is `union_mode='smart'`. -->
`union_mode='left_to_right'`は意外な結果をもたらす可能性があるため、Pydantic>=2では`Union`検証のデフォルトモードは`union_mode='smart'`です。

<!-- In this mode, pydantic attempts to select the best match for the input from the union members. The exact algorithm may change between Pydantic minor releases to allow for improvements in both performance and accuracy. -->
このモードでは、pydanticはUnionメンバからの入力に最も一致するものを選択しようとします。正確なアルゴリズムは、パフォーマンスと精度の両方を向上させるために、Pydanticのマイナーリリース間で変更される可能性があります。

!!! note

    <!-- We reserve the right to tweak the internal `smart` matching algorithm in future versions of Pydantic. If you rely on very specific  matching behavior, it's recommended to use `union_mode='left_to_right'` or [discriminated unions](#discriminated-unions). -->
    Pydanticの将来のバージョンでは、内部の`smart`マッチングアルゴリズムを微調整する権利を留保します。非常に特殊なマッチング動作に依存している場合は、`union_mode='left_to_right'`または[discriminated unions](#discriminated-unions)を使用することをお勧めします。

??? info "Smart Mode Algorithm"

    <!-- The smart mode algorithm uses two metrics to determine the best match for the input: -->
    スマートモードアルゴリズムは、次の2つのメトリックを使用して、入力の最適な一致を判断します。

    <!-- 1. The number of valid fields set (relevant for models, dataclasses, and typed dicts)
    2. The exactness of the match (relevant for all types) -->
    1. 有効なフィールドセットの数(モデル、データクラス、および型指定された辞書に関連)
    2. 一致の正確さ(すべてのタイプに関連)

    #### Number of valid fields set

    !!! note
        <!-- This metric was introduced in Pydantic v2.8.0. Prior to this version, only exactness was used to determine the best match. -->
        このメトリックは、Pydantic v2.8.0で導入されました。このバージョン以前は、正確さのみを使用して最適な一致を決定していました。

    <!-- This metric is currently only relevant for models, dataclasses, and typed dicts. -->
    このメトリックは現在、モデル、データクラス、および型付き辞書にのみ関連しています。

    <!-- The greater the number of valid fields set, the better the match. The number of fields set on nested models is also taken into account.
    These counts bubble up to the top-level union, where the union member with the highest count is considered the best match. -->
    設定された有効なフィールドの数が多いほど、一致度が高くなります。ネストされたモデルに設定されたフィールドの数も考慮されます。
    これらのカウントは最上位レベルのUnionまでバブルアップされ、最も高いカウントを持つUnionメンバーが最適な一致と見なされます。

    For data types where this metric is relevant, we prioritize this count over exactness. For all other types, we use solely exactness.
    このメトリックが関連するデータ型では、このカウントが正確さよりも優先されます。その他のすべてのデータ型では、正確さのみが使用されます。

    #### Exactness

    <!-- For `exactness`, Pydantic scores a match of a union member into one of the following three groups (from highest score to lowest score): -->
    `正確さ`のために、Pydanticは組合員の試合を次の3つのグループのいずれかに採点します(最高得点から最低得点まで)。

    <!--
    - An exact type match, for example an `int` input to a `float | int` union validation is an exact type match for the `int` member
    - Validation would have succeeded in [`strict` mode](../concepts/strict_mode.md)
    - Validation would have succeeded in lax mode
    -->
    - 正確な型の一致。たとえば、`float int`Union検証への`int`入力は、`int`メンバーの正確な型の一致です。
    - 検証は[`strict`モード](../concepts/strict_mode.md)で成功します。
    - 検証はlaxモードで成功します。

    <!-- The union match which produced the highest exactness score will be considered the best match. -->
    最も高い正確さのスコアを生成したUnionマッチが、ベストマッチと見なされます。

    <!-- In smart mode, the following steps are taken to try to select the best match for the input: -->
    スマートモードでは、入力に最適なものを選択するために次の手順が実行されます。

    === "`BaseModel`, `dataclass`, and `TypedDict`"

        <!-- 1. Union members are attempted left to right, with any successful matches scored into one of the three exactness categories described above, with the valid fields set count also tallied. -->
        1. Union・メンバーは左から右に試行され、成功した一致は前述の3つの正確さのカテゴリーのいずれかにスコア付けされ、有効なフィールド・セット・カウントも集計されます。
        <!-- 2. After all members have been evaluated, the member with the highest "valid fields set" count is returned. -->
        2. すべてのメンバーが評価された後、「有効なフィールド・セット」カウントが最も高いメンバーが戻されます。
        <!-- 3. If there's a tie for the highest "valid fields set" count, the exactness score is used as a tiebreaker, and the member with the highest exactness score is returned. -->
        3. 最大の「有効フィールド・セット」カウントに対してタイがある場合、正確さのスコアがタイ・ブレーカーとして使用され、正確さのスコアが最も高いメンバーが戻されます。
        <!-- 4. If validation failed on all the members, return all the errors. -->
        4. すべてのメンバーで検証が失敗した場合は、すべてのエラーが戻されます。

    === "All other data types"

        <!-- 1. Union members are attempted left to right, with any successful matches scored into one of the three exactness categories described above. -->
        1. Unionは左から右に試みられ、成功した試合は上記の3つの正確さのカテゴリーのいずれかに得点されます。
            <!-- - If validation succeeds with an exact type match, that member is returned immediately and following members will not be attempted. -->
            - 型が完全に一致して検証が成功した場合、そのメンバーはすぐに戻され、後続のメンバーは試行されません。
        <!-- 2. If validation succeeded on at least one member as a "strict" match, the leftmost of those "strict" matches is returned. -->
        2. 少なくとも1つのメンバーで検証が「厳密な」一致として成功した場合、それらの「厳密な」一致のうち最も左のものが戻されます。
        <!-- 3. If validation succeeded on at least one member in "lax" mode, the leftmost match is returned. -->
        3. 「lax」モードで少なくとも1つのメンバーの検証が成功した場合、一番左の一致が戻されます。
        <!-- 4. Validation failed on all the members, return all the errors. -->
        4. すべてのメンバーで検証が失敗すると、すべてのエラーが戻されます。

```py
from typing import Union
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    id: Union[int, str, UUID]
    name: str


user_01 = User(id=123, name='John Doe')
print(user_01)
#> id=123 name='John Doe'
print(user_01.id)
#> 123
user_02 = User(id='1234', name='John Doe')
print(user_02)
#> id='1234' name='John Doe'
print(user_02.id)
#> 1234
user_03_uuid = UUID('cf57432e-809e-4353-adbd-9d5c0d733868')
user_03 = User(id=user_03_uuid, name='John Doe')
print(user_03)
#> id=UUID('cf57432e-809e-4353-adbd-9d5c0d733868') name='John Doe'
print(user_03.id)
#> cf57432e-809e-4353-adbd-9d5c0d733868
print(user_03_uuid.int)
#> 275603287559914445491632874575877060712
```

!!! tip
    <!-- The type `Optional[x]` is a shorthand for `Union[x, None]`. -->
    型`Optional[x]`は`Union[x, None]`の省略形です。

    <!-- See more details in [Required fields](../concepts/models.md#required-fields). -->
    詳細については、[Required fields](../concepts/models.md#required-fields)を参照してください。

## Discriminated Unions

<!-- **Discriminated unions are sometimes referred to as "Tagged Unions".** -->
**識別されたUnionは、「タグ付きUnion」と呼ばれることがあります。**

<!-- We can use discriminated unions to more efficiently validate `Union` types, by choosing which member of the union to validate against. -->
識別されたUnionを使用して、どのUnionのメンバーに対して検証するかを選択することで、`Union`タイプをより効率的に検証することができる。

<!-- This makes validation more efficient and also avoids a proliferation of errors when validation fails. -->
これにより、検証がより効率的になり、検証が失敗した場合のエラーの急増も回避されます。

<!-- Adding discriminator to unions also means the generated JSON schema implements the [associated OpenAPI specification](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#discriminator-object). -->
Unionに識別子を追加することは、生成されたJSONスキーマが[associated OpenAPI specification](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#discriminator-object)を実装することも意味します。

### Discriminated Unions with `str` discriminators

<!-- Frequently, in the case of a `Union` with multiple models, there is a common field to all members of the union that can be used to distinguish which union case the data should be validated against; this is referred to as the "discriminator" in [OpenAPI](https://swagger.io/docs/specification/data-models/inheritance-and-polymorphism/). -->
多くの場合、複数のモデルを持つ`Union`の場合、Unionのすべてのメンバーに共通のフィールドがあり、どのUnionケースに対してデータを検証すべきかを区別するために使用できます。これは、[OpenAPI](https://swagger.io/docs/specification/data-models/inheritance-and-polymorphism/)では「識別子」と呼ばれています。

<!-- To validate models based on that information you can set the same field - let's call it `my_discriminator` - in each of the models with a discriminated value, which is one (or many) `Literal` value(s). -->
その情報に基づいてモデルを検証するには、同じフィールド(`my_discriminator`と呼びましょう)を、1つ(または複数)の`Literal`値である識別された値を持つ各モデルに設定します。
<!-- For your `Union`, you can set the discriminator in its value: `Field(discriminator='my_discriminator')`. -->
`Union`では、`Field(discriminator='my_discriminator')`の値に識別子を設定することができます。

```py requires="3.8"
from typing import Literal, Union

from pydantic import BaseModel, Field, ValidationError


class Cat(BaseModel):
    pet_type: Literal['cat']
    meows: int


class Dog(BaseModel):
    pet_type: Literal['dog']
    barks: float


class Lizard(BaseModel):
    pet_type: Literal['reptile', 'lizard']
    scales: bool


class Model(BaseModel):
    pet: Union[Cat, Dog, Lizard] = Field(..., discriminator='pet_type')
    n: int


print(Model(pet={'pet_type': 'dog', 'barks': 3.14}, n=1))
#> pet=Dog(pet_type='dog', barks=3.14) n=1
try:
    Model(pet={'pet_type': 'dog'}, n=1)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.dog.barks
      Field required [type=missing, input_value={'pet_type': 'dog'}, input_type=dict]
    """
```

### Discriminated Unions with callable `Discriminator`

??? api "API Documentation"
    [`pydantic.types.Discriminator`][pydantic.types.Discriminator]<br>

<!-- In the case of a `Union` with multiple models, sometimes there isn't a single uniform field across all models that you can use as a discriminator.
This is the perfect use case for a callable `Discriminator`. -->
複数のモデルを持つ`Union`の場合、すべてのモデルにわたって識別子として使用できる単一の均一なフィールドが存在しないことがあります。
これは、呼び出し可能な`Discriminator`の完璧なユースケースです。

```py requires="3.8"
from typing import Any, Literal, Union

from typing_extensions import Annotated

from pydantic import BaseModel, Discriminator, Tag


class Pie(BaseModel):
    time_to_cook: int
    num_ingredients: int


class ApplePie(Pie):
    fruit: Literal['apple'] = 'apple'


class PumpkinPie(Pie):
    filling: Literal['pumpkin'] = 'pumpkin'


def get_discriminator_value(v: Any) -> str:
    if isinstance(v, dict):
        return v.get('fruit', v.get('filling'))
    return getattr(v, 'fruit', getattr(v, 'filling', None))


class ThanksgivingDinner(BaseModel):
    dessert: Annotated[
        Union[
            Annotated[ApplePie, Tag('apple')],
            Annotated[PumpkinPie, Tag('pumpkin')],
        ],
        Discriminator(get_discriminator_value),
    ]


apple_variation = ThanksgivingDinner.model_validate(
    {'dessert': {'fruit': 'apple', 'time_to_cook': 60, 'num_ingredients': 8}}
)
print(repr(apple_variation))
"""
ThanksgivingDinner(dessert=ApplePie(time_to_cook=60, num_ingredients=8, fruit='apple'))
"""

pumpkin_variation = ThanksgivingDinner.model_validate(
    {
        'dessert': {
            'filling': 'pumpkin',
            'time_to_cook': 40,
            'num_ingredients': 6,
        }
    }
)
print(repr(pumpkin_variation))
"""
ThanksgivingDinner(dessert=PumpkinPie(time_to_cook=40, num_ingredients=6, filling='pumpkin'))
"""
```

<!-- `Discriminator`s can also be used to validate `Union` types with combinations of models and primitive types. -->
`Discriminator`は、モデルとプリミティブ型の組み合わせで`Union`型を検証するためにも使用できます。

For example:

```py requires="3.8"
from typing import Any, Union

from typing_extensions import Annotated

from pydantic import BaseModel, Discriminator, Tag, ValidationError


def model_x_discriminator(v: Any) -> str:
    if isinstance(v, int):
        return 'int'
    if isinstance(v, (dict, BaseModel)):
        return 'model'
    else:
        # return None if the discriminator value isn't found
        return None


class SpecialValue(BaseModel):
    value: int


class DiscriminatedModel(BaseModel):
    value: Annotated[
        Union[
            Annotated[int, Tag('int')],
            Annotated['SpecialValue', Tag('model')],
        ],
        Discriminator(model_x_discriminator),
    ]


model_data = {'value': {'value': 1}}
m = DiscriminatedModel.model_validate(model_data)
print(m)
#> value=SpecialValue(value=1)

int_data = {'value': 123}
m = DiscriminatedModel.model_validate(int_data)
print(m)
#> value=123

try:
    DiscriminatedModel.model_validate({'value': 'not an int or a model'})
except ValidationError as e:
    print(e)  # (1)!
    """
    1 validation error for DiscriminatedModel
    value
      Unable to extract tag using discriminator model_x_discriminator() [type=union_tag_not_found, input_value='not an int or a model', input_type=str]
    """
```

<!-- 1. Notice the callable discriminator function returns `None` if a discriminator value is not found.
   When `None` is returned, this `union_tag_not_found` error is raised. -->
1. 識別子の値が見つからない場合、呼び出し可能な識別子関数が`None`を返すことに注意してください。
`None`が返された場合、この`union_tag_not_found`エラーが発生します。

!!! note
    <!-- Using the [[`typing.Annotated`][] fields syntax](../concepts/types.md#composing-types-via-annotated) can be handy to regroup the `Union` and `discriminator` information. See the next example for more details. -->
    [[`typing.Annotated`][]fields syntax](./concepts/types.md#composing-types-via-annotated)を使用すると、`Union`および`discriminator`情報を簡単に再グループ化できます。詳細については、次の例を参照してください。

    <!-- There are a few ways to set a discriminator for a field, all varying slightly in syntax. -->
    フィールドに識別子を設定する方法はいくつかありますが、構文はわずかに異なります。

    <!-- For `str` discriminators: -->
    `str` 識別子の場合:
    ```
    some_field: Union[...] = Field(discriminator='my_discriminator'
    some_field: Annotated[Union[...], Field(discriminator='my_discriminator')]
    ```

    <!-- For callable `Discriminator`s: -->
    呼び出し可能な`Discriminator`の場合:
    ```
    some_field: Union[...] = Field(discriminator=Discriminator(...))
    some_field: Annotated[Union[...], Discriminator(...)]
    some_field: Annotated[Union[...], Field(discriminator=Discriminator(...))]
    ```

!!! warning
    <!-- Discriminated unions cannot be used with only a single variant, such as `Union[Cat]`. -->
    識別されたUnionは、`Union[Cat]`のような単一のバリアントでのみ使用することはできません。

    <!-- Python changes `Union[T]` into `T` at interpretation time, so it is not possible for `pydantic` to distinguish fields of `Union[T]` from `T`. -->
    Pythonは解釈時に`Union[T]`を`T`に変更するので、`pydantic`が`Union[T]`と`T`のフィールドを区別することはできません。

### Nested Discriminated Unions

<!-- Only one discriminator can be set for a field but sometimes you want to combine multiple discriminators.
You can do it by creating nested `Annotated` types, e.g.: -->
1つのフィールドに設定できる識別子は1つだけですが、複数の識別子を組み合わせたい場合があります。
これを行うには、ネストされた`Annotated`型を作成します。

```py requires="3.8"
from typing import Literal, Union

from typing_extensions import Annotated

from pydantic import BaseModel, Field, ValidationError


class BlackCat(BaseModel):
    pet_type: Literal['cat']
    color: Literal['black']
    black_name: str


class WhiteCat(BaseModel):
    pet_type: Literal['cat']
    color: Literal['white']
    white_name: str


Cat = Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]


class Dog(BaseModel):
    pet_type: Literal['dog']
    name: str


Pet = Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]


class Model(BaseModel):
    pet: Pet
    n: int


m = Model(pet={'pet_type': 'cat', 'color': 'black', 'black_name': 'felix'}, n=1)
print(m)
#> pet=BlackCat(pet_type='cat', color='black', black_name='felix') n=1
try:
    Model(pet={'pet_type': 'cat', 'color': 'red'}, n='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.cat
      Input tag 'red' found using 'color' does not match any of the expected tags: 'black', 'white' [type=union_tag_invalid, input_value={'pet_type': 'cat', 'color': 'red'}, input_type=dict]
    """
try:
    Model(pet={'pet_type': 'cat', 'color': 'black'}, n='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.cat.black.black_name
      Field required [type=missing, input_value={'pet_type': 'cat', 'color': 'black'}, input_type=dict]
    """
```

!!! tip
    <!-- If you want to validate data against a union, and solely a union, you can use pydantic's [`TypeAdapter`](../concepts/type_adapter.md) construct instead of inheriting from the standard `BaseModel`. -->
    Unionのみに対してデータを検証したい場合は、標準の`BaseModel`から継承する代わりに、pydanticの[`TypeAdapter`](../concepts/type_adapter.md)構文を使用できます。

    <!-- In the context of the previous example, we have the following: -->
    前の例では、次のようになります。

    ```python lint="skip" test="skip"
    type_adapter = TypeAdapter(Pet)

    pet = type_adapter.validate_python(
        {'pet_type': 'cat', 'color': 'black', 'black_name': 'felix'}
    )
    print(repr(pet))
    #> BlackCat(pet_type='cat', color='black', black_name='felix')
    ```

## Union Validation Errors

<!-- When `Union` validation fails, error messages can be quite verbose, as they will produce validation errors for each case in the union.
This is especially noticeable when dealing with recursive models, where reasons may be generated at each level of recursion.
Discriminated unions help to simplify error messages in this case, as validation errors are only produced for the case with a matching discriminator value. -->
`Union`の検証が失敗した場合、エラーメッセージは非常に冗長になる可能性があります。なぜなら、エラーメッセージはUnionの各ケースに対して検証エラーを生成するからです。
これは、再帰モデルを処理する場合に特に顕著であり、再帰の各レベルで理由が生成される可能性があります。
識別された結合は、この場合のエラーメッセージを単純化するのに役立つ。検証エラーは、識別値が一致する場合にのみ生成されるからです。

<!-- You can also customize the error type, message, and context for a `Discriminator` by passing these specifications as parameters to the `Discriminator` constructor, as seen in the example below. -->
以下の例に示すように、`Discriminator`コンストラクタにこれらの指定をパラメータとして渡すことで、`Discriminator`のエラータイプ、メッセージ、コンテキストをカスタマイズすることもできます。

```py
from typing import Union

from typing_extensions import Annotated

from pydantic import BaseModel, Discriminator, Tag, ValidationError


# Errors are quite verbose with a normal Union:
class Model(BaseModel):
    x: Union[str, 'Model']


try:
    Model.model_validate({'x': {'x': {'x': 1}}})
except ValidationError as e:
    print(e)
    """
    4 validation errors for Model
    x.str
      Input should be a valid string [type=string_type, input_value={'x': {'x': 1}}, input_type=dict]
    x.Model.x.str
      Input should be a valid string [type=string_type, input_value={'x': 1}, input_type=dict]
    x.Model.x.Model.x.str
      Input should be a valid string [type=string_type, input_value=1, input_type=int]
    x.Model.x.Model.x.Model
      Input should be a valid dictionary or instance of Model [type=model_type, input_value=1, input_type=int]
    """

try:
    Model.model_validate({'x': {'x': {'x': {}}}})
except ValidationError as e:
    print(e)
    """
    4 validation errors for Model
    x.str
      Input should be a valid string [type=string_type, input_value={'x': {'x': {}}}, input_type=dict]
    x.Model.x.str
      Input should be a valid string [type=string_type, input_value={'x': {}}, input_type=dict]
    x.Model.x.Model.x.str
      Input should be a valid string [type=string_type, input_value={}, input_type=dict]
    x.Model.x.Model.x.Model.x
      Field required [type=missing, input_value={}, input_type=dict]
    """


# Errors are much simpler with a discriminated union:
def model_x_discriminator(v):
    if isinstance(v, str):
        return 'str'
    if isinstance(v, (dict, BaseModel)):
        return 'model'


class DiscriminatedModel(BaseModel):
    x: Annotated[
        Union[
            Annotated[str, Tag('str')],
            Annotated['DiscriminatedModel', Tag('model')],
        ],
        Discriminator(
            model_x_discriminator,
            custom_error_type='invalid_union_member',  # (1)!
            custom_error_message='Invalid union member',  # (2)!
            custom_error_context={'discriminator': 'str_or_model'},  # (3)!
        ),
    ]


try:
    DiscriminatedModel.model_validate({'x': {'x': {'x': 1}}})
except ValidationError as e:
    print(e)
    """
    1 validation error for DiscriminatedModel
    x.model.x.model.x
      Invalid union member [type=invalid_union_member, input_value=1, input_type=int]
    """

try:
    DiscriminatedModel.model_validate({'x': {'x': {'x': {}}}})
except ValidationError as e:
    print(e)
    """
    1 validation error for DiscriminatedModel
    x.model.x.model.x.model.x
      Field required [type=missing, input_value={}, input_type=dict]
    """

# The data is still handled properly when valid:
data = {'x': {'x': {'x': 'a'}}}
m = DiscriminatedModel.model_validate(data)
print(m.model_dump())
#> {'x': {'x': {'x': 'a'}}}
```
<!--
1. `custom_error_type` is the `type` attribute of the `ValidationError` raised when validation fails.
2. `custom_error_message` is the `msg` attribute of the `ValidationError` raised when validation fails.
3. `custom_error_context` is the `ctx` attribute of the `ValidationError` raised when validation fails.
 -->
1. `custom_error_type`は、検証が失敗したときに発生する`ValidationError`の`type`属性です。
2. `custom_error_message`は、検証が失敗したときに発生する`ValidationError`の`msg`属性です。
3. `custom_error_context`は、検証が失敗したときに発生する`ValidationError`の`ctx`属性です。

<!-- You can also simplify error messages by labeling each case with a [`Tag`][pydantic.types.Tag].
This is especially useful when you have complex types like those in this example: -->
各ケースに[`Tag`][pydantic.types.Tag]というラベルを付けることで、エラーメッセージを簡略化することもできます。
これは、この例のような複雑な型がある場合に特に便利です。

```py
from typing import Dict, List, Union

from typing_extensions import Annotated

from pydantic import AfterValidator, Tag, TypeAdapter, ValidationError

DoubledList = Annotated[List[int], AfterValidator(lambda x: x * 2)]
StringsMap = Dict[str, str]


# Not using any `Tag`s for each union case, the errors are not so nice to look at
adapter = TypeAdapter(Union[DoubledList, StringsMap])

try:
    adapter.validate_python(['a'])
except ValidationError as exc_info:
    print(exc_info)
    """
    2 validation errors for union[function-after[<lambda>(), list[int]],dict[str,str]]
    function-after[<lambda>(), list[int]].0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    dict[str,str]
      Input should be a valid dictionary [type=dict_type, input_value=['a'], input_type=list]
    """

tag_adapter = TypeAdapter(
    Union[
        Annotated[DoubledList, Tag('DoubledList')],
        Annotated[StringsMap, Tag('StringsMap')],
    ]
)

try:
    tag_adapter.validate_python(['a'])
except ValidationError as exc_info:
    print(exc_info)
    """
    2 validation errors for union[DoubledList,StringsMap]
    DoubledList.0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    StringsMap
      Input should be a valid dictionary [type=dict_type, input_value=['a'], input_type=list]
    """
```
