"""ネットワークモジュールには、一般的なネットワーク関連フィールドのタイプが含まれています。"""

from __future__ import annotations as _annotations

import dataclasses as _dataclasses
import re
from importlib.metadata import version
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import TYPE_CHECKING, Any

from pydantic_core import MultiHostUrl, PydanticCustomError, Url, core_schema
from typing_extensions import Annotated, Self, TypeAlias

from ._internal import _fields, _repr, _schema_generation_shared
from ._migration import getattr_migration
from .annotated_handlers import GetCoreSchemaHandler
from .json_schema import JsonSchemaValue

if TYPE_CHECKING:
    import email_validator

    NetworkType: TypeAlias = 'str | bytes | int | tuple[str | bytes | int, str | int]'

else:
    email_validator = None


__all__ = [
    'AnyUrl',
    'AnyHttpUrl',
    'FileUrl',
    'FtpUrl',
    'HttpUrl',
    'WebsocketUrl',
    'AnyWebsocketUrl',
    'UrlConstraints',
    'EmailStr',
    'NameEmail',
    'IPvAnyAddress',
    'IPvAnyInterface',
    'IPvAnyNetwork',
    'PostgresDsn',
    'CockroachDsn',
    'AmqpDsn',
    'RedisDsn',
    'MongoDsn',
    'KafkaDsn',
    'NatsDsn',
    'validate_email',
    'MySQLDsn',
    'MariaDBDsn',
    'ClickHouseDsn',
]


@_dataclasses.dataclass
class UrlConstraints(_fields.PydanticMetadata):
    """URLの制約。

    Attributes:
        max_length: URLの最大長。デフォルトは`None`です。
        allowed_schemes: 許可されたスキーマ。デフォルトは`None`です。
        host_required: ホストが必要です。かどうか。デフォルトは`None`です。
        default_host: デフォルトのホスト。デフォルトは`None`です。
        default_port: デフォルトのポート。デフォルトは`None`です。
        default_path: デフォルトのパス。デフォルトは`None`です。
    """

    max_length: int | None = None
    allowed_schemes: list[str] | None = None
    host_required: bool | None = None
    default_host: str | None = None
    default_port: int | None = None
    default_path: str | None = None

    def __hash__(self) -> int:
        return hash(
            (
                self.max_length,
                tuple(self.allowed_schemes) if self.allowed_schemes is not None else None,
                self.host_required,
                self.default_host,
                self.default_port,
                self.default_path,
            )
        )


