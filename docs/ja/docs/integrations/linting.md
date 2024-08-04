{% include-markdown "../warning.md" %}

## Flake8 plugin

<!-- If using Flake8 in your project, a [plugin](https://pypi.org/project/flake8-pydantic/) is available and can be installed using the following: -->
プロジェクトでFlake8を使用している場合は、[プラグイン](https://pypi.org/project/Flake8-pydantic/)が利用でき、以下を使用してインストールできます。

```bash
pip install flake8-pydantic
```

<!-- The lint errors provided by this plugin are namespaced under the `PYDXXX` code. To ignore some unwanted rules, the Flake8 configuration can be adapted: -->
このプラグインによって提供されるlintエラーは、`PYDXXX`コードの下に名前空間があります。いくつかの不要なルールを無視するために、Flake8の設定を適用することができる。

```ini
[flake8]
extend-ignore = PYD001,PYD002
```
