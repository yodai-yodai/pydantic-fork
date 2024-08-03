"""Defining fields on models."""

from __future__ import annotations as _annotations

import dataclasses
import inspect
import sys
import typing
from copy import copy
from dataclasses import Field as DataclassField
from functools import cached_property
from typing import Any, ClassVar
from warnings import warn

import annotated_types
import typing_extensions
from pydantic_core import PydanticUndefined
from typing_extensions import Literal, TypeAlias, Unpack, deprecated

from . import types
from ._internal import _decorators, _fields, _generics, _internal_dataclass, _repr, _typing_extra, _utils
from .aliases import AliasChoices, AliasPath
from .config import JsonDict
from .errors import PydanticUserError
from .warnings import PydanticDeprecatedSince20

if typing.TYPE_CHECKING:
    from ._internal._repr import ReprArgs
else:
    # See PyCharm issues https://youtrack.jetbrains.com/issue/PY-21915
    # and https://youtrack.jetbrains.com/issue/PY-51428
    DeprecationWarning = PydanticDeprecatedSince20

__all__ = 'Field', 'PrivateAttr', 'computed_field'


_Unset: Any = PydanticUndefined

if sys.version_info >= (3, 13):
    import warnings

    Deprecated: TypeAlias = warnings.deprecated | deprecated
else:
    Deprecated: TypeAlias = deprecated


class _FromFieldInfoInputs(typing_extensions.TypedDict, total=False):
    """このクラスは、`FieldInfo.from_field`の`**kwargs`の型チェックを追加するためだけに存在します。"""

    annotation: type[Any] | None
    default_factory: typing.Callable[[], Any] | None
    alias: str | None
    alias_priority: int | None
    validation_alias: str | AliasPath | AliasChoices | None
    serialization_alias: str | None
    title: str | None
    field_title_generator: typing_extensions.Callable[[str, FieldInfo], str] | None
    description: str | None
    examples: list[Any] | None
    exclude: bool | None
    gt: annotated_types.SupportsGt | None
    ge: annotated_types.SupportsGe | None
    lt: annotated_types.SupportsLt | None
    le: annotated_types.SupportsLe | None
    multiple_of: float | None
    strict: bool | None
    min_length: int | None
    max_length: int | None
    pattern: str | typing.Pattern[str] | None
    allow_inf_nan: bool | None
    max_digits: int | None
    decimal_places: int | None
    union_mode: Literal['smart', 'left_to_right'] | None
    discriminator: str | types.Discriminator | None
    deprecated: Deprecated | str | bool | None
    json_schema_extra: JsonDict | typing.Callable[[JsonDict], None] | None
    frozen: bool | None
    validate_default: bool | None
    repr: bool
    init: bool | None
    init_var: bool | None
    kw_only: bool | None
    coerce_numbers_to_str: bool | None
    fail_fast: bool | None


class _FieldInfoInputs(_FromFieldInfoInputs, total=False):
    """このクラスは、`FieldInfo.__init__`の`**kwargs`の型チェックを追加するためだけに存在します。"""

    default: Any


