{% include-markdown "./warning.md" %}

<!-- Installation is as simple as: -->
インストールは簡単です。

```bash
pip install pydantic
```

<!-- Pydantic has a few dependencies: -->
Pydanticにはいくつかの依存関係があります。

<!--
* [`pydantic-core`](https://pypi.org/project/pydantic-core/): Core validation logic for _pydantic_ written in rust.
* [`typing-extensions`](https://pypi.org/project/typing-extensions/): Backport of the standard library [typing][] module.
* [`annotated-types`](https://pypi.org/project/annotated-types/): Reusable constraint types to use with [`typing.Annotated`][].
-->
* [`pydantic-core`](https://pypi.org/project/pydantic-core/): rustで書かれた_pydantic_のコア検証ロジック。
* [`typing-extensions`](https://pypi.org/project/typing-extension/): 標準ライブラリ[typing][]モジュールのバックポート。
* [`annotated-types`](https://pypi.org/project/annotated-types/): [`typing.Annotated`][]で使用する再利用可能な制約タイプ。

<!-- If you've got Python 3.8+ and `pip` installed, you're good to go. -->
Python 3.8以降と`pip`がインストールされていれば、問題ありません。

<!-- Pydantic is also available on [conda](https://www.anaconda.com) under the [conda-forge](https://conda-forge.org) -->
Pydanticは、[conda-forge](https://conda-forge.org)の下の[conda](https://www.anaconda.com)でも利用できます。

<!-- channel: -->
チャネル:

```bash
conda install pydantic -c conda-forge
```

## Optional dependencies

<!-- Pydantic has the following optional dependencies: -->
Pydanticには、次のオプションの依存関係があります。

<!-- * If you require email validation, you can add [email-validator](https://github.com/JoshData/python-email-validator). -->
* Eメールの検証が必要な場合は、[email-validator](https://github.com/JoshData/python-email-validator)を追加できます。

<!-- To install optional dependencies along with Pydantic: -->
Pydanticと一緒にオプションの依存関係をインストールするには、次のようにします。

```bash
pip install pydantic[email]
```

<!-- Of course, you can also install requirements manually with `pip install email-validator`. -->
もちろん、`pip install email-validator`を使って手動で必要な依存関係をインストールすることもできます。

## Install from repository

<!-- And if you prefer to install Pydantic directly from the repository: -->
また、リポジトリから直接Pydanticをインストールしたい場合は、次のようにします。

```bash
pip install git+https://github.com/pydantic/pydantic@main#egg=pydantic
# or with extras
pip install git+https://github.com/pydantic/pydantic@main#egg=pydantic[email]
```
