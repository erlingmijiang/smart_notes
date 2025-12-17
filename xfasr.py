import base64
import hashlib
import hmac
import json
import os
import time
import requests
import urllib
import json

"""
调用讯飞语音识别API，进行语音转文本
"""

lfasr_host = "https://raasr.xfyun.cn/v2/api"
# 请求的接口名
api_upload = "/upload"
api_get_result = "/getResult"


class RequestApi(object):
    def __init__(self, appid, secret_key, upload_file_path):
        self.appid = appid
        self.secret_key = secret_key
        self.upload_file_path = upload_file_path
        self.ts = str(int(time.time()))
        self.signa = self.get_signa()

    def get_signa(self):
        appid = self.appid
        secret_key = self.secret_key
        m2 = hashlib.md5()
        m2.update((appid + self.ts).encode("utf-8"))
        md5 = m2.hexdigest()
        md5 = bytes(md5, encoding="utf-8")
        # 以secret_key为key, 上面的md5为msg， 使用hashlib.sha1加密结果为signa
        signa = hmac.new(secret_key.encode("utf-8"), md5, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        signa = str(signa, "utf-8")
        return signa

    def upload(self):
        # print("上传部分：")
        upload_file_path = self.upload_file_path
        file_len = os.path.getsize(upload_file_path)
        file_name = os.path.basename(upload_file_path)

        param_dict = {}
        param_dict["appId"] = self.appid
        param_dict["signa"] = self.signa
        param_dict["ts"] = self.ts
        param_dict["fileSize"] = file_len
        param_dict["fileName"] = file_name
        param_dict["duration"] = "200"
        print("upload参数：", param_dict)
        data = open(upload_file_path, "rb").read(file_len)

        response = requests.post(
            url=lfasr_host + api_upload + "?" + urllib.parse.urlencode(param_dict),
            headers={"Content-type": "application/json"},
            data=data,
        )
        print("upload_url:", response.request.url)
        result = json.loads(response.text)
        print("upload resp:", result)
        return result

    def get_result(self):
        uploadresp = self.upload()
        orderId = uploadresp["content"]["orderId"]
        # estimate_time = uploadresp["content"]["taskEstimateTime"] / 1000  # 转换为秒
        param_dict = {}
        param_dict["appId"] = self.appid
        param_dict["signa"] = self.signa
        param_dict["ts"] = self.ts
        param_dict["orderId"] = orderId
        param_dict["resultType"] = "transfer,predict"
        print("")
        # print("查询部分：")
        print("get result参数：", param_dict)
        print('正在解析中，请稍后……')
        status = 3
        # 讯飞官方建议使用回调的方式查询结果，查询接口有请求频率限制

        while status == 3:
            response = requests.post(
                url=lfasr_host + api_get_result + "?" + urllib.parse.urlencode(param_dict),
                headers={"Content-type": "application/json"}
            )
            # print("get_result_url:",response.request.url)
            result = json.loads(response.text)
            # print(result)             # 打印请求结果
            status = result["content"]["orderInfo"]["status"]
            # print("status=",status)   # 从请求结果里提取状态码并打印
            estimate_time = result['content']['taskEstimateTime'] / 1000  # 转换为秒
            print(f"正在识别中，请稍后... 剩余时间【{estimate_time}】秒")
            if status == 4:
                break
            time.sleep(15)  # 轮讯秒数，存在频率限制，低数值太快会被拒绝，高数值需要反复计算signa。差不多5~30秒轮询一次合适。
            # print("get_result resp:",result)
        return result


def decode(response_data: dict):
    """解码讯飞语音识别API传回来的最后一次数据，已调试确实能用
    这段代码千万别动了，层层循环解包太费劲了"""

    result_words = []

    for key in response_data:
        content = response_data["content"]
        order_result = content["orderResult"]
        order_result = eval(order_result)

        for lattice_data in order_result.values():

            for json_item in lattice_data:
                json_best = json_item["json_1best"]
                try:
                    json_best = eval(json_best)
                except:
                    pass
                words_list = json_best["st"]["rt"][0]["ws"]

                for word_item in words_list:
                    word = word_item["cw"][0]["w"]
                    result_words.append(word)

    result_words = "".join(result_words)
    return result_words

# 导入的时候，【导这个函数】
def xf_asr(upload_file_name, appid, secret_key):

    api = RequestApi(
        appid=appid,
        secret_key=secret_key,
        upload_file_path="./wav_cache/" + upload_file_name + '.wav',
    )

    res = api.get_result()
    res = decode(res)
    # print('语音识别结果为：',res)
    with open(
        f"./asr_result/{upload_file_name.split('.')[0]}.txt", "w", encoding="utf-8"
    ) as f:
        f.write(res)
    print("语音识别已完成")


def main():
    xf_asr(
        upload_file_name = upload_file_name,
        appid = appid,
        secret_key = secret_key)


if __name__ == "__main__":

######################################################
    # 参数配置
    with open("config.json", "r") as f:
        config = json.load(f)
        appid = config[0]["xunfei_asr"]["appid"]
        secret_key = config[0]["xunfei_asr"]["secret_key"]

######################################################

    upload_file_name = input("请输入待转写的文件名：")  # 导入的话就不要带这句了，直接往函数里传参

    main()
