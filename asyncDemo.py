#！/usr/bin/python
#此句用于指定脚本执行的py版本
# -*- coding: utf-8 -*-
#此句用于让python脚本能够识别一些字符，如汉字
import sys
import json
import base64
import asyncio
import aiohttp
from _asyncio import Task

# 保证兼容python2以及python3
IS_PY3 = sys.version_info.major == 3
if IS_PY3:
    from urllib.request import urlopen
    from urllib.request import Request
    from urllib.error import URLError
    from urllib.parse import urlencode
    from urllib.parse import quote_plus
else:
    import urllib2
    from urllib import quote_plus
    from urllib2 import urlopen
    from urllib2 import Request
    from urllib2 import URLError
    from urllib import urlencode

# 防止https证书校验不正确
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


# 配置成你自己的APIKEY和SECRETKEY
API_KEY = '50BYrfyWPsoFvGnpvRrz50yg'

SECRET_KEY = 'rwZ8nMTeoHdAvuPDtQ9GjGXboEhx5j4L'

OCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/business_card"   # 名片识别接口的前缀

"""  TOKEN start """
TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'

"------------------------------------百度识别官方SDK------------------------------------------------"
"""
    获取token
"""
def fetch_token():
    params = {'grant_type': 'client_credentials',
              'client_id': API_KEY,
              'client_secret': SECRET_KEY}
    post_data = urlencode(params)
    if (IS_PY3):
        post_data = post_data.encode('utf-8')
    req = Request(TOKEN_URL, post_data)
    try:
        f = urlopen(req, timeout=5)
        result_str = f.read()
    except URLError as err:
        print(err)
    if (IS_PY3):
        result_str = result_str.decode()


    result = json.loads(result_str)

    if ('access_token' in result.keys() and 'scope' in result.keys()):
        if not 'brain_all_scope' in result['scope'].split(' '):
            print ('please ensure has check the  ability')
            exit()
        return result['access_token']
    else:
        print ('please overwrite the correct API_KEY and SECRET_KEY')
        exit()

"""
    读取文件
"""
def read_file(image_path):
    f = None
    try:
        f = open(image_path, 'rb')
        print("f",f)
        return f.read()
    except:
        print('read image file fail')
        return None
    finally:
        if f:
            f.close()


"""
    调用远程服务
"""
def request(url, data):
    req = Request(url, data.encode('utf-8'))
    has_error = False
    try:
        f = urlopen(req)
        result_str = f.read()
        if (IS_PY3):
            result_str = result_str.decode()
        return result_str
    except  URLError as err:
        print(err)
"------------------------------------百度识别官方SDK------------------------------------------------"


"------------------------------------有序结果的异步请求------------------------------------------------"
class BaiduOCR(object):
    """
    基于百度识别
    示例Demo
    """

    def __init__(self, sem):
        self.__taskList = []  # 存放loop管理的task
        self.__sem = sem  # 并发数量上限

    def ocr_res(self, req_data, url):
        """
        返回所有请求的识别结果
        :param req_data:
        :param url:
        :return:
        """
        self.mark_res_async(req_data, url)
        result = [json.loads(t.result()) for t in self.__taskList]
        print("result", result)

    def mark_res_async(self, req_data, url):
        """
        配置loop管理所有请求
        :param req_data:
        :param url:
        :return:
        """
        asyncio.set_event_loop(asyncio.new_event_loop())  # 支持多线程的async
        sem = asyncio.Semaphore(self.__sem)  # 控制并发数量
        for d in req_data:
            # 每个task就是一个请求
            # 将asyncio.Task对象实例的引用暂存起来
            self.__taskList.append(asyncio.ensure_future(self.req_baidu_api(d, sem, url)))
        loop = asyncio.get_event_loop()
        # print("__taskList bef", self.__taskList)
        tasks = set(self.__taskList)
        loop.run_until_complete(asyncio.wait(tasks))  # 等待所有请求完成
        # print("__taskList aft", self.__taskList)
        loop.close()

    async def req_baidu_api(self, data, sem, url):
        headers = {}  # 请求头
        res = None
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with sem:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url=url, data=data, headers=headers) as resp:
                        res = await resp.text()
                        return res
        except Exception as e:
            return res



async def req_baidu_api(param, sem, url):
    # url = "https://aip.baidubce.com/rest/2.0/ocr/v1/business_card"
    headers = {}
    # param = json.dumps()
    res = None
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with sem:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url=url, data=param,headers=headers) as resp:
                    res = await resp.text()
                    return res
    except Exception as e:
        return res
if __name__ == '__main__':

    # 获取access token
    token = fetch_token()

    # 拼接通用文字识别高精度url
    url = OCR_URL + "?access_token=" + token
    print(url)
    text = ""

    # 读取书籍页面图片
    file_content1 = read_file('./card_1.jpg')
    file_content2 = read_file('./card_2.jpg')
    file_content3 = read_file('./card_3.jpg')
    file_content4 = read_file('./card_4.jpg')
    # file_content5 = read_file('./card_5.jpg')
    # print(base64.b64encode(file_content))

    # 调用文字识别服务
    # result = request(image_url, urlencode({'image': base64.b64encode(file_content1)}))

    params = [{'image': base64.b64encode(file_content1)},
             {'image': base64.b64encode(file_content2)},
             {'image': base64.b64encode(file_content3)},
             {'image': base64.b64encode(file_content4)}]


    baiduOCR = BaiduOCR(2)
    baiduOCR.ocr_res(params, url)
