import json
import os
import re
from blbl_download import download_bilibili_audio
from xfasr import xf_asr
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


def main(url):

# 【这是第一部分，先把视频的音频部分下载下来】
    if url[:2] == "BV":
        url = "https://www.bilibili.com/video/" + url
    upload_file_name = download_bilibili_audio(url)
    
    # 处理文件名中的非法字符，避免特殊字符导致的报错
    illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized_name = re.sub(illegal_chars, '_', upload_file_name)
    # 确保文件名不为空
    if not sanitized_name:
        sanitized_name = "untitled"
    upload_file_name = sanitized_name

# 【这是第二部分，调用讯飞ASR，把音频文件转写为文本】
    xf_asr(
        upload_file_name = upload_file_name,
        appid = appid,
        secret_key = secret_key)

    # 【这是第三部分，调用 LLM 生成笔记】
    with open(f"./asr_result/{upload_file_name.split('.')[0]}.txt", "r", encoding="utf-8") as f:
        text = f.read()

    result = llm_inference(
        api_key = api_key,
        base_url = base_url,
        model_name = model_name,
        text = text)

    # 格式化输出文本
    result = format_note(result)
    
    try:
        with open(f"{output_path}/【智能笔记】{upload_file_name.split('.')[0]}.md", "w", encoding="utf-8") as f:
            f.write(f"视频链接：[{upload_file_name}]({url})\n\n")
            f.write(result)
    except:
        with open(f"./notebook_output/【智能笔记】{upload_file_name.split('.')[0]}.md", "w", encoding="utf-8") as f:
            f.write(f"视频链接：[{upload_file_name}]({url})\n\n")
            f.write(result)
    """
    这缺少鲁棒性，要考虑上传字数的问题，超字数得给报个错。
    """

    # # 【最后清掉各种缓存文件】
    # clean_cache(
    #     clean_wav_cache = True,
    #     clean_asr_result = False,
    # )



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
    
    for url in task_list:
        try:
            main(url)
        except Exception as e:
            print(f"视频链接 {url} 处理失败，错误信息：{e}")
    
    # 【最后清掉各种缓存文件】
    clean_cache(
        clean_wav_cache = True,
        clean_asr_result = False,
    )
    
    # 清理提示词选择记忆
    clear_prompt_memory()