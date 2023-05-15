from linebot import LineBotApi
from linebot.models import RichMenu, RichMenuSize, RichMenuArea, RichMenuBounds, \
    PostbackAction

import logger
from appconfig import AppConfig, LineBotConfig
from tile_image import TileImage

logger = logger.get_logger()


class RichMenuManager:
    api_client: LineBotApi
    setting: LineBotConfig

    def __init__(self, api_client: LineBotApi, setting: LineBotConfig):
        self.api_client = api_client
        self.setting = setting

    def create_default_rich_menu(self) -> str:
        rich_menu_to_create = RichMenu(
            size=RichMenuSize(width=805, height=306),
            selected=True,
            name="Default Rich Menu",
            chat_bar_text="メニュー",
            areas=[RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=805, height=306),
                action=PostbackAction(data="action=start_question"))]
        )
        _rich_menu_id = self.api_client.create_rich_menu(rich_menu_to_create)

        with open(self.setting.default_rich_menu_img_path, 'rb') as default_img:
            self.api_client.set_rich_menu_image(
                _rich_menu_id, "image/png",
                default_img.read()
            )

        self.api_client.set_default_rich_menu(_rich_menu_id)
        return _rich_menu_id

    def set_mahjong_tile(
        self, user_id: str, question_id: int, tile_image: TileImage
    ) -> str:
        rich_menu_areas = [RichMenuArea(
            bounds=RichMenuBounds(
                x=area.x, y=area.y, width=area.w, height=area.h),
            action=PostbackAction(
                data=f"action=answer_tile&tile={area.tile}&id={question_id}"))
            for area in tile_image.areas]
        rich_menu_to_create = RichMenu(
            size=RichMenuSize(width=805, height=306),
            selected=True,
            name="Mahjong Tile",
            chat_bar_text="メニュー",
            areas=rich_menu_areas
        )
        _rich_menu_id = self.api_client.create_rich_menu(rich_menu_to_create)
        self.api_client.set_rich_menu_image(
            _rich_menu_id, "image/png", tile_image.bytes)
        self.api_client.link_rich_menu_to_user(user_id, _rich_menu_id)

        return _rich_menu_id

    def delete_rich_menu_of_user(self, user_id: str):
        _rich_menu_id = self.api_client.get_rich_menu_id_of_user(user_id)
        self.api_client.unlink_rich_menu_from_user(user_id)
        self.api_client.delete_rich_menu(_rich_menu_id)


if __name__ == "__main__":
    appconfig = AppConfig.load("config/local.yaml")
    line_bot_api = LineBotApi(appconfig.line_bot.channel_access_token)
    rich_menu_manager = RichMenuManager(line_bot_api, appconfig.line_bot)

    rich_menu_id = rich_menu_manager.create_default_rich_menu()
    print(f"Created richMenuId: {rich_menu_id}")
