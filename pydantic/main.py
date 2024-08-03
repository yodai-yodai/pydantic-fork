"""モデル作成ロジック"""

from __future__ import annotations as _annotations

import operator
import sys
import types
import typing
import warnings
from copy import copy, deepcopy
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    Literal,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

import pydantic_core
import typing_extensions
from pydantic_core import PydanticUndefined
from typing_extensions import Self, TypeAlias, Unpack

from ._internal import (
    _config,
    _decorators,
    _fields,
    _forward_ref,
    _generics,
    _mock_val_ser,
    _model_construction,
    _repr,
    _typing_extra,
    _utils,
)
from ._migration import getattr_migration
from .aliases import AliasChoices, AliasPath
from .annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler
from .config import ConfigDict
from .errors import PydanticUndefinedAnnotation, PydanticUserError
from .json_schema import DEFAULT_REF_TEMPLATE, GenerateJsonSchema, JsonSchemaMode, JsonSchemaValue, model_json_schema
from .plugin._schema_validator import PluggableSchemaValidator
from .warnings import PydanticDeprecatedSince20

# Always define certain types that are needed to resolve method type hints/annotations
# (even when not type checking) via typing.get_type_hints.
ModelT = TypeVar('ModelT', bound='BaseModel')
TupleGenerator = Generator[Tuple[str, Any], None, None]
IncEx: TypeAlias = Union[Set[int], Set[str], Dict[int, 'IncEx'], Dict[str, 'IncEx'], None]


if TYPE_CHECKING:
    from inspect import Signature
    from pathlib import Path

    from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator

    from ._internal._utils import AbstractSetIntStr, MappingIntStrAny
    from .deprecated.parse import Protocol as DeprecatedParseProtocol
    from .fields import ComputedFieldInfo, FieldInfo, ModelPrivateAttr
    from .fields import PrivateAttr as _PrivateAttr
else:
    # See PyCharm issues https://youtrack.jetbrains.com/issue/PY-21915
    # and https://youtrack.jetbrains.com/issue/PY-51428
    DeprecationWarning = PydanticDeprecatedSince20

__all__ = 'BaseModel', 'create_model'

_object_setattr = _model_construction.object_setattr


