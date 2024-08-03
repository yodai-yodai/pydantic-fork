"""Alias generators for converting between different capitalization conventions."""

import re

__all__ = ("to_pascal", "to_camel", "to_snake")

# TODO: in V3, change the argument names to be more descriptive
# Generally, don't only convert from snake_case, or name the functions
# more specifically like snake_to_camel.


def to_pascal(snake: str) -> str:
    """snake_case文字列をPascalCaseに変換します。

    Args:
        snake: 変換する文字列。

    Returns:
        PascalCase文字列。
    """
    camel = snake.title()
    return re.sub("([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), camel)


def to_camel(snake: str) -> str:
    """snake_case文字列をcamelCaseに変換します。

    Args:
        snake: 変換する文字列。

    Returns:
        変換されたcamelCase文字列。
    """
    # If the string is already in camelCase and does not contain a digit followed
    # by a lowercase letter, return it as it is
    if re.match("^[a-z]+[A-Za-z0-9]*$", snake) and not re.search(r"\d[a-z]", snake):
        return snake

    camel = to_pascal(snake)
    return re.sub("(^_*[A-Z])", lambda m: m.group(1).lower(), camel)


def to_snake(camel: str) -> str:
    """PascalCase、camelCase、またはkebab-case文字列をsnake_caseに変換します。

    Args:
        camel: 変換する文字列。

    Returns:
        snake_caseで変換された文字列。
    """
    # Handle the sequence of uppercase letters followed by a lowercase letter
    snake = re.sub(
        r"([A-Z]+)([A-Z][a-z])", lambda m: f"{m.group(1)}_{m.group(2)}", camel
    )
    # Insert an underscore between a lowercase letter and an uppercase letter
    snake = re.sub(r"([a-z])([A-Z])", lambda m: f"{m.group(1)}_{m.group(2)}", snake)
    # Insert an underscore between a digit and an uppercase letter
    snake = re.sub(r"([0-9])([A-Z])", lambda m: f"{m.group(1)}_{m.group(2)}", snake)
    # Insert an underscore between a lowercase letter and a digit
    snake = re.sub(r"([a-z])([0-9])", lambda m: f"{m.group(1)}_{m.group(2)}", snake)
    # Replace hyphens with underscores to handle kebab-case
    snake = snake.replace("-", "_")
    return snake.lower()
