{% include-markdown "../warning.md" %}

<!-- [Hypothesis](https://hypothesis.readthedocs.io/) is the Python library for [property-based testing](https://increment.com/testing/in-praise-of-property-based-testing/).
Hypothesis can infer how to construct type-annotated classes, and supports builtin types, many standard library types, and generic types from the [`typing`](https://docs.python.org/3/library/typing.html) and [`typing_extensions`](https://pypi.org/project/typing-extensions/) modules by default. -->
[Hypothesis](https://hypothematic.readthedocs.io/)は、[property-based testing](https://increment.com/testing/in-praise-of-property-based-testing/)のPythonライブラリです。
Hypothesisは、型注釈付きクラスの構築方法を推測することができ、デフォルトで[`typing`](https://docs.python.org/3/library/typing.html)および[`typing_extensions`](https://pypi.org/project/typing-extension/)モジュールからの組み込み型、多くの標準ライブラリ型、および総称型をサポートしています。

<!-- Pydantic v2.0 drops built-in support for Hypothesis and no more ships with the integrated Hypothesis plugin. -->
Pydantic v2.0は、Hypothesisの組み込みサポートを廃止し、統合されたHypothesisプラグインは廃止しました。

!!! warning
    We are temporarily removing the Hypothesis plugin in favor of studying a different mechanism. For more information, see the issue [annotated-types/annotated-types#37](https://github.com/annotated-types/annotated-types/issues/37).
    別のメカニズムを研究するために、プラグインを一時的に削除しています。詳細については、問題[annotated-types/annotated-types#37](https://github.com/annotated-types/annotated-types/issues/37)を参照してください。

    <!-- The Hypothesis plugin may be back in a future release. Subscribe to [pydantic/pydantic#4682](https://github.com/pydantic/pydantic/issues/4682) for updates. -->
    Hypothesisプラグインは将来のリリースで復活する可能性があります。更新については、[pydantic/pydantic#4682](https://github.com/pydantic/pydantic/issues/4682)を購読してください。
