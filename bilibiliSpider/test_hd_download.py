import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibiliSpider import BilibiliSpider
from bilibiliSpider.bilibili_spider import check_ffmpeg_available, merge_video_audio

cookie = "_uuid=85DE74210-7AC2-AE25-F1DF-2F267C710EFB880761infoc; b_lsid=3DDE27FD_19DC001F821; b_nut=1773926080; bili_jct=5ab70fcc709eae7e27a04e2e2de1bcff; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzcyOTc4NzMsImlhdCI6MTc3NzAzODYxMywicGx0IjotMX0.2HwAoPMQdFQHclyZ_igbuqNI7EP2hSfQfgpMrGwF9k8; bili_ticket_expires=1777297813; bmg_af_switch=1; bmg_src_def_domain=i1.hdslb.com; browser_resolution=1512-859; buvid_fp=9679d52942516729087dd7ab1ab2b62b; buvid3=7A28E347-28FB-7933-FC21-FC8D3664AF3980526infoc; buvid4=0E959D79-5665-AE3D-1C77-9471FFFE48BC80891-026031921-X7ayaHkoo1nmL52waLEYuAkhm0dNdof88t/uH7pVJ7tgF1XUorAyMgwLCRJPz5l+; CURRENT_FNVAL=4048; CURRENT_QUALITY=0; DedeUserID=22919972; DedeUserID__ckMd5=02053c7dd74fc11c; home_feed_column=5; rpdid=0zbfvRPX7t|YWmGvgoF|rpy|3w1W3dds; SESSDATA=4f51a0c9%2C1792594660%2C7ab29%2A42CjBPx-843u76kKHYraebRtZ-OMYcc-vPCqQiqMaKsEB7UdZIqHsuWbQcJz3jy-0cPa0SVlVMd2NqdXVSYWpaNGhCaU5TYnRKS2NNZjN4X0psOC1SYjZ2WENrNE5QU2ZaUmwwQjM0QkhWdDRMYXF5QnBpa1B3OXNneGRMbEowazVpXzVuM1RBdzVRIIEC; sid=7rme7h23; theme-tip-show=SHOWED"

print("=" * 60)
print("B站高清视频下载测试（自动合并音视频）")
print("=" * 60)

bvid = "BV1xQcvzbEAi"
save_dir = "./downloads"

# 检查ffmpeg
if check_ffmpeg_available():
    print("\n✓ ffmpeg 已安装，支持音视频自动合并")
else:
    print("\n✗ ffmpeg 未安装，无法自动合并音视频")
    print("  安装命令: brew install ffmpeg (macOS) 或 sudo apt install ffmpeg (Linux)")

print(f"\n正在使用Cookie获取视频信息: {bvid}")
print("-" * 60)

spider = BilibiliSpider(cookie=cookie)

print("\n1. 先获取视频信息和可用画质...")
video_info = spider.get_structured_data(bvid)

if video_info['status'] == 'success':
    data = video_info['data']
    summary = video_info['summary']
    
    print("\n" + "=" * 60)
    print("视频信息:")
    print("-" * 60)
    print(f"标题: {summary.get('title')}")
    print(f"作者: {summary.get('author')}")
    print(f"播放量: {summary.get('play_count')}")
    print(f"弹幕数: {summary.get('danmaku_count')}")
    
    print("\n" + "=" * 60)
    print("可用视频流:")
    print("-" * 60)
    
    video_streams = data.get('video_streams', [])
    if video_streams:
        for i, stream in enumerate(video_streams):
            quality_id = stream.get('id')
            width = stream.get('width')
            height = stream.get('height')
            codecs = stream.get('codecs')
            bandwidth = stream.get('bandwidth')
            
            quality_map = {
                120: '2160p (4K)',
                116: '1080p60',
                112: '1080p+',
                80: '1080p',
                74: '720p60',
                64: '720p',
                32: '480p',
                16: '360p',
            }
            
            quality_name = quality_map.get(quality_id, f'未知({quality_id})')
            
            print(f"\n流 {i+1}:")
            print(f"  画质ID: {quality_id} ({quality_name})")
            print(f"  分辨率: {width}x{height}")
            print(f"  编码: {codecs}")
            print(f"  码率: {bandwidth} bps")
    else:
        print("未找到视频流")
    
    print("\n" + "=" * 60)
    print("2. 开始下载1080p视频并自动合并...")
    print("-" * 60)
    
    # 下载视频并自动合并
    result = spider.download_video(
        bvid=bvid,
        save_dir=save_dir,
        quality="1080p",
        download_audio=True,
        merge=True,
        keep_original=True
    )
    
    if result:
        print("\n" + "=" * 60)
        print("下载结果:")
        print("-" * 60)
        
        if result.get('video_file'):
            print(f"视频文件: {result['video_file']}")
        else:
            print("视频下载失败或未找到1080p画质")
        
        if result.get('audio_file'):
            print(f"音频文件: {result['audio_file']}")
        else:
            print("音频下载失败")
        
        if result.get('merged_file'):
            print(f"\n✓ 合并后的文件: {result['merged_file']}")
        else:
            print("\n✗ 合并失败或未进行合并")
        
        if result.get('video_info'):
            video_info = result['video_info']
            video_streams = video_info.get('video_streams', [])
            if video_streams:
                print(f"\n实际可用画质:")
                for stream in video_streams:
                    quality_id = stream.get('id')
                    width = stream.get('width')
                    height = stream.get('height')
                    quality_map = {
                        120: '2160p (4K)',
                        116: '1080p60',
                        112: '1080p+',
                        80: '1080p',
                        74: '720p60',
                        64: '720p',
                        32: '480p',
                        16: '360p',
                    }
                    quality_name = quality_map.get(quality_id, f'未知({quality_id})')
                    print(f"  - {quality_name} ({width}x{height})")
    else:
        print("下载失败")
else:
    print("获取视频信息失败")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