AnyUrl = Url
"""すべてのURLの基本タイプ。

* 任意のスキームを使用可能です。
* トップレベルドメイン(TLD)は不要です。
* ホストは必要です。

入力URLが`http://samuel:pass@example.com:8000/the/path/?query=here#fragment=is;this=bit`の場合、型は次のプロパティをエクスポートします。

-`scheme`: URLスキーム(`http`)が常に設定されます。
-`host`: URLホスト(`example.com`)で、常に設定されます。
-`username`: オプションのユーザ名(`samuel`)がある場合。
-`password`: オプションのパスワード(`pass`)がある場合。
-`port`: オプションのポート(`8000`)です。
-`path`: オプションのパス(`/the/path/`)。
-`query`: オプションのURLクエリ(例えば`GET`引数や`query=here`のような"search string")。
-`fragment`: オプションのfragment(`fragment=is;this=bit`)。
"""
AnyHttpUrl = Annotated[Url, UrlConstraints(allowed_schemes=['http', 'https'])]
"""任意のhttpまたはhttps URLを受け入れるタイプ。

* TLDは不要です。
* ホストが必要です。
"""
HttpUrl = Annotated[Url, UrlConstraints(max_length=2083, allowed_schemes=['http', 'https'])]
"""任意のhttpまたはhttps URLを受け入れるタイプ。

* TLDは不要です。
* ホストが必要です。
* 最大長2083です。

```py
from pydantic import BaseModel, HttpUrl, ValidationError

class MyModel(BaseModel):
    url: HttpUrl

m = MyModel(url='http://www.example.com')  # (1)!
print(m.url)
#> http://www.example.com/

try:
    MyModel(url='ftp://invalid.url')
except ValidationError as e:
    print(e)
    '''
    1 validation error for MyModel
    url
      URL scheme should be 'http' or 'https' [type=url_scheme, input_value='ftp://invalid.url', input_type=str]
    '''

try:
    MyModel(url='not a url')
except ValidationError as e:
    print(e)
    '''
    1 validation error for MyModel
    url
      Input should be a valid URL, relative URL without a base [type=url_parsing, input_value='not a url', input_type=str]
    '''
```

1. 注意:mypyは`m=MyModel(url=HttpUrl('http://www.example.com'))`を好みますが、いずれにせよPydanticは文字列をHttpUrlインスタンスに変換します。

「International domains」(たとえば、ホストまたはTLDに非ASCII文字が含まれるURL)は、[punycode](https://en.wikipedia.org/wiki/Punycode)によってエンコードされます(これが重要である理由の適切な説明については、[this article](https://www.xudongz.com/blog/2017/idn-phishing/)を参照してください)。

```py
from pydantic import BaseModel, HttpUrl

class MyModel(BaseModel):
    url: HttpUrl

m1 = MyModel(url='http://puny£code.com')
print(m1.url)
#> http://xn--punycode-eja.com/
m2 = MyModel(url='https://www.аррӏе.com/')
print(m2.url)
#> https://www.xn--80ak6aa92e.com/
m3 = MyModel(url='https://www.example.珠宝/')
print(m3.url)
#> https://www.example.xn--pbt977c/
```


!!! warning "Underscores in Hostnames"
    Pydanticでは、TLDを除くドメインのすべての部分でアンダースコアを使用できます。
    技術的には、これは間違っている可能性があります。理論的には、ホスト名にアンダースコアを付けることはできませんが、サブドメインにはアンダースコアを付けることができます。

    これを説明するために、次の2つのケースを考えてみましょう。

    - `exam_ple.co.uk`:ホスト名は`exam_ple`ですが、アンダースコアが含まれているため許可されません。
    - `foo_bar.example.com`ホスト名は`example`です。アンダースコアはサブドメインにあるので、これは許可されるべきです。

    TLDの網羅的なリストがなければ、これら2つを区別することは不可能であろう。したがって、アンダースコアは使用できますが、必要に応じていつでもバリデータでさらに検証を行うことができます。

    また、Chrome、Firefox、Safariは現在、URLとして`http://exam_ple.com`を受け入れているので、私たちは良い(あるいは少なくとも大きな)会社にいます。
"""
AnyWebsocketUrl = Annotated[Url, UrlConstraints(allowed_schemes=['ws', 'wss'])]
"""任意のwsまたはwss URLを受け入れるタイプ。

* TLDは不要です。
* ホストが必要です。
"""
WebsocketUrl = Annotated[Url, UrlConstraints(max_length=2083, allowed_schemes=['ws', 'wss'])]
"""任意のwsまたはwss URLを受け入れるタイプ。

* TLDは不要です。
* ホストが必要です。
* 最大長2083です。
"""
FileUrl = Annotated[Url, UrlConstraints(allowed_schemes=['file'])]
"""任意のファイルURLを受け入れるタイプ。

* ホストは不要です。
"""
FtpUrl = Annotated[Url, UrlConstraints(allowed_schemes=['ftp'])]
"""ftp URLを受け入れるタイプ。

* TLDは不要です。
* ホストが必要です。
"""
PostgresDsn = Annotated[
    MultiHostUrl,
    UrlConstraints(
        host_required=True,
        allowed_schemes=[
            'postgres',
            'postgresql',
            'postgresql+asyncpg',
            'postgresql+pg8000',
            'postgresql+psycopg',
            'postgresql+psycopg2',
            'postgresql+psycopg2cffi',
            'postgresql+py-postgresql',
            'postgresql+pygresql',
        ],
    ),
]
"""任意のPostgres DSNを受け入れるタイプ。

* ユーザー情報が必要です。
* TLDは不要です。
* ホストが必要です。
* 複数のホストをサポート

さらに検証が必要な場合は、これらのプロパティをバリデータで使用して、特定の動作を強制できます。

```py
from pydantic import (
    BaseModel,
    HttpUrl,
    PostgresDsn,
    ValidationError,
    field_validator,
)

class MyModel(BaseModel):
    url: HttpUrl

m = MyModel(url='http://www.example.com')

# the repr() method for a url will display all properties of the url
print(repr(m.url))
#> Url('http://www.example.com/')
print(m.url.scheme)
#> http
print(m.url.host)
#> www.example.com
print(m.url.port)
#> 80

class MyDatabaseModel(BaseModel):
    db: PostgresDsn

    @field_validator('db')
    def check_db_name(cls, v):
        assert v.path and len(v.path) > 1, 'database must be provided'
        return v

m = MyDatabaseModel(db='postgres://user:pass@localhost:5432/foobar')
print(m.db)
#> postgres://user:pass@localhost:5432/foobar

try:
    MyDatabaseModel(db='postgres://user:pass@localhost:5432')
except ValidationError as e:
    print(e)
    '''
    1 validation error for MyDatabaseModel
    db
      Assertion failed, database must be provided
    assert (None)
     +  where None = MultiHostUrl('postgres://user:pass@localhost:5432').path [type=assertion_error, input_value='postgres://user:pass@localhost:5432', input_type=str]
    '''
```
"""

