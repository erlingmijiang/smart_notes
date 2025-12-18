import os
from openai import OpenAI
import json

# 全局变量用于记忆用户选择的提示词文件路径
_selected_prompt_file = None


def select_prompt_file():

    """
    选择系统提示词的功能
    可以从多套提示词模板中选择一个
    支持记忆功能，避免重复选择
    """
    global _selected_prompt_file
    
    # 如果已经选择过，直接返回记忆的路径
    if _selected_prompt_file is not None:
        return _selected_prompt_file
    
    prompt_dir = './prompt'
    
    prompt_files = [f for f in os.listdir(prompt_dir) if f.endswith('.txt')]
    
    if len(prompt_files) == 1:
        _selected_prompt_file = os.path.join(prompt_dir, prompt_files[0])
        return _selected_prompt_file
    
    print('请选择要使用的提示词文件：')
    for i, filename in enumerate(prompt_files, 1):
        display_name = filename[:-4]  # 去掉 .txt 后缀
        print(f'{i}. {display_name}')
    
    while True:
        try:
            choice = input(f'请输入序号（1-{len(prompt_files)}）：')
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(prompt_files):
                selected_file = prompt_files[choice_num - 1]
                display_name = selected_file[:-4]  # 去掉 .txt 后缀用于显示
                print(f'已选择提示词文件：{display_name}')
                _selected_prompt_file = os.path.join(prompt_dir, selected_file)
                return _selected_prompt_file
            else:
                print(f'请输入1到{len(prompt_files)}之间的序号。')
        except ValueError:
            print('请输入有效的数字序号。')

def llm_inference(api_key, base_url, model_name, text):

    prompt_file_path = select_prompt_file()
    
    if prompt_file_path is None:
        return None
    
    client = OpenAI(
        api_key = api_key,
        base_url = base_url)

    print('笔记生成中……')

    # 载入用户选择的系统提示词模板
    with open(prompt_file_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    response = client.chat.completions.create(
        model = model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        stream=False,
    )

    print('笔记已生成！')
    
    return response.choices[0].message.content


def clear_prompt_memory():
    """
    清理记忆的用户选择，避免干扰下一次程序运行
    【在主程序结束时调用此函数！】
    """
    global _selected_prompt_file
    _selected_prompt_file = None
    # print("提示词记忆已清理")



if __name__ == "__main__":
    
######################################################
    # 参数配置
    with open("config.json", "r") as f:
        config = json.load(f)
        api_key = config[1]['llm']['api_key']
        base_url = config[1]['llm']['base_url']
        model_name = config[1]['llm']['model_name']

######################################################

    with open('./asr_result/test.txt','r',encoding = 'utf-8') as f:
        text = f.read()

    result = llm_inference(
        api_key = api_key,
        base_url = base_url,
        model_name = model_name,
        text = text)

    with open('output.md','w',encoding = 'utf-8') as f:
        f.write(result) 

    clear_prompt_memory()