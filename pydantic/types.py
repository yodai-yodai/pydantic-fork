"""タイプモジュールには、pydanticで使用されるカスタムタイプが含まれています。"""

from __future__ import annotations as _annotations

import base64
import dataclasses as _dataclasses
import re
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    FrozenSet,
    Generic,
    Hashable,
    Iterator,
    List,
    Pattern,
    Set,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)
from uuid import UUID

import annotated_types
from annotated_types import BaseMetadata, MaxLen, MinLen
from pydantic_core import CoreSchema, PydanticCustomError, core_schema
from typing_extensions import Annotated, Literal, Protocol, TypeAlias, TypeAliasType, deprecated

from ._internal import _core_utils, _fields, _internal_dataclass, _typing_extra, _utils, _validators
from ._migration import getattr_migration
from .annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler
from .errors import PydanticUserError
from .json_schema import JsonSchemaValue
from .warnings import PydanticDeprecatedSince20

__all__ = (
    'Strict',
    'StrictStr',
    'conbytes',
    'conlist',
    'conset',
    'confrozenset',
    'constr',
    'ImportString',
    'conint',
    'PositiveInt',
    'NegativeInt',
    'NonNegativeInt',
    'NonPositiveInt',
    'confloat',
    'PositiveFloat',
    'NegativeFloat',
    'NonNegativeFloat',
    'NonPositiveFloat',
    'FiniteFloat',
    'condecimal',
    'UUID1',
    'UUID3',
    'UUID4',
    'UUID5',
    'FilePath',
    'DirectoryPath',
    'NewPath',
    'Json',
    'Secret',
    'SecretStr',
    'SecretBytes',
    'StrictBool',
    'StrictBytes',
    'StrictInt',
    'StrictFloat',
    'PaymentCardNumber',
    'ByteSize',
    'PastDate',
    'FutureDate',
    'PastDatetime',
    'FutureDatetime',
    'condate',
    'AwareDatetime',
    'NaiveDatetime',
    'AllowInfNan',
    'EncoderProtocol',
    'EncodedBytes',
    'EncodedStr',
    'Base64Encoder',
    'Base64Bytes',
    'Base64Str',
    'Base64UrlBytes',
    'Base64UrlStr',
    'GetPydanticSchema',
    'StringConstraints',
    'Tag',
    'Discriminator',
    'JsonValue',
    'OnErrorOmit',
    'FailFast',
)


T = TypeVar('T')


@_dataclasses.dataclass
class Strict(_fields.PydanticMetadata, BaseMetadata):
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/strict_mode/#strict-mode-with-annotated-strict

    フィールドがstrictモードで検証される必要があることを示すフィールドメタデータクラス。

    Attributes:
        strict: strictモードでフィールドを検証するかどうか。

    例:
        ```python
        from typing_extensions import Annotated

        from pydantic.types import Strict

        StrictBool = Annotated[bool, Strict()]
        ```
    """

    strict: bool = True

    def __hash__(self) -> int:
        return hash(self.strict)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BOOLEAN TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

StrictBool = Annotated[bool, Strict()]
"""ブール値で、"True"または"False"のいずれかでなければなりません。"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INTEGER TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def conint(
    *,
    strict: bool | None = None,
    gt: int | None = None,
    ge: int | None = None,
    lt: int | None = None,
    le: int | None = None,
    multiple_of: int | None = None,
) -> type[int]:
    """
    !!! warning "Discouraged"
        この関数は推奨されません。代わりに[`Field`][pydantic.fields.Field]と共に[`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated)を使用してください。

        この関数はPydantic 3.0で**非推奨**になります。

        その理由は、`conint`が型を返すため、静的解析ツールではうまく動作しないからです。

        === ":x: Don't do this"
            ```py
            from pydantic import BaseModel, conint

            class Foo(BaseModel):
                bar: conint(strict=True, gt=0)
            ```

        === ":white_check_mark: Do this"
            ```py
            from typing_extensions import Annotated

            from pydantic import BaseModel, Field

            class Foo(BaseModel):
                bar: Annotated[int, Field(strict=True, gt=0)]
            ```

        追加の制約を可能にする`int`のラッパ。

    Args:
        strict: strictモードで整数を検証するかどうか。デフォルトは`None`です。
        gt: この値より大きい必要があります。
        ge: この値以上にする必要があります。
        lt: この値より小さくなければなりません。
        le: この値以下でなければなりません。
        multiple_of: 値はこのの倍数でなければなりません。

    Returns:
        ラップされた整数型です。

    ```py
    from pydantic import BaseModel, ValidationError, conint

    class ConstrainedExample(BaseModel):
        constrained_int: conint(gt=1)

    m = ConstrainedExample(constrained_int=2)
    print(repr(m))
    #> ConstrainedExample(constrained_int=2)

    try:
        ConstrainedExample(constrained_int=0)
    except ValidationError as e:
        print(e.errors())
        '''
        [
            {
                'type': 'greater_than',
                'loc': ('constrained_int',),
                'msg': 'Input should be greater than 1',
                'input': 0,
                'ctx': {'gt': 1},
                'url': 'https://errors.pydantic.dev/2/v/greater_than',
            }
        ]
        '''
    ```

    """  # noqa: D212
    return Annotated[  # pyright: ignore[reportReturnType]
        int,
        Strict(strict) if strict is not None else None,
        annotated_types.Interval(gt=gt, ge=ge, lt=lt, le=le),
        annotated_types.MultipleOf(multiple_of) if multiple_of is not None else None,
    ]


