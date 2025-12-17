import os
import yt_dlp
# import subprocess


def download_bilibili_audio(url: str, out_dir: str = "./wav_cache"):
    """
    下载单个 B 站视频的音频部分并转换为 WAV 格式。
        :param url: 完整的 B 站视频链接，例如 https://www.bilibili.com/video/BV1xxxxxx
        :param out_dir: 保存目录，默认 ./wav_cache
        :return: 视频标题
    """
    # 确保输出目录存在
    os.makedirs(out_dir, exist_ok=True)

    # 先获取视频信息以提取标题
    info_opts = {
        "quiet": True,
        "no_warnings": True,
    }

    video_title = None
    with yt_dlp.YoutubeDL(info_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            video_title = info_dict.get("title", "unknown_title")
        except yt_dlp.utils.DownloadError as e:
            print(f"\n获取视频信息出错: {e}")
            return None

    def progress_hook(d):
        if d["status"] == "downloading":
            print(f"\r下载进度: {d['_percent_str']} 速度: {d['_speed_str']}", end="")
        elif d["status"] == "finished":
            print("\n下载完成，正在转换为 wav 格式…")

    # yt-dlp 参数说明
    ydl_opts = {
        # 保存路径和文件名模板，%(title)s 为视频标题，%(ext)s 为文件后缀
        "outtmpl": f"{out_dir}/%(title)s.%(ext)s",
        # 仅下载最低质量的音频
        "format": "worstaudio/worst",
        # 下载时显示进度条
        "progress_hooks": [progress_hook],
        # 后处理选项：转换为 WAV
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
    }

    # 开始下载
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            print("\n音频下载并转换完成！")
            return video_title
        except yt_dlp.utils.DownloadError as e:
            print(f"\n下载出错: {e}")
            return None


if __name__ == "__main__":
    download_bilibili_audio(input("请输入B站视频链接："))
