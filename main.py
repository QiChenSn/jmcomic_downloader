from astrbot.api.message_components import *
from astrbot.api.message_components import File
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api.all import *

import httpx
import json
import asyncio
import os
import time

import jmcomic
# 导入此模块，需要先安装（pip install jmcomic -i https://pypi.org/project -U）
# 创建配置对象
# 注册插件的装饰器
@register("JMdownloader", "FateTrial", "一个下载JM本子的插件,修复了不能下载仅登录查看的本子请自行配置cookies", "1.0.1")
class JMPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.downloading = set() # 存储正在下载的ID
        
    # 将同步下载任务包装成异步函数
    async def download_comic_async(self, album_id, option):
        if album_id in self.downloading:
            return False, "该本子正在下载中，请稍后再试"
            
        self.downloading.add(album_id)
        try:
            # 将同步下载操作放到线程池中执行，避免阻塞事件循环
            await asyncio.to_thread(jmcomic.download_album, album_id, option)
            return True, None
        except Exception as e:
            return False, f"下载出错: {str(e)}"
        finally:
            self.downloading.discard(album_id)

    # 注册指令的装饰器。指令名为 JM下载。注册成功后，发送 `/JM下载` 就会触发这个指令
    @filter.command("jm下载")
    async def JMid(self, event: AstrMessageEvent):
        path = os.path.abspath(os.path.dirname(__file__))
        messages = event.get_messages()
        if not messages:
            yield event.plain_result("请输入要下载的本子ID,如果有多页，请输入第一页的ID")
            return
        # 获取原始消息文本
        message_text = messages[0].text  
        parts = message_text.split()  
        if len(parts) < 2:  
            yield event.plain_result("请输入要下载的本子ID,如果有多页，请输入第一页的ID")
            return
            
        tokens = parts[1]  
        pdf_path = f"{path}/pdf/{tokens}.pdf"
        
        # 检查文件是否已存在
        if os.path.exists(pdf_path):
            yield event.plain_result(f"本子 {tokens} 已存在，直接发送")
            yield event.chain_result(
                [File(name=f"{tokens}.pdf", file=pdf_path)]
            )
            return
            
        # 创建配置并开始异步下载
        yield event.plain_result(f"开始下载本子 {tokens}，请稍候...")
        option = jmcomic.create_option_by_file(path + "/option.yml")
        
        success, error_msg = await self.download_comic_async(tokens, option)
        
        if not success:
            yield event.plain_result(error_msg)
            return
            
        # 检查文件是否下载成功
        if os.path.exists(pdf_path):
            yield event.plain_result(f"本子 {tokens} 下载完成")
            yield event.chain_result(
                [File(name=f"{tokens}.pdf", file=pdf_path)]
            )
        else:
            yield event.plain_result(f"下载完成，但未找到生成的PDF文件，请检查下载路径")

    @filter.command("jm_help")
    async def show_help(self, event: AstrMessageEvent):
        '''显示帮助信息'''
        help_text = """JM下载插件指令说明：
        
/jm下载 本子ID - 下载JM漫画 如果有多页，请输入第一页的ID
/jm_help - 显示本帮助信息

powerd by FateTrial
"""
        yield event.plain_result(help_text)