PositiveInt = Annotated[int, annotated_types.Gt(0)]
"""0より大きくなければならない整数。

```py
from pydantic import BaseModel, PositiveInt, ValidationError

class Model(BaseModel):
    positive_int: PositiveInt

m = Model(positive_int=1)
print(repr(m))
#> Model(positive_int=1)

try:
    Model(positive_int=-1)
except ValidationError as e:
    print(e.errors())
    '''
    [
        {
            'type': 'greater_than',
            'loc': ('positive_int',),
            'msg': 'Input should be greater than 0',
            'input': -1,
            'ctx': {'gt': 0},
            'url': 'https://errors.pydantic.dev/2/v/greater_than',
        }
    ]
    '''
```
"""
NegativeInt = Annotated[int, annotated_types.Lt(0)]
"""ゼロより小さくなければならない整数。

```py
from pydantic import BaseModel, NegativeInt, ValidationError

class Model(BaseModel):
    negative_int: NegativeInt

m = Model(negative_int=-1)
print(repr(m))
#> Model(negative_int=-1)

try:
    Model(negative_int=1)
except ValidationError as e:
    print(e.errors())
    '''
    [
        {
            'type': 'less_than',
            'loc': ('negative_int',),
            'msg': 'Input should be less than 0',
            'input': 1,
            'ctx': {'lt': 0},
            'url': 'https://errors.pydantic.dev/2/v/less_than',
        }
    ]
    '''
```
"""
NonPositiveInt = Annotated[int, annotated_types.Le(0)]
"""0以下の整数。

```py
from pydantic import BaseModel, NonPositiveInt, ValidationError

class Model(BaseModel):
    non_positive_int: NonPositiveInt

m = Model(non_positive_int=0)
print(repr(m))
#> Model(non_positive_int=0)

try:
    Model(non_positive_int=1)
except ValidationError as e:
    print(e.errors())
    '''
    [
        {
            'type': 'less_than_equal',
            'loc': ('non_positive_int',),
            'msg': 'Input should be less than or equal to 0',
            'input': 1,
            'ctx': {'le': 0},
            'url': 'https://errors.pydantic.dev/2/v/less_than_equal',
        }
    ]
    '''
```
"""
NonNegativeInt = Annotated[int, annotated_types.Ge(0)]
"""0以上の整数。

```py
from pydantic import BaseModel, NonNegativeInt, ValidationError

class Model(BaseModel):
    non_negative_int: NonNegativeInt

m = Model(non_negative_int=0)
print(repr(m))
#> Model(non_negative_int=0)

try:
    Model(non_negative_int=-1)
except ValidationError as e:
    print(e.errors())
    '''
    [
        {
            'type': 'greater_than_equal',
            'loc': ('non_negative_int',),
            'msg': 'Input should be greater than or equal to 0',
            'input': -1,
            'ctx': {'ge': 0},
            'url': 'https://errors.pydantic.dev/2/v/greater_than_equal',
        }
    ]
    '''
```
"""
StrictInt = Annotated[int, Strict()]
"""strictモードで検証する必要がある整数。

```py
from pydantic import BaseModel, StrictInt, ValidationError

class StrictIntModel(BaseModel):
    strict_int: StrictInt

try:
    StrictIntModel(strict_int=3.14159)
except ValidationError as e:
    print(e)
    '''
    1 validation error for StrictIntModel
    strict_int
      Input should be a valid integer [type=int_type, input_value=3.14159, input_type=float]
    '''
```
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FLOAT TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@_dataclasses.dataclass
class AllowInfNan(_fields.PydanticMetadata):
    """フィールドが"-inf"、"inf"、"nan"を許可すべきであることを示すフィールドメタデータクラス。"""

    allow_inf_nan: bool = True

    def __hash__(self) -> int:
        return hash(self.allow_inf_nan)


def confloat(
    *,
    strict: bool | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
) -> type[float]:
    """
    !!! warning "Discouraged"
        この関数は推奨されません。代わりに[`Field`][pydantic.fields.Field]と共に[`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated)を使用してください。

        この関数はPydantic 3.0で**非推奨**になります。

        その理由は、`confloat`が型を返すため、静的解析ツールではうまく動作しないからです。

        === ":x: Don't do this"
            ```py
            from pydantic import BaseModel, confloat

            class Foo(BaseModel):
                bar: confloat(strict=True, gt=0)
            ```

        === ":white_check_mark: Do this"
            ```py
            from typing_extensions import Annotated

            from pydantic import BaseModel, Field

            class Foo(BaseModel):
                bar: Annotated[float, Field(strict=True, gt=0)]
            ```

    追加の制約を可能にする`float`のラッパです。

    Args:
        strict: 浮動小数点をstrictモードで検証するかどうか。
        gt: この値より大きい必要があります。
        ge: この値以上にする必要があります。
        lt: この値より小さくなければなりません。
        le: この値以下でなければなりません。
        multiple_of: 値はこのの倍数でなければなりません。
        allow_inf_nan: `-inf`、`inf`、`nan`を許可するかどうか。

    Returns:
        ラップされたfloat型。

    ```py
    from pydantic import BaseModel, ValidationError, confloat

    class ConstrainedExample(BaseModel):
        constrained_float: confloat(gt=1.0)

    m = ConstrainedExample(constrained_float=1.1)
    print(repr(m))
    #> ConstrainedExample(constrained_float=1.1)

    try:
        ConstrainedExample(constrained_float=0.9)
    except ValidationError as e:
        print(e.errors())
        '''
        [
            {
                'type': 'greater_than',
                'loc': ('constrained_float',),
                'msg': 'Input should be greater than 1',
                'input': 0.9,
                'ctx': {'gt': 1.0},
                'url': 'https://errors.pydantic.dev/2/v/greater_than',
            }
        ]
        '''
    ```
    """  # noqa: D212
    return Annotated[  # pyright: ignore[reportReturnType]
        float,
        Strict(strict) if strict is not None else None,
        annotated_types.Interval(gt=gt, ge=ge, lt=lt, le=le),
        annotated_types.MultipleOf(multiple_of) if multiple_of is not None else None,
        AllowInfNan(allow_inf_nan) if allow_inf_nan is not None else None,
    ]


PositiveFloat = Annotated[float, annotated_types.Gt(0)]
"""0より大きくなければならない浮動小数点。

```py
from pydantic import BaseModel, PositiveFloat, ValidationError

class Model(BaseModel):
    positive_float: PositiveFloat

m = Model(positive_float=1.0)
print(repr(m))
#> Model(positive_float=1.0)

try:
    Model(positive_float=-1.0)
except ValidationError as e:
    print(e.errors())
    '''
    [
        {
            'type': 'greater_than',
            'loc': ('positive_float',),
            'msg': 'Input should be greater than 0',
            'input': -1.0,
            'ctx': {'gt': 0.0},
            'url': 'https://errors.pydantic.dev/2/v/greater_than',
        }
    ]
    '''
```
"""
NegativeFloat = Annotated[float, annotated_types.Lt(0)]
"""0より小さくなければならない浮動小数点。

```py
from pydantic import BaseModel, NegativeFloat, ValidationError

class Model(BaseModel):
    negative_float: NegativeFloat

m = Model(negative_float=-1.0)
print(repr(m))
#> Model(negative_float=-1.0)

try:
    Model(negative_float=1.0)
except ValidationError as e:
    print(e.errors())
    '''
    [
        {
            'type': 'less_than',
            'loc': ('negative_float',),
            'msg': 'Input should be less than 0',
            'input': 1.0,
            'ctx': {'lt': 0.0},
            'url': 'https://errors.pydantic.dev/2/v/less_than',
        }
    ]
    '''
```
"""
NonPositiveFloat = Annotated[float, annotated_types.Le(0)]
"""0以下でなければならない浮動小数点。

```py
from pydantic import BaseModel, NonPositiveFloat, ValidationError

class Model(BaseModel):
    non_positive_float: NonPositiveFloat

m = Model(non_positive_float=0.0)
print(repr(m))
#> Model(non_positive_float=0.0)

try:
    Model(non_positive_float=1.0)
except ValidationError as e:
    print(e.errors())
    '''
    [
        {
            'type': 'less_than_equal',
            'loc': ('non_positive_float',),
            'msg': 'Input should be less than or equal to 0',
            'input': 1.0,
            'ctx': {'le': 0.0},
            'url': 'https://errors.pydantic.dev/2/v/less_than_equal',
        }
    ]
    '''
```
"""
NonNegativeFloat = Annotated[float, annotated_types.Ge(0)]
"""0以上でなければならない浮動小数点。

```py
from pydantic import BaseModel, NonNegativeFloat, ValidationError

class Model(BaseModel):
    non_negative_float: NonNegativeFloat

m = Model(non_negative_float=0.0)
print(repr(m))
#> Model(non_negative_float=0.0)

try:
    Model(non_negative_float=-1.0)
except ValidationError as e:
    print(e.errors())
    '''
    [
        {
            'type': 'greater_than_equal',
            'loc': ('non_negative_float',),
            'msg': 'Input should be greater than or equal to 0',
            'input': -1.0,
            'ctx': {'ge': 0.0},
            'url': 'https://errors.pydantic.dev/2/v/greater_than_equal',
        }
    ]
    '''
```
"""
StrictFloat = Annotated[float, Strict(True)]
"""strictモードで検証する必要があるfloat。

```py
from pydantic import BaseModel, StrictFloat, ValidationError

class StrictFloatModel(BaseModel):
    strict_float: StrictFloat

try:
    StrictFloatModel(strict_float='1.0')
except ValidationError as e:
    print(e)
    '''
    1 validation error for StrictFloatModel
    strict_float
      Input should be a valid number [type=float_type, input_value='1.0', input_type=str]
    '''
```
"""
FiniteFloat = Annotated[float, AllowInfNan(False)]
"""finiteでなければならないfloat("-inf"、"inf"、"nan"ではない)。

```py
from pydantic import BaseModel, FiniteFloat

class Model(BaseModel):
    finite: FiniteFloat

m = Model(finite=1.0)
print(m)
#> finite=1.0
```
"""


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BYTES TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def conbytes(
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
) -> type[bytes]:
    """追加の制約を可能にする`bytes`のラッパ。

    Args:
        min_length: バイトの最小長。
        max_length: バイトの最大長。
        strict: strictモードでバイトを検証するかどうか。

    Returns:
        ラップされたバイトのタイプ。
    """
    return Annotated[  # pyright: ignore[reportReturnType]
        bytes,
        Strict(strict) if strict is not None else None,
        annotated_types.Len(min_length or 0, max_length),
    ]


StrictBytes = Annotated[bytes, Strict()]
"""strictモードで検証する必要があるバイト"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ STRING TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@_dataclasses.dataclass(frozen=True)
class StringConstraints(annotated_types.GroupedMetadata):
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/fields/#string-constraints

    `str`型に制約を適用します。

    Attributes:
        strip_whitespace: 先頭と末尾の空白を削除するかどうか。
        to_upper: 文字列を大文字に変換するかどうか。
        to_lower: 文字列を小文字に変換するかどうか。
        strict: 文字列をstrictモードで検証するかどうか。
        min_length: 文字列の最小長。
        max_length: 文字列の最大長。
        pattern: 文字列が一致しなければならない正規表現パターン。
    """

    strip_whitespace: bool | None = None
    to_upper: bool | None = None
    to_lower: bool | None = None
    strict: bool | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | Pattern[str] | None = None

    def __iter__(self) -> Iterator[BaseMetadata]:
        if self.min_length is not None:
            yield MinLen(self.min_length)
        if self.max_length is not None:
            yield MaxLen(self.max_length)
        if self.strict is not None:
            yield Strict(self.strict)
        if (
            self.strip_whitespace is not None
            or self.pattern is not None
            or self.to_lower is not None
            or self.to_upper is not None
        ):
            yield _fields.pydantic_general_metadata(
                strip_whitespace=self.strip_whitespace,
                to_upper=self.to_upper,
                to_lower=self.to_lower,
                pattern=self.pattern,
            )


def constr(
    *,
    strip_whitespace: bool | None = None,
    to_upper: bool | None = None,
    to_lower: bool | None = None,
    strict: bool | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | Pattern[str] | None = None,
) -> type[str]:
    """
    !!! warning "Discouraged"
        この関数は推奨されません。代わりに[`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated)と[`StringConstraints`][pydantic.types.StringConstraints]を使用してください。

        この関数はPydantic 3.0で**非推奨**になります。

        その理由は、`constr`が型を返すため、静的解析ツールではうまく動作しないからです。

        === ":x: Don't do this"
            ```py
            from pydantic import BaseModel, constr

            class Foo(BaseModel):
                bar: constr(strip_whitespace=True, to_upper=True, pattern=r'^[A-Z]+$')
            ```

        === ":white_check_mark: Do this"
            ```py
            from typing_extensions import Annotated

            from pydantic import BaseModel, StringConstraints

            class Foo(BaseModel):
                bar: Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, pattern=r'^[A-Z]+$')]
            ```

    追加の制約を可能にする`str`のラッパ。

    ```py
    from pydantic import BaseModel, constr

    class Foo(BaseModel):
        bar: constr(strip_whitespace=True, to_upper=True, pattern=r'^[A-Z]+$')


    foo = Foo(bar='  hello  ')
    print(foo)
    #> bar='HELLO'
    ```

    Args:
        strip_whitespace: 先頭と末尾の空白を削除するかどうか。
        to_upper: すべての文字を大文字にするかどうか。
        to_lower: すべての文字を小文字にするかどうか。
        strict: 文字列をstrictモードで検証するかどうか。
        min_length: 文字列の最小長。
        max_length: 文字列の最大長。
        pattern: 文字列を検証するための正規表現パターン。

    Returns:
        ラップされた文字列型。
    """  # noqa: D212
    return Annotated[  # pyright: ignore[reportReturnType]
        str,
        StringConstraints(
            strip_whitespace=strip_whitespace,
            to_upper=to_upper,
            to_lower=to_lower,
            strict=strict,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
        ),
    ]


StrictStr = Annotated[str, Strict()]
"""strictモードで検証する必要がある文字列"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~ COLLECTION TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
HashableItemType = TypeVar('HashableItemType', bound=Hashable)


def conset(
    item_type: type[HashableItemType], *, min_length: int | None = None, max_length: int | None = None
) -> type[set[HashableItemType]]:
    """追加の制約を可能にする`typing.Set`のラッパ。

    Args:
        item_type: セット内の項目のタイプ。
        min_length: セットの最小長。
        max_length: セットの最大長。

    Returns:
        ラップされたセットのタイプ。
    """
    return Annotated[Set[item_type], annotated_types.Len(min_length or 0, max_length)]  # pyright: ignore[reportReturnType]


def confrozenset(
    item_type: type[HashableItemType], *, min_length: int | None = None, max_length: int | None = None
) -> type[frozenset[HashableItemType]]:
    """追加の制約を可能にする`typing.FrozenSet`のラッパ。

    Args:
        item_type: FrozenSet内の項目のタイプ。
        min_length: FrozenSetの最小長。
        max_length: FrozenSetの最大長。

    Returns:
        ラップされたfrozenset型。
    """
    return Annotated[FrozenSet[item_type], annotated_types.Len(min_length or 0, max_length)]  # pyright: ignore[reportReturnType]


AnyItemType = TypeVar('AnyItemType')


