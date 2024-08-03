"""Pydantic固有のワーニング。"""


from __future__ import annotations as _annotations

from .version import version_short

__all__ = (
    'PydanticDeprecatedSince20',
    'PydanticDeprecationWarning',
    'PydanticDeprecatedSince26',
    'PydanticExperimentalWarning',
)


class PydanticDeprecationWarning(DeprecationWarning):
    """Pydantic固有の非推奨ワーニングです。

    このワーニングは、Pydanticで非推奨の機能を使用する場合に発生します。非推奨が導入された時期と、対応する機能が削除される予定のバージョンに関する情報を提供します。

    Attributes:
        message: ワーニングの説明。
        since: 非推奨になったPydanticバージョン。
        expected_removal: 対応する機能が削除されると予想されるPydanticバージョン。
    """

    message: str
    since: tuple[int, int]
    expected_removal: tuple[int, int]

    def __init__(
        self, message: str, *args: object, since: tuple[int, int], expected_removal: tuple[int, int] | None = None
    ) -> None:
        super().__init__(message, *args)
        self.message = message.rstrip('.')
        self.since = since
        self.expected_removal = expected_removal if expected_removal is not None else (since[0] + 1, 0)

    def __str__(self) -> str:
        message = (
            f'{self.message}. Deprecated in Pydantic V{self.since[0]}.{self.since[1]}'
            f' to be removed in V{self.expected_removal[0]}.{self.expected_removal[1]}.'
        )
        if self.since == (2, 0):
            message += f' See Pydantic V2 Migration Guide at https://errors.pydantic.dev/{version_short()}/migration/'
        return message


class PydanticDeprecatedSince20(PydanticDeprecationWarning):
    """Pydantic 2.0以降で非推奨となった機能を定義する特定の`PydanticDeprecationWarning`サブクラス。"""

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args, since=(2, 0), expected_removal=(3, 0))


class PydanticDeprecatedSince26(PydanticDeprecationWarning):
    """Pydantic 2.6以降で非推奨となった機能を定義する特定の`PydanticDeprecationWarning`サブクラス。"""

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args, since=(2, 0), expected_removal=(3, 0))


class GenericBeforeBaseModelWarning(Warning):
    pass


class PydanticExperimentalWarning(Warning):
    """Pydantic固有の実験的な機能に関するワーニング。

    このワーニングは、Pydanticで実験的な機能を使用している場合に発生する。
    これは、Pydanticの将来のバージョンで機能が変更または削除される可能性があることをユーザにワーニングするために提起された。
    """
