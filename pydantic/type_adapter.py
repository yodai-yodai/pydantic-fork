"""アダプター仕様"""

from __future__ import annotations as _annotations

import sys
from contextlib import contextmanager
from dataclasses import is_dataclass
from functools import cached_property, wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    Literal,
    Set,
    TypeVar,
    Union,
    cast,
    final,
    overload,
)

from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator, Some
from typing_extensions import Concatenate, ParamSpec, is_typeddict

from pydantic.errors import PydanticUserError
from pydantic.main import BaseModel

from ._internal import _config, _generate_schema, _mock_val_ser, _typing_extra, _utils
from .config import ConfigDict
from .json_schema import (
    DEFAULT_REF_TEMPLATE,
    GenerateJsonSchema,
    JsonSchemaKeyT,
    JsonSchemaMode,
    JsonSchemaValue,
)
from .plugin._schema_validator import PluggableSchemaValidator, create_schema_validator

T = TypeVar('T')
R = TypeVar('R')
P = ParamSpec('P')
TypeAdapterT = TypeVar('TypeAdapterT', bound='TypeAdapter')


if TYPE_CHECKING:
    # should be `set[int] | set[str] | dict[int, IncEx] | dict[str, IncEx] | None`, but mypy can't cope
    IncEx = Union[Set[int], Set[str], Dict[int, Any], Dict[str, Any]]


def _get_schema(type_: Any, config_wrapper: _config.ConfigWrapper, parent_depth: int) -> CoreSchema:
    """`BaseModel`は独自の`__module__`を使用して定義された場所を見つけ、それらのグローバル内の前方参照を解決するシンボルを探します。
    一方、この関数は、`__module__`(常に`typing.py`)が役に立たないような、型エイリアスを含む任意のオブジェクトで呼び出すことができます。
    そのため、代わりに親スタックフレーム内のグローバルを調べます。

    これは、この関数がスコープ内に前方参照のターゲットを持つモジュール内で呼び出される場合には機能しますが、より複雑な場合には必ずしも機能しません。

    たとえば、

    a.py
    ```python
    from typing import Dict, List

    IntList = List[int]
    OuterDict = Dict[str, 'IntList']
    ```

    b.py
    ```python test="skip"
    from a import OuterDict

    from pydantic import TypeAdapter

    IntList = int  # replaces the symbol the forward reference is looking for
    v = TypeAdapter(OuterDict)
    v({'x': 1})  # should fail but doesn't
    ```

    `OuterDict`が`BaseModel`であれば、`a.py`名前空間内の前方参照を解決するので、これはうまくいきます。
    しかし、`TypeAdapter(OuterDict)`は`OuterDict`がどのモジュールから来たのか判断できません。

    言い換えれば、呼び出し元のモジュールに_all_forward参照が存在するという前提は、技術的には常に正しいとは限りません。
    ほとんどの場合はそうで、再帰的なモデルなどではうまく動作しますが、`BaseModel`の動作も完璧ではなく、同じような方法で_破ることができるので、この2つの間に正しいことも間違っていることもありません。

    しかし、少なくともこの振る舞いは`BaseModel`のものとは微妙に異なっています。
    """
    local_ns = _typing_extra.parent_frame_namespace(parent_depth=parent_depth)
    global_ns = sys._getframe(max(parent_depth - 1, 1)).f_globals.copy()
    global_ns.update(local_ns or {})
    gen = _generate_schema.GenerateSchema(config_wrapper, types_namespace=global_ns, typevars_map={})
    schema = gen.generate_schema(type_)
    schema = gen.clean_schema(schema)
    return schema


def _getattr_no_parents(obj: Any, attribute: str) -> Any:
    """親タイプから属性を検索せずに属性値を返します。"""
    if hasattr(obj, '__dict__'):
        try:
            return obj.__dict__[attribute]
        except KeyError:
            pass

    slots = getattr(obj, '__slots__', None)
    if slots is not None and attribute in slots:
        return getattr(obj, attribute)
    else:
        raise AttributeError(attribute)


def _type_has_config(type_: Any) -> bool:
    """タイプにconfigがあるかどうかを返します。"""
    type_ = _typing_extra.annotated_type(type_) or type_
    try:
        return issubclass(type_, BaseModel) or is_dataclass(type_) or is_typeddict(type_)
    except TypeError:
        # type is not a class
        return False