def conlist(
    item_type: type[AnyItemType],
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    unique_items: bool | None = None,
) -> type[list[AnyItemType]]:
    """検証を追加するtyping.Listのラッパー。

    Args:
        item_type: リスト内の項目のタイプ。
        min_length: リストの最小長。デフォルトは"なし"です。
        max_length: リストの最大長。デフォルトは"なし"です。
        unique_items:リスト内のアイテムが一意である必要があるかどうか。デフォルトは"なし"です。
            !!! warning Deprecated
                `unique_items`パラメータは廃止されました。代わりに`Set`を使用してください。
                詳細については、[this issue](https://github.com/pydantic/pydantic-core/issues/296)を参照してください。

    Returns:
        ラップされたリストのタイプ。
    """
    if unique_items is not None:
        raise PydanticUserError(
            (
                '`unique_items` is removed, use `Set` instead'
                '(this feature is discussed in https://github.com/pydantic/pydantic-core/issues/296)'
            ),
            code='removed-kwargs',
        )
    return Annotated[List[item_type], annotated_types.Len(min_length or 0, max_length)]  # pyright: ignore[reportReturnType]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ IMPORT STRING TYPE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AnyType = TypeVar('AnyType')
if TYPE_CHECKING:
    ImportString = Annotated[AnyType, ...]
