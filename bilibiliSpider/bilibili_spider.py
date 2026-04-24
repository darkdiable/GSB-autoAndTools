import re
import json
import time
import requests
import subprocess
import shutil
import os
from bs4 import BeautifulSoup
from typing import Dict, Optional, List, Any
from urllib.parse import urljoin, urlparse

from .config import (
    get_default_headers,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
)


def check_ffmpeg_available() -> bool:
    return shutil.which('ffmpeg') is not None


def merge_video_audio(
    video_path: str,
    audio_path: str,
    output_path: str,
    keep_original: bool = True,
) -> bool:
    if not check_ffmpeg_available():
        print("错误: 未找到ffmpeg，请先安装ffmpeg")
        print("安装命令: brew install ffmpeg (macOS) 或 sudo apt install ffmpeg (Linux)")
        return False
    
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        return False
    
    if not os.path.exists(audio_path):
        print(f"错误: 音频文件不存在: {audio_path}")
        return False
    
    print(f"\n正在合并音视频...")
    print(f"  视频文件: {video_path}")
    print(f"  音频文件: {audio_path}")
    print(f"  输出文件: {output_path}")
    
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-i', audio_path,
        '-c', 'copy',
        '-y',
        output_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print("合并成功!")
        
        if not keep_original:
            print("正在删除原始文件...")
            try:
                os.remove(video_path)
                os.remove(audio_path)
                print("原始文件已删除")
            except OSError as e:
                print(f"删除原始文件失败: {str(e)}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"合并失败: {e.stderr}")
        return False
    except Exception as e:
        print(f"合并过程中发生错误: {str(e)}")
        return False


class BilibiliSpider:
    def __init__(self, cookie: Optional[str] = None):
        self.cookie = cookie
        self.session = requests.Session()
        self.session.headers.update(get_default_headers(cookie))
        
    def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Optional[requests.Response]:
        for attempt in range(MAX_RETRIES):
            try:
                request_headers = self.session.headers.copy()
                if headers:
                    request_headers.update(headers)
                    
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    headers=request_headers,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                )
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                print(f"请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    print(f"已达到最大重试次数 {MAX_RETRIES}，放弃请求")
                    return None
        return None
    
    def extract_initial_state(self, html: str) -> Optional[Dict]:
        patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});\s*\(function',
            r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*;',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
        return None
    
    def extract_video_info(self, bvid: str) -> Optional[Dict[str, Any]]:
        url = f"https://www.bilibili.com/video/{bvid}/"
        
        print(f"正在获取视频页面: {url}")
        response = self._make_request(url)
        if not response:
            return None
        
        html = response.text
        soup = BeautifulSoup(html, 'lxml')
        
        video_info = {
            'bvid': bvid,
            'url': url,
            'title': None,
            'play_count': None,
            'danmaku_count': None,
            'author': None,
            'description': None,
            'publish_time': None,
            'duration': None,
            'video_streams': [],
            'audio_streams': [],
        }
        
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            video_info['title'] = title_text.replace('_哔哩哔哩_bilibili', '').strip()
        
        meta_title = soup.find('meta', {'property': 'og:title'})
        if meta_title and not video_info['title']:
            video_info['title'] = meta_title.get('content', '').strip()
        
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            video_info['description'] = meta_desc.get('content', '').strip()
        
        initial_state = self.extract_initial_state(html)
        if initial_state:
            try:
                video_data = initial_state.get('videoData', {})
                if video_data:
                    if not video_info['title']:
                        video_info['title'] = video_data.get('title', '')
                    
                    stat = video_data.get('stat', {})
                    video_info['play_count'] = stat.get('view', 0)
                    video_info['danmaku_count'] = stat.get('danmaku', 0)
                    
                    owner = video_data.get('owner', {})
                    video_info['author'] = owner.get('name', '')
                    
                    video_info['duration'] = video_data.get('duration', 0)
                    video_info['publish_time'] = video_data.get('pubdate', 0)
                    
                aid = initial_state.get('aid', 0)
                cid = initial_state.get('cid', 0)
                video_info['aid'] = aid
                video_info['cid'] = cid
                
            except (KeyError, TypeError) as e:
                print(f"解析INITIAL_STATE时出错: {str(e)}")
        
        if video_info.get('aid') and video_info.get('cid'):
            play_info = self.get_play_url(
                video_info['aid'],
                video_info['cid'],
            )
            if play_info:
                video_info['video_streams'] = play_info.get('video_streams', [])
                video_info['audio_streams'] = play_info.get('audio_streams', [])
        
        return video_info
    
    def get_play_url(
        self,
        aid: int,
        cid: int,
        quality: int = 80,
    ) -> Optional[Dict[str, List]]:
        url = "https://api.bilibili.com/x/player/playurl"
        
        params = {
            'avid': aid,
            'cid': cid,
            'qn': quality,
            'type': '',
            'otype': 'json',
            'fourk': 1,
            'fnver': 0,
            'fnval': 16,
        }
        
        headers = {
            'Referer': f'https://www.bilibili.com/video/av{aid}/',
        }
        
        print(f"正在获取播放地址 (aid={aid}, cid={cid})")
        response = self._make_request(url, params=params, headers=headers)
        
        if not response:
            return None
        
        try:
            data = response.json()
            if data.get('code') != 0:
                print(f"获取播放地址失败: {data.get('message', '未知错误')}")
                return None
            
            result = {
                'video_streams': [],
                'audio_streams': [],
            }
            
            dash_data = data.get('data', {}).get('dash', {})
            if dash_data:
                video_streams = dash_data.get('video', [])
                for stream in video_streams:
                    result['video_streams'].append({
                        'id': stream.get('id'),
                        'base_url': stream.get('baseUrl'),
                        'backup_urls': stream.get('backupUrl', []),
                        'bandwidth': stream.get('bandwidth'),
                        'codecid': stream.get('codecid'),
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'frame_rate': stream.get('frameRate'),
                        'mime_type': stream.get('mimeType'),
                        'codecs': stream.get('codecs'),
                    })
                
                audio_streams = dash_data.get('audio', [])
                for stream in audio_streams:
                    result['audio_streams'].append({
                        'id': stream.get('id'),
                        'base_url': stream.get('baseUrl'),
                        'backup_urls': stream.get('backupUrl', []),
                        'bandwidth': stream.get('bandwidth'),
                        'codecid': stream.get('codecid'),
                        'mime_type': stream.get('mimeType'),
                        'codecs': stream.get('codecs'),
                    })
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"解析播放地址JSON失败: {str(e)}")
            return None
    
    def download_file(
        self,
        url: str,
        save_path: str,
        headers: Optional[Dict] = None,
        show_progress: bool = True,
    ) -> bool:
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        request_headers.update({
            'Range': 'bytes=0-',
            'Referer': 'https://www.bilibili.com/',
        })
        
        print(f"开始下载: {url}")
        print(f"保存路径: {save_path}")
        
        try:
            response = self.session.get(
                url,
                headers=request_headers,
                stream=True,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if show_progress and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r下载进度: {percent:.2f}% ({downloaded}/{total_size} bytes)", end='')
            
            if show_progress:
                print()
            
            print(f"下载完成: {save_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"下载失败: {str(e)}")
            return False
        except IOError as e:
            print(f"文件写入失败: {str(e)}")
            return False
    
    def download_video(
        self,
        bvid: str,
        save_dir: str = "./",
        quality: str = "1080p",
        download_audio: bool = True,
        merge: bool = True,
        keep_original: bool = True,
    ) -> Optional[Dict]:
        video_info = self.extract_video_info(bvid)
        if not video_info:
            print("无法获取视频信息")
            return None
        
        if not video_info.get('video_streams'):
            print("未找到视频流地址，可能需要登录Cookie才能获取高清视频")
            print("提示：请在浏览器登录B站后，复制Cookie并传递给BilibiliSpider")
            return video_info
        
        os.makedirs(save_dir, exist_ok=True)
        
        quality_map = {
            '2160p': 120,
            '1080p60': 116,
            '1080p': 80,
            '720p60': 74,
            '720p': 64,
            '480p': 32,
            '360p': 16,
        }
        
        target_quality = quality_map.get(quality, 80)
        
        selected_video = None
        for stream in video_info['video_streams']:
            if stream.get('id') == target_quality:
                selected_video = stream
                break
        
        if not selected_video and video_info['video_streams']:
            selected_video = video_info['video_streams'][0]
            print(f"未找到指定画质 {quality}，使用可用的最高画质")
        
        result = {
            'video_info': video_info,
            'video_file': None,
            'audio_file': None,
            'merged_file': None,
        }
        
        if selected_video:
            video_url = selected_video.get('base_url')
            if video_url:
                safe_title = re.sub(r'[\\/:*?"<>|]', '_', video_info.get('title', bvid))
                video_filename = f"{safe_title}_video.mp4"
                video_path = os.path.join(save_dir, video_filename)
                
                video_headers = {
                    'Referer': f'https://www.bilibili.com/video/{bvid}/',
                }
                
                if self.download_file(video_url, video_path, headers=video_headers):
                    result['video_file'] = video_path
        
        if download_audio and video_info.get('audio_streams'):
            selected_audio = video_info['audio_streams'][0]
            if selected_audio:
                audio_url = selected_audio.get('base_url')
                if audio_url:
                    safe_title = re.sub(r'[\\/:*?"<>|]', '_', video_info.get('title', bvid))
                    audio_filename = f"{safe_title}_audio.mp4"
                    audio_path = os.path.join(save_dir, audio_filename)
                    
                    audio_headers = {
                        'Referer': f'https://www.bilibili.com/video/{bvid}/',
                    }
                    
                    if self.download_file(audio_url, audio_path, headers=audio_headers):
                        result['audio_file'] = audio_path
        
        if merge and result['video_file'] and result['audio_file']:
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', video_info.get('title', bvid))
            output_filename = f"{safe_title}.mp4"
            output_path = os.path.join(save_dir, output_filename)
            
            if merge_video_audio(
                result['video_file'],
                result['audio_file'],
                output_path,
                keep_original
            ):
                result['merged_file'] = output_path
        
        return result
    
    def get_structured_data(self, bvid: str) -> Dict[str, Any]:
        video_info = self.extract_video_info(bvid)
        
        structured = {
            'status': 'success' if video_info else 'failed',
            'timestamp': time.time(),
            'data': video_info,
            'summary': {},
        }
        
        if video_info:
            structured['summary'] = {
                'title': video_info.get('title'),
                'bvid': video_info.get('bvid'),
                'play_count': video_info.get('play_count'),
                'danmaku_count': video_info.get('danmaku_count'),
                'author': video_info.get('author'),
                'video_streams_available': len(video_info.get('video_streams', [])),
                'audio_streams_available': len(video_info.get('audio_streams', [])),
            }
        
        return structured


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='B站视频爬虫')
    parser.add_argument('bvid', type=str, help='视频BV号，例如: BV1xQcvzbEAi')
    parser.add_argument('--cookie', type=str, default=None, help='B站登录Cookie（可选，用于获取高清视频）')
    parser.add_argument('--download', action='store_true', help='是否下载视频')
    parser.add_argument('--quality', type=str, default='1080p', choices=['2160p', '1080p60', '1080p', '720p60', '720p', '480p', '360p'], help='视频画质')
    parser.add_argument('--save-dir', type=str, default='./downloads', help='下载保存目录')
    parser.add_argument('--no-audio', action='store_true', help='不下载音频')
    parser.add_argument('--no-merge', action='store_true', help='不自动合并音视频（默认自动合并）')
    parser.add_argument('--delete-original', action='store_true', help='合并后删除原始音视频文件（默认保留）')
    parser.add_argument('--output', type=str, default=None, help='输出JSON文件路径')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("B站视频爬虫")
    print("=" * 60)
    
    if check_ffmpeg_available():
        print("\n✓ ffmpeg 已安装，支持音视频自动合并")
    else:
        print("\n✗ ffmpeg 未安装，无法自动合并音视频")
        print("  安装命令: brew install ffmpeg (macOS) 或 sudo apt install ffmpeg (Linux)")
    
    spider = BilibiliSpider(cookie=args.cookie)
    
    print(f"\n正在处理视频: {args.bvid}")
    print("-" * 60)
    
    if args.download:
        result = spider.download_video(
            bvid=args.bvid,
            save_dir=args.save_dir,
            quality=args.quality,
            download_audio=not args.no_audio,
            merge=not args.no_merge,
            keep_original=not args.delete_original,
        )
    else:
        result = spider.get_structured_data(args.bvid)
    
    print("\n" + "=" * 60)
    print("结果输出:")
    print("-" * 60)
    
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n结果已保存到: {args.output}")
        except IOError as e:
            print(f"\n保存文件失败: {str(e)}")
    
    return result


if __name__ == "__main__":
    main()
