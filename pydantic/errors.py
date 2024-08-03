"""Pydantic固有のエラー"""

from __future__ import annotations as _annotations

import re

from typing_extensions import Literal, Self

from ._migration import getattr_migration
from .version import version_short

__all__ = (
    'PydanticUserError',
    'PydanticUndefinedAnnotation',
    'PydanticImportError',
    'PydanticSchemaGenerationError',
    'PydanticInvalidForJsonSchema',
    'PydanticErrorCodes',
)

# We use this URL to allow for future flexibility about how we host the docs, while allowing for Pydantic
# code in the while with "old" URLs to still work.
# 'u' refers to "user errors" - e.g. errors caused by developers using pydantic, as opposed to validation errors.
DEV_ERROR_DOCS_URL = f'https://errors.pydantic.dev/{version_short()}/u/'
PydanticErrorCodes = Literal[
    'class-not-fully-defined',
    'custom-json-schema',
    'decorator-missing-field',
    'discriminator-no-field',
    'discriminator-alias-type',
    'discriminator-needs-literal',
    'discriminator-alias',
    'discriminator-validator',
    'callable-discriminator-no-tag',
    'typed-dict-version',
    'model-field-overridden',
    'model-field-missing-annotation',
    'config-both',
    'removed-kwargs',
    'invalid-for-json-schema',
    'json-schema-already-used',
    'base-model-instantiated',
    'undefined-annotation',
    'schema-for-unknown-type',
    'import-error',
    'create-model-field-definitions',
    'create-model-config-base',
    'validator-no-fields',
    'validator-invalid-fields',
    'validator-instance-method',
    'root-validator-pre-skip',
    'model-serializer-instance-method',
    'validator-field-config-info',
    'validator-v1-signature',
    'validator-signature',
    'field-serializer-signature',
    'model-serializer-signature',
    'multiple-field-serializers',
    'invalid-annotated-type',
    'type-adapter-config-unused',
    'root-model-extra',
    'unevaluable-type-annotation',
    'dataclass-init-false-extra-allow',
    'clashing-init-and-init-var',
    'model-config-invalid-field-name',
    'with-config-on-model',
    'dataclass-on-model',
]


class PydanticErrorMixin:
    """すべてのPydantic固有のエラーによって共有される共通機能のためのミックスインクラス。

    Attributes:
        message: エラーを説明するメッセージ。
        code: PydanticErrorCodes列挙型からのオプションのエラーコード。
    """

    def __init__(self, message: str, *, code: PydanticErrorCodes | None) -> None:
        self.message = message
        self.code = code

    def __str__(self) -> str:
        if self.code is None:
            return self.message
        else:
            return f'{self.message}\n\nFor further information visit {DEV_ERROR_DOCS_URL}{self.code}'


class PydanticUserError(PydanticErrorMixin, TypeError):
    """Pydanticの使用が正しくないために発生したエラーです。"""


class PydanticUndefinedAnnotation(PydanticErrorMixin, NameError):
    """`CoreSchema`の生成中に未定義の注釈を処理すると、`NameError`のサブクラスが発生します。

    Attributes:
        name: エラーの名前。
        message: エラーの説明。
    """

    def __init__(self, name: str, message: str) -> None:
        self.name = name
        super().__init__(message=message, code='undefined-annotation')

    @classmethod
    def from_name_error(cls, name_error: NameError) -> Self:
        """`NameError`を`PydanticUndefinedAnnotation`エラーに変換します。

        Args:
            name_error: `NameError`を変換します。

        Returns:
            `PydanticUndefinedAnnotation`エラーを変換しました。
        """
        try:
            name = name_error.name  # type: ignore  # python > 3.10
        except AttributeError:
            name = re.search(r".*'(.+?)'", str(name_error)).group(1)  # type: ignore[union-attr]
        return cls(name=name, message=str(name_error))


class PydanticImportError(PydanticErrorMixin, ImportError):
    """V1とV2の間でモジュールが変更されたためにインポートが失敗した場合に発生するエラー。

    Attributes:
        message: エラーの説明。
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code='import-error')


class PydanticSchemaGenerationError(PydanticUserError):
    """あるタイプの`CoreSchema`の生成に失敗したときに発生したエラー。

    Attributes:
        message: エラーの説明。
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code='schema-for-unknown-type')


class PydanticInvalidForJsonSchema(PydanticUserError):
    """一部の`CoreSchema`のJSONスキーマの生成に失敗したときに発生したエラー。

    Attributes:
        message: エラーの説明。
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code='invalid-for-json-schema')


__getattr__ = getattr_migration(__name__)
