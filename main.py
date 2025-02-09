from astrbot.api.message_components import *
from astrbot.api.message_components import File
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api.all import *

import httpx
import json
import asyncio

import jmcomic
# 导入此模块，需要先安装（pip install jmcomic -i https://pypi.org/project -U）
# 创建配置对象
# 注册插件的装饰器
@register("JMdownloader", "FateTrial", "一个下载JM本子的插件,修复了不能下载仅登录查看的本子请自行配置cookies", "1.0.1")
class JMPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.cd = 10  # 默认冷却时间为 10 秒
        self.last_usage = {} # 存储每个用户上次使用指令的时间
# 注册指令的装饰器。指令名为 JM下载。注册成功后，发送 `/JM下载` 就会触发这个指令
    @filter.command("JM下载")
    async def JMid(self, event: AstrMessageEvent):
        path = os.path.abspath(os.path.dirname(__file__))
        messages = event.get_messages()
        if not messages:
            yield event.plain_result("请输入要下载的本子ID,如果有多页，请输入第一页的ID")
            return
        # 获取原始消息文本
        message_text = messages[0].text  
        # 直接获取 Plain 对象的 text 属性
        parts = message_text.split()  
        # 分割消息文本
        if len(parts) < 2:  
            # 检查是否有本子ID
            yield event.plain_result("请输入要下载的本子ID,如果有多页，请输入第一页的ID")
            return
        tokens = parts[1]  
        # 获取本子ID
        option = jmcomic.create_option_by_file(path + "/option.yml")
        # 使用option对象来下载本子
        jmcomic.download_album(tokens, option)
        # 等价写法: option.download_album(422866)
        yield event.plain_result("已启用下载线程")
        yield event.chain_result(
            [File(name=f"{tokens}.pdf", file=f"{path}/pdf/{tokens}.pdf")]
        )
    @filter.command("JM_help")
    async def show_help(self, event: AstrMessageEvent):
        '''显示帮助信息'''
        help_text = """JM下载插件指令说明：
        
/JM下载 本子ID - 下载JM漫画 如果有多页，请输入第一页的ID
/JM_help - 显示本帮助信息

powerd by FateTrial
"""
        yield event.plain_result(help_text)
