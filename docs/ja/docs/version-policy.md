{% include-markdown "./warning.md" %}

<!-- First of all, we recognize that the transitions from Pydantic V1 to V2 has been and will be painful for some users.
We're sorry about this pain :pray:, it was an unfortunate but necessary step to correct design mistakes of V1. -->
まず第一に、Pydantic V1からV2への移行は、一部のユーザにとって苦痛であり、これからも苦痛であることを認識しています。
私たちはこの苦痛についてお詫びします :pray:、これは不幸なことでしたが、V1の設計ミスを修正するために必要なステップでした。

**There will not be another breaking change of this magnitude!**

## Pydantic V1

<!-- Active development of V1 has already stopped, however critical bug fixes and security vulnerabilities will be fixed in V1 for **one year** after the release of V2 (June 30, 2024). -->
V1の積極的な開発はすでに中止されていますが、重大なバグ修正とセキュリティ脆弱性は、V2のリリース(2024年6月30日)から**1年間**V1で修正されます。

## Pydantic V2

<!-- We will not intentionally make breaking changes in minor releases of V2. -->
V2のマイナーリリースで意図的に重大な変更を加えることはありません。

<!-- Methods marked as `deprecated` will not be removed until the next major release, V3. -->
`deprecated`とマークされたメソッドは、次のメジャーリリースであるV3まで削除されません。

