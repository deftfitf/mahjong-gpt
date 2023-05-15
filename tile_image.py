import io
from dataclasses import dataclass
from typing import List, ByteString

from PIL.Image import Image, open as image_open, new as image_new

from mahjong import MahjongTile, MAHJONG_TILE_LIST, MahjongQuestion


@dataclass
class TileArea:
    tile: str
    x: int
    y: int
    w: int
    h: int


@dataclass
class TileImage:
    bytes: ByteString
    areas: List[TileArea]


class TileImageGenerator:
    image_cache: dict[MahjongTile, Image]

    _ROWS = 2
    _COLS = 7

    _RESIZE_WIDTH = 115
    _RESIZE_HEIGHT = 153

    _OUTPUT_WIDTH = 805
    _OUTPUT_HEIGHT = 306

    def __init__(self):
        self.image_cache = {}
        for tile in MAHJONG_TILE_LIST:
            image_path = f"img/{tile.get_image_name()}"
            image = image_open(image_path)
            image = image.resize((self._RESIZE_WIDTH, self._RESIZE_HEIGHT))
            self.image_cache[tile] = image

    def generate(
        self, mahjong_hands: List[MahjongTile], is_save=False
    ) -> TileImage:
        areas = []
        generated_image = image_new(
            'RGB', (self._OUTPUT_WIDTH, self._OUTPUT_HEIGHT)
        )

        for i in range(self._ROWS):
            for j in range(self._COLS):
                index = i * self._COLS + j
                tile = mahjong_hands[index]
                tile_image = self.image_cache.get(tile)

                paste_x = j * self._RESIZE_WIDTH
                paste_y = i * self._RESIZE_HEIGHT

                areas.append(TileArea(
                    tile.serialize(), paste_x, paste_y,
                    self._RESIZE_WIDTH, self._RESIZE_HEIGHT))
                generated_image.paste(tile_image, (paste_x, paste_y))

        byte_stream = io.BytesIO()
        generated_image.save(byte_stream, format='PNG')
        byte_stream.seek(0)
        gif_bytes = byte_stream.getvalue()

        if is_save:
            with open('output.png', 'wb') as f:
                f.write(gif_bytes)

        return TileImage(gif_bytes, areas)


if __name__ == "__main__":
    tiles = MahjongQuestion.parse_hand("1m2m2m3m4m5m6m7m1p1p1s2s3s5z")
    generator = TileImageGenerator()
    generator.generate(tiles, True)
