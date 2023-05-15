from urllib.parse import parse_qs

import openai
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    TextSendMessage, PostbackEvent,
)

import logger
from appconfig import appconfig
from mahjong import MahjongService, MahjongTile
from richmenu import RichMenuManager
from storage import Storage
from tile_image import TileImageGenerator

openai.api_key = appconfig.gpt.token

app = Flask(__name__)
logger = logger.get_logger()

line_bot_api = LineBotApi(appconfig.line_bot.channel_access_token)
handler = WebhookHandler(appconfig.line_bot.channel_secret)
rich_menu_manager = RichMenuManager(line_bot_api, appconfig.line_bot)
mahjong_service = MahjongService(appconfig.gpt)
tile_image_generator = TileImageGenerator()
storage = Storage(appconfig)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(PostbackEvent)
def handle_postback(event: PostbackEvent):
    user_id = event.source.user_id
    postback_data = {k: v[0] for k, v in parse_qs(event.postback.data).items()}
    logger.info(
        f"Received postback: user_id={user_id}, postback={postback_data}")

    action = postback_data['action']
    if action == 'start_question':
        question = mahjong_service.generate_question()
        question_id = storage.insert_question(question)
        tile_image = tile_image_generator.generate(question.hand)
        rich_menu_manager.set_mahjong_tile(user_id, question_id, tile_image)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"{question.question}\n難易度: {question.difficulty}"))
        return
    elif action == 'answer_tile':
        question_id = postback_data['id']
        mahjong_tile = MahjongTile.parse_tile(postback_data['tile'])
        question = storage.find_question(question_id)

        if question.answer == mahjong_tile:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"正解です！\n解説: {question.explanation}"))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"不正解です！\n解説: {question.explanation}"))

        rich_menu_manager.delete_rich_menu_of_user(user_id)
        return


if __name__ == "__main__":
    app.run()
