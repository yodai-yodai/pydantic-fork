# """`class_validators` module is a backport module from V1."""
"""`class_validators`モジュールはV1からのバックポートモジュールです。"""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__)
