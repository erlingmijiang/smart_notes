import json
import os
import re
import asyncio
from blbl_download import download_bilibili_audio
from xfasr_async import xf_asr
from llm_inference import llm_inference, select_prompt_file, clear_prompt_memory
from format_note import format_note

######################################################
# 参数配置
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        appid = config[0]["xunfei_asr"]["appid"]
        secret_key = config[0]["xunfei_asr"]["secret_key"]
        api_key = config[1]['llm']['api_key']
        base_url = config[1]['llm']['base_url']
        model_name = config[1]['llm']['model_name']
        output_path = config[2]['output_path']["obsidian_path"]
except Exception as e:
    print(f'程序运行异常，请检查 config.json 文件')
    exit()
######################################################

def clean_cache(
        clean_wav_cache = True,
        clean_asr_result = False,
    ):
    """
    删除缓存文件
    默认删除音频下载缓存
    不删除ASR语音识别结果
    """
    if clean_wav_cache == True:
        wav_cache_dir = "./wav_cache"
        for file in os.listdir(wav_cache_dir):
            os.remove(os.path.join(wav_cache_dir, file))
    if clean_asr_result == True:
        asr_result_dir = "./asr_result"
        for file in os.listdir(asr_result_dir):
            os.remove(os.path.join(asr_result_dir, file))

async def download_task(url, download_semaphore, transcribe_queue):
    """异步下载任务"""
    async with download_semaphore:
        try:
            if url[:2] == "BV":
                full_url = "https://www.bilibili.com/video/" + url
            else:
                full_url = url
            upload_file_name = await asyncio.to_thread(download_bilibili_audio, full_url)
            
            # 处理文件名中的非法字符，避免特殊字符导致的报错
            illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
            sanitized_name = re.sub(illegal_chars, '_', upload_file_name)
            # 确保文件名不为空
            if not sanitized_name:
                sanitized_name = "untitled"
            upload_file_name = sanitized_name
            
            # 将任务放入转写队列
            await transcribe_queue.put((upload_file_name, full_url))
            print(f"下载完成：{url} -> {upload_file_name}")
        except Exception as e:
            print(f"下载失败：{url}，错误信息：{e}")

async def transcribe_task(upload_file_name, full_url, transcribe_semaphore, summarize_queue):
    """异步转写任务"""
    async with transcribe_semaphore:
        try:
            # 【这是第二部分，调用讯飞ASR，把音频文件转写为文本】
            await xf_asr(
                upload_file_name = upload_file_name,
                appid = appid,
                secret_key = secret_key)
            
            # 将任务放入总结队列
            await summarize_queue.put((upload_file_name, full_url))
            print(f"转写完成：{upload_file_name}")
        except Exception as e:
            print(f"转写失败：{upload_file_name}，错误信息：{e}")

async def summarize_task(upload_file_name, full_url, summarize_semaphore):
    """异步总结任务"""
    async with summarize_semaphore:
        try:
            # 读取转写结果
            with open(f"./asr_result/{upload_file_name.split('.')[0]}.txt", "r", encoding="utf-8") as f:
                text = f.read()
            
            # 调用LLM生成笔记
            result = await asyncio.to_thread(llm_inference,
                api_key = api_key,
                base_url = base_url,
                model_name = model_name,
                text = text)
            
            # 格式化笔记
            result = format_note(result)
            
            # 保存结果
            try:
                with open(f"{output_path}/【智能笔记】{upload_file_name.split('.')[0]}.md", "w", encoding="utf-8") as f:
                    f.write(f"视频链接：[{upload_file_name}]({full_url})\n\n")
                    f.write(result)
            except:
                with open(f"./notebook_output/【智能笔记】{upload_file_name.split('.')[0]}.md", "w", encoding="utf-8") as f:
                    f.write(f"视频链接：[{upload_file_name}]({full_url})\n\n")
                    f.write(result)
            
            print(f"总结完成：{upload_file_name}")
        except Exception as e:
            print(f"总结失败：{upload_file_name}，错误信息：{e}")

async def download_worker(download_queue, download_semaphore, transcribe_queue):
    """下载任务处理器"""
    while True:
        url = await download_queue.get()
        if url is None:
            break
        await download_task(url, download_semaphore, transcribe_queue)
        download_queue.task_done()

async def transcribe_worker(transcribe_queue, transcribe_semaphore, summarize_queue):
    """转写任务处理器"""
    while True:
        upload_file_name, full_url = await transcribe_queue.get()
        if upload_file_name is None:
            break
        await transcribe_task(upload_file_name, full_url, transcribe_semaphore, summarize_queue)
        transcribe_queue.task_done()

async def summarize_worker(summarize_queue, summarize_semaphore):
    """总结任务处理器"""
    while True:
        upload_file_name, full_url = await summarize_queue.get()
        if upload_file_name is None:
            break
        await summarize_task(upload_file_name, full_url, summarize_semaphore)
        summarize_queue.task_done()



if __name__ == "__main__":

    # (初始化）检测并创建必要目录
    for folder in ["asr_result", "notebook_output", "wav_cache"]:
        if not os.path.exists(folder):
            os.makedirs(folder)


    task_list = []
    url = input("请输入B站视频链接（空行回车启动）：")
    while url != '':
        task_list.append(url)
        url = input("请输入B站视频链接（空行回车启动）：")
    
    # 让用户选择提示词模板
    select_prompt_file()
    
    async def main_async():
        # 创建三个队列
        download_queue = asyncio.Queue()
        transcribe_queue = asyncio.Queue()
        summarize_queue = asyncio.Queue()
        
        # 创建并发控制信号量，每个模块最多4个并发
        download_semaphore = asyncio.Semaphore(4)
        transcribe_semaphore = asyncio.Semaphore(4)
        summarize_semaphore = asyncio.Semaphore(4)
        
        # 启动工作线程
        workers = []
        # 启动2个下载 worker
        for _ in range(2):
            worker = asyncio.create_task(download_worker(download_queue, download_semaphore, transcribe_queue))
            workers.append(worker)
        # 启动2个转写 worker
        for _ in range(2):
            worker = asyncio.create_task(transcribe_worker(transcribe_queue, transcribe_semaphore, summarize_queue))
            workers.append(worker)
        # 启动2个总结 worker
        for _ in range(2):
            worker = asyncio.create_task(summarize_worker(summarize_queue, summarize_semaphore))
            workers.append(worker)
        
        # 将所有URL放入下载队列
        for url in task_list:
            await download_queue.put(url)
        
        # 等待所有下载任务完成
        await download_queue.join()
        print("所有下载任务已完成")
        
        # 等待所有转写任务完成
        await transcribe_queue.join()
        print("所有转写任务已完成")
        
        # 等待所有总结任务完成
        await summarize_queue.join()
        print("所有总结任务已完成")
        
        # 关闭所有工作线程
        for _ in range(2):
            await download_queue.put(None)
        for _ in range(2):
            await transcribe_queue.put((None, None))
        for _ in range(2):
            await summarize_queue.put((None, None))
        
        # 等待所有工作线程退出
        await asyncio.gather(*workers)
    
    # 运行异步主函数
    asyncio.run(main_async())
    
    # 【最后清掉各种缓存文件】
    clean_cache(
        clean_wav_cache = True,
        clean_asr_result = False,
    )
    
    # 清理提示词选择记忆
    clear_prompt_memory()