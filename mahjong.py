import re
from dataclasses import dataclass
from enum import Enum
from typing import Final, Optional, List

import openai

import logger
from appconfig import GPTConfig

logger = logger.get_logger()

PROMPT: Final = """
麻雀の現実に即した何切る問題を日本語で生成します。手牌はツモした直後の14枚で、数牌と字牌が使用されます。数牌は1m、1p、1sのように表記し、字牌は1z（東）や5z（白）のように表記します。

問題は以下のフォーマットで提供されます：
問題文: [問題文]
手牌: [手牌(スペース無し28文字)]
難易度: [1-5の整数]
解答: [解答(1枚)]
解説: [解説]
"""


class TileCategory(Enum):
    East = "1z"
    South = "2z"
    West = "3z"
    North = "4z"
    White = "5z"
    Green = "6z"
    Red = "7z"
    Man = "m"
    Pin = "p"
    Sou = "s"


STR_TO_TILE_CATEGORY = {}
for _category in TileCategory:
    STR_TO_TILE_CATEGORY[_category.value] = _category


@dataclass(frozen=True)
class MahjongTile:
    number: Optional[int]
    category: TileCategory

    @classmethod
    def parse_tile(cls, tile_str: str):
        # Parse role tile
        __category = STR_TO_TILE_CATEGORY.get(tile_str)
        if __category is not None:
            return MahjongTile(None, __category)

        # Parse number tile
        __category = STR_TO_TILE_CATEGORY.get(tile_str[1])
        if __category is not None:
            number = int(tile_str[0])
            return MahjongTile(number, __category)

        raise RuntimeError(f"Cannot parse mahjong tile string: {tile_str}")

    def serialize(self) -> str:
        if self.number is not None:
            return f"{self.number}{self.category.value}"
        return self.category.value

    def get_image_name(self) -> str:
        return f"p_{self.serialize()}_1.gif"

    def __hash__(self):
        return hash(self.serialize())


class _InvalidNumberMahjongHandException(RuntimeError):
    pass


MAHJONG_HAND_LENGTH = 14 * 2
MAHJONG_TILE_LIST = [
                        MahjongTile(i, su) for i in range(1, 10)
                        for su in
                        [TileCategory.Man, TileCategory.Pin, TileCategory.Sou]
                    ] + [
                        MahjongTile(None, ji) for ji in
                        [TileCategory.East, TileCategory.South,
                         TileCategory.West, TileCategory.North,
                         TileCategory.White, TileCategory.Green,
                         TileCategory.Red]
                    ]


@dataclass(frozen=True)
class MahjongQuestion:
    id: Optional[int]
    question: str
    hand: List[MahjongTile]
    difficulty: int
    answer: MahjongTile
    explanation: str

    @classmethod
    def parse_hand(cls, hand_str: str) -> List[MahjongTile]:
        if len(hand_str) != 28:
            raise _InvalidNumberMahjongHandException(
                f"The number of Mahjong hand is unexpected size: "
                f"expected={MAHJONG_HAND_LENGTH}, actual={len(hand_str)}")
        return [MahjongTile.parse_tile(hand_str[i:i + 2]) for i in
                range(0, MAHJONG_HAND_LENGTH, 2)]

    def serialize_hand(self) -> str:
        return "".join([tile.serialize() for tile in self.hand])

    def serialize(self) -> (str, str, str, str, int):
        return (
            self.question, self.serialize_hand(),
            self.answer.serialize(), self.explanation, self.difficulty,
        )

    @classmethod
    def deserialize(cls, data: (int, str, str, str, str, int)):
        (_id, question, hand, answer, explanation, difficulty) = data
        return MahjongQuestion(
            _id, question, MahjongQuestion.parse_hand(hand),
            difficulty, MahjongTile.parse_tile(answer), explanation
        )


class MahjongService:
    gpt_config: GPTConfig

    def __init__(self, gpt_config: GPTConfig):
        self.gpt_config = gpt_config

    def generate_question(self, context=None, retry_count=0) -> MahjongQuestion:
        if retry_count >= 3:
            message = f"Failed to generate_question because retry_count is " \
                      f"over upper limit. context={context} "
            logger.error(message)
            raise RuntimeError(message)

        if context is None:
            context: List = [{"role": "system", "content": PROMPT}]

        logger.info(f"GPT Request with prompt: {context}")
        response = openai.ChatCompletion.create(
            model=self.gpt_config.model,
            messages=context,
            temperature=self.gpt_config.temperature,
            max_tokens=self.gpt_config.max_tokens,
            n=self.gpt_config.n,
            stop=None
        )
        logger.info(f"GPT Response: {response}")
        gpt_output_text = response.choices[0].message.content.strip()

        try:
            mahjong_question = self.__parse_generated_result(gpt_output_text)
        except _InvalidNumberMahjongHandException as e:
            logger.info(
                "A mahjong question was tried to be created, "
                "but it had invalid hand that is unexpected length. "
                f"output={gpt_output_text}, retry_count={retry_count}", e)
            context.append({"role": "assistant", "content": gpt_output_text})
            context.append({
                "role": "user",
                "content": "出力が事前に与えられたフォーマットに沿っていません。"
                           "手牌の枚数が14枚ではないため、正しい手牌を生成し直してください。"
            })

            return self.generate_question(context, retry_count + 1)

        return mahjong_question

    @classmethod
    def __parse_generated_result(cls, gpt_output_text: str) -> MahjongQuestion:
        question_match = re.search(r"問題文: (.+)", gpt_output_text)
        hand_match = re.search(r"手牌: (.+)", gpt_output_text)
        difficulty_match = re.search(r"難易度: (.+)", gpt_output_text)
        answer_match = re.search(r"解答: (.+)", gpt_output_text)
        explanation_match = re.search(r"解説: (.+)", gpt_output_text)

        question = question_match.group(1)

        hand = hand_match.group(1)
        hands = MahjongQuestion.parse_hand(hand)

        difficulty = int(difficulty_match.group(1))
        answer = MahjongTile.parse_tile(answer_match.group(1))
        explanation = explanation_match.group(1)

        return MahjongQuestion(
            id=None, question=question, hand=hands, difficulty=difficulty,
            answer=answer, explanation=explanation
        )
