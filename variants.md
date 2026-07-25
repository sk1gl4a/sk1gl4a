# Варианты набора символов

Все шесть на параметрах A (`scale 1.5`, `warp 3.6`, `bands 2.4`, `contrast 2.6`, `octaves 4`), seed от 25 июля, фон `#0d1117`.

## 1. classic

Текущий набор: `пробел . : - = + * # % @`

![classic](https://raw.githubusercontent.com/sk1gl4a/sk1gl4a/previews/variant_1-classic.svg)

## 2. blocks

`░ ▒ ▓ █`, плотная графика.

![blocks](https://raw.githubusercontent.com/sk1gl4a/sk1gl4a/previews/variant_2-blocks.svg)

## 3. sparse

Редкий набор, много воздуха.

![sparse](https://raw.githubusercontent.com/sk1gl4a/sk1gl4a/previews/variant_3-sparse.svg)

## 4. photo

Длинная рампа на 68 градаций.

![photo](https://raw.githubusercontent.com/sk1gl4a/sk1gl4a/previews/variant_4-photo.svg)

## 5. levels

`▁ ▂ ▃ ▄ ▅ ▆ ▇ █`, уровни снизу вверх.

![levels](https://raw.githubusercontent.com/sk1gl4a/sk1gl4a/previews/variant_5-levels.svg)

## 6. braille

Точки Брайля, каждый глиф это матрица 2×4, поэтому деталей вдвое больше.

![braille](https://raw.githubusercontent.com/sk1gl4a/sk1gl4a/previews/variant_6-braille.svg)

---

# Брайль с глубиной

Форма та же, но полутона вернулись.

## 7. braille + dither

Порядковый дизеринг по матрице Байера 4×4. Яркость передаётся плотностью точек, цвет один. Тёмные места сохраняют редкие точки, светлые заливаются целиком.

![braille dither](https://raw.githubusercontent.com/sk1gl4a/sk1gl4a/previews/variant_7-braille-dither.svg)

## 8. braille + shading

Точки ставятся по порогу, как в шестом варианте, но каждый глиф красится в один из 10 оттенков по средней яркости ячейки.

![braille shaded](https://raw.githubusercontent.com/sk1gl4a/sk1gl4a/previews/variant_8-braille-shaded.svg)

## 9. braille + dither + shading

И плотность точек, и цвет. Самая глубокая картинка из всех.

![braille both](https://raw.githubusercontent.com/sk1gl4a/sk1gl4a/previews/variant_9-braille-both.svg)