class FieldInfo(_repr.Representation):
    """このクラスはフィールドに関する情報を保持します。

    `FieldInfo`は、[`Field()`][pydantic.fields.Field]関数が明示的に使用されているかどうかにかかわらず、すべてのフィールド定義に使用されます。

    !!! warning
        一般的には`FieldInfo`を直接作成すべきではありません。[`BaseModel`][pydantic.main.BaseModel]`.model_fields`内部にアクセスするときにのみ使用する必要があります。

    Attributes:
        annotation: フィールドの型注釈。
        default: フィールドのデフォルト値。
        default_factory: フィールドのデフォルトを構成するために使用されるファクトリ関数。
        alias: フィールドのエイリアス名。
        alias_priority: フィールドのエイリアスの優先度。
        validation_alias: フィールドの検証エイリアス。
        serialization_alias: フィールドのシリアル化エイリアス。
        title: フィールドのタイトル。
        field_title_generator: フィールド名を受け取り、そのタイトルを返す呼び出し可能オブジェクト。
        description: フィールドの説明。
        examples: フィールドの例のリスト。
        exclude: モデルのシリアライゼーションからフィールドを除外するかどうか。
        discriminator: タグ付き共用体の型を識別するためのフィールド名または識別子。
        deprecated: 非推奨メッセージ、`warnings.deprecated`または`typing_extensions.deprecated`バックポートのインスタンス、またはブール値。`True`の場合、フィールドにアクセスするとデフォルトの非推奨メッセージが出力されます。
        json_schema_extra: 追加のJSONスキーマ・プロパティーを提供するためのdictまたはcallable。
        frozen: フィールドが凍結されているかどうか。
        validate_default: フィールドのデフォルト値を検証するかどうか。
        repr: モデルの表現にフィールドを含めるかどうか。
        init: フィールドをデータクラスのコンストラクタに含めるかどうか。
        init_var: フィールドがデータ・クラスのコンストラクターに含まれ、保管されないようにするかどうか。
        kw_only: データクラスのコンストラクタで、フィールドをキーワードのみの引数にするかどうか。
        metadata: メタデータ制約のリスト。
    """

    annotation: type[Any] | None
    default: Any
    default_factory: typing.Callable[[], Any] | None
    alias: str | None
    alias_priority: int | None
    validation_alias: str | AliasPath | AliasChoices | None
    serialization_alias: str | None
    title: str | None
    field_title_generator: typing.Callable[[str, FieldInfo], str] | None
    description: str | None
    examples: list[Any] | None
    exclude: bool | None
    discriminator: str | types.Discriminator | None
    deprecated: Deprecated | str | bool | None
    json_schema_extra: JsonDict | typing.Callable[[JsonDict], None] | None
    frozen: bool | None
    validate_default: bool | None
    repr: bool
    init: bool | None
    init_var: bool | None
    kw_only: bool | None
    metadata: list[Any]

    __slots__ = (
        'annotation',
        'default',
        'default_factory',
        'alias',
        'alias_priority',
        'validation_alias',
        'serialization_alias',
        'title',
        'field_title_generator',
        'description',
        'examples',
        'exclude',
        'discriminator',
        'deprecated',
        'json_schema_extra',
        'frozen',
        'validate_default',
        'repr',
        'init',
        'init_var',
        'kw_only',
        'metadata',
        '_attributes_set',
    )

    # used to convert kwargs to metadata/constraints,
    # None has a special meaning - these items are collected into a `PydanticGeneralMetadata`
    metadata_lookup: ClassVar[dict[str, typing.Callable[[Any], Any] | None]] = {
        'strict': types.Strict,
        'gt': annotated_types.Gt,
        'ge': annotated_types.Ge,
        'lt': annotated_types.Lt,
        'le': annotated_types.Le,
        'multiple_of': annotated_types.MultipleOf,
        'min_length': annotated_types.MinLen,
        'max_length': annotated_types.MaxLen,
        'pattern': None,
        'allow_inf_nan': None,
        'max_digits': None,
        'decimal_places': None,
        'union_mode': None,
        'coerce_numbers_to_str': None,
        'fail_fast': types.FailFast,
    }

    def __init__(self, **kwargs: Unpack[_FieldInfoInputs]) -> None:
        """このクラスは通常、直接初期化すべきではありません。代わりに、`pydantic.fields.Field`関数またはコンストラクタクラスメソッドの1つを使用してください。

        期待される引数の詳細については、`pydantic.fields.Field`のシグネチャを参照してください。
        """
        self._attributes_set = {k: v for k, v in kwargs.items() if v is not _Unset}
        kwargs = {k: _DefaultValues.get(k) if v is _Unset else v for k, v in kwargs.items()}  # type: ignore
        self.annotation, annotation_metadata = self._extract_metadata(kwargs.get('annotation'))

        default = kwargs.pop('default', PydanticUndefined)
        if default is Ellipsis:
            self.default = PydanticUndefined
        else:
            self.default = default

        self.default_factory = kwargs.pop('default_factory', None)

        if self.default is not PydanticUndefined and self.default_factory is not None:
            raise TypeError('cannot specify both default and default_factory')

        self.alias = kwargs.pop('alias', None)
        self.validation_alias = kwargs.pop('validation_alias', None)
        self.serialization_alias = kwargs.pop('serialization_alias', None)
        alias_is_set = any(alias is not None for alias in (self.alias, self.validation_alias, self.serialization_alias))
        self.alias_priority = kwargs.pop('alias_priority', None) or 2 if alias_is_set else None
        self.title = kwargs.pop('title', None)
        self.field_title_generator = kwargs.pop('field_title_generator', None)
        self.description = kwargs.pop('description', None)
        self.examples = kwargs.pop('examples', None)
        self.exclude = kwargs.pop('exclude', None)
        self.discriminator = kwargs.pop('discriminator', None)
        # For compatibility with FastAPI<=0.110.0, we preserve the existing value if it is not overridden
        self.deprecated = kwargs.pop('deprecated', getattr(self, 'deprecated', None))
        self.repr = kwargs.pop('repr', True)
        self.json_schema_extra = kwargs.pop('json_schema_extra', None)
        self.validate_default = kwargs.pop('validate_default', None)
        self.frozen = kwargs.pop('frozen', None)
        # currently only used on dataclasses
        self.init = kwargs.pop('init', None)
        self.init_var = kwargs.pop('init_var', None)
        self.kw_only = kwargs.pop('kw_only', None)

        self.metadata = self._collect_metadata(kwargs) + annotation_metadata  # type: ignore

    @staticmethod
    def from_field(default: Any = PydanticUndefined, **kwargs: Unpack[_FromFieldInfoInputs]) -> FieldInfo:
        """`Field`関数を使用して新しい`FieldInfo`オブジェクトを作成します。

        Args:
            default: フィールドのデフォルト値。デフォルトは"未定義"です。
            **kwargs: 追加引数の辞書。

        Raises:
            TypeError: 'annotation'がキーワード引数として渡された場合。

        Returns:
            指定されたパラメータを持つ新しいFieldInfoオブジェクト。

        Example:
            次のようにして、デフォルト値を持つフィールドを作成できます。

            ```python
            import pydantic

            class MyModel(pydantic.BaseModel):
                foo: int = pydantic.Field(4)
            ```
        """
        if 'annotation' in kwargs:
            raise TypeError('"annotation" is not permitted as a Field keyword argument')
        return FieldInfo(default=default, **kwargs)

    @staticmethod
    def from_annotation(annotation: type[Any]) -> FieldInfo:
        """生の注釈から`FieldInfo`インスタンスを作成します。

        この関数は、次のような生の注釈から`FieldInfo`を作成するために内部的に使用されます。

        ```python
        import pydantic

        class MyModel(pydantic.BaseModel):
            foo: int  # <-- like this
        ```

        また、注釈が`Annotated`のインスタンスである可能性があり、`Annotated`の(最初ではない)引数の1つが`FieldInfo`のインスタンスである場合についても説明します。次に例を示します。

        ```python
        import annotated_types
        from typing_extensions import Annotated

        import pydantic

        class MyModel(pydantic.BaseModel):
            foo: Annotated[int, annotated_types.Gt(42)]
            bar: Annotated[int, pydantic.Field(gt=42)]
        ```

        Args:
            annotation: 注釈オブジェクト。

        Returns:
            フィールドメタデータのインスタンス。
        """
        final = False
        if _typing_extra.is_finalvar(annotation):
            final = True
            if annotation is not typing_extensions.Final:
                annotation = typing_extensions.get_args(annotation)[0]

        if _typing_extra.is_annotated(annotation):
            first_arg, *extra_args = typing_extensions.get_args(annotation)
            if _typing_extra.is_finalvar(first_arg):
                final = True
            field_info_annotations = [a for a in extra_args if isinstance(a, FieldInfo)]
            field_info = FieldInfo.merge_field_infos(*field_info_annotations, annotation=first_arg)
            if field_info:
                new_field_info = copy(field_info)
                new_field_info.annotation = first_arg
                new_field_info.frozen = final or field_info.frozen
                metadata: list[Any] = []
                for a in extra_args:
                    if _typing_extra.is_deprecated_instance(a):
                        new_field_info.deprecated = a.message
                    elif not isinstance(a, FieldInfo):
                        metadata.append(a)
                    else:
                        metadata.extend(a.metadata)
                new_field_info.metadata = metadata
                return new_field_info

        return FieldInfo(annotation=annotation, frozen=final or None)  # pyright: ignore[reportArgumentType]

    @staticmethod
    def from_annotated_attribute(annotation: type[Any], default: Any) -> FieldInfo:
        """デフォルト値を持つ注釈から`FieldInfo`を作成します。

        これは、次のような場合に使用されます。

        ```python
        import annotated_types
        from typing_extensions import Annotated

        import pydantic

        class MyModel(pydantic.BaseModel):
            foo: int = 4  # <-- like this
            bar: Annotated[int, annotated_types.Gt(4)] = 4  # <-- or this
            spam: Annotated[int, pydantic.Field(gt=4)] = 4  # <-- or this
        ```

        Args:
            annotation: フィールドの型注釈。
            default: フィールドのデフォルト値。

        Returns:
            渡された値を持つフィールド・オブジェクト。
        """
        if annotation is default:
            raise PydanticUserError(
                'Error when building FieldInfo from annotated attribute. '
                "Make sure you don't have any field name clashing with a type annotation ",
                code='unevaluable-type-annotation',
            )

        final = False
        if _typing_extra.is_finalvar(annotation):
            final = True
            if annotation is not typing_extensions.Final:
                annotation = typing_extensions.get_args(annotation)[0]

        if isinstance(default, FieldInfo):
            default.annotation, annotation_metadata = FieldInfo._extract_metadata(annotation)  # pyright: ignore[reportArgumentType]
            default.metadata += annotation_metadata
            default = default.merge_field_infos(
                *[x for x in annotation_metadata if isinstance(x, FieldInfo)], default, annotation=default.annotation
            )
            default.frozen = final or default.frozen
            return default
        elif isinstance(default, dataclasses.Field):
            init_var = False
            if annotation is dataclasses.InitVar:
                init_var = True
                annotation = typing.cast(Any, Any)
            elif isinstance(annotation, dataclasses.InitVar):
                init_var = True
                annotation = annotation.type
            pydantic_field = FieldInfo._from_dataclass_field(default)
            pydantic_field.annotation, annotation_metadata = FieldInfo._extract_metadata(annotation)  # pyright: ignore[reportArgumentType]
            pydantic_field.metadata += annotation_metadata
            pydantic_field = pydantic_field.merge_field_infos(
                *[x for x in annotation_metadata if isinstance(x, FieldInfo)],
                pydantic_field,
                annotation=pydantic_field.annotation,
            )
            pydantic_field.frozen = final or pydantic_field.frozen
            pydantic_field.init_var = init_var
            pydantic_field.init = getattr(default, 'init', None)
            pydantic_field.kw_only = getattr(default, 'kw_only', None)
            return pydantic_field
        else:
            if _typing_extra.is_annotated(annotation):
                first_arg, *extra_args = typing_extensions.get_args(annotation)
                field_infos = [a for a in extra_args if isinstance(a, FieldInfo)]
                field_info = FieldInfo.merge_field_infos(*field_infos, annotation=first_arg, default=default)
                metadata: list[Any] = []
                for a in extra_args:
                    if _typing_extra.is_deprecated_instance(a):
                        field_info.deprecated = a.message
                    elif not isinstance(a, FieldInfo):
                        metadata.append(a)
                    else:
                        metadata.extend(a.metadata)
                field_info.metadata = metadata
                return field_info

            return FieldInfo(annotation=annotation, default=default, frozen=final or None)  # pyright: ignore[reportArgumentType]

    @staticmethod
    def merge_field_infos(*field_infos: FieldInfo, **overrides: Any) -> FieldInfo:
        """明示的に設定された属性のみを保持して`FieldInfo`インスタンスをマージします。

        後の`FieldInfo`インスタンスは前のインスタンスを上書きします。

        Returns:
            FieldInfo: マージされたFieldInfoインスタンス。
        """
        flattened_field_infos: list[FieldInfo] = []
        for field_info in field_infos:
            flattened_field_infos.extend(x for x in field_info.metadata if isinstance(x, FieldInfo))
            flattened_field_infos.append(field_info)
        field_infos = tuple(flattened_field_infos)
        if len(field_infos) == 1:
            # No merging necessary, but we still need to make a copy and apply the overrides
            field_info = copy(field_infos[0])
            field_info._attributes_set.update(overrides)

            default_override = overrides.pop('default', PydanticUndefined)
            if default_override is Ellipsis:
                default_override = PydanticUndefined
            if default_override is not PydanticUndefined:
                field_info.default = default_override

            for k, v in overrides.items():
                setattr(field_info, k, v)
            return field_info  # type: ignore

        merged_field_info_kwargs: dict[str, Any] = {}
        metadata = {}
        for field_info in field_infos:
            attributes_set = field_info._attributes_set.copy()

            try:
                json_schema_extra = attributes_set.pop('json_schema_extra')
                existing_json_schema_extra = merged_field_info_kwargs.get('json_schema_extra', {})

                if isinstance(existing_json_schema_extra, dict) and isinstance(json_schema_extra, dict):
                    merged_field_info_kwargs['json_schema_extra'] = {**existing_json_schema_extra, **json_schema_extra}
                else:
                    # if ever there's a case of a callable, we'll just keep the last json schema extra spec
                    merged_field_info_kwargs['json_schema_extra'] = json_schema_extra
            except KeyError:
                pass

            # later FieldInfo instances override everything except json_schema_extra from earlier FieldInfo instances
            merged_field_info_kwargs.update(attributes_set)

            for x in field_info.metadata:
                if not isinstance(x, FieldInfo):
                    metadata[type(x)] = x

        merged_field_info_kwargs.update(overrides)
        field_info = FieldInfo(**merged_field_info_kwargs)
        field_info.metadata = list(metadata.values())
        return field_info

    @staticmethod
    def _from_dataclass_field(dc_field: DataclassField[Any]) -> FieldInfo:
        """`dataclasses.Field`インスタンスから新しい`FieldInfo`インスタンスを返します。
        Args:
            dc_field: 変換する`dataclasses.Field`インスタンスです。

        Returns:
            対応する`FieldInfo`インスタンス。

        Raises:
            TypeError: `FieldInfo`kwargsのいずれかが`dataclass.Field`kwargsと一致しない場合。
        """
        default = dc_field.default
        if default is dataclasses.MISSING:
            default = _Unset

        if dc_field.default_factory is dataclasses.MISSING:
            default_factory: typing.Callable[[], Any] | None = _Unset
        else:
            default_factory = dc_field.default_factory

        # use the `Field` function so in correct kwargs raise the correct `TypeError`
        dc_field_metadata = {k: v for k, v in dc_field.metadata.items() if k in _FIELD_ARG_NAMES}
        return Field(default=default, default_factory=default_factory, repr=dc_field.repr, **dc_field_metadata)

    @staticmethod
    def _extract_metadata(annotation: type[Any] | None) -> tuple[type[Any] | None, list[Any]]:
        """注釈が`Annotated`を使用している場合、注釈からメタデータ/制約を抽出しようとします。

        Args:
            annotation: メタデータを抽出する必要がある型ヒントの注釈。

        Returns:
            抽出されたメタデータタイプと追加引数のリストを含むタプル。
        """
        if annotation is not None:
            if _typing_extra.is_annotated(annotation):
                first_arg, *extra_args = typing_extensions.get_args(annotation)
                return first_arg, list(extra_args)

        return annotation, []

    @staticmethod
    def _collect_metadata(kwargs: dict[str, Any]) -> list[Any]:
        """kwargsから注釈を収集します。

        Args:
            kwargs: 関数に渡されるキーワード引数。

        Returns:
            メタデータオブジェクトのリスト-`annotated_types.BaseMetadata`と`PydanticMetadata`の組み合わせです。
        """
        metadata: list[Any] = []
        general_metadata = {}
        for key, value in list(kwargs.items()):
            try:
                marker = FieldInfo.metadata_lookup[key]
            except KeyError:
                continue

            del kwargs[key]
            if value is not None:
                if marker is None:
                    general_metadata[key] = value
                else:
                    metadata.append(marker(value))
        if general_metadata:
            metadata.append(_fields.pydantic_general_metadata(**general_metadata))
        return metadata

    @property
    def deprecation_message(self) -> str | None:
        """発行される非推奨メッセージ、または設定されていない場合は`None`。"""
        if self.deprecated is None:
            return None
        if isinstance(self.deprecated, bool):
            return 'deprecated' if self.deprecated else None
        return self.deprecated if isinstance(self.deprecated, str) else self.deprecated.message

    def get_default(self, *, call_default_factory: bool = False) -> Any:
        """デフォルト値を取得します。

        default_factoryを呼び出すと、回避したい副作用が発生する可能性があるため、default_factory(存在する場合)を呼び出すかどうかのオプションを公開します。ただし、実際に呼び出す必要がある場合もあります(つまり、`model_construct`を使用してモデルをインスタンス化する場合)。

        Args:
            call_default_factory:default_factoryを呼び出すかどうか。デフォルトは`False`です。

        Returns:
            デフォルト値。要求された場合はデフォルトのファクトリを呼び出し、設定されていない場合は`None`を呼び出します。
        """
        if self.default_factory is None:
            return _utils.smart_deepcopy(self.default)
        elif call_default_factory:
            return self.default_factory()
        else:
            return None

    def is_required(self) -> bool:
        """フィールドが必要かどうかをチェックしてください(デフォルト値またはファクトリがないなど)。

        Returns:
            フィールドが必要な場合は`True`、そうでない場合は`False`です。
        """
        return self.default is PydanticUndefined and self.default_factory is None

    def rebuild_annotation(self) -> Any:
        """関数シグネチャで使用するために元の注釈を再構築しようとします。

        メタデータが存在する場合は、`Annotated`を使用して元の注釈に追加します。存在しない場合は、元の注釈をそのまま返します。

        メタデータがフラット化されているため、元の型に認識されないアノテーションがあったり、`pydantic.Field`を呼び出してアノテーションが付けられたりした場合など、元のアノテーションが元のまま正確に再構築されない可能性があることに注意してください。

        Returns:
            再構築された注釈。
        """
        if not self.metadata:
            return self.annotation
        else:
            # Annotated arguments must be a tuple
            return typing_extensions.Annotated[(self.annotation, *self.metadata)]  # type: ignore

    def apply_typevars_map(self, typevars_map: dict[Any, Any] | None, types_namespace: dict[str, Any] | None) -> None:
        """注釈に`typevars_map`を適用してください。

        このメソッドは、パラメータ化されたジェネリック型を分析して、型変数を具体的な型に置き換えるときに使用されます。

        このメソッドは、`typevars_map`をアノテーションにインプレイスで適用します。

        Args:
            typevars_map: 型変数をその具象型にマップする辞書。
            types_namespace: アノテーションが付けられた型に関連する型を含む辞書。

        See Also:
            pydantic._internal._generics.replace_typesは、typevarを具象型に置き換えるために使用されます。
        """
        annotation = _typing_extra.eval_type_lenient(self.annotation, types_namespace)
        self.annotation = _generics.replace_types(annotation, typevars_map)

    def __repr_args__(self) -> ReprArgs:
        yield 'annotation', _repr.PlainRepr(_repr.display_as_type(self.annotation))
        yield 'required', self.is_required()

        for s in self.__slots__:
            if s == '_attributes_set':
                continue
            if s == 'annotation':
                continue
            elif s == 'metadata' and not self.metadata:
                continue
            elif s == 'repr' and self.repr is True:
                continue
            if s == 'frozen' and self.frozen is False:
                continue
            if s == 'validation_alias' and self.validation_alias == self.alias:
                continue
            if s == 'serialization_alias' and self.serialization_alias == self.alias:
                continue
            if s == 'default' and self.default is not PydanticUndefined:
                yield 'default', self.default
            elif s == 'default_factory' and self.default_factory is not None:
                yield 'default_factory', _repr.PlainRepr(_repr.display_as_type(self.default_factory))
            else:
                value = getattr(self, s)
                if value is not None and value is not PydanticUndefined:
                    yield s, value