CockroachDsn = Annotated[
    Url,
    UrlConstraints(
        host_required=True,
        allowed_schemes=[
            'cockroachdb',
            'cockroachdb+psycopg2',
            'cockroachdb+asyncpg',
        ],
    ),
]
"""任意のCockroach DSNを受け入れるタイプ。

* ユーザー情報が必要です。
* TLDは不要です。
* ホストが必要です。
"""
AmqpDsn = Annotated[Url, UrlConstraints(allowed_schemes=['amqp', 'amqps'])]
"""任意のAMQP DSNを受け入れるタイプ。

* ユーザー情報が必要です。
* TLDは不要です。
* ホストが必要です。
"""
RedisDsn = Annotated[
    Url,
    UrlConstraints(allowed_schemes=['redis', 'rediss'], default_host='localhost', default_port=6379, default_path='/0'),
]
"""任意のRedis DSNを受け入れるタイプ。

* ユーザー情報が必要です。
* TLDは不要です。
* ホストが必要です。(例:`rediss://:pass@localhost`)
"""
MongoDsn = Annotated[MultiHostUrl, UrlConstraints(allowed_schemes=['mongodb', 'mongodb+srv'], default_port=27017)]
"""任意のMongoDB DSNを受け入れる型。

* ユーザー情報は必要ありません
* データベース名は必要ありません
* ポートは不要です。
* ユーザ情報はユーザパートなしで渡すことができます(例:`mongodb://mongodb0.example.com:27017`)。
"""
KafkaDsn = Annotated[Url, UrlConstraints(allowed_schemes=['kafka'], default_host='localhost', default_port=9092)]
"""任意のKafka DSNを受け入れるタイプ。

* ユーザー情報が必要です。
* TLDは不要です。
* ホストが必要です。
"""
NatsDsn = Annotated[
    MultiHostUrl, UrlConstraints(allowed_schemes=['nats', 'tls', 'ws'], default_host='localhost', default_port=4222)
]
"""任意のNATS DSNを受け入れるタイプ。

NATSは、ますます高度に接続される世界のために構築された接続技術です。
これは、オンプレミス、エッジ、ウェブとモバイル、デバイスなど、クラウドベンダーのあらゆる組み合わせにわたって、アプリケーションが安全に通信できるようにする単一のテクノロジーです。
詳細:https://nats.io
"""
MySQLDsn = Annotated[
    Url,
    UrlConstraints(
        allowed_schemes=[
            'mysql',
            'mysql+mysqlconnector',
            'mysql+aiomysql',
            'mysql+asyncmy',
            'mysql+mysqldb',
            'mysql+pymysql',
            'mysql+cymysql',
            'mysql+pyodbc',
        ],
        default_port=3306,
    ),
]
"""任意のMySQL DSNを受け入れるタイプ。

* ユーザー情報が必要です。。
* TLDは不要です。
* ホストが必要です。
"""
MariaDBDsn = Annotated[
    Url,
    UrlConstraints(
        allowed_schemes=['mariadb', 'mariadb+mariadbconnector', 'mariadb+pymysql'],
        default_port=3306,
    ),
]
"""任意のMariaDB DSNを受け入れるタイプ。

* ユーザー情報が必要です。
* TLDは不要です。
* ホストが必要です。
"""
ClickHouseDsn = Annotated[
    Url,
    UrlConstraints(
        allowed_schemes=['clickhouse+native', 'clickhouse+asynch'],
        default_host='localhost',
        default_port=9000,
    ),
]
"""A type that will accept any ClickHouse DSN.

* ユーザー情報が必要です。
* TLDは不要です。
* ホストが必要です。
"""

def import_email_validator() -> None:
    global email_validator
    try:
        import email_validator
    except ImportError as e:
        raise ImportError('email-validator is not installed, run `pip install pydantic[email]`') from e
    if not version('email-validator').partition('.')[0] == '2':
        raise ImportError('email-validator version >= 2.0 required, run pip install -U email-validator')


