"""`version`モジュールは、Pydanticのバージョン情報を保持します。"""



from __future__ import annotations as _annotations

__all__ = 'VERSION', 'version_info'

VERSION = '2.9.0a1'
"""Pydanticのバージョン"""


def version_short() -> str:
    """Pydanticバージョンの`major.minor`部分を返します。

    Pydanticのバージョンが'2.1.1'の場合は'2.1'を返します。
    """
    return '.'.join(VERSION.split('.')[:2])


def version_info() -> str:
    """Pydanticとその依存関係の完全なバージョン情報を返します。"""


    import importlib.metadata as importlib_metadata
    import os
    import platform
    import sys
    from pathlib import Path

    import pydantic_core._pydantic_core as pdc

    from ._internal import _git as git

    # get data about packages that are closely related to pydantic, use pydantic or often conflict with pydantic
    package_names = {
        'email-validator',
        'fastapi',
        'mypy',
        'pydantic-extra-types',
        'pydantic-settings',
        'pyright',
        'typing_extensions',
    }
    related_packages = []

    for dist in importlib_metadata.distributions():
        name = dist.metadata['Name']
        if name in package_names:
            related_packages.append(f'{name}-{dist.version}')

    pydantic_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    most_recent_commit = (
        git.git_revision(pydantic_dir) if git.is_git_repo(pydantic_dir) and git.have_git() else 'unknown'
    )

    info = {
        'pydantic version': VERSION,
        'pydantic-core version': pdc.__version__,
        'pydantic-core build': getattr(pdc, 'build_info', None) or pdc.build_profile,
        'install path': Path(__file__).resolve().parent,
        'python version': sys.version,
        'platform': platform.platform(),
        'related packages': ' '.join(related_packages),
        'commit': most_recent_commit,
    }
    return '\n'.join('{:>30} {}'.format(k + ':', str(v).replace('\n', ' ')) for k, v in info.items())


def parse_mypy_version(version: str) -> tuple[int, ...]:
    """mypy文字列バージョンをintのタプルに解析します。

    `0.930`のような通常のバージョンと、`0.940+dev.04cac4b5d911c4f9529e6ce86a27b44f28846f5d.dirty`のような`+`記号が後に続く追加情報を解析します。

    Args:
        version: mypyのバージョン文字列。

    Returns:
        intのタプル。例:(0, 930)。
    """
    return tuple(map(int, version.partition('+')[0].split('.')))