# This is keeping track of the frame depth for the TypeAdapter functions. This is required for _parent_depth used for
# ForwardRef resolution. We may enter the TypeAdapter schema building via different TypeAdapter functions. Hence, we
# need to keep track of the frame depth relative to the originally provided _parent_depth.
def _frame_depth(
    depth: int,
) -> Callable[[Callable[Concatenate[TypeAdapterT, P], R]], Callable[Concatenate[TypeAdapterT, P], R]]:
    def wrapper(func: Callable[Concatenate[TypeAdapterT, P], R]) -> Callable[Concatenate[TypeAdapterT, P], R]:
        @wraps(func)
        def wrapped(self: TypeAdapterT, *args: P.args, **kwargs: P.kwargs) -> R:
            with self._with_frame_depth(depth + 1):  # depth + 1 for the wrapper function
                return func(self, *args, **kwargs)

        return wrapped

    return wrapper


@final
class TypeAdapter(Generic[T]):
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/type_adapter/

    タイプアダプタは、Pythonタイプに基づいて検証とシリアライゼーションを実行する柔軟な方法を提供します。

    `TypeAdapter`インスタンスは、そのようなメソッドを持たない型(データクラス、プリミティブ型など)に対して、`BaseModel`インスタンスメソッドの機能の一部を公開します。

    **Note:** `TypeAdapter`インスタンスは型ではなく、フィールドの型注釈として使用することはできません。

    **Note:** デフォルトでは、`TypeAdapter`は[`model_config`][pydantic.BaseModel.model_config]または`TypeAdapter`コンストラクタ`config`の[`defer_build=True`][pydantic.config.ConfigDict.defer_build]設定を考慮しません。また、モデルバリデータとシリアライザの構築を延期するには、設定の[`experimental_defer_build_mode=('model','type_adapter')`][pydantic.config.ConfigDict.experimental_defer_build_mode]を明示的に設定する必要があります。したがって、この機能は下位互換性を保証するためにオプトインされています。

    Attributes:
        core_schema: 型のコア・スキーマ。
        validator(SchemaValidator): 型のスキーマ・バリデーター。
        serializer: 型のスキーマ・シリアライザ。
    """

    @overload
    def __init__(
        self,
        type: type[T],
        *,
        config: ConfigDict | None = ...,
        _parent_depth: int = ...,
        module: str | None = ...,
    ) -> None: ...

    # This second overload is for unsupported special forms (such as Annotated, Union, etc.)
    # Currently there is no way to type this correctly
    # See https://github.com/python/typing/pull/1618
    @overload
    def __init__(
        self,
        type: Any,
        *,
        config: ConfigDict | None = ...,
        _parent_depth: int = ...,
        module: str | None = ...,
    ) -> None: ...

    def __init__(
        self,
        type: Any,
        *,
        config: ConfigDict | None = None,
        _parent_depth: int = 2,
        module: str | None = None,
    ) -> None:
        """TypeAdapterオブジェクトを初期化します。

        Args:
            type: `TypeAdapter`に関連付けられた型。
            config: `TypeAdapter`の設定は、[`ConfigDict`][pydantic.config.ConfigDict]に準拠した辞書でなければなりません。
            _parent_depth: ローカルネームスペースを構築するために親ネームスペースを検索するデプス。
            module: プラグインに渡されるモジュール(指定されている場合)。

        !!! note
            使用している型が上書きできない独自の設定を持っている場合(例:`BaseModel`、`TypedDict`、`dataclass`)、`TypeAdapter`をインスタンス化するときに`config`引数を使用することはできません。この場合、[`type-adapter-config-unused`](../errors/usage_errors.md#type-adapter-config-unused)エラーが発生します。

        !!! note
            `_parent_depth`引数の名前にはアンダースコアが付いています。これは、引数がプライベートであることを示し、使用しないようにするためです。
            マイナーバージョンでは非推奨になる可能性があるため、動作/サポートの潜在的な変更に満足している場合にのみ使用することをお勧めします。

        ??? tip "Compatibility with `mypy`"
            使用されているタイプによっては、`mypy`が`TypeAdapter`をインスタンス化するときにエラーが発生することがあります。回避策として、変数に明示的に注釈を付けることができます。

            ```py
            from typing import Union

            from pydantic import TypeAdapter

            ta: TypeAdapter[Union[str, int]] = TypeAdapter(Union[str, int])  # type: ignore[arg-type]
            ```

        Returns:
            指定された`type`用に設定されたタイプアダプタ。
        """
        if _type_has_config(type) and config is not None:
            raise PydanticUserError(
                'Cannot use `config` when the type is a BaseModel, dataclass or TypedDict.'
                ' These types can have their own config and setting the config via the `config`'
                ' parameter to TypeAdapter will not override it, thus the `config` you passed to'
                ' TypeAdapter becomes meaningless, which is probably not what you want.',
                code='type-adapter-config-unused',
            )

        self._type = type
        self._config = config
        self._parent_depth = _parent_depth
        if module is None:
            f = sys._getframe(1)
            self._module_name = cast(str, f.f_globals.get('__name__', ''))
        else:
            self._module_name = module

        self._core_schema: CoreSchema | None = None
        self._validator: SchemaValidator | PluggableSchemaValidator | None = None
        self._serializer: SchemaSerializer | None = None

        if not self._defer_build():
            # Immediately initialize the core schema, validator and serializer
            with self._with_frame_depth(1):  # +1 frame depth for this __init__
                # Model itself may be using deferred building. For backward compatibility we don't rebuild model mocks
                # here as part of __init__ even though TypeAdapter itself is not using deferred building.
                self._init_core_attrs(rebuild_mocks=False)

    @contextmanager
    def _with_frame_depth(self, depth: int) -> Iterator[None]:
        self._parent_depth += depth
        try:
            yield
        finally:
            self._parent_depth -= depth

    @_frame_depth(1)
    def _init_core_attrs(self, rebuild_mocks: bool) -> None:
        try:
            self._core_schema = _getattr_no_parents(self._type, '__pydantic_core_schema__')
            self._validator = _getattr_no_parents(self._type, '__pydantic_validator__')
            self._serializer = _getattr_no_parents(self._type, '__pydantic_serializer__')
        except AttributeError:
            config_wrapper = _config.ConfigWrapper(self._config)
            core_config = config_wrapper.core_config(None)

            self._core_schema = _get_schema(self._type, config_wrapper, parent_depth=self._parent_depth)
            self._validator = create_schema_validator(
                schema=self._core_schema,
                schema_type=self._type,
                schema_type_module=self._module_name,
                schema_type_name=str(self._type),
                schema_kind='TypeAdapter',
                config=core_config,
                plugin_settings=config_wrapper.plugin_settings,
            )
            self._serializer = SchemaSerializer(self._core_schema, core_config)

        if rebuild_mocks and isinstance(self._core_schema, _mock_val_ser.MockCoreSchema):
            self._core_schema.rebuild()
            self._init_core_attrs(rebuild_mocks=False)
            assert not isinstance(self._core_schema, _mock_val_ser.MockCoreSchema)
            assert not isinstance(self._validator, _mock_val_ser.MockValSer)
            assert not isinstance(self._serializer, _mock_val_ser.MockValSer)

    @cached_property
    @_frame_depth(2)  # +2 for @cached_property and core_schema(self)
    def core_schema(self) -> CoreSchema:
        """SchemaValidatorとSchemaSerializerを構築するために使用されるpydantic-coreスキーマ。"""
        if self._core_schema is None or isinstance(self._core_schema, _mock_val_ser.MockCoreSchema):
            self._init_core_attrs(rebuild_mocks=True)  # Do not expose MockCoreSchema from public function
        assert self._core_schema is not None and not isinstance(self._core_schema, _mock_val_ser.MockCoreSchema)
        return self._core_schema

    @cached_property
    @_frame_depth(2)  # +2 for @cached_property + validator(self)
    def validator(self) -> SchemaValidator | PluggableSchemaValidator:
        """モデルのインスタンスを検証するために使用されるpydantic-core SchemaValidator。"""
        if not isinstance(self._validator, (SchemaValidator, PluggableSchemaValidator)):
            self._init_core_attrs(rebuild_mocks=True)  # Do not expose MockValSer from public function
        assert isinstance(self._validator, (SchemaValidator, PluggableSchemaValidator))
        return self._validator

    @cached_property
    @_frame_depth(2)  # +2 for @cached_property + serializer(self)
    def serializer(self) -> SchemaSerializer:
        """モデルのインスタンスをダンプするために使用されるpydantic-core SchemaSerializer。"""
        if not isinstance(self._serializer, SchemaSerializer):
            self._init_core_attrs(rebuild_mocks=True)  # Do not expose MockValSer from public function
        assert isinstance(self._serializer, SchemaSerializer)
        return self._serializer

    def _defer_build(self) -> bool:
        config = self._config if self._config is not None else self._model_config()
        return self._is_defer_build_config(config) if config is not None else False

    def _model_config(self) -> ConfigDict | None:
        type_: Any = _typing_extra.annotated_type(self._type) or self._type  # Eg FastAPI heavily uses Annotated
        if _utils.lenient_issubclass(type_, BaseModel):
            return type_.model_config
        return getattr(type_, '__pydantic_config__', None)

    @staticmethod
    def _is_defer_build_config(config: ConfigDict) -> bool:
        # TODO reevaluate this logic when we have a better understanding of how defer_build should work with TypeAdapter
        # Should we drop the special experimental_defer_build_mode check?
        return config.get('defer_build', False) is True and 'type_adapter' in config.get(
            'experimental_defer_build_mode', tuple()
        )

    @_frame_depth(1)
    def validate_python(
        self,
        object: Any,
        /,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
    ) -> T:
        """モデルに対してPythonオブジェクトを検証します。

        Args:
            object: モデルに対して検証するPythonオブジェクト。
            strict: 型を厳密にチェックするかどうか。
            from_attributes: オブジェクト属性からデータを抽出するかどうか。
            context: バリデータに渡す追加のコンテキスト。

        !!! note
            Pydanticの`dataclass`で`TypeAdapter`を使用する場合、`from_attributes`引数の使用はサポートされません。

        Returns:
            検証されたオブジェクトです。
        """
        return self.validator.validate_python(object, strict=strict, from_attributes=from_attributes, context=context)

    @_frame_depth(1)
    def validate_json(
        self, data: str | bytes, /, *, strict: bool | None = None, context: dict[str, Any] | None = None
    ) -> T:
        """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/json/#json-parsing

        JSON文字列またはバイトをモデルに対して検証します。

        Args:
            data: モデルに対して検証するJSONデータ。
            strict: 型を厳密にチェックするかどうか。
            context: 検証中に使用する追加のコンテキスト。

        Returns:
            検証されたオブジェクトです。
        """
        return self.validator.validate_json(data, strict=strict, context=context)

    @_frame_depth(1)
    def validate_strings(self, obj: Any, /, *, strict: bool | None = None, context: dict[str, Any] | None = None) -> T:
        """検証オブジェクトには、モデルに対する文字列データが含まれています。

        Args:
            obj: 検証する文字列データがオブジェクトに含まれています。
            strict: 型を厳密にチェックするかどうか。
            context: 検証中に使用する追加のコンテキスト。

        Returns:
            検証されたオブジェクトです。
        """
        return self.validator.validate_strings(obj, strict=strict, context=context)

    @_frame_depth(1)
    def get_default_value(self, *, strict: bool | None = None, context: dict[str, Any] | None = None) -> Some[T] | None:
        """ラップされたタイプのデフォルト値を取得します。

        Args:
            strict: 型を厳密にチェックするかどうか。
            context: バリデータに渡す追加のコンテキスト。

        Returns:
            存在する場合は`Some`でラップされたデフォルト値、存在しない場合はNoneでラップされたデフォルト値。
        """
        return self.validator.get_default_value(strict=strict, context=context)

    @_frame_depth(1)
    def dump_python(
        self,
        instance: T,
        /,
        *,
        mode: Literal['json', 'python'] = 'python',
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal['none', 'warn', 'error'] = True,
        serialize_as_any: bool = False,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """適合した型のインスタンスをPythonオブジェクトにダンプします。

        Args:
            instance: シリアライズするPythonオブジェクト。
            mode: 出力フォーマット。
            include: 出力に含めるフィールド。
            exclude: 出力から除外するフィールド。
            by_alias: フィールド名にエイリアス名を使用するかどうか。
            exclude_unset: 設定されていないフィールドを除外するかどうか。
            exclude_defaults: デフォルト値を持つフィールドを除外するかどうか。
            exclude_none: None値を持つフィールドを除外するかどうか。
            round_trip: デシリアライズと互換性のある方法でシリアライズされたデータを出力するかどうか。
            warnings: シリアライゼーションエラーの処理方法。False/"none"はエラーを無視します。True/"warn"はエラーをログに記録します。"error"は[`PydanticSerializationError`][pydantic_core.PydanticSerializationError]を発生させます。
            serialize_as_any: ダック型のシリアライズ動作でフィールドをシリアライズするかどうか。
            context: シリアライザに渡す追加のコンテキスト。

        Returns:
            シリアライズされたオブジェクト。
        """
        return self.serializer.to_python(
            instance,
            mode=mode,
            by_alias=by_alias,
            include=include,
            exclude=exclude,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
            context=context,
        )

    @_frame_depth(1)
    def dump_json(
        self,
        instance: T,
        /,
        *,
        indent: int | None = None,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal['none', 'warn', 'error'] = True,
        serialize_as_any: bool = False,
        context: dict[str, Any] | None = None,
    ) -> bytes:
        """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/json/#json-serialization

        適応型のインスタンスをJSONにシリアライズします。

        Args:
            instance: シリアライズされるインスタンス。
            indent: JSONインデントのスペースの数。
            include: 含めるフィールド。
            exclude: 除外するフィールド。
            by_alias: フィールド名にエイリアス名を使用するかどうか。
            exclude_unset: 設定されていないフィールドを除外するかどうか。
            exclude_defaults: デフォルト値を持つフィールドを除外するかどうか。
            exclude_none: `None`の値を持つフィールドを除外するかどうか。
            round_trip: ラウンドトリップを確実にするために、インスタンスをシリアライズしてデシリアライズするかどうか。
            warnings: シリアライゼーションエラーの処理方法。False/"none"はエラーを無視します。True/"warn"はエラーをログに記録します。"error"は[`PydanticSerializationError`][pydantic_core.PydanticSerializationError]を発生させます。
            serialize_as_any: ダック型のシリアライズ動作でフィールドをシリアライズするかどうか。
            context: シリアライザに渡す追加のコンテキスト。

        Returns:
            指定されたインスタンスのJSON表現(バイト単位)。
        """
        return self.serializer.to_json(
            instance,
            indent=indent,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
            context=context,
        )

    @_frame_depth(1)
    def json_schema(
        self,
        *,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
        mode: JsonSchemaMode = 'validation',
    ) -> dict[str, Any]:
        """適用された型のJSONスキーマを生成します。

        Args:
            by_alias: フィールド名にエイリアス名を使用するかどうか。
            ref_template: $ref文字列の生成に使用される書式文字列。
            schema_generator: スキーマの作成に使用するジェネレーター・クラス。
            mode: スキーマの生成に使用するモード。

        Returns:
            ディクショナリとしてのモデルのJSONスキーマ。
        """
        schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)
        return schema_generator_instance.generate(self.core_schema, mode=mode)

    @staticmethod
    def json_schemas(
        inputs: Iterable[tuple[JsonSchemaKeyT, JsonSchemaMode, TypeAdapter[Any]]],
        /,
        *,
        by_alias: bool = True,
        title: str | None = None,
        description: str | None = None,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    ) -> tuple[dict[tuple[JsonSchemaKeyT, JsonSchemaMode], JsonSchemaValue], JsonSchemaValue]:
        """複数のタイプアダプタからの定義を含むJSONスキーマを生成します。

        Args:
            inputs: スキーマ生成への入力です。最初の2つの項目は、(最初の)出力マッピングのキーを形成します。
            by_alias: エイリアス名を使用するかどうか。
            title: スキーマのタイトル。
            description: スキーマの説明。
            ref_template: $ref文字列の生成に使用される書式文字列。
            schema_generator: スキーマの作成に使用するジェネレーター・クラス。

        Returns:
            次の条件を満たすタプル:

                - 最初の要素は、JSONスキーマ・キー・タイプとJSONモードのタプルをキーとし、その入力ペアに対応するJSONスキーマを値とする辞書です(これらのスキーマは、2番目に返された要素で定義されている定義へのJsonRef参照を持つ場合があります)。
                - 2番目の要素は、最初に返された要素で参照されるすべての定義と、オプションのtitleおよびdescriptionキーを含むJSONスキーマです。
        """
        schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)

        inputs_ = []
        for key, mode, adapter in inputs:
            with adapter._with_frame_depth(1):  # +1 for json_schemas staticmethod
                inputs_.append((key, mode, adapter.core_schema))

        json_schemas_map, definitions = schema_generator_instance.generate_definitions(inputs_)

        json_schema: dict[str, Any] = {}
        if definitions:
            json_schema['$defs'] = definitions
        if title:
            json_schema['title'] = title
        if description:
            json_schema['description'] = description

        return json_schemas_map, json_schema
