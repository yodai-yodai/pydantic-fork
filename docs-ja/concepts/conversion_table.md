{% include-markdown "../warning.md" %}

<!-- The following table provides details on how Pydantic converts data during validation in both strict and lax modes. -->
次の表は、strictモードとlaxモードの両方で、Pydanticが検証中にデータを変換する方法の詳細を示しています。

<!-- The "Strict" column contains checkmarks for type conversions that are allowed when validating in [Strict Mode](strict_mode.md). -->
"Strict"列には、[Strict Mode](strict_mode.md)での検証時に許可される型変換のチェックマークが含まれます。

=== "All"
{{ conversion_table_all }}

=== "JSON"
{{ conversion_table_json }}

=== "JSON - Strict"
{{ conversion_table_json_strict }}

=== "Python"
{{ conversion_table_python }}

=== "Python - Strict"
{{ conversion_table_python_strict }}