else:

    class ImportString:
        """文字列から型をインポートするために使用できる型。

        `ImportString`は文字列を予期し、そのドットパスでインポート可能なPythonオブジェクトをロードします。
        モジュールの属性はモジュールと`:`または`.`で区切ることができます。例えば、`'math:cos'`が与えられた場合、結果のフィールド値は関数`cos`になります。`.`が使用され、属性とサブモジュールの両方が同じパスに存在する場合、モジュールが優先されます。

        モデルのインスタンス化では、ポインタが評価されてインポートされます。この動作には、次の例に示すような微妙な違いがあります。

        **適切な動作:**
        ```py
        from math import cos

        from pydantic import BaseModel, Field, ImportString, ValidationError


        class ImportThings(BaseModel):
            obj: ImportString


        # A string value will cause an automatic import
        my_cos = ImportThings(obj='math.cos')

        # You can use the imported function as you would expect
        cos_of_0 = my_cos.obj(0)
        assert cos_of_0 == 1


        # A string whose value cannot be imported will raise an error
        try:
            ImportThings(obj='foo.bar')
        except ValidationError as e:
            print(e)
            '''
            1 validation error for ImportThings
            obj
            Invalid python path: No module named 'foo.bar' [type=import_error, input_value='foo.bar', input_type=str]
            '''


        # Actual python objects can be assigned as well
        my_cos = ImportThings(obj=cos)
        my_cos_2 = ImportThings(obj='math.cos')
        my_cos_3 = ImportThings(obj='math:cos')
        assert my_cos == my_cos_2 == my_cos_3


        # You can set default field value either as Python object:
        class ImportThingsDefaultPyObj(BaseModel):
            obj: ImportString = math.cos


        # or as a string value (but only if used with `validate_default=True`)
        class ImportThingsDefaultString(BaseModel):
            obj: ImportString = Field(default='math.cos', validate_default=True)


        my_cos_default1 = ImportThingsDefaultPyObj()
        my_cos_default2 = ImportThingsDefaultString()
        assert my_cos_default1.obj == my_cos_default2.obj == math.cos


        # note: this will not work!
        class ImportThingsMissingValidateDefault(BaseModel):
            obj: ImportString = 'math.cos'

        my_cos_default3 = ImportThingsMissingValidateDefault()
        assert my_cos_default3.obj == 'math.cos'  # just string, not evaluated
        ```

        `ImportString`型をjsonにシリアライズすることも可能です。

        ```py
        from pydantic import BaseModel, ImportString


        class ImportThings(BaseModel):
            obj: ImportString


        # Create an instance
        m = ImportThings(obj='math.cos')
        print(m)
        #> obj=<built-in function cos>
        print(m.model_dump_json())
        #> {"obj":"math.cos"}
        ```
        """

        @classmethod
        def __class_getitem__(cls, item: AnyType) -> AnyType:
            return Annotated[item, cls()]

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            serializer = core_schema.plain_serializer_function_ser_schema(cls._serialize, when_used='json')
            if cls is source:
                # Treat bare usage of ImportString (`schema is None`) as the same as ImportString[Any]
                return core_schema.no_info_plain_validator_function(
                    function=_validators.import_string, serialization=serializer
                )
            else:
                return core_schema.no_info_before_validator_function(
                    function=_validators.import_string, schema=handler(source), serialization=serializer
                )

        @classmethod
        def __get_pydantic_json_schema__(cls, cs: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            return handler(core_schema.str_schema())

        @staticmethod
        def _serialize(v: Any) -> str:
            if isinstance(v, ModuleType):
                return v.__name__
            elif hasattr(v, '__module__') and hasattr(v, '__name__'):
                return f'{v.__module__}.{v.__name__}'
            else:
                return v

        def __repr__(self) -> str:
            return 'ImportString'


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DECIMAL TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def condecimal(
    *,
    strict: bool | None = None,
    gt: int | Decimal | None = None,
    ge: int | Decimal | None = None,
    lt: int | Decimal | None = None,
    le: int | Decimal | None = None,
    multiple_of: int | Decimal | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    allow_inf_nan: bool | None = None,
) -> type[Decimal]:
    """
    !!! warning "Discouraged"
        この関数は推奨されません。代わりに[`Field`][pydantic.fields.Field]と共に[`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated)を使用してください。

        この関数はPydantic 3.0で**非推奨**になります。

        その理由は、`condecimal`が型を返すため、静的解析ツールではうまく動作しないからです。

        === ":x: Don't do this"
            ```py
            from pydantic import BaseModel, condecimal

            class Foo(BaseModel):
                bar: condecimal(strict=True, allow_inf_nan=True)
            ```

        === ":white_check_mark: Do this"
            ```py
            from decimal import Decimal

            from typing_extensions import Annotated

            from pydantic import BaseModel, Field

            class Foo(BaseModel):
                bar: Annotated[Decimal, Field(strict=True, allow_inf_nan=True)]
            ```

    検証を追加するDecimalのラッパー。

    Args:
        strict: strictモードで値を検証するかどうか。デフォルトは`None`です。
        gt: この値より大きい必要があります。デフォルトは`None`です。
        ge: この値以上でなければなりません。デフォルトは`None`です。
        lt: 値はこれより小さくなければなりません。デフォルトは`None`です。
        le: この値以下でなければなりません。デフォルトは`None`です。
        multiple_of: 値はthisの倍数でなければなりません。デフォルトは`None`です。
        max_digits: 最大桁数。デフォルトは`None`です。
        decimal_places: 小数点以下の桁数。デフォルトは`None`です。
        allow_inf_nan: 無限大とNaNを許可するかどうか。デフォルトは`None`です。

    ```py
    from decimal import Decimal

    from pydantic import BaseModel, ValidationError, condecimal

    class ConstrainedExample(BaseModel):
        constrained_decimal: condecimal(gt=Decimal('1.0'))

    m = ConstrainedExample(constrained_decimal=Decimal('1.1'))
    print(repr(m))
    #> ConstrainedExample(constrained_decimal=Decimal('1.1'))

    try:
        ConstrainedExample(constrained_decimal=Decimal('0.9'))
    except ValidationError as e:
        print(e.errors())
        '''
        [
            {
                'type': 'greater_than',
                'loc': ('constrained_decimal',),
                'msg': 'Input should be greater than 1.0',
                'input': Decimal('0.9'),
                'ctx': {'gt': Decimal('1.0')},
                'url': 'https://errors.pydantic.dev/2/v/greater_than',
            }
        ]
        '''
    ```
    """  # noqa: D212
    return Annotated[  # pyright: ignore[reportReturnType]
        Decimal,
        Strict(strict) if strict is not None else None,
        annotated_types.Interval(gt=gt, ge=ge, lt=lt, le=le),
        annotated_types.MultipleOf(multiple_of) if multiple_of is not None else None,
        _fields.pydantic_general_metadata(max_digits=max_digits, decimal_places=decimal_places),
        AllowInfNan(allow_inf_nan) if allow_inf_nan is not None else None,
    ]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ UUID TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@_dataclasses.dataclass(**_internal_dataclass.slots_true)
class UuidVersion:
    """[UUID](https://docs.python.org/3/library/uuid.html)バージョンを示すフィールドメタデータクラス。"""

    uuid_version: Literal[1, 3, 4, 5]

    def __get_pydantic_json_schema__(
        self, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = handler(core_schema)
        field_schema.pop('anyOf', None)  # remove the bytes/str union
        field_schema.update(type='string', format=f'uuid{self.uuid_version}')
        return field_schema

    def __get_pydantic_core_schema__(self, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        if isinstance(self, source):
            # used directly as a type
            return core_schema.uuid_schema(version=self.uuid_version)
        else:
            # update existing schema with self.uuid_version
            schema = handler(source)
            _check_annotated_type(schema['type'], 'uuid', self.__class__.__name__)
            schema['version'] = self.uuid_version  # type: ignore
            return schema

    def __hash__(self) -> int:
        return hash(type(self.uuid_version))


UUID1 = Annotated[UUID, UuidVersion(1)]
"""バージョン1である必要がある[UUID](https://docs.python.org/3/library/uuid.html)。

```py
import uuid

from pydantic import UUID1, BaseModel

class Model(BaseModel):
    uuid1: UUID1

Model(uuid1=uuid.uuid1())
```
"""
UUID3 = Annotated[UUID, UuidVersion(3)]
"""バージョン3である必要がある[UUID](https://docs.python.org/3/library/uuid.html)。

```py
import uuid

from pydantic import UUID3, BaseModel

class Model(BaseModel):
    uuid3: UUID3

Model(uuid3=uuid.uuid3(uuid.NAMESPACE_DNS, 'pydantic.org'))
```
"""
UUID4 = Annotated[UUID, UuidVersion(4)]
"""バージョン4である必要がある[UUID](https://docs.python.org/3/library/uuid.html)。

```py
import uuid

from pydantic import UUID4, BaseModel

class Model(BaseModel):
    uuid4: UUID4

Model(uuid4=uuid.uuid4())
```
"""
UUID5 = Annotated[UUID, UuidVersion(5)]
"""バージョン5である必要がある[UUID](https://docs.python.org/3/library/uuid.html)。

```py
import uuid

from pydantic import UUID5, BaseModel

class Model(BaseModel):
    uuid5: UUID5

Model(uuid5=uuid.uuid5(uuid.NAMESPACE_DNS, 'pydantic.org'))
```
"""


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PATH TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@_dataclasses.dataclass
class PathType:
    path_type: Literal['file', 'dir', 'new']

    def __get_pydantic_json_schema__(
        self, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = handler(core_schema)
        format_conversion = {'file': 'file-path', 'dir': 'directory-path'}
        field_schema.update(format=format_conversion.get(self.path_type, 'path'), type='string')
        return field_schema

    def __get_pydantic_core_schema__(self, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        function_lookup = {
            'file': cast(core_schema.WithInfoValidatorFunction, self.validate_file),
            'dir': cast(core_schema.WithInfoValidatorFunction, self.validate_directory),
            'new': cast(core_schema.WithInfoValidatorFunction, self.validate_new),
        }

        return core_schema.with_info_after_validator_function(
            function_lookup[self.path_type],
            handler(source),
        )

    @staticmethod
    def validate_file(path: Path, _: core_schema.ValidationInfo) -> Path:
        if path.is_file():
            return path
        else:
            raise PydanticCustomError('path_not_file', 'Path does not point to a file')

    @staticmethod
    def validate_directory(path: Path, _: core_schema.ValidationInfo) -> Path:
        if path.is_dir():
            return path
        else:
            raise PydanticCustomError('path_not_directory', 'Path does not point to a directory')

    @staticmethod
    def validate_new(path: Path, _: core_schema.ValidationInfo) -> Path:
        if path.exists():
            raise PydanticCustomError('path_exists', 'Path already exists')
        elif not path.parent.exists():
            raise PydanticCustomError('parent_does_not_exist', 'Parent directory does not exist')
        else:
            return path

    def __hash__(self) -> int:
        return hash(type(self.path_type))


FilePath = Annotated[Path, PathType('file')]
"""ファイルへの参照が必要なパス。

```py
from pathlib import Path

from pydantic import BaseModel, FilePath, ValidationError

class Model(BaseModel):
    f: FilePath

path = Path('text.txt')
path.touch()
m = Model(f='text.txt')
print(m.model_dump())
#> {'f': PosixPath('text.txt')}
path.unlink()

path = Path('directory')
path.mkdir(exist_ok=True)
try:
    Model(f='directory')  # directory
except ValidationError as e:
    print(e)
    '''
    1 validation error for Model
    f
      Path does not point to a file [type=path_not_file, input_value='directory', input_type=str]
    '''
path.rmdir()

try:
    Model(f='not-exists-file')
except ValidationError as e:
    print(e)
    '''
    1 validation error for Model
    f
      Path does not point to a file [type=path_not_file, input_value='not-exists-file', input_type=str]
    '''
```
"""
DirectoryPath = Annotated[Path, PathType('dir')]
"""ディレクトリへの参照が必要なパス。

```py
from pathlib import Path

from pydantic import BaseModel, DirectoryPath, ValidationError

class Model(BaseModel):
    f: DirectoryPath

path = Path('directory/')
path.mkdir()
m = Model(f='directory/')
print(m.model_dump())
#> {'f': PosixPath('directory')}
path.rmdir()

path = Path('file.txt')
path.touch()
try:
    Model(f='file.txt')  # file
except ValidationError as e:
    print(e)
    '''
    1 validation error for Model
    f
      Path does not point to a directory [type=path_not_directory, input_value='file.txt', input_type=str]
    '''
path.unlink()

try:
    Model(f='not-exists-directory')
except ValidationError as e:
    print(e)
    '''
    1 validation error for Model
    f
      Path does not point to a directory [type=path_not_directory, input_value='not-exists-directory', input_type=str]
    '''
```
"""
NewPath = Annotated[Path, PathType('new')]
"""まだ存在していない新しいファイルまたはディレクトリのパス。親ディレクトリはすでに存在している必要があります。"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ JSON TYPE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if TYPE_CHECKING:
    # Json[list[str]] will be recognized by type checkers as list[str]
    Json = Annotated[AnyType, ...]

else:

    class Json:
        """解析前にJSONをロードする特殊な型ラッパー。

        `Json`データ型を使用すると、ロードされたデータをパラメータ化された型に検証する前に、Pydanticに生のJSON文字列を最初にロードさせることができます。

        ```py
        from typing import Any, List

        from pydantic import BaseModel, Json, ValidationError


        class AnyJsonModel(BaseModel):
            json_obj: Json[Any]


        class ConstrainedJsonModel(BaseModel):
            json_obj: Json[List[int]]


        print(AnyJsonModel(json_obj='{"b": 1}'))
        #> json_obj={'b': 1}
        print(ConstrainedJsonModel(json_obj='[1, 2, 3]'))
        #> json_obj=[1, 2, 3]

        try:
            ConstrainedJsonModel(json_obj=12)
        except ValidationError as e:
            print(e)
            '''
            1 validation error for ConstrainedJsonModel
            json_obj
            JSON input should be string, bytes or bytearray [type=json_type, input_value=12, input_type=int]
            '''

        try:
            ConstrainedJsonModel(json_obj='[a, b]')
        except ValidationError as e:
            print(e)
            '''
            1 validation error for ConstrainedJsonModel
            json_obj
            Invalid JSON: expected value at line 1 column 2 [type=json_invalid, input_value='[a, b]', input_type=str]
            '''

        try:
            ConstrainedJsonModel(json_obj='["a", "b"]')
        except ValidationError as e:
            print(e)
            '''
            2 validation errors for ConstrainedJsonModel
            json_obj.0
            Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
            json_obj.1
            Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='b', input_type=str]
            '''
        ```

        `model_dump`または`model_dump_json`を使用してモデルをダンプすると、ダンプされた値は元のJSON文字列ではなく検証の結果になります。ただし、引数`round_trip=True`を使用して元のJSON文字列を取得することもできます。

        ```py
        from typing import List

        from pydantic import BaseModel, Json


        class ConstrainedJsonModel(BaseModel):
            json_obj: Json[List[int]]


        print(ConstrainedJsonModel(json_obj='[1, 2, 3]').model_dump_json())
        #> {"json_obj":[1,2,3]}
        print(
            ConstrainedJsonModel(json_obj='[1, 2, 3]').model_dump_json(round_trip=True)
        )
        #> {"json_obj":"[1,2,3]"}
        ```
        """

        @classmethod
        def __class_getitem__(cls, item: AnyType) -> AnyType:
            return Annotated[item, cls()]

        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            if cls is source:
                return core_schema.json_schema(None)
            else:
                return core_schema.json_schema(handler(source))

        def __repr__(self) -> str:
            return 'Json'

        def __hash__(self) -> int:
            return hash(type(self))

        def __eq__(self, other: Any) -> bool:
            return type(other) == type(self)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ SECRET TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SecretType = TypeVar('SecretType')


class _SecretBase(Generic[SecretType]):
    def __init__(self, secret_value: SecretType) -> None:
        self._secret_value: SecretType = secret_value

    def get_secret_value(self) -> SecretType:
        """シークレット値を取得します。

        Returns:
            シークレット値。
        """
        return self._secret_value

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.get_secret_value() == other.get_secret_value()

    def __hash__(self) -> int:
        return hash(self.get_secret_value())

    def __str__(self) -> str:
        return str(self._display())

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._display()!r})'

    def _display(self) -> str | bytes:
        raise NotImplementedError


class Secret(_SecretBase[SecretType]):
    """ロギングやトレースバックで表示したくない機密情報を含むフィールドを定義するために使用される汎用基本クラス。

    `Secret`を型で直接パラメータ化するか、または`Secret`のサブクラスをパラメータ化された型でパラメータ化することができます。サブクラス化の利点は、`repr()`および`str()`メソッドに使用されるカスタム`_display`メソッドを定義できることです。以下の例は、`Secret`を使用して新しいシークレット型を作成する両方の方法を示しています。

    1. `Secret`型を直接パラメータ化する:

    ```py
    from pydantic import BaseModel, Secret

    SecretBool = Secret[bool]

    class Model(BaseModel):
        secret_bool: SecretBool

    m = Model(secret_bool=True)
    print(m.model_dump())
    #> {'secret_bool': Secret('**********')}

    print(m.model_dump_json())
    #> {"secret_bool":"**********"}

    print(m.secret_bool.get_secret_value())
    #> True
    ```

    2. パラメータ化された`Secret`からのサブクラス化:

    ```py
    from datetime import date

    from pydantic import BaseModel, Secret

    class SecretDate(Secret[date]):
        def _display(self) -> str:
            return '****/**/**'

    class Model(BaseModel):
        secret_date: SecretDate

    m = Model(secret_date=date(2022, 1, 1))
    print(m.model_dump())
    #> {'secret_date': SecretDate('****/**/**')}

    print(m.model_dump_json())
    #> {"secret_date":"****/**/**"}

    print(m.secret_date.get_secret_value())
    #> 2022-01-01
    ```

    `_display`メソッドが返す値は`repr()`と`str()`に使用されます。
    """

    def _display(self) -> str | bytes:
        return '**********' if self.get_secret_value() else ''

    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        inner_type = None
        # if origin_type is Secret, then cls is a GenericAlias, and we can extract the inner type directly
        origin_type = get_origin(source)
        if origin_type is not None:
            inner_type = get_args(source)[0]
        # otherwise, we need to get the inner type from the base class
        else:
            bases = getattr(cls, '__orig_bases__', getattr(cls, '__bases__', []))
            for base in bases:
                if get_origin(base) is Secret:
                    inner_type = get_args(base)[0]
            if bases == [] or inner_type is None:
                raise TypeError(
                    f"Can't get secret type from {cls.__name__}. "
                    'Please use Secret[<type>], or subclass from Secret[<type>] instead.'
                )

        inner_schema = handler.generate_schema(inner_type)  # type: ignore

        def validate_secret_value(value, handler) -> Secret[SecretType]:
            if isinstance(value, Secret):
                value = value.get_secret_value()
            validated_inner = handler(value)
            return cls(validated_inner)

        def serialize(value: Secret[SecretType], info: core_schema.SerializationInfo) -> str | Secret[SecretType]:
            if info.mode == 'json':
                return str(value)
            else:
                return value

        return core_schema.json_or_python_schema(
            python_schema=core_schema.no_info_wrap_validator_function(
                validate_secret_value,
                inner_schema,
            ),
            json_schema=core_schema.no_info_after_validator_function(lambda x: cls(x), inner_schema),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize,
                info_arg=True,
                when_used='always',
            ),
        )


def _secret_display(value: SecretType) -> str:  # type: ignore
    return '**********' if value else ''


class _SecretField(_SecretBase[SecretType]):
    _inner_schema: ClassVar[CoreSchema]
    _error_kind: ClassVar[str]

    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        def serialize(
            value: _SecretField[SecretType], info: core_schema.SerializationInfo
        ) -> str | _SecretField[SecretType]:
            if info.mode == 'json':
                # we want the output to always be string without the `b'` prefix for bytes,
                # hence we just use `secret_display`
                return _secret_display(value.get_secret_value())
            else:
                return value

        def get_json_schema(_core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            json_schema = handler(cls._inner_schema)
            _utils.update_not_none(
                json_schema,
                type='string',
                writeOnly=True,
                format='password',
            )
            return json_schema

        json_schema = core_schema.no_info_after_validator_function(
            source,  # construct the type
            cls._inner_schema,
        )

        def get_secret_schema(strict: bool) -> CoreSchema:
            return core_schema.json_or_python_schema(
                python_schema=core_schema.union_schema(
                    [
                        core_schema.is_instance_schema(source),
                        json_schema,
                    ],
                    custom_error_type=cls._error_kind,
                    strict=strict,
                ),
                json_schema=json_schema,
                serialization=core_schema.plain_serializer_function_ser_schema(
                    serialize,
                    info_arg=True,
                    return_schema=core_schema.str_schema(),
                    when_used='json',
                ),
            )

        return core_schema.lax_or_strict_schema(
            lax_schema=get_secret_schema(strict=False),
            strict_schema=get_secret_schema(strict=True),
            metadata={'pydantic_js_functions': [get_json_schema]},
        )


class SecretStr(_SecretField[str]):
    """ロギングやトレースバックで表示したくない機密情報を格納するために使用される文字列。

    シークレットの値が空でない場合、`repr()`や`str()`の呼び出しでは、元になる値の代わりに`'**********'`として表示されます。
    value_is_emptyの場合は、""と表示されます。

    ```py
    from pydantic import BaseModel, SecretStr

    class User(BaseModel):
        username: str
        password: SecretStr

    user = User(username='scolvin', password='password1')

    print(user)
    #> username='scolvin' password=SecretStr('**********')
    print(user.password.get_secret_value())
    #> password1
    print((SecretStr('password'), SecretStr('')))
    #> (SecretStr('**********'), SecretStr(''))
    ```
    """

    _inner_schema: ClassVar[CoreSchema] = core_schema.str_schema()
    _error_kind: ClassVar[str] = 'string_type'

    def __len__(self) -> int:
        return len(self._secret_value)

    def _display(self) -> str:
        return _secret_display(self._secret_value)


class SecretBytes(_SecretField[bytes]):
    """ログやトレースバックに表示したくない機密情報を保存するために使用されるバイト。

    `repr()`や`str()`を呼び出すと、文字列値の代わりに`b'**********'`が表示されます。
    シークレット値が空でない場合、`repr()`や`str()`の呼び出しでは、元になる値の代わりに`b'**********'`として表示されます。

    ```py
    from pydantic import BaseModel, SecretBytes

    class User(BaseModel):
        username: str
        password: SecretBytes

    user = User(username='scolvin', password=b'password1')
    #> username='scolvin' password=SecretBytes(b'**********')
    print(user.password.get_secret_value())
    #> b'password1'
    print((SecretBytes(b'password'), SecretBytes(b'')))
    #> (SecretBytes(b'**********'), SecretBytes(b''))
    ```
    """

    _inner_schema: ClassVar[CoreSchema] = core_schema.bytes_schema()
    _error_kind: ClassVar[str] = 'bytes_type'

    def __len__(self) -> int:
        return len(self._secret_value)

    def _display(self) -> bytes:
        return _secret_display(self._secret_value).encode()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PAYMENT CARD TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PaymentCardBrand(str, Enum):
    amex = 'American Express'
    mastercard = 'Mastercard'
    visa = 'Visa'
    other = 'other'

    def __str__(self) -> str:
        return self.value


@deprecated(
    'The `PaymentCardNumber` class is deprecated, use `pydantic_extra_types` instead. '
    'See https://docs.pydantic.dev/latest/api/pydantic_extra_types_payment/#pydantic_extra_types.payment.PaymentCardNumber.',
    category=PydanticDeprecatedSince20,
)
class PaymentCardNumber(str):
    """https://en.wikipedia.org/wiki/Payment_card_numberに基づきます。"""

    strip_whitespace: ClassVar[bool] = True
    min_length: ClassVar[int] = 12
    max_length: ClassVar[int] = 19
    bin: str
    last4: str
    brand: PaymentCardBrand

    def __init__(self, card_number: str):
        self.validate_digits(card_number)

        card_number = self.validate_luhn_check_digit(card_number)

        self.bin = card_number[:6]
        self.last4 = card_number[-4:]
        self.brand = self.validate_brand(card_number)

    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.with_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(
                min_length=cls.min_length, max_length=cls.max_length, strip_whitespace=cls.strip_whitespace
            ),
        )

    @classmethod
    def validate(cls, input_value: str, /, _: core_schema.ValidationInfo) -> PaymentCardNumber:
        """カード番号を検証して、`PaymentCardNumber`インスタンスを返します。"""
        return cls(input_value)

    @property
    def masked(self) -> str:
        """カード番号の最後の4桁を除くすべてをマスクします。

        Returns:
            マスクされたカード番号文字列。
        """
        num_masked = len(self) - 10  # len(bin) + len(last4) == 10
        return f'{self.bin}{"*" * num_masked}{self.last4}'

    @classmethod
    def validate_digits(cls, card_number: str) -> None:
        """カード番号がすべて数字であることを確認します。"""

        if not card_number.isdigit():
            raise PydanticCustomError('payment_card_number_digits', 'Card number is not all digits')

    @classmethod
    def validate_luhn_check_digit(cls, card_number: str) -> str:
        """https://en.wikipedia.org/wiki/Luhn_algorithmに基づきます。"""

        sum_ = int(card_number[-1])
        length = len(card_number)
        parity = length % 2
        for i in range(length - 1):
            digit = int(card_number[i])
            if i % 2 == parity:
                digit *= 2
            if digit > 9:
                digit -= 9
            sum_ += digit
        valid = sum_ % 10 == 0
        if not valid:
            raise PydanticCustomError('payment_card_number_luhn', 'Card number is not luhn valid')
        return card_number

    @staticmethod
    def validate_brand(card_number: str) -> PaymentCardBrand:
        """主要ブランドのBINに基づいて長さを検証します:
        https://en.wikipedia.org/wiki/Payment_card_number#Issuer_identification_number_(IIN)
        """
        if card_number[0] == '4':
            brand = PaymentCardBrand.visa
        elif 51 <= int(card_number[:2]) <= 55:
            brand = PaymentCardBrand.mastercard
        elif card_number[:2] in {'34', '37'}:
            brand = PaymentCardBrand.amex
        else:
            brand = PaymentCardBrand.other

        required_length: None | int | str = None
        if brand in PaymentCardBrand.mastercard:
            required_length = 16
            valid = len(card_number) == required_length
        elif brand == PaymentCardBrand.visa:
            required_length = '13, 16 or 19'
            valid = len(card_number) in {13, 16, 19}
        elif brand == PaymentCardBrand.amex:
            required_length = 15
            valid = len(card_number) == required_length
        else:
            valid = True

        if not valid:
            raise PydanticCustomError(
                'payment_card_number_brand',
                'Length for a {brand} card must be {required_length}',
                {'brand': brand, 'required_length': required_length},
            )
        return brand


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BYTE SIZE TYPE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class ByteSize(int):
    """単位付きのバイト数を表す文字列("1 KB"や"11.5 MiB"など)を整数に変換します。

    `ByteSize`データ型を使用すると、バイト数の文字列表現を(大文字小文字を区別せずに)整数に変換したり、バイト数を表す人間が読める文字列を出力したりできます。

    [IEC 80000-13 Standard](https://en.wikipedia.org/wiki/ISO/IEC_80000)に準拠して、"1 KB"は1000バイトを意味し、"1 KiB"は1024バイトを意味すると解釈されます。一般に、中間の"i"を含めると、単位は10の累乗ではなく2の累乗として解釈されます(たとえば、"1 MB"は"1_000_000"バイトとして扱われ、"1 MiB"は"1_048_576"バイトとして扱われます)。

    !!! info
        `1b`は"1 bit"ではなく"1 byte"として解析されることに注意してください。

    ```py
    from pydantic import BaseModel, ByteSize

    class MyModel(BaseModel):
        size: ByteSize

    print(MyModel(size=52000).size)
    #> 52000
    print(MyModel(size='3000 KiB').size)
    #> 3072000

    m = MyModel(size='50 PB')
    print(m.size.human_readable())
    #> 44.4PiB
    print(m.size.human_readable(decimal=True))
    #> 50.0PB
    print(m.size.human_readable(separator=' '))
    #> 44.4 PiB

    print(m.size.to('TiB'))
    #> 45474.73508864641
    ```
    """

    byte_sizes = {
        'b': 1,
        'kb': 10**3,
        'mb': 10**6,
        'gb': 10**9,
        'tb': 10**12,
        'pb': 10**15,
        'eb': 10**18,
        'kib': 2**10,
        'mib': 2**20,
        'gib': 2**30,
        'tib': 2**40,
        'pib': 2**50,
        'eib': 2**60,
        'bit': 1 / 8,
        'kbit': 10**3 / 8,
        'mbit': 10**6 / 8,
        'gbit': 10**9 / 8,
        'tbit': 10**12 / 8,
        'pbit': 10**15 / 8,
        'ebit': 10**18 / 8,
        'kibit': 2**10 / 8,
        'mibit': 2**20 / 8,
        'gibit': 2**30 / 8,
        'tibit': 2**40 / 8,
        'pibit': 2**50 / 8,
        'eibit': 2**60 / 8,
    }
    byte_sizes.update({k.lower()[0]: v for k, v in byte_sizes.items() if 'i' not in k})

    byte_string_pattern = r'^\s*(\d*\.?\d+)\s*(\w+)?'
    byte_string_re = re.compile(byte_string_pattern, re.IGNORECASE)

    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.with_info_after_validator_function(
            function=cls._validate,
            schema=core_schema.union_schema(
                [
                    core_schema.str_schema(pattern=cls.byte_string_pattern),
                    core_schema.int_schema(ge=0),
                ],
                custom_error_type='byte_size',
                custom_error_message='could not parse value and unit from byte string',
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                int, return_schema=core_schema.int_schema(ge=0)
            ),
        )

    @classmethod
    def _validate(cls, input_value: Any, /, _: core_schema.ValidationInfo) -> ByteSize:
        try:
            return cls(int(input_value))
        except ValueError:
            pass

        str_match = cls.byte_string_re.match(str(input_value))
        if str_match is None:
            raise PydanticCustomError('byte_size', 'could not parse value and unit from byte string')

        scalar, unit = str_match.groups()
        if unit is None:
            unit = 'b'

        try:
            unit_mult = cls.byte_sizes[unit.lower()]
        except KeyError:
            raise PydanticCustomError('byte_size_unit', 'could not interpret byte unit: {unit}', {'unit': unit})

        return cls(int(float(scalar) * unit_mult))

    def human_readable(self, decimal: bool = False, separator: str = '') -> str:
        """バイトサイズを人間が読める文字列に変換します。

        Args:
            decimal: Trueの場合、10進単位(例:KBあたり1000バイト)を使用します。Falseの場合、バイナリ単位(例:KiBあたり1024バイト)を使用します。
            separator: 値と単位の分割に使用される文字列。デフォルトは空の文字列('')です。

        Returns:
            人間が判読可能なバイト・サイズの文字列表現。
        """
        if decimal:
            divisor = 1000
            units = 'B', 'KB', 'MB', 'GB', 'TB', 'PB'
            final_unit = 'EB'
        else:
            divisor = 1024
            units = 'B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'
            final_unit = 'EiB'

        num = float(self)
        for unit in units:
            if abs(num) < divisor:
                if unit == 'B':
                    return f'{num:0.0f}{separator}{unit}'
                else:
                    return f'{num:0.1f}{separator}{unit}'
            num /= divisor

        return f'{num:0.1f}{separator}{final_unit}'

    def to(self, unit: str) -> float:
        """バイトサイズを、バイト単位とビット単位の両方を含む別の単位に変換します。

        Args:
            unit: 変換先の単位。次のいずれかである必要があります。
                B, KB, MB, GB, TB, PB, EB,
                KiB, MiB, GiB, TiB, PiB, EiB (byte units)
                bit, kbit, mbit, gbit, tbit, pbit, ebit,
                kibit, mibit, gibit, tibit, pibit, eibit (bit units).

        Returns:
            新しい単位のバイトサイズ。
        """
        try:
            unit_div = self.byte_sizes[unit.lower()]
        except KeyError:
            raise PydanticCustomError('byte_size_unit', 'Could not interpret byte unit: {unit}', {'unit': unit})

        return self / unit_div


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DATE TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def _check_annotated_type(annotated_type: str, expected_type: str, annotation: str) -> None:
    if annotated_type != expected_type:
        raise PydanticUserError(f"'{annotation}' cannot annotate '{annotated_type}'.", code='invalid-annotated-type')


if TYPE_CHECKING:
    PastDate = Annotated[date, ...]
    FutureDate = Annotated[date, ...]
else:

    class PastDate:
        """過去の日付"""

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.date_schema(now_op='past')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'date', cls.__name__)
                schema['now_op'] = 'past'
                return schema

        def __repr__(self) -> str:
            return 'PastDate'

    class FutureDate:
        """未来の日付"""

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.date_schema(now_op='future')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'date', cls.__name__)
                schema['now_op'] = 'future'
                return schema

        def __repr__(self) -> str:
            return 'FutureDate'


def condate(
    *,
    strict: bool | None = None,
    gt: date | None = None,
    ge: date | None = None,
    lt: date | None = None,
    le: date | None = None,
) -> type[date]:
    """制約を追加する日付のラッパ。

    Args:
        strict: 日付値をstrictモードで検証するかどうか。デフォルトは`None`です。
        gt: この値より大きい必要があります。デフォルトは`None`です。
        ge: この値以上でなければなりません。デフォルトは`None`です。
        lt: 値はこれより小さくなければなりません。デフォルトは`None`です。
        le: この値以下でなければなりません。デフォルトは`None`です。

    Returns:
        指定された制約を持つ日付型。
    """
    return Annotated[  # pyright: ignore[reportReturnType]
        date,
        Strict(strict) if strict is not None else None,
        annotated_types.Interval(gt=gt, ge=ge, lt=lt, le=le),
    ]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DATETIME TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if TYPE_CHECKING:
    AwareDatetime = Annotated[datetime, ...]
    NaiveDatetime = Annotated[datetime, ...]
    PastDatetime = Annotated[datetime, ...]
    FutureDatetime = Annotated[datetime, ...]

else:

    class AwareDatetime:
        """タイムゾーン情報を必要とする日時。"""

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.datetime_schema(tz_constraint='aware')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'datetime', cls.__name__)
                schema['tz_constraint'] = 'aware'
                return schema

        def __repr__(self) -> str:
            return 'AwareDatetime'

    class NaiveDatetime:
        """タイムゾーン情報を必要としない日時。"""

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.datetime_schema(tz_constraint='naive')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'datetime', cls.__name__)
                schema['tz_constraint'] = 'naive'
                return schema

        def __repr__(self) -> str:
            return 'NaiveDatetime'

    class PastDatetime:
        """過去の日時。"""

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.datetime_schema(now_op='past')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'datetime', cls.__name__)
                schema['now_op'] = 'past'
                return schema

        def __repr__(self) -> str:
            return 'PastDatetime'

    class FutureDatetime:
        """未来の日時"""

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            if cls is source:
                # used directly as a type
                return core_schema.datetime_schema(now_op='future')
            else:
                schema = handler(source)
                _check_annotated_type(schema['type'], 'datetime', cls.__name__)
                schema['now_op'] = 'future'
                return schema

        def __repr__(self) -> str:
            return 'FutureDatetime'


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Encoded TYPES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class EncoderProtocol(Protocol):
    """バイトとの間でデータをエンコードおよびデコードするためのプロトコル。"""

    @classmethod
    def decode(cls, data: bytes) -> bytes:
        """エンコーダを使用してデータをデコードします。

        Args:
            data: デコードするデータ。

        Returns:
            デコードされたデータ。
        """
        ...

    @classmethod
    def encode(cls, value: bytes) -> bytes:
        """エンコーダを使用してデータをエンコードします。

        Args:
            value: エンコードするデータ。

        Returns:
            エンコードされたデータ。
        """
        ...

    @classmethod
    def get_json_format(cls) -> str:
        """エンコードされたデータのJSONフォーマットを取得します。

        Returns:
            エンコードされたデータのJSONフォーマット。
        """
        ...


