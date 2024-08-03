{% include-markdown "../warning.md" %}

## Annotated Validators

??? api "API Documentation"
    [`pydantic.functional_validators.WrapValidator`][pydantic.functional_validators.WrapValidator]<br>
    [`pydantic.functional_validators.PlainValidator`][pydantic.functional_validators.PlainValidator]<br>
    [`pydantic.functional_validators.BeforeValidator`][pydantic.functional_validators.BeforeValidator]<br>
    [`pydantic.functional_validators.AfterValidator`][pydantic.functional_validators.AfterValidator]<br>

<!-- Pydantic provides a way to apply validators via use of `Annotated`.
You should use this whenever you want to bind validation to a type instead of model or field. -->
Pydanticは`Annotated`を使用してバリデータを適用する方法を提供します。
検証をモデルまたはフィールドではなく型にバインドする場合は、この関数を使用してください。

```py
from typing import Any, List

from typing_extensions import Annotated

from pydantic import BaseModel, ValidationError
from pydantic.functional_validators import AfterValidator


def check_squares(v: int) -> int:
    assert v**0.5 % 1 == 0, f'{v} is not a square number'
    return v


def double(v: Any) -> Any:
    return v * 2


MyNumber = Annotated[int, AfterValidator(double), AfterValidator(check_squares)]


class DemoModel(BaseModel):
    number: List[MyNumber]


print(DemoModel(number=[2, 8]))
#> number=[4, 16]
try:
    DemoModel(number=[2, 4])
except ValidationError as e:
    print(e)
    """
    1 validation error for DemoModel
    number.1
      Assertion failed, 8 is not a square number
    assert ((8 ** 0.5) % 1) == 0 [type=assertion_error, input_value=4, input_type=int]
    """
```

