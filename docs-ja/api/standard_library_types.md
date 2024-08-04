{% include-markdown "../warning.md" %}

---
description: Support for common types from the Python standard library.
---

<!-- Pydantic supports many common types from the Python standard library. If you need stricter processing see [Strict Types](../concepts/types.md#strict-types), including if you need to constrain the values allowed (e.g. to require a positive `int`). -->
Pydanticは、Python標準ライブラリから多くの一般的な型をサポートしています。より厳密な処理が必要な場合は、[Strict Types](../concepts/types.md#strict-types)を参照してください。これには、許可される値を制限する必要がある場合(たとえば、正の`int`を要求する場合)も含まれます。

## Booleans

<!-- A standard `bool` field will raise a `ValidationError` if the value is not one of the following: -->
標準の`bool`フィールドは、値が次のいずれでもない場合に`ValidationError`を発生させます。

<!-- * A valid boolean (i.e. `True` or `False`),
* The integers `0` or `1`,
* a `str` which when converted to lower case is one of `'0', 'off', 'f', 'false', 'n', 'no', '1', 'on', 't', 'true', 'y', 'yes'`
* a `bytes` which is valid per the previous rule when decoded to `str` -->
* 有効なブール値(すなわち`True`または`False`)
* 整数`0`または`1`
* 小文字に変換されたときに、"0"、"off"、"f"、"false"、"n"、"no"、"1"、"on"、"t"、"true"、"y"、"yes"のいずれかになる"str"
* `str`にデコードされたときに、前の規則に従った有効な`bytes`

!!! note
    <!-- If you want stricter boolean logic (e.g. a field which only permits `True` and `False`) you can  use [`StrictBool`](../api/types.md#pydantic.types.StrictBool). -->
    より厳密なブール論理(例えば、`True`と`False`のみを許可するフィールド)が必要な場合は、[`StrictBool`](../api/types.md#pydantic.types.StrictBool)を使用できます。

<!-- Here is a script demonstrating some of these behaviors: -->
次に、これらの動作の一部を示すスクリプトを示します。

```py
from pydantic import BaseModel, ValidationError


class BooleanModel(BaseModel):
    bool_value: bool


print(BooleanModel(bool_value=False))
#> bool_value=False
print(BooleanModel(bool_value='False'))
#> bool_value=False
print(BooleanModel(bool_value=1))
#> bool_value=True
try:
    BooleanModel(bool_value=[])
except ValidationError as e:
    print(str(e))
    """
    1 validation error for BooleanModel
    bool_value
      Input should be a valid boolean [type=bool_type, input_value=[], input_type=list]
    """
```

## Datetime Types

<!-- Pydantic supports the following [datetime](https://docs.python.org/library/datetime.html#available-types) types: -->
Pydanticは次の[datetime](https://docs.python.org/library/datetime.html#available-types)型をサポートしています。

### [`datetime.datetime`][]
<!-- * `datetime` fields will accept values of type: -->
* `datetime`フィールドは以下の型の値を受け付けます:

    <!-- * `datetime`; an existing `datetime` object
    * `int` or `float`; assumed as Unix time, i.e. seconds (if >= `-2e10` and <= `2e10`) or milliseconds (if < `-2e10`or > `2e10`) since 1 January 1970
    * `str`; the following formats are accepted:
        * `YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`
        * `YYYY-MM-DD` is accepted in lax mode, but not in strict mode
        * `int` or `float` as a string (assumed as Unix time)
    * [`datetime.date`][] instances are accepted in lax mode, but not in strict mode -->

    * `datetime`; 既存の`datetime`オブジェクト
    * `int`または`float`; 1970年1月1日からのUnix時間、つまり秒(>=`-2e10`および<=`2e10`の場合)またはミリ秒(<`-2e10`または>`2e10`の場合)と見なされます。
    * `str`; 以下のフォーマットが使用できます。
    * `YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or[±]HH[:]MM]`
    * [`datetime.date`][]インスタンスはlaxモードでは受け付けられますが、strictモードでは受け付けられません。
    * 文字列としての`int`または`float`(Unix時間と仮定)

```py
from datetime import datetime

from pydantic import BaseModel


class Event(BaseModel):
    dt: datetime = None


event = Event(dt='2032-04-23T10:20:30.400+02:30')

print(event.model_dump())
"""
{'dt': datetime.datetime(2032, 4, 23, 10, 20, 30, 400000, tzinfo=TzInfo(+02:30))}
"""
```

### [`datetime.date`][]
<!-- * `date` fields will accept values of type: -->
*`date`フィールドは以下の型の値を受け付けます:

    <!--
    * `date`; an existing `date` object
    * `int` or `float`; handled the same as described for `datetime` above
    * `str`; the following formats are accepted:
        * `YYYY-MM-DD`
        * `int` or `float` as a string (assumed as Unix time)
    -->
    * `date`; 既存の`date`オブジェクト
    * `int`または`float`; 上記の`datetime`と同じように扱われます。
    * `str`; 以下のフォーマットが使用できます。
        * `YYYY-MM-DD`
        * 文字列としての`int`または`float`(Unix時間と仮定)



```py
from datetime import date

from pydantic import BaseModel


class Birthday(BaseModel):
    d: date = None


my_birthday = Birthday(d=1679616000.0)

print(my_birthday.model_dump())
#> {'d': datetime.date(2023, 3, 24)}
```

### [`datetime.time`][]
<!-- * `time` fields will accept values of type: -->
* `time`フィールドは以下の型の値を受け付けます:

    <!-- * `time`; an existing `time` object
    * `str`; the following formats are accepted:
        * `HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`
     -->
    * `time`; 既存の`time`オブジェクト
    * `str`; 以下のフォーマットが使用できます。
        * `HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`



```py
from datetime import time

from pydantic import BaseModel


class Meeting(BaseModel):
    t: time = None


m = Meeting(t=time(4, 8, 16))

print(m.model_dump())
#> {'t': datetime.time(4, 8, 16)}
```

### [`datetime.timedelta`][]
<!-- * `timedelta` fields will accept values of type: -->
* `timedelta`フィールドは以下の型の値を受け付けます:

    <!--
    * `timedelta`; an existing `timedelta` object
    * `int` or `float`; assumed to be seconds
    * `str`; the following formats are accepted:
        * `[-][DD]D[,][HH:MM:]SS[.ffffff]`
            * Ex: `'1d,01:02:03.000004'` or `'1D01:02:03.000004'` or `'01:02:03'`
        * `[±]P[DD]DT[HH]H[MM]M[SS]S` ([ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) タイムデルタフォーマット)
    -->

    * `timedelta`; 既存の`timedelta`オブジェクト
    * `int`または`float`; 秒と見なされます
    * `str`; 以下のフォーマットが使用できます。
        * `[-][DD]D[,][HH:MM:]SS[.ffffff]`
            * 例: `'1d,01:02:03.000004'` または `'1D01:02:03.000004'` または `'01:02:03'`
        * `[±]P[DD]DT[HH]H[MM]M[SS]S` ([ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) タイムデルタフォーマット)

```py
from datetime import timedelta

from pydantic import BaseModel


class Model(BaseModel):
    td: timedelta = None


m = Model(td='P3DT12H30M5S')

print(m.model_dump())
#> {'td': datetime.timedelta(days=3, seconds=45005)}
```

## Number Types

<!-- Pydantic supports the following numeric types from the Python standard library: -->
Pydanticは、Python標準ライブラリから次の数値型をサポートしています。

### [`int`][]

<!-- * Pydantic uses `int(v)` to coerce types to an `int`; -->
* Pydanticは型を`int`に強制するために`int(v)`を使用します。
  <!-- see [Data conversion](../concepts/models.md#data-conversion) for details on loss of information during data conversion. -->
  データ変換中の情報損失の詳細については、[Data conversion](../concepts/models.md#data-conversion)を参照してください。

### [`float`][]

<!-- * Pydantic uses `float(v)` to coerce values to floats. -->
* Pydanticは`float(v)`を使用して値を浮動小数点に変換します。

### [`enum.IntEnum`][]

<!-- * Validation: Pydantic checks that the value is a valid `IntEnum` instance. -->
* バリデーション: Pydanticは、値が有効な`IntEnum`インスタンスであることを確認します。
<!-- * Validation for subclass of `enum.IntEnum`: checks that the value is a valid member of the integer enum; -->
* `enum.IntEnum`のサブクラスのバリデーション: 値が整数列挙型の有効なメンバーであることをチェックします;
  <!-- see [Enums and Choices](#enum) for more details. -->
  詳細については、[Enums and Choices](#enum)を参照してください。



### [`decimal.Decimal`][]

<!-- * Validation: Pydantic attempts to convert the value to a string, then passes the string to `Decimal(v)`.
* Serialization: Pydantic serializes [`Decimal`][decimal.Decimal] types as strings. -->
* 検証: Pydanticは値を文字列に変換してから、その文字列を`Decimal(v)`に渡します。
* シリアライゼーション: Pydanticは[`Decimal`][decimal.Decimal]型を文字列としてシリアライズします。
<!-- You can use a custom serializer to override this behavior if desired. For example: -->
必要に応じて、カスタム・シリアライザを使用してこの動作を上書きできます。次に例を示します。

```py
from decimal import Decimal

from typing_extensions import Annotated

from pydantic import BaseModel, PlainSerializer


class Model(BaseModel):
    x: Decimal
    y: Annotated[
        Decimal,
        PlainSerializer(
            lambda x: float(x), return_type=float, when_used='json'
        ),
    ]


my_model = Model(x=Decimal('1.1'), y=Decimal('2.1'))

print(my_model.model_dump())  # (1)!
#> {'x': Decimal('1.1'), 'y': Decimal('2.1')}
print(my_model.model_dump(mode='json'))  # (2)!
#> {'x': '1.1', 'y': 2.1}
print(my_model.model_dump_json())  # (3)!
#> {"x":"1.1","y":2.1}
```

<!--
1. Using [`model_dump`][pydantic.main.BaseModel.model_dump], both `x` and `y` remain instances of the `Decimal` type
2. Using [`model_dump`][pydantic.main.BaseModel.model_dump] with `mode='json'`, `x` is serialized as a `string`, and `y` is serialized as a `float` because of the custom serializer applied.
3. Using [`model_dump_json`][pydantic.main.BaseModel.model_dump_json], `x` is serialized as a `string`, and `y` is serialized as a `float` because of the custom serializer applied.
 -->
1. [`model_dump`][pydantic.main.BaseModel.model_dump]を使用すると、`x`と`y`の両方が`Decimal`型のインスタンスのままになります
2. [`model_dump`][pydantic.main.BaseModel.model_dump]を`mode='json'`で使用すると、`x`は`string`としてシリアライズされ、`y`はカスタムシリアライザが適用されているため`float`としてシリアライズされます。
3. [`model_dump_json`][pydantic.main.BaseModel.model_dump_json]を使用すると、`x`は`string`としてシリアライズされ、`y`はカスタムシリアライザが適用されているため`float`としてシリアライズされます。

## [`Enum`][enum.Enum]

<!-- Pydantic uses Python's standard [`enum`][] classes to define choices. -->
PydanticはPythonの標準の[`enum`][]クラスを使って選択肢を定義します。

<!-- `enum.Enum` checks that the value is a valid `Enum` instance.
Subclass of `enum.Enum` checks that the value is a valid member of the enum. -->
`enum.Enum`は、値が有効な`Enum`インスタンスであることをチェックします。
`enum.Enum`のサブクラスは、値が列挙型の有効なメンバーであることをチェックします。

```py
from enum import Enum, IntEnum

from pydantic import BaseModel, ValidationError


class FruitEnum(str, Enum):
    pear = 'pear'
    banana = 'banana'


class ToolEnum(IntEnum):
    spanner = 1
    wrench = 2


class CookingModel(BaseModel):
    fruit: FruitEnum = FruitEnum.pear
    tool: ToolEnum = ToolEnum.spanner


print(CookingModel())
#> fruit=<FruitEnum.pear: 'pear'> tool=<ToolEnum.spanner: 1>
print(CookingModel(tool=2, fruit='banana'))
#> fruit=<FruitEnum.banana: 'banana'> tool=<ToolEnum.wrench: 2>
try:
    CookingModel(fruit='other')
except ValidationError as e:
    print(e)
    """
    1 validation error for CookingModel
    fruit
      Input should be 'pear' or 'banana' [type=enum, input_value='other', input_type=str]
    """
```

## Lists and Tuples

### [`list`][]

<!-- Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`list`][].
When a generic parameter is provided, the appropriate validation is applied to all items of the list. -->
[`list`][]、[`tuple`][]、[`set`][]、[`frozenset`][]、[`deque`][collections.deque]、またはジェネレータと[`list`][]へのキャストを許可します。
汎用パラメータを指定すると、適切な検証がリストのすべての項目に適用されます。

### [`typing.List`][]

<!-- Handled the same as `list` above. -->
上記の`list`と同じように扱われます。

```py
from typing import List, Optional

from pydantic import BaseModel


class Model(BaseModel):
    simple_list: Optional[list] = None
    list_of_ints: Optional[List[int]] = None


print(Model(simple_list=['1', '2', '3']).simple_list)
#> ['1', '2', '3']
print(Model(list_of_ints=['1', '2', '3']).list_of_ints)
#> [1, 2, 3]
```

### [`tuple`][]

<!-- Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`tuple`][].
When generic parameters are provided, the appropriate validation is applied to the respective items of the tuple -->
[`list`][]、[`tuple`][]、[`set`][]、[`frozenset`][]、[`deque`][collections.deque]、またはジェネレータと[`tuple`][]へのキャストを許可します。
汎用パラメータが提供される場合、適切な検証がタプルの各項目に適用されます。

### [`typing.Tuple`][]

<!-- Handled the same as `tuple` above. -->
上記の`tuple`と同じように扱われます。

```py
from typing import Optional, Tuple

from pydantic import BaseModel


class Model(BaseModel):
    simple_tuple: Optional[tuple] = None
    tuple_of_different_types: Optional[Tuple[int, float, bool]] = None


print(Model(simple_tuple=[1, 2, 3, 4]).simple_tuple)
#> (1, 2, 3, 4)
print(Model(tuple_of_different_types=[3, 2, 1]).tuple_of_different_types)
#> (3, 2.0, True)
```

### [`typing.NamedTuple`][]

<!-- Subclasses of [`typing.NamedTuple`][] are similar to `tuple`, but create instances of the given `namedtuple` class. -->
[`typing.NamedTuple`][]のサブクラスは`tuple`に似ていますが、与えられた`NamedTuple`クラスのインスタンスを作成します。

<!-- Subclasses of [`collections.namedtuple`][] are similar to subclass of [`typing.NamedTuple`][], but since field types are not specified, all fields are treated as having type [`Any`][typing.Any]. -->
[`collections.namedtuple`][]のサブクラスは、[`typing.NamedTuple`][]のサブクラスと似ていますが、フィールド型が指定されていないので、すべてのフィールドは[`Any`][typing.Any]型として扱われます。

```py
from typing import NamedTuple

from pydantic import BaseModel, ValidationError


class Point(NamedTuple):
    x: int
    y: int


class Model(BaseModel):
    p: Point


try:
    Model(p=('1.3', '2'))
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    p.0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='1.3', input_type=str]
    """
```

## Deque

### [`deque`][collections.deque]

<!-- Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`deque`][collections.deque].
When generic parameters are provided, the appropriate validation is applied to the respective items of the `deque`. -->
[`list`][]、[`tuple`][]、[`set`][]、[`frozenset`][]、[`deque`][collections.deque]、またはジェネレータと[`deque`][collections.deque]へのキャストを許可します。
一般的なパラメータが与えられると、適切な検証が`deque`の各項目に適用されます。

### [`typing.Deque`][]

Handled the same as `deque` above.

```py
from typing import Deque, Optional

from pydantic import BaseModel


class Model(BaseModel):
    deque: Optional[Deque[int]] = None


print(Model(deque=[1, 2, 3]).deque)
#> deque([1, 2, 3])
```

## Sets

### [`set`][]

<!-- Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`set`][].
When a generic parameter is provided, the appropriate validation is applied to all items of the set. -->
[`list`][]、[`tuple`][]、[`set`][]、[`frozenset`][]、[`deque`][collections.deque]、またはジェネレータと[`set`][]へのキャストを許可します。
汎用パラメータを指定すると、セットのすべてのアイテムに適切な検証が適用されます。

### [`typing.Set`][]

<!-- Handled the same as `set` above. -->
上記の`set`と同じように扱われます。

```py
from typing import Optional, Set

from pydantic import BaseModel


class Model(BaseModel):
    simple_set: Optional[set] = None
    set_of_ints: Optional[Set[int]] = None


print(Model(simple_set={'1', '2', '3'}).simple_set)
#> {'1', '2', '3'}
print(Model(simple_set=['1', '2', '3']).simple_set)
#> {'1', '2', '3'}
print(Model(set_of_ints=['1', '2', '3']).set_of_ints)
#> {1, 2, 3}
```

### [`frozenset`][]

<!-- Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`frozenset`][].
When a generic parameter is provided, the appropriate validation is applied to all items of the frozen set. -->
[`list`][]、[`tuple`][]、[`set`][]、[`frozenset`][]、[`deque`][collections.deque]、またはジェネレータと[`frozenset`][]へのキャストを許可します。
汎用パラメータを指定すると、フリーズされたセットのすべてのアイテムに適切な検証が適用されます。

### [`typing.FrozenSet`][]

<!-- Handled the same as `frozenset` above. -->
上記の`frozenset`と同じように扱われます。

```py
from typing import FrozenSet, Optional

from pydantic import BaseModel


class Model(BaseModel):
    simple_frozenset: Optional[frozenset] = None
    frozenset_of_ints: Optional[FrozenSet[int]] = None


m1 = Model(simple_frozenset=['1', '2', '3'])
print(type(m1.simple_frozenset))
#> <class 'frozenset'>
print(sorted(m1.simple_frozenset))
#> ['1', '2', '3']

m2 = Model(frozenset_of_ints=['1', '2', '3'])
print(type(m2.frozenset_of_ints))
#> <class 'frozenset'>
print(sorted(m2.frozenset_of_ints))
#> [1, 2, 3]
```


## Other Iterables

### [`typing.Sequence`][]

<!-- This is intended for use when the provided value should meet the requirements of the `Sequence` ABC, and it is desirable to do eager validation of the values in the container. -->
これは、提供された値が`Sequence`ABCの要件を満たす必要があり、コンテナ内の値を積極的に検証することが望ましい場合に使用することを意図しています。
<!-- Note that when validation must be performed on the values of the container, the type of the container may not be preserved since validation may end up replacing values. -->
コンテナの値に対して検証を実行する必要がある場合、検証によって値が置き換えられる可能性があるため、コンテナのタイプが保持されない可能性があることに注意してください。
<!-- We guarantee that the validated value will be a valid [`typing.Sequence`][], but it may have a different type than was provided (generally, it will become a `list`). -->
検証された値が有効な[`typing.Sequence`][]であることを保証しますが、提供されたものとは異なる型を持つ可能性があります(一般的には`list`になります)。

### [`typing.Iterable`][]

<!-- This is intended for use when the provided value may be an iterable that shouldn't be consumed.
See [Infinite Generators](#infinite-generators) below for more detail on parsing and validation. -->
これは、提供された値が消費されるべきではないiterableである場合に使用することを意図しています。
解析と検証の詳細については、以下の[Infinite Generators](#infinite-generators)を参照してください。
<!-- Similar to [`typing.Sequence`][], we guarantee that the validated result will be a valid [`typing.Iterable`][], but it may have a different type than was provided. In particular, even if a non-generator type such as a `list` is provided, the post-validation value of a field of type [`typing.Iterable`][] will be a generator. -->
[`typing.Sequence`][]と同様に、検証された結果が有効な[`typing.Iterable`][]であることを保証しますが、提供されたものとは異なる型を持つ可能性があります。特に、`list`のような非ジェネレータ型が提供された場合でも、[`typing.Iterable`][]型のフィールドの検証後の値はジェネレータになります。

<!-- Here is a simple example using [`typing.Sequence`][]: -->
以下は、[`typing.Sequence`][]を使用した簡単な例です。

```py
from typing import Sequence

from pydantic import BaseModel


class Model(BaseModel):
    sequence_of_ints: Sequence[int] = None


print(Model(sequence_of_ints=[1, 2, 3, 4]).sequence_of_ints)
#> [1, 2, 3, 4]
print(Model(sequence_of_ints=(1, 2, 3, 4)).sequence_of_ints)
#> (1, 2, 3, 4)
```

### Infinite Generators

<!-- If you have a generator you want to validate, you can still use `Sequence` as described above.
In that case, the generator will be consumed and stored on the model as a list and its values will be validated against the type parameter of the `Sequence` (e.g. `int` in `Sequence[int]`). -->
検証したいジェネレータがある場合は、上記のように`Sequence`を使うことができます。
この場合、ジェネレータが消費されてリストとしてモデルに保存され、その値が`Sequence`の型パラメータ(例えば`int`in`Sequence[int]`)に対して検証されます。

<!-- However, if you have a generator that you _don't_ want to be eagerly consumed (e.g. an infinite generator or a remote data loader), you can use a field of type [`Iterable`][typing.Iterable]: -->
しかし、あまり使われたくないジェネレータ(無限ジェネレータやリモートデータローダなど)がある場合は、[`Iterable`][typing.Iterable]型のフィールドを使うことができます。

```py
from typing import Iterable

from pydantic import BaseModel


class Model(BaseModel):
    infinite: Iterable[int]


def infinite_ints():
    i = 0
    while True:
        yield i
        i += 1


m = Model(infinite=infinite_ints())
print(m)
"""
infinite=ValidatorIterator(index=0, schema=Some(Int(IntValidator { strict: false })))
"""

for i in m.infinite:
    print(i)
    #> 0
    #> 1
    #> 2
    #> 3
    #> 4
    #> 5
    #> 6
    #> 7
    #> 8
    #> 9
    #> 10
    if i == 10:
        break
```

!!! warning
    <!-- During initial validation, `Iterable` fields only perform a simple check that the provided argument is iterable.
    To prevent it from being consumed, no validation of the yielded values is performed eagerly. -->
    最初の検証では、`Iterable`フィールドは与えられた引数がiterableであるかどうかの単純なチェックのみを行います。
    それが消費されないようにするために、得られた値の検証は熱心に行われない。

<!-- Though the yielded values are not validated eagerly, they are still validated when yielded, and will raise a `ValidationError` at yield time when appropriate: -->
生成された値はすぐには検証されませんが、生成時には検証され、適切な場合には生成時に`ValidationError`が発生します。

```python
from typing import Iterable

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    int_iterator: Iterable[int]


def my_iterator():
    yield 13
    yield '27'
    yield 'a'


m = Model(int_iterator=my_iterator())
print(next(m.int_iterator))
#> 13
print(next(m.int_iterator))
#> 27
try:
    next(m.int_iterator)
except ValidationError as e:
    print(e)
    """
    1 validation error for ValidatorIterator
    2
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """
```

## Mapping Types

### [`dict`][]

<!-- `dict(v)` is used to attempt to convert a dictionary. see [`typing.Dict`][] below for sub-type constraints. -->
`dict(v)`は辞書を変換するために使用されます。サブタイプの制約については以下の[`typing.Dict`][]を参照してください。

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: dict


m = Model(x={'foo': 1})
print(m.model_dump())
#> {'x': {'foo': 1}}

try:
    Model(x='test')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    x
      Input should be a valid dictionary [type=dict_type, input_value='test', input_type=str]
    """
```

### [`typing.Dict`][]

```py
from typing import Dict

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: Dict[str, int]


m = Model(x={'foo': 1})
print(m.model_dump())
#> {'x': {'foo': 1}}

try:
    Model(x={'foo': '1'})
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    x
      Input should be a valid dictionary [type=dict_type, input_value='test', input_type=str]
    """
```

### TypedDict

!!! note
    <!-- This is a new feature of the Python standard library as of Python 3.8.
    Because of limitations in [typing.TypedDict][] before 3.12, the [typing-extensions](https://pypi.org/project/typing-extensions/) package is required for Python <3.12. You'll need to import `TypedDict` from `typing_extensions` instead of `typing` and will get a build time error if you don't.
    これは、Python 3.8のPython標準ライブラリの新機能です。 -->
    3.12より前の[typing.TypedDict][]の制限により、Python<3.12には[typing-extensions](https://pypi.org/project/typing-extension/)パッケージが必要です。`typing`の代わりに`typing_extensions`から`TypedDict`をインポートする必要があり、インポートしないとビルド時エラーが発生します。

<!-- [`TypedDict`][typing.TypedDict] declares a dictionary type that expects all of its instances to have a certain set of keys, where each key is associated with a value of a consistent type. -->
[`TypedDict`][typing.TypedDict]は、すべてのインスタンスが特定のキーのセットを持つことを期待する辞書型を宣言します。各キーは一貫した型の値に関連付けられています。

<!-- It is same as [`dict`][] but Pydantic will validate the dictionary since keys are annotated. -->
[`dict`][]と同じですが、キーには注釈が付けられているので、Pydanticは辞書を検証します。

```py
from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError


class User(TypedDict):
    name: str
    id: int


ta = TypeAdapter(User)

print(ta.validate_python({'name': 'foo', 'id': 1}))
#> {'name': 'foo', 'id': 1}

try:
    ta.validate_python({'name': 'foo'})
except ValidationError as e:
    print(e)
    """
    1 validation error for typed-dict
    id
      Field required [type=missing, input_value={'name': 'foo'}, input_type=dict]
    """
```

<!-- You can define `__pydantic_config__` to change the model inherited from [`TypedDict`][typing.TypedDict].
See the [`ConfigDict` API reference][pydantic.config.ConfigDict] for more details. -->
`__pydantic_config__`を定義して、[`TypedDict`][typing.TypedDict]から継承されたモデルを変更することができます。
詳細については、[`ConfigDict`API reference][pydantic.config.ConfigDict]を参照してください。

```py
from typing import Optional

from typing_extensions import TypedDict

from pydantic import ConfigDict, TypeAdapter, ValidationError


# `total=False` means keys are non-required
class UserIdentity(TypedDict, total=False):
    name: Optional[str]
    surname: str


class User(TypedDict):
    __pydantic_config__ = ConfigDict(extra='forbid')

    identity: UserIdentity
    age: int


ta = TypeAdapter(User)

print(
    ta.validate_python(
        {'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}
    )
)
#> {'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}

print(
    ta.validate_python(
        {'identity': {'name': None, 'surname': 'John'}, 'age': 37}
    )
)
#> {'identity': {'name': None, 'surname': 'John'}, 'age': 37}

print(ta.validate_python({'identity': {}, 'age': 37}))
#> {'identity': {}, 'age': 37}


try:
    ta.validate_python(
        {'identity': {'name': ['Smith'], 'surname': 'John'}, 'age': 24}
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for typed-dict
    identity.name
      Input should be a valid string [type=string_type, input_value=['Smith'], input_type=list]
    """

try:
    ta.validate_python(
        {
            'identity': {'name': 'Smith', 'surname': 'John'},
            'age': '37',
            'email': 'john.smith@me.com',
        }
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for typed-dict
    email
      Extra inputs are not permitted [type=extra_forbidden, input_value='john.smith@me.com', input_type=str]
    """
```

## Callable

<!-- See below for more detail on parsing and validation -->
解析と検証の詳細については、以下を参照してください。

<!-- Fields can also be of type [`Callable`][typing.Callable]: -->
フィールドは[`Callable`][typing.Callable]型にすることもできます。

```py
from typing import Callable

from pydantic import BaseModel


class Foo(BaseModel):
    callback: Callable[[int], int]


m = Foo(callback=lambda x: x)
print(m)
#> callback=<function <lambda> at 0x0123456789ab>
```

!!! warning
    <!-- Callable fields only perform a simple check that the argument is callable; no validation of arguments, their types, or the return type is performed. -->
    呼び出し可能フィールドは、引数が呼び出し可能であることの単純なチェックのみを実行します。引数、その型、または戻り値の型の検証は実行されません。


## IP Address Types

<!-- * [`ipaddress.IPv4Address`][]: Uses the type itself for validation by passing the value to `IPv4Address(v)`.
* [`ipaddress.IPv4Interface`][]: Uses the type itself for validation by passing the value to `IPv4Address(v)`.
* [`ipaddress.IPv4Network`][]: Uses the type itself for validation by passing the value to `IPv4Network(v)`.
* [`ipaddress.IPv6Address`][]: Uses the type itself for validation by passing the value to `IPv6Address(v)`.
* [`ipaddress.IPv6Interface`][]: Uses the type itself for validation by passing the value to `IPv6Interface(v)`.
* [`ipaddress.IPv6Network`][]: Uses the type itself for validation by passing the value to `IPv6Network(v)`. -->
* [`ipaddress.IPv4Address`][]: 値を`IPv4Address(v)`に渡すことで、型自体を検証に使用します。
* [`ipaddress.IPv4Interface`][]: 値を`IPv4Address(v)`に渡すことで、型自体を検証に使用します。
* [`ipaddress.IPv4Network`][]: 値を`IPv4Network(v)`に渡すことで、型自体を検証に使用します。
* [`ipaddress.IPv6Address`][]: 値を`IPv6Address(v)`に渡すことで、型自体を検証に使用します。
* [`ipaddress.IPv6Interface`][]: 値を`IPv6Interface(v)`に渡すことで、型自体を検証に使用します。
* [`ipaddress.IPv6Network`][]: 値を`IPv6Network(v)`に渡すことで、型自体を検証に使用します。

<!-- See [Network Types](../api/networks.md) for other custom IP address types. -->
その他のカスタムIPアドレスタイプについては、[Network Types](../api/networks.md)を参照してください。



## UUID

<!-- For UUID, Pydantic tries to use the type itself for validation by passing the value to `UUID(v)`.
There's a fallback to `UUID(bytes=v)` for `bytes` and `bytearray`. -->
UUIDの場合、Pydanticは`UUID(v)`に値を渡すことで、型自体を検証に使用しようとします。
`bytes`と`bytearray`には`UUID(bytes=v)`へのフォールバックがあります。

<!-- In case you want to constrain the UUID version, you can check the following types: -->
UUIDバージョンを制限する場合は、次のタイプをチェックします。

<!--
* [`UUID1`][pydantic.types.UUID1]: requires UUID version 1.
* [`UUID3`][pydantic.types.UUID3]: requires UUID version 3.
* [`UUID4`][pydantic.types.UUID4]: requires UUID version 4.
* [`UUID5`][pydantic.types.UUID5]: requires UUID version 5.
-->
* [`UUID1`][pydantic.types.UUID1]: UUIDバージョン1が必要です。
* [`UUID3`][pydantic.types.UUID3]: UUIDバージョン3が必要です。
* [`UUID4`][pydantic.types.UUID4]: UUIDバージョン4が必要です。
* [`UUID5`][pydantic.types.UUID5]: UUIDバージョン5が必要です。

## Union

<!-- Pydantic has extensive support for union validation, both [`typing.Union`][] and Python 3.10's pipe syntax (`A | B`) are supported.
Read more in the [`Unions`](../concepts/unions.md) section of the concepts docs. -->
Pydanticはユニオン検証を幅広くサポートしており、[`typing.Union`][]とPython 3.10のパイプ構文(`A B`)の両方がサポートされています。
詳細はconcepts docsの[`Unions`](../concepts/unions.md)セクションを読んでください。

## [`Type`][typing.Type] and [`TypeVar`][typing.TypeVar]

### [`type`][]

<!-- Pydantic supports the use of `type[T]` to specify that a field may only accept classes (not instances) that are subclasses of `T`. -->
Pydanticでは、`type[T]`を使用して、フィールドが`T`のサブクラスであるクラス(インスタンスではない)のみを受け入れるように指定できます。

### [`typing.Type`][]

<!-- Handled the same as `type` above. -->
上記の`type`と同様に扱われます。

```py
from typing import Type

from pydantic import BaseModel, ValidationError


class Foo:
    pass


class Bar(Foo):
    pass


class Other:
    pass


class SimpleModel(BaseModel):
    just_subclasses: Type[Foo]


SimpleModel(just_subclasses=Foo)
SimpleModel(just_subclasses=Bar)
try:
    SimpleModel(just_subclasses=Other)
except ValidationError as e:
    print(e)
    """
    1 validation error for SimpleModel
    just_subclasses
      Input should be a subclass of Foo [type=is_subclass_of, input_value=<class '__main__.Other'>, input_type=type]
    """
```

<!-- You may also use `Type` to specify that any class is allowed. -->
`Type`を使用して、任意のクラスを許可するように指定することもできます。

```py upgrade="skip"
from typing import Type

from pydantic import BaseModel, ValidationError


class Foo:
    pass


class LenientSimpleModel(BaseModel):
    any_class_goes: Type


LenientSimpleModel(any_class_goes=int)
LenientSimpleModel(any_class_goes=Foo)
try:
    LenientSimpleModel(any_class_goes=Foo())
except ValidationError as e:
    print(e)
    """
    1 validation error for LenientSimpleModel
    any_class_goes
      Input should be a type [type=is_type, input_value=<__main__.Foo object at 0x0123456789ab>, input_type=Foo]
    """
```

### [`typing.TypeVar`][]

<!-- [`TypeVar`][typing.TypeVar] is supported either unconstrained, constrained or with a bound. -->
[`TypeVar`][typing.TypeVar]は、アンバインド、バインド、または境界付きのいずれかでサポートされています。

```py
from typing import TypeVar

from pydantic import BaseModel

Foobar = TypeVar('Foobar')
BoundFloat = TypeVar('BoundFloat', bound=float)
IntStr = TypeVar('IntStr', int, str)


class Model(BaseModel):
    a: Foobar  # equivalent of ": Any"
    b: BoundFloat  # equivalent of ": float"
    c: IntStr  # equivalent of ": Union[int, str]"


print(Model(a=[1], b=4.2, c='x'))
#> a=[1] b=4.2 c='x'

# a may be None
print(Model(a=None, b=1, c=1))
#> a=None b=1.0 c=1
```

## None Types

<!-- [`None`][], `type(None)`, or `Literal[None]` are all equivalent according to [the typing specification](https://typing.readthedocs.io/en/latest/spec/special-types.html#none). -->
[`None`][]、`type(None)`、または`Literal[None]`はすべて、[the typing specification](https://typing.readthedocs.io/en/latest/spec/special-types.html#none)に従って等価です。
<!-- Allows only `None` value. -->
`None`値のみを許可します。

## Strings

<!-- `str`: Strings are accepted as-is. `bytes` and `bytearray` are converted using `v.decode()`.
Enum`s inheriting from `str` are converted using `v.value`. All other types cause an error. -->
`str`:文字列はそのまま受け入れられます。`bytes`と`bytearray`は`v.decode()`を使って変換されます。
`str`から継承した列挙型は`v.value`を使用して変換されます。他のすべての型はエラーを引き起こします。
<!-- * TODO: add note about optional number to string conversion from lig's PR -->

!!! warning "Strings aren't Sequences"

    <!-- While instances of `str` are technically valid instances of the `Sequence[str]` protocol from a type-checker's point of view, this is frequently not intended as is a common source of bugs. -->
    型チェッカーの観点から見ると、`str`のインスタンスは技術的には`Sequence[str]`プロトコルの有効なインスタンスですが、これはバグの一般的な原因として意図されていないことがよくあります。

    <!-- As a result, Pydantic raises a `ValidationError` if you attempt to pass a `str` or `bytes` instance into a field of type `Sequence[str]` or `Sequence[bytes]`: -->
    その結果、`str`または`bytes`インスタンスを`Sequence[str]`型または`Sequence[bytes]`型のフィールドに渡そうとすると、Pydanticは`ValidationError`を発生させます。



```py
from typing import Optional, Sequence

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    sequence_of_strs: Optional[Sequence[str]] = None
    sequence_of_bytes: Optional[Sequence[bytes]] = None


print(Model(sequence_of_strs=['a', 'bc']).sequence_of_strs)
#> ['a', 'bc']
print(Model(sequence_of_strs=('a', 'bc')).sequence_of_strs)
#> ('a', 'bc')
print(Model(sequence_of_bytes=[b'a', b'bc']).sequence_of_bytes)
#> [b'a', b'bc']
print(Model(sequence_of_bytes=(b'a', b'bc')).sequence_of_bytes)
#> (b'a', b'bc')


try:
    Model(sequence_of_strs='abc')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    sequence_of_strs
      'str' instances are not allowed as a Sequence value [type=sequence_str, input_value='abc', input_type=str]
    """
try:
    Model(sequence_of_bytes=b'abc')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    sequence_of_bytes
      'bytes' instances are not allowed as a Sequence value [type=sequence_str, input_value=b'abc', input_type=bytes]
    """
```

## Bytes

<!-- [`bytes`][] are accepted as-is. [`bytearray`][] is converted using `bytes(v)`. `str` are converted using `v.encode()`. `int`, `float`, and `Decimal` are coerced using `str(v).encode()`. See [ByteSize](types.md#pydantic.types.ByteSize) for more details. -->
[`bytes`][]はそのまま受け入れられます。[`bytearray`][]は`bytes(v)`を使って変換されます。`str`は`v.encode()`を使って変換されます。`int`、`float`、`Decimal`は`str(v).encode()`を使って強制されます。詳細は[ByteSize](types.md#pydantic.types.ByteSize)を参照してください。

## [`typing.Literal`][]

<!-- Pydantic supports the use of [`typing.Literal`][] as a lightweight way to specify that a field may accept only specific literal values: -->
Pydanticは、フィールドが特定のリテラル値のみを受け入れることを指定する軽量な方法として、[`typing.Literal`][]の使用をサポートしています。

```py
from typing import Literal

from pydantic import BaseModel, ValidationError


class Pie(BaseModel):
    flavor: Literal['apple', 'pumpkin']


Pie(flavor='apple')
Pie(flavor='pumpkin')
try:
    Pie(flavor='cherry')
except ValidationError as e:
    print(str(e))
    """
    1 validation error for Pie
    flavor
      Input should be 'apple' or 'pumpkin' [type=literal_error, input_value='cherry', input_type=str]
    """
```

<!-- One benefit of this field type is that it can be used to check for equality with one or more specific values without needing to declare custom validators: -->
このフィールド型の利点の1つは、カスタムバリデータを宣言しなくても、1つ以上の特定の値との等価性をチェックできることです。

```py requires="3.8"
from typing import ClassVar, List, Literal, Union

from pydantic import BaseModel, ValidationError


class Cake(BaseModel):
    kind: Literal['cake']
    required_utensils: ClassVar[List[str]] = ['fork', 'knife']


class IceCream(BaseModel):
    kind: Literal['icecream']
    required_utensils: ClassVar[List[str]] = ['spoon']


class Meal(BaseModel):
    dessert: Union[Cake, IceCream]


print(type(Meal(dessert={'kind': 'cake'}).dessert).__name__)
#> Cake
print(type(Meal(dessert={'kind': 'icecream'}).dessert).__name__)
#> IceCream
try:
    Meal(dessert={'kind': 'pie'})
except ValidationError as e:
    print(str(e))
    """
    2 validation errors for Meal
    dessert.Cake.kind
      Input should be 'cake' [type=literal_error, input_value='pie', input_type=str]
    dessert.IceCream.kind
      Input should be 'icecream' [type=literal_error, input_value='pie', input_type=str]
    """
```

<!-- With proper ordering in an annotated `Union`, you can use this to parse types of decreasing specificity: -->
注釈付きの`Union`で適切な順序付けを行うと、これを使用して減少する特異性の型を解析できます。

```py requires="3.8"
from typing import Literal, Optional, Union

from pydantic import BaseModel


class Dessert(BaseModel):
    kind: str


class Pie(Dessert):
    kind: Literal['pie']
    flavor: Optional[str]


class ApplePie(Pie):
    flavor: Literal['apple']


class PumpkinPie(Pie):
    flavor: Literal['pumpkin']


class Meal(BaseModel):
    dessert: Union[ApplePie, PumpkinPie, Pie, Dessert]


print(type(Meal(dessert={'kind': 'pie', 'flavor': 'apple'}).dessert).__name__)
#> ApplePie
print(type(Meal(dessert={'kind': 'pie', 'flavor': 'pumpkin'}).dessert).__name__)
#> PumpkinPie
print(type(Meal(dessert={'kind': 'pie'}).dessert).__name__)
#> Dessert
print(type(Meal(dessert={'kind': 'cake'}).dessert).__name__)
#> Dessert
```

## [`typing.Any`][]

Allows any value, including `None`.


## [`typing.Annotated`][]

<!-- Allows wrapping another type with arbitrary metadata, as per [PEP-593](https://www.python.org/dev/peps/pep-0593/). The `Annotated` hint may contain a single call to the [`Field` function](../concepts/types.md#composing-types-via-annotated), but otherwise the additional metadata is ignored and the root type is used. -->
[PEP-593](https://www.python.org/dev/peps/pep-0593/)に従って、別の型を任意のメタデータでラップすることを許可します。`Annotated`ヒントには、[`Field`関数](../concepts/types.md#composing-types-via-annotated)への単一の呼び出しを含めることができますが、それ以外の場合は追加のメタデータは無視され、ルート型が使用されます。


## [`typing.Pattern`][]

<!-- Will cause the input value to be passed to `re.compile(v)` to create a regular expression pattern. -->
正規表現パターンを作成するために、入力値が`re.compile(v)`に渡されます。

## [`pathlib.Path`][]

<!-- Simply uses the type itself for validation by passing the value to `Path(v)`. -->
値を`Path(v)`に渡すことで、型自体を検証に使用します。
