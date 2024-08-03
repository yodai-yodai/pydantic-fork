"""
Usage docs: ../concepts/json_schema/

`json_schema`モジュールには、[JSON Schema](https://json-schema.org/)の生成方法をカスタマイズできるようにするクラスと関数が含まれています。

一般的に、このモジュールを直接使用する必要はありません。代わりに、[`BaseModel.model_json_schema`][pydantic.BaseModel.model_json_schema]と[`TypeAdapter.json_schema`][pydantic.TypeAdapter.json_schema]を使用できます。
"""

from __future__ import annotations as _annotations

import dataclasses
import inspect
import math
import re
import warnings
from collections import defaultdict
from copy import deepcopy
from dataclasses import is_dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Counter,
    Dict,
    Hashable,
    Iterable,
    NewType,
    Pattern,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import pydantic_core
from pydantic_core import CoreSchema, PydanticOmit, core_schema, to_jsonable_python
from pydantic_core.core_schema import ComputedField
from typing_extensions import Annotated, Literal, TypeAlias, assert_never, deprecated, final

from pydantic.warnings import PydanticDeprecatedSince26

from ._internal import (
    _config,
    _core_metadata,
    _core_utils,
    _decorators,
    _internal_dataclass,
    _mock_val_ser,
    _schema_generation_shared,
    _typing_extra,
)
from .annotated_handlers import GetJsonSchemaHandler
from .config import JsonDict, JsonSchemaExtraCallable, JsonValue
from .errors import PydanticInvalidForJsonSchema, PydanticSchemaGenerationError, PydanticUserError

if TYPE_CHECKING:
    from . import ConfigDict
    from ._internal._core_utils import CoreSchemaField, CoreSchemaOrField
    from ._internal._dataclasses import PydanticDataclass
    from ._internal._schema_generation_shared import GetJsonSchemaFunction
    from .main import BaseModel


CoreSchemaOrFieldType = Literal[core_schema.CoreSchemaType, core_schema.CoreSchemaFieldType]
"""
`core_schema.CoreSchemaType`と`core_schema.CoreSchemaFieldType`の和集合を表す、定義済みスキーマ型の型エイリアスです。
"""

JsonSchemaValue = Dict[str, Any]
"""
JSONスキーマ値の型の別名。任意のJSON値に対する文字列キーのディクショナリです。
"""

JsonSchemaMode = Literal['validation', 'serialization']
"""
JSONスキーマのモードを表す型エイリアス。"検証"または"シリアライゼーション"のいずれか。

タイプによっては、検証への入力がシリアライゼーションの出力と異なる場合があります。
たとえば、計算フィールドはシリアライズ時にのみ存在し、検証時には提供されません。
このフラグは、検証入力に必要なJSONスキーマを必要とするか、直列化出力によって一致させるかを示す方法を提供します。
"""

_MODE_TITLE_MAPPING: dict[JsonSchemaMode, str] = {'validation': 'Input', 'serialization': 'Output'}


@deprecated(
    '`update_json_schema` is deprecated, use a simple `my_dict.update(update_dict)` call instead.',
    category=None,
)
def update_json_schema(schema: JsonSchemaValue, updates: dict[str, Any]) -> JsonSchemaValue:
    """更新の辞書を提供して、JSONスキーマをインプレースで更新します。

    この関数は、指定されたキーと値のペアをスキーマに設定し、更新されたスキーマを返します。

    Args:
        schema: 更新するJSONスキーマ。
        updates: スキーマに設定するキーと値のペアのディクショナリ。

    Returns:
        更新されたJSONスキーマ。
    """
    schema.update(updates)
    return schema


JsonSchemaWarningKind = Literal['skipped-choice', 'non-serializable-default']
"""
JSONスキーマ生成時に発生する可能性のある警告の種類を表す型エイリアス。

詳細については、[`GenerateJsonSchema.render_warning_message`][pydantic.json_schema.GenerateJsonSchema.render_warning_message]を参照してください。
"""


class PydanticJsonSchemaWarning(UserWarning):
    """このクラスは、JSONスキーマの生成中に生成される警告を発行するために使用されます。
    詳細については、[`GenerateJsonSchema.emit_warning`][pydantic.json_schema.GenerateJsonSchema.emit_warning]および[`GenerateJsonSchema.render_warning_message`][pydantic.json_schema.GenerateJsonSchema.render_warning_message]メソッドを参照してください。これらのメソッドは、警告の動作を制御するためにオーバーライドできます。
    """


# ##### JSON Schema Generation #####
DEFAULT_REF_TEMPLATE = '#/$defs/{model}'
"""参照名の生成に使用されるデフォルトのフォーマット文字列。"""

# There are three types of references relevant to building JSON schemas:
#   1. core_schema "ref" values; these are not exposed as part of the JSON schema
#       * these might look like the fully qualified path of a model, its id, or something similar
CoreRef = NewType('CoreRef', str)
#   2. keys of the "definitions" object that will eventually go into the JSON schema
#       * by default, these look like "MyModel", though may change in the presence of collisions
#       * eventually, we may want to make it easier to modify the way these names are generated
DefsRef = NewType('DefsRef', str)
#   3. the values corresponding to the "$ref" key in the schema
#       * By default, these look like "#/$defs/MyModel", as in {"$ref": "#/$defs/MyModel"}
JsonRef = NewType('JsonRef', str)

CoreModeRef = Tuple[CoreRef, JsonSchemaMode]
JsonSchemaKeyT = TypeVar('JsonSchemaKeyT', bound=Hashable)


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class _DefinitionsRemapping:
    defs_remapping: dict[DefsRef, DefsRef]
    json_remapping: dict[JsonRef, JsonRef]

    @staticmethod
    def from_prioritized_choices(
        prioritized_choices: dict[DefsRef, list[DefsRef]],
        defs_to_json: dict[DefsRef, JsonRef],
        definitions: dict[DefsRef, JsonSchemaValue],
    ) -> _DefinitionsRemapping:
        """
        この関数は、複雑なDefsRefをprioritized_choicesの単純なものに置き換える再マッピングを生成し、名前の再マッピングを適用すると同等のJSONスキーマになるようにする必要がある。
        """
        # We need to iteratively simplify the definitions until we reach a fixed point.
        # The reason for this is that outer definitions may reference inner definitions that get simplified
        # into an equivalent reference, and the outer definitions won't be equivalent until we've simplified
        # the inner definitions.
        copied_definitions = deepcopy(definitions)
        definitions_schema = {'$defs': copied_definitions}
        for _iter in range(100):  # prevent an infinite loop in the case of a bug, 100 iterations should be enough
            # For every possible remapped DefsRef, collect all schemas that that DefsRef might be used for:
            schemas_for_alternatives: dict[DefsRef, list[JsonSchemaValue]] = defaultdict(list)
            for defs_ref in copied_definitions:
                alternatives = prioritized_choices[defs_ref]
                for alternative in alternatives:
                    schemas_for_alternatives[alternative].append(copied_definitions[defs_ref])

            # Deduplicate the schemas for each alternative; the idea is that we only want to remap to a new DefsRef
            # if it introduces no ambiguity, i.e., there is only one distinct schema for that DefsRef.
            for defs_ref, schemas in schemas_for_alternatives.items():
                schemas_for_alternatives[defs_ref] = _deduplicate_schemas(schemas_for_alternatives[defs_ref])

            # Build the remapping
            defs_remapping: dict[DefsRef, DefsRef] = {}
            json_remapping: dict[JsonRef, JsonRef] = {}
            for original_defs_ref in definitions:
                alternatives = prioritized_choices[original_defs_ref]
                # Pick the first alternative that has only one schema, since that means there is no collision
                remapped_defs_ref = next(x for x in alternatives if len(schemas_for_alternatives[x]) == 1)
                defs_remapping[original_defs_ref] = remapped_defs_ref
                json_remapping[defs_to_json[original_defs_ref]] = defs_to_json[remapped_defs_ref]
            remapping = _DefinitionsRemapping(defs_remapping, json_remapping)
            new_definitions_schema = remapping.remap_json_schema({'$defs': copied_definitions})
            if definitions_schema == new_definitions_schema:
                # We've reached the fixed point
                return remapping
            definitions_schema = new_definitions_schema

        raise PydanticInvalidForJsonSchema('Failed to simplify the JSON schema definitions')

    def remap_defs_ref(self, ref: DefsRef) -> DefsRef:
        return self.defs_remapping.get(ref, ref)

    def remap_json_ref(self, ref: JsonRef) -> JsonRef:
        return self.json_remapping.get(ref, ref)

    def remap_json_schema(self, schema: Any) -> Any:
        """
        すべての$refを置き換えて、JSONスキーマを再帰的に更新します。
        """
        if isinstance(schema, str):
            # Note: this may not really be a JsonRef; we rely on having no collisions between JsonRefs and other strings
            return self.remap_json_ref(JsonRef(schema))
        elif isinstance(schema, list):
            return [self.remap_json_schema(item) for item in schema]
        elif isinstance(schema, dict):
            for key, value in schema.items():
                if key == '$ref' and isinstance(value, str):
                    schema['$ref'] = self.remap_json_ref(JsonRef(value))
                elif key == '$defs':
                    schema['$defs'] = {
                        self.remap_defs_ref(DefsRef(key)): self.remap_json_schema(value)
                        for key, value in schema['$defs'].items()
                    }
                else:
                    schema[key] = self.remap_json_schema(value)
        return schema


