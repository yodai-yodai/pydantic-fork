"""Type annotations to use with `__get_pydantic_core_schema__` and `__get_pydantic_json_schema__`."""

from __future__ import annotations as _annotations

from typing import TYPE_CHECKING, Any, Union

from pydantic_core import core_schema

if TYPE_CHECKING:
    from .json_schema import JsonSchemaMode, JsonSchemaValue

    CoreSchemaOrField = Union[
        core_schema.CoreSchema,
        core_schema.ModelField,
        core_schema.DataclassField,
        core_schema.TypedDictField,
        core_schema.ComputedField,
    ]

__all__ = 'GetJsonSchemaHandler', 'GetCoreSchemaHandler'


class GetJsonSchemaHandler:
    """次のJSONスキーマ生成関数を呼び出すハンドラです。

    Attributes:
        mode:   Jsonスキーマモードで、`validation`または`serialization`。
    """

    mode: JsonSchemaMode

    def __call__(self, core_schema: CoreSchemaOrField, /) -> JsonSchemaValue:
        """内部ハンドラを呼び出して、返されるJsonSchemaValueを取得します。
        これは、`pydantic.json_schema.GenerateJsonSchema`を呼び出すまで、次のJSONスキーマ修正関数を呼び出します。
        JSONスキーマを生成できない場合は、`pydantic.errors.PydanticInvalidForJsonSchema`エラー。

        Args:
            core_schema: `pydantic_core.core_schema.CoreSchema`

        Returns:
            JsonSchemaValue:内部JSONスキーマ変更関数によって生成されるJSONスキーマ。
        """
        raise NotImplementedError

    def resolve_ref_schema(self, maybe_ref_json_schema: JsonSchemaValue, /) -> JsonSchemaValue:
        """`{"$ref": ...}`スキーマの実際のスキーマを取得します。
        指定したスキーマが`$ref`スキーマでない場合は、そのまま返されます。
        つまり、この関数を呼び出す前にチェックする必要はありません。

        Args:
            maybe_ref_json_schema: `$ref`スキーマの可能性があるJsonSchemaValue。

        Raises:
            LookupError: 参照が見つからない場合。

        Returns:
            JsonSchemaValue: `$ref`を持たないJsonSchemaValue。
        """
        raise NotImplementedError


class GetCoreSchemaHandler:
    """CoreSchemaスキーマ生成関数を呼び出すハンドラ。"""

    def __call__(self, source_type: Any, /) -> core_schema.CoreSchema:
        """内部ハンドラを呼び出して、返されるCoreSchemaを取得します。
        これは、Pydanticの内部スキーマ生成機構を呼び出すまで、次のCoreSchema修正関数を呼び出します。
        指定されたソースタイプのCoreSchemaを生成できない場合は、`pydantic.errors.PydanticSchemaGenerationError`エラーが発生します。

        Args:
            source_type: 入力タイプ。

        Returns:
            CoreSchema: 生成された`pydantic-core`CoreSchema。
        """
        raise NotImplementedError

    def generate_schema(self, source_type: Any, /) -> core_schema.CoreSchema:
        """現在のコンテキストに関連しないスキーマを生成します。
        この関数は、例えばシーケンスのスキーマ生成を処理していて、その項目のスキーマを生成したい場合に使用します。
        そうしないと、シーケンス自体を対象とした`min_length`制約を項目に適用するようなことになってしまいます。

        Args:
            source_type: 入力タイプ。

        Returns:
            CoreSchema: 生成された`pydantic-core`CoreSchema。
        """
        raise NotImplementedError

    def resolve_ref_schema(self, maybe_ref_schema: core_schema.CoreSchema, /) -> core_schema.CoreSchema:
        """`definition-ref`スキーマの実際のスキーマを取得します。
        指定されたスキーマが`definition-ref`スキーマでない場合は、そのまま返されます。
        つまり、この関数を呼び出す前にチェックする必要はありません。

        Args:
            maybe_ref_schema: `CoreSchema`で、`ref`ベースかどうか。

        Raises:
            LookupError: `ref`が見つからない場合。

        Returns:
            具体的な`CoreSchema`。
        """
        raise NotImplementedError

    @property
    def field_name(self) -> str | None:
        """このバリデータに最も近いフィールドの名前を取得します。"""
        raise NotImplementedError

    def _get_types_namespace(self) -> dict[str, Any] | None:
        """シリアライザ注釈の型解決中に使用される内部メソッド。"""
        raise NotImplementedError
