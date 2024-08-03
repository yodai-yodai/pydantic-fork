"""カラー定義はCSS3に従って使用されます
[CSS Color Module Level 3](http://www.w3.org/TR/css3-color/#svg-color)仕様

いくつかの色は、同じ色を参照する複数の名前を持っています。例えば、`grey`と`gray`、または`aqua`と`cyan`です。

例えば`Color((0, 255, 255)).as_named()=='cyan'`のようにアルファベット順にソートすると、"cyan"は"aqua"の後に来るので、_last_colorが優先されます。

Warning: Deprecated
    `Color`クラスは廃止されました。代わりに`pydantic_extra_types`を使用してください。
    詳細については、[`pydantic-extra-types.Color`](../usage/types/extra_types/color_types.md)を参照してください。
"""

import math
import re
from colorsys import hls_to_rgb, rgb_to_hls
from typing import Any, Callable, Optional, Tuple, Type, Union, cast

from pydantic_core import CoreSchema, PydanticCustomError, core_schema
from typing_extensions import deprecated

from ._internal import _repr
from ._internal._schema_generation_shared import (
    GetJsonSchemaHandler as _GetJsonSchemaHandler,
)
from .json_schema import JsonSchemaValue
from .warnings import PydanticDeprecatedSince20

ColorTuple = Union[Tuple[int, int, int], Tuple[int, int, int, float]]
ColorType = Union[ColorTuple, str]
HslColorTuple = Union[Tuple[float, float, float], Tuple[float, float, float, float]]


class RGBA:
    """色の表現としてのみ内部的に使用されます。"""

    __slots__ = 'r', 'g', 'b', 'alpha', '_tuple'

    def __init__(self, r: float, g: float, b: float, alpha: Optional[float]):
        self.r = r
        self.g = g
        self.b = b
        self.alpha = alpha

        self._tuple: Tuple[float, float, float, Optional[float]] = (r, g, b, alpha)

    def __getitem__(self, item: Any) -> Any:
        return self._tuple[item]


# these are not compiled here to avoid import slowdown, they'll be compiled the first time they're used, then cached
_r_255 = r'(\d{1,3}(?:\.\d+)?)'
_r_comma = r'\s*,\s*'
_r_alpha = r'(\d(?:\.\d+)?|\.\d+|\d{1,2}%)'
_r_h = r'(-?\d+(?:\.\d+)?|-?\.\d+)(deg|rad|turn)?'
_r_sl = r'(\d{1,3}(?:\.\d+)?)%'
r_hex_short = r'\s*(?:#|0x)?([0-9a-f])([0-9a-f])([0-9a-f])([0-9a-f])?\s*'
r_hex_long = r'\s*(?:#|0x)?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})?\s*'
# CSS3 RGB examples: rgb(0, 0, 0), rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 50%)
r_rgb = rf'\s*rgba?\(\s*{_r_255}{_r_comma}{_r_255}{_r_comma}{_r_255}(?:{_r_comma}{_r_alpha})?\s*\)\s*'
# CSS3 HSL examples: hsl(270, 60%, 50%), hsla(270, 60%, 50%, 0.5), hsla(270, 60%, 50%, 50%)
r_hsl = rf'\s*hsla?\(\s*{_r_h}{_r_comma}{_r_sl}{_r_comma}{_r_sl}(?:{_r_comma}{_r_alpha})?\s*\)\s*'
# CSS4 RGB examples: rgb(0 0 0), rgb(0 0 0 / 0.5), rgb(0 0 0 / 50%), rgba(0 0 0 / 50%)
r_rgb_v4_style = rf'\s*rgba?\(\s*{_r_255}\s+{_r_255}\s+{_r_255}(?:\s*/\s*{_r_alpha})?\s*\)\s*'
# CSS4 HSL examples: hsl(270 60% 50%), hsl(270 60% 50% / 0.5), hsl(270 60% 50% / 50%), hsla(270 60% 50% / 50%)
r_hsl_v4_style = rf'\s*hsla?\(\s*{_r_h}\s+{_r_sl}\s+{_r_sl}(?:\s*/\s*{_r_alpha})?\s*\)\s*'