class _EmptyKwargs(typing_extensions.TypedDict):
    """このクラスは、型チェックが`Field`に`**extra`を渡すことについて警告することを保証するためだけに存在します。"""

_DefaultValues = dict(
    default=...,
    default_factory=None,
    alias=None,
    alias_priority=None,
    validation_alias=None,
    serialization_alias=None,
    title=None,
    description=None,
    examples=None,
    exclude=None,
    discriminator=None,
    json_schema_extra=None,
    frozen=None,
    validate_default=None,
    repr=True,
    init=None,
    init_var=None,
    kw_only=None,
    pattern=None,
    strict=None,
    gt=None,
    ge=None,
    lt=None,
    le=None,
    multiple_of=None,
    allow_inf_nan=None,
    max_digits=None,
    decimal_places=None,
    min_length=None,
    max_length=None,
    coerce_numbers_to_str=None,
)


def Field(  # noqa: C901
    default: Any = PydanticUndefined,
    *,
    default_factory: typing.Callable[[], Any] | None = _Unset,
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: str | AliasPath | AliasChoices | None = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: typing_extensions.Callable[[str, FieldInfo], str] | None = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    discriminator: str | types.Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: JsonDict | typing.Callable[[JsonDict], None] | None = _Unset,
    frozen: bool | None = _Unset,
    validate_default: bool | None = _Unset,
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | typing.Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: annotated_types.SupportsGt | None = _Unset,
    ge: annotated_types.SupportsGe | None = _Unset,
    lt: annotated_types.SupportsLt | None = _Unset,
    le: annotated_types.SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal['smart', 'left_to_right'] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs],
) -> Any:
    """Usage docs: https://docs.pydantic.dev/2.9/pydantic-docs-ja/concepts/fields

    設定可能なオブジェクトのフィールドを作成します。

    モデルスキーマまたは複雑な検証のために、フィールドに関する追加情報を提供するために使用されます。引数の中には、数値フィールド(`int`、`float`、`Decimal`)にのみ適用されるものと、`str`にのみ適用されるものがあります。

    Note:
        - `_Unset`オブジェクトは、`_DefaultValues`辞書で定義された対応する値に置き換えられます。`_Unset`オブジェクトのキーが`_DefaultValues`辞書で見つからない場合は、デフォルトで`None`になります。

    Args:
        default: フィールドが設定されていない場合のデフォルト値。
        default_factory: :func: `~datetime.utcnow`のような、デフォルト値を生成するためにコールできるもの。
        alias: エイリアスによる検証またはシリアライズ時にアトリビュートに使用する名前。スネークとキャメルケース間の変換などによく使用されます。
        alias_priority: 別名の優先度。別名ジェネレータを使用するかどうかに影響します。
        validation_alias: `alias`と似ていますが、検証にのみ影響し、シリアライゼーションには影響しません。
        serialization_alias: `alias`と似ていますが、シリアライズにのみ影響し、検証には影響しません。
        title: 人間が読めるタイトル。
        field_title_generator: フィールド名を受け取り、そのタイトルを返す呼び出し可能オブジェクト。
        description: 人間が読める形式の説明。
        examples: このフィールドの値の例。
        exclude: モデルのシリアライゼーションからフィールドを除外するかどうか。
        discriminator: タグ付き共用体の型を識別するためのフィールド名または識別子。
        deprecated: 非推奨メッセージ、`warnings.deprecated`または`typing_extensions.deprecated`バックポートのインスタンス、またはブール値。`True`の場合、フィールドにアクセスするとデフォルトの非推奨メッセージが出力されます。
        json_schema_extra: 追加のJSONスキーマ・プロパティーを提供するためのdictまたはcallable。
        frozen: フィールドが凍結されているかどうか。TRUEの場合、インスタンスの値を変更しようとするとエラーが発生します。
        validate_default: `True`の場合、インスタンスを作成するたびにデフォルト値に検証が適用されます。それ以外の場合は、パフォーマンス上の理由から、フィールドのデフォルト値は信頼され、検証されません。
        repr: フィールドを`__repr__`出力に含めるかどうかを示すブール値です。
        init: フィールドをデータクラスのコンストラクタに含めるかどうかを指定します(データクラスにのみ適用されます)。
        init_var: データ・クラスのコンストラクタにフィールドを含めるかどうか(データ・クラスにのみ適用)。
        kw_only: データクラスのコンストラクタで、フィールドをキーワードのみの引数にするかどうかを指定します(データクラスにのみ適用されます)。
        coerce_numbers_to_str: `Number`型の`str`への強制を有効にするかどうか(`strict`モードでは適用されません)。
        strict: `True`の場合、厳密な検証がフィールドに適用されます。詳細については、[Strict Mode](https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/strict_mode.md)を参照してください。
        gt: より大きい。設定する場合、値はこれより大きい必要があります。数値にのみ適用できます。
        ge: 以上。設定する場合、値はこれ以上である必要があります。数値にのみ適用できます。
        lt: より小さい。設定する場合、値はこれより小さくする必要があります。数値にのみ適用できます。
        le: 以下です。設定する場合、値はこれ以下である必要があります。数値にのみ適用できます。
        multiple_of: 値はこのの倍数である必要があります。数値にのみ適用できます。
        min_length: iterableの最小長。
        max_length: iterableの最大長。
        pattern: 文字列のパターン(正規表現)。
        allow_inf_nan: `inf`、`-inf`、`nan`を許可します。数値にのみ適用されます。
        max_digits: 文字列の最大許容桁数。
        decimal_places: 数値の小数点以下の最大桁数。
        union_mode: 共用体を検証するときに適用される方式。`smart`(デフォルト)または`left_to_right`のいずれかです。詳細については、[Union Mode](https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/unions.md#union-modes)を参照してください。
        fail_fast: `True`の場合、検証は最初のエラーで停止します。`False`の場合、すべての検証エラーが収集されます。このオプションは、反復可能な型(list、tuple、set、frozenset)にのみ適用できます。
        extra: (非推奨)JSONスキーマに含まれる追加フィールド。

            !!! warning Deprecated
                `extra`kwargsは非推奨です。代わりに`json_schema_extra`を使用してください。

    Returns:
        新しい[`FieldInfo`][pydantic.fields.FieldInfo]。返される注釈は`Any`なので、型エラーを起こすことなく型注釈付きのフィールドで`Field`を使用できます。
    """
    # Check deprecated and removed params from V1. This logic should eventually be removed.
    const = extra.pop('const', None)  # type: ignore
    if const is not None:
        raise PydanticUserError('`const` is removed, use `Literal` instead', code='removed-kwargs')

    min_items = extra.pop('min_items', None)  # type: ignore
    if min_items is not None:
        warn('`min_items` is deprecated and will be removed, use `min_length` instead', DeprecationWarning)
        if min_length in (None, _Unset):
            min_length = min_items  # type: ignore

    max_items = extra.pop('max_items', None)  # type: ignore
    if max_items is not None:
        warn('`max_items` is deprecated and will be removed, use `max_length` instead', DeprecationWarning)
        if max_length in (None, _Unset):
            max_length = max_items  # type: ignore

    unique_items = extra.pop('unique_items', None)  # type: ignore
    if unique_items is not None:
        raise PydanticUserError(
            (
                '`unique_items` is removed, use `Set` instead'
                '(this feature is discussed in https://github.com/pydantic/pydantic-core/issues/296)'
            ),
            code='removed-kwargs',
        )

    allow_mutation = extra.pop('allow_mutation', None)  # type: ignore
    if allow_mutation is not None:
        warn('`allow_mutation` is deprecated and will be removed. use `frozen` instead', DeprecationWarning)
        if allow_mutation is False:
            frozen = True

    regex = extra.pop('regex', None)  # type: ignore
    if regex is not None:
        raise PydanticUserError('`regex` is removed. use `pattern` instead', code='removed-kwargs')

    if extra:
        warn(
            'Using extra keyword arguments on `Field` is deprecated and will be removed.'
            ' Use `json_schema_extra` instead.'
            f' (Extra keys: {", ".join(k.__repr__() for k in extra.keys())})',
            DeprecationWarning,
        )
        if not json_schema_extra or json_schema_extra is _Unset:
            json_schema_extra = extra  # type: ignore

    if (
        validation_alias
        and validation_alias is not _Unset
        and not isinstance(validation_alias, (str, AliasChoices, AliasPath))
    ):
        raise TypeError('Invalid `validation_alias` type. it should be `str`, `AliasChoices`, or `AliasPath`')

    if serialization_alias in (_Unset, None) and isinstance(alias, str):
        serialization_alias = alias

    if validation_alias in (_Unset, None):
        validation_alias = alias

    include = extra.pop('include', None)  # type: ignore
    if include is not None:
        warn('`include` is deprecated and does nothing. It will be removed, use `exclude` instead', DeprecationWarning)

    return FieldInfo.from_field(
        default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        field_title_generator=field_title_generator,
        description=description,
        examples=examples,
        exclude=exclude,
        discriminator=discriminator,
        deprecated=deprecated,
        json_schema_extra=json_schema_extra,
        frozen=frozen,
        pattern=pattern,
        validate_default=validate_default,
        repr=repr,
        init=init,
        init_var=init_var,
        kw_only=kw_only,
        coerce_numbers_to_str=coerce_numbers_to_str,
        strict=strict,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        min_length=min_length,
        max_length=max_length,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        union_mode=union_mode,
        fail_fast=fail_fast,
    )