if TYPE_CHECKING:
    EmailStr = Annotated[str, ...]
else:

    class EmailStr:
        """
        Info:
            このタイプを使用するには、オプションの[`email-validator`](https://github.com/JoshData/python-email-validator)パッケージをインストールする必要があります。

            ```bash
            pip install email-validator
            ```

        電子メールアドレスを検証します。

        ```py
        from pydantic import BaseModel, EmailStr

        class Model(BaseModel):
            email: EmailStr

        print(Model(email='contact@mail.com'))
        #> email='contact@mail.com'
        ```
        """  # noqa: D212

        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            _source: type[Any],
            _handler: GetCoreSchemaHandler,
        ) -> core_schema.CoreSchema:
            import_email_validator()
            return core_schema.no_info_after_validator_function(cls._validate, core_schema.str_schema())

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: _schema_generation_shared.GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            field_schema = handler(core_schema)
            field_schema.update(type='string', format='email')
            return field_schema

        @classmethod
        def _validate(cls, input_value: str, /) -> str:
            return validate_email(input_value)[1]


class NameEmail(_repr.Representation):
    """
    Info:
        このタイプを使用するには、オプションの[`email-validator`](https://github.com/JoshData/python-email-validator)パッケージをインストールする必要があります。

        ```bash
        pip install email-validator
        ```

    [RFC 5322](https://datatracker.ietf.org/doc/html/rfc5322#section-3.4)で指定されているように、名前と電子メールアドレスの組み合わせを検証します。

    `NameEmail`には`name`と`email`という2つの属性があります。
    `name`が指定されていない場合は、メールアドレスから推測されます。

    ```py
    from pydantic import BaseModel, NameEmail

    class User(BaseModel):
        email: NameEmail

    user = User(email='Fred Bloggs <fred.bloggs@example.com>')
    print(user.email)
    #> Fred Bloggs <fred.bloggs@example.com>
    print(user.email.name)
    #> Fred Bloggs

    user = User(email='fred.bloggs@example.com')
    print(user.email)
    #> fred.bloggs <fred.bloggs@example.com>
    print(user.email.name)
    #> fred.bloggs
    ```
    """  # noqa: D212

    __slots__ = 'name', 'email'

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, NameEmail) and (self.name, self.email) == (other.name, other.email)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: _schema_generation_shared.GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = handler(core_schema)
        field_schema.update(type='string', format='name-email')
        return field_schema

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source: type[Any],
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        import_email_validator()

        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.json_or_python_schema(
                json_schema=core_schema.str_schema(),
                python_schema=core_schema.union_schema(
                    [core_schema.is_instance_schema(cls), core_schema.str_schema()],
                    custom_error_type='name_email_type',
                    custom_error_message='Input is not a valid NameEmail',
                ),
                serialization=core_schema.to_string_ser_schema(),
            ),
        )

    @classmethod
    def _validate(cls, input_value: Self | str, /) -> Self:
        if isinstance(input_value, str):
            name, email = validate_email(input_value)
            return cls(name, email)
        else:
            return input_value

    def __str__(self) -> str:
        if '@' in self.name:
            return f'"{self.name}" <{self.email}>'

        return f'{self.name} <{self.email}>'


class IPvAnyAddress:
    """IPv4またはIPv6アドレスを検証します。

    ```py
    from pydantic import BaseModel
    from pydantic.networks import IPvAnyAddress

    class IpModel(BaseModel):
        ip: IPvAnyAddress

    print(IpModel(ip='127.0.0.1'))
    #> ip=IPv4Address('127.0.0.1')

    try:
        IpModel(ip='http://www.example.com')
    except ValueError as e:
        print(e.errors())
        '''
        [
            {
                'type': 'ip_any_address',
                'loc': ('ip',),
                'msg': 'value is not a valid IPv4 or IPv6 address',
                'input': 'http://www.example.com',
            }
        ]
        '''
    ```
    """

    __slots__ = ()

    def __new__(cls, value: Any) -> IPv4Address | IPv6Address:
        """Validate an IPv4 or IPv6 address."""
        try:
            return IPv4Address(value)
        except ValueError:
            pass

        try:
            return IPv6Address(value)
        except ValueError:
            raise PydanticCustomError('ip_any_address', 'value is not a valid IPv4 or IPv6 address')

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: _schema_generation_shared.GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = {}
        field_schema.update(type='string', format='ipvanyaddress')
        return field_schema

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source: type[Any],
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate, serialization=core_schema.to_string_ser_schema()
        )

    @classmethod
    def _validate(cls, input_value: Any, /) -> IPv4Address | IPv6Address:
        return cls(input_value)  # type: ignore[return-value]