# colors where the two hex characters are the same, if all colors match this the short version of hex colors can be used
repeat_colors = {int(c * 2, 16) for c in '0123456789abcdef'}
rads = 2 * math.pi


@deprecated(
    'The `Color` class is deprecated, use `pydantic_extra_types` instead. '
    'See https://docs.pydantic.dev/latest/api/pydantic_extra_types_color/.',
    category=PydanticDeprecatedSince20,
)
class Color(_repr.Representation):
    """Represents a color."""

    __slots__ = '_original', '_rgba'

    def __init__(self, value: ColorType) -> None:
        self._rgba: RGBA
        self._original: ColorType
        if isinstance(value, (tuple, list)):
            self._rgba = parse_tuple(value)
        elif isinstance(value, str):
            self._rgba = parse_str(value)
        elif isinstance(value, Color):
            self._rgba = value._rgba
            value = value._original
        else:
            raise PydanticCustomError(
                'color_error',
                'value is not a valid color: value must be a tuple, list or string',
            )

        # if we've got here value must be a valid color
        self._original = value

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: _GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = {}
        field_schema.update(type='string', format='color')
        return field_schema

    def original(self) -> ColorType:
        """Original value passed to `Color`."""
        return self._original

    def as_named(self, *, fallback: bool = False) -> str:
        """Returns the name of the color if it can be found in `COLORS_BY_VALUE` dictionary,
        otherwise returns the hexadecimal representation of the color or raises `ValueError`.

        Args:
            fallback: If True, falls back to returning the hexadecimal representation of
                the color instead of raising a ValueError when no named color is found.

        Returns:
            The name of the color, or the hexadecimal representation of the color.

        Raises:
            ValueError: When no named color is found and fallback is `False`.
        """
        if self._rgba.alpha is None:
            rgb = cast(Tuple[int, int, int], self.as_rgb_tuple())
            try:
                return COLORS_BY_VALUE[rgb]
            except KeyError as e:
                if fallback:
                    return self.as_hex()
                else:
                    raise ValueError('no named color found, use fallback=True, as_hex() or as_rgb()') from e
        else:
            return self.as_hex()

    def as_hex(self) -> str:
        """Returns the hexadecimal representation of the color.

        Hex string representing the color can be 3, 4, 6, or 8 characters depending on whether the string
        a "short" representation of the color is possible and whether there's an alpha channel.

        Returns:
            The hexadecimal representation of the color.
        """
        values = [float_to_255(c) for c in self._rgba[:3]]
        if self._rgba.alpha is not None:
            values.append(float_to_255(self._rgba.alpha))

        as_hex = ''.join(f'{v:02x}' for v in values)
        if all(c in repeat_colors for c in values):
            as_hex = ''.join(as_hex[c] for c in range(0, len(as_hex), 2))
        return '#' + as_hex

    def as_rgb(self) -> str:
        """Color as an `rgb(<r>, <g>, <b>)` or `rgba(<r>, <g>, <b>, <a>)` string."""
        if self._rgba.alpha is None:
            return f'rgb({float_to_255(self._rgba.r)}, {float_to_255(self._rgba.g)}, {float_to_255(self._rgba.b)})'
        else:
            return (
                f'rgba({float_to_255(self._rgba.r)}, {float_to_255(self._rgba.g)}, {float_to_255(self._rgba.b)}, '
                f'{round(self._alpha_float(), 2)})'
            )

    def as_rgb_tuple(self, *, alpha: Optional[bool] = None) -> ColorTuple:
        """Returns the color as an RGB or RGBA tuple.

        Args:
            alpha: Whether to include the alpha channel. There are three options for this input:

                - `None` (default): Include alpha only if it's set. (e.g. not `None`)
                - `True`: Always include alpha.
                - `False`: Always omit alpha.

        Returns:
            A tuple that contains the values of the red, green, and blue channels in the range 0 to 255.
                If alpha is included, it is in the range 0 to 1.
        """
        r, g, b = (float_to_255(c) for c in self._rgba[:3])
        if alpha is None:
            if self._rgba.alpha is None:
                return r, g, b
            else:
                return r, g, b, self._alpha_float()
        elif alpha:
            return r, g, b, self._alpha_float()
        else:
            # alpha is False
            return r, g, b

    def as_hsl(self) -> str:
        """Color as an `hsl(<h>, <s>, <l>)` or `hsl(<h>, <s>, <l>, <a>)` string."""
        if self._rgba.alpha is None:
            h, s, li = self.as_hsl_tuple(alpha=False)  # type: ignore
            return f'hsl({h * 360:0.0f}, {s:0.0%}, {li:0.0%})'
        else:
            h, s, li, a = self.as_hsl_tuple(alpha=True)  # type: ignore
            return f'hsl({h * 360:0.0f}, {s:0.0%}, {li:0.0%}, {round(a, 2)})'

    def as_hsl_tuple(self, *, alpha: Optional[bool] = None) -> HslColorTuple:
        """Returns the color as an HSL or HSLA tuple.

        Args:
            alpha: Whether to include the alpha channel.

                - `None` (default): Include the alpha channel only if it's set (e.g. not `None`).
                - `True`: Always include alpha.
                - `False`: Always omit alpha.

        Returns:
            The color as a tuple of hue, saturation, lightness, and alpha (if included).
                All elements are in the range 0 to 1.

        Note:
            This is HSL as used in HTML and most other places, not HLS as used in Python's `colorsys`.
        """
        h, l, s = rgb_to_hls(self._rgba.r, self._rgba.g, self._rgba.b)  # noqa: E741
        if alpha is None:
            if self._rgba.alpha is None:
                return h, s, l
            else:
                return h, s, l, self._alpha_float()
        if alpha:
            return h, s, l, self._alpha_float()
        else:
            # alpha is False
            return h, s, l

    def _alpha_float(self) -> float:
        return 1 if self._rgba.alpha is None else self._rgba.alpha

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[Any], handler: Callable[[Any], CoreSchema]
    ) -> core_schema.CoreSchema:
        return core_schema.with_info_plain_validator_function(
            cls._validate, serialization=core_schema.to_string_ser_schema()
        )

    @classmethod
    def _validate(cls, __input_value: Any, _: Any) -> 'Color':
        return cls(__input_value)

    def __str__(self) -> str:
        return self.as_named(fallback=True)

    def __repr_args__(self) -> '_repr.ReprArgs':
        return [(None, self.as_named(fallback=True))] + [('rgb', self.as_rgb_tuple())]

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Color) and self.as_rgb_tuple() == other.as_rgb_tuple()

    def __hash__(self) -> int:
        return hash(self.as_rgb_tuple())


