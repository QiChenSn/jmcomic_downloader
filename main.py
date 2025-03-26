from astrbot.api.message_components import *
from astrbot.api.message_components import File
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig
from astrbot.api.all import *
import httpx
import json
import asyncio
import os
import time
import random

import jmcomic

#自定义JMComic插件实现控制最大下载页数
#继承JmOptionPlugin
class SkipTooLongBook(jmcomic.JmOptionPlugin):
    plugin_key='skip_too_long_book'
    def invoke(self, 
               max_pages: int = 100,#可在option.yml中配置
               album:jmcomic.JmAlbumDetail = None,
               **kwargs) :
        if album is None:
            print('错误:Album is None')
            return
        pages=album.page_count
        if pages<=max_pages:
            return
        else:
            print('超过页数限制，已阻止下载')

# 导入此模块，需要先安装（pip install jmcomic -i https://pypi.org/project -U）
# 创建配置对象
# 注册插件的装饰器
@register("jmcomic_downloader", "QiChenSn", "一个下载JM的插件,添加了一些新功能，原项目名FateTrial_JMdownloader", "1.0.0")
class JMPlugin(Star):
    def __init__(self, context: Context,config: AstrBotConfig):
        super().__init__(context)
        #注册自定义插件
        jmcomic.JmModuleConfig.register_plugin(SkipTooLongBook)
        self.downloading = set() # 存储正在下载的ID
        #获取配置文件
        random_range_config = config.get('RandomRange', {})
        self.IDmin=random_range_config.get('IDmin')
        self.IDmax=random_range_config.get('IDmax')

        
    # 将同步下载任务包装成异步函数
    async def download_comic_async(self, album_id, option):
        if album_id in self.downloading:
            return False, "正在下载中，请稍后再试"
            
        self.downloading.add(album_id)
        try:
            # 将同步下载操作放到线程池中执行，避免阻塞事件循环
            await asyncio.to_thread(jmcomic.download_album, album_id, option)
            return True, None
        except Exception as e:
            return False, f"下载出错: {str(e)}"
        finally:
            self.downloading.discard(album_id)

    #下载事件
    async def JMDownload(self, event: AstrMessageEvent,tokens):
        path = os.path.abspath(os.path.dirname(__file__))
        pdf_path = f"{path}/pdf/{tokens}.pdf"
        # 检查文件是否已存在
        if os.path.exists(pdf_path):
            yield event.plain_result(f" {tokens}.pdf 已下载，直接发送")
            yield event.chain_result(
                [File(name=f"{tokens}.pdf", file=pdf_path)]
            )
            return
            
        # 创建配置并开始异步下载
        yield event.plain_result(f"开始下载 {tokens}，请稍候...")
        option = jmcomic.create_option_by_file(path + "/option.yml")
        success, error_msg = await self.download_comic_async(tokens, option)
        
        if not success:
            yield event.plain_result(error_msg)
            return
        # 检查文件是否下载成功
        if os.path.exists(pdf_path):
            yield event.plain_result(f" {tokens} 下载完成")
            yield event.chain_result(
                [File(name=f"{tokens}.pdf", file=pdf_path)]
            )
        else:
            yield event.plain_result(f"无法转为PDF或超出页数限制")


    #注册指令装饰器。用于随机下载
    @filter.command("jmr")
    async def JMRand(self, event: AstrMessageEvent):
        '''随机下载'''
        randToken = random.randint(self.IDmin, self.IDmax)
        async for result in self.JMDownload(event, randToken):
            yield result
            # 下载成功
            if isinstance(result, AstrMessageEvent) and "下载完成" in result.plain_result:
                return
        yield event.plain_result(f"运气不佳。随机下载失败")

    #根据ID下载
    @filter.command("jm")
    async def getJMid(self,event:AstrMessageEvent):
        '''由ID指定下载'''
        path = os.path.abspath(os.path.dirname(__file__))
        messages = event.get_messages()
        if not messages:
            yield event.plain_result("请输入要下载的ID,如果有多页，请输入第一页的ID")
            return
        # 获取原始消息文本
        message_text = messages[0].text  
        parts = message_text.split()  
        if len(parts) < 2:  
            yield event.plain_result("请输入要下载的ID,如果有多页，请输入第一页的ID")
            return
            
        tokens = parts[1]
        async for result in self.JMDownload(event, tokens):
            yield result

    @filter.command("jm_help")
    async def show_help(self, event: AstrMessageEvent):
        '''显示帮助信息'''
        help_text = """jmcomic_downloader指令说明：    
/jm ID - 下载JM漫画 如果有多页，请输入第一页的ID
/jmr -随机下载
/jm_help - 显示本帮助信息
"""
        yield event.plain_result(help_text)
