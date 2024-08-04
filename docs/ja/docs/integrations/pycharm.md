{% include-markdown "../warning.md" %}

<!-- While pydantic will work well with any IDE out of the box, a [PyCharm plugin](https://plugins.jetbrains.com/plugin/12861-pydantic)
offering improved pydantic integration is available on the JetBrains Plugins Repository for PyCharm.
You can install the plugin for free from the plugin marketplace (PyCharm's Preferences -> Plugin -> Marketplace -> search "pydantic"). -->
pydanticはどんなIDEでもすぐに動作しますが、[PyCharm plugin](https://plugins.jetbrains.com/plugin/12861-pydantic)
PyCharmのJetBrains Plugins Repositoryでは、pydantic統合の改善が提供されています。
プラグインは、プラグイン・マーケットプレイス(PyCharmのPreferences->Plugin->Marketplace->search"pydantic")から無料でインストールできます。

<!-- The plugin currently supports the following features: -->
このプラグインは現在、次の機能をサポートしています。

<!-- * For `pydantic.BaseModel.__init__`:
  * Inspection
  * Autocompletion
  * Type-checking -->

* `pydantic.BaseModel.__init__`の場合:
  * 検査
  * オートコンプリート
  * 型チェック


<!-- * For fields of `pydantic.BaseModel`:
  * Refactor-renaming fields updates `__init__` calls, and affects sub- and super-classes
  * Refactor-renaming `__init__` keyword arguments updates field names, and affects sub- and super-classes -->
* `pydantic.BaseModel`のフィールドでは:
  * リファクタリングによるフィールド名の変更は`__init__`呼び出しを更新し、サブクラスとスーパークラスに影響を与えます。
  * リファクタリング-`__init__`キーワード引数の名前を変更すると、フィールド名が更新され、サブクラスとスーパークラスに影響します。

<!-- More information can be found on the [official plugin page](https://plugins.jetbrains.com/plugin/12861-pydantic) and [Github repository](https://github.com/koxudaxi/pydantic-pycharm-plugin). -->
詳細については、[公式プラグインページ](https://plugins.jetbrains.com/plugin/12861-pydantic)および[Githubリポジトリ](https://github.com/koxudaxi/pydantic-pycharm-plugin)を参照してください。