def parse_tuple(value: Tuple[Any, ...]) -> RGBA:
    """タプルまたはリストを解析してRGBA値を取得します。

    Args:
        value: タプルまたはリスト。

    Returns:
        入力タプルから解析された`RGBA`タプル。

    Raises:
        PydantictCustomError:タプルが無効な場合。
    """
    if len(value) == 3:
        r, g, b = (parse_color_value(v) for v in value)
        return RGBA(r, g, b, None)
    elif len(value) == 4:
        r, g, b = (parse_color_value(v) for v in value[:3])
        return RGBA(r, g, b, parse_float_alpha(value[3]))
    else:
        raise PydanticCustomError('color_error', 'value is not a valid color: tuples must have length 3 or 4')


def parse_str(value: str) -> RGBA:
    """色を表す文字列をRGBAタプルに解析します。

    入力文字列の形式は次のとおりです。

    * 名前付きの色、`COLORS_BY_NAME`を参照
    * hex short eg. `<prefix>fff`(prefixには`#`、`0x`または何も指定しない)
    * hex long例:`<prefix>ffffff`(prefixには`#`、`0x`または何も指定しない)
    * `rgb(<r>,<g>,<b>)`
    * `rgba(<r>,<g>,<b>,<a>)`

    Args:
        value: 色を表す文字列。

    Returns:
        入力文字列から解析された`RGBA`タプル。

    Raises:
        ValueError: 入力文字列をRGBAタプルに解析できない場合。
    """
    value_lower = value.lower()
    try:
        r, g, b = COLORS_BY_NAME[value_lower]
    except KeyError:
        pass
    else:
        return ints_to_rgba(r, g, b, None)

    m = re.fullmatch(r_hex_short, value_lower)
    if m:
        *rgb, a = m.groups()
        r, g, b = (int(v * 2, 16) for v in rgb)
        if a:
            alpha: Optional[float] = int(a * 2, 16) / 255
        else:
            alpha = None
        return ints_to_rgba(r, g, b, alpha)

    m = re.fullmatch(r_hex_long, value_lower)
    if m:
        *rgb, a = m.groups()
        r, g, b = (int(v, 16) for v in rgb)
        if a:
            alpha = int(a, 16) / 255
        else:
            alpha = None
        return ints_to_rgba(r, g, b, alpha)

    m = re.fullmatch(r_rgb, value_lower) or re.fullmatch(r_rgb_v4_style, value_lower)
    if m:
        return ints_to_rgba(*m.groups())  # type: ignore

    m = re.fullmatch(r_hsl, value_lower) or re.fullmatch(r_hsl_v4_style, value_lower)
    if m:
        return parse_hsl(*m.groups())  # type: ignore

    raise PydanticCustomError(
        'color_error',
        'value is not a valid color: string not recognised as a valid color',
    )


