"""エイリアス構成のサポート."""

from __future__ import annotations

import dataclasses
from typing import Any, Callable, Literal

from pydantic_core import PydanticUndefined

from ._internal import _internal_dataclass

__all__ = ('AliasGenerator', 'AliasPath', 'AliasChoices')


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class AliasPath:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/alias#aliaspath-and-aliaschoices

    エイリアスを作成するために`validation_alias`によって使用されるデータクラス。

    Attributes:
        path: 文字列または整数のエイリアスのリスト。
    """

    path: list[int | str]

    def __init__(self, first_arg: str, *args: str | int) -> None:
        self.path = [first_arg] + list(args)

    def convert_to_aliases(self) -> list[str | int]:
        """引数を文字列または整数のエイリアスのリストに変換します。

        Returns:
            別名のリスト.
        """
        return self.path

    def search_dict_for_path(self, d: dict) -> Any:
        """エイリアスで指定されたパスを辞書で検索します。

        Returns:
            指定されたパスの値、またはパスが見つからない場合は`PydanticUndefined`。
        """
        v = d
        for k in self.path:
            if isinstance(v, str):
                # disallow indexing into a str, like for AliasPath('x', 0) and x='abc'
                return PydanticUndefined
            try:
                v = v[k]
            except (KeyError, IndexError, TypeError):
                return PydanticUndefined
        return v


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class AliasChoices:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/alias#aliaspath-and-aliaschoices

    エイリアスを作成するために`validation_alias`によって使用されるデータクラス。

    Attributes:
        choices: 文字列または`AliasPath`を含むリスト。
    """

    choices: list[str | AliasPath]

    def __init__(self, first_choice: str | AliasPath, *choices: str | AliasPath) -> None:
        self.choices = [first_choice] + list(choices)

    def convert_to_aliases(self) -> list[list[str | int]]:
        """引数を、文字列または整数のエイリアスを含むリストのリストに変換します。

        Returns:
            別名のリスト。
        """
        aliases: list[list[str | int]] = []
        for c in self.choices:
            if isinstance(c, AliasPath):
                aliases.append(c.convert_to_aliases())
            else:
                aliases.append([c])
        return aliases


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class AliasGenerator:
    """Usage docs: https://yodai-yodai.github.io/translated/pydantic-docs-ja/concepts/alias#using-an-aliasgenerator

    さまざまなエイリアスを簡単に作成するために`alias_generator`が使用するデータクラスです。

    Attributes:
        alias: フィールド名を受け取り、そのエイリアスを返す呼び出し可能オブジェクト。
        validation_alias: フィールド名を受け取り、その検証エイリアスを返す呼び出し可能オブジェクト。
        serialization_alias: フィールド名を取り、そのシリアライゼーション・エイリアスを返す呼び出し可能オブジェクト。
    """

    alias: Callable[[str], str] | None = None
    validation_alias: Callable[[str], str | AliasPath | AliasChoices] | None = None
    serialization_alias: Callable[[str], str] | None = None

    def _generate_alias(
        self,
        alias_kind: Literal['alias', 'validation_alias', 'serialization_alias'],
        allowed_types: tuple[type[str] | type[AliasPath] | type[AliasChoices], ...],
        field_name: str,
    ) -> str | AliasPath | AliasChoices | None:
        """指定された種類のエイリアスを生成します.エイリアスジェネレータがNoneの場合は、Noneを返します。

        Raises:
            TypeError: エイリアスジェネレータが無効な型を生成した場合。
        """
        alias = None
        if alias_generator := getattr(self, alias_kind):
            alias = alias_generator(field_name)
            if alias and not isinstance(alias, allowed_types):
                raise TypeError(
                    f'Invalid `{alias_kind}` type. `{alias_kind}` generator must produce one of `{allowed_types}`'
                )
        return alias

    def generate_aliases(self, field_name: str) -> tuple[str | None, str | AliasPath | AliasChoices | None, str | None]:
        """フィールドの`alias`、`validation_alias`、`serialization_alias`を生成します。

        Returns:
            3つのエイリアス(バリデーション、エイリアス、シリアル化)のタプル。
        """
        alias = self._generate_alias('alias', (str,), field_name)
        validation_alias = self._generate_alias('validation_alias', (str, AliasChoices, AliasPath), field_name)
        serialization_alias = self._generate_alias('serialization_alias', (str,), field_name)

        return alias, validation_alias, serialization_alias  # type: ignore
