{% include-markdown "../warning.md" %}

<!-- Pydantic works well with [mypy](http://mypy-lang.org) right out of the box. -->
Pydanticはすぐに[mypy](http://mypy-lang.org)とうまく連携します。

<!-- However, Pydantic also ships with a mypy plugin that adds a number of important pydantic-specific features to mypy that improve its ability to type-check your code. -->
Pydanticにはmypyプラグインも付属しており、コードの型チェック機能を改善するpydantic固有の重要な機能がmypyに追加されています。

<!-- For example, consider the following script: -->
たとえば、次のスクリプトを考えてみます。

```py test="skip"
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Model(BaseModel):
    age: int
    first_name = 'John'
    last_name: Optional[str] = None
    signup_ts: Optional[datetime] = None
    list_of_ints: List[int]


m = Model(age=42, list_of_ints=[1, '2', b'3'])
print(m.middle_name)  # not a model field!
Model()  # will raise a validation error for age and list_of_ints
```

<!-- Without any special configuration, mypy does not catch the [missing model field annotation](https://docs.pydantic.dev/2.5/errors/usage_errors/#model-field-missing-annotation) and warns about the `list_of_ints` argument which Pydantic parses correctly: -->
特別な設定がなければ、mypyは[missing model field annotation](https://docs.pydantic.dev/2.5/errors/usage_errors/#model-field-missing-annotation)をキャッチせず、Pydanticが正しく解析する`list_of_ints`引数について警告します。

```
test.py:15: error: List item 1 has incompatible type "str"; expected "int"  [list-item]
test.py:15: error: List item 2 has incompatible type "bytes"; expected "int"  [list-item]
test.py:16: error: "Model" has no attribute "middle_name"  [attr-defined]
test.py:17: error: Missing named argument "age" for "Model"  [call-arg]
test.py:17: error: Missing named argument "list_of_ints" for "Model"  [call-arg]
```

<!-- But [with the plugin enabled](#enabling-the-plugin), it gives the correct error: -->
しかし、[with the plugin enabled](#enabling-the-plugin)、正しいエラーが表示されます。
```
9: error: Untyped fields disallowed  [pydantic-field]
16: error: "Model" has no attribute "middle_name"  [attr-defined]
17: error: Missing named argument "age" for "Model"  [call-arg]
17: error: Missing named argument "list_of_ints" for "Model"  [call-arg]
```

<!-- With the pydantic mypy plugin, you can fearlessly refactor your models knowing mypy will catch any mistakes if your field names or types change. -->
pydantic mypyプラグインを使用すると、フィールド名や型が変更された場合にmypyが間違いをキャッチすることを知っているので、恐れずにモデルをリファクタリングすることができます。

<!-- There are other benefits too! See below for more details. -->
他にも利点があります!詳細は以下を参照してください。

## Using mypy without the plugin

<!-- You can run your code through mypy with: -->
コードをmypyで実行するには、次のようにします。

```bash
mypy \
  --ignore-missing-imports \
  --follow-imports=skip \
  --strict-optional \
  pydantic_mypy_test.py
```

### Strict Optional

<!-- For your code to pass with `--strict-optional`, you need to use `Optional[]` or an alias of `Optional[]` for all fields with `None` as the default. (This is standard with mypy.) -->
コードで`--strict-optional`を渡すためには、デフォルトとして`None`を持つすべてのフィールドに`Optional[]`または`Optional[]`のエイリアスを使用する必要があります(これはmypyでは標準です)。

### Other Pydantic interfaces

<!-- Pydantic [dataclasses](../concepts/dataclasses.md) and the [`validate_call` decorator](../concepts/validation_decorator.md) should also work well with mypy. -->
Pydantic[dataclasses](../concepts/dataclasses.md)と[`validate_call` decorator](../concepts/validation_decorator.md)もmypyでうまく動作するはずです。

## Mypy Plugin Capabilities

### Generate a signature for `Model.__init__`
<!-- * Any required fields that don't have dynamically-determined aliases will be included as required keyword arguments.
* If `Config.populate_by_name=True`, the generated signature will use the field names, rather than aliases.
* If `Config.extra='forbid'` and you don't make use of dynamically-determined aliases, the generated signature will not allow unexpected inputs.
* **Optional:** If the [`init_forbid_extra` **plugin setting**](#configuring-the-plugin) is set to `True`, unexpected inputs to `__init__` will raise errors even if `Config.extra` is not `'forbid'`.
* **Optional:** If the [`init_typed` **plugin setting**](#configuring-the-plugin) is set to `True`, the generated signature will use the types of the model fields (otherwise they will be annotated as `Any` to allow parsing). -->
* 動的に決定されるエイリアスを持たない必須フィールドは、必須キーワード引数として含まれます。
* `Config.populate_by_name=True`の場合、生成されたシグネチャはエイリアスではなくフィールド名を使用します。
* `Config.extra='forbid'`で、動的に決定されるエイリアスを使用しない場合、生成されたシグネチャは予期しない入力を許可しません。
* **オプション:** [`init_forbid_extra` **plugin setting**](#configuring-the-plugin)が`True`に設定されている場合、`Config.extra`が`'forbid'`でなくても、`__init__`への予期しない入力によってエラーが発生します。
* **オプション:** [`init_typed` **plugin setting**](#configuring-the-plugin)が`True`に設定されている場合、生成されたシグネチャはモデルフィールドの型を使用します(そうでない場合は、解析を可能にするために`Any`として注釈が付けられます)。

### Generate a typed signature for `Model.model_construct`
<!-- * The [`model_construct`](../concepts/models.md#creating-models-without-validation) method is an alternative to `__init__` when input data is known to be valid and should not be parsed. Because this method performs no runtime validation, static checking is important to detect errors. -->
* [`model_construct`](../concepts/models.md#creating-models-without-validation)メソッドは、入力データが有効であることがわかっており、解析する必要がない場合に、`__init__`の代わりに使用できます。このメソッドは実行時に検証を行わないため、エラーを検出するには静的チェックが重要です。

### Respect `Config.frozen`
<!-- * If `Config.frozen` is `True`, you'll get a mypy error if you try to change the value of a model field; cf.
[faux immutability](../concepts/models.md#faux-immutability). -->
* `Config.frozen`が`True`の場合、モデルフィールドの値を変更しようとするとmypyエラーが発生します。[faux immutability](../concepts/models.md#faux-immutability)

### Generate a signature for `dataclasses`
<!-- * classes decorated with [`@pydantic.dataclasses.dataclass`](../concepts/dataclasses.md) are type checked the same as standard Python dataclasses
* The `@pydantic.dataclasses.dataclass` decorator accepts a `config` keyword argument which has the same meaning as [the `Config` sub-class](../concepts/config.md). -->
* [`@pydantic.dataclasses.dataclass`](../concepts/dataclasses.md)で装飾されたクラスは、標準のPythonデータクラスと同様に型チェックされます。
* `@pydantic.dataclasses.dataclass`デコレータは、[the `Config` sub-class](../concepts/config.md)と同じ意味を持つ`config`キーワード引数を受け入れます。

### Respect the type of the `Field`'s `default` and `default_factory`
<!-- * Field with both a `default` and a `default_factory` will result in an error during static checking.
* The type of the `default` and `default_factory` value must be compatible with the one of the field. -->
* `default`と`default_factory`の両方を持つフィールドは、静的チェック中にエラーになります。
* `default`および`default_factory`値の型は、フィールドの型と互換性がなければなりません。

### Warn about the use of untyped fields
<!-- * You'll get a mypy error any time you assign a public attribute on a model without annotating its type
* If your goal is to set a ClassVar, you should explicitly annotate the field using typing.ClassVar -->
* 型に注釈を付けずにモデルにパブリック属性を割り当てると、mypyエラーが発生します。
* 目的がClassVarを設定することである場合は、入力を使用してフィールドに明示的に注釈を付ける必要があります。ClassVar

## Optional Capabilities:
### Prevent the use of required dynamic aliases

<!-- * If the [`warn_required_dynamic_aliases` **plugin setting**](#configuring-the-plugin) is set to `True`, you'll get a mypy error any time you use a dynamically-determined alias or alias generator on a model with `Config.populate_by_name=False`.
* This is important because if such aliases are present, mypy cannot properly type check calls to `__init__`.
  In this case, it will default to treating all arguments as optional. -->
* [`warn_required_dynamic_aliases`**plugin setting**](#configuring-the-plugin)が`True`に設定されている場合、`Config.populate_by_name=False`のモデルで動的に決定されるエイリアスまたはエイリアスジェネレータを使用すると、mypyエラーが発生します。
* このようなエイリアスが存在すると、mypyは`__init__`を正しく型チェックできないので、これは重要です。
  この場合、デフォルトですべての引数がオプションとして扱われます。

## Enabling the Plugin

<!-- To enable the plugin, just add `pydantic.mypy` to the list of plugins in your [mypy config file](https://mypy.readthedocs.io/en/latest/config_file.html) (this could be `mypy.ini`, `pyproject.toml`, or `setup.cfg`). -->
プラグインを有効にするには、[mypy config file](https://mypy.readthedocs.io/en/latest/config_file.html)のプラグインのリストに`pydantic.mypy`を追加します(`mypy.ini`,`pyproject.toml`,`setup.cfg`)。

<!-- To get started, all you need to do is create a `mypy.ini` file with following contents: -->
開始するには、以下の内容の`mypy.ini`ファイルを作成するだけです。

```ini
[mypy]
plugins = pydantic.mypy
```

!!! note
  <!-- If you're using `pydantic.v1` models, you'll need to add `pydantic.v1.mypy` to your list of plugins. -->
  `pydantic.v1`モデルを使用している場合は、プラグインのリストに`pydantic.v1.mypy`を追加する必要があります。

<!-- The plugin is compatible with mypy versions `>=0.930`. -->
このプラグインはmypyバージョン`>=0.930`と互換性があります。

<!-- See the [plugin configuration](#configuring-the-plugin) docs for more details. -->
詳細については、[plugin configuration](#configuring-the-plugin)ドキュメントを参照してください。

### Configuring the Plugin
<!-- To change the values of the plugin settings, create a section in your mypy config file called `[pydantic-mypy]`, and add any key-value pairs for settings you want to override. -->
プラグイン設定の値を変更するには、mypy設定ファイルに`[pydantic-mypy]`というセクションを作成し、オーバーライドしたい設定のキーと値のペアを追加します。

<!-- A `mypy.ini` file with all plugin strictness flags enabled (and some other mypy strictness flags, too) might look like: -->
プラグインのstrictnessフラグをすべて有効にした`mypy.ini`ファイル(およびその他のmypy strictnessフラグも)は、次のようになります。

```ini
[mypy]
plugins = pydantic.mypy

follow_imports = silent
warn_redundant_casts = True
warn_unused_ignores = True
disallow_any_generics = True
check_untyped_defs = True
no_implicit_reexport = True

# for strict mypy: (this is the tricky one :-))
disallow_untyped_defs = True

[pydantic-mypy]
init_forbid_extra = True
init_typed = True
warn_required_dynamic_aliases = True
```

<!-- As of `mypy>=0.900`, mypy config may also be included in the `pyproject.toml` file rather than `mypy.ini`.
The same configuration as above would be: -->
`mypy>=0.900`の時点で、mypy configは`mypy.ini`ではなく`pyproject.toml`ファイルに含めることもできます。
上記と同じ設定は次のようになります。

```toml
[tool.mypy]
plugins = [
  "pydantic.mypy"
]

follow_imports = "silent"
warn_redundant_casts = true
warn_unused_ignores = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_reexport = true

# for strict mypy: (this is the tricky one :-))
disallow_untyped_defs = true

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true
```

#### Note on `--disallow-any-explicit`

<!-- If you're using the `--disallow-any-explicit` mypy config setting (or other settings that ban `Any`), you may encounter `no-any-explicit` errors when extending `BaseModel`. This is because by default, Pydantic's `mypy` plugin adds an `__init__` method with a signature like `def __init__(self, field_1: Any, field_2: Any, **kwargs: Any):` -->
`--disallow-any-explicit`mypy設定(または`Any`を禁止するその他の設定)を使用している場合、`BaseModel`を拡張するときに`no-any-explicit`エラーが発生する可能性があります。これは、デフォルトでは、Pydanticの`mypy`プラグインが`def__init__(self, field_1:Any, field_2:Any, **kwargs:Any):`のようなシグネチャを持つ`__init__`メソッドを追加するためです。

!!! note "Why the extra signature?"
    <!-- The Pydantic `mypy` plugin adds an `__init__` method with a signature like `def __init__(self, field_1: Any, field_2: Any, **kwargs: Any):` in order to avoid type errors when initializing models with types that don't match the field annotations.
    For example `Model(date='2024-01-01')` would raise a type error without this `Any` signature, but Pydantic has the ability to parse the string `'2024-01-01'` into a `datetime.date` type. -->
    Pydantic`mypy`プラグインは、フィールドアノテーションと一致しない型でモデルを初期化する際の型エラーを避けるために、`def__init__(self, field_1:Any, field_2:Any, **kwargs:Any):`のようなシグネチャを持つ`__init__`メソッドを追加します。
    例えば`Model(date='2024-01-01')`はこの`Any`シグネチャがなければ型エラーになりますが、Pydanticには文字列`'2024-01-01'`を`datetime.date`型に解析する機能があります。

<!-- To resolve this issue, you need to enable strict mode settings for the Pydantic mypy plugin. Specifically, add these options to your `[pydantic-mypy]` section: -->
この問題を解決するには、Pydantic mypyプラグインの厳密なモード設定を有効にする必要があります。具体的には、`[pydantic-mypy]`セクションに次のオプションを追加します。

```toml
[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
```

<!-- With `init_forbid_extra = True`, the `**kwargs` are removed from the generated `__init__` signature. With `init_typed = True`, the `Any` types for fields are replaced with their actual type hints. -->
`init_prohibit_extra=True`の場合、`**kwargs`は生成された`__init__`シグネチャから削除されます。`init_typed=True`の場合、フィールドの`Any`型は実際の型ヒントに置き換えられます。

<!-- This configuration allows you to use `--disallow-any-explicit` without getting errors on your Pydantic models. However, be aware that this stricter checking might flag some valid Pydantic use cases (like passing a string for a datetime field) as type errors. -->
この設定により、Pydanticモデルでエラーを発生させることなく`--disallow-any-explicit`を使用することができます。ただし、この厳密なチェックによって、有効なPydanticユースケース(datetimeフィールドに文字列を渡すなど)が型エラーとしてフラグ付けされる可能性があることに注意してください。