_FIELD_ARG_NAMES = set(inspect.signature(Field).parameters)
_FIELD_ARG_NAMES.remove('extra')  # do not include the varkwargs parameter


class ModelPrivateAttr(_repr.Representation):
    """クラスモデル内のプライベート属性の記述子。

    !!! warning
        一般的に、`ModelPrivateAttr`インスタンスを直接作成すべきではなく、代わりに`pydantic.fields.PrivateAttr`を使用してください(これは`FieldInfo`と`Field`に似ています)。

    Attributes:
        default: 属性のデフォルト値(指定されていない場合)。
        default_factory: 指定されていない場合に属性のデフォルト値を生成する、呼び出し可能な関数。
    """

    __slots__ = 'default', 'default_factory'

    def __init__(
        self, default: Any = PydanticUndefined, *, default_factory: typing.Callable[[], Any] | None = None
    ) -> None:
        self.default = default
        self.default_factory = default_factory

    if not typing.TYPE_CHECKING:
        # We put `__getattr__` in a non-TYPE_CHECKING block because otherwise, mypy allows arbitrary attribute access

        def __getattr__(self, item: str) -> Any:
            """This function improves compatibility with custom descriptors by ensuring delegation happens
            as expected when the default value of a private attribute is a descriptor.
            """
            if item in {'__get__', '__set__', '__delete__'}:
                if hasattr(self.default, item):
                    return getattr(self.default, item)
            raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')

    def __set_name__(self, cls: type[Any], name: str) -> None:
        """Preserve `__set_name__` protocol defined in https://peps.python.org/pep-0487."""
        default = self.default
        if default is PydanticUndefined:
            return
        set_name = getattr(default, '__set_name__', None)
        if callable(set_name):
            set_name(cls, name)

    def get_default(self) -> Any:
        """オブジェクトのデフォルト値を取得します。

        `self.default_factory`が`None`の場合、このメソッドは`self.default`オブジェクトのディープコピーを返します。

        `self.default_factory`が`None`でない場合、`self.default_factory`を呼び出し、返された値を返します。

        Returns:
            オブジェクトのデフォルト値。
        """
        return _utils.smart_deepcopy(self.default) if self.default_factory is None else self.default_factory()

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and (self.default, self.default_factory) == (
            other.default,
            other.default_factory,
        )