class Base64Encoder(EncoderProtocol):
    """標準(URLセーフではない)Base64エンコーダ。"""

    @classmethod
    def decode(cls, data: bytes) -> bytes:
        """base64でエンコードされたバイトから元のバイトデータにデータをデコードします。

        Args:
            data: デコードするデータ。

        Returns:
            デコードされたデータ。
        """
        try:
            return base64.decodebytes(data)
        except ValueError as e:
            raise PydanticCustomError('base64_decode', "Base64 decoding error: '{error}'", {'error': str(e)})

    @classmethod
    def encode(cls, value: bytes) -> bytes:
        """データをバイトからbase64エンコードされたバイトにエンコードします。

        Args:
            value: エンコードするデータ。

        Returns:
            エンコードされたデータ。
        """
        return base64.encodebytes(value)

    @classmethod
    def get_json_format(cls) -> Literal['base64']:
        """エンコードされたデータのJSONフォーマットを取得します。

        Returns:
            エンコードされたデータのJSONフォーマット。
        """
        return 'base64'


class Base64UrlEncoder(EncoderProtocol):
    """URLセーフなBase64エンコーダ。"""

    @classmethod
    def decode(cls, data: bytes) -> bytes:
        """base64でエンコードされたバイトから元のバイトデータにデータをデコードします。

        Args:
            data: デコードするデータ。

        Returns:
            デコードされたデータ。
        """
        try:
            return base64.urlsafe_b64decode(data)
        except ValueError as e:
            raise PydanticCustomError('base64_decode', "Base64 decoding error: '{error}'", {'error': str(e)})

    @classmethod
    def encode(cls, value: bytes) -> bytes:
        """データをバイトからbase64エンコードされたバイトにエンコードします。

        Args:
            value: エンコードするデータ。

        Returns:
            エンコードされたデータ。
        """
        return base64.urlsafe_b64encode(value)

    @classmethod
    def get_json_format(cls) -> Literal['base64url']:
        """エンコードされたデータのJSONフォーマットを取得します。

        Returns:
            エンコードされたデータのJSONフォーマット。
        """
        return 'base64url'