<!-- Of course some apparently safe changes and bug fixes will inevitably break some users' code &mdash; obligatory link to [XKCD](https://m.xkcd.com/1172/). -->
もちろん、一見安全な変更やバグ修正の中には、[XKCD](https://m.xkcd.com/1172/)への必須リンクなど、一部のユーザーのコードを破壊するものもあります。

<!-- The following changes will **NOT** be considered breaking changes, and may occur in minor releases: -->
以下の変更は、重大な変更とはみなされず、マイナーリリースで発生する可能性があります。

<!-- * Changing the format of `ref` as used in JSON Schema.
* Changing the `msg`, `ctx`, and `loc` fields of `ValidationError` errors. `type` will not change &mdash; if you're programmatically parsing error messages, you should use `type`.
* Adding new keys to `ValidationError` errors &mdash; e.g. we intend to add `line_number` and `column_number` to errors when validating JSON once we migrate to a new JSON parser.
* Adding new `ValidationError` errors.
* Changing `repr` even of public classes. -->
* JSONスキーマで使用される`ref`のフォーマットを変更します。
* `ValidationError`エラーの`msg`、`ctx`、`loc`フィールドを変更します。`type`は変更されません。プログラムでエラーメッセージを解析している場合は、`type`を使用する必要があります。
* `ValidationError`エラーに新しいキーを追加します。たとえば、新しいJSONパーサに移行した後、JSONを検証するときにエラーに`line_number`と`column_number`を追加する予定です。
* 新しい`ValidationError`エラーを追加します。
* パブリッククラスの「repr」も変更します。

<!-- In all cases we will aim to minimize churn and do so only when justified by the increase of quality of `pydantic` for users. -->
いずれの場合も、私たちはひっかきまわすことをを最小限に抑えることを目指し、ユーザーにとって「pydantic」の質の向上によって正当化される場合にのみ修正します。

## Pydantic V3 and beyond

<!-- We expect to make new major releases roughly once a year going forward, although as mentioned above, any associated breaking changes should be trivial to fix compared to the V1-to-V2 transition. -->
今後、新しいメジャーリリースはほぼ1年に1回行われる予定ですが、前述したように、関連する重大な変更は、V 1からV 2への移行と比較して簡単に修正できるはずです。

## Experimental Features

<!-- At Pydantic, we like to move quickly and innovate! To that end, we may introduce experimental features in minor releases. -->
Pydanticでは、私たちは迅速に行動し、革新することを望んでいます!そのために、マイナーリリースで実験的な機能を導入することがあります。

!!! abstract "Usage Documentation"
    <!-- To learn more about our current experimental features, see the [experimental features documentation](./concepts/experimental.md). -->
    現在の試験的な機能の詳細については、[experimental features documentation](./concepts/experimental.md)を参照してください。

<!-- Please keep in mind, experimental features are active works in progress. If these features are successful, they'll eventually beocme part of Pydantic. If unsuccessful, said features will be removed with little notice. While in its experimental phase, a feature's API and behaviors may not be stable, and it's very possible that changes made to the feature will not be backward-compatible. -->
実験的な機能は進行中の活発な作業であることを覚えておいてください。これらの機能が成功すれば、最終的にはPydanticの一部になるでしょう。失敗した場合、これらの機能はほとんど予告なしに削除されます。実験段階では、機能のAPIと動作が安定していない可能性があり、機能に加えられた変更が下位互換性を持たない可能性が非常に高くなります。

### Naming Conventions

<!-- We use one of the following naming conventions to indicate that a feature is experimental: -->
次の命名規則のいずれかを使用して、機能が試験的であることを示します。

<!-- 1. The feature is located in the `experimental` module. In this case, you can access the feature like this: -->
1. 機能は`experimental`モジュールにあります。この場合、次のように機能にアクセスできます。

    ```python test="skip" lint="skip"
    from pydantic.experimental import feature_name
    ```

<!-- 2. The feature is located in the main module, but prefixed with `experimental_`. This case occurs when we add a new field, argument, or method to an existing data structure already within the main `pydantic` module. -->
2. 機能はメインモジュールにありますが、先頭に`experimental_`が付いています。このケースは、メインの`pydantic`モジュール内にすでにある既存のデータ構造に新しいフィールド、引数、またはメソッドを追加したときに発生します。

<!-- New features with these naming conventions are subject to change or removal, and we are looking for feedback and suggestions before making them a permanent part of Pydantic. See the [feedback section](./concepts/experimental.md#feedback) for more information. -->
これらの命名規則を持つ新機能は変更または削除される可能性があり、Pydanticの恒久的な一部にする前にフィードバックと提案を求めています。詳細については、[feedback section](./concepts/experimental.md#feedback)を参照してください。

### Importing Experimental Features

<!-- When you import an experimental feature from the `experimental` module, you'll see a warning message that the feature is experimental. You can disable this warning with the following: -->
`experimental`モジュールから試験的な機能をインポートすると、その機能が試験的であることを示す警告メッセージが表示されます。この警告を無効にするには、次のようにします。

```python
import warnings

from pydantic import PydanticExperimentalWarning

warnings.filterwarnings('ignore', category=PydanticExperimentalWarning)
```

### Lifecycle of Experimental Features

<!-- 1. A new feature is added, either in the `experimental` module or with the `experimental_` prefix.
2. The behavior is often modified during patch/minor releases, with potential API/behavior changes.
3. If the feature is successful, we promote it to Pydantic with the following steps: -->
1. 新しい機能が`experimental`モジュールか`experimental_`プレフィックスで追加されます。
2. 動作は、パッチ/マイナーリリース中に変更されることが多く、API/動作が変更される可能性があります。
3. 機能が成功した場合は、次の手順でPydanticにプロモートします:
    <!-- a. If it was in the `experimental` module, the feature is cloned to Pydantic's main module. The original experimental feature still remains in the `experimental` module, but it will show a warning when used. If the feature was already in the main Pydantic module, we create a copy of the feature without the `experimental_` prefix, so the feature exists with both the official and experimental names. A deprecation warning is attached to the experimental version. -->
    a. それが`experimental`モジュールにあった場合、その機能はPydanticのメインモジュールにクローンされます。元の実験的な機能はまだ`experimental`モジュールに残っていますが、使用時に警告が表示されます。機能がすでにメインのPydanticモジュールにあった場合、`experimental_`プレフィックスなしで機能のコピーを作成するので、その機能は正式な名前と実験的な名前の両方で存在します。非推奨の警告は実験バージョンに添付されます。
    <!-- b. At some point, the code of the experimental feature is removed, but there will still be a stub of the feature that provides an error message with appropriate instructions. -->
    b. ある時点で、実験的な機能のコードは削除されますが、適切な指示とともにエラーメッセージを提供する機能のスタブがまだ存在します。
    <!-- c. As a last step, the experimental version of the feature is entirely removed from the codebase. -->
    c. 最後のステップとして、機能の実験バージョンがコードベースから完全に削除されます。

<!-- If the feature is unsuccessful or unpopular, it's removed with little notice. A stub will remain in the location of the deprecated feature with an error message. -->
機能が成功しなかったり、人気がない場合は、ほとんど通知なしに削除されます。スタブは、エラーメッセージとともに非推奨の機能の場所に残ります。

<!-- Thanks to [streamlit](https://docs.streamlit.io/develop/quick-reference/prerelease) for the inspiration for the lifecycle and naming conventions of our new experimental feature patterns. -->
新しい実験的な機能パターンのライフサイクルと命名規則のヒントを与えてくれた[streamlit](https://docs.streamlit.io/develop/quick-reference/prerelease)に感謝します。

## Support for Python versions

<!-- Pydantic will drop support for a Python version when the following conditions are met: -->
Pydanticは、次の条件が満たされた場合、Pythonバージョンのサポートを終了します。

<!-- * The Python version has reached [EOL](https://devguide.python.org/versions/).
* <5% of downloads of the most recent minor release need to be using that version. -->
* Pythonのバージョンが[EOL]に達したとき(https://devguide.python.org/versions/)。
* 最新のマイナーリリースのダウンロードの5%未満しかそのバージョンを使用していないとき。