def PrivateAttr(
    default: Any = PydanticUndefined,
    *,
    default_factory: typing.Callable[[], Any] | None = None,
    init: Literal[False] = False,
) -> Any:
    """Usage docs: https://docs.pydantic.dev/2.9/pydantic-docs-ja/concepts/models/#private-model-attributes

    属性がプライベートに使用され、通常の検証/シリアライゼーションでは処理されないことを示します。

    private属性はPydanticによって検証されないため、タイプセーフな方法で使用するかどうかはユーザー次第です。

    プライベート属性は、モデルの`__private_attributes__`に保存されます。

    Args:
        default: 属性のデフォルト値。デフォルトは"未定義"です。
        default_factory: この属性にデフォルト値が必要な場合に呼び出される呼び出し可能オブジェクト。`default`と`default_factory`の両方が設定されている場合、エラーが発生します。
        init: 属性をデータクラスのコンストラクタに含めるかどうか。常に`False`です。

    Returns:
        [`ModelPrivateAttr`][pydantic.fields.ModelPrivateAttr]クラスのインスタンスです。

    Raises:
        ValueError: `default`と`default_factory`の両方が設定されている場合。
    """
    if default is not PydanticUndefined and default_factory is not None:
        raise TypeError('cannot specify both default and default_factory')

    return ModelPrivateAttr(
        default,
        default_factory=default_factory,
    )


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class ComputedFieldInfo:
    """pydantic-coreスキーマを構築する際にアクセスできるように、`@computed_field`からのデータのコンテナ。

    Attributes:
        decorator_repr: デコレータ文字列'@computed_field'を表すクラス変数。
        wrapped_property: ラップされた計算結果フィールド・プロパティ。
        return_type: 計算フィールド・プロパティの戻り値の型。
        alias: シリアライズ中に使用されるプロパティのエイリアス。
        alias_priority: 別名の優先度。これは、別名ジェネレータを使用するかどうかに影響します。
        title: シリアライゼーションJSONスキーマに含める計算フィールドのタイトル。
        field_title_generator: フィールド名を受け取り、そのタイトルを返す呼び出し可能オブジェクト。
        description: シリアライゼーションJSONスキーマに含める計算フィールドの説明。
        deprecated: 非推奨メッセージ、`warnings.deprecated`または`typing_extensions.deprecated`バックポートのインスタンス、またはブール値。`True`の場合、フィールドにアクセスするとデフォルトの非推奨メッセージが出力されます。
        examples: シリアライズJSONスキーマに含める計算結果フィールドの値の例。
        json_schema_extra: 追加のJSONスキーマ・プロパティーを提供するためのdictまたはcallable。
        repr: __repr__出力にフィールドを含めるかどうかを示すブール値。
    """

    decorator_repr: ClassVar[str] = '@computed_field'
    wrapped_property: property
    return_type: Any
    alias: str | None
    alias_priority: int | None
    title: str | None
    field_title_generator: typing.Callable[[str, ComputedFieldInfo], str] | None
    description: str | None
    deprecated: Deprecated | str | bool | None
    examples: list[Any] | None
    json_schema_extra: JsonDict | typing.Callable[[JsonDict], None] | None
    repr: bool

    @property
    def deprecation_message(self) -> str | None:
        """出力される非推奨メッセージ、または設定されていない場合は`None`。"""
        if self.deprecated is None:
            return None
        if isinstance(self.deprecated, bool):
            return 'deprecated' if self.deprecated else None
        return self.deprecated if isinstance(self.deprecated, str) else self.deprecated.message