@_dataclasses.dataclass(**_internal_dataclass.slots_true)
class EncodedBytes:
    """指定されたエンコーダを使用してエンコードおよびデコードされるバイトタイプ。

    `EncodedBytes`を動作させるには、`EncoderProtocol`を実装したエンコーダが必要です。

    ```py
    from typing_extensions import Annotated

    from pydantic import BaseModel, EncodedBytes, EncoderProtocol, ValidationError

    class MyEncoder(EncoderProtocol):
        @classmethod
        def decode(cls, data: bytes) -> bytes:
            if data == b'**undecodable**':
                raise ValueError('Cannot decode data')
            return data[13:]

        @classmethod
        def encode(cls, value: bytes) -> bytes:
            return b'**encoded**: ' + value

        @classmethod
        def get_json_format(cls) -> str:
            return 'my-encoder'

    MyEncodedBytes = Annotated[bytes, EncodedBytes(encoder=MyEncoder)]

    class Model(BaseModel):
        my_encoded_bytes: MyEncodedBytes

    # Initialize the model with encoded data
    m = Model(my_encoded_bytes=b'**encoded**: some bytes')

    # Access decoded value
    print(m.my_encoded_bytes)
    #> b'some bytes'

    # Serialize into the encoded form
    print(m.model_dump())
    #> {'my_encoded_bytes': b'**encoded**: some bytes'}

    # Validate encoded data
    try:
        Model(my_encoded_bytes=b'**undecodable**')
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        my_encoded_bytes
          Value error, Cannot decode data [type=value_error, input_value=b'**undecodable**', input_type=bytes]
        '''
    ```
    """

    encoder: type[EncoderProtocol]

    def __get_pydantic_json_schema__(
        self, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = handler(core_schema)
        field_schema.update(type='string', format=self.encoder.get_json_format())
        return field_schema

    def __get_pydantic_core_schema__(self, source: type[Any], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.with_info_after_validator_function(
            function=self.decode,
            schema=core_schema.bytes_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(function=self.encode),
        )

    def decode(self, data: bytes, _: core_schema.ValidationInfo) -> bytes:
        """指定されたエンコーダを使用してデータをデコードします。

        Args:
            data: デコードするデータ。

        Returns:
            デコードされたデータ。
        """
        return self.encoder.decode(data)

    def encode(self, value: bytes) -> bytes:
        """指定されたエンコーダを使用してデータをエンコードします。

        Args:
            value: エンコードするデータ。

        Returns:
            エンコードされたデータ。
        """
        return self.encoder.encode(value)

    def __hash__(self) -> int:
        return hash(self.encoder)


@_dataclasses.dataclass(**_internal_dataclass.slots_true)
class EncodedStr(EncodedBytes):
    """指定されたエンコーダを使用してエンコードおよびデコードされるstrタイプ。

    `EncodedStr`を動作させるには、`EncoderProtocol`を実装したエンコーダが必要です。

    ```py
    from typing_extensions import Annotated

    from pydantic import BaseModel, EncodedStr, EncoderProtocol, ValidationError

    class MyEncoder(EncoderProtocol):
        @classmethod
        def decode(cls, data: bytes) -> bytes:
            if data == b'**undecodable**':
                raise ValueError('Cannot decode data')
            return data[13:]

        @classmethod
        def encode(cls, value: bytes) -> bytes:
            return b'**encoded**: ' + value

        @classmethod
        def get_json_format(cls) -> str:
            return 'my-encoder'

    MyEncodedStr = Annotated[str, EncodedStr(encoder=MyEncoder)]

    class Model(BaseModel):
        my_encoded_str: MyEncodedStr

    # Initialize the model with encoded data
    m = Model(my_encoded_str='**encoded**: some str')

    # Access decoded value
    print(m.my_encoded_str)
    #> some str

    # Serialize into the encoded form
    print(m.model_dump())
    #> {'my_encoded_str': '**encoded**: some str'}

    # Validate encoded data
    try:
        Model(my_encoded_str='**undecodable**')
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        my_encoded_str
          Value error, Cannot decode data [type=value_error, input_value='**undecodable**', input_type=str]
        '''
    ```
    """

    def __get_pydantic_core_schema__(self, source: type[Any], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.with_info_after_validator_function(
            function=self.decode_str,
            schema=super(EncodedStr, self).__get_pydantic_core_schema__(source=source, handler=handler),  # noqa: UP008
            serialization=core_schema.plain_serializer_function_ser_schema(function=self.encode_str),
        )

    def decode_str(self, data: bytes, _: core_schema.ValidationInfo) -> str:
        """指定されたエンコーダを使用してデータをデコードします。

        Args:
            data: デコードするデータ。

        Returns:
            デコードされたデータ。
        """
        return data.decode()

    def encode_str(self, value: str) -> str:
        """指定されたエンコーダを使用してデータをエンコードします。

        Args:
            value: エンコードするデータ。

        Returns:
            エンコードされたデータ。
        """
        return super(EncodedStr, self).encode(value=value.encode()).decode()  # noqa: UP008

    def __hash__(self) -> int:
        return hash(self.encoder)


Base64Bytes = Annotated[bytes, EncodedBytes(encoder=Base64Encoder)]
"""標準の(URLセーフでない)base64エンコーダを使用してエンコードおよびデコードされるバイトタイプ。

Note:
    内部的には、`Base64Bytes`は標準ライブラリ`base64.encodebytes`と`base64.decodebytes`関数を使用します。

    その結果、`Base64Bytes`タイプを使用してURLセーフなbase64データをデコードしようとすると、失敗したり、不正なデコードが行われたりする可能性があります。

```py
from pydantic import Base64Bytes, BaseModel, ValidationError

class Model(BaseModel):
    base64_bytes: Base64Bytes

# Initialize the model with base64 data
m = Model(base64_bytes=b'VGhpcyBpcyB0aGUgd2F5')

# Access decoded value
print(m.base64_bytes)
#> b'This is the way'

# Serialize into the base64 form
print(m.model_dump())
#> {'base64_bytes': b'VGhpcyBpcyB0aGUgd2F5\n'}

# Validate base64 data
try:
    print(Model(base64_bytes=b'undecodable').base64_bytes)
except ValidationError as e:
    print(e)
    '''
    1 validation error for Model
    base64_bytes
      Base64 decoding error: 'Incorrect padding' [type=base64_decode, input_value=b'undecodable', input_type=bytes]
    '''
```
"""
Base64Str = Annotated[str, EncodedStr(encoder=Base64Encoder)]
"""標準の(URLセーフでない)base64エンコーダを使用してエンコードおよびデコードされるstrタイプ。

Note:
    内部的には、`Base64Bytes`は標準ライブラリ`base64.encodebytes`と`base64.decodebytes`関数を使用します。

    その結果、`Base64Str`型を使用してURLセーフなbase64データをデコードしようとすると、失敗したり、不正なデコードが行われたりする可能性があります。

```py
from pydantic import Base64Str, BaseModel, ValidationError

class Model(BaseModel):
    base64_str: Base64Str

# Initialize the model with base64 data
m = Model(base64_str='VGhlc2UgYXJlbid0IHRoZSBkcm9pZHMgeW91J3JlIGxvb2tpbmcgZm9y')

# Access decoded value
print(m.base64_str)
#> These aren't the droids you're looking for

# Serialize into the base64 form
print(m.model_dump())
#> {'base64_str': 'VGhlc2UgYXJlbid0IHRoZSBkcm9pZHMgeW91J3JlIGxvb2tpbmcgZm9y\n'}

# Validate base64 data
try:
    print(Model(base64_str='undecodable').base64_str)
except ValidationError as e:
    print(e)
    '''
    1 validation error for Model
    base64_str
      Base64 decoding error: 'Incorrect padding' [type=base64_decode, input_value='undecodable', input_type=str]
    '''
```
"""
Base64UrlBytes = Annotated[bytes, EncodedBytes(encoder=Base64UrlEncoder)]
"""URLセーフなbase64エンコーダを使用してエンコードおよびデコードされるバイトタイプ。

Note:
    内部的には、`Base64UrlBytes`は標準ライブラリ`base64.urlsafe_b64encode`および`base64.urlsafe_b64decode`関数を使用します。

    その結果、`Base64UrlBytes`型を使用して"普通の"base64データを忠実にデコードすることができます(`'+'`と`'/'`を使用)。

```py
from pydantic import Base64UrlBytes, BaseModel

class Model(BaseModel):
    base64url_bytes: Base64UrlBytes

# Initialize the model with base64 data
m = Model(base64url_bytes=b'SHc_dHc-TXc==')
print(m)
#> base64url_bytes=b'Hw?tw>Mw'
```
"""
Base64UrlStr = Annotated[str, EncodedStr(encoder=Base64UrlEncoder)]
"""URLセーフなbase64エンコーダを使用してエンコードおよびデコードされるstrタイプ。

Note:
    内部的には、`Base64UrlStr`は標準ライブラリ`base64.urlsafe_b64encode`および`base64.urlsafe_b64decode`関数を使用します。

    その結果、`Base64UrlStr`型を使用して、"普通の"base64データを忠実にデコードすることができます(`'+'`と`'/'`を使用)。

```py
from pydantic import Base64UrlStr, BaseModel

class Model(BaseModel):
    base64url_str: Base64UrlStr

# Initialize the model with base64 data
m = Model(base64url_str='SHc_dHc-TXc==')
print(m)
#> base64url_str='Hw?tw>Mw'
```
"""


__getattr__ = getattr_migration(__name__)


@_dataclasses.dataclass(**_internal_dataclass.slots_true)
class GetPydanticSchema:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/types/#using-getpydanticschema-to-reduce-boilerplate

    pydanticカスタム型フックを提供する注釈を作成するための便利なクラスです。

    このクラスは、`__get_pydantic_core_schema__`および`__get_pydantic_json_schema__`カスタムフックメソッドを定義するカスタム"マーカー"を作成する必要性をなくすことを目的としています。

    例えば、型チェッカーでは`int`として扱われますが、pydanticでは`Any`として扱われるようにするには、次のようにします。

    ```python
    from typing import Any

    from typing_extensions import Annotated

    from pydantic import BaseModel, GetPydanticSchema

    HandleAsAny = GetPydanticSchema(lambda _s, h: h(Any))

    class Model(BaseModel):
        x: Annotated[int, HandleAsAny]  # pydantic sees `x: Any`

    print(repr(Model(x='abc').x))
    #> 'abc'
    ```
    """

    get_pydantic_core_schema: Callable[[Any, GetCoreSchemaHandler], CoreSchema] | None = None
    get_pydantic_json_schema: Callable[[Any, GetJsonSchemaHandler], JsonSchemaValue] | None = None

    # Note: we may want to consider adding a convenience staticmethod `def for_type(type_: Any) -> GetPydanticSchema:`
    #   which returns `GetPydanticSchema(lambda _s, h: h(type_))`

    if not TYPE_CHECKING:
        # We put `__getattr__` in a non-TYPE_CHECKING block because otherwise, mypy allows arbitrary attribute access

        def __getattr__(self, item: str) -> Any:
            """Use this rather than defining `__get_pydantic_core_schema__` etc. to reduce the number of nested calls."""
            if item == '__get_pydantic_core_schema__' and self.get_pydantic_core_schema:
                return self.get_pydantic_core_schema
            elif item == '__get_pydantic_json_schema__' and self.get_pydantic_json_schema:
                return self.get_pydantic_json_schema
            else:
                return object.__getattribute__(self, item)

    __hash__ = object.__hash__


@_dataclasses.dataclass(**_internal_dataclass.slots_true, frozen=True)
class Tag:
    """(呼び出し可能な)識別された結合の場合に使用する、予期されるタグを指定する方法を提供します。

    また、エラーメッセージ内のUnionケースにラベルを付ける方法も提供します。

    呼び出し可能な`Discriminator`を使用する場合は、`Union`内の各ケースに`Tag`を付けて、そのケースを識別するために使用するタグを指定します。
    例えば、以下の例では`Tag`を使用して、`get_discriminator_value`が`'apple'`を返す場合、入力は`ApplePie`として検証されるべきであり、`'pumpkin'`を返す場合、入力は`PumpkinPie`として検証されるべきであることを指定しています。

    ここでの`Tag`の主な役割は、呼び出し可能な`Discriminator`関数からの戻り値を、問題の`Union`の適切なメンバーにマップすることです。

    ```py
    from typing import Any, Union

    from typing_extensions import Annotated, Literal

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
    '''
    ThanksgivingDinner(dessert=ApplePie(time_to_cook=60, num_ingredients=8, fruit='apple'))
    '''

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
    '''
    ThanksgivingDinner(dessert=PumpkinPie(time_to_cook=40, num_ingredients=6, filling='pumpkin'))
    '''
    ```

    !!! note
        呼び出し可能な`Discriminator`に関連付けられた`Tag`のすべてのケースに対して`Tag`を指定する必要があります。そうしないと、コード[`callable-discriminator-no-tag`](../errors/usage_errors.md#callable-discriminator-no-tag)で`PydantictUserError`が発生します。

    `Tag`の使い方の詳細については、[Discriminated Unions]concepts docsを参照してください。

    [Discriminated Unions]: https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/unions.md#discriminated-unions
    """

    tag: str

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        schema = handler(source_type)
        metadata = schema.setdefault('metadata', {})
        assert isinstance(metadata, dict)
        metadata[_core_utils.TAGGED_UNION_TAG_KEY] = self.tag
        return schema


@_dataclasses.dataclass(**_internal_dataclass.slots_true, frozen=True)
class Discriminator:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/unions/#discriminated-unions-with-callable-discriminator

    Union識別子の値を抽出する方法として、カスタムの呼び出し可能オブジェクトを使用する方法を提供します。

    これにより、`Field(discriminator=<field_name>)`から得られるような検証動作を得ることができますが、すべてのUnionの選択にわたって単一の共有フィールドを持つ必要はありません。これにより、識別されたUnionスタイルの検証エラーを持つモデルとプリミティブ型のUnionを処理することも可能になります。
    最後に、これにより、識別されたUnionのパフォーマンス上の利点をすべて確認しながら、値が属するUnionのメンバーを識別する方法として、カスタムの呼び出し可能オブジェクトを使用できます。

    この例を考えてみましょう。この例では、`Discriminator`と`TaggedUnion`を使用すると、通常の`Union`を使用する場合よりもはるかにパフォーマンスが向上します。

    ```py
    from typing import Any, Union

    from typing_extensions import Annotated, Literal

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
    '''
    ThanksgivingDinner(dessert=ApplePie(time_to_cook=60, num_ingredients=8, fruit='apple'))
    '''

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
    '''
    ThanksgivingDinner(dessert=PumpkinPie(time_to_cook=40, num_ingredients=6, filling='pumpkin'))
    '''
    ```

    `Discriminator`の使い方の詳細については、[Discriminated Unions]concepts docsを参照してください。

    [Discriminated Unions]: https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/unions.md#discriminated-unions
    """

    discriminator: str | Callable[[Any], Hashable]
    """タグ付きUnionの型を識別するための呼び出し可能な名前またはフィールド名。

    "呼び出し可能な"識別子は、入力から識別子の値を抽出する必要があります。
    `str`識別子は、識別するフィールドの名前でなければなりません。
    """
    custom_error_type: str | None = None
    """標準の識別されたUnion検証エラーを置き換える[custom errors](../errors/errors.md#custom-errors)で使用するタイプ。
    """
    custom_error_message: str | None = None
    """カスタムエラーで使用するメッセージ。"""
    custom_error_context: dict[str, int | str | float] | None = None
    """カスタムエラーで使用するコンテキスト。"""

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        origin = _typing_extra.get_origin(source_type)
        if not origin or not _typing_extra.origin_is_union(origin):
            raise TypeError(f'{type(self).__name__} must be used with a Union type, not {source_type}')

        if isinstance(self.discriminator, str):
            from pydantic import Field

            return handler(Annotated[source_type, Field(discriminator=self.discriminator)])
        else:
            original_schema = handler(source_type)
            return self._convert_schema(original_schema)

    def _convert_schema(self, original_schema: core_schema.CoreSchema) -> core_schema.TaggedUnionSchema:
        if original_schema['type'] != 'union':
            # This likely indicates that the schema was a single-item union that was simplified.
            # In this case, we do the same thing we do in
            # `pydantic._internal._discriminated_union._ApplyInferredDiscriminator._apply_to_root`, namely,
            # package the generated schema back into a single-item union.
            original_schema = core_schema.union_schema([original_schema])

        tagged_union_choices = {}
        for i, choice in enumerate(original_schema['choices']):
            tag = None
            if isinstance(choice, tuple):
                choice, tag = choice
            metadata = choice.get('metadata')
            if metadata is not None:
                metadata_tag = metadata.get(_core_utils.TAGGED_UNION_TAG_KEY)
                if metadata_tag is not None:
                    tag = metadata_tag
            if tag is None:
                raise PydanticUserError(
                    f'`Tag` not provided for choice {choice} used with `Discriminator`',
                    code='callable-discriminator-no-tag',
                )
            tagged_union_choices[tag] = choice

        # Have to do these verbose checks to ensure falsy values ('' and {}) don't get ignored
        custom_error_type = self.custom_error_type
        if custom_error_type is None:
            custom_error_type = original_schema.get('custom_error_type')

        custom_error_message = self.custom_error_message
        if custom_error_message is None:
            custom_error_message = original_schema.get('custom_error_message')

        custom_error_context = self.custom_error_context
        if custom_error_context is None:
            custom_error_context = original_schema.get('custom_error_context')

        custom_error_type = original_schema.get('custom_error_type') if custom_error_type is None else custom_error_type
        return core_schema.tagged_union_schema(
            tagged_union_choices,
            self.discriminator,
            custom_error_type=custom_error_type,
            custom_error_message=custom_error_message,
            custom_error_context=custom_error_context,
            strict=original_schema.get('strict'),
            ref=original_schema.get('ref'),
            metadata=original_schema.get('metadata'),
            serialization=original_schema.get('serialization'),
        )


_JSON_TYPES = {int, float, str, bool, list, dict, type(None)}


def _get_type_name(x: Any) -> str:
    type_ = type(x)
    if type_ in _JSON_TYPES:
        return type_.__name__

    # Handle proper subclasses; note we don't need to handle None or bool here
    if isinstance(x, int):
        return 'int'
    if isinstance(x, float):
        return 'float'
    if isinstance(x, str):
        return 'str'
    if isinstance(x, list):
        return 'list'
    if isinstance(x, dict):
        return 'dict'

    # Fail by returning the type's actual name
    return getattr(type_, '__name__', '<no type name>')


class _AllowAnyJson:
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        python_schema = handler(source_type)
        return core_schema.json_or_python_schema(json_schema=core_schema.any_schema(), python_schema=python_schema)


if TYPE_CHECKING:
    # This seems to only be necessary for mypy
    JsonValue: TypeAlias = Union[
        List['JsonValue'],
        Dict[str, 'JsonValue'],
        str,
        bool,
        int,
        float,
        None,
    ]
    """`JsonValue`は、JSONにシリアライズできる値を表すために使用されます。

    次のいずれかになります。

    * `List['JsonValue']`
    * `Dict[str, 'JsonValue']`
    * `str`
    * `bool`
    * `int`
    * `float`
    * `None`

    次の例は、`JsonValue`を使用してJSONデータを検証する方法と、入力データがJSONシリアライズ可能でない場合に予想されるエラーの種類を示しています。

    ```py
    import json

    from pydantic import BaseModel, JsonValue, ValidationError

    class Model(BaseModel):
        j: JsonValue

    valid_json_data = {'j': {'a': {'b': {'c': 1, 'd': [2, None]}}}}
    invalid_json_data = {'j': {'a': {'b': ...}}}

    print(repr(Model.model_validate(valid_json_data)))
    #> Model(j={'a': {'b': {'c': 1, 'd': [2, None]}}})
    print(repr(Model.model_validate_json(json.dumps(valid_json_data))))
    #> Model(j={'a': {'b': {'c': 1, 'd': [2, None]}}})

    try:
        Model.model_validate(invalid_json_data)
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        j.dict.a.dict.b
          input was not a valid JSON value [type=invalid-json-value, input_value=Ellipsis, input_type=ellipsis]
        '''
    ```
    """

else:
    JsonValue = TypeAliasType(
        'JsonValue',
        Annotated[
            Union[
                Annotated[List['JsonValue'], Tag('list')],
                Annotated[Dict[str, 'JsonValue'], Tag('dict')],
                Annotated[str, Tag('str')],
                Annotated[bool, Tag('bool')],
                Annotated[int, Tag('int')],
                Annotated[float, Tag('float')],
                Annotated[None, Tag('NoneType')],
            ],
            Discriminator(
                _get_type_name,
                custom_error_type='invalid-json-value',
                custom_error_message='input was not a valid JSON value',
            ),
            _AllowAnyJson,
        ],
    )


class _OnErrorOmit:
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        # there is no actual default value here but we use with_default_schema since it already has the on_error
        # behavior implemented and it would be no more efficient to implement it on every other validator
        # or as a standalone validator
        return core_schema.with_default_schema(schema=handler(source_type), on_error='omit')


OnErrorOmit = Annotated[T, _OnErrorOmit]
"""
リスト内の項目として使用される場合、dict内のキータイプ、TypedDictのオプションの値など。
この注釈では、検証中にエラーが発生した場合に、その項目を繰り返し処理から除外します。
つまり、[`ValidationError`][pydantic_core.ValidationError]が伝播されてiterable全体が破棄されるのではなく、無効な項目が破棄されて有効な項目が返されます。
"""


@_dataclasses.dataclass
class FailFast(_fields.PydanticMetadata, BaseMetadata):
    """`FailFast`アノテーションを使用して、最初のエラーで検証を停止するように指定できます。

    これは、大量のデータを検証する必要があり、そのデータが有効かどうかを知るだけでよい場合に便利です。

    データをより速く検証したい場合は、この設定を有効にすることができます(基本的に、これを使用すると、検証のパフォーマンスが向上しますが、取得する情報が少なくなります)。

    ```py
    from typing import List
    from typing_extensions import Annotated
    from pydantic import BaseModel, FailFast, ValidationError

    class Model(BaseModel):
        x: Annotated[List[int], FailFast()]

    # This will raise a single error for the first invalid value and stop validation
    try:
        obj = Model(x=[1, 2, 'a', 4, 5, 'b', 7, 8, 9, 'c'])
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        x.2
          Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
        '''
    ```
    """

    fail_fast: bool = True