class GenerateJsonSchema:
    """Usage docs: ../concepts/json_schema/#customizing-the-json-schema-generation-process

    JSONスキーマを生成するためのクラス。

    このクラスは、設定されたパラメータに基づいてJSONスキーマを生成します。デフォルトのスキーマダイアレクトは[https://json-schema.org/draft/2020-12/schema](https://json-schema.org/draft/2020-12/schema)です。
    このクラスは、複数の名前を持つフィールドの処理方法を設定するために`by_alias`を使用し、参照名をフォーマットするために`ref_template`を使用します。

    Attributes:
        schema_dialect: スキーマの生成に使用されるJSONスキーマダイアレクト。ダイアレクトの詳細については、JSONスキーマのドキュメントの[Declaring a Dialect](https: //json-schema. org/understanding-json-schema/reference/schema. html#id4)を参照してください。
        ignored_warning_kind: スキーマの生成時に無視される警告。`self.render_warning_message`は、引数`kind`が`ignored_warning_kind`にある場合は何もしません。この値は、どの警告が出されるかを簡単に制御するためにサブクラスで変更できます。
        by_alias: スキーマの生成時にフィールドの別名を使用するかどうか。
        ref_template: 参照名を生成するときに使用されるフォーマット文字列。
        core_to_json_refs: コア参照からJSON参照へのマッピングです。
        core_to_defs_refs: コア参照から定義参照へのマッピング。
        defs_to_core_refs: 定義参照からコア参照へのマッピング。
        json_to_defs_refs: JSON参照から定義参照へのマッピングです。
        definitions: スキーマ内の定義。

    Args:
        by_alias: 生成されたスキーマでフィールドの別名を使用するかどうか。
        ref_template: 参照名を生成するときに使用するフォーマット文字列。

    Raises:
        JsonSchemaError: スキーマの生成後にクラスのインスタンスが誤って再利用された場合。
    """

    schema_dialect = 'https://json-schema.org/draft/2020-12/schema'

    # `self.render_warning_message` will do nothing if its argument `kind` is in `ignored_warning_kinds`;
    # this value can be modified on subclasses to easily control which warnings are emitted
    ignored_warning_kinds: set[JsonSchemaWarningKind] = {'skipped-choice'}

    def __init__(self, by_alias: bool = True, ref_template: str = DEFAULT_REF_TEMPLATE):
        self.by_alias = by_alias
        self.ref_template = ref_template

        self.core_to_json_refs: dict[CoreModeRef, JsonRef] = {}
        self.core_to_defs_refs: dict[CoreModeRef, DefsRef] = {}
        self.defs_to_core_refs: dict[DefsRef, CoreModeRef] = {}
        self.json_to_defs_refs: dict[JsonRef, DefsRef] = {}

        self.definitions: dict[DefsRef, JsonSchemaValue] = {}
        self._config_wrapper_stack = _config.ConfigWrapperStack(_config.ConfigWrapper({}))

        self._mode: JsonSchemaMode = 'validation'

        # The following includes a mapping of a fully-unique defs ref choice to a list of preferred
        # alternatives, which are generally simpler, such as only including the class name.
        # At the end of schema generation, we use these to produce a JSON schema with more human-readable
        # definitions, which would also work better in a generated OpenAPI client, etc.
        self._prioritized_defsref_choices: dict[DefsRef, list[DefsRef]] = {}
        self._collision_counter: dict[str, int] = defaultdict(int)
        self._collision_index: dict[str, int] = {}

        self._schema_type_to_method = self.build_schema_type_to_method()

        # When we encounter definitions we need to try to build them immediately
        # so that they are available schemas that reference them
        # But it's possible that CoreSchema was never going to be used
        # (e.g. because the CoreSchema that references short circuits is JSON schema generation without needing
        #  the reference) so instead of failing altogether if we can't build a definition we
        # store the error raised and re-throw it if we end up needing that def
        self._core_defs_invalid_for_json_schema: dict[DefsRef, PydanticInvalidForJsonSchema] = {}

        # This changes to True after generating a schema, to prevent issues caused by accidental re-use
        # of a single instance of a schema generator
        self._used = False

    @property
    def _config(self) -> _config.ConfigWrapper:
        return self._config_wrapper_stack.tail

    @property
    def mode(self) -> JsonSchemaMode:
        if self._config.json_schema_mode_override is not None:
            return self._config.json_schema_mode_override
        else:
            return self._mode

    def build_schema_type_to_method(
        self,
    ) -> dict[CoreSchemaOrFieldType, Callable[[CoreSchemaOrField], JsonSchemaValue]]:
        """JSONスキーマを生成するメソッドにフィールドをマッピングする辞書を構築します。

        Returns:
            ハンドラメソッドへの`CoreSchemaOrFieldType`のマッピングを含むディクショナリです。

        Raises:
            TypeError: 指定されたpydanticコアスキーマタイプのJSONスキーマを生成するためのメソッドが定義されていない場合。
        """
        mapping: dict[CoreSchemaOrFieldType, Callable[[CoreSchemaOrField], JsonSchemaValue]] = {}
        core_schema_types: list[CoreSchemaOrFieldType] = _typing_extra.all_literal_values(
            CoreSchemaOrFieldType  # type: ignore
        )
        for key in core_schema_types:
            method_name = f"{key.replace('-', '_')}_schema"
            try:
                mapping[key] = getattr(self, method_name)
            except AttributeError as e:  # pragma: no cover
                raise TypeError(
                    f'No method for generating JsonSchema for core_schema.type={key!r} '
                    f'(expected: {type(self).__name__}.{method_name})'
                ) from e
        return mapping

    def generate_definitions(
        self, inputs: Sequence[tuple[JsonSchemaKeyT, JsonSchemaMode, core_schema.CoreSchema]]
    ) -> tuple[dict[tuple[JsonSchemaKeyT, JsonSchemaMode], JsonSchemaValue], dict[DefsRef, JsonSchemaValue]]:
        """コアスキーマのリストからJSONスキーマ定義を生成し、生成された定義を、入力キーを定義参照にリンクするマッピングと組み合わせます。

        Args:
            inputs:タプルのシーケンス。

                - 最初の要素はJSONスキーマのキー型です。
                - 2番目の要素はJSONモードで、"検証"または"シリアライゼーション"のいずれかです。
                - 3番目の要素はコア・スキーマです。

        Returns:
            次の条件を満たすタプル:

                - 最初の要素は、JSONスキーマ・キー・タイプとJSONモードのタプルをキーとし、その入力ペアに対応するJSONスキーマを値とする辞書です(これらのスキーマは、2番目に返された要素で定義されている定義へのJsonRef参照を持つ場合があります)。
                - 2番目の要素は、最初に返された要素からのJSONスキーマの定義参照をキーとし、実際のJSONスキーマ定義を値とする辞書です。

        Raises:
            PydantictUserError: JSONスキーマジェネレータがすでにJSONスキーマの生成に使用されている場合に発生します。
        """
        if self._used:
            raise PydanticUserError(
                'This JSON schema generator has already been used to generate a JSON schema. '
                f'You must create a new instance of {type(self).__name__} to generate a new JSON schema.',
                code='json-schema-already-used',
            )

        for key, mode, schema in inputs:
            self._mode = mode
            self.generate_inner(schema)

        definitions_remapping = self._build_definitions_remapping()

        json_schemas_map: dict[tuple[JsonSchemaKeyT, JsonSchemaMode], DefsRef] = {}
        for key, mode, schema in inputs:
            self._mode = mode
            json_schema = self.generate_inner(schema)
            json_schemas_map[(key, mode)] = definitions_remapping.remap_json_schema(json_schema)

        json_schema = {'$defs': self.definitions}
        json_schema = definitions_remapping.remap_json_schema(json_schema)
        self._used = True
        return json_schemas_map, _sort_json_schema(json_schema['$defs'])  # type: ignore

    def generate(self, schema: CoreSchema, mode: JsonSchemaMode = 'validation') -> JsonSchemaValue:
        """指定されたスキーマのJSONスキーマを指定されたモードで生成します。

        Args:
            schema: Pydanticモデル。
            mode: スキーマを生成するモード。デフォルトは"検証"です。

        Returns:
            指定されたスキーマを表すJSONスキーマ。

        Raises:
            PydantictUserError: JSONスキーマジェネレータがすでにJSONスキーマの生成に使用されている場合。
        """
        self._mode = mode
        if self._used:
            raise PydanticUserError(
                'This JSON schema generator has already been used to generate a JSON schema. '
                f'You must create a new instance of {type(self).__name__} to generate a new JSON schema.',
                code='json-schema-already-used',
            )

        json_schema: JsonSchemaValue = self.generate_inner(schema)
        json_ref_counts = self.get_json_ref_counts(json_schema)

        # Remove the top-level $ref if present; note that the _generate method already ensures there are no sibling keys
        ref = cast(JsonRef, json_schema.get('$ref'))
        while ref is not None:  # may need to unpack multiple levels
            ref_json_schema = self.get_schema_from_definitions(ref)
            if json_ref_counts[ref] > 1 or ref_json_schema is None:
                # Keep the ref, but use an allOf to remove the top level $ref
                json_schema = {'allOf': [{'$ref': ref}]}
            else:
                # "Unpack" the ref since this is the only reference
                json_schema = ref_json_schema.copy()  # copy to prevent recursive dict reference
                json_ref_counts[ref] -= 1
            ref = cast(JsonRef, json_schema.get('$ref'))

        self._garbage_collect_definitions(json_schema)
        definitions_remapping = self._build_definitions_remapping()

        if self.definitions:
            json_schema['$defs'] = self.definitions

        json_schema = definitions_remapping.remap_json_schema(json_schema)

        # For now, we will not set the $schema key. However, if desired, this can be easily added by overriding
        # this method and adding the following line after a call to super().generate(schema):
        # json_schema['$schema'] = self.schema_dialect

        self._used = True
        return _sort_json_schema(json_schema)

    def generate_inner(self, schema: CoreSchemaOrField) -> JsonSchemaValue:  # noqa: C901
        """指定されたコアスキーマのJSONスキーマを生成します。

        Args:
            schema: 指定されたコアスキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        # If a schema with the same CoreRef has been handled, just return a reference to it
        # Note that this assumes that it will _never_ be the case that the same CoreRef is used
        # on types that should have different JSON schemas
        if 'ref' in schema:
            core_ref = CoreRef(schema['ref'])  # type: ignore[typeddict-item]
            core_mode_ref = (core_ref, self.mode)
            if core_mode_ref in self.core_to_defs_refs and self.core_to_defs_refs[core_mode_ref] in self.definitions:
                return {'$ref': self.core_to_json_refs[core_mode_ref]}

        # Generate the JSON schema, accounting for the json_schema_override and core_schema_override
        metadata_handler = _core_metadata.CoreMetadataHandler(schema)

        def populate_defs(core_schema: CoreSchema, json_schema: JsonSchemaValue) -> JsonSchemaValue:
            if 'ref' in core_schema:
                core_ref = CoreRef(core_schema['ref'])  # type: ignore[typeddict-item]
                defs_ref, ref_json_schema = self.get_cache_defs_ref_schema(core_ref)
                json_ref = JsonRef(ref_json_schema['$ref'])
                self.json_to_defs_refs[json_ref] = defs_ref
                # Replace the schema if it's not a reference to itself
                # What we want to avoid is having the def be just a ref to itself
                # which is what would happen if we blindly assigned any
                if json_schema.get('$ref', None) != json_ref:
                    self.definitions[defs_ref] = json_schema
                    self._core_defs_invalid_for_json_schema.pop(defs_ref, None)
                json_schema = ref_json_schema
            return json_schema

        def convert_to_all_of(json_schema: JsonSchemaValue) -> JsonSchemaValue:
            if '$ref' in json_schema and len(json_schema.keys()) > 1:
                # technically you can't have any other keys next to a "$ref"
                # but it's an easy mistake to make and not hard to correct automatically here
                json_schema = json_schema.copy()
                ref = json_schema.pop('$ref')
                json_schema = {'allOf': [{'$ref': ref}], **json_schema}
            return json_schema

        def handler_func(schema_or_field: CoreSchemaOrField) -> JsonSchemaValue:
            """入力スキーマに基づいてJSONスキーマを生成します。

            Args:
                schema_or_field: JSONスキーマを生成するためのコア・スキーマです。

            Returns:
                生成されたJSONスキーマ。

            Raises:
                TypeError: 予期しないスキーマ・タイプが検出された場合。
            """
            # Generate the core-schema-type-specific bits of the schema generation:
            json_schema: JsonSchemaValue | None = None
            if self.mode == 'serialization' and 'serialization' in schema_or_field:
                ser_schema = schema_or_field['serialization']  # type: ignore
                json_schema = self.ser_schema(ser_schema)
            if json_schema is None:
                if _core_utils.is_core_schema(schema_or_field) or _core_utils.is_core_schema_field(schema_or_field):
                    generate_for_schema_type = self._schema_type_to_method[schema_or_field['type']]
                    json_schema = generate_for_schema_type(schema_or_field)
                else:
                    raise TypeError(f'Unexpected schema type: schema={schema_or_field}')
            if _core_utils.is_core_schema(schema_or_field):
                json_schema = populate_defs(schema_or_field, json_schema)
                json_schema = convert_to_all_of(json_schema)
            return json_schema

        current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, handler_func)

        for js_modify_function in metadata_handler.metadata.get('pydantic_js_functions', ()):

            def new_handler_func(
                schema_or_field: CoreSchemaOrField,
                current_handler: GetJsonSchemaHandler = current_handler,
                js_modify_function: GetJsonSchemaFunction = js_modify_function,
            ) -> JsonSchemaValue:
                json_schema = js_modify_function(schema_or_field, current_handler)
                if _core_utils.is_core_schema(schema_or_field):
                    json_schema = populate_defs(schema_or_field, json_schema)
                original_schema = current_handler.resolve_ref_schema(json_schema)
                ref = json_schema.pop('$ref', None)
                if ref and json_schema:
                    original_schema.update(json_schema)
                return original_schema

            current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, new_handler_func)

        for js_modify_function in metadata_handler.metadata.get('pydantic_js_annotation_functions', ()):

            def new_handler_func(
                schema_or_field: CoreSchemaOrField,
                current_handler: GetJsonSchemaHandler = current_handler,
                js_modify_function: GetJsonSchemaFunction = js_modify_function,
            ) -> JsonSchemaValue:
                json_schema = js_modify_function(schema_or_field, current_handler)
                if _core_utils.is_core_schema(schema_or_field):
                    json_schema = populate_defs(schema_or_field, json_schema)
                    json_schema = convert_to_all_of(json_schema)
                return json_schema

            current_handler = _schema_generation_shared.GenerateJsonSchemaHandler(self, new_handler_func)

        json_schema = current_handler(schema)
        if _core_utils.is_core_schema(schema):
            json_schema = populate_defs(schema, json_schema)
            json_schema = convert_to_all_of(json_schema)
        return json_schema

    # ### Schema generation methods
    def any_schema(self, schema: core_schema.AnySchema) -> JsonSchemaValue:
        """任意の値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return {}

    def none_schema(self, schema: core_schema.NoneSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches `None`.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        return {'type': 'null'}

    def bool_schema(self, schema: core_schema.BoolSchema) -> JsonSchemaValue:
        """bool値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return {'type': 'boolean'}

    def int_schema(self, schema: core_schema.IntSchema) -> JsonSchemaValue:
        """int値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        json_schema: dict[str, Any] = {'type': 'integer'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.numeric)
        json_schema = {k: v for k, v in json_schema.items() if v not in {math.inf, -math.inf}}
        return json_schema

    def float_schema(self, schema: core_schema.FloatSchema) -> JsonSchemaValue:
        """float値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        json_schema: dict[str, Any] = {'type': 'number'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.numeric)
        json_schema = {k: v for k, v in json_schema.items() if v not in {math.inf, -math.inf}}
        return json_schema

    def decimal_schema(self, schema: core_schema.DecimalSchema) -> JsonSchemaValue:
        """decimal値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        json_schema = self.str_schema(core_schema.str_schema())
        if self.mode == 'validation':
            multiple_of = schema.get('multiple_of')
            le = schema.get('le')
            ge = schema.get('ge')
            lt = schema.get('lt')
            gt = schema.get('gt')
            json_schema = {
                'anyOf': [
                    self.float_schema(
                        core_schema.float_schema(
                            allow_inf_nan=schema.get('allow_inf_nan'),
                            multiple_of=None if multiple_of is None else float(multiple_of),
                            le=None if le is None else float(le),
                            ge=None if ge is None else float(ge),
                            lt=None if lt is None else float(lt),
                            gt=None if gt is None else float(gt),
                        )
                    ),
                    json_schema,
                ],
            }
        return json_schema

    def str_schema(self, schema: core_schema.StringSchema) -> JsonSchemaValue:
        """string値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        json_schema = {'type': 'string'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.string)
        if isinstance(json_schema.get('pattern'), Pattern):
            # TODO: should we add regex flags to the pattern?
            json_schema['pattern'] = json_schema.get('pattern').pattern  # type: ignore
        return json_schema

    def bytes_schema(self, schema: core_schema.BytesSchema) -> JsonSchemaValue:
        """bytes値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        json_schema = {'type': 'string', 'format': 'base64url' if self._config.ser_json_bytes == 'base64' else 'binary'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.bytes)
        return json_schema

    def date_schema(self, schema: core_schema.DateSchema) -> JsonSchemaValue:
        """date値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        json_schema = {'type': 'string', 'format': 'date'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.date)
        return json_schema

    def time_schema(self, schema: core_schema.TimeSchema) -> JsonSchemaValue:
        """time値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return {'type': 'string', 'format': 'time'}

    def datetime_schema(self, schema: core_schema.DatetimeSchema) -> JsonSchemaValue:
        """datetime値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return {'type': 'string', 'format': 'date-time'}

    def timedelta_schema(self, schema: core_schema.TimedeltaSchema) -> JsonSchemaValue:
        """timedelta値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        if self._config.ser_json_timedelta == 'float':
            return {'type': 'number'}
        return {'type': 'string', 'format': 'duration'}

    def literal_schema(self, schema: core_schema.LiteralSchema) -> JsonSchemaValue:
        """literal値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        expected = [v.value if isinstance(v, Enum) else v for v in schema['expected']]
        # jsonify the expected values
        expected = [to_jsonable_python(v) for v in expected]

        result: dict[str, Any] = {'enum': expected}
        if len(expected) == 1:
            result['const'] = expected[0]

        types = {type(e) for e in expected}
        if types == {str}:
            result['type'] = 'string'
        elif types == {int}:
            result['type'] = 'integer'
        elif types == {float}:
            result['type'] = 'numeric'
        elif types == {bool}:
            result['type'] = 'boolean'
        elif types == {list}:
            result['type'] = 'array'
        elif types == {type(None)}:
            result['type'] = 'null'
        return result

    def enum_schema(self, schema: core_schema.EnumSchema) -> JsonSchemaValue:
        """Enum値に一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        enum_type = schema['cls']
        description = None if not enum_type.__doc__ else inspect.cleandoc(enum_type.__doc__)
        if (
            description == 'An enumeration.'
        ):  # This is the default value provided by enum.EnumMeta.__new__; don't use it
            description = None
        result: dict[str, Any] = {'title': enum_type.__name__, 'description': description}
        result = {k: v for k, v in result.items() if v is not None}

        expected = [to_jsonable_python(v.value) for v in schema['members']]

        result['enum'] = expected
        if len(expected) == 1:
            result['const'] = expected[0]

        types = {type(e) for e in expected}
        if isinstance(enum_type, str) or types == {str}:
            result['type'] = 'string'
        elif isinstance(enum_type, int) or types == {int}:
            result['type'] = 'integer'
        elif isinstance(enum_type, float) or types == {float}:
            result['type'] = 'numeric'
        elif types == {bool}:
            result['type'] = 'boolean'
        elif types == {list}:
            result['type'] = 'array'

        return result

    def is_instance_schema(self, schema: core_schema.IsInstanceSchema) -> JsonSchemaValue:
        """値がクラスのインスタンスであるかどうかをチェックするコアスキーマのJSONスキーマ生成を処理します。

        サブクラスでオーバーライドされない限り、エラーが発生します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self.handle_invalid_for_json_schema(schema, f'core_schema.IsInstanceSchema ({schema["cls"]})')

    def is_subclass_schema(self, schema: core_schema.IsSubclassSchema) -> JsonSchemaValue:
        """値がクラスのサブクラスであるかどうかをチェックするコアスキーマのJSONスキーマ生成を処理します。

        v1との下位互換性のため、これによってエラーが発生することはありませんが、オーバーライドして変更できます。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。

        """
        # Note: This is for compatibility with V1; you can override if you want different behavior.
        return {}

    def callable_schema(self, schema: core_schema.CallableSchema) -> JsonSchemaValue:
        """呼び出し可能な値に一致するJSONスキーマを生成します。

        サブクラスでオーバーライドされない限り、エラーが発生します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self.handle_invalid_for_json_schema(schema, 'core_schema.CallableSchema')

    def list_schema(self, schema: core_schema.ListSchema) -> JsonSchemaValue:
        """リストスキーマに一致するスキーマを返します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        items_schema = {} if 'items_schema' not in schema else self.generate_inner(schema['items_schema'])
        json_schema = {'type': 'array', 'items': items_schema}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    @deprecated('`tuple_positional_schema` is deprecated. Use `tuple_schema` instead.', category=None)
    @final
    def tuple_positional_schema(self, schema: core_schema.TupleSchema) -> JsonSchemaValue:
        """Replaced by `tuple_schema`."""
        warnings.warn(
            '`tuple_positional_schema` is deprecated. Use `tuple_schema` instead.',
            PydanticDeprecatedSince26,
            stacklevel=2,
        )
        return self.tuple_schema(schema)

    @deprecated('`tuple_variable_schema` is deprecated. Use `tuple_schema` instead.', category=None)
    @final
    def tuple_variable_schema(self, schema: core_schema.TupleSchema) -> JsonSchemaValue:
        """Replaced by `tuple_schema`."""
        warnings.warn(
            '`tuple_variable_schema` is deprecated. Use `tuple_schema` instead.',
            PydanticDeprecatedSince26,
            stacklevel=2,
        )
        return self.tuple_schema(schema)

    def tuple_schema(self, schema: core_schema.TupleSchema) -> JsonSchemaValue:
        """タプルスキーマに一致するJSONスキーマを生成します。例えば、`Tuple[int, str, bool]`や`Tuple[int, .]`などです。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        json_schema: JsonSchemaValue = {'type': 'array'}
        if 'variadic_item_index' in schema:
            variadic_item_index = schema['variadic_item_index']
            if variadic_item_index > 0:
                json_schema['minItems'] = variadic_item_index
                json_schema['prefixItems'] = [
                    self.generate_inner(item) for item in schema['items_schema'][:variadic_item_index]
                ]
            if variadic_item_index + 1 == len(schema['items_schema']):
                # if the variadic item is the last item, then represent it faithfully
                json_schema['items'] = self.generate_inner(schema['items_schema'][variadic_item_index])
            else:
                # otherwise, 'items' represents the schema for the variadic
                # item plus the suffix, so just allow anything for simplicity
                # for now
                json_schema['items'] = True
        else:
            prefixItems = [self.generate_inner(item) for item in schema['items_schema']]
            if prefixItems:
                json_schema['prefixItems'] = prefixItems
            json_schema['minItems'] = len(prefixItems)
            json_schema['maxItems'] = len(prefixItems)
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    def set_schema(self, schema: core_schema.SetSchema) -> JsonSchemaValue:
        """setスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self._common_set_schema(schema)

    def frozenset_schema(self, schema: core_schema.FrozenSetSchema) -> JsonSchemaValue:
        """frozensetスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self._common_set_schema(schema)

    def _common_set_schema(self, schema: core_schema.SetSchema | core_schema.FrozenSetSchema) -> JsonSchemaValue:
        items_schema = {} if 'items_schema' not in schema else self.generate_inner(schema['items_schema'])
        json_schema = {'type': 'array', 'uniqueItems': True, 'items': items_schema}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    def generator_schema(self, schema: core_schema.GeneratorSchema) -> JsonSchemaValue:
        """指定されたGeneratorSchemaを表すJSONスキーマを返します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        items_schema = {} if 'items_schema' not in schema else self.generate_inner(schema['items_schema'])
        json_schema = {'type': 'array', 'items': items_schema}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    def dict_schema(self, schema: core_schema.DictSchema) -> JsonSchemaValue:
        """dictスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        json_schema: JsonSchemaValue = {'type': 'object'}

        keys_schema = self.generate_inner(schema['keys_schema']).copy() if 'keys_schema' in schema else {}
        keys_pattern = keys_schema.pop('pattern', None)

        values_schema = self.generate_inner(schema['values_schema']).copy() if 'values_schema' in schema else {}
        values_schema.pop('title', None)  # don't give a title to the additionalProperties
        if values_schema or keys_pattern is not None:  # don't add additionalProperties if it's empty
            if keys_pattern is None:
                json_schema['additionalProperties'] = values_schema
            else:
                json_schema['patternProperties'] = {keys_pattern: values_schema}

        self.update_with_validations(json_schema, schema, self.ValidationsMapping.object)
        return json_schema

    def _function_schema(
        self,
        schema: _core_utils.AnyFunctionSchema,
    ) -> JsonSchemaValue:
        if _core_utils.is_function_with_inner_schema(schema):
            # This could be wrong if the function's mode is 'before', but in practice will often be right, and when it
            # isn't, I think it would be hard to automatically infer what the desired schema should be.
            return self.generate_inner(schema['schema'])

        # function-plain
        return self.handle_invalid_for_json_schema(
            schema, f'core_schema.PlainValidatorFunctionSchema ({schema["function"]})'
        )

    def function_before_schema(self, schema: core_schema.BeforeValidatorFunctionSchema) -> JsonSchemaValue:
        """function-beforeスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self._function_schema(schema)

    def function_after_schema(self, schema: core_schema.AfterValidatorFunctionSchema) -> JsonSchemaValue:
        """function-afterスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self._function_schema(schema)

    def function_plain_schema(self, schema: core_schema.PlainValidatorFunctionSchema) -> JsonSchemaValue:
        """function-plainスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self._function_schema(schema)

    def function_wrap_schema(self, schema: core_schema.WrapValidatorFunctionSchema) -> JsonSchemaValue:
        """function-wrapスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self._function_schema(schema)

    def default_schema(self, schema: core_schema.WithDefaultSchema) -> JsonSchemaValue:
        """デフォルト値を持つスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        json_schema = self.generate_inner(schema['schema'])

        if 'default' not in schema:
            return json_schema
        default = schema['default']
        # Note: if you want to include the value returned by the default_factory,
        # override this method and replace the code above with:
        # if 'default' in schema:
        #     default = schema['default']
        # elif 'default_factory' in schema:
        #     default = schema['default_factory']()
        # else:
        #     return json_schema

        # we reflect the application of custom plain, no-info serializers to defaults for
        # json schemas viewed in serialization mode
        # TODO: improvements along with https://github.com/pydantic/pydantic/issues/8208
        # TODO: improve type safety here
        if self.mode == 'serialization':
            if (
                (ser_schema := schema['schema'].get('serialization', {}))
                and (ser_func := ser_schema.get('function'))
                and ser_schema.get('type') == 'function-plain'  # type: ignore
                and ser_schema.get('info_arg') is False  # type: ignore
            ):
                default = ser_func(default)  # type: ignore

        try:
            encoded_default = self.encode_default(default)
        except pydantic_core.PydanticSerializationError:
            self.emit_warning(
                'non-serializable-default',
                f'Default value {default} is not JSON serializable; excluding default from JSON schema',
            )
            # Return the inner schema, as though there was no default
            return json_schema

        if '$ref' in json_schema:
            # Since reference schemas do not support child keys, we wrap the reference schema in a single-case allOf:
            return {'allOf': [json_schema], 'default': encoded_default}
        else:
            json_schema['default'] = encoded_default
            return json_schema

    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        """null値を許可するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        null_schema = {'type': 'null'}
        inner_json_schema = self.generate_inner(schema['schema'])

        if inner_json_schema == null_schema:
            return null_schema
        else:
            # Thanks to the equality check against `null_schema` above, I think 'oneOf' would also be valid here;
            # I'll use 'anyOf' for now, but it could be changed it if it would work better with some external tooling
            return self.get_flattened_anyof([inner_json_schema, null_schema])

    def union_schema(self, schema: core_schema.UnionSchema) -> JsonSchemaValue:
        """指定されたスキーマのいずれかに一致する値を許可するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。

        """
        generated: list[JsonSchemaValue] = []

        choices = schema['choices']
        for choice in choices:
            # choice will be a tuple if an explicit label was provided
            choice_schema = choice[0] if isinstance(choice, tuple) else choice
            try:
                generated.append(self.generate_inner(choice_schema))
            except PydanticOmit:
                continue
            except PydanticInvalidForJsonSchema as exc:
                self.emit_warning('skipped-choice', exc.message)
        if len(generated) == 1:
            return generated[0]
        return self.get_flattened_anyof(generated)

    def tagged_union_schema(self, schema: core_schema.TaggedUnionSchema) -> JsonSchemaValue:
        """指定されたスキーマのいずれかに一致する値を許可するスキーマに一致するJSONスキーマを生成します。スキーマには、値の検証に使用するスキーマを示す識別子フィールドのタグが付けられます。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        generated: dict[str, JsonSchemaValue] = {}
        for k, v in schema['choices'].items():
            if isinstance(k, Enum):
                k = k.value
            try:
                # Use str(k) since keys must be strings for json; while not technically correct,
                # it's the closest that can be represented in valid JSON
                generated[str(k)] = self.generate_inner(v).copy()
            except PydanticOmit:
                continue
            except PydanticInvalidForJsonSchema as exc:
                self.emit_warning('skipped-choice', exc.message)

        one_of_choices = _deduplicate_schemas(generated.values())
        json_schema: JsonSchemaValue = {'oneOf': one_of_choices}

        # This reflects the v1 behavior; TODO: we should make it possible to exclude OpenAPI stuff from the JSON schema
        openapi_discriminator = self._extract_discriminator(schema, one_of_choices)
        if openapi_discriminator is not None:
            json_schema['discriminator'] = {
                'propertyName': openapi_discriminator,
                'mapping': {k: v.get('$ref', v) for k, v in generated.items()},
            }

        return json_schema

    def _extract_discriminator(
        self, schema: core_schema.TaggedUnionSchema, one_of_choices: list[JsonDict]
    ) -> str | None:
        """スキーマから互換性のあるOpenAPI識別子を抽出し、最終的なスキーマになる1つの選択肢を抽出します。"""

        openapi_discriminator: str | None = None

        if isinstance(schema['discriminator'], str):
            return schema['discriminator']

        if isinstance(schema['discriminator'], list):
            # If the discriminator is a single item list containing a string, that is equivalent to the string case
            if len(schema['discriminator']) == 1 and isinstance(schema['discriminator'][0], str):
                return schema['discriminator'][0]
            # When an alias is used that is different from the field name, the discriminator will be a list of single
            # str lists, one for the attribute and one for the actual alias. The logic here will work even if there is
            # more than one possible attribute, and looks for whether a single alias choice is present as a documented
            # property on all choices. If so, that property will be used as the OpenAPI discriminator.
            for alias_path in schema['discriminator']:
                if not isinstance(alias_path, list):
                    break  # this means that the discriminator is not a list of alias paths
                if len(alias_path) != 1:
                    continue  # this means that the "alias" does not represent a single field
                alias = alias_path[0]
                if not isinstance(alias, str):
                    continue  # this means that the "alias" does not represent a field
                alias_is_present_on_all_choices = True
                for choice in one_of_choices:
                    while '$ref' in choice:
                        assert isinstance(choice['$ref'], str)
                        choice = self.get_schema_from_definitions(JsonRef(choice['$ref'])) or {}
                    properties = choice.get('properties', {})
                    if not isinstance(properties, dict) or alias not in properties:
                        alias_is_present_on_all_choices = False
                        break
                if alias_is_present_on_all_choices:
                    openapi_discriminator = alias
                    break
        return openapi_discriminator

    def chain_schema(self, schema: core_schema.ChainSchema) -> JsonSchemaValue:
        """core_schema.ChainSchemaに一致するJSONスキーマを生成します。

        検証のためのスキーマを生成するとき、チェーンの最初のステップの検証JSONスキーマを返します。
        シリアライゼーションでは、チェーンの最後のステップのシリアライゼーションJSONスキーマを返します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        step_index = 0 if self.mode == 'validation' else -1  # use first step for validation, last for serialization
        return self.generate_inner(schema['steps'][step_index])

    def lax_or_strict_schema(self, schema: core_schema.LaxOrStrictSchema) -> JsonSchemaValue:
        """laxスキーマまたはstrictスキーマのいずれかに一致する値を許可するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        # TODO: Need to read the default value off of model config or whatever
        use_strict = schema.get('strict', False)  # TODO: replace this default False
        # If your JSON schema fails to generate it is probably
        # because one of the following two branches failed.
        if use_strict:
            return self.generate_inner(schema['strict_schema'])
        else:
            return self.generate_inner(schema['lax_schema'])

    def json_or_python_schema(self, schema: core_schema.JsonOrPythonSchema) -> JsonSchemaValue:
        """JSONスキーマまたはPythonスキーマのいずれかに一致する値を許可するスキーマに一致するJSONスキーマを生成します。

        Pythonスキーマの代わりにJSONスキーマが使用されます。Pythonスキーマを使用する場合は、このメソッドをオーバーライドする必要があります。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self.generate_inner(schema['json_schema'])

    def typed_dict_schema(self, schema: core_schema.TypedDictSchema) -> JsonSchemaValue:
        """型付きdictを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        total = schema.get('total', True)
        named_required_fields: list[tuple[str, bool, CoreSchemaField]] = [
            (name, self.field_is_required(field, total), field)
            for name, field in schema['fields'].items()
            if self.field_is_present(field)
        ]
        if self.mode == 'serialization':
            named_required_fields.extend(self._name_required_computed_fields(schema.get('computed_fields', [])))
        cls = _get_typed_dict_cls(schema)
        config = _get_typed_dict_config(cls)
        with self._config_wrapper_stack.push(config):
            json_schema = self._named_required_fields_schema(named_required_fields)

        json_schema_extra = config.get('json_schema_extra')
        extra = schema.get('extra_behavior')
        if extra is None:
            extra = config.get('extra', 'ignore')

        if cls is not None:
            title = config.get('title') or cls.__name__
            json_schema = self._update_class_schema(json_schema, title, extra, cls, json_schema_extra)
        else:
            if extra == 'forbid':
                json_schema['additionalProperties'] = False
            elif extra == 'allow':
                json_schema['additionalProperties'] = True

        return json_schema

    @staticmethod
    def _name_required_computed_fields(
        computed_fields: list[ComputedField],
    ) -> list[tuple[str, bool, core_schema.ComputedField]]:
        return [(field['property_name'], True, field) for field in computed_fields]

    def _named_required_fields_schema(
        self, named_required_fields: Sequence[tuple[str, bool, CoreSchemaField]]
    ) -> JsonSchemaValue:
        properties: dict[str, JsonSchemaValue] = {}
        required_fields: list[str] = []
        for name, required, field in named_required_fields:
            if self.by_alias:
                name = self._get_alias_name(field, name)
            try:
                field_json_schema = self.generate_inner(field).copy()
            except PydanticOmit:
                continue
            if 'title' not in field_json_schema and self.field_title_should_be_set(field):
                title = self.get_title_from_name(name)
                field_json_schema['title'] = title
            field_json_schema = self.handle_ref_overrides(field_json_schema)
            properties[name] = field_json_schema
            if required:
                required_fields.append(name)

        json_schema = {'type': 'object', 'properties': properties}
        if required_fields:
            json_schema['required'] = required_fields
        return json_schema

    def _get_alias_name(self, field: CoreSchemaField, name: str) -> str:
        if field['type'] == 'computed-field':
            alias: Any = field.get('alias', name)
        elif self.mode == 'validation':
            alias = field.get('validation_alias', name)
        else:
            alias = field.get('serialization_alias', name)
        if isinstance(alias, str):
            name = alias
        elif isinstance(alias, list):
            alias = cast('list[str] | str', alias)
            for path in alias:
                if isinstance(path, list) and len(path) == 1 and isinstance(path[0], str):
                    # Use the first valid single-item string path; the code that constructs the alias array
                    # should ensure the first such item is what belongs in the JSON schema
                    name = path[0]
                    break
        else:
            assert_never(alias)
        return name

    def typed_dict_field_schema(self, schema: core_schema.TypedDictField) -> JsonSchemaValue:
        """型指定されたdictフィールドを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。

        """
        return self.generate_inner(schema['schema'])

    def dataclass_field_schema(self, schema: core_schema.DataclassField) -> JsonSchemaValue:
        """データクラスフィールドを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self.generate_inner(schema['schema'])

    def model_field_schema(self, schema: core_schema.ModelField) -> JsonSchemaValue:
        """モデルフィールドを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self.generate_inner(schema['schema'])

    def computed_field_schema(self, schema: core_schema.ComputedField) -> JsonSchemaValue:
        """計算フィールドを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self.generate_inner(schema['return_schema'])

    def model_schema(self, schema: core_schema.ModelSchema) -> JsonSchemaValue:
        """モデルを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        # We do not use schema['model'].model_json_schema() here
        # because it could lead to inconsistent refs handling, etc.
        cls = cast('type[BaseModel]', schema['cls'])
        config = cls.model_config
        title = config.get('title')

        with self._config_wrapper_stack.push(config):
            json_schema = self.generate_inner(schema['schema'])

        json_schema_extra = config.get('json_schema_extra')
        if cls.__pydantic_root_model__:
            root_json_schema_extra = cls.model_fields['root'].json_schema_extra
            if json_schema_extra and root_json_schema_extra:
                raise ValueError(
                    '"model_config[\'json_schema_extra\']" and "Field.json_schema_extra" on "RootModel.root"'
                    ' field must not be set simultaneously'
                )
            if root_json_schema_extra:
                json_schema_extra = root_json_schema_extra

        json_schema = self._update_class_schema(json_schema, title, config.get('extra', None), cls, json_schema_extra)

        return json_schema

    def _update_class_schema(
        self,
        json_schema: JsonSchemaValue,
        title: str | None,
        extra: Literal['allow', 'ignore', 'forbid'] | None,
        cls: type[Any],
        json_schema_extra: JsonDict | JsonSchemaExtraCallable | None,
    ) -> JsonSchemaValue:
        if '$ref' in json_schema:
            schema_to_update = self.get_schema_from_definitions(JsonRef(json_schema['$ref'])) or json_schema
        else:
            schema_to_update = json_schema

        if title is not None:
            # referenced_schema['title'] = title
            schema_to_update.setdefault('title', title)

        if 'additionalProperties' not in schema_to_update:
            if extra == 'allow':
                schema_to_update['additionalProperties'] = True
            elif extra == 'forbid':
                schema_to_update['additionalProperties'] = False

        if isinstance(json_schema_extra, (staticmethod, classmethod)):
            # In older versions of python, this is necessary to ensure staticmethod/classmethods are callable
            json_schema_extra = json_schema_extra.__get__(cls)

        if isinstance(json_schema_extra, dict):
            schema_to_update.update(json_schema_extra)
        elif callable(json_schema_extra):
            if len(inspect.signature(json_schema_extra).parameters) > 1:
                json_schema_extra(schema_to_update, cls)  # type: ignore
            else:
                json_schema_extra(schema_to_update)  # type: ignore
        elif json_schema_extra is not None:
            raise ValueError(
                f"model_config['json_schema_extra']={json_schema_extra} should be a dict, callable, or None"
            )

        if hasattr(cls, '__deprecated__'):
            json_schema['deprecated'] = True

        return json_schema

    def resolve_schema_to_update(self, json_schema: JsonSchemaValue) -> JsonSchemaValue:
        """JsonSchemaValueが$refスキーマである場合は、非refスキーマに解決します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        if '$ref' in json_schema:
            schema_to_update = self.get_schema_from_definitions(JsonRef(json_schema['$ref']))
            if schema_to_update is None:
                raise RuntimeError(f'Cannot update undefined schema for $ref={json_schema["$ref"]}')
            return self.resolve_schema_to_update(schema_to_update)
        else:
            schema_to_update = json_schema
        return schema_to_update

    def model_fields_schema(self, schema: core_schema.ModelFieldsSchema) -> JsonSchemaValue:
        """モデルのフィールドを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        named_required_fields: list[tuple[str, bool, CoreSchemaField]] = [
            (name, self.field_is_required(field, total=True), field)
            for name, field in schema['fields'].items()
            if self.field_is_present(field)
        ]
        if self.mode == 'serialization':
            named_required_fields.extend(self._name_required_computed_fields(schema.get('computed_fields', [])))
        json_schema = self._named_required_fields_schema(named_required_fields)
        extras_schema = schema.get('extras_schema', None)
        if extras_schema is not None:
            schema_to_update = self.resolve_schema_to_update(json_schema)
            schema_to_update['additionalProperties'] = self.generate_inner(extras_schema)
        return json_schema

    def field_is_present(self, field: CoreSchemaField) -> bool:
        """生成されたJSONスキーマにフィールドを含めるかどうか。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        if self.mode == 'serialization':
            # If you still want to include the field in the generated JSON schema,
            # override this method and return True
            return not field.get('serialization_exclude')
        elif self.mode == 'validation':
            return True
        else:
            assert_never(self.mode)

    def field_is_required(
        self,
        field: core_schema.ModelField | core_schema.DataclassField | core_schema.TypedDictField,
        total: bool,
    ) -> bool:
        """生成されたJSONスキーマでフィールドが必須としてマークされるかどうか。
        (フィールドがJSONスキーマに存在しない場合、これは無関係であることに注意してください。

        Args:
            field: フィールド自体のスキーマ。
            total: `TypedDictField`にのみ適用されます。
                このフィールドが属する`TypedDict`が合計かどうかを示します。この場合、`required=False`を明示的に指定していないフィールドはすべて必要です。

        Returns:
            生成されたJSONスキーマでフィールドがrequiredとマークされる場合は`True`、それ以外の場合は`False`です。
        """
        if self.mode == 'serialization' and self._config.json_schema_serialization_defaults_required:
            return not field.get('serialization_exclude')
        else:
            if field['type'] == 'typed-dict-field':
                return field.get('required', total)
            else:
                return field['schema']['type'] != 'default'

    def dataclass_args_schema(self, schema: core_schema.DataclassArgsSchema) -> JsonSchemaValue:
        """データクラスのコンストラクタ引数を定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        named_required_fields: list[tuple[str, bool, CoreSchemaField]] = [
            (field['name'], self.field_is_required(field, total=True), field)
            for field in schema['fields']
            if self.field_is_present(field)
        ]
        if self.mode == 'serialization':
            named_required_fields.extend(self._name_required_computed_fields(schema.get('computed_fields', [])))
        return self._named_required_fields_schema(named_required_fields)

    def dataclass_schema(self, schema: core_schema.DataclassSchema) -> JsonSchemaValue:
        """データクラスを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        cls = schema['cls']
        config: ConfigDict = getattr(cls, '__pydantic_config__', cast('ConfigDict', {}))
        title = config.get('title') or cls.__name__

        with self._config_wrapper_stack.push(config):
            json_schema = self.generate_inner(schema['schema']).copy()

        json_schema_extra = config.get('json_schema_extra')
        json_schema = self._update_class_schema(json_schema, title, config.get('extra', None), cls, json_schema_extra)

        # Dataclass-specific handling of description
        if is_dataclass(cls) and not hasattr(cls, '__pydantic_validator__'):
            # vanilla dataclass; don't use cls.__doc__ as it will contain the class signature by default
            description = None
        else:
            description = None if cls.__doc__ is None else inspect.cleandoc(cls.__doc__)
        if description:
            json_schema['description'] = description

        return json_schema

    def arguments_schema(self, schema: core_schema.ArgumentsSchema) -> JsonSchemaValue:
        """関数の引数を定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        metadata = _core_metadata.CoreMetadataHandler(schema).metadata
        prefer_positional = metadata.get('pydantic_js_prefer_positional_arguments')

        arguments = schema['arguments_schema']
        kw_only_arguments = [a for a in arguments if a.get('mode') == 'keyword_only']
        kw_or_p_arguments = [a for a in arguments if a.get('mode') in {'positional_or_keyword', None}]
        p_only_arguments = [a for a in arguments if a.get('mode') == 'positional_only']
        var_args_schema = schema.get('var_args_schema')
        var_kwargs_schema = schema.get('var_kwargs_schema')

        if prefer_positional:
            positional_possible = not kw_only_arguments and not var_kwargs_schema
            if positional_possible:
                return self.p_arguments_schema(p_only_arguments + kw_or_p_arguments, var_args_schema)

        keyword_possible = not p_only_arguments and not var_args_schema
        if keyword_possible:
            return self.kw_arguments_schema(kw_or_p_arguments + kw_only_arguments, var_kwargs_schema)

        if not prefer_positional:
            positional_possible = not kw_only_arguments and not var_kwargs_schema
            if positional_possible:
                return self.p_arguments_schema(p_only_arguments + kw_or_p_arguments, var_args_schema)

        raise PydanticInvalidForJsonSchema(
            'Unable to generate JSON schema for arguments validator with positional-only and keyword-only arguments'
        )

    def kw_arguments_schema(
        self, arguments: list[core_schema.ArgumentsParameter], var_kwargs_schema: CoreSchema | None
    ) -> JsonSchemaValue:
        """関数のキーワード引数を定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        properties: dict[str, JsonSchemaValue] = {}
        required: list[str] = []
        for argument in arguments:
            name = self.get_argument_name(argument)
            argument_schema = self.generate_inner(argument['schema']).copy()
            argument_schema['title'] = self.get_title_from_name(name)
            properties[name] = argument_schema

            if argument['schema']['type'] != 'default':
                # This assumes that if the argument has a default value,
                # the inner schema must be of type WithDefaultSchema.
                # I believe this is true, but I am not 100% sure
                required.append(name)

        json_schema: JsonSchemaValue = {'type': 'object', 'properties': properties}
        if required:
            json_schema['required'] = required

        if var_kwargs_schema:
            additional_properties_schema = self.generate_inner(var_kwargs_schema)
            if additional_properties_schema:
                json_schema['additionalProperties'] = additional_properties_schema
        else:
            json_schema['additionalProperties'] = False
        return json_schema

    def p_arguments_schema(
        self, arguments: list[core_schema.ArgumentsParameter], var_args_schema: CoreSchema | None
    ) -> JsonSchemaValue:
        """関数の位置引数を定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        prefix_items: list[JsonSchemaValue] = []
        min_items = 0

        for argument in arguments:
            name = self.get_argument_name(argument)

            argument_schema = self.generate_inner(argument['schema']).copy()
            argument_schema['title'] = self.get_title_from_name(name)
            prefix_items.append(argument_schema)

            if argument['schema']['type'] != 'default':
                # This assumes that if the argument has a default value,
                # the inner schema must be of type WithDefaultSchema.
                # I believe this is true, but I am not 100% sure
                min_items += 1

        json_schema: JsonSchemaValue = {'type': 'array', 'prefixItems': prefix_items}
        if min_items:
            json_schema['minItems'] = min_items

        if var_args_schema:
            items_schema = self.generate_inner(var_args_schema)
            if items_schema:
                json_schema['items'] = items_schema
        else:
            json_schema['maxItems'] = len(prefix_items)

        return json_schema

    def get_argument_name(self, argument: core_schema.ArgumentsParameter) -> str:
        """引数の名前を取得します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        name = argument['name']
        if self.by_alias:
            alias = argument.get('alias')
            if isinstance(alias, str):
                name = alias
            else:
                pass  # might want to do something else?
        return name

    def call_schema(self, schema: core_schema.CallSchema) -> JsonSchemaValue:
        """関数呼び出しを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self.generate_inner(schema['arguments_schema'])

    def custom_error_schema(self, schema: core_schema.CustomErrorSchema) -> JsonSchemaValue:
        """カスタムエラーを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return self.generate_inner(schema['schema'])

    def json_schema(self, schema: core_schema.JsonSchema) -> JsonSchemaValue:
        """JSONオブジェクトを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        content_core_schema = schema.get('schema') or core_schema.any_schema()
        content_json_schema = self.generate_inner(content_core_schema)
        if self.mode == 'validation':
            return {'type': 'string', 'contentMediaType': 'application/json', 'contentSchema': content_json_schema}
        else:
            # self.mode == 'serialization'
            return content_json_schema

    def url_schema(self, schema: core_schema.UrlSchema) -> JsonSchemaValue:
        """URLを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        json_schema = {'type': 'string', 'format': 'uri', 'minLength': 1}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.string)
        return json_schema

    def multi_host_url_schema(self, schema: core_schema.MultiHostUrlSchema) -> JsonSchemaValue:
        """複数のホストで使用できるURLを定義するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        # Note: 'multi-host-uri' is a custom/pydantic-specific format, not part of the JSON Schema spec
        json_schema = {'type': 'string', 'format': 'multi-host-uri', 'minLength': 1}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.string)
        return json_schema

    def uuid_schema(self, schema: core_schema.UuidSchema) -> JsonSchemaValue:
        """UUIDに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return {'type': 'string', 'format': 'uuid'}

    def definitions_schema(self, schema: core_schema.DefinitionsSchema) -> JsonSchemaValue:
        """定義を持つJSONオブジェクトを定義するスキーマと一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        for definition in schema['definitions']:
            try:
                self.generate_inner(definition)
            except PydanticInvalidForJsonSchema as e:
                core_ref: CoreRef = CoreRef(definition['ref'])  # type: ignore
                self._core_defs_invalid_for_json_schema[self.get_defs_ref((core_ref, self.mode))] = e
                continue
        return self.generate_inner(schema['schema'])

    def definition_ref_schema(self, schema: core_schema.DefinitionReferenceSchema) -> JsonSchemaValue:
        """定義を参照するスキーマに一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        core_ref = CoreRef(schema['schema_ref'])
        _, ref_json_schema = self.get_cache_defs_ref_schema(core_ref)
        return ref_json_schema

    def ser_schema(
        self, schema: core_schema.SerSchema | core_schema.IncExSeqSerSchema | core_schema.IncExDictSerSchema
    ) -> JsonSchemaValue | None:
        """シリアライズされたオブジェクトを定義するスキーマと一致するJSONスキーマを生成します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        schema_type = schema['type']
        if schema_type == 'function-plain' or schema_type == 'function-wrap':
            # PlainSerializerFunctionSerSchema or WrapSerializerFunctionSerSchema
            return_schema = schema.get('return_schema')
            if return_schema is not None:
                return self.generate_inner(return_schema)
        elif schema_type == 'format' or schema_type == 'to-string':
            # FormatSerSchema or ToStringSerSchema
            return self.str_schema(core_schema.str_schema())
        elif schema['type'] == 'model':
            # ModelSerSchema
            return self.generate_inner(schema['schema'])
        return None

    # ### Utility methods

    def get_title_from_name(self, name: str) -> str:
        """名前からタイトルを取得します。

        Args:
            schema: コア・スキーマ。

        Returns:
            生成されたJSONスキーマ。
        """
        return name.title().replace('_', ' ')

    def field_title_should_be_set(self, schema: CoreSchemaOrField) -> bool:
        """指定されたスキーマを持つフィールドに、フィールド名に基づいたタイトルセットが必要な場合、trueを返します。

        直感的には、他の方法では独自のタイトルを提供しないスキーマ(int、float、strなど)に対してはtrueを返し、独自のタイトルを提供するスキーマ(BaseModelサブクラスなど)に対してはfalseを返すようにします。

        Args:
            schema: チェックするスキーマ。

        Returns:
            フィールドにタイトルを設定する必要がある場合は`True`、そうでない場合は`False`です。
        """
        if _core_utils.is_core_schema_field(schema):
            if schema['type'] == 'computed-field':
                field_schema = schema['return_schema']
            else:
                field_schema = schema['schema']
            return self.field_title_should_be_set(field_schema)

        elif _core_utils.is_core_schema(schema):
            if schema.get('ref'):  # things with refs, such as models and enums, should not have titles set
                return False
            if schema['type'] in {'default', 'nullable', 'definitions'}:
                return self.field_title_should_be_set(schema['schema'])  # type: ignore[typeddict-item]
            if _core_utils.is_function_with_inner_schema(schema):
                return self.field_title_should_be_set(schema['schema'])
            if schema['type'] == 'definition-ref':
                # Referenced schemas should not have titles set for the same reason
                # schemas with refs should not
                return False
            return True  # anything else should have title set

        else:
            raise PydanticInvalidForJsonSchema(f'Unexpected schema type: schema={schema}')  # pragma: no cover

    def normalize_name(self, name: str) -> str:
        """名前を正規化して、辞書のキーとして使用します。

        Args:
            name: 正規化する名前。

        Returns:
            正規化された名前。
       """
        return re.sub(r'[^a-zA-Z0-9.\-_]', '_', name).replace('.', '__')

    def get_defs_ref(self, core_mode_ref: CoreModeRef) -> DefsRef:
        """このメソッドをオーバーライドして、コア参照から定義キーを生成する方法を変更します。

        Args:
            core_mode_ref: コアへの参照。

        Returns:
            定義キー。
        """
        # Split the core ref into "components"; generic origins and arguments are each separate components
        core_ref, mode = core_mode_ref
        components = re.split(r'([\][,])', core_ref)
        # Remove IDs from each component
        components = [x.rsplit(':', 1)[0] for x in components]
        core_ref_no_id = ''.join(components)
        # Remove everything before the last period from each "component"
        components = [re.sub(r'(?:[^.[\]]+\.)+((?:[^.[\]]+))', r'\1', x) for x in components]
        short_ref = ''.join(components)

        mode_title = _MODE_TITLE_MAPPING[mode]

        # It is important that the generated defs_ref values be such that at least one choice will not
        # be generated for any other core_ref. Currently, this should be the case because we include
        # the id of the source type in the core_ref
        name = DefsRef(self.normalize_name(short_ref))
        name_mode = DefsRef(self.normalize_name(short_ref) + f'-{mode_title}')
        module_qualname = DefsRef(self.normalize_name(core_ref_no_id))
        module_qualname_mode = DefsRef(f'{module_qualname}-{mode_title}')
        module_qualname_id = DefsRef(self.normalize_name(core_ref))
        occurrence_index = self._collision_index.get(module_qualname_id)
        if occurrence_index is None:
            self._collision_counter[module_qualname] += 1
            occurrence_index = self._collision_index[module_qualname_id] = self._collision_counter[module_qualname]

        module_qualname_occurrence = DefsRef(f'{module_qualname}__{occurrence_index}')
        module_qualname_occurrence_mode = DefsRef(f'{module_qualname_mode}__{occurrence_index}')

        self._prioritized_defsref_choices[module_qualname_occurrence_mode] = [
            name,
            name_mode,
            module_qualname,
            module_qualname_mode,
            module_qualname_occurrence,
            module_qualname_occurrence_mode,
        ]

        return module_qualname_occurrence_mode

    def get_cache_defs_ref_schema(self, core_ref: CoreRef) -> tuple[DefsRef, JsonSchemaValue]:
        """このメソッドは、get_defs_refメソッドをキャッシュ・ルックアップ/ポピュレーション・ロジックでラップし、生成されたdefs_refと、適切な定義を参照するJSONスキーマの両方を返します。

        Args:
            core_ref: 定義リファレンスを取得するためのコアリファレンス。

        Returns:
            定義参照と、それを参照するJSONスキーマのタプル。
        """
        core_mode_ref = (core_ref, self.mode)
        maybe_defs_ref = self.core_to_defs_refs.get(core_mode_ref)
        if maybe_defs_ref is not None:
            json_ref = self.core_to_json_refs[core_mode_ref]
            return maybe_defs_ref, {'$ref': json_ref}

        defs_ref = self.get_defs_ref(core_mode_ref)

        # populate the ref translation mappings
        self.core_to_defs_refs[core_mode_ref] = defs_ref
        self.defs_to_core_refs[defs_ref] = core_mode_ref

        json_ref = JsonRef(self.ref_template.format(model=defs_ref))
        self.core_to_json_refs[core_mode_ref] = json_ref
        self.json_to_defs_refs[json_ref] = defs_ref
        ref_json_schema = {'$ref': json_ref}
        return defs_ref, ref_json_schema

    def handle_ref_overrides(self, json_schema: JsonSchemaValue) -> JsonSchemaValue:
        """最上位の$refを持つスキーマが兄弟キーを持つことは無効です。

        During our own schema generation, we treat sibling keys as overrides to the referenced schema, but this is not how the official JSON schema spec works.
        自身のスキーマ生成では、兄弟キーを参照されるスキーマに対するオーバーライドとして扱いますが、これは公式のJSONスキーマ仕様の動作方法ではありません。

        このため、まず、参照されるスキーマと重複する兄弟キーを削除し、残っている場合は、最上位の'$ref'からスキーマを変換し、allOfを使用して$refを最上位から移動します。
        (この動作については、https://swagger.io/docs/specification/using-ref/の下部を参照してください)。
        """
        if '$ref' in json_schema:
            # prevent modifications to the input; this copy may be safe to drop if there is significant overhead
            json_schema = json_schema.copy()

            referenced_json_schema = self.get_schema_from_definitions(JsonRef(json_schema['$ref']))
            if referenced_json_schema is None:
                # This can happen when building schemas for models with not-yet-defined references.
                # It may be a good idea to do a recursive pass at the end of the generation to remove
                # any redundant override keys.
                if len(json_schema) > 1:
                    # Make it an allOf to at least resolve the sibling keys issue
                    json_schema = json_schema.copy()
                    json_schema.setdefault('allOf', [])
                    json_schema['allOf'].append({'$ref': json_schema['$ref']})
                    del json_schema['$ref']

                return json_schema
            for k, v in list(json_schema.items()):
                if k == '$ref':
                    continue
                if k in referenced_json_schema and referenced_json_schema[k] == v:
                    del json_schema[k]  # redundant key
            if len(json_schema) > 1:
                # There is a remaining "override" key, so we need to move $ref out of the top level
                json_ref = JsonRef(json_schema['$ref'])
                del json_schema['$ref']
                assert 'allOf' not in json_schema  # this should never happen, but just in case
                json_schema['allOf'] = [{'$ref': json_ref}]

        return json_schema

    def get_schema_from_definitions(self, json_ref: JsonRef) -> JsonSchemaValue | None:
        def_ref = self.json_to_defs_refs[json_ref]
        if def_ref in self._core_defs_invalid_for_json_schema:
            raise self._core_defs_invalid_for_json_schema[def_ref]
        return self.definitions.get(def_ref, None)

    def encode_default(self, dft: Any) -> Any:
        """デフォルト値をJSONシリアル化可能な値にエンコードします。

        これは、生成されたJSONスキーマのフィールドのデフォルト値をエンコードするために使用されます。

        Args:
            dft: エンコードするデフォルト値。

        Returns:
            エンコードされたデフォルト値。
        """
        from .type_adapter import TypeAdapter, _type_has_config

        config = self._config
        try:
            default = (
                dft
                if _type_has_config(type(dft))
                else TypeAdapter(type(dft), config=config.config_dict).dump_python(dft, mode='json')
            )
        except PydanticSchemaGenerationError:
            raise pydantic_core.PydanticSerializationError(f'Unable to encode default value {dft}')

        return pydantic_core.to_jsonable_python(
            default,
            timedelta_mode=config.ser_json_timedelta,
            bytes_mode=config.ser_json_bytes,
        )

    def update_with_validations(
        self, json_schema: JsonSchemaValue, core_schema: CoreSchema, mapping: dict[str, str]
    ) -> None:
        """提供されたマッピングを使用してcore_schema内のキーをJSONスキーマの適切なキーに変換し、core_schemaで指定された対応する検証でjson_schemaを更新します。

        Args:
            json_schema: 更新するJSONスキーマ。
            core_schema: 検証を取得するコア・スキーマ。
            mapping: core_schema属性名から対応するJSONスキーマ属性名へのマッピングです。
        """
        for core_key, json_schema_key in mapping.items():
            if core_key in core_schema:
                json_schema[json_schema_key] = core_schema[core_key]

    class ValidationsMapping:
        """このクラスには、core_schema属性名から対応するJSONスキーマ属性名へのマッピングだけが含まれています。
        必要になる可能性は低いと思いますが、原則として、GenerateJsonSchemaのサブクラスでこのクラスをオーバーライドして(GenerateJsonSchema.Validation Mappingから継承することによって)、これらのマッピングを変更することができます。
        """

        numeric = {
            'multiple_of': 'multipleOf',
            'le': 'maximum',
            'ge': 'minimum',
            'lt': 'exclusiveMaximum',
            'gt': 'exclusiveMinimum',
        }
        bytes = {
            'min_length': 'minLength',
            'max_length': 'maxLength',
        }
        string = {
            'min_length': 'minLength',
            'max_length': 'maxLength',
            'pattern': 'pattern',
        }
        array = {
            'min_length': 'minItems',
            'max_length': 'maxItems',
        }
        object = {
            'min_length': 'minProperties',
            'max_length': 'maxProperties',
        }
        date = {
            'le': 'maximum',
            'ge': 'minimum',
            'lt': 'exclusiveMaximum',
            'gt': 'exclusiveMinimum',
        }

    def get_flattened_anyof(self, schemas: list[JsonSchemaValue]) -> JsonSchemaValue:
        members = []
        for schema in schemas:
            if len(schema) == 1 and 'anyOf' in schema:
                members.extend(schema['anyOf'])
            else:
                members.append(schema)
        members = _deduplicate_schemas(members)
        if len(members) == 1:
            return members[0]
        return {'anyOf': members}

    def get_json_ref_counts(self, json_schema: JsonSchemaValue) -> dict[JsonRef, int]:
        """json_schema内の任意の場所にあるキー'$ref'に対応するすべての値を取得します。"""
        json_refs: dict[JsonRef, int] = Counter()

        def _add_json_refs(schema: Any) -> None:
            if isinstance(schema, dict):
                if '$ref' in schema:
                    json_ref = JsonRef(schema['$ref'])
                    if not isinstance(json_ref, str):
                        return  # in this case, '$ref' might have been the name of a property
                    already_visited = json_ref in json_refs
                    json_refs[json_ref] += 1
                    if already_visited:
                        return  # prevent recursion on a definition that was already visited
                    defs_ref = self.json_to_defs_refs[json_ref]
                    if defs_ref in self._core_defs_invalid_for_json_schema:
                        raise self._core_defs_invalid_for_json_schema[defs_ref]
                    _add_json_refs(self.definitions[defs_ref])

                for v in schema.values():
                    _add_json_refs(v)
            elif isinstance(schema, list):
                for v in schema:
                    _add_json_refs(v)

        _add_json_refs(json_schema)
        return json_refs

    def handle_invalid_for_json_schema(self, schema: CoreSchemaOrField, error_info: str) -> JsonSchemaValue:
        raise PydanticInvalidForJsonSchema(f'Cannot generate a JsonSchema for {error_info}')

    def emit_warning(self, kind: JsonSchemaWarningKind, detail: str) -> None:
        """このメソッドは、`warning_message`メソッドでの処理に基づいて、単にPydantictJsonSchemaWarningsを生成します。"""
        message = self.render_warning_message(kind, detail)
        if message is not None:
            warnings.warn(message, PydanticJsonSchemaWarning)

    def render_warning_message(self, kind: JsonSchemaWarningKind, detail: str) -> str | None:
        """このメソッドは、必要に応じて警告を無視し、警告メッセージをフォーマットします。

        GenerateJsonSchemaのサブクラスの`ignored_warning_kind`の値をオーバーライドして、生成される警告を変更することができます。
        より詳細な制御が必要な場合は、このメソッドをオーバーライドできます。
        警告を表示したくない場合は、Noneを返してください。

        Args:
            kind: 表示する警告の種類。次のいずれかになります。

                - 'skipped-choice': 有効な選択肢がないため、選択肢フィールドがスキップされました。
                - 'non-serializable-default': JSONシリアル化できなかったため、デフォルト値がスキップされました。

            detail:警告に関する追加の詳細を含む文字列。

        Returns:
            書式設定された警告メッセージ。警告を表示しない場合は`None`。
        """
        if kind in self.ignored_warning_kinds:
            return None
        return f'{detail} [{kind}]'

    def _build_definitions_remapping(self) -> _DefinitionsRemapping:
        defs_to_json: dict[DefsRef, JsonRef] = {}
        for defs_refs in self._prioritized_defsref_choices.values():
            for defs_ref in defs_refs:
                json_ref = JsonRef(self.ref_template.format(model=defs_ref))
                defs_to_json[defs_ref] = json_ref

        return _DefinitionsRemapping.from_prioritized_choices(
            self._prioritized_defsref_choices, defs_to_json, self.definitions
        )

    def _garbage_collect_definitions(self, schema: JsonSchemaValue) -> None:
        visited_defs_refs: set[DefsRef] = set()
        unvisited_json_refs = _get_all_json_refs(schema)
        while unvisited_json_refs:
            next_json_ref = unvisited_json_refs.pop()
            next_defs_ref = self.json_to_defs_refs[next_json_ref]
            if next_defs_ref in visited_defs_refs:
                continue
            visited_defs_refs.add(next_defs_ref)
            unvisited_json_refs.update(_get_all_json_refs(self.definitions[next_defs_ref]))

        self.definitions = {k: v for k, v in self.definitions.items() if k in visited_defs_refs}


# ##### Start JSON Schema Generation Functions #####


def model_json_schema(
    cls: type[BaseModel] | type[PydanticDataclass],
    by_alias: bool = True,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    mode: JsonSchemaMode = 'validation',
) -> dict[str, Any]:
    """モデルのJSONスキーマを生成するユーティリティ関数。

    Args:
        cls: JSONスキーマを生成するためのモデル・クラスです。
        by_alias: `True`(デフォルト)の場合、フィールドはエイリアスに従ってシリアライズされます。`False`の場合、フィールドは属性名に従ってシリアライズされます。
        ref_template: JSONスキーマ参照の生成に使用するテンプレートです。
        schema_generator: JSONスキーマの生成に使用するクラス。
        mode: JSONスキーマの生成に使用するモード。次のいずれかになります。
            - 'validation':データを検証するためのJSONスキーマを生成します。
            - 'serialization':データをシリアライズするためのJSONスキーマを生成します。

    Returns:
        生成されたJSONスキーマ。
    """
    from .main import BaseModel

    schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)

    if isinstance(cls.__pydantic_core_schema__, _mock_val_ser.MockCoreSchema):
        cls.__pydantic_core_schema__.rebuild()

    if cls is BaseModel:
        raise AttributeError('model_json_schema() must be called on a subclass of BaseModel, not BaseModel itself.')

    assert not isinstance(cls.__pydantic_core_schema__, _mock_val_ser.MockCoreSchema), 'this is a bug! please report it'
    return schema_generator_instance.generate(cls.__pydantic_core_schema__, mode=mode)


def models_json_schema(
    models: Sequence[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode]],
    *,
    by_alias: bool = True,
    title: str | None = None,
    description: str | None = None,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
) -> tuple[dict[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode], JsonSchemaValue], JsonSchemaValue]:
    """複数のモデルのJSONスキーマを生成するユーティリティ関数。

    Args:
        by_alias: 生成されたJSONスキーマでフィールドのエイリアスをキーとして使用するかどうか。
        title: 生成されたJSONスキーマのタイトル。
        description: 生成されたJSONスキーマの説明。
        ref_template: JSONスキーマ参照の生成に使用する参照テンプレートです。
        schema_generator: JSONスキーマの生成に使用するスキーマ・ジェネレーターです。

    Returns:
        次の条件を満たすタプル:
            - 最初の要素は、JSONスキーマ・キー・タイプとJSONモードのタプルをキーとし、その入力ペアに対応するJSONスキーマを値とする辞書です
            (これらのスキーマは、2番目に返された要素で定義されている定義へのJsonRef参照を持つ場合があります)。
            - 2番目の要素は、最初に返された要素で参照されるすべての定義と、オプションのtitleおよびdescriptionキーを含むJSONスキーマです。
    """
    for cls, _ in models:
        if isinstance(cls.__pydantic_core_schema__, _mock_val_ser.MockCoreSchema):
            cls.__pydantic_core_schema__.rebuild()

    instance = schema_generator(by_alias=by_alias, ref_template=ref_template)
    inputs: list[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode, CoreSchema]] = [
        (m, mode, m.__pydantic_core_schema__) for m, mode in models
    ]
    json_schemas_map, definitions = instance.generate_definitions(inputs)

    json_schema: dict[str, Any] = {}
    if definitions:
        json_schema['$defs'] = definitions
    if title:
        json_schema['title'] = title
    if description:
        json_schema['description'] = description

    return json_schemas_map, json_schema


# ##### End JSON Schema Generation Functions #####


_HashableJsonValue: TypeAlias = Union[
    int, float, str, bool, None, Tuple['_HashableJsonValue', ...], Tuple[Tuple[str, '_HashableJsonValue'], ...]
]


def _deduplicate_schemas(schemas: Iterable[JsonDict]) -> list[JsonDict]:
    return list({_make_json_hashable(schema): schema for schema in schemas}.values())


def _make_json_hashable(value: JsonValue) -> _HashableJsonValue:
    if isinstance(value, dict):
        return tuple(sorted((k, _make_json_hashable(v)) for k, v in value.items()))
    elif isinstance(value, list):
        return tuple(_make_json_hashable(v) for v in value)
    else:
        return value


def _sort_json_schema(value: JsonSchemaValue, parent_key: str | None = None) -> JsonSchemaValue:
    if isinstance(value, dict):
        sorted_dict: dict[str, JsonSchemaValue] = {}
        keys = value.keys()
        if (parent_key != 'properties') and (parent_key != 'default'):
            keys = sorted(keys)
        for key in keys:
            sorted_dict[key] = _sort_json_schema(value[key], parent_key=key)
        return sorted_dict
    elif isinstance(value, list):
        sorted_list: list[JsonSchemaValue] = []
        for item in value:  # type: ignore
            sorted_list.append(_sort_json_schema(item, parent_key))
        return sorted_list  # type: ignore
    else:
        return value


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class WithJsonSchema:
    """Usage docs: ../concepts/json_schema/#withjsonschema-annotation

    これをフィールドのアノテーションとして追加し、そのフィールドに対して生成される(ベース)JSONスキーマをオーバーライドします。
    これにより、pydantic.json_schema.GenerateJsonSchemaのカスタムサブクラスを作成しなくても、CallableなどのJSONスキーマの生成時にエラーが発生する型や、is-instanceコアスキーマを持つ型に対してJSONスキーマを設定する方法が提供される。
    通常行われるスキーマへの変更(モデルフィールドのタイトルの設定など)は
    が実行されます。

    `mode`が設定されている場合、これはそのスキーマ生成モードにのみ適用され、検証とシリアライゼーションのために異なるjsonスキーマを設定できます。
    """

    json_schema: JsonSchemaValue | None
    mode: Literal['validation', 'serialization'] | None = None

    def __get_pydantic_json_schema__(
        self, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        mode = self.mode or handler.mode
        if mode != handler.mode:
            return handler(core_schema)
        if self.json_schema is None:
            # This exception is handled in pydantic.json_schema.GenerateJsonSchema._named_required_fields_schema
            raise PydanticOmit
        else:
            return self.json_schema

    def __hash__(self) -> int:
        return hash(type(self.mode))


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class Examples:
    """JSONスキーマに例を追加します。

    例は、例の名前(文字列)から例の値(任意の有効なJSON)へのマップである必要があります。

    `mode`が設定されている場合、これはそのスキーマ生成モードにのみ適用され、検証とシリアライゼーションのために別の例を追加できます。
    """

    examples: dict[str, Any]
    mode: Literal['validation', 'serialization'] | None = None

    def __get_pydantic_json_schema__(
        self, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        mode = self.mode or handler.mode
        json_schema = handler(core_schema)
        if mode != handler.mode:
            return json_schema
        examples = json_schema.get('examples', {})
        examples.update(to_jsonable_python(self.examples))
        json_schema['examples'] = examples
        return json_schema

    def __hash__(self) -> int:
        return hash(type(self.mode))


def _get_all_json_refs(item: Any) -> set[JsonRef]:
    """Get all the definitions references from a JSON schema."""
    refs: set[JsonRef] = set()
    stack = [item]

    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                if key == '$ref' and isinstance(value, str):
                    refs.add(JsonRef(value))
                elif isinstance(value, dict):
                    stack.append(value)
                elif isinstance(value, list):
                    stack.extend(value)
        elif isinstance(current, list):
            stack.extend(current)

    return refs


AnyType = TypeVar('AnyType')

if TYPE_CHECKING:
    SkipJsonSchema = Annotated[AnyType, ...]
else:

    @dataclasses.dataclass(**_internal_dataclass.slots_true)
    class SkipJsonSchema:
        """Usage docs: ../concepts/json_schema/#skipjsonschema-annotation

        これをアノテーションとしてフィールドに追加すると、そのフィールドのJSONスキーマの生成がスキップされます。

        Example:
            ```py
            from typing import Union

            from pydantic import BaseModel
            from pydantic.json_schema import SkipJsonSchema

            from pprint import pprint


            class Model(BaseModel):
                a: Union[int, None] = None  # (1)!
                b: Union[int, SkipJsonSchema[None]] = None  # (2)!
                c: SkipJsonSchema[Union[int, None]] = None  # (3)!


            pprint(Model.model_json_schema())
            '''
            {
                'properties': {
                    'a': {
                        'anyOf': [
                            {'type': 'integer'},
                            {'type': 'null'}
                        ],
                        'default': None,
                        'title': 'A'
                    },
                    'b': {
                        'default': None,
                        'title': 'B',
                        'type': 'integer'
                    }
                },
                'title': 'Model',
                'type': 'object'
            }
            '''
            ```

            1. integer型とnull型はどちらも`a`のスキーマに含まれています。
            2. integer型は、`b`のスキーマに含まれる唯一の型です。
            3. `c`フィールド全体がスキーマから省略されます。
        """

        def __class_getitem__(cls, item: AnyType) -> AnyType:
            return Annotated[item, cls()]

        def __get_pydantic_json_schema__(
            self, core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            raise PydanticOmit

        def __hash__(self) -> int:
            return hash(type(self))


def _get_typed_dict_cls(schema: core_schema.TypedDictSchema) -> type[Any] | None:
    metadata = _core_metadata.CoreMetadataHandler(schema).metadata
    cls = metadata.get('pydantic_typed_dict_cls')
    return cls


def _get_typed_dict_config(cls: type[Any] | None) -> ConfigDict:
    if cls is not None:
        try:
            return _decorators.get_attribute_from_bases(cls, '__pydantic_config__')
        except AttributeError:
            pass
    return {}