def _wrapped_property_is_private(property_: cached_property | property) -> bool:  # type: ignore
    """指定されたプロパティがプライベートの場合はtrue、それ以外の場合はfalseを返します。"""
    wrapped_name: str = ''

    if isinstance(property_, property):
        wrapped_name = getattr(property_.fget, '__name__', '')
    elif isinstance(property_, cached_property):  # type: ignore
        wrapped_name = getattr(property_.func, '__name__', '')  # type: ignore

    return wrapped_name.startswith('_') and not wrapped_name.startswith('__')


# this should really be `property[T], cached_property[T]` but property is not generic unlike cached_property
# See https://github.com/python/typing/issues/985 and linked issues
PropertyT = typing.TypeVar('PropertyT')


@typing.overload
def computed_field(
    *,
    alias: str | None = None,
    alias_priority: int | None = None,
    title: str | None = None,
    field_title_generator: typing.Callable[[str, ComputedFieldInfo], str] | None = None,
    description: str | None = None,
    deprecated: Deprecated | str | bool | None = None,
    examples: list[Any] | None = None,
    json_schema_extra: JsonDict | typing.Callable[[JsonDict], None] | None = None,
    repr: bool = True,
    return_type: Any = PydanticUndefined,
) -> typing.Callable[[PropertyT], PropertyT]: ...


