---
<!-- description: Support for loading a settings or config class from environment variables or secrets files. -->
description: 環境変数またはシークレットファイルから設定クラスまたは構成クラスをロードするためのサポートです。
---

# Settings Management

{% include-markdown "../warning.md" %}

<!-- [Pydantic Settings](https://github.com/pydantic/pydantic-settings) provides optional Pydantic features for loading a settings or config class from environment variables or secrets files. -->
[Pydantic Settings](https://github.com/pydantic/pydantic-settings)は、環境変数やシークレットファイルから設定や構成クラスをロードするためのオプションのPydantic機能を提供します。

<!-- {{ external_markdown('https://raw.githubusercontent.com/pydantic/pydantic-settings/main/docs/index.md', '') }} -->
!!! warning
    このドキュメントは、https://raw.githubusercontent.com/pydantic/pydantic-settings/main/docs/index.md にリンクされたドキュメントのコピーを翻訳しています。

## Installation

<!-- Installation is as simple as: -->
インストールは次のように簡単です。

```bash
pip install pydantic-settings
```

## Usage

<!-- If you create a model that inherits from `BaseSettings`, the model initialiser will attempt to determine the values of any fields not passed as keyword arguments by reading from the environment. (Default values will still be used if the matching environment variable is not set.) -->
`BaseSettings`から継承するモデルを作成した場合、モデルイニシャライザは、キーワード引数として渡されていないフィールドの値を、環境から読み取って決定しようとします(一致する環境変数が設定されていない場合でも、デフォルト値が使用されます)。

<!-- This makes it easy to: -->
これにより、次のことが容易になります。

<!-- * Create a clearly-defined, type-hinted application configuration class
* Automatically read modifications to the configuration from environment variables
* Manually override specific settings in the initialiser where desired (e.g. in unit tests) -->
* 明確に定義され、型をヒントにしたアプリケーション構成クラスの作成
* 環境変数から構成への変更を自動的な読み取り
* 必要に応じて、イニシャライザの特定の設定を手動での上書き(ユニットテストなど)

<!-- For example: -->
次に例を示します。

```py
from typing import Any, Callable, Set

from pydantic import (
    AliasChoices,
    AmqpDsn,
    BaseModel,
    Field,
    ImportString,
    PostgresDsn,
    RedisDsn,
)

from pydantic_settings import BaseSettings, SettingsConfigDict


class SubModel(BaseModel):
    foo: str = 'bar'
    apple: int = 1


class Settings(BaseSettings):
    auth_key: str = Field(validation_alias='my_auth_key')  # (1)!

    api_key: str = Field(alias='my_api_key')  # (2)!

    redis_dsn: RedisDsn = Field(
        'redis://user:pass@localhost:6379/1',
        validation_alias=AliasChoices('service_redis_dsn', 'redis_url'),  # (3)!
    )
    pg_dsn: PostgresDsn = 'postgres://user:pass@localhost:5432/foobar'
    amqp_dsn: AmqpDsn = 'amqp://user:pass@localhost:5672/'

    special_function: ImportString[Callable[[Any], Any]] = 'math.cos'  # (4)!

    # to override domains:
    # export my_prefix_domains='["foo.com", "bar.com"]'
    domains: Set[str] = set()

    # to override more_settings:
    # export my_prefix_more_settings='{"foo": "x", "apple": 1}'
    more_settings: SubModel = SubModel()

    model_config = SettingsConfigDict(env_prefix='my_prefix_')  # (5)!


print(Settings().model_dump())
"""
{
    'auth_key': 'xxx',
    'api_key': 'xxx',
    'redis_dsn': Url('redis://user:pass@localhost:6379/1'),
    'pg_dsn': MultiHostUrl('postgres://user:pass@localhost:5432/foobar'),
    'amqp_dsn': Url('amqp://user:pass@localhost:5672/'),
    'special_function': math.cos,
    'domains': set(),
    'more_settings': {'foo': 'bar', 'apple': 1},
}
"""
```

<!-- 1. The environment variable name is overridden using `validation_alias`. In this case, the environment variable `my_auth_key` will be read instead of `auth_key`. Check the [`Field` documentation](fields.md) for more information. -->
1. 環境変数名は`validation_alias`を使用してオーバーライドされます。この場合、環境変数`my_auth_key`が`auth_key`の代わりに読み込まれます。詳細については、[`Field`documentation](fields.md)を参照してください。

<!-- 2. The environment variable name is overridden using `alias`. In this case, the environment variable `my_api_key` will be used for both validation and serialization instead of `api_key`. Check the [`Field` documentation](fields.md#field-aliases) for more information. -->
2. 環境変数名は`alias`を使用してオーバーライドされます。この場合、環境変数`my_api_key`が検証とシリアライゼーションの両方に`api_key`の代わりに使用されます。詳細については、[`Field`documentation](fields.md#field-aliases)を参照してください。

<!-- 3. The `AliasChoices` class allows to have multiple environment variable names for a single field. The first environment variable that is found will be used. Check the [`AliasChoices`](alias.md#aliaspath-and-aliaschoices) for more information. -->
3. `AliasChoices`クラスでは、1つのフィールドに対して複数の環境変数名を持つことができます。最初に見つかった環境変数が使用されます。詳細については、[`AliasChoices`](alias.md#aliaspath-and-AliasChoices)を確認してください。

<!-- 4. The `ImportString` class allows to import an object from a string. In this case, the environment variable `special_function` will be read and the function `math.cos` will be imported. -->
4. `ImportString`クラスを使用すると、文字列からオブジェクトをインポートできます。この場合、環境変数`special_function`が読み込まれ、関数`math.cos`がインポートされます。

<!-- 5. The `env_prefix` config setting allows to set a prefix for all environment variables. Check the [Environment variable names documentation](#environment-variable-names) for more information. -->
5. `env_prefix`構成設定では、すべての環境変数に接頭辞を設定できます。詳細については、[環境変数名のドキュメント](#environment-variable-names)を参照してください。

## Validation of default values

<!-- Unlike pydantic `BaseModel`, default values of `BaseSettings` fields are validated by default.
You can disable this behaviour by setting `validate_default=False` either in `model_config` or on field level by `Field(validate_default=False)`: -->
pydanicの`BaseModel`とは異なり、`BaseSettings`フィールドのデフォルト値はデフォルトで検証されます。
この動作を無効にするには、`model_config`または`Field(validate_default=False)`のフィールドレベルで`validate_default=False`を設定します。

```py
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(validate_default=False)

    # default won't be validated
    foo: int = 'test'


print(Settings())
#> foo='test'


class Settings1(BaseSettings):
    # default won't be validated
    foo: int = Field('test', validate_default=False)


print(Settings1())
#> foo='test'
```

<!-- Check the [Validation of default values](validators.md#validation-of-default-values) for more information. -->
詳細については、[Validation of default values](validators.md#validation-of-default-values)を参照してください。

## Environment variable names

<!-- By default, the environment variable name is the same as the field name. -->
デフォルトでは、環境変数名はフィールド名と同じです。

<!-- You can change the prefix for all environment variables by setting the `env_prefix` config setting, or via the `_env_prefix` keyword argument on instantiation: -->
すべての環境変数のプレフィックスを変更するには、`env_prefix`config設定を設定するか、インスタンス化時に`_env_prefix`キーワード引数を使用します。

```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='my_prefix_')

    auth_key: str = 'xxx'  # will be read from `my_prefix_auth_key`
```

!!! note
    <!-- The default `env_prefix` is `''` (empty string). -->
    デフォルトの`env_prefix`は`''`(空文字列)です。

<!-- If you want to change the environment variable name for a single field, you can use an alias. -->
1つのフィールドの環境変数名を変更する場合は、エイリアスを使用できます。

<!-- There are two ways to do this: -->
これには2つの方法があります。

<!-- * Using `Field(alias=...)` (see `api_key` above)
* Using `Field(validation_alias=...)` (see `auth_key` above) -->
* `Field(alias=...)`を使用する(上記の`api_key`を参照)
* `Field(validation_alias=...)`を使用します(上記の`auth_key`を参照)

<!-- Check the [`Field` aliases documentation](fields.md#field-aliases) for more information about aliases. -->
エイリアスの詳細については、[`Field`aliases documentation](fields.md#field-aliases)を参照してください。

<!-- `env_prefix` does not apply to fields with alias. It means the environment variable name is the same as field alias: -->
`env_prefix`はエイリアスを持つフィールドには適用されません。これは、環境変数名がフィールドエイリアスと同じであることを意味します:

```py
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='my_prefix_')

    foo: str = Field('xxx', alias='FooAlias')  # (1)!
```

1. `env_prefix` will be ignored and the value will be read from `FooAlias` environment variable.

### Case-sensitivity

<!-- By default, environment variable names are case-insensitive. -->
デフォルトでは、環境変数名の大文字と小文字は区別されません。

<!-- If you want to make environment variable names case-sensitive, you can set the `case_sensitive` config setting: -->
環境変数名の大文字と小文字を区別する場合は、`case_sensitive`構成設定を設定します。

```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    redis_host: str = 'localhost'
```

<!-- When `case_sensitive` is `True`, the environment variable names must match field names (optionally with a prefix), so in this example `redis_host` could only be modified via `export redis_host`.
If you want to name environment variables all upper-case, you should name attribute all upper-case too.
You can still name environment variables anything you like through `Field(validation_alias=...)`. -->
`case_sensitive`が`True`の場合、環境変数名はフィールド名と一致する必要があります(オプションで接頭辞が必要)。したがって、この例では`redis_host`は`export redis_host`を介してのみ変更できます。
環境変数にすべて大文字の名前を付ける場合は、attributeにもすべて大文字の名前を付ける必要があります。
`Field(validation_alias=...)`を使用して、環境変数に任意の名前を付けることができます。

<!-- Case-sensitivity can also be set via the `_case_sensitive` keyword argument on instantiation. -->
大文字と小文字の区別は、インスタンス化時に`_case_sensitive`キーワード引数を使用して設定することもできます。

<!-- In case of nested models, the `case_sensitive` setting will be applied to all nested models. -->
ネストされたモデルの場合、`case_sensitive`設定はすべてのネストされたモデルに適用されます。

```py
import os

from pydantic import BaseModel, ValidationError

from pydantic_settings import BaseSettings


class RedisSettings(BaseModel):
    host: str
    port: int


class Settings(BaseSettings, case_sensitive=True):
    redis: RedisSettings


os.environ['redis'] = '{"host": "localhost", "port": 6379}'
print(Settings().model_dump())
#> {'redis': {'host': 'localhost', 'port': 6379}}
os.environ['redis'] = '{"HOST": "localhost", "port": 6379}'  # (1)!
try:
    Settings()
except ValidationError as e:
    print(e)
    """
    1 validation error for Settings
    redis.host
      Field required [type=missing, input_value={'HOST': 'localhost', 'port': 6379}, input_type=dict]
        For further information visit https://errors.pydantic.dev/2/v/missing
    """
```

<!-- 1. Note that the `host` field is not found because the environment variable name is `HOST` (all upper-case). -->
1. 環境変数名が`HOST`(すべて大文字)であるため、`host`フィールドが見つからないことに注意してください。

!!! note
    <!-- On Windows, Python's `os` module always treats environment variables as case-insensitive, so the `case_sensitive` config setting will have no effect - settings will always be updated ignoring case. -->
    Windowsでは、Pythonの`os`モジュールは常に環境変数を大文字小文字を区別しないものとして扱うので、`case_sensitive`設定には何の効果もありません。設定は常に大文字小文字を無視して更新されます。

## Parsing environment variable values

<!-- By default environment variables are parsed verbatim, including if the value is empty. You can choose to ignore empty environment variables by setting the `env_ignore_empty` config setting to `True`.
This can be useful if you would prefer to use the default value for a field rather than an empty value from the environment. -->
デフォルトでは、環境変数は値が空の場合も含めて逐語的にパースされます。`env_ignore_empty`設定を`True`に設定することで、空の環境変数を無視することを選択できます。
これは、環境からの空の値ではなく、フィールドのデフォルト値を使用する場合に便利です。

<!-- For most simple field types (such as `int`, `float`, `str`, etc.), the environment variable value is parsed the same way it would be if passed directly to the initialiser (as a string). -->
ほとんどの単純なフィールド型(`int`、`float`、`str`など)では、環境変数の値はイニシャライザに(文字列として)直接渡された場合と同じようにパースされます。

<!-- Complex types like `list`, `set`, `dict`, and sub-models are populated from the environment by treating the environment variable's value as a JSON-encoded string. -->
`list`、`set`、`dict`、サブモデルなどの複雑な型は、環境変数の値をJSONでエンコードされた文字列として扱うことによって、環境から生成されます。

<!-- Another way to populate nested complex variables is to configure your model with the `env_nested_delimiter` config setting, then use an environment variable with a name pointing to the nested module fields.
What it does is simply explodes your variable into nested models or dicts.
So if you define a variable `FOO__BAR__BAZ=123` it will convert it into `FOO={'BAR': {'BAZ': 123}}`
If you have multiple variables with the same structure they will be merged. -->
ネストされた複合変数を設定するもう1つの方法は、`env_nested_delimiter`構成設定でモデルを構成し、ネストされたモジュールフィールドを指す名前の環境変数を使用することです。
これは単に、変数をネストされたモデルやディクテーションに展開するだけです。
ですから、変数`FOO__BAR__BAZ=123`を定義すると、`FOO={'BAR':{'BAZ':123}}`に変換されます。
同じ構造を持つ複数の変数がある場合、それらはマージされます。

!!! note
    <!-- Sub model has to inherit from `pydantic.BaseModel`, Otherwise `pydantic-settings` will initialize sub model, collects values for sub model fields separately, and you may get unexpected results. -->
    サブモデルは`pydantic.BaseModel`から継承する必要があります。そうしないと、`pydantic-settings`がサブモデルを初期化し、サブモデルフィールドの値を個別に収集し、予期しない結果になる可能性があります。

<!-- As an example, given the following environment variables: -->
たとえば、次の環境変数があるとします。

```bash
# your environment
export V0=0
export SUB_MODEL='{"v1": "json-1", "v2": "json-2"}'
export SUB_MODEL__V2=nested-2
export SUB_MODEL__V3=3
export SUB_MODEL__DEEP__V4=v4
```

<!-- You could load them into the following settings model: -->
次の設定モデルにロードすることができます。

```py
from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepSubModel(BaseModel):  # (1)!
    v4: str


class SubModel(BaseModel):  # (2)!
    v1: str
    v2: bytes
    v3: int
    deep: DeepSubModel


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter='__')

    v0: str
    sub_model: SubModel


print(Settings().model_dump())
"""
{
    'v0': '0',
    'sub_model': {'v1': 'json-1', 'v2': b'nested-2', 'v3': 3, 'deep': {'v4': 'v4'}},
}
"""
```

<!-- 1. Sub model has to inherit from `pydantic.BaseModel`. -->
1. サブモデルは`pydantic.BaseModel`から継承する必要があります。

<!-- 2. Sub model has to inherit from `pydantic.BaseModel`. -->
2. サブモデルは`pydantic.BaseModel`から継承する必要があります。

<!-- `env_nested_delimiter` can be configured via the `model_config` as shown above, or via the `_env_nested_delimiter` keyword argument on instantiation. -->
`env_nested_delimiter`は、上記のように`model_config`を介して、またはインスタンス化時に`_env_nested_delimiter`キーワード引数を介して設定できます。

<!-- Nested environment variables take precedence over the top-level environment variable JSON (e.g. in the example above, `SUB_MODEL__V2` trumps `SUB_MODEL`). -->
ネストされた環境変数は、トップレベルの環境変数JSONよりも優先されます(例えば、上の例では`SUB_MODEL__V2`が`SUB_MODEL`より優先されます)。

<!-- You may also populate a complex type by providing your own source class. -->
また、独自のソースクラスを指定して複合型を生成することもできます。

```py
import json
import os
from typing import Any, List, Tuple, Type

from pydantic.fields import FieldInfo

from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)


class MyCustomSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == 'numbers':
            return [int(x) for x in value.split(',')]
        return json.loads(value)


class Settings(BaseSettings):
    numbers: List[int]

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (MyCustomSource(settings_cls),)


os.environ['numbers'] = '1,2,3'
print(Settings().model_dump())
#> {'numbers': [1, 2, 3]}
```

## Dotenv (.env) support

<!-- Dotenv files (generally named `.env`) are a common pattern that make it easy to use environment variables in a platform-independent manner. -->
.envファイル(通常は`.env`)は、プラットフォームに依存しない方法で環境変数を簡単に使用できるようにする一般的なパターンです。

<!-- A dotenv file follows the same general principles of all environment variables, and it looks like this: -->
.envファイルは、すべての環境変数と同じ一般原則に従い、次のようになります。

```bash title=".env"
# ignore comment
ENVIRONMENT="production"
REDIS_ADDRESS=localhost:6379
MEANING_OF_LIFE=42
MY_VAR='Hello world'
```

<!-- Once you have your `.env` file filled with variables, *pydantic* supports loading it in two ways: -->
`.env`ファイルに変数を入れると、*pydantic*は以下の2つの方法でロードをサポートします。

<!-- 1. Setting the `env_file` (and `env_file_encoding` if you don't want the default encoding of your OS) on `model_config` in the `BaseSettings` class: -->
1. `BaseSettings`クラスの`model_config`で`env_file`(およびOSのデフォルトエンコーディングが不要な場合は`env_file_encoding`)を設定します。
   ````py hl_lines="4 5"
   from pydantic_settings import BaseSettings, SettingsConfigDict


   class Settings(BaseSettings):
       model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
   ````
<!-- 2. Instantiating the `BaseSettings` derived class with the `_env_file` keyword argument (and the `_env_file_encoding` if needed): -->
2. `_env_file`キーワード引数(および必要に応じて`_env_file_encoding`)を使用して`BaseSettings`派生クラスをインスタンス化します。
   ````py hl_lines="8"
   from pydantic_settings import BaseSettings, SettingsConfigDict


   class Settings(BaseSettings):
       model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


   settings = Settings(_env_file='prod.env', _env_file_encoding='utf-8')
   ````
<!-- In either case, the value of the passed argument can be any valid path or filename, either absolute or relative to the current working directory. From there, *pydantic* will handle everything for you by loading in your variables and validating them. -->
どちらの場合も、渡される引き数の値は任意の有効なパスまたはファイル名(絶対パスまたは現在の作業ディレクトリからの相対パス)にすることができます。そこから、*pydantic*は変数をロードして検証することで、すべてを処理します。

!!! note
    <!-- If a filename is specified for `env_file`, Pydantic will only check the current working directory and won't check any parent directories for the `.env` file. -->
    `env_file`にファイル名が指定されている場合、Pydanticは現在の作業ディレクトリのみをチェックし、`.env`ファイルの親ディレクトリはチェックしません。

<!-- Even when using a dotenv file, *pydantic* will still read environment variables as well as the dotenv file, **environment variables will always take priority over values loaded from a dotenv file**. -->
.envファイルを使用している場合でも、*pydantic*は環境変数とdotenvファイルを読み込みます。**環境変数は常にdotenvファイルからロードされた値よりも優先されます**。

<!-- Passing a file path via the `_env_file` keyword argument on instantiation (method 2) will override the value (if any) set on the `model_config` class. If the above snippets were used in conjunction, `prod.env` would be loaded while `.env` would be ignored. -->
インスタンス化(方法2)で`_env_file`キーワード引数を介してファイルパスを渡すと、`model_config`クラスに設定された値(もしあれば)が上書きされます。上記のスニペットが一緒に使用された場合、`prod.env`がロードされ、`.env`は無視されます。

<!-- If you need to load multiple dotenv files, you can pass multiple file paths as a tuple or list. The files will be loaded in order, with each file overriding the previous one. -->
複数のdotenvファイルをロードする必要がある場合は、複数のファイルパスをタプルまたはリストとして渡すことができます。ファイルは順番にロードされ、各ファイルが前のファイルを上書きします。

```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # `.env.prod` takes priority over `.env`
        env_file=('.env', '.env.prod')
    )
```

<!-- You can also use the keyword argument override to tell Pydantic not to load any file at all (even if one is set in the `model_config` class) by passing `None` as the instantiation keyword argument, e.g. `settings = Settings(_env_file=None)`. -->
`settings=Settings(_env_file=None)`のように、キーワード引数overrideを使用して、インスタンス化キーワード引数として`None`を渡すことで、(`model_config`クラスにファイルが設定されていても)ファイルをまったくロードしないようにPydanticに指示することもできます。

<!-- Because python-dotenv is used to parse the file, bash-like semantics such as `export` can be used which (depending on your OS and environment) may allow your dotenv file to also be used with `source`, see [python-dotenv's documentation](https://saurabh-kumar.com/python-dotenv/#usages) for more details. -->
python-dotenvはファイルをパースするために使用されるので、`export`のようなbashのようなセマンティクスを使用することができます。(お使いのOSや環境によっては)dotenvファイルを`source`でも使用できる場合があります。詳細については、[python-dotenv's documentation](https://saurabh-kumar.com/python-dotenv/#usages)を参照してください。

<!-- Pydantic settings consider `extra` config in case of dotenv file. It means if you set the `extra=forbid` (*default*) on `model_config` and your dotenv file contains an entry for a field that is not defined in settings model, it will raise `ValidationError` in settings construction. -->
Pydanticの設定では、dotenvファイルの場合に`extra`configを考慮します。これは、`model_config`で`extra=forbid`(*default*)を設定し、dotenvファイルに設定モデルで定義されていないフィールドのエントリが含まれている場合、設定の構築で`ValidationError`が発生することを意味します。

<!-- For compatibility with pydantic 1.x BaseSettings you should use `extra=ignore`: -->
pydantic 1.x BaseSettingsとの互換性のために、`extra=ignore`を使用してください。

```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
```


!!! note
    <!-- Pydantic settings loads all the values from dotenv file and passes it to the model, regardless of the model's `env_prefix`.
    So if you provide extra values in a dotenv file, whether they start with `env_prefix` or not, a `ValidationError` will be raised. -->
    Pydantic設定は、モデルの`env_prefix`に関係なく、dotenvファイルからすべての値をロードしてモデルに渡します。
    したがって、dotenvファイルに追加の値を指定すると、それらが`env_prefix`で始まるかどうかにかかわらず、`ValidationError`が発生します。

## Command Line Support

<!-- Pydantic settings provides integrated CLI support, making it easy to quickly define CLI applications using Pydantic models. There are two primary use cases for Pydantic settings CLI: -->
Pydantic設定は統合されたCLIサポートを提供し、Pydanticモデルを使用してCLIアプリケーションを簡単にすばやく定義できるようにします。Pydantic設定CLIの主なユースケースは次の2つです。

<!-- 1. When using a CLI to override fields in Pydantic models.
2. When using Pydantic models to define CLIs. -->
1. CLIを使用してPydanticモデルのフィールドを上書きする場合。
2. Pydanticモデルを使用してCLIを定義する場合。

<!-- By default, the experience is tailored towards use case #1 and builds on the foundations established in [parsing environment variables](#parsing-environment-variable-values). If your use case primarily falls into #2, you will likely want to enable [enforcing required arguments at the CLI](#enforce-required-arguments-at-cli). -->
デフォルトでは、エクスペリエンスはユースケース#1に合わせて調整され、[parsing environment variables](#parsing-environment-variable-values)で確立された基礎の上に構築されます。ユースケースが主に#2に該当する場合は、[enforcing required arguments at the CLI](#enforce-required-arguments-at-cli)を有効にする必要があります。

### The Basics

<!-- To get started, let's revisit the example presented in [parsing environment variables](#parsing-environment-variable-values) but using a Pydantic settings CLI: -->
最初に、[parsing environment variables](#parsing-environment-variable-values)で示した例を、Pydantic設定CLIを使用してもう一度見てみましょう。

```py
import sys

from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepSubModel(BaseModel):
    v4: str


class SubModel(BaseModel):
    v1: str
    v2: bytes
    v3: int
    deep: DeepSubModel


class Settings(BaseSettings):
    model_config = SettingsConfigDict(cli_parse_args=True)

    v0: str
    sub_model: SubModel


sys.argv = [
    'example.py',
    '--v0=0',
    '--sub_model={"v1": "json-1", "v2": "json-2"}',
    '--sub_model.v2=nested-2',
    '--sub_model.v3=3',
    '--sub_model.deep.v4=v4',
]

print(Settings().model_dump())
"""
{
    'v0': '0',
    'sub_model': {'v1': 'json-1', 'v2': b'nested-2', 'v3': 3, 'deep': {'v4': 'v4'}},
}
"""
```

<!-- To enable CLI parsing, we simply set the `cli_parse_args` flag to a valid value, which retains similar connotations as defined in `argparse`. Alternatively, we can also directly provide the args to parse at time of instantiation: -->
CLIでのパースを有効にするには、単に`cli_parse_args`フラグを有効な値に設定します。このフラグは`argparse`で定義されているのと同様の意味を保持します。あるいは、インスタンス化時にパースする引数を直接指定することもできます。

```py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    this_foo: str


print(Settings(_cli_parse_args=['--this_foo', 'is such a foo']).model_dump())
#> {'this_foo': 'is such a foo'}
```

Note that a CLI settings source is [**the topmost source**](#field-value-priority) by default unless its [priority value is customised](#customise-settings-sources):
CLIの設定ソースは、[priority value is customised](#customise-settings-sources)でない限り、デフォルトで[**the topmost source**](#field-value-priority)であることに注意してください。

```py
import os
import sys
from typing import Tuple, Type

from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    PydanticBaseSettingsSource,
)


class Settings(BaseSettings):
    my_foo: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, CliSettingsSource(settings_cls, cli_parse_args=True)


os.environ['MY_FOO'] = 'from environment'

sys.argv = ['example.py', '--my_foo=from cli']

print(Settings().model_dump())
#> {'my_foo': 'from environment'}
```

#### Lists

CLI argument parsing of lists supports intermixing of any of the below three styles:
リストのCLI引数のパースでは、次の3つのスタイルの混在がサポートされています。

  * JSON style `--field='[1,2]'`
  * Argparse style `--field 1 --field 2`
  * Lazy style `--field=1,2`

```py
import sys
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True):
    my_list: List[int]


sys.argv = ['example.py', '--my_list', '[1,2]']
print(Settings().model_dump())
#> {'my_list': [1, 2]}

sys.argv = ['example.py', '--my_list', '1', '--my_list', '2']
print(Settings().model_dump())
#> {'my_list': [1, 2]}

sys.argv = ['example.py', '--my_list', '1,2']
print(Settings().model_dump())
#> {'my_list': [1, 2]}
```

#### Dictionaries

CLI argument parsing of dictionaries supports intermixing of any of the below two styles:
ディクショナリのCLI引数のパースでは、次の2つのスタイルの混在がサポートされています。

  * JSON style `--field='{"k1": 1, "k2": 2}'`
  * Environment variable style `--field k1=1 --field k2=2`

<!-- These can be used in conjunction with list forms as well, e.g: -->
これらは、次のようにリスト形式と組み合わせて使用することもできます。

  * `--field k1=1,k2=2 --field k3=3 --field '{"k4": 4}'` etc.

```py
import sys
from typing import Dict

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True):
    my_dict: Dict[str, int]


sys.argv = ['example.py', '--my_dict', '{"k1":1,"k2":2}']
print(Settings().model_dump())
#> {'my_dict': {'k1': 1, 'k2': 2}}

sys.argv = ['example.py', '--my_dict', 'k1=1', '--my_dict', 'k2=2']
print(Settings().model_dump())
#> {'my_dict': {'k1': 1, 'k2': 2}}
```

#### Literals and Enums

CLI argument parsing of literals and enums are converted into CLI choices.
リテラルおよび列挙型のCLI引数のパースは、CLIでの選択項目に変換されます。

```py
import sys
from enum import IntEnum
from typing import Literal

from pydantic_settings import BaseSettings


class Fruit(IntEnum):
    pear = 0
    kiwi = 1
    lime = 2


class Settings(BaseSettings, cli_parse_args=True):
    fruit: Fruit
    pet: Literal['dog', 'cat', 'bird']


sys.argv = ['example.py', '--fruit', 'lime', '--pet', 'cat']
print(Settings().model_dump())
#> {'fruit': <Fruit.lime: 2>, 'pet': 'cat'}
```

#### Aliases

<!-- Pydantic field aliases are added as CLI argument aliases. Aliases of length one are converted into short options. -->
Pydanticフィールドエイリアスは、CLI引数エイリアスとして追加されます。長さ1のエイリアスは、短いオプションに変換されます。

```py
import sys

from pydantic import AliasChoices, AliasPath, Field

from pydantic_settings import BaseSettings


class User(BaseSettings, cli_parse_args=True):
    first_name: str = Field(
        validation_alias=AliasChoices('f', 'fname', AliasPath('name', 0))
    )
    last_name: str = Field(
        validation_alias=AliasChoices('l', 'lname', AliasPath('name', 1))
    )


sys.argv = ['example.py', '--fname', 'John', '--lname', 'Doe']
print(User().model_dump())
#> {'first_name': 'John', 'last_name': 'Doe'}

sys.argv = ['example.py', '-f', 'John', '-l', 'Doe']
print(User().model_dump())
#> {'first_name': 'John', 'last_name': 'Doe'}

sys.argv = ['example.py', '--name', 'John,Doe']
print(User().model_dump())
#> {'first_name': 'John', 'last_name': 'Doe'}

sys.argv = ['example.py', '--name', 'John', '--lname', 'Doe']
print(User().model_dump())
#> {'first_name': 'John', 'last_name': 'Doe'}
```

### Subcommands and Positional Arguments

<!-- Subcommands and positional arguments are expressed using the `CliSubCommand` and `CliPositionalArg` annotations.
These annotations can only be applied to required fields (i.e. fields that do not have a default value).
Furthermore, subcommands must be a valid type derived from either a pydantic `BaseModel` or pydantic.dataclasses `dataclass`. -->
サブコマンドと位置引数は、`CliSubCommand`および`CliPositionalArg`アノテーションを使用して表現されます。
これらの注釈は必須フィールド(つまり、デフォルト値のないフィールド)にのみ適用できます。
さらに、サブコマンドはpydanic`BaseModel`またはpydanic.dataclasses`dataclass`から派生した有効な型でなければなりません。

!!! note
    <!-- CLI settings subcommands are limited to a single subparser per model. In other words, all subcommands for a model are grouped under a single subparser; it does not allow for multiple subparsers with each subparser having its own set of subcommands. For more information on subparsers, see [argparse subcommands](https://docs.python.org/3/library/argparse.html#sub-commands). -->
    CLI設定サブコマンドは、モデルごとに1つのサブパーサーに制限されています。つまり、モデルのすべてのサブコマンドは1つのサブパーサーにグループ化されます。各サブパーサーが独自のサブコマンドセットを持つ複数のサブパーサーは許可されません。サブパーサーの詳細については、[argparse subcommands](https://docs.python.org/3/library/argparse.html#sub-commands)を参照してください。

!!! note
    <!-- `CliSubCommand` and `CliPositionalArg` are always case sensitive and do not support aliases. -->
    `CliSubCommand`と`CliPositionalArg`は常に大文字と小文字が区別され、エイリアスをサポートしていません。

```py
import sys

from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass

from pydantic_settings import (
    BaseSettings,
    CliPositionalArg,
    CliSubCommand,
)


@dataclass
class FooPlugin:
    """git-plugins-foo - Extra deep foo plugin command"""

    x_feature: bool = Field(default=False, description='Enable "X" feature')


@dataclass
class BarPlugin:
    """git-plugins-bar - Extra deep bar plugin command"""

    y_feature: bool = Field(default=False, description='Enable "Y" feature')


@dataclass
class Plugins:
    """git-plugins - Fake plugins for GIT"""

    foo: CliSubCommand[FooPlugin] = Field(description='Foo is fake plugin')

    bar: CliSubCommand[BarPlugin] = Field(description='Bar is fake plugin')


class Clone(BaseModel):
    """git-clone - Clone a repository into a new directory"""

    repository: CliPositionalArg[str] = Field(description='The repo ...')

    directory: CliPositionalArg[str] = Field(description='The dir ...')

    local: bool = Field(default=False, description='When the repo ...')


class Git(BaseSettings, cli_parse_args=True, cli_prog_name='git'):
    """git - The stupid content tracker"""

    clone: CliSubCommand[Clone] = Field(description='Clone a repo ...')

    plugins: CliSubCommand[Plugins] = Field(description='Fake GIT plugins')


try:
    sys.argv = ['example.py', '--help']
    Git()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: git [-h] {clone,plugins} ...

git - The stupid content tracker

options:
  -h, --help       show this help message and exit

subcommands:
  {clone,plugins}
    clone          Clone a repo ...
    plugins        Fake GIT plugins
"""


try:
    sys.argv = ['example.py', 'clone', '--help']
    Git()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: git clone [-h] [--local bool] [--shared bool] REPOSITORY DIRECTORY

git-clone - Clone a repository into a new directory

positional arguments:
  REPOSITORY    The repo ...
  DIRECTORY     The dir ...

options:
  -h, --help    show this help message and exit
  --local bool  When the repo ... (default: False)
"""


try:
    sys.argv = ['example.py', 'plugins', 'bar', '--help']
    Git()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: git plugins bar [-h] [--my_feature bool]

git-plugins-bar - Extra deep bar plugin command

options:
  -h, --help        show this help message and exit
  --y_feature bool  Enable "Y" feature (default: False)
"""
```

### Customizing the CLI Experience

<!-- The below flags can be used to customise the CLI experience to your needs. -->
次のフラグを使用して、必要に応じてCLIエクスペリエンスをカスタマイズできます。

#### Change the Displayed Program Name

<!-- Change the default program name displayed in the help text usage by setting `cli_prog_name`. By default, it will derive the name of the currently executing program from `sys.argv[0]`, just like argparse. -->
`cli_prog_name`を設定して、ヘルプテキストの使用方法に表示されるデフォルトのプログラム名を変更します。デフォルトでは、argparseと同様に、現在実行中のプログラムの名前を`sys.argv[0]`から取得します。

```py
import sys

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_prog_name='appdantic'):
    pass


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: appdantic [-h]

options:
  -h, --help  show this help message and exit
"""
```

#### Change Whether CLI Should Exit on Error

<!-- Change whether the CLI internal parser will exit on error or raise a `SettingsError` exception by using `cli_exit_on_error`. By default, the CLI internal parser will exit on error. -->
`cli_exit_on_error`を使用して、CLI内部パーサーがエラー時に終了するか、`SettingsError`例外を発生させるかを変更します。デフォルトでは、CLI内部パーサーはエラー時に終了します。

```py
import sys

from pydantic_settings import BaseSettings, SettingsError


class Settings(BaseSettings, cli_parse_args=True, cli_exit_on_error=False): ...


try:
    sys.argv = ['example.py', '--bad-arg']
    Settings()
except SettingsError as e:
    print(e)
    #> error parsing CLI: unrecognized arguments: --bad-arg
```

#### Enforce Required Arguments at CLI

<!-- Pydantic settings is designed to pull values in from various sources when instantiating a model.
This means a field that is required is not strictly required from any single source (e.g. the CLI).
Instead, all that matters is that one of the sources provides the required value. -->
Pydantic設定は、モデルをインスタンス化するときにさまざまなソースから値を取得するように設計されている。
つまり、必須フィールドは、単一のソース(CLIなど)からは厳密に必須ではありません。
代わりに重要なのは、ソースの1つが必要な値を提供することだけです。

<!-- However, if your use case [aligns more with #2](#command-line-support), using Pydantic models to define CLIs, you will likely want required fields to be _strictly required at the CLI_. We can enable this behavior by using `cli_enforce_required`. -->
しかし、Pydanticモデルを使用してCLIを定義するユースケース[#2](#command-line-support)では、必須フィールドをCLIで厳密に必須にする必要があります。この動作を有効にするには、`cli_enforce_required`を使用します。

```py
import os
import sys

from pydantic import Field

from pydantic_settings import BaseSettings, SettingsError


class Settings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_exit_on_error=False,
):
    my_required_field: str = Field(description='a top level required field')


os.environ['MY_REQUIRED_FIELD'] = 'hello from environment'

try:
    sys.argv = ['example.py']
    Settings()
except SettingsError as e:
    print(e)
    #> error parsing CLI: the following arguments are required: --my_required_field
```

#### Change the None Type Parse String

<!-- Change the CLI string value that will be parsed (e.g. "null", "void", "None", etc.) into `None` by setting `cli_parse_none_str`. By default it will use the `env_parse_none_str` value if set. Otherwise, it will default to "null" if `cli_avoid_json` is `False`, and "None" if `cli_avoid_json` is `True`. -->
解析されるCLI文字列値("null"、"void"、"None"など)を`None`に変更するには、`cli_parse_none_str`を設定します。デフォルトでは、設定されている場合は`env_parse_none_str`値が使用されます。設定されていない場合は、`cli_avoid_json`が`False`の場合はデフォルトで"null"になり、`cli_avoid_json`が`True`の場合はデフォルトで"None"になります。

```py
import sys
from typing import Optional

from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_parse_none_str='void'):
    v1: Optional[int] = Field(description='the top level v0 option')


sys.argv = ['example.py', '--v1', 'void']
print(Settings().model_dump())
#> {'v1': None}
```

#### Hide None Type Values

<!-- Hide `None` values from the CLI help text by enabling `cli_hide_none_type`. -->
`cli_hide_none_type`を有効にして、CLIヘルプテキストから`None`値を非表示にします。

```py
import sys
from typing import Optional

from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_hide_none_type=True):
    v0: Optional[str] = Field(description='the top level v0 option')


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h] [--v0 str]

options:
  -h, --help  show this help message and exit
  --v0 str    the top level v0 option (required)
"""
```

#### Avoid Adding JSON CLI Options

<!-- Avoid adding complex fields that result in JSON strings at the CLI by enabling `cli_avoid_json`. -->
`cli_avoid_json`を有効にして、CLIでJSON文字列になる複雑なフィールドを追加しないようにします。

```py
import sys

from pydantic import BaseModel, Field

from pydantic_settings import BaseSettings


class SubModel(BaseModel):
    v1: int = Field(description='the sub model v1 option')


class Settings(BaseSettings, cli_parse_args=True, cli_avoid_json=True):
    sub_model: SubModel = Field(
        description='The help summary for SubModel related options'
    )


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h] [--sub_model.v1 int]

options:
  -h, --help          show this help message and exit

sub_model options:
  The help summary for SubModel related options

  --sub_model.v1 int  the sub model v1 option (required)
"""
```

#### Use Class Docstring for Group Help Text

<!-- By default, when populating the group help text for nested models it will pull from the field descriptions.
Alternatively, we can also configure CLI settings to pull from the class docstring instead. -->
デフォルトでは、ネストされたモデルのグループヘルプテキストを設定すると、フィールドの説明から取得されます。
代わりに、クラスdocstringからプルするようにCLI設定を構成することもできます。

!!! note
    <!-- If the field is a union of nested models the group help text will always be pulled from the field description; even if `cli_use_class_docs_for_groups` is set to `True`. -->
    フィールドがネストされたモデルの結合である場合、`cli_use_class_docs_for_groups`が`True`に設定されていても、グループのヘルプテキストは常にフィールドの説明から取得されます。

```py
import sys

from pydantic import BaseModel, Field

from pydantic_settings import BaseSettings


class SubModel(BaseModel):
    """The help text from the class docstring."""

    v1: int = Field(description='the sub model v1 option')


class Settings(BaseSettings, cli_parse_args=True, cli_use_class_docs_for_groups=True):
    """My application help text."""

    sub_model: SubModel = Field(description='The help text from the field description')


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h] [--sub_model JSON] [--sub_model.v1 int]

My application help text.

options:
  -h, --help          show this help message and exit

sub_model options:
  The help text from the class docstring.

  --sub_model JSON    set sub_model from JSON string
  --sub_model.v1 int  the sub model v1 option (required)
"""
```

### Integrating with Existing Parsers

<!-- A CLI settings source can be integrated with existing parsers by overriding the default CLI settings source with a user defined one that specifies the `root_parser` object. -->
CLI設定ソースは、デフォルトのCLI設定ソースを`root_parser`オブジェクトを指定するユーザ定義の設定ソースで上書きすることで、既存のパーサと統合できます。

```py
import sys
from argparse import ArgumentParser

from pydantic_settings import BaseSettings, CliSettingsSource

parser = ArgumentParser()
parser.add_argument('--food', choices=['pear', 'kiwi', 'lime'])


class Settings(BaseSettings):
    name: str = 'Bob'


# Set existing `parser` as the `root_parser` object for the user defined settings source
cli_settings = CliSettingsSource(Settings, root_parser=parser)

# Parse and load CLI settings from the command line into the settings source.
sys.argv = ['example.py', '--food', 'kiwi', '--name', 'waldo']
print(Settings(_cli_settings_source=cli_settings(args=True)).model_dump())
#> {'name': 'waldo'}

# Load CLI settings from pre-parsed arguments. i.e., the parsing occurs elsewhere and we
# just need to load the pre-parsed args into the settings source.
parsed_args = parser.parse_args(['--food', 'kiwi', '--name', 'ralph'])
print(Settings(_cli_settings_source=cli_settings(parsed_args=parsed_args)).model_dump())
#> {'name': 'ralph'}
```

<!-- A `CliSettingsSource` connects with a `root_parser` object by using parser methods to add `settings_cls` fields as command line arguments.
The `CliSettingsSource` internal parser representation is based on the `argparse` library, and therefore, requires parser methods that support the same attributes as their `argparse` counterparts.
The available parser methods that can be customised, along with their argparse counterparts (the defaults), are listed below: -->
`CliSettingsSource`は、パーサメソッドを使用して`settings_cls`フィールドをコマンドライン引数として追加することにより、`root_parser`オブジェクトと接続します。
`CliSettingsSource`内部パーサー表現は`argparse`ライブラリに基づいているので、対応する`argparse`と同じ属性をサポートするパーサーメソッドが必要です。
カスタマイズできる使用可能なパーサーメソッドと、対応するargparse(デフォルト)を次に示します。

* `parse_args_method` - (`argparse.ArgumentParser.parse_args`)
* `add_argument_method` - (`argparse.ArgumentParser.add_argument`)
* `add_argument_group_method` - (`argparse.ArgumentParser.add_argument_group`)
* `add_parser_method` - (`argparse._SubParsersAction.add_parser`)
* `add_subparsers_method` - (`argparse.ArgumentParser.add_subparsers`)
* `formatter_class` - (`argparse.HelpFormatter`)

<!-- For a non-argparse parser the parser methods can be set to `None` if not supported. The CLI settings will only raise an error when connecting to the root parser if a parser method is necessary but set to `None`. -->
非argparseパーサの場合、サポートされていなければパーサメソッドを`None`に設定することができます。CLI設定では、パーサメソッドが必要であるが`None`に設定されている場合にのみ、ルートパーサに接続するときにエラーが発生します。

## Secrets

<!-- Placing secret values in files is a common pattern to provide sensitive configuration to an application. -->
ファイルに秘密の値を設定することは、アプリケーションに機密性の高い設定を提供するための一般的なパターンです。

<!-- A secret file follows the same principal as a dotenv file except it only contains a single value and the file name is used as the key. A secret file will look like the following: -->
シークレット・ファイルは、1つの値のみを含み、ファイル名がキーとして使用されることを除いて、dotenvファイルと同じプリンシパルに従います。シークレット・ファイルは次のようになります。

``` title="/var/run/database_password"
super_secret_database_password
```

<!-- Once you have your secret files, *pydantic* supports loading it in two ways: -->
シークレットファイルを取得すると、*pydantic*は次の2つの方法でそのファイルのロードをサポートします。

<!-- 1. Setting the `secrets_dir` on `model_config` in a `BaseSettings` class to the directory where your secret files are stored. -->
1. `BaseSettings`クラスの`model_config`の`secrets_dir`を、シークレットファイルが保存されているディレクトリに設定します。

   ````py hl_lines="4 5 6 7"
   from pydantic_settings import BaseSettings, SettingsConfigDict


   class Settings(BaseSettings):
       model_config = SettingsConfigDict(secrets_dir='/var/run')

       database_password: str
   ````
<!-- 2. Instantiating the `BaseSettings` derived class with the `_secrets_dir` keyword argument: -->
2. `_secrets_dir`キーワード引数を使用して`BaseSettings`派生クラスのインスタンス化:
   ````
   settings = Settings(_secrets_dir='/var/run')
   ````

<!-- In either case, the value of the passed argument can be any valid directory, either absolute or relative to the current working directory. **Note that a non existent directory will only generate a warning**.
From there, *pydantic* will handle everything for you by loading in your variables and validating them. -->
どちらの場合も、渡される引数の値は、任意の有効なディレクトリ(絶対ディレクトリまたは現在の作業ディレクトリに対する相対ディレクトリ)にすることができます。**存在しないディレクトリは警告を生成するだけであることに注意してください**。
そこから、*pydantic*は変数をロードして検証することで、すべてを処理します。

<!-- Even when using a secrets directory, *pydantic* will still read environment variables from a dotenv file or the environment,**a dotenv file and environment variables will always take priority over values loaded from the secrets directory**. -->
secretsディレクトリを使用する場合でも、*pydantic*はdotenvファイルまたは環境から環境変数を読み込みます。**dotenvファイルと環境変数は、secretsディレクトリからロードされた値よりも常に優先されます**。

<!-- Passing a file path via the `_secrets_dir` keyword argument on instantiation (method 2) will override the value (if any) set on the `model_config` class. -->
インスタンス化(メソッド2)で`_secrets_dir`キーワード引数を介してファイルパスを渡すと、`model_config`クラスに設定された値(もしあれば)が上書きされます。

### Use Case: Docker Secrets

<!-- Docker Secrets can be used to provide sensitive configuration to an application running in a Docker container.
To use these secrets in a *pydantic* application the process is simple. More information regarding creating, managing and using secrets in Docker see the official [Docker documentation](https://docs.docker.com/engine/reference/commandline/secret/). -->
Docker Secretsは、Dockerコンテナで実行されているアプリケーションに機密性の高い設定を提供するために使用できる。
これらのシークレットを*pydantic*アプリケーションで使用するプロセスは簡単です。Dockerでのシークレットの作成、管理、使用に関する詳細は、公式の[Docker documentation](https://docs.docker.com/engine/reference/commandline/secret/)を参照してください。

<!-- First, define your `Settings` class with a `SettingsConfigDict` that specifies the secrets directory. -->
まず、secretsディレクトリを指定する`SettingsConfigDict`で`Settings`クラスを定義します。

```py hl_lines="4 5 6 7"
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(secrets_dir='/run/secrets')

    my_secret_data: str
```

!!! note
    <!-- By default [Docker uses `/run/secrets`](https://docs.docker.com/engine/swarm/secrets/#how-docker-manages-secrets) as the target mount point. If you want to use a different location, change `Config.secrets_dir` accordingly. -->
    デフォルトでは、[Dockerは`/run/secrets`](https://docs.docker.com/engine/swarm/secrets/#how-docker-manages-secrets)をターゲットマウントポイントとして使用します。別の場所を使用したい場合は、それに応じて`Config.secrets_dir`を変更してください。

<!-- Then, create your secret via the Docker CLI -->
次に、Docker CLIを使用してシークレットを作成します。
```bash
printf "This is a secret" | docker secret create my_secret_data -
```

<!-- Last, run your application inside a Docker container and supply your newly created secret -->
最後に、Dockerコンテナ内でアプリケーションを実行し、新しく作成したシークレットを指定します。
```bash
docker service create --name pydantic-with-secrets --secret my_secret_data pydantic-app:latest
```

## Azure Key Vault

<!-- You must set two parameters: -->
次の2つのパラメータを設定する必要があります。

<!-- - `url`: For example, `https://my-resource.vault.azure.net/`.
- `credential`: If you use `DefaultAzureCredential`, in local you can execute `az login` to get your identity credentials. The identity must have a role assignment (the recommended one is `Key Vault Secrets User`), so you can access the secrets. -->
- `url`:例えば`https://my-resource.vault.azure.net/`です。
- `credential`:`DefaultAzureCredential`を使用する場合は、ローカルで`az login`を実行してIDクレデンシャルを取得できます。シークレットにアクセスできるように、IDにロールが割り当てられている必要があります(推奨されるのは`Key Vault Secrets User`です)。

<!-- You must have the same naming convention in the field name as in the Key Vault secret name. For example, if the secret is named `SqlServerPassword`, the field name must be the same. You can use an alias too. -->
フィールド名には、キー・ヴォールト・シークレット名と同じ命名規則を使用する必要があります。たとえば、シークレットの名前が`SqlServerPassword`の場合、フィールド名は同じである必要があります。別名も使用できます。

<!-- In Key Vault, nested models are supported with the `--` separator. For example, `SqlServer--Password`. -->
Key Vaultでは、ネストされたモデルは`--`セパレータでサポートされます。たとえば、`SqlServer--Password`のようになります。

<!-- Key Vault arrays (e.g. `MySecret--0`, `MySecret--1`) are not supported. -->
Key Vault配列(例えば`MySecret--0`、`MySecret--1`)はサポートされていません。

```py
import os
from typing import Tuple, Type

from azure.identity import DefaultAzureCredential
from pydantic import BaseModel

from pydantic_settings import (
    AzureKeyVaultSettingsSource,
    BaseSettings,
    PydanticBaseSettingsSource,
)


class SubModel(BaseModel):
    a: str


class AzureKeyVaultSettings(BaseSettings):
    foo: str
    bar: int
    sub: SubModel

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        az_key_vault_settings = AzureKeyVaultSettingsSource(
            settings_cls,
            os.environ['AZURE_KEY_VAULT_URL'],
            DefaultAzureCredential(),
        )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            az_key_vault_settings,
        )
```

## Other settings source

<!-- Other settings sources are available for common configuration files: -->
その他の設定ソースは、一般的な設定ファイルに使用できます。

<!-- - `JsonConfigSettingsSource` using `json_file` and `json_file_encoding` arguments
- `PyprojectTomlConfigSettingsSource` using *(optional)* `pyproject_toml_depth` and *(optional)* `pyproject_toml_table_header` arguments
- `TomlConfigSettingsSource` using `toml_file` argument
- `YamlConfigSettingsSource` using `yaml_file` and yaml_file_encoding arguments -->
- `json_file`および`json_file_encoding`引数を使用した`JsonConfigSettingsSource`
- *(オプション)*`pyproject_toml_depth`および*(オプション)*`pyproject_toml_table_header`引数を使用した`PyprojectTomlConfigSettingsSource`
- `toml_file`引数を使用した`TomlConfigSettingsSource`
- `yaml_file`およびyaml_file_encoding引数を使用した`YamlConfigSettingsSource`

<!-- You can also provide multiple files by providing a list of path: -->
パスのリストを指定して、複数のファイルを指定することもできます。
```py
toml_file = ['config.default.toml', 'config.custom.toml']
```
<!-- To use them, you can use the same mechanism described [here](#customise-settings-sources) -->
これらを使用するには、[ここ](#customise-settings-sources)で説明したのと同じメカニズムを使用できます。

```py
from typing import Tuple, Type

from pydantic import BaseModel

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class Nested(BaseModel):
    nested_field: str


class Settings(BaseSettings):
    foobar: str
    nested: Nested
    model_config = SettingsConfigDict(toml_file='config.toml')

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)
```

<!-- This will be able to read the following "config.toml" file, located in your working directory: -->
これにより、ワーキングディレクトリにある次の"config.toml"ファイルを読み込むことができます。

```toml
foobar = "Hello"
[nested]
nested_field = "world!"
```

### pyproject.toml

<!-- "pyproject.toml" is a standardized file for providing configuration values in Python projects. [PEP 518](https://peps.python.org/pep-0518/#tool-table) defines a `[tool]` table that can be used to provide arbitrary tool configuration.
While encouraged to use the `[tool]` table, `PyprojectTomlConfigSettingsSource` can be used to load variables from any location with in "pyproject.toml" file. -->
"pyproject.toml"は、Pythonプロジェクトで構成値を提供するための標準化されたファイルです。[PEP 518](https://peps.python.org/pep-0518/#tool-table)では、任意のツール構成を提供するために使用できる`[tool]`テーブルが定義されています。
`[tool]`テーブルを使用することをお勧めしますが、`PyprojectTomlConfigSettingsSource`は"pyproject.toml"ファイル内の任意の場所から変数をロードするために使用できます。

<!-- This is controlled by providing `SettingsConfigDict(pyproject_toml_table_header=tuple[str, ...])` where the value is a tuple of header parts.
By default, `pyproject_toml_table_header=('tool', 'pydantic-settings')` which will load variables from the `[tool.pydantic-settings]` table. -->
これは`SettingsConfigDict(pyproject_toml_table_header=tuple[str, .])`を提供することで制御されます。ここで、値はヘッダー部分のタプルです。
デフォルトでは`pyproject_toml_table_header=('tool','pydantic-settings')`で、`[tool.pydantic-settings]`テーブルから変数をロードします。

```python
from typing import Tuple, Type

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    """Example loading values from the table used by default."""

    field: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (PyprojectTomlConfigSettingsSource(settings_cls),)


class SomeTableSettings(Settings):
    """Example loading values from a user defined table."""

    model_config = SettingsConfigDict(
        pyproject_toml_table_header=('tool', 'some-table')
    )


class RootSettings(Settings):
    """Example loading values from the root of a pyproject.toml file."""

    model_config = SettingsConfigDict(extra='ignore', pyproject_toml_table_header=())
```

<!-- This will be able to read the following "pyproject.toml" file, located in your working directory, resulting in `Settings(field='default-table')`, `SomeTableSettings(field='some-table')`, & `RootSettings(field='root')`: -->
これは、作業ディレクトリにある以下の"pyproject.toml"ファイルを読み込むことができ、結果は`Settings(field='default-table')`、`SomeTableSettings(field='some-table')`、`RootSettings(field='root')`になります。

```toml
field = "root"

[tool.pydantic-settings]
field = "default-table"

[tool.some-table]
field = "some-table"
```

<!-- By default, `PyprojectTomlConfigSettingsSource` will only look for a "pyproject.toml" in the your current working directory.
However, there are two options to change this behavior. -->
デフォルトでは、`PyprojectTomlConfigSettingsSource`は現在の作業ディレクトリ内の"pyproject.toml"のみを検索します。
ただし、この動作を変更するには2つのオプションがあります。

<!-- * `SettingsConfigDict(pyproject_toml_depth=<int>)` can be provided to check `<int>` number of directories **up** in the directory tree for a "pyproject.toml" if one is not found in the current working directory. By default, no parent directories are checked.
* An explicit file path can be provided to the source when it is instantiated (e.g. `PyprojectTomlConfigSettingsSource(settings_cls, Path('~/.config').resolve() / 'pyproject.toml')`). If a file path is provided this way, it will be treated as absolute (no other locations are checked). -->
* `SettingsConfigDict(pyproject_toml_depth=<int>)`を提供して、"pyproject.toml"が現在の作業ディレクトリに見つからない場合に、ディレクトリツリー内のディレクトリ数**up**をチェックすることができます。デフォルトでは、親ディレクトリはチェックされません。
* ソースがインスタンス化されるときに、明示的なファイルパスをソースに提供することができます(例:`PyprojectTomlConfigSettingsSource(settings_cls, Path('~/.config').resolve()/'pyproject.toml')`)。ファイルパスがこのように提供される場合、絶対パスとして扱われます(他の場所はチェックされません)。

```python
from pathlib import Path
from typing import Tuple, Type

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)


class DiscoverSettings(BaseSettings):
    """Example of discovering a pyproject.toml in parent directories in not in `Path.cwd()`."""

    model_config = SettingsConfigDict(pyproject_toml_depth=2)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (PyprojectTomlConfigSettingsSource(settings_cls),)


class ExplicitFilePathSettings(BaseSettings):
    """Example of explicitly providing the path to the file to load."""

    field: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            PyprojectTomlConfigSettingsSource(
                settings_cls, Path('~/.config').resolve() / 'pyproject.toml'
            ),
        )
```

## Field value priority

<!-- In the case where a value is specified for the same `Settings` field in multiple ways, the selected value is determined as follows (in descending order of priority): -->
同じ"設定"フィールドに複数の方法で値が指定されている場合、選択された値は次のように決定されます(優先順位の高い順に)。

<!-- 1. If `cli_parse_args` is enabled, arguments passed in at the CLI.
2. Arguments passed to the `Settings` class initialiser.
3. Environment variables, e.g. `my_prefix_special_function` as described above.
4. Variables loaded from a dotenv (`.env`) file.
5. Variables loaded from the secrets directory.
6. The default field values for the `Settings` model. -->
1. `cli_parse_args`が有効な場合、CLIに渡される引数
2. `Settings`クラスのイニシャライザに渡される引数
3. 環境変数。例えば、上で説明した`my_prefix_special_function`
4. dotenv(`.env`)ファイルからロードされた変数
5. secretsディレクトリからロードされた変数
6. `Settings`モデルのデフォルトのフィールド値

## Customise settings sources

<!-- If the default order of priority doesn't match your needs, it's possible to change it by overriding the `settings_customise_sources` method of your `Settings` . -->
デフォルトの優先順位があなたのニーズに合わない場合は、`Settings`の`settings_customise_sources`メソッドをオーバーライドすることで変更できます。

<!-- `settings_customise_sources` takes four callables as arguments and returns any number of callables as a tuple.
In turn these callables are called to build the inputs to the fields of the settings class. -->
`settings_customise_sources`は引数として4つのcallableを取り、任意の数のcallableをタプルとして返します。
次に、これらの呼び出し可能オブジェクトが呼び出されて、settingsクラスのフィールドへの入力が作成されます。

<!-- Each callable should take an instance of the settings class as its sole argument and return a `dict`. -->
各呼び出し可能オブジェクトは、設定クラスのインスタンスを唯一の引数として取り、`dict`を返します。

### Changing Priority

<!-- The order of the returned callables decides the priority of inputs; first item is the highest priority. -->
返される呼び出し可能オブジェクトの順序によって、入力の優先順位が決まります。最初の項目が最も高い優先順位になります。

```py
from typing import Tuple, Type

from pydantic import PostgresDsn

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


class Settings(BaseSettings):
    database_dsn: PostgresDsn

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, init_settings, file_secret_settings


print(Settings(database_dsn='postgres://postgres@localhost:5432/kwargs_db'))
#> database_dsn=MultiHostUrl('postgres://postgres@localhost:5432/kwargs_db')
```

<!-- By flipping `env_settings` and `init_settings`, environment variables now have precedence over `__init__` kwargs. -->
`env_settings`と`init_settings`を反転することで、環境変数が`__init__`kwargsよりも優先されるようになりました。

### Adding sources

<!-- As explained earlier, *pydantic* ships with multiples built-in settings sources. However, you may occasionally need to add your own custom sources, `settings_customise_sources` makes this very easy: -->
すでに説明したように、*pydantic*には複数の設定ソースが組み込まれています。ただし、独自のカスタムソースを追加する必要がある場合もあります。`settings_customise_sources`を使用すると、これを非常に簡単に行うことができます。

```py
import json
from pathlib import Path
from typing import Any, Dict, Tuple, Type

from pydantic.fields import FieldInfo

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class JsonConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A simple settings source class that loads variables from a JSON file
    at the project's root.

    Here we happen to choose to use the `env_file_encoding` from Config
    when reading `config.json`
    """

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> Tuple[Any, str, bool]:
        encoding = self.config.get('env_file_encoding')
        file_content_json = json.loads(
            Path('tests/example_test_config.json').read_text(encoding)
        )
        field_value = file_content_json.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field, field_name
            )
            field_value = self.prepare_field_value(
                field_name, field, field_value, value_is_complex
            )
            if field_value is not None:
                d[field_key] = field_value

        return d


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file_encoding='utf-8')

    foobar: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            JsonConfigSettingsSource(settings_cls),
            env_settings,
            file_secret_settings,
        )


print(Settings())
#> foobar='test'
```

#### Accessing the result of previous sources

<!-- Each source of settings can access the output of the previous ones. -->
設定の各ソースは、前の設定の出力にアクセスできます。

```python
from typing import Any, Dict, Tuple

from pydantic.fields import FieldInfo

from pydantic_settings import PydanticBaseSettingsSource


class MyCustomSource(PydanticBaseSettingsSource):
    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> Tuple[Any, str, bool]: ...

    def __call__(self) -> Dict[str, Any]:
        # Retrieve the aggregated settings from previous sources
        current_state = self.current_state
        current_state.get('some_setting')

        # Retrieve settings from all sources individually
        # self.settings_sources_data["SettingsSourceName"]: Dict[str, Any]
        settings_sources_data = self.settings_sources_data
        settings_sources_data['SomeSettingsSource'].get('some_setting')

        # Your code here...
```

### Removing sources

<!-- You might also want to disable a source: -->
また、ソースを無効にすることもできます。

```py
from typing import Tuple, Type

from pydantic import ValidationError

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


class Settings(BaseSettings):
    my_api_key: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        # here we choose to ignore arguments from init_settings
        return env_settings, file_secret_settings


try:
    Settings(my_api_key='this is ignored')
except ValidationError as exc_info:
    print(exc_info)
    """
    1 validation error for Settings
    my_api_key
      Field required [type=missing, input_value={}, input_type=dict]
        For further information visit https://errors.pydantic.dev/2/v/missing
    """
```


## In-place reloading

<!-- In case you want to reload in-place an existing setting, you can do it by using its `__init__` method : -->
既存の設定をインプレイスで再ロードしたい場合は、`__init__`メソッドを使って行うことができます。

```py
import os

from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    foo: str = Field('foo')


mutable_settings = Settings()

print(mutable_settings.foo)
#> foo

os.environ['foo'] = 'bar'
print(mutable_settings.foo)
#> foo

mutable_settings.__init__()
print(mutable_settings.foo)
#> bar

os.environ.pop('foo')
mutable_settings.__init__()
print(mutable_settings.foo)
#> foo
```