class BaseModel(metaclass=_model_construction.ModelMetaclass):
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/models/

    Pydanticモデルを作成するための基本クラス。

    Attributes:
        __class_vars__: モデルに定義されているクラス変数の名前。
        __private_attributes__: モデルのプライベート属性に関するメタデータ。
        __signature__: モデルをインスタンス化するためのシグネチャ。

        __pydantic_complete__: モデルの構築が完了したかどうか、またはまだ未定義のフィールドがあるかどうか。
        __pydantic_core_schema__: SchemaValidatorとSchemaSerializerの構築に使用されたpydantic-coreスキーマ。
        __pydantic_custom_init__: モデルにカスタムの`__init__`関数があるかどうか。
        __pydantic_decorators__: モデルで定義されたデコレータを含むメタデータ。これは、Pydantic V1の`Model.__validators__`と`Model.__root_validators__`を置き換えます。
        __pydantic_generic_metadata__: ジェネリックモデル用のメタデータ。型モジュールジェネリックの__args__、__origin__、__parameters__と同様の目的で使用されるデータが含まれています。最終的にはこれらに置き換えられる可能性があります。
        __pydantic_parent_namespace__: モデルの親ネームスペース。モデルの自動再構築に使用されます。
        __pydantic_post_init__: モデルの初期化後のメソッドの名前(定義されている場合)。
        __pydantic_root_model__: モデルが`RootModel`かどうか。
        __pydantic_serializer__: モデルのインスタンスをダンプするために使用されるpydantic-core SchemaSerializer。
        __pydantic_validator__: モデルのインスタンスを検証するために使用されるpydantic-core SchemaValidator。

        __pydantic_extra__: `model_config['extra']=='allow'`の場合に、検証からの追加フィールドの値を持つインスタンス属性。
        __pydantic_fields_set__: フィールドの名前が明示的に設定されたインスタンス属性。
        __pydantic_private__: モデルインスタンスに設定されたプライベート属性の値を持つインスタンス属性。
    """

    if TYPE_CHECKING:
        # Here we provide annotations for the attributes of BaseModel.
        # Many of these are populated by the metaclass, which is why this section is in a `TYPE_CHECKING` block.
        # However, for the sake of easy review, we have included type annotations of all class and instance attributes
        # of `BaseModel` here:

        # Class attributes
        model_config: ClassVar[ConfigDict]
        """
        モデルの設定は、[`ConfigDict`][pydantic.config.ConfigDict]に準拠した辞書でなければなりません。
        """

        model_fields: ClassVar[dict[str, FieldInfo]]
        """
        モデルで定義されたフィールドに関するメタデータ、[`FieldInfo`][pydantic.fields.FieldInfo]へのフィールド名のマッピング。

        これはPydantic V1の`Model.__fields__`を置き換えます。
        """

        model_computed_fields: ClassVar[dict[str, ComputedFieldInfo]]
        """計算されたフィールド名とそれに対応する`ComputedFieldInfo`オブジェクトの辞書。"""

        __class_vars__: ClassVar[set[str]]
        __private_attributes__: ClassVar[dict[str, ModelPrivateAttr]]
        __signature__: ClassVar[Signature]

        __pydantic_complete__: ClassVar[bool]
        __pydantic_core_schema__: ClassVar[CoreSchema]
        __pydantic_custom_init__: ClassVar[bool]
        __pydantic_decorators__: ClassVar[_decorators.DecoratorInfos]
        __pydantic_generic_metadata__: ClassVar[_generics.PydanticGenericMetadata]
        __pydantic_parent_namespace__: ClassVar[dict[str, Any] | None]
        __pydantic_post_init__: ClassVar[None | Literal['model_post_init']]
        __pydantic_root_model__: ClassVar[bool]
        __pydantic_serializer__: ClassVar[SchemaSerializer]
        __pydantic_validator__: ClassVar[SchemaValidator | PluggableSchemaValidator]

        # Instance attributes
        __pydantic_extra__: dict[str, Any] | None = _PrivateAttr()
        __pydantic_fields_set__: set[str] = _PrivateAttr()
        __pydantic_private__: dict[str, Any] | None = _PrivateAttr()

    else:
        # `model_fields` and `__pydantic_decorators__` must be set for
        # pydantic._internal._generate_schema.GenerateSchema.model_schema to work for a plain BaseModel annotation
        model_fields = {}
        model_computed_fields = {}

        __pydantic_decorators__ = _decorators.DecoratorInfos()
        __pydantic_parent_namespace__ = None
        # Prevent `BaseModel` from being instantiated directly:
        __pydantic_core_schema__ = _mock_val_ser.MockCoreSchema(
            'Pydantic models should inherit from BaseModel, BaseModel cannot be instantiated directly',
            code='base-model-instantiated',
        )
        __pydantic_validator__ = _mock_val_ser.MockValSer(
            'Pydantic models should inherit from BaseModel, BaseModel cannot be instantiated directly',
            val_or_ser='validator',
            code='base-model-instantiated',
        )
        __pydantic_serializer__ = _mock_val_ser.MockValSer(
            'Pydantic models should inherit from BaseModel, BaseModel cannot be instantiated directly',
            val_or_ser='serializer',
            code='base-model-instantiated',
        )

    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    model_config = ConfigDict()
    __pydantic_complete__ = False
    __pydantic_root_model__ = False

    def __init__(self, /, **data: Any) -> None:  # type: ignore
        """キーワード引数からの入力データを解析および検証して、新しいモデルを作成します。

        入力データを検証して有効なモデルを作成できない場合は、[`ValidationError`][pydantic_core.ValidationError]が発生します。

        `self`は、フィールド名として`self`を許可するために、明示的に定位置のみです。
        """
        # `__tracebackhide__` tells pytest and some other tools to omit this function from tracebacks
        __tracebackhide__ = True
        self.__pydantic_validator__.validate_python(data, self_instance=self)

    # The following line sets a flag that we use to determine when `__init__` gets overridden by the user
    __init__.__pydantic_base_init__ = True  # pyright: ignore[reportFunctionMemberAccess]

    @property
    def model_extra(self) -> dict[str, Any] | None:
        """検証中に追加フィールドセットを取得します。

        Returns:
            追加フィールドの辞書、または`config.extra`が`"allow"`に設定されていない場合は`None`。
        """
        return self.__pydantic_extra__

    @property
    def model_fields_set(self) -> set[str]:
        """このモデルインスタンスに明示的に設定されているフィールドのセットを返します。

        Returns:
            設定された(つまり、デフォルトから入力されなかった)フィールドを表す文字列のセット。
        """
        return self.__pydantic_fields_set__

    @classmethod
    def model_construct(cls, _fields_set: set[str] | None = None, **values: Any) -> Self:  # noqa: C901
        """検証されたデータを持つ`Model`クラスの新しいインスタンスを作成します。

        信頼できるデータまたは事前に検証されたデータから、新しいモデル設定`__dict__`および`__pydantic_fields_set__`を作成します。
        デフォルト値が使用されますが、その他の検証は実行されません。

        !!! note
            `model_construct()`は一般に、提供されたモデルの`model_config.extra`設定を尊重します。
            つまり、`model_config.extra=='allow'`の場合、余分に渡された値はすべてモデルインスタンスの`__dict__`フィールドと`__pydantic_extra__`フィールドに追加されます。`model_config.extra=='ignore'`(デフォルト)の場合、余分に渡された値はすべて無視されます。
            `model_construct()`を呼び出しても検証は行われないので、`model_config.extra=='forbid'`を指定しても、余分な値が渡されてもエラーにはなりませんが、無視されます。

        Args:
            _fields_set: Modelインスタンスに受け入れられるフィールド名のセット。
            values: 信頼できるデータ辞書または事前に検証されたデータ辞書。

        Returns:
            検証されたデータを持つ`Model`クラスの新しいインスタンス。
        """
        m = cls.__new__(cls)
        fields_values: dict[str, Any] = {}
        fields_set = set()

        for name, field in cls.model_fields.items():
            if field.alias is not None and field.alias in values:
                fields_values[name] = values.pop(field.alias)
                fields_set.add(name)

            if (name not in fields_set) and (field.validation_alias is not None):
                validation_aliases: list[str | AliasPath] = (
                    field.validation_alias.choices
                    if isinstance(field.validation_alias, AliasChoices)
                    else [field.validation_alias]
                )

                for alias in validation_aliases:
                    if isinstance(alias, str) and alias in values:
                        fields_values[name] = values.pop(alias)
                        fields_set.add(name)
                        break
                    elif isinstance(alias, AliasPath):
                        value = alias.search_dict_for_path(values)
                        if value is not PydanticUndefined:
                            fields_values[name] = value
                            fields_set.add(name)
                            break

            if name not in fields_set:
                if name in values:
                    fields_values[name] = values.pop(name)
                    fields_set.add(name)
                elif not field.is_required():
                    fields_values[name] = field.get_default(call_default_factory=True)
        if _fields_set is None:
            _fields_set = fields_set

        _extra: dict[str, Any] | None = (
            {k: v for k, v in values.items()} if cls.model_config.get('extra') == 'allow' else None
        )
        _object_setattr(m, '__dict__', fields_values)
        _object_setattr(m, '__pydantic_fields_set__', _fields_set)
        if not cls.__pydantic_root_model__:
            _object_setattr(m, '__pydantic_extra__', _extra)

        if cls.__pydantic_post_init__:
            m.model_post_init(None)
            # update private attributes with values set
            if hasattr(m, '__pydantic_private__') and m.__pydantic_private__ is not None:
                for k, v in values.items():
                    if k in m.__private_attributes__:
                        m.__pydantic_private__[k] = v

        elif not cls.__pydantic_root_model__:
            # Note: if there are any private attributes, cls.__pydantic_post_init__ would exist
            # Since it doesn't, that means that `__pydantic_private__` should be set to None
            _object_setattr(m, '__pydantic_private__', None)

        return m

    def model_copy(self, *, update: dict[str, Any] | None = None, deep: bool = False) -> Self:
        """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/serialization/#model_copy

        モデルのコピーを返します。

        Args:
            update: 新しいモデルで変更または追加する値です。注意:新しいモデルを作成する前にデータは検証されません。このデータは信頼してください。
            deep: モデルのディープコピーを作成するには`True`に設定します。

        Returns:
            新しいモデルインスタンス。
        """
        copied = self.__deepcopy__() if deep else self.__copy__()
        if update:
            if self.model_config.get('extra') == 'allow':
                for k, v in update.items():
                    if k in self.model_fields:
                        copied.__dict__[k] = v
                    else:
                        if copied.__pydantic_extra__ is None:
                            copied.__pydantic_extra__ = {}
                        copied.__pydantic_extra__[k] = v
            else:
                copied.__dict__.update(update)
            copied.__pydantic_fields_set__.update(update.keys())
        return copied

    def model_dump(
        self,
        *,
        mode: Literal['json', 'python'] | str = 'python',
        include: IncEx = None,
        exclude: IncEx = None,
        context: Any | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal['none', 'warn', 'error'] = True,
        serialize_as_any: bool = False,
    ) -> dict[str, Any]:
        """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/serialization/#modelmodel_dump

        モデルのディクショナリ表現を生成します。オプションで、含めるフィールドまたは除外するフィールドを指定します。

        Args:
            mode: `to_python`が実行されるモード。
                modeが'json'の場合、出力にはJSONシリアライザブル型のみが含まれます。
                modeが'python'の場合、出力にはJSONシリアライズできないPythonオブジェクトが含まれる可能性があります。
            include: 出力に含めるフィールドのセット。
            exclude: 出力から除外するフィールドのセット。
            context: シリアライザに渡す追加のコンテキスト。
            by_alias: 定義されている場合に、ディクショナリ・キーでフィールドの別名を使用するかどうか。
            exclude_unset: 明示的に設定されていないフィールドを除外するかどうか。
            exclude_defaults: デフォルト値に設定されているフィールドを除外するかどうか。
            exclude_none: `None`の値を持つフィールドを除外するかどうか。
            round_trip: Trueの場合、ダンプされた値はJson[T]のようなべき等でない型の入力として有効であるべきです。
            warnings: シリアライゼーションエラーの処理方法。False/"none"はエラーを無視します。True/"warn"はエラーをログに記録します。"error"は[`PydanticSerializationError`][pydantic_core.PydanticSerializationError]を発生させます。
            serialize_as_any: ダック型のシリアライズ動作でフィールドをシリアライズするかどうか。

        Returns:
            モデルのディクショナリ表現。
        """
        return self.__pydantic_serializer__.to_python(
            self,
            mode=mode,
            by_alias=by_alias,
            include=include,
            exclude=exclude,
            context=context,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )

    def model_dump_json(
        self,
        *,
        indent: int | None = None,
        include: IncEx = None,
        exclude: IncEx = None,
        context: Any | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal['none', 'warn', 'error'] = True,
        serialize_as_any: bool = False,
    ) -> str:
        """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/serialization/#modelmodel_dump_json

        Pydanticの`to_json`メソッドを使用してモデルのJSON表現を生成します。

        Args:
            indent: JSON出力で使用するインデント。Noneが渡された場合、出力はコンパクトになります。
            include: JSON出力に含めるフィールド。
            exclude: JSON出力から除外するフィールド。
            context: シリアライザに渡す追加のコンテキスト。
            by_alias: フィールドエイリアスを使用してシリアライズするかどうか。
            exclude_unset: 明示的に設定されていないフィールドを除外するかどうか。
            exclude_defaults: デフォルト値に設定されているフィールドを除外するかどうか。
            exclude_none: `None`の値を持つフィールドを除外するかどうか。
            round_trip: Trueの場合、ダンプされた値はJson[T]のようなべき等でない型の入力として有効であるべきです。
            warnings: シリアライゼーションエラーの処理方法。False/"none"はエラーを無視します。True/"warn"はエラーをログに記録します。"error"は[`PydanticSerializationError`][pydantic_core.PydanticSerializationError]を発生させます。
            serialize_as_any: ダック型のシリアライズ動作でフィールドをシリアライズするかどうか。

        Returns:
            モデルのJSON文字列表現。
        """
        return self.__pydantic_serializer__.to_json(
            self,
            indent=indent,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        ).decode()

    @classmethod
    def model_json_schema(
        cls,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
        mode: JsonSchemaMode = 'validation',
    ) -> dict[str, Any]:
        """モデルクラスのJSONスキーマを生成します。

        Args:
            by_alias: 属性の別名を使用するかどうか。
            ref_template:参照テンプレート。
            schema_generator:JSONスキーマの生成に使用されるロジックを、`GenerateJsonSchema`のサブクラスとして、必要な変更を加えてオーバーライドします。
            mode:スキーマを生成するモード。

        Returns:
            指定されたモデルクラスのJSONスキーマ。

        """
        return model_json_schema(
            cls, by_alias=by_alias, ref_template=ref_template, schema_generator=schema_generator, mode=mode
        )

    @classmethod
    def model_parametrized_name(cls, params: tuple[type[Any], ...]) -> str:
        """ジェネリッククラスのパラメータ化のクラス名を計算します。

        このメソッドをオーバーライドして、汎用BaseModelsのカスタム命名スキームを実現できます。

        Args:
            params: クラスの型のタプルです。2つの型変数を持つジェネリッククラス`Model`と具象モデル`Model[str, int]`が与えられると、値`(str, int)`が`params`に渡されます。

        Returns:
            `params`が型変数として`cls`に渡される新しいクラスを表す文字列。

        Raises:
            TypeError:非ジェネリックモデルの具象名を生成しようとしたときに発生します。

        """
        if not issubclass(cls, typing.Generic):
            raise TypeError('Concrete names should only be generated for generic models.')

        # Any strings received should represent forward references, so we handle them specially below.
        # If we eventually move toward wrapping them in a ForwardRef in __class_getitem__ in the future,
        # we may be able to remove this special case.
        param_names = [param if isinstance(param, str) else _repr.display_as_type(param) for param in params]
        params_component = ', '.join(param_names)
        return f'{cls.__name__}[{params_component}]'

    def model_post_init(self, __context: Any) -> None:
        """このメソッドをオーバーライドして、`__init__`と`model_construct`の後に追加の初期化を実行します。
        これは、モデル全体を初期化する必要がある検証を行う場合に便利です。
        """
        pass

    @classmethod
    def model_rebuild(
        cls,
        *,
        force: bool = False,
        raise_errors: bool = True,
        _parent_namespace_depth: int = 2,
        _types_namespace: dict[str, Any] | None = None,
    ) -> bool | None:
        """モデルのpydantic-coreスキーマを再構築してみてください。

        これは、最初にスキーマを構築しようとしたときに解決できなかったForwardRefが注釈の1つであり、自動再構築が失敗した場合に必要になることがあります。

        Args:
            force: モデルスキーマの再構築を強制するかどうか。デフォルトは`False`です。
            raise_errors: エラーを発生させるかどうか。デフォルトは`True`です。
            _parent_namespace_depth: 親ネームスペースのデプスレベル。デフォルトは2です。
            _types_namespace: タイプの名前空間で、デフォルトは`None`です。


        Returns:
            スキーマが既に"完了"していて、再構築が必要なかった場合は`None`を返します。
            rebuilding_was_requiredの場合、再構築が成功した場合は`True`を返し、それ以外の場合は`False`を返します。
        """
        if not force and cls.__pydantic_complete__:
            return None
        else:
            if '__pydantic_core_schema__' in cls.__dict__:
                delattr(cls, '__pydantic_core_schema__')  # delete cached value to ensure full rebuild happens
            if _types_namespace is not None:
                types_namespace: dict[str, Any] | None = _types_namespace.copy()
            else:
                if _parent_namespace_depth > 0:
                    frame_parent_ns = _typing_extra.parent_frame_namespace(parent_depth=_parent_namespace_depth) or {}
                    cls_parent_ns = (
                        _model_construction.unpack_lenient_weakvaluedict(cls.__pydantic_parent_namespace__) or {}
                    )
                    types_namespace = {**cls_parent_ns, **frame_parent_ns}
                    cls.__pydantic_parent_namespace__ = _model_construction.build_lenient_weakvaluedict(types_namespace)
                else:
                    types_namespace = _model_construction.unpack_lenient_weakvaluedict(
                        cls.__pydantic_parent_namespace__
                    )

                types_namespace = _typing_extra.get_cls_types_namespace(cls, types_namespace)

            # manually override defer_build so complete_model_class doesn't skip building the model again
            config = {**cls.model_config, 'defer_build': False}
            return _model_construction.complete_model_class(
                cls,
                cls.__name__,
                _config.ConfigWrapper(config, check=False),
                raise_errors=raise_errors,
                types_namespace=types_namespace,
            )

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: Any | None = None,
    ) -> Self:
        """pydanticモデルインスタンスを検証します。

        Args:
            obj: 検証するオブジェクト。
            strict: 型を厳密に適用するかどうか。
            from_attributes: オブジェクト属性からデータを抽出するかどうか。
            context: バリデータに渡す追加のコンテキスト。

        Raises:
            ValidationError: オブジェクトを検証できなかった場合。

        Returns:
            検証されたモデルインスタンスです。
        """
        # `__tracebackhide__` tells pytest and some other tools to omit this function from tracebacks
        __tracebackhide__ = True
        return cls.__pydantic_validator__.validate_python(
            obj, strict=strict, from_attributes=from_attributes, context=context
        )

    @classmethod
    def model_validate_json(
        cls,
        json_data: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: Any | None = None,
    ) -> Self:
        """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/json/#json-parsing

        指定されたJSONデータをPydanticモデルに対して検証します。

        Args:
            json_data: 検証するJSONデータ。
            strict: 型を厳密に適用するかどうか。
            context: バリデータに渡す追加の変数。

        Returns:
            検証されたPydanticモデル。

        Raises:
            ValidationError: `json_data`がJSON文字列でないか、オブジェクトを検証できなかった場合。
        """
        # `__tracebackhide__` tells pytest and some other tools to omit this function from tracebacks
        __tracebackhide__ = True
        return cls.__pydantic_validator__.validate_json(json_data, strict=strict, context=context)

    @classmethod
    def model_validate_strings(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        context: Any | None = None,
    ) -> Self:
        """文字列データを持つ指定されたオブジェクトをPydanticモデルに対して検証します。

        Args:
            obj: 検証するストリング・データを含むオブジェクト。
            strict: 型を厳密に適用するかどうか。
            context: バリデータに渡す追加の変数。

        Returns:
            検証されたPydanticモデル。

        """
        # `__tracebackhide__` tells pytest and some other tools to omit this function from tracebacks
        __tracebackhide__ = True
        return cls.__pydantic_validator__.validate_strings(obj, strict=strict, context=context)

    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[BaseModel], handler: GetCoreSchemaHandler, /) -> CoreSchema:
        """モデルのCoreSchemaの生成にフックします。

        Args:
            source: スキーマを生成しているクラス。
            クラスメソッドの場合、これは通常`cls`引数と同じになります。
            handler: Pydanticの内部CoreSchema生成ロジックを呼び出す呼び出し可能オブジェクトです。

        Returns:
            `pydantic-core``CoreSchema`です。
        """
        # Only use the cached value from this _exact_ class; we don't want one from a parent class
        # This is why we check `cls.__dict__` and don't use `cls.__pydantic_core_schema__` or similar.
        schema = cls.__dict__.get('__pydantic_core_schema__')
        if schema is not None and not isinstance(schema, _mock_val_ser.MockCoreSchema):
            # Due to the way generic classes are built, it's possible that an invalid schema may be temporarily
            # set on generic classes. I think we could resolve this to ensure that we get proper schema caching
            # for generics, but for simplicity for now, we just always rebuild if the class has a generic origin.
            if not cls.__pydantic_generic_metadata__['origin']:
                return cls.__pydantic_core_schema__

        return handler(source)

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: CoreSchema,
        handler: GetJsonSchemaHandler,
        /,
    ) -> JsonSchemaValue:
        """モデルのJSONスキーマの生成にフックします。

        Args:
            core_schema: `pydantic-core`CoreSchemaです。
                この引数を無視して、新しいCoreSchemaでハンドラを呼び出すか、このCoreSchemaをラップ(`{'type':'nullable','schema':current_schema}`)するか、あるいは単に元のスキーマでハンドラを呼び出すことができます。
            handler: Pydanticの内部JSONスキーマ生成を呼び出します。
                JSONスキーマの生成に失敗した場合、`pydantic.errors.PydanticInvalidForJsonSchema`が発生します。
                これは`BaseModel.model_json_schema`によって呼び出されるので、その関数の`schema_generator`引数をオーバーライドして、型のJSONスキーマ生成をグローバルに変更できます。

        Returns:
            PythonオブジェクトとしてのJSONスキーマ。
        """
        return handler(core_schema)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """これは`__init_subclass__`と同じように動作することを意図していますが、クラスが実際に完全に初期化された後にのみ`ModelMetaclass`によって呼び出されます。特に、`model_fields`のような属性は、これが呼び出されたときに存在します。

        これが必要なのは、`__init_subclass__`は常に`type.__new__`によって呼び出され、`type.__new__`がクラスがすでに十分に初期化されているような方法で呼び出されるようにするためには、`ModelMetaclass`に対して非常に大きなリファクタリングが必要になるからです。

        これは、標準の`__init_subclass__`に渡されるのと同じ`kwargs`、つまり、pydanticが内部的に使用していないクラス定義に渡されたkwargsを受け取ります。

        Args:
            **kwargs: クラス定義に渡されるキーワード引数で、pydanticが内部的に使用しないもの。
        """
        pass

    def __class_getitem__(
        cls, typevar_values: type[Any] | tuple[type[Any], ...]
    ) -> type[BaseModel] | _forward_ref.PydanticRecursiveRef:
        cached = _generics.get_cached_generic_type_early(cls, typevar_values)
        if cached is not None:
            return cached

        if cls is BaseModel:
            raise TypeError('Type parameters should be placed on typing.Generic, not BaseModel')
        if not hasattr(cls, '__parameters__'):
            raise TypeError(f'{cls} cannot be parametrized because it does not inherit from typing.Generic')
        if not cls.__pydantic_generic_metadata__['parameters'] and typing.Generic not in cls.__bases__:
            raise TypeError(f'{cls} is not a generic class')

        if not isinstance(typevar_values, tuple):
            typevar_values = (typevar_values,)
        _generics.check_parameters_count(cls, typevar_values)

        # Build map from generic typevars to passed params
        typevars_map: dict[_typing_extra.TypeVarType, type[Any]] = dict(
            zip(cls.__pydantic_generic_metadata__['parameters'], typevar_values)
        )

        if _utils.all_identical(typevars_map.keys(), typevars_map.values()) and typevars_map:
            submodel = cls  # if arguments are equal to parameters it's the same object
            _generics.set_cached_generic_type(cls, typevar_values, submodel)
        else:
            parent_args = cls.__pydantic_generic_metadata__['args']
            if not parent_args:
                args = typevar_values
            else:
                args = tuple(_generics.replace_types(arg, typevars_map) for arg in parent_args)

            origin = cls.__pydantic_generic_metadata__['origin'] or cls
            model_name = origin.model_parametrized_name(args)
            params = tuple(
                {param: None for param in _generics.iter_contained_typevars(typevars_map.values())}
            )  # use dict as ordered set

            with _generics.generic_recursion_self_type(origin, args) as maybe_self_type:
                if maybe_self_type is not None:
                    return maybe_self_type

                cached = _generics.get_cached_generic_type_late(cls, typevar_values, origin, args)
                if cached is not None:
                    return cached

                # Attempt to rebuild the origin in case new types have been defined
                try:
                    # depth 3 gets you above this __class_getitem__ call
                    origin.model_rebuild(_parent_namespace_depth=3)
                except PydanticUndefinedAnnotation:
                    # It's okay if it fails, it just means there are still undefined types
                    # that could be evaluated later.
                    # TODO: Make sure validation fails if there are still undefined types, perhaps using MockValidator
                    pass

                submodel = _generics.create_generic_submodel(model_name, origin, args, params)

                # Update cache
                _generics.set_cached_generic_type(cls, typevar_values, submodel, origin, args)

        return submodel

    def __copy__(self) -> Self:
        """モデルのシャローコピーを返します。"""
        cls = type(self)
        m = cls.__new__(cls)
        _object_setattr(m, '__dict__', copy(self.__dict__))
        _object_setattr(m, '__pydantic_extra__', copy(self.__pydantic_extra__))
        _object_setattr(m, '__pydantic_fields_set__', copy(self.__pydantic_fields_set__))

        if not hasattr(self, '__pydantic_private__') or self.__pydantic_private__ is None:
            _object_setattr(m, '__pydantic_private__', None)
        else:
            _object_setattr(
                m,
                '__pydantic_private__',
                {k: v for k, v in self.__pydantic_private__.items() if v is not PydanticUndefined},
            )

        return m

    def __deepcopy__(self, memo: dict[int, Any] | None = None) -> Self:
        """モデルのディープコピーを返します。"""
        cls = type(self)
        m = cls.__new__(cls)
        _object_setattr(m, '__dict__', deepcopy(self.__dict__, memo=memo))
        _object_setattr(m, '__pydantic_extra__', deepcopy(self.__pydantic_extra__, memo=memo))
        # This next line doesn't need a deepcopy because __pydantic_fields_set__ is a set[str],
        # and attempting a deepcopy would be marginally slower.
        _object_setattr(m, '__pydantic_fields_set__', copy(self.__pydantic_fields_set__))

        if not hasattr(self, '__pydantic_private__') or self.__pydantic_private__ is None:
            _object_setattr(m, '__pydantic_private__', None)
        else:
            _object_setattr(
                m,
                '__pydantic_private__',
                deepcopy({k: v for k, v in self.__pydantic_private__.items() if v is not PydanticUndefined}, memo=memo),
            )

        return m

    if not TYPE_CHECKING:
        # We put `__getattr__` in a non-TYPE_CHECKING block because otherwise, mypy allows arbitrary attribute access
        # The same goes for __setattr__ and __delattr__, see: https://github.com/pydantic/pydantic/issues/8643

        def __getattr__(self, item: str) -> Any:
            private_attributes = object.__getattribute__(self, '__private_attributes__')
            if item in private_attributes:
                attribute = private_attributes[item]
                if hasattr(attribute, '__get__'):
                    return attribute.__get__(self, type(self))  # type: ignore

                try:
                    # Note: self.__pydantic_private__ cannot be None if self.__private_attributes__ has items
                    return self.__pydantic_private__[item]  # type: ignore
                except KeyError as exc:
                    raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
            else:
                # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
                # See `BaseModel.__repr_args__` for more details
                try:
                    pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
                except AttributeError:
                    pydantic_extra = None

                if pydantic_extra:
                    try:
                        return pydantic_extra[item]
                    except KeyError as exc:
                        raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
                else:
                    if hasattr(self.__class__, item):
                        return super().__getattribute__(item)  # Raises AttributeError if appropriate
                    else:
                        # this is the current error
                        raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')

        def __setattr__(self, name: str, value: Any) -> None:
            if name in self.__class_vars__:
                raise AttributeError(
                    f'{name!r} is a ClassVar of `{self.__class__.__name__}` and cannot be set on an instance. '
                    f'If you want to set a value on the class, use `{self.__class__.__name__}.{name} = value`.'
                )
            elif not _fields.is_valid_field_name(name):
                if self.__pydantic_private__ is None or name not in self.__private_attributes__:
                    _object_setattr(self, name, value)
                else:
                    attribute = self.__private_attributes__[name]
                    if hasattr(attribute, '__set__'):
                        attribute.__set__(self, value)  # type: ignore
                    else:
                        self.__pydantic_private__[name] = value
                return

            self._check_frozen(name, value)

            attr = getattr(self.__class__, name, None)
            if isinstance(attr, property):
                attr.__set__(self, value)
            elif self.model_config.get('validate_assignment', None):
                self.__pydantic_validator__.validate_assignment(self, name, value)
            elif self.model_config.get('extra') != 'allow' and name not in self.model_fields:
                # TODO - matching error
                raise ValueError(f'"{self.__class__.__name__}" object has no field "{name}"')
            elif self.model_config.get('extra') == 'allow' and name not in self.model_fields:
                if self.model_extra and name in self.model_extra:
                    self.__pydantic_extra__[name] = value  # type: ignore
                else:
                    try:
                        getattr(self, name)
                    except AttributeError:
                        # attribute does not already exist on instance, so put it in extra
                        self.__pydantic_extra__[name] = value  # type: ignore
                    else:
                        # attribute _does_ already exist on instance, and was not in extra, so update it
                        _object_setattr(self, name, value)
            else:
                self.__dict__[name] = value
                self.__pydantic_fields_set__.add(name)

        def __delattr__(self, item: str) -> Any:
            if item in self.__private_attributes__:
                attribute = self.__private_attributes__[item]
                if hasattr(attribute, '__delete__'):
                    attribute.__delete__(self)  # type: ignore
                    return

                try:
                    # Note: self.__pydantic_private__ cannot be None if self.__private_attributes__ has items
                    del self.__pydantic_private__[item]  # type: ignore
                    return
                except KeyError as exc:
                    raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc

            self._check_frozen(item, None)

            if item in self.model_fields:
                object.__delattr__(self, item)
            elif self.__pydantic_extra__ is not None and item in self.__pydantic_extra__:
                del self.__pydantic_extra__[item]
            else:
                try:
                    object.__delattr__(self, item)
                except AttributeError:
                    raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')

    def _check_frozen(self, name: str, value: Any) -> None:
        if self.model_config.get('frozen', None):
            typ = 'frozen_instance'
        elif getattr(self.model_fields.get(name), 'frozen', False):
            typ = 'frozen_field'
        else:
            return
        error: pydantic_core.InitErrorDetails = {
            'type': typ,
            'loc': (name,),
            'input': value,
        }
        raise pydantic_core.ValidationError.from_exception_data(self.__class__.__name__, [error])

    def __getstate__(self) -> dict[Any, Any]:
        private = self.__pydantic_private__
        if private:
            private = {k: v for k, v in private.items() if v is not PydanticUndefined}
        return {
            '__dict__': self.__dict__,
            '__pydantic_extra__': self.__pydantic_extra__,
            '__pydantic_fields_set__': self.__pydantic_fields_set__,
            '__pydantic_private__': private,
        }

    def __setstate__(self, state: dict[Any, Any]) -> None:
        _object_setattr(self, '__pydantic_fields_set__', state.get('__pydantic_fields_set__', {}))
        _object_setattr(self, '__pydantic_extra__', state.get('__pydantic_extra__', {}))
        _object_setattr(self, '__pydantic_private__', state.get('__pydantic_private__', {}))
        _object_setattr(self, '__dict__', state.get('__dict__', {}))

    if not TYPE_CHECKING:

        def __eq__(self, other: Any) -> bool:
            if isinstance(other, BaseModel):
                # When comparing instances of generic types for equality, as long as all field values are equal,
                # only require their generic origin types to be equal, rather than exact type equality.
                # This prevents headaches like MyGeneric(x=1) != MyGeneric[Any](x=1).
                self_type = self.__pydantic_generic_metadata__['origin'] or self.__class__
                other_type = other.__pydantic_generic_metadata__['origin'] or other.__class__

                # Perform common checks first
                if not (
                    self_type == other_type
                    and getattr(self, '__pydantic_private__', None) == getattr(other, '__pydantic_private__', None)
                    and self.__pydantic_extra__ == other.__pydantic_extra__
                ):
                    return False

                # We only want to compare pydantic fields but ignoring fields is costly.
                # We'll perform a fast check first, and fallback only when needed
                # See GH-7444 and GH-7825 for rationale and a performance benchmark

                # First, do the fast (and sometimes faulty) __dict__ comparison
                if self.__dict__ == other.__dict__:
                    # If the check above passes, then pydantic fields are equal, we can return early
                    return True

                # We don't want to trigger unnecessary costly filtering of __dict__ on all unequal objects, so we return
                # early if there are no keys to ignore (we would just return False later on anyway)
                model_fields = type(self).model_fields.keys()
                if self.__dict__.keys() <= model_fields and other.__dict__.keys() <= model_fields:
                    return False

                # If we reach here, there are non-pydantic-fields keys, mapped to unequal values, that we need to ignore
                # Resort to costly filtering of the __dict__ objects
                # We use operator.itemgetter because it is much faster than dict comprehensions
                # NOTE: Contrary to standard python class and instances, when the Model class has a default value for an
                # attribute and the model instance doesn't have a corresponding attribute, accessing the missing attribute
                # raises an error in BaseModel.__getattr__ instead of returning the class attribute
                # So we can use operator.itemgetter() instead of operator.attrgetter()
                getter = operator.itemgetter(*model_fields) if model_fields else lambda _: _utils._SENTINEL
                try:
                    return getter(self.__dict__) == getter(other.__dict__)
                except KeyError:
                    # In rare cases (such as when using the deprecated BaseModel.copy() method),
                    # the __dict__ may not contain all model fields, which is how we can get here.
                    # getter(self.__dict__) is much faster than any 'safe' method that accounts
                    # for missing keys, and wrapping it in a `try` doesn't slow things down much
                    # in the common case.
                    self_fields_proxy = _utils.SafeGetItemProxy(self.__dict__)
                    other_fields_proxy = _utils.SafeGetItemProxy(other.__dict__)
                    return getter(self_fields_proxy) == getter(other_fields_proxy)

            # other instance is not a BaseModel
            else:
                return NotImplemented  # delegate to the other item in the comparison

    if TYPE_CHECKING:
        # We put `__init_subclass__` in a TYPE_CHECKING block because, even though we want the type-checking benefits
        # described in the signature of `__init_subclass__` below, we don't want to modify the default behavior of
        # subclass initialization.

        def __init_subclass__(cls, **kwargs: Unpack[ConfigDict]):
            """このシグネチャは、型チェッカーがクラス宣言の引数をチェックするのを助けるためだけに含まれており、model_configのキーと値のペアを簡単に設定する方法を提供します。

            ```py
            from pydantic import BaseModel

            class MyModel(BaseModel, extra='allow'):
                ...
            ```

            しかし、`__init_subclass__`の_actual_callsはconfig引数を受け取らず、クラスの初期化中に渡されたConfigDictの_not_expectedキーであるキーワード引数のみを受け取るので、これはごまかしかもしれません(これは`ModelMetaclass.__new__`の動作によるものです)。

            Args:
                **kwargs: クラス定義に渡されるキーワード引数で、model_config

            Note:
                代わりに`__pydantic_init_subclass__`をオーバーライドすることもできます。これは同様に動作しますが、クラスが完全に初期化された*後*に呼び出されます。
            """

    def __iter__(self) -> TupleGenerator:
        """dict(model)`は動作します。"""
        yield from [(k, v) for (k, v) in self.__dict__.items() if not k.startswith('_')]
        extra = self.__pydantic_extra__
        if extra:
            yield from extra.items()

    def __repr__(self) -> str:
        return f'{self.__repr_name__()}({self.__repr_str__(", ")})'

    def __repr_args__(self) -> _repr.ReprArgs:
        for k, v in self.__dict__.items():
            field = self.model_fields.get(k)
            if field and field.repr:
                yield k, v

        # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
        # This can happen if a `ValidationError` is raised during initialization and the instance's
        # repr is generated as part of the exception handling. Therefore, we use `getattr` here
        # with a fallback, even though the type hints indicate the attribute will always be present.
        try:
            pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
        except AttributeError:
            pydantic_extra = None

        if pydantic_extra is not None:
            yield from ((k, v) for k, v in pydantic_extra.items())
        yield from ((k, getattr(self, k)) for k, v in self.model_computed_fields.items() if v.repr)

    # take logic from `_repr.Representation` without the side effects of inheritance, see #5740
    __repr_name__ = _repr.Representation.__repr_name__
    __repr_str__ = _repr.Representation.__repr_str__
    __pretty__ = _repr.Representation.__pretty__
    __rich_repr__ = _repr.Representation.__rich_repr__

    def __str__(self) -> str:
        return self.__repr_str__(' ')

    # ##### Deprecated methods from v1 #####
    @property
    @typing_extensions.deprecated(
        'The `__fields__` attribute is deprecated, use `model_fields` instead.', category=None
    )
    def __fields__(self) -> dict[str, FieldInfo]:
        warnings.warn(
            'The `__fields__` attribute is deprecated, use `model_fields` instead.', category=PydanticDeprecatedSince20
        )
        return self.model_fields

    @property
    @typing_extensions.deprecated(
        'The `__fields_set__` attribute is deprecated, use `model_fields_set` instead.',
        category=None,
    )
    def __fields_set__(self) -> set[str]:
        warnings.warn(
            'The `__fields_set__` attribute is deprecated, use `model_fields_set` instead.',
            category=PydanticDeprecatedSince20,
        )
        return self.__pydantic_fields_set__

    @typing_extensions.deprecated('The `dict` method is deprecated; use `model_dump` instead.', category=None)
    def dict(  # noqa: D102
        self,
        *,
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Dict[str, Any]:  # noqa UP006
        warnings.warn('The `dict` method is deprecated; use `model_dump` instead.', category=PydanticDeprecatedSince20)
        return self.model_dump(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    @typing_extensions.deprecated('The `json` method is deprecated; use `model_dump_json` instead.', category=None)
    def json(  # noqa: D102
        self,
        *,
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        encoder: Callable[[Any], Any] | None = PydanticUndefined,  # type: ignore[assignment]
        models_as_dict: bool = PydanticUndefined,  # type: ignore[assignment]
        **dumps_kwargs: Any,
    ) -> str:
        warnings.warn(
            'The `json` method is deprecated; use `model_dump_json` instead.', category=PydanticDeprecatedSince20
        )
        if encoder is not PydanticUndefined:
            raise TypeError('The `encoder` argument is no longer supported; use field serializers instead.')
        if models_as_dict is not PydanticUndefined:
            raise TypeError('The `models_as_dict` argument is no longer supported; use a model serializer instead.')
        if dumps_kwargs:
            raise TypeError('`dumps_kwargs` keyword arguments are no longer supported.')
        return self.model_dump_json(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    @classmethod
    @typing_extensions.deprecated('The `parse_obj` method is deprecated; use `model_validate` instead.', category=None)
    def parse_obj(cls, obj: Any) -> Self:  # noqa: D102
        warnings.warn(
            'The `parse_obj` method is deprecated; use `model_validate` instead.', category=PydanticDeprecatedSince20
        )
        return cls.model_validate(obj)

    @classmethod
    @typing_extensions.deprecated(
        'The `parse_raw` method is deprecated; if your data is JSON use `model_validate_json`, '
        'otherwise load the data then use `model_validate` instead.',
        category=None,
    )
    def parse_raw(  # noqa: D102
        cls,
        b: str | bytes,
        *,
        content_type: str | None = None,
        encoding: str = 'utf8',
        proto: DeprecatedParseProtocol | None = None,
        allow_pickle: bool = False,
    ) -> Self:  # pragma: no cover
        warnings.warn(
            'The `parse_raw` method is deprecated; if your data is JSON use `model_validate_json`, '
            'otherwise load the data then use `model_validate` instead.',
            category=PydanticDeprecatedSince20,
        )
        from .deprecated import parse

        try:
            obj = parse.load_str_bytes(
                b,
                proto=proto,
                content_type=content_type,
                encoding=encoding,
                allow_pickle=allow_pickle,
            )
        except (ValueError, TypeError) as exc:
            import json

            # try to match V1
            if isinstance(exc, UnicodeDecodeError):
                type_str = 'value_error.unicodedecode'
            elif isinstance(exc, json.JSONDecodeError):
                type_str = 'value_error.jsondecode'
            elif isinstance(exc, ValueError):
                type_str = 'value_error'
            else:
                type_str = 'type_error'

            # ctx is missing here, but since we've added `input` to the error, we're not pretending it's the same
            error: pydantic_core.InitErrorDetails = {
                # The type: ignore on the next line is to ignore the requirement of LiteralString
                'type': pydantic_core.PydanticCustomError(type_str, str(exc)),  # type: ignore
                'loc': ('__root__',),
                'input': b,
            }
            raise pydantic_core.ValidationError.from_exception_data(cls.__name__, [error])
        return cls.model_validate(obj)

    @classmethod
    @typing_extensions.deprecated(
        'The `parse_file` method is deprecated; load the data from file, then if your data is JSON '
        'use `model_validate_json`, otherwise `model_validate` instead.',
        category=None,
    )
    def parse_file(  # noqa: D102
        cls,
        path: str | Path,
        *,
        content_type: str | None = None,
        encoding: str = 'utf8',
        proto: DeprecatedParseProtocol | None = None,
        allow_pickle: bool = False,
    ) -> Self:
        warnings.warn(
            'The `parse_file` method is deprecated; load the data from file, then if your data is JSON '
            'use `model_validate_json`, otherwise `model_validate` instead.',
            category=PydanticDeprecatedSince20,
        )
        from .deprecated import parse

        obj = parse.load_file(
            path,
            proto=proto,
            content_type=content_type,
            encoding=encoding,
            allow_pickle=allow_pickle,
        )
        return cls.parse_obj(obj)

    @classmethod
    @typing_extensions.deprecated(
        'The `from_orm` method is deprecated; set '
        "`model_config['from_attributes']=True` and use `model_validate` instead.",
        category=None,
    )
    def from_orm(cls, obj: Any) -> Self:  # noqa: D102
        warnings.warn(
            'The `from_orm` method is deprecated; set '
            "`model_config['from_attributes']=True` and use `model_validate` instead.",
            category=PydanticDeprecatedSince20,
        )
        if not cls.model_config.get('from_attributes', None):
            raise PydanticUserError(
                'You must set the config attribute `from_attributes=True` to use from_orm', code=None
            )
        return cls.model_validate(obj)

    @classmethod
    @typing_extensions.deprecated('The `construct` method is deprecated; use `model_construct` instead.', category=None)
    def construct(cls, _fields_set: set[str] | None = None, **values: Any) -> Self:  # noqa: D102
        warnings.warn(
            'The `construct` method is deprecated; use `model_construct` instead.', category=PydanticDeprecatedSince20
        )
        return cls.model_construct(_fields_set=_fields_set, **values)

    @typing_extensions.deprecated(
        'The `copy` method is deprecated; use `model_copy` instead. '
        'See the docstring of `BaseModel.copy` for details about how to handle `include` and `exclude`.',
        category=None,
    )
    def copy(
        self,
        *,
        include: AbstractSetIntStr | MappingIntStrAny | None = None,
        exclude: AbstractSetIntStr | MappingIntStrAny | None = None,
        update: Dict[str, Any] | None = None,  # noqa UP006
        deep: bool = False,
    ) -> Self:  # pragma: no cover
        """モデルのコピーを戻します。

        !!! warning "Deprecated"
            このメソッドは廃止されました。代わりに`model_copy`を使用してください。

        `include`または`exclude`が必要な場合は、次のようにします。

        ```py
        data = self.model_dump(include=include, exclude=exclude, round_trip=True)
        data = {**data, **(update or {})}
        copied = self.model_validate(data)
        ```

        Args:
            include: コピーされたモデルに含めるフィールドを指定するオプションのセットまたはマッピング。
            exclude: コピーされたモデルで除外するフィールドを指定するオプションのセットまたはマッピング。
            update: コピーされたモデルのフィールド値を上書きするためのフィールド値ペアのオプション辞書。
            deep: Trueの場合、Pydanticモデルであるフィールドの値がディープコピーされます。

        Returns:
            指定されたフィールドが含まれ、除外され、更新されたモデルのコピー。
        """
        warnings.warn(
            'The `copy` method is deprecated; use `model_copy` instead. '
            'See the docstring of `BaseModel.copy` for details about how to handle `include` and `exclude`.',
            category=PydanticDeprecatedSince20,
        )
        from .deprecated import copy_internals

        values = dict(
            copy_internals._iter(
                self, to_dict=False, by_alias=False, include=include, exclude=exclude, exclude_unset=False
            ),
            **(update or {}),
        )
        if self.__pydantic_private__ is None:
            private = None
        else:
            private = {k: v for k, v in self.__pydantic_private__.items() if v is not PydanticUndefined}

        if self.__pydantic_extra__ is None:
            extra: dict[str, Any] | None = None
        else:
            extra = self.__pydantic_extra__.copy()
            for k in list(self.__pydantic_extra__):
                if k not in values:  # k was in the exclude
                    extra.pop(k)
            for k in list(values):
                if k in self.__pydantic_extra__:  # k must have come from extra
                    extra[k] = values.pop(k)

        # new `__pydantic_fields_set__` can have unset optional fields with a set value in `update` kwarg
        if update:
            fields_set = self.__pydantic_fields_set__ | update.keys()
        else:
            fields_set = set(self.__pydantic_fields_set__)

        # removing excluded fields from `__pydantic_fields_set__`
        if exclude:
            fields_set -= set(exclude)

        return copy_internals._copy_and_set_values(self, values, fields_set, extra, private, deep=deep)

    @classmethod
    @typing_extensions.deprecated('The `schema` method is deprecated; use `model_json_schema` instead.', category=None)
    def schema(  # noqa: D102
        cls, by_alias: bool = True, ref_template: str = DEFAULT_REF_TEMPLATE
    ) -> Dict[str, Any]:  # noqa UP006
        warnings.warn(
            'The `schema` method is deprecated; use `model_json_schema` instead.', category=PydanticDeprecatedSince20
        )
        return cls.model_json_schema(by_alias=by_alias, ref_template=ref_template)

    @classmethod
    @typing_extensions.deprecated(
        'The `schema_json` method is deprecated; use `model_json_schema` and json.dumps instead.',
        category=None,
    )
    def schema_json(  # noqa: D102
        cls, *, by_alias: bool = True, ref_template: str = DEFAULT_REF_TEMPLATE, **dumps_kwargs: Any
    ) -> str:  # pragma: no cover
        warnings.warn(
            'The `schema_json` method is deprecated; use `model_json_schema` and json.dumps instead.',
            category=PydanticDeprecatedSince20,
        )
        import json

        from .deprecated.json import pydantic_encoder

        return json.dumps(
            cls.model_json_schema(by_alias=by_alias, ref_template=ref_template),
            default=pydantic_encoder,
            **dumps_kwargs,
        )

    @classmethod
    @typing_extensions.deprecated('The `validate` method is deprecated; use `model_validate` instead.', category=None)
    def validate(cls, value: Any) -> Self:  # noqa: D102
        warnings.warn(
            'The `validate` method is deprecated; use `model_validate` instead.', category=PydanticDeprecatedSince20
        )
        return cls.model_validate(value)

    @classmethod
    @typing_extensions.deprecated(
        'The `update_forward_refs` method is deprecated; use `model_rebuild` instead.',
        category=None,
    )
    def update_forward_refs(cls, **localns: Any) -> None:  # noqa: D102
        warnings.warn(
            'The `update_forward_refs` method is deprecated; use `model_rebuild` instead.',
            category=PydanticDeprecatedSince20,
        )
        if localns:  # pragma: no cover
            raise TypeError('`localns` arguments are not longer accepted.')
        cls.model_rebuild(force=True)

    @typing_extensions.deprecated(
        'The private method `_iter` will be removed and should no longer be used.', category=None
    )
    def _iter(self, *args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            'The private method `_iter` will be removed and should no longer be used.',
            category=PydanticDeprecatedSince20,
        )
        from .deprecated import copy_internals

        return copy_internals._iter(self, *args, **kwargs)

    @typing_extensions.deprecated(
        'The private method `_copy_and_set_values` will be removed and should no longer be used.',
        category=None,
    )
    def _copy_and_set_values(self, *args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            'The private method `_copy_and_set_values` will be removed and should no longer be used.',
            category=PydanticDeprecatedSince20,
        )
        from .deprecated import copy_internals

        return copy_internals._copy_and_set_values(self, *args, **kwargs)

    @classmethod
    @typing_extensions.deprecated(
        'The private method `_get_value` will be removed and should no longer be used.',
        category=None,
    )
    def _get_value(cls, *args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            'The private method `_get_value` will be removed and should no longer be used.',
            category=PydanticDeprecatedSince20,
        )
        from .deprecated import copy_internals

        return copy_internals._get_value(cls, *args, **kwargs)

    @typing_extensions.deprecated(
        'The private method `_calculate_keys` will be removed and should no longer be used.',
        category=None,
    )
    def _calculate_keys(self, *args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            'The private method `_calculate_keys` will be removed and should no longer be used.',
            category=PydanticDeprecatedSince20,
        )
        from .deprecated import copy_internals

        return copy_internals._calculate_keys(self, *args, **kwargs)


@overload
def create_model(
    model_name: str,
    /,
    *,
    __config__: ConfigDict | None = None,
    __doc__: str | None = None,
    __base__: None = None,
    __module__: str = __name__,
    __validators__: dict[str, Callable[..., Any]] | None = None,
    __cls_kwargs__: dict[str, Any] | None = None,
    **field_definitions: Any,
) -> type[BaseModel]: ...


@overload
def create_model(
    model_name: str,
    /,
    *,
    __config__: ConfigDict | None = None,
    __doc__: str | None = None,
    __base__: type[ModelT] | tuple[type[ModelT], ...],
    __module__: str = __name__,
    __validators__: dict[str, Callable[..., Any]] | None = None,
    __cls_kwargs__: dict[str, Any] | None = None,
    **field_definitions: Any,
) -> type[ModelT]: ...


def create_model(  # noqa: C901
    model_name: str,
    /,
    *,
    __config__: ConfigDict | None = None,
    __doc__: str | None = None,
    __base__: type[ModelT] | tuple[type[ModelT], ...] | None = None,
    __module__: str | None = None,
    __validators__: dict[str, Callable[..., Any]] | None = None,
    __cls_kwargs__: dict[str, Any] | None = None,
    __slots__: tuple[str, ...] | None = None,
    **field_definitions: Any,
) -> type[ModelT]:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/pydantic-docs-ja/models/#dynamic-model-creation

    新しいPydanticモデルを動的に作成して返します。言い換えれば、`create_model`は[`BaseModel`][pydantic.BaseModel]のサブクラスを動的に作成します。

    Args:
        model_name: 新しく作成されたモデルの名前。
        __config__: 新しいモデルの構成。
        __doc__: 新しいモデルのdocstring。
        __base__: 新しいモデルの1つまたは複数の基本クラス。
        __module__: モデルが属するモジュールの名前。`None`の場合、値は`sys._getframe(1)`から取得されます。
        __validators__: フィールドを検証するメソッドのディクショナリです。キーはモデルに追加される検証メソッドの名前で、値は検証メソッド自体です。関数型バリデータの詳細については、[ここ](https: //docs.pydantic.dev/2.8/concepts/validators/#field-validators)を参照してください。
        __cls_kwargs__: `metaclass`など、クラスを作成するためのキーワード引数の辞書です。
        __slots__: 非推奨です。`create_model`に渡すべきではありません。
        **field_definitions: 新しいモデルの属性です。次の形式で渡されます。`<name>=(<type>,<default value>)`、`<name>=(<type>,<FieldInfo>)`、`typing.Annotated[<type>,<FieldInfo>]`のいずれかです。`typing.Annotated[<type>,<FieldInfo>,...]`の追加のメタデータは無視されます。

    Returns:
        新しい[model][pydantic.BaseModel]です。

    Raises:
        PydantictUserError: `__base__`と`__config__`の両方が渡された場合。
    """
    if __slots__ is not None:
        # __slots__ will be ignored from here on
        warnings.warn('__slots__ should not be passed to create_model', RuntimeWarning)

    if __base__ is not None:
        if __config__ is not None:
            raise PydanticUserError(
                'to avoid confusion `__config__` and `__base__` cannot be used together',
                code='create-model-config-base',
            )
        if not isinstance(__base__, tuple):
            __base__ = (__base__,)
    else:
        __base__ = (cast('type[ModelT]', BaseModel),)

    __cls_kwargs__ = __cls_kwargs__ or {}

    fields = {}
    annotations = {}

    for f_name, f_def in field_definitions.items():
        if not _fields.is_valid_field_name(f_name):
            warnings.warn(f'fields may not start with an underscore, ignoring "{f_name}"', RuntimeWarning)
        if isinstance(f_def, tuple):
            f_def = cast('tuple[str, Any]', f_def)
            try:
                f_annotation, f_value = f_def
            except ValueError as e:
                raise PydanticUserError(
                    'Field definitions should be a `(<type>, <default>)`.',
                    code='create-model-field-definitions',
                ) from e

        elif _typing_extra.is_annotated(f_def):
            (f_annotation, f_value, *_) = typing_extensions.get_args(
                f_def
            )  # first two input are expected from Annotated, refer to https://docs.python.org/3/library/typing.html#typing.Annotated
            from .fields import FieldInfo

            if not isinstance(f_value, FieldInfo):
                raise PydanticUserError(
                    'Field definitions should be a Annotated[<type>, <FieldInfo>]',
                    code='create-model-field-definitions',
                )

        else:
            f_annotation, f_value = None, f_def

        if f_annotation:
            annotations[f_name] = f_annotation
        fields[f_name] = f_value

    if __module__ is None:
        f = sys._getframe(1)
        __module__ = f.f_globals['__name__']

    namespace: dict[str, Any] = {'__annotations__': annotations, '__module__': __module__}
    if __doc__:
        namespace.update({'__doc__': __doc__})
    if __validators__:
        namespace.update(__validators__)
    namespace.update(fields)
    if __config__:
        namespace['model_config'] = _config.ConfigWrapper(__config__).config_dict
    resolved_bases = types.resolve_bases(__base__)
    meta, ns, kwds = types.prepare_class(model_name, resolved_bases, kwds=__cls_kwargs__)
    if resolved_bases is not __base__:
        ns['__orig_bases__'] = __base__
    namespace.update(ns)

    return meta(
        model_name,
        resolved_bases,
        namespace,
        __pydantic_reset_parent_namespace__=False,
        _create_model_module=__module__,
        **kwds,
    )


__getattr__ = getattr_migration(__name__)
