"""`datetime_parse`モジュールはV1からのバックポートモジュールです。"""


from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__)