@typing.overload
def computed_field(__func: PropertyT) -> PropertyT: ...


def computed_field(
    func: PropertyT | None = None,
    /,
    *,
    alias: str | None = None,
    alias_priority: int | None = None,
    title: str | None = None,
    field_title_generator: typing.Callable[[str, ComputedFieldInfo], str] | None = None,
    description: str | None = None,
    deprecated: Deprecated | str | bool | None = None,
    examples: list[Any] | None = None,
    json_schema_extra: JsonDict | typing.Callable[[JsonDict], None] | None = None,
    repr: bool | None = None,
    return_type: Any = PydanticUndefined,
) -> PropertyT | typing.Callable[[PropertyT], PropertyT]:
    """Usage docs: https://docs.pydantic.dev/2.9/pydantic-docs-ja/concepts/fields#the-computed_field-decorator

    モデルまたはデータクラスをシリアライズするときに`property`と`cached_property`を含めるデコレータ。

    これは、他のフィールドから計算されるフィールドや、計算にコストがかかり、キャッシュする必要があるフィールドに便利です。

    ```py
    from pydantic import BaseModel, computed_field

    class Rectangle(BaseModel):
        width: int
        length: int

        @computed_field
        @property
        def area(self) -> int:
            return self.width * self.length

    print(Rectangle(width=3, length=2).model_dump())
    #> {'width': 3, 'length': 2, 'area': 6}
    ```

    `@property`または`@cached_property`でデコレートされていない関数に適用すると、その関数は自動的に`property`でラップされます。
    これはより簡潔ですが、IDE内のIntelliSenseが失われ、静的型チェッカーが混乱するため、`@property`を明示的に使用することをお勧めします。

    !!! warning "Mypy Warning"
        `@computed_field`の前に`@property`または`@cached_property`を関数に適用しても、mypyは`Decorated property not supported`エラーをスローすることがあります。
        詳細については、[mypy issue #1362](https://github.com/python/mypy/issues/1362)を参照してください。
        このエラーメッセージを回避するには、`@computed_field`行に`#type:ignore[misc]`を追加してください。

        [pyright](https://github.com/microsoft/pyright)はエラーなしで`@computed_field`をサポートしています。

    ```py
    import random

    from pydantic import BaseModel, computed_field

    class Square(BaseModel):
        width: float

        @computed_field
        def area(self) -> float:  # converted to a `property` by `computed_field`
            return round(self.width**2, 2)

        @area.setter
        def area(self, new_area: float) -> None:
            self.width = new_area**0.5

        @computed_field(alias='the magic number', repr=False)
        def random_number(self) -> int:
            return random.randint(0, 1_000)

    square = Square(width=1.3)

    # `random_number` does not appear in representation
    print(repr(square))
    #> Square(width=1.3, area=1.69)

    print(square.random_number)
    #> 3

    square.area = 4

    print(square.model_dump_json(by_alias=True))
    #> {"width":2.0,"area":4.0,"the magic number":3}
    ```

    !!! warning "Overriding with `computed_field`"
        親クラスのフィールドを子クラスの`computed_field`で上書きすることはできません。
        `mypy`は許可されていればこのふるまいは許しませんし、`dataclasses`もこのパターンを許可していません。
        次の例を参照してください。

    ```py
    from pydantic import BaseModel, computed_field

    class Parent(BaseModel):
        a: str

    try:

        class Child(Parent):
            @computed_field
            @property
            def a(self) -> str:
                return 'new a'

    except ValueError as e:
        print(repr(e))
        #> ValueError("you can't override a field with a computed field")
    ```

    `@computed_field`でデコレートされたプライベートプロパティは、デフォルトで`repr=False`です。

    ```py
    from functools import cached_property

    from pydantic import BaseModel, computed_field

    class Model(BaseModel):
        foo: int

        @computed_field
        @cached_property
        def _private_cached_property(self) -> int:
            return -self.foo

        @computed_field
        @property
        def _private_property(self) -> int:
            return -self.foo

    m = Model(foo=1)
    print(repr(m))
    #> M(foo=1)
    ```

    Args:
        func: ラップする関数。
        alias: この計算フィールドをシリアライズするときに使用するエイリアス。`by_alias=True`の場合にのみ使用されます。
        alias_priority: 別名の優先度。これは、別名ジェネレータを使用するかどうかに影響します。
        title: この計算フィールドをJSONスキーマに含めるときに使用するタイトル
        field_title_generator: フィールド名を受け取り、そのタイトルを返す呼び出し可能オブジェクト。
        description: この計算フィールドをJSONスキーマに含めるときに使用する説明。デフォルトは関数のdocstringです。
        deprecated: 非推奨メッセージ(または`warnings.deprecated`または`typing_extensions.deprecated`バックポートのインスタンス)。フィールドにアクセスするときに発行されます。またはブール値。プロパティが`deprecated`デコレータでデコレートされている場合、これは自動的に設定されます。
        examples: この計算フィールドをJSONスキーマに含める場合に使用する値の例
        json_schema_extra: 追加のJSONスキーマ・プロパティーを提供するためのdictまたはcallable。
        repr: この計算済みフィールドをモデルreprに含めるかどうか。デフォルトは、プライベートプロパティの場合は`False`で、パブリックプロパティの場合は`True`です。
        return_type: JSONへのシリアライズ時に期待されるシリアライズロジックのオプションの戻り値。これが含まれている場合は正しくなければなりません。含まれていない場合は`TypeError`が発生します。戻り値の型が含まれていない場合は、任意のオブジェクトを処理するために実行時イントロスペクションを行うAnyが使用されます。

    Returns:
        プロパティのプロキシラッパー。
    """

    def dec(f: Any) -> Any:
        nonlocal description, deprecated, return_type, alias_priority
        unwrapped = _decorators.unwrap_wrapped_function(f)

        if description is None and unwrapped.__doc__:
            description = inspect.cleandoc(unwrapped.__doc__)

        if deprecated is None and hasattr(unwrapped, '__deprecated__'):
            deprecated = unwrapped.__deprecated__

        # if the function isn't already decorated with `@property` (or another descriptor), then we wrap it now
        f = _decorators.ensure_property(f)
        alias_priority = (alias_priority or 2) if alias is not None else None

        if repr is None:
            repr_: bool = not _wrapped_property_is_private(property_=f)
        else:
            repr_ = repr

        dec_info = ComputedFieldInfo(
            f,
            return_type,
            alias,
            alias_priority,
            title,
            field_title_generator,
            description,
            deprecated,
            examples,
            json_schema_extra,
            repr_,
        )
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    if func is None:
        return dec
    else:
        return dec(func)