def ints_to_rgba(
    r: Union[int, str],
    g: Union[int, str],
    b: Union[int, str],
    alpha: Optional[float] = None,
) -> RGBA:
    """RGBカラーの整数値または文字列値とオプションのアルファ値を`RGBA`オブジェクトに変換します。

    Args:
        r: 赤のカラー値を表す整数または文字列。
        g: 緑のカラー値を表す整数または文字列。
        b: 青のカラー値を表す整数または文字列。
        alpha: アルファ値を表すfloat。デフォルトは"なし"です。

    Returns:
        対応するカラー値とアルファ値を持つ`RGBA`クラスのインスタンス。


    """
    return RGBA(
        parse_color_value(r),
        parse_color_value(g),
        parse_color_value(b),
        parse_float_alpha(alpha),
    )


def parse_color_value(value: Union[int, str], max_val: int = 255) -> float:
    """指定された色の値を解析し、0～1の数値を返します。

    Args:
        value: 整数または文字列のカラー値。
        max_val: 最大範囲値。デフォルトは255です。

    Raises:
        PydantictCustomError:値が有効な色でない場合。

    Returns:
        0～1の数値。
    """
    try:
        color = float(value)
    except ValueError:
        raise PydanticCustomError(
            'color_error',
            'value is not a valid color: color values must be a valid number',
        )
    if 0 <= color <= max_val:
        return color / max_val
    else:
        raise PydanticCustomError(
            'color_error',
            'value is not a valid color: color values must be in the range 0 to {max_val}',
            {'max_val': max_val},
        )


def parse_float_alpha(value: Union[None, str, float, int]) -> Optional[float]:
    """アルファ値を解析して、それが0から1の範囲の有効な浮動小数点であることを確認します。

    Args:
        value: 解析する入力値。

    Returns:
        浮動小数点として解析された値、または値がNoneまたは1の場合は`None`。

    Raises:
        PydantictCustomError: 入力値が期待される範囲内の浮動小数点として正常に解析できない場合。
    """
    if value is None:
        return None
    try:
        if isinstance(value, str) and value.endswith('%'):
            alpha = float(value[:-1]) / 100
        else:
            alpha = float(value)
    except ValueError:
        raise PydanticCustomError(
            'color_error',
            'value is not a valid color: alpha values must be a valid float',
        )

    if math.isclose(alpha, 1):
        return None
    elif 0 <= alpha <= 1:
        return alpha
    else:
        raise PydanticCustomError(
            'color_error',
            'value is not a valid color: alpha values must be in the range 0 to 1',
        )