class IPvAnyInterface:
    """IPv4またはIPv6インターフェイスを検証します。"""

    __slots__ = ()

    def __new__(cls, value: NetworkType) -> IPv4Interface | IPv6Interface:
        """Validate an IPv4 or IPv6 interface."""
        try:
            return IPv4Interface(value)
        except ValueError:
            pass

        try:
            return IPv6Interface(value)
        except ValueError:
            raise PydanticCustomError('ip_any_interface', 'value is not a valid IPv4 or IPv6 interface')

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: _schema_generation_shared.GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = {}
        field_schema.update(type='string', format='ipvanyinterface')
        return field_schema

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source: type[Any],
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate, serialization=core_schema.to_string_ser_schema()
        )

    @classmethod
    def _validate(cls, input_value: NetworkType, /) -> IPv4Interface | IPv6Interface:
        return cls(input_value)  # type: ignore[return-value]


IPvAnyNetworkType: TypeAlias = 'IPv4Network | IPv6Network'

if TYPE_CHECKING:
    IPvAnyNetwork = IPvAnyNetworkType
else:

    class IPvAnyNetwork:
        """IPv4またはIPv6ネットワークを検証します。"""

        __slots__ = ()

        def __new__(cls, value: NetworkType) -> IPvAnyNetworkType:
            """IPv4またはIPv6ネットワークを検証します。"""
            # Assume IP Network is defined with a default value for `strict` argument.
            # Define your own class if you want to specify network address check strictness.
            try:
                return IPv4Network(value)
            except ValueError:
                pass

            try:
                return IPv6Network(value)
            except ValueError:
                raise PydanticCustomError('ip_any_network', 'value is not a valid IPv4 or IPv6 network')

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: _schema_generation_shared.GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            field_schema = {}
            field_schema.update(type='string', format='ipvanynetwork')
            return field_schema

        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            _source: type[Any],
            _handler: GetCoreSchemaHandler,
        ) -> core_schema.CoreSchema:
            return core_schema.no_info_plain_validator_function(
                cls._validate, serialization=core_schema.to_string_ser_schema()
            )

        @classmethod
        def _validate(cls, input_value: NetworkType, /) -> IPvAnyNetworkType:
            return cls(input_value)  # type: ignore[return-value]


def _build_pretty_email_regex() -> re.Pattern[str]:
    name_chars = r'[\w!#$%&\'*+\-/=?^_`{|}~]'
    unquoted_name_group = rf'((?:{name_chars}+\s+)*{name_chars}+)'
    quoted_name_group = r'"((?:[^"]|\")+)"'
    email_group = r'<\s*(.+)\s*>'
    return re.compile(rf'\s*(?:{unquoted_name_group}|{quoted_name_group})?\s*{email_group}\s*')


pretty_email_regex = _build_pretty_email_regex()

MAX_EMAIL_LENGTH = 2048
"""電子メールの最大長。
ほとんどの実装で許可されている数と比較して、多少任意ですが非常に寛大な数です。
"""
def validate_email(value: str) -> tuple[str, str]:
    """[email-validator](https://pypi.org/project/email-validator/)を使用した電子メールアドレスの検証。

    Note:
        Note that:

        * 生のIPアドレス(リテラル)ドメイン部分は許可されません。
        * `"John Doe<local_part@domain.com>"`スタイルの"pretty"電子メールアドレスが処理されます。
        * スペースはアドレスの先頭と末尾からストライプされますが、エラーは発生しません。


    """
    if email_validator is None:
        import_email_validator()

    if len(value) > MAX_EMAIL_LENGTH:
        raise PydanticCustomError(
            'value_error',
            'value is not a valid email address: {reason}',
            {'reason': f'Length must not exceed {MAX_EMAIL_LENGTH} characters'},
        )

    m = pretty_email_regex.fullmatch(value)
    name: str | None = None
    if m:
        unquoted_name, quoted_name, value = m.groups()
        name = unquoted_name or quoted_name

    email = value.strip()

    try:
        parts = email_validator.validate_email(email, check_deliverability=False)
    except email_validator.EmailNotValidError as e:
        raise PydanticCustomError(
            'value_error', 'value is not a valid email address: {reason}', {'reason': str(e.args[0])}
        ) from e

    email = parts.normalized
    assert email is not None
    name = name or parts.local_part
    return name, email


__getattr__ = getattr_migration(__name__)
