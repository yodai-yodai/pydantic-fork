{% include-markdown "../warning.md" %}

<!-- `pydantic` integrates well with AWS Lambda functions. In this guide, we'll discuss how to setup `pydantic` for an AWS Lambda function. -->
`pydantic`はAWS Lambda関数とうまく統合されています。このガイドでは、AWS Lambda関数に`pydantic`を設定する方法について説明します。

## Installing Python libraries for AWS Lambda functions

<!-- There are many ways to utilize Python libraries in AWS Lambda functions. As outlined in the [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html), the most common approaches include: -->
AWS Lambda関数でPythonライブラリを利用する方法は数多くあります。[AWS Lambdaドキュメント](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)で概説されているように、最も一般的なアプローチには次のものがあります。

<!-- * Using a [`.zip` file archive](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html) to package your code and dependencies
* Using [AWS Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html) to share libraries across multiple functions
* Using a [container image](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html) to package your code and dependencies -->
* [`.zip` file archive](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html)を使用して、コードと依存関係をパッケージ化します。
* [AWS Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html)を使用して、複数の関数間でライブラリを共有します。
* [container image](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html)を使用してコードと依存関係をパッケージ化します。

<!-- All of these approaches can be used with `pydantic`.
The best approach for you will depend on your specific requirements and constraints. We'll cover the first two cases more in-depth here, as dependency management with a container image is more straightforward. If you're using a container image, you might find [this comment](https://github.com/pydantic/pydantic/issues/6557#issuecomment-1699456562) helpful for installing `pydantic`. -->
これらのアプローチはすべて`pydantic`で使用できます。
最適なアプローチは、特定の要件と制約によって異なります。コンテナイメージを使用した依存関係管理の方が簡単なので、ここでは最初の2つのケースについて詳しく説明します。コンテナイメージを使用している場合は、[this comment](https://github.com/pydantic/pydantic/issues/6557#issuecomment-1699456562)が`pydantic`のインストールに役立つことがわかります。

!!! tip
    <!-- If you use `pydantic` across multiple functions, you may want to consider AWS Lambda Layers, which support seamless sharing of libraries across multiple functions. -->
    複数の関数にわたって`pydantic`を使用する場合は、複数の関数間でライブラリをシームレスに共有できるAWS Lambda Layersを検討するとよいでしょう。

<!-- Regardless of the dependencies management approach you choose, it's beneficial to adhere to these guidelines to ensure a smooth dependency management process. -->
選択する依存関係管理の手法にかかわらず、円滑な依存関係管理プロセスを確実にするために、これらのガイドラインに従うことは有益です。

## Installing `pydantic` for AWS Lambda functions

<!-- When you're building your `.zip` file archive with your code and dependencies or organizing your `.zip` file for a Lambda Layer, you'll likely use a local virtual environment to install and manage your dependencies. This can be a bit tricky if you're using `pip` because `pip` installs wheels compiled for your local platform, which may not be compatible with the Lambda environment. -->
コードと依存関係を使用して`.zip`ファイルアーカイブを構築したり、`.zip`ファイルをLambda Layer用に整理したりする場合は、依存関係のインストールと管理にローカルの仮想環境を使用する可能性があります。`pip`を使用している場合、`pip`はローカルプラットフォーム用にコンパイルされたwheelsをインストールするため、これは少し厄介ですが、Lambda環境と互換性がない可能性があります。

Thus, we suggest you use a command similar to the following:

```bash
pip install \
    --platform manylinux2014_x86_64 \  # (1)!
    --target=<your_package_dir> \  # (2)!
    --implementation cp \  # (3)!
    --python-version 3.10 \  # (4)!
    --only-binary=:all: \  # (5)!
    --upgrade pydantic  # (6)!
```

<!-- 1. Use the platform corresponding to your Lambda runtime.
2. Specify the directory where you want to install the package (often `python` for Lambda Layers).
3. Use the CPython implementation.
4. The Python version must be compatible with the Lambda runtime.
5. This flag ensures that the package is installed pre-built binary wheels.
6. The latest version of `pydantic` will be installed. -->
1. Lambdaランタイムに対応するプラットフォームを使用します。
2. パッケージをインストールするディレクトリを指定します(Lambdaレイヤーの場合は`python`がよく使用されます)。
3. CPython実装を使用します。
4. PythonバージョンはLambdaランタイムと互換性がある必要があります。
5. このフラグは、パッケージが事前に構築されたバイナリホイールにインストールされていることを確認します。
6. `pydantic`の最新バージョンがインストールされます。

## Troubleshooting

### `no module named 'pydantic_core._pydantic_core'`

この
```
no module named `pydantic_core._pydantic_core`
```

<!-- error is a common issue that indicates you have installed `pydantic` incorrectly.
To debug this issue, you can try the following steps (before the failing import): -->
エラーは、`pydantic`が正しくインストールされていないことを示す一般的な問題です。
この問題をデバッグするには、次の手順を実行します(インポートが失敗する前)。

<!-- 1. Check the contents of the installed `pydantic-core` package. Are the compiled library and its type stubs both present? -->
1. インストールされている`pydantic-core`パッケージの内容を確認します。コンパイルされたライブラリとその型スタブの両方が存在しますか?

```py test="skip" lint="skip"
from importlib.metadata import files
print([file for file in files('pydantic-core') if file.name.startswith('_pydantic_core')])
"""
[PackagePath('pydantic_core/_pydantic_core.pyi'), PackagePath('pydantic_core/_pydantic_core.cpython-312-x86_64-linux-gnu.so')]
"""
```

<!-- You should expect to see two files like those printed above. The compile library file will be a .so or .pyd with a name that varies according to the OS and Python version. -->
上記のような2つのファイルが表示されるはずです。コンパイルライブラリファイルは.soまたは.pydで、名前はOSとPythonのバージョンによって異なります。

<!-- 2. Check that your lambda's Python version is compatible with the compiled library version found above. -->
2. lambdaのPythonバージョンが上記のコンパイルされたライブラリバージョンと互換性があることを確認します。

```py test="skip" lint="skip"
import sysconfig
print(sysconfig.get_config_var("EXT_SUFFIX"))
#> '.cpython-312-x86_64-linux-gnu.so'
```

<!-- You should expect to see the same suffix here as the compiled library, for example here we see this suffix `.cpython-312-x86_64-linux-gnu.so` indeed matches `_pydantic_core.cpython-312-x86_64-linux-gnu.so`. -->
コンパイルされたライブラリと同じサフィックスがここに表示されるはずです。例えば、ここでは`.cpython-312-x86_64-linux-gnu.so`というサフィックスが`_pydantic_core.cpython-312-x86_64-linux-gnu.so`と実際に一致しています。

<!-- If these two checks do not match, your build steps have not installed the correct native code for your lambda's target platform. You should adjust your build steps to change the version of the installed library which gets installed. -->
これら2つのチェックが一致しない場合は、ビルドステップでラムダのターゲットプラットフォーム用の正しいネイティブコードがインストールされていません。インストールされるインストール済みライブラリのバージョンを変更するために、ビルドステップを調整する必要があります。

Most likely errors:

<!-- * Your OS or CPU architecture is mismatched (e.g. darwin vs x86_64-linux-gnu). Try passing correct `--platform` argument to `pip install` when installing your lambda dependencies, or build inside a linux docker container for the correct platform. Possible platforms at the moment include `--platform manylinux2014_x86_64` or `--platform manylinux2014_aarch64`, but these may change with a future Pydantic major release. -->
* OSまたはCPUのアーキテクチャが一致していません(例:darwin vs x86_64-linux-gnu)。lambda依存関係をインストールするときに正しい`--platform`引数を`pip install`に渡すか、正しいプラットフォーム用のlinux dockerコンテナ内でビルドしてみてください。現在使用可能なプラットフォームには`--platform manylinux2014_x86_64`または`--platform manylinux2014_aarch64`がありますが、これらは将来のPydanticメジャーリリースで変更される可能性があります。

<!-- * Your Python version is mismatched (e.g. `cpython-310` vs `cpython-312`). Try passing correct `--python-version` argument to `pip install`, or otherwise change the Python version used on your build. -->
* あなたのPythonのバージョンが一致していません(例えば`cpython-310`と`cpython-312`)。`pip install`に正しい`--python-version`引数を渡すか、あなたのビルドで使用されているPythonのバージョンを変更してください。

### No package metadata was found for `email-validator`

<!-- Pydantic uses `version` from `importlib.metadata` to [check what version](https://github.com/pydantic/pydantic/pull/6033) of `email-validator` is installed.
This package versioning mechanism is somewhat incompatible with AWS Lambda, even though it's the industry standard for versioning packages in Python.
There are a few ways to fix this issue: -->
Pydanticは、`importlib.metadata`の`version`を使用して、`email-validator`がインストールされている[check what version](https://github.com/pydantic/pydantic/pull/6033)。
このパッケージのバージョン管理メカニズムは、Pythonでのパッケージのバージョン管理の業界標準であるにもかかわらず、AWS Lambdaとは多少互換性がありません。
この問題を解決するにはいくつかの方法があります。

<!-- If you're deploying your lambda with the serverless framework, it's likely that the appropriate metadata for the `email-validator` package is not being included in your deployment package.
Tools like [`serverless-python-requirements`](https://github.com/serverless/serverless-python-requirements/tree/master) remove metadata to reduce package size. You can fix this issue by setting the `slim` setting to false in your `serverless.yml` file: -->
サーバレスフレームワークでlambdaをデプロイしている場合、`email-validator`パッケージの適切なメタデータがデプロイパッケージに含まれていない可能性があります。
[`serverless-python-requirements`](https://github.com/serverless/serverless-python-requirements/tree/master)などのツールは、パッケージサイズを小さくするためにメタデータを削除します。この問題は、`serverless.yml`ファイルで`slim`設定をfalseに設定することで修正できます。

```
pythonRequirements:
    dockerizePip: non-linux
    slim: false
    fileName: requirements.txt
```

<!-- You can read more about this fix, and other `slim` settings that might be relevant [here](https://biercoff.com/how-to-fix-package-not-found-error-importlib-metadata/). -->
この修正、および関連する可能性のあるその他の"slim"設定の詳細については、[here](https://biercoff.com/how-to-fix-package-not-found-error-importlib-metadata/)を参照してください。

<!-- If you're using a `.zip` archive for your code and/or dependencies, make sure that your package contains the required version metadata. To do this, make sure you include the `dist-info` directory in your `.zip` archive for the `email-validator` package. -->
コードや依存関係に`.zip`アーカイブを使用している場合は、パッケージに必要なバージョンメタデータが含まれていることを確認してください。これを行うには、`.zip`アーカイブに`dist-info`ディレクトリを`email-validator`パッケージ用に含めてください。

<!-- This issue has been reported for other popular python libraries like [`jsonschema`](https://github.com/python-jsonschema/jsonschema/issues/584), so you can read more about the issue and potential fixes there as well. -->
この問題は、[`jsonschema`](https://github.com/python-jsonschema/jsonschema/issues/584)のような他の人気のあるpythonライブラリで報告されているので、この問題と潜在的な修正についてもそこで読むことができます。

## Extra Resources

### More Debugging Tips

<!-- If you're still struggling with installing `pydantic` for your AWS Lambda, you might consult with [this issue](https://github.com/pydantic/pydantic/issues/6557), which covers a variety of problems and solutions encountered by other developers. -->
AWS Lambdaに`pydantic`をインストールするのにまだ苦労している場合は、他の開発者が遭遇するさまざまな問題と解決策をカバーしている[this issue](https://github.com/pydantic/pydantic/issues/6557)を参照してください。


### Validating `event` and `context` data

<!-- Check out our [blog post](https://pydantic.dev/articles/lambda-intro) to learn more about how to use `pydantic` to validate `event` and `context` data in AWS Lambda functions. -->
AWS Lambda関数で`pydantic`を使用して`event`および`context`データを検証する方法について詳しくは、私たちの[blog post](https://pydantic.dev/articles/lambda-intro)を参照してください。