def parse_hsl(h: str, h_units: str, sat: str, light: str, alpha: Optional[float] = None) -> RGBA:
    """生の色相、彩度、明度、およびアルファ値を解析し、RGBAに変換します。

    Args:
        h: 色相の値。
        h_units: 色相値の単位。
        sat: 彩度の値。
        light: 明度の値。
        alpha: アルファ値。

    Returns:
        `RGBA`のインスタンス。
    """
    s_value, l_value = parse_color_value(sat, 100), parse_color_value(light, 100)

    h_value = float(h)
    if h_units in {None, 'deg'}:
        h_value = h_value % 360 / 360
    elif h_units == 'rad':
        h_value = h_value % rads / rads
    else:
        # turns
        h_value = h_value % 1

    r, g, b = hls_to_rgb(h_value, l_value, s_value)
    return RGBA(r, g, b, parse_float_alpha(alpha))


def float_to_255(c: float) -> int:
    """0～1(両端を含む)の浮動小数点値を0～255(両端を含む)の整数に変換します。

    Args:
        c :変換されるfloat値。0以上1以下である必要があります。

    Returns:
        最も近い整数に丸められた、指定されたfloat値に相当する整数。

    Raises:
        ValueError: 指定されたfloat値が0～1(両端を含む)の許容範囲外である場合。
    """
    return int(round(c * 255))