<!-- In this example we used some type aliases (`MyNumber = Annotated[...]`).
While this can help with legibility of the code, it is not required, you can use `Annotated` directly in a model field type hint.
These type aliases are also not actual types but you can use a similar approach with `TypeAliasType` to create actual types.
See [Custom Types](../concepts/types.md#custom-types) for a more detailed explanation of custom types. -->
この例では、いくつかの型エイリアス(`MyNumber=Annotated[...]`)を使用しました。
これはコードの読みやすさに役立ちますが、必須ではありません。モデルのフィールド型ヒントで直接`Annotated`を使用できます。
これらの型エイリアスも実際の型ではありませんが、`TypeAliasType`で同様のアプローチを使用して実際の型を作成できます。
カスタムタイプの詳細については、[Custom Types](../concepts/types.md#custom-types)を参照してください。

<!-- It is also worth noting that you can nest `Annotated` inside other types.
In this example we used that to apply validation to the inner items of a list.
The same approach can be used for dict keys, etc. -->
`Annotated`を他の型の中にネストできることも注目に値します。
この例では、これを使用して、リストの内部項目に検証を適用しました。
同じアプローチをdictキーなどにも使用できます。

### Before, After, Wrap and Plain validators

<!-- Pydantic provides multiple types of validator functions: -->
Pydanticには複数のタイプのバリデータ関数が用意されています。

<!-- * `After` validators run after Pydantic's internal parsing. They are generally more type safe and thus easier to implement.
* `Before` validators run before Pydantic's internal parsing and validation (e.g. coercion of a `str` to an `int`). These are more flexible than `After` validators since they can modify the raw input, but they also have to deal with the raw input, which in theory could be any arbitrary object.
* `Plain` validators are like a `mode='before'` validator but they terminate validation immediately, no further validators are called and Pydantic does not do any of its internal validation.
* `Wrap` validators are the most flexible of all. You can run code before or after Pydantic and other validators do their thing or you can terminate validation immediately, both with a successful value or an error. -->
* `After`バリデータは、Pydanticの内部解析の後に実行されます。一般的に型安全性が高いため、実装が簡単です。
* `Before`バリデータは、Pydanticの内部解析と検証の前に実行されます(例えば`str`の`int`への強制)。これらは生の入力を変更できるので`After`バリデータよりも柔軟ですが、理論的には任意のオブジェクトである生の入力も処理する必要があります。
* `Plain`バリデータは`mode='before'`バリデータのようなものですが、すぐに検証を終了し、それ以上のバリデータは呼び出されず、Pydanticは内部検証を行いません。
* `Wrap`バリデーターは、すべての中で最も柔軟です。Pydanticや他のバリデーターが処理を行う前または後にコードを実行することも、値が成功した場合やエラーが発生した場合に検証をすぐに終了することもできます。

<!-- You can use multiple before, after, or `mode='wrap'` validators, but only one `PlainValidator` since a plain validator will not call any inner validators. -->
複数のbefore、after、または`mode='wrap'`バリデータを使用できますが、`PlainValidator`は1つだけです。これは、プレーンバリデータは内部バリデータを呼び出さないためです。

<!-- Here's an example of a `mode='wrap'` validator: -->
以下に`mode='wrap'`バリデータの例を示します。

```python
import json
from typing import Any, List

from typing_extensions import Annotated

from pydantic import (
    BaseModel,
    ValidationError,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
)
from pydantic.functional_validators import WrapValidator


def maybe_strip_whitespace(
    v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
) -> int:
    if info.mode == 'json':
        assert isinstance(v, str), 'In JSON mode the input must be a string!'
        # you can call the handler multiple times
        try:
            return handler(v)
        except ValidationError:
            return handler(v.strip())
    assert info.mode == 'python'
    assert isinstance(v, int), 'In Python mode the input must be an int!'
    # do no further validation
    return v


MyNumber = Annotated[int, WrapValidator(maybe_strip_whitespace)]


class DemoModel(BaseModel):
    number: List[MyNumber]


print(DemoModel(number=[2, 8]))
#> number=[2, 8]
print(DemoModel.model_validate_json(json.dumps({'number': [' 2 ', '8']})))
#> number=[2, 8]
try:
    DemoModel(number=['2'])
except ValidationError as e:
    print(e)
    """
    1 validation error for DemoModel
    number.0
      Assertion failed, In Python mode the input must be an int!
    assert False
     +  where False = isinstance('2', int) [type=assertion_error, input_value='2', input_type=str]
    """
```

The same "modes" apply to `@field_validator`, which is discussed in the next section.
<!-- 同じ"モード"が`@field_validator`にも適用されます。これについては次のセクションで説明します。 -->

### Ordering of validators within `Annotated`

<!-- Order of validation metadata within `Annotated` matters.
Validation goes from right to left and back.
That is, it goes from right to left running all "before" validators (or calling into "wrap" validators), then left to right back out calling all "after" validators. -->
"注釈付き"事項内の検証メタデータの順序。
検証は右から左へ、そして逆方向に行われます。
つまり、右から左に向かってすべての"before"バリデーターを実行し(または"wrap"バリデーターを呼び出し)、左から右に戻ってすべての"after"バリデーターを呼び出します。

```py
from typing import Any, Callable, List, cast

from typing_extensions import Annotated, TypedDict

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    PlainValidator,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)
from pydantic.functional_validators import field_validator


class Context(TypedDict):
    logs: List[str]


def make_validator(label: str) -> Callable[[Any, ValidationInfo], Any]:
    def validator(v: Any, info: ValidationInfo) -> Any:
        context = cast(Context, info.context)
        context['logs'].append(label)
        return v

    return validator


def make_wrap_validator(
    label: str,
) -> Callable[[Any, ValidatorFunctionWrapHandler, ValidationInfo], Any]:
    def validator(
        v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
    ) -> Any:
        context = cast(Context, info.context)
        context['logs'].append(f'{label}: pre')
        result = handler(v)
        context['logs'].append(f'{label}: post')
        return result

    return validator


class A(BaseModel):
    x: Annotated[
        str,
        BeforeValidator(make_validator('before-1')),
        AfterValidator(make_validator('after-1')),
        WrapValidator(make_wrap_validator('wrap-1')),
        BeforeValidator(make_validator('before-2')),
        AfterValidator(make_validator('after-2')),
        WrapValidator(make_wrap_validator('wrap-2')),
        BeforeValidator(make_validator('before-3')),
        AfterValidator(make_validator('after-3')),
        WrapValidator(make_wrap_validator('wrap-3')),
        BeforeValidator(make_validator('before-4')),
        AfterValidator(make_validator('after-4')),
        WrapValidator(make_wrap_validator('wrap-4')),
    ]
    y: Annotated[
        str,
        BeforeValidator(make_validator('before-1')),
        AfterValidator(make_validator('after-1')),
        WrapValidator(make_wrap_validator('wrap-1')),
        BeforeValidator(make_validator('before-2')),
        AfterValidator(make_validator('after-2')),
        WrapValidator(make_wrap_validator('wrap-2')),
        PlainValidator(make_validator('plain')),
        BeforeValidator(make_validator('before-3')),
        AfterValidator(make_validator('after-3')),
        WrapValidator(make_wrap_validator('wrap-3')),
        BeforeValidator(make_validator('before-4')),
        AfterValidator(make_validator('after-4')),
        WrapValidator(make_wrap_validator('wrap-4')),
    ]

    val_x_before = field_validator('x', mode='before')(
        make_validator('val_x before')
    )
    val_x_after = field_validator('x', mode='after')(
        make_validator('val_x after')
    )
    val_y_wrap = field_validator('y', mode='wrap')(
        make_wrap_validator('val_y wrap')
    )


context = Context(logs=[])

A.model_validate({'x': 'abc', 'y': 'def'}, context=context)
print(context['logs'])
"""
[
    'val_x before',
    'wrap-4: pre',
    'before-4',
    'wrap-3: pre',
    'before-3',
    'wrap-2: pre',
    'before-2',
    'wrap-1: pre',
    'before-1',
    'after-1',
    'wrap-1: post',
    'after-2',
    'wrap-2: post',
    'after-3',
    'wrap-3: post',
    'after-4',
    'wrap-4: post',
    'val_x after',
    'val_y wrap: pre',
    'wrap-4: pre',
    'before-4',
    'wrap-3: pre',
    'before-3',
    'plain',
    'after-3',
    'wrap-3: post',
    'after-4',
    'wrap-4: post',
    'val_y wrap: post',
]
"""
```

## Validation of default values

<!-- Validators won't run when the default value is used.
This applies both to `@field_validator` validators and `Annotated` validators.
You can force them to run with `Field(validate_default=True)`. Setting `validate_default` to `True` has the closest behavior to using `always=True` in `validator` in Pydantic v1. However, you are generally better off using a `@model_validator(mode='before')` where the function is called before the inner validator is called. -->
デフォルト値を使用すると、バリデータは実行されません。
これは`@field_validator`バリデータと`Annotated`バリデータの両方に適用されます。
`Field(validate_default=True)`で強制的に実行させることができます。`validate_default`を`True`に設定することは、Pydantic v1の`validator`で`always=True`を使用することに最も近い動作をします。ただし、一般的には、内部バリデータが呼び出される前に関数が呼び出される`@model_validator(mode='before')`を使用する方がよいでしょう。

```py
from typing_extensions import Annotated

from pydantic import BaseModel, Field, field_validator


class Model(BaseModel):
    x: str = 'abc'
    y: Annotated[str, Field(validate_default=True)] = 'xyz'

    @field_validator('x', 'y')
    @classmethod
    def double(cls, v: str) -> str:
        return v * 2


print(Model())
#> x='abc' y='xyzxyz'
print(Model(x='foo'))
#> x='foofoo' y='xyzxyz'
print(Model(x='abc'))
#> x='abcabc' y='xyzxyz'
print(Model(x='foo', y='bar'))
#> x='foofoo' y='barbar'
```

## Field validators

??? api "API Documentation"
    [`pydantic.functional_validators.field_validator`][pydantic.functional_validators.field_validator]<br>

<!-- If you want to attach a validator to a specific field of a model you can use the `@field_validator` decorator. -->
モデルの特定のフィールドにバリデータを付加したい場合は、`@field_validator`デコレータを使用できます。

```py
from pydantic import (
    BaseModel,
    ValidationError,
    ValidationInfo,
    field_validator,
)


class UserModel(BaseModel):
    name: str
    id: int

    @field_validator('name')
    @classmethod
    def name_must_contain_space(cls, v: str) -> str:
        if ' ' not in v:
            raise ValueError('must contain a space')
        return v.title()

    # you can select multiple fields, or use '*' to select all fields
    @field_validator('id', 'name')
    @classmethod
    def check_alphanumeric(cls, v: str, info: ValidationInfo) -> str:
        if isinstance(v, str):
            # info.field_name is the name of the field being validated
            is_alphanumeric = v.replace(' ', '').isalnum()
            assert is_alphanumeric, f'{info.field_name} must be alphanumeric'
        return v


print(UserModel(name='John Doe', id=1))
#> name='John Doe' id=1

try:
    UserModel(name='samuel', id=1)
except ValidationError as e:
    print(e)
    """
    1 validation error for UserModel
    name
      Value error, must contain a space [type=value_error, input_value='samuel', input_type=str]
    """

try:
    UserModel(name='John Doe', id='abc')
except ValidationError as e:
    print(e)
    """
    1 validation error for UserModel
    id
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='abc', input_type=str]
    """

try:
    UserModel(name='John Doe!', id=1)
except ValidationError as e:
    print(e)
    """
    1 validation error for UserModel
    name
      Assertion failed, name must be alphanumeric
    assert False [type=assertion_error, input_value='John Doe!', input_type=str]
    """
```

<!-- A few things to note on validators: -->
バリデータに関して注意すべき点がいくつかあります。

<!-- * `@field_validator`s are "class methods", so the first argument value they receive is the `UserModel` class, not an instance of `UserModel`. We recommend you use the `@classmethod` decorator on them below the `@field_validator` decorator to get proper type checking.
* the second argument is the field value to validate; it can be named as you please
* the third argument, if present, is an instance of `pydantic.ValidationInfo`
* validators should either return the parsed value or raise a `ValueError` or `AssertionError` (``assert`` statements may be used).
* A single validator can be applied to multiple fields by passing it multiple field names.
* A single validator can also be called on *all* fields by passing the special value `'*'`. -->
* `@field_validator`は"クラスメソッド"であるため、受け取る最初の引数値は`UserModel`クラスであり、`UserModel`のインスタンスではありません。適切な型チェックを行うには、`@field_validator`デコレータの下で`@classmethod`デコレータを使用することをお勧めします。
* 2番目の引数は検証するフィールド値です。任意の名前を付けることができます。
* 3番目の引数が存在する場合は、`pydantic.ValidationInfo`のインスタンスです。
* バリデータは解析された値を返すか、`ValueError`または`AssertionError`を送出する必要があります(`assert`文を使用することもできます)。
* 1つのバリデータを複数のフィールドに適用するには、複数のフィールド名を渡します。
* 特殊な値`'*'`を渡すことで、*すべての*フィールドに対して単一のバリデータを呼び出すこともできます。

!!! warning
    <!-- If you make use of `assert` statements, keep in mind that running Python with the [`-O` optimization flag](https://docs.python.org/3/using/cmdline.html#cmdoption-o) disables `assert` statements, and **validators will stop working**. -->
    `assert`文を使用する場合、[`-O` optimization flag](https://docs.python.org/3/using/cmdline.html#cmdoption-o)を付けてPythonを実行すると`assert`文が無効になり、**バリデータが動作しなくなる**ことに注意してください。

!!! note
    <!-- `FieldValidationInfo` is **deprecated** in 2.4, use `ValidationInfo` instead. -->
    `FieldValidationInfo`は2.4で**廃止されました**。代わりに`ValidationInfo`を使用してください。

<!-- If you want to access values from another field inside a `@field_validator`, this may be possible using `ValidationInfo.data`, which is a dict of field name to field value.
Validation is done in the order fields are defined, so you have to be careful when using `ValidationInfo.data` to not access a field that has not yet been validated/populated — in the code above, for example, you would not be able to access `info.data['id']` from within `name_must_contain_space`.
However, in most cases where you want to perform validation using multiple field values, it is better to use `@model_validator` which is discussed in the section below. -->
`@field_validator`内の別のフィールドの値にアクセスしたい場合は、フィールド名からフィールド値への辞書である`ValidationInfo.data`を使用することができます。
検証はフィールドが定義された順序で行われるので、`ValidationInfo.data`を使用するときは、まだ検証/入力されていないフィールドにアクセスしないように注意する必要があります。たとえば、上記のコードでは、`name_must_contain_space`内から`info.data['id']`にアクセスすることはできません。
ただし、複数のフィールド値を使用して検証を実行する場合は、以下のセクションで説明する`@model_validator`を使用することをお勧めします。


## Model validators

??? api "API Documentation"
    [`pydantic.functional_validators.model_validator`][pydantic.functional_validators.model_validator]<br>

<!-- Validation can also be performed on the entire model's data using `@model_validator`. -->
検証は、`@model_validator`を使用してモデルのデータ全体に対して実行することもできます。

```py
from typing import Any

from typing_extensions import Self

from pydantic import BaseModel, ValidationError, model_validator


class UserModel(BaseModel):
    username: str
    password1: str
    password2: str

    @model_validator(mode='before')
    @classmethod
    def check_card_number_omitted(cls, data: Any) -> Any:
        if isinstance(data, dict):
            assert (
                'card_number' not in data
            ), 'card_number should not be included'
        return data

    @model_validator(mode='after')
    def check_passwords_match(self) -> Self:
        pw1 = self.password1
        pw2 = self.password2
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('passwords do not match')
        return self


print(UserModel(username='scolvin', password1='zxcvbn', password2='zxcvbn'))
#> username='scolvin' password1='zxcvbn' password2='zxcvbn'
try:
    UserModel(username='scolvin', password1='zxcvbn', password2='zxcvbn2')
except ValidationError as e:
    print(e)
    """
    1 validation error for UserModel
      Value error, passwords do not match [type=value_error, input_value={'username': 'scolvin', '... 'password2': 'zxcvbn2'}, input_type=dict]
    """

try:
    UserModel(
        username='scolvin',
        password1='zxcvbn',
        password2='zxcvbn',
        card_number='1234',
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for UserModel
      Assertion failed, card_number should not be included
    assert 'card_number' not in {'card_number': '1234', 'password1': 'zxcvbn', 'password2': 'zxcvbn', 'username': 'scolvin'} [type=assertion_error, input_value={'username': 'scolvin', '..., 'card_number': '1234'}, input_type=dict]
    """
```

!!! note "On return type checking"
    <!-- Methods decorated with `@model_validator` should return the self instance at the end of the method.
    For type checking purposes, you can use `Self` from either `typing` or the `typing_extensions` backport as the return type of the decorated method.
    In the context of the above example, you could also use `def check_passwords_match(self: 'UserModel') -> 'UserModel'` to indicate that the method returns an instance of the model. -->
    `@model_validator`でデコレートされたメソッドは、メソッドの最後にselfインスタンスを返します。
    型チェックの目的で、デコレートされたメソッドの戻り値の型として`typing`または`typing_extensions`バックポートから`Self`を使用できます。
    上記の例では、`def check_passwords_match(self:'UserModel')->'UserModel'`を使用して、メソッドがモデルのインスタンスを返すことを示すこともできます。

!!! note "On Inheritance"
    <!-- A `@model_validator` defined in a base class will be called during the validation of a subclass instance. -->
    基底クラスで定義された`@model_validator`は、サブクラスインスタンスの検証中に呼び出されます。

    <!-- Overriding a `@model_validator` in a subclass will override the base class' `@model_validator`, and thus only the subclass' version of said `@model_validator` will be called. -->
    サブクラスの`@model_validator`をオーバーライドすると、ベースクラスの'`@model_validator`がオーバーライドされるので、その`@model_validator`のサブクラスのバージョンだけが呼び出されます。

<!-- Model validators can be `mode='before'`, `mode='after'` or `mode='wrap'`. -->
モデルバリデータは`mode='before'`,`mode='after'`,`mode='wrap'`のいずれかです。

<!-- Before model validators are passed the raw input which is often a `dict[str, Any]` but could also be an instance of the model itself (e.g. if `UserModel.model_validate(UserModel.construct(...))` is called) or anything else since you can pass arbitrary objects into `model_validate`.
Because of this `mode='before'` validators are extremely flexible and powerful but can be cumbersome and error prone to implement.
Before model validators should be class methods.
The first argument should be `cls` (and we also recommend you use `@classmethod` below `@model_validator` for proper type checking), the second argument will be the input (you should generally type it as `Any` and use `isinstance` to narrow the type) and the third argument (if present) will be a `pydantic.ValidationInfo`. -->
モデルバリデータが渡される前に、生の入力が渡されます。これは`dict[str, Any]`であることがよくありますが、モデル自体のインスタンスであることもあります(例えば`UserModel.model_validate(UserModel.construct(...))`が呼び出された場合)。また、`model_validate`には任意のオブジェクトを渡すことができるので、その他のものでもかまいません。
このため、`mode='before'`バリデータは非常に柔軟で強力ですが、実装が煩雑でエラーが発生しやすくなります。
モデルの前では、バリデーターはクラスメソッドでなければなりません。
最初の引数は`cls`でなければならず(適切な型チェックのために`@model_validator`の下に`@classmethod`を使用することもお勧めします)、2番目の引数は入力になり(通常は`Any`と入力し、型を絞り込むために`isinstance`を使用します)、3番目の引数(存在する場合)は`pydantic.ValidationInfo`になります。

<!-- `mode='after'` validators are instance methods and always receive an instance of the model as the first argument. Be sure to return the instance at the end of your validator.
You should not use `(cls, ModelType)` as the signature, instead just use `(self)` and let type checkers infer the type of `self` for you.
Since these are fully type safe they are often easier to implement than `mode='before'` validators.
If any field fails to validate, `mode='after'` validators for that field will not be called. -->
`mode='after'`バリデータはインスタンスメソッドであり、常に最初の引数としてモデルのインスタンスを受け取ります。バリデータの最後に必ずインスタンスを返してください。
署名として`(cls, ModelType)`を使うべきではなく、単に`(self)`を使って、型チェッカーに`self`の型を推測させてください。
これらは完全に型安全なので、`mode='before'`バリデータよりも実装しやすいことがよくあります。
検証に失敗したフィールドがある場合、そのフィールドの`mode='after'`バリデータは呼び出されません。

## Handling errors in validators

<!-- As mentioned in the previous sections you can raise either a `ValueError` or `AssertionError` (including ones generated by `assert ...` statements) within a validator to indicate validation failed.
You can also raise a `PydanticCustomError` which is a bit more verbose but gives you extra flexibility.
Any other errors (including `TypeError`) are bubbled up and not wrapped in a `ValidationError`. -->
前のセクションで説明したように、バリデータ内で`ValueError`または`AssertionError`(`assert...`文によって生成されたものを含む)を発生させて、検証が失敗したことを示すことができます。
`PydanticCustomError`を発生させることもできます。これはもう少し冗長ですが、より柔軟性があります。
その他のエラー(`TypeError`を含む)はバブルアップされ、`ValidationError`にラップされません。

```python
from pydantic_core import PydanticCustomError

from pydantic import BaseModel, ValidationError, field_validator


class Model(BaseModel):
    x: int

    @field_validator('x')
    @classmethod
    def validate_x(cls, v: int) -> int:
        if v % 42 == 0:
            raise PydanticCustomError(
                'the_answer_error',
                '{number} is the answer!',
                {'number': v},
            )
        return v


try:
    Model(x=42 * 2)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    x
      84 is the answer! [type=the_answer_error, input_value=84, input_type=int]
    """
```

## Special Types

<!-- Pydantic provides a few special types that can be used to customize validation. -->
Pydanticには、検証をカスタマイズするために使用できる特殊な型がいくつか用意されています。

<!-- - [`InstanceOf`][pydantic.functional_validators.InstanceOf] is a type that can be used to validate that a value is an instance of a given class. -->
- [`InstanceOf`][pydantic.functional_validators.InstanceOf]は、値が指定されたクラスのインスタンスであることを検証するために使用できる型です。

```py
from typing import List

from pydantic import BaseModel, InstanceOf, ValidationError


class Fruit:
    def __repr__(self):
        return self.__class__.__name__


class Banana(Fruit): ...


class Apple(Fruit): ...


class Basket(BaseModel):
    fruits: List[InstanceOf[Fruit]]


print(Basket(fruits=[Banana(), Apple()]))
#> fruits=[Banana, Apple]
try:
    Basket(fruits=[Banana(), 'Apple'])
except ValidationError as e:
    print(e)
    """
    1 validation error for Basket
    fruits.1
      Input should be an instance of Fruit [type=is_instance_of, input_value='Apple', input_type=str]
    """
```

<!-- - [`SkipValidation`][pydantic.functional_validators.SkipValidation] is a type that can be used to skip validation on a field. -->
- [`SkipValidation`][pydantic.functional_validators.SkipValidation]は、フィールドの検証をスキップするために使用できる型です。


```py
from typing import List

from pydantic import BaseModel, SkipValidation


class Model(BaseModel):
    names: List[SkipValidation[str]]


m = Model(names=['foo', 'bar'])
print(m)
#> names=['foo', 'bar']

m = Model(names=['foo', 123])  # (1)!
print(m)
#> names=['foo', 123]
```

<!-- 1. Note that the validation of the second item is skipped. If it has the wrong type it will emit a warning during serialization. -->
1. 2番目のアイテムの検証はスキップされることに注意してください。タイプが間違っている場合は、シリアル化中に警告が表示されます。

## Field checks

<!-- During class creation, validators are checked to confirm that the fields they specify actually exist on the model. -->
クラスの作成中に、指定されたフィールドが実際にモデル上に存在することを確認するためにバリデーターがチェックされます。

<!-- This may be undesirable if, for example, you want to define a validator to validate fields that will only be present on subclasses of the model where the validator is defined. -->
これは、たとえば、バリデータが定義されているモデルのサブクラスにのみ存在するフィールドを検証するバリデータを定義する場合には望ましくないことがあります。

<!-- If you want to disable these checks during class creation, you can pass `check_fields=False` as a keyword argument to the validator. -->
クラスの作成中にこれらのチェックを無効にしたい場合は、`check_fields=False`をキーワード引数としてバリデータに渡すことができます。

## Dataclass validators

<!-- Validators also work with Pydantic dataclasses. -->
バリデーターはPydanticデータ・クラスでも動作します。

```py
from pydantic import field_validator
from pydantic.dataclasses import dataclass


@dataclass
class DemoDataclass:
    product_id: str  # should be a five-digit string, may have leading zeros

    @field_validator('product_id', mode='before')
    @classmethod
    def convert_int_serial(cls, v):
        if isinstance(v, int):
            v = str(v).zfill(5)
        return v


print(DemoDataclass(product_id='01234'))
#> DemoDataclass(product_id='01234')
print(DemoDataclass(product_id=2468))
#> DemoDataclass(product_id='02468')
```

## Validation Context

<!-- You can pass a context object to the validation methods which can be accessed from the `info` argument to decorated validator functions: -->
デコレートされたバリデータ関数の`info`引数からアクセスできる検証メソッドにコンテキストオブジェクトを渡すことができます。

```python
from pydantic import BaseModel, ValidationInfo, field_validator


class Model(BaseModel):
    text: str

    @field_validator('text')
    @classmethod
    def remove_stopwords(cls, v: str, info: ValidationInfo):
        context = info.context
        if context:
            stopwords = context.get('stopwords', set())
            v = ' '.join(w for w in v.split() if w.lower() not in stopwords)
        return v


data = {'text': 'This is an example document'}
print(Model.model_validate(data))  # no context
#> text='This is an example document'
print(Model.model_validate(data, context={'stopwords': ['this', 'is', 'an']}))
#> text='example document'
print(Model.model_validate(data, context={'stopwords': ['document']}))
#> text='This is an example'
```

<!-- This is useful when you need to dynamically update the validation behavior during runtime. For example, if you wanted a field to have a dynamically controllable set of allowed values, this could be done by passing the allowed values by context, and having a separate mechanism for updating what is allowed: -->
これは、実行時に検証動作を動的に更新する必要がある場合に便利です。たとえば、フィールドに動的に制御可能な許可された値のセットを持たせたい場合、コンテキストによって許可された値を渡し、許可されたものを更新するための別のメカニズムを持つことによって、これを行うことができます。

```python
from typing import Any, Dict, List

from pydantic import (
    BaseModel,
    ValidationError,
    ValidationInfo,
    field_validator,
)

_allowed_choices = ['a', 'b', 'c']


def set_allowed_choices(allowed_choices: List[str]) -> None:
    global _allowed_choices
    _allowed_choices = allowed_choices


def get_context() -> Dict[str, Any]:
    return {'allowed_choices': _allowed_choices}


class Model(BaseModel):
    choice: str

    @field_validator('choice')
    @classmethod
    def validate_choice(cls, v: str, info: ValidationInfo):
        allowed_choices = info.context.get('allowed_choices')
        if allowed_choices and v not in allowed_choices:
            raise ValueError(f'choice must be one of {allowed_choices}')
        return v


print(Model.model_validate({'choice': 'a'}, context=get_context()))
#> choice='a'

try:
    print(Model.model_validate({'choice': 'd'}, context=get_context()))
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model
    choice
      Value error, choice must be one of ['a', 'b', 'c'] [type=value_error, input_value='d', input_type=str]
    """

set_allowed_choices(['b', 'c'])

try:
    print(Model.model_validate({'choice': 'a'}, context=get_context()))
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model
    choice
      Value error, choice must be one of ['b', 'c'] [type=value_error, input_value='a', input_type=str]
    """
```

<!-- Similarly, you can [use a context for serialization](../concepts/serialization.md#serialization-context). -->
同様に、[use a context for serialization]こともできます(../concepts/serialization.md#serialization-context)。

### Using validation context with `BaseModel` initialization

<!-- Although there is no way to specify a context in the standard `BaseModel` initializer, you can work around this through the use of `contextvars.ContextVar` and a custom `__init__` method: -->
標準の`BaseModel`イニシャライザでコンテキストを指定する方法はありませんが、`contextvars.ContextVar`とカスタムの`__init__`メソッドを使用してこれを回避することができます。

```python
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Iterator

from pydantic import BaseModel, ValidationInfo, field_validator

_init_context_var = ContextVar('_init_context_var', default=None)


@contextmanager
def init_context(value: Dict[str, Any]) -> Iterator[None]:
    token = _init_context_var.set(value)
    try:
        yield
    finally:
        _init_context_var.reset(token)


class Model(BaseModel):
    my_number: int

    def __init__(self, /, **data: Any) -> None:
        self.__pydantic_validator__.validate_python(
            data,
            self_instance=self,
            context=_init_context_var.get(),
        )

    @field_validator('my_number')
    @classmethod
    def multiply_with_context(cls, value: int, info: ValidationInfo) -> int:
        if info.context:
            multiplier = info.context.get('multiplier', 1)
            value = value * multiplier
        return value


print(Model(my_number=2))
#> my_number=2

with init_context({'multiplier': 3}):
    print(Model(my_number=2))
    #> my_number=6

print(Model(my_number=2))
#> my_number=2
```

## Reusing Validators

<!-- Occasionally, you will want to use the same validator on multiple fields/models (e.g. to normalize some input data).
The "naive" approach would be to write a separate function, then call it from multiple decorators.
Obviously, this entails a lot of repetition and boiler plate code.
The following approach demonstrates how you can reuse a validator so that redundancy is minimized and the models become again almost declarative. -->
場合によっては、複数のフィールド/モデルに対して同じバリデータを使用することもあります(たとえば、一部の入力データを正規化する場合)。
"単純な"アプローチは、別の関数を作成し、複数のデコレータからそれを呼び出すことです。
明らかに、これは多くの繰り返しとボイラープレートコードを必要とします。
次のアプローチでは、冗長性が最小限に抑えられ、モデルが再びほぼ宣言型になるように、バリデータを再利用する方法を示します。

```py
from pydantic import BaseModel, field_validator


def normalize(name: str) -> str:
    return ' '.join((word.capitalize()) for word in name.split(' '))


class Producer(BaseModel):
    name: str

    _normalize_name = field_validator('name')(normalize)


class Consumer(BaseModel):
    name: str

    _normalize_name = field_validator('name')(normalize)


jane_doe = Producer(name='JaNe DOE')
print(repr(jane_doe))
#> Producer(name='Jane Doe')
john_doe = Consumer(name='joHN dOe')
print(repr(john_doe))
#> Consumer(name='John Doe')
```