COLORS_BY_NAME = {
    'aliceblue': (240, 248, 255),
    'antiquewhite': (250, 235, 215),
    'aqua': (0, 255, 255),
    'aquamarine': (127, 255, 212),
    'azure': (240, 255, 255),
    'beige': (245, 245, 220),
    'bisque': (255, 228, 196),
    'black': (0, 0, 0),
    'blanchedalmond': (255, 235, 205),
    'blue': (0, 0, 255),
    'blueviolet': (138, 43, 226),
    'brown': (165, 42, 42),
    'burlywood': (222, 184, 135),
    'cadetblue': (95, 158, 160),
    'chartreuse': (127, 255, 0),
    'chocolate': (210, 105, 30),
    'coral': (255, 127, 80),
    'cornflowerblue': (100, 149, 237),
    'cornsilk': (255, 248, 220),
    'crimson': (220, 20, 60),
    'cyan': (0, 255, 255),
    'darkblue': (0, 0, 139),
    'darkcyan': (0, 139, 139),
    'darkgoldenrod': (184, 134, 11),
    'darkgray': (169, 169, 169),
    'darkgreen': (0, 100, 0),
    'darkgrey': (169, 169, 169),
    'darkkhaki': (189, 183, 107),
    'darkmagenta': (139, 0, 139),
    'darkolivegreen': (85, 107, 47),
    'darkorange': (255, 140, 0),
    'darkorchid': (153, 50, 204),
    'darkred': (139, 0, 0),
    'darksalmon': (233, 150, 122),
    'darkseagreen': (143, 188, 143),
    'darkslateblue': (72, 61, 139),
    'darkslategray': (47, 79, 79),
    'darkslategrey': (47, 79, 79),
    'darkturquoise': (0, 206, 209),
    'darkviolet': (148, 0, 211),
    'deeppink': (255, 20, 147),
    'deepskyblue': (0, 191, 255),
    'dimgray': (105, 105, 105),
    'dimgrey': (105, 105, 105),
    'dodgerblue': (30, 144, 255),
    'firebrick': (178, 34, 34),
    'floralwhite': (255, 250, 240),
    'forestgreen': (34, 139, 34),
    'fuchsia': (255, 0, 255),
    'gainsboro': (220, 220, 220),
    'ghostwhite': (248, 248, 255),
    'gold': (255, 215, 0),
    'goldenrod': (218, 165, 32),
    'gray': (128, 128, 128),
    'green': (0, 128, 0),
    'greenyellow': (173, 255, 47),
    'grey': (128, 128, 128),
    'honeydew': (240, 255, 240),
    'hotpink': (255, 105, 180),
    'indianred': (205, 92, 92),
    'indigo': (75, 0, 130),
    'ivory': (255, 255, 240),
    'khaki': (240, 230, 140),
    'lavender': (230, 230, 250),
    'lavenderblush': (255, 240, 245),
    'lawngreen': (124, 252, 0),
    'lemonchiffon': (255, 250, 205),
    'lightblue': (173, 216, 230),
    'lightcoral': (240, 128, 128),
    'lightcyan': (224, 255, 255),
    'lightgoldenrodyellow': (250, 250, 210),
    'lightgray': (211, 211, 211),
    'lightgreen': (144, 238, 144),
    'lightgrey': (211, 211, 211),
    'lightpink': (255, 182, 193),
    'lightsalmon': (255, 160, 122),
    'lightseagreen': (32, 178, 170),
    'lightskyblue': (135, 206, 250),
    'lightslategray': (119, 136, 153),
    'lightslategrey': (119, 136, 153),
    'lightsteelblue': (176, 196, 222),
    'lightyellow': (255, 255, 224),
    'lime': (0, 255, 0),
    'limegreen': (50, 205, 50),
    'linen': (250, 240, 230),
    'magenta': (255, 0, 255),
    'maroon': (128, 0, 0),
    'mediumaquamarine': (102, 205, 170),
    'mediumblue': (0, 0, 205),
    'mediumorchid': (186, 85, 211),
    'mediumpurple': (147, 112, 219),
    'mediumseagreen': (60, 179, 113),
    'mediumslateblue': (123, 104, 238),
    'mediumspringgreen': (0, 250, 154),
    'mediumturquoise': (72, 209, 204),
    'mediumvioletred': (199, 21, 133),
    'midnightblue': (25, 25, 112),
    'mintcream': (245, 255, 250),
    'mistyrose': (255, 228, 225),
    'moccasin': (255, 228, 181),
    'navajowhite': (255, 222, 173),
    'navy': (0, 0, 128),
    'oldlace': (253, 245, 230),
    'olive': (128, 128, 0),
    'olivedrab': (107, 142, 35),
    'orange': (255, 165, 0),
    'orangered': (255, 69, 0),
    'orchid': (218, 112, 214),
    'palegoldenrod': (238, 232, 170),
    'palegreen': (152, 251, 152),
    'paleturquoise': (175, 238, 238),
    'palevioletred': (219, 112, 147),
    'papayawhip': (255, 239, 213),
    'peachpuff': (255, 218, 185),
    'peru': (205, 133, 63),
    'pink': (255, 192, 203),
    'plum': (221, 160, 221),
    'powderblue': (176, 224, 230),
    'purple': (128, 0, 128),
    'red': (255, 0, 0),
    'rosybrown': (188, 143, 143),
    'royalblue': (65, 105, 225),
    'saddlebrown': (139, 69, 19),
    'salmon': (250, 128, 114),
    'sandybrown': (244, 164, 96),
    'seagreen': (46, 139, 87),
    'seashell': (255, 245, 238),
    'sienna': (160, 82, 45),
    'silver': (192, 192, 192),
    'skyblue': (135, 206, 235),
    'slateblue': (106, 90, 205),
    'slategray': (112, 128, 144),
    'slategrey': (112, 128, 144),
    'snow': (255, 250, 250),
    'springgreen': (0, 255, 127),
    'steelblue': (70, 130, 180),
    'tan': (210, 180, 140),
    'teal': (0, 128, 128),
    'thistle': (216, 191, 216),
    'tomato': (255, 99, 71),
    'turquoise': (64, 224, 208),
    'violet': (238, 130, 238),
    'wheat': (245, 222, 179),
    'white': (255, 255, 255),
    'whitesmoke': (245, 245, 245),
    'yellow': (255, 255, 0),
    'yellowgreen': (154, 205, 50),
}

COLORS_BY_VALUE = {v: k for k, v in COLORS_BY_NAME.items()}
