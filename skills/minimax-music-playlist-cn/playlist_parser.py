"""
Minimax Music Playlist CN - 歌单解析器
支持：QQ音乐、网易云音乐、汽水音乐
基于官方 minimax-music-playlist v2.0 优化
"""

import re
import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter


# ============ 数据模型 ============

@dataclass
class Track:
    """歌曲信息"""
    name: str
    artists: List[str]
    album: str = ""
    duration_ms: int = 0


@dataclass
class Playlist:
    """歌单信息"""
    name: str
    tracks: List[Track]
    source: str  # qqmusic, netease, qishui, manual
    creator: str = ""
    play_count: int = 0


@dataclass
class TasteProfile:
    """品味画像"""
    total_tracks: int = 0
    total_playlists: int = 0
    top_artists: List[Tuple[str, int]] = field(default_factory=list)
    genres: Dict[str, float] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)
    playlist_names: List[str] = field(default_factory=list)


# ============ 歌单解析器 ============

class PlaylistParser:
    """歌单解析器 - 支持 QQ音乐、网易云音乐、汽水音乐"""
    
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    def _http_get(self, url: str, headers: Dict = None, timeout: int = 10) -> Optional[dict]:
        """HTTP GET 请求（使用 urllib 标准库）"""
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", self.USER_AGENT)
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)
            
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read().decode('utf-8')
                return json.loads(data)
        except Exception as e:
            print(f"HTTP 请求失败: {e}")
            return None
    
    def _http_get_raw(self, url: str, headers: Dict = None, timeout: int = 10, follow_redirects: bool = True) -> Tuple[int, Dict, str]:
        """HTTP GET 请求，返回 (status_code, headers, body)"""
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", self.USER_AGENT)
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)
            
            if not follow_redirects:
                class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
                    def redirect_request(self, req, fp, code, msg, headers, newurl):
                        return None
                opener = urllib.request.build_opener(NoRedirectHandler)
                response = opener.open(req, timeout=timeout)
            else:
                response = urllib.request.urlopen(req, timeout=timeout)
            
            status_code = response.getcode()
            resp_headers = dict(response.headers)
            body = response.read().decode('utf-8')
            return status_code, resp_headers, body
        except urllib.error.HTTPError as e:
            return e.code, {}, ""
        except Exception as e:
            print(f"HTTP 请求失败: {e}")
            return 0, {}, ""
    
    def parse(self, url: str, browser=None) -> Optional[Playlist]:
        """
        解析歌单链接，自动识别平台
        
        Args:
            url: 分享链接
            browser: 浏览器工具（汽水音乐需要）
        """
        if "y.qq.com" in url:
            return self._parse_qqmusic(url)
        elif "music.163.com" in url:
            return self._parse_netease(url)
        elif "qishui.douyin.com" in url or "music.douyin.com" in url:
            if browser:
                return self._parse_qishui(url, browser)
            else:
                print("汽水音乐需要浏览器工具支持")
                return None
        else:
            print(f"不支持的链接格式: {url}")
            return None
    
    def parse_manual(self, description: str) -> Playlist:
        """从用户描述构建虚拟歌单"""
        # 提取艺术家名
        artists = []
        # 常见分隔符
        for sep in ['、', '，', ',', '和', '与', ' ']:
            if sep in description:
                parts = description.split(sep)
                artists.extend([p.strip() for p in parts if p.strip()])
                break
        
        if not artists:
            artists = [description.strip()]
        
        # 构建虚拟歌单
        return Playlist(
            name="手动输入",
            source="manual",
            tracks=[
                Track(name=f"({artist}风格歌曲)", artists=[artist])
                for artist in artists[:10]  # 最多10个艺术家
            ]
        )
    
    def _extract_id(self, url: str, patterns: List[str]) -> Optional[str]:
        """从 URL 提取 ID"""
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _parse_qqmusic(self, url: str) -> Optional[Playlist]:
        """解析 QQ音乐歌单"""
        try:
            playlist_id = self._extract_id(url, [r'id=(\d+)', r'playlist/(\d+)'])
            if not playlist_id:
                print(f"无法从 URL 提取歌单 ID: {url}")
                return None
            
            api_url = (
                f"https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg"
                f"?disstid={playlist_id}&type=1&json=1&utf8=1&onlysong=0&format=json"
            )
            data = self._http_get(api_url, headers={"Referer": "https://y.qq.com/"})
            
            if not data:
                return None
            
            cdlist = data.get("cdlist", [])
            if not cdlist:
                return None
            
            cd = cdlist[0]
            playlist = Playlist(
                name=cd.get("dissname", "未知歌单"),
                source="qqmusic",
                creator=cd.get("nickname", ""),
                play_count=cd.get("visitnum", 0),
                tracks=[]
            )
            
            for song in cd.get("songlist", []):
                artists = [s.get("name", "") for s in song.get("singer", []) if s.get("name")]
                track = Track(
                    name=song.get("songname", ""),
                    artists=artists,
                    album=song.get("albumname", "")
                )
                playlist.tracks.append(track)
            
            print(f"✅ 解析 QQ音乐歌单: {playlist.name} ({len(playlist.tracks)} 首)")
            return playlist
            
        except Exception as e:
            print(f"❌ 解析 QQ音乐失败: {e}")
            return None
    
    def _parse_netease(self, url: str) -> Optional[Playlist]:
        """解析网易云音乐歌单"""
        try:
            playlist_id = self._extract_id(url, [r'id=(\d+)'])
            if not playlist_id:
                print(f"无法从 URL 提取歌单 ID: {url}")
                return None
            
            headers = {"Referer": "https://music.163.com/"}
            
            # 步骤1：获取歌单信息
            data = self._http_get(
                f"https://music.163.com/api/v3/playlist/detail?id={playlist_id}",
                headers=headers
            )
            
            if not data:
                return None
            
            playlist_info = data.get("playlist", {})
            track_ids = [t["id"] for t in playlist_info.get("trackIds", [])]
            
            # 步骤2：批量获取歌曲详情
            all_songs = []
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i+100]
                ids_str = ",".join(str(id) for id in batch)
                songs_data = self._http_get(
                    f"https://music.163.com/api/song/detail?ids=[{ids_str}]",
                    headers=headers
                )
                if songs_data:
                    all_songs.extend(songs_data.get("songs", []))
            
            playlist = Playlist(
                name=playlist_info.get("name", "未知歌单"),
                source="netease",
                creator=playlist_info.get("creator", {}).get("nickname", ""),
                play_count=playlist_info.get("playCount", 0),
                tracks=[]
            )
            
            for song in all_songs:
                # 兼容 artists 和 ar 字段
                artists_data = song.get("artists") or song.get("ar") or []
                artists = [a.get("name", "") for a in artists_data if a.get("name")]
                album_data = song.get("album") or song.get("al") or {}
                track = Track(
                    name=song.get("name", ""),
                    artists=artists,
                    album=album_data.get("name", "")
                )
                playlist.tracks.append(track)
            
            print(f"✅ 解析网易云音乐歌单: {playlist.name} ({len(playlist.tracks)} 首)")
            return playlist
            
        except Exception as e:
            print(f"❌ 解析网易云音乐失败: {e}")
            return None
    
    def _parse_qishui(self, url: str, browser) -> Optional[Playlist]:
        """解析汽水音乐歌单（需浏览器）"""
        try:
            # 解析短链接
            if "qishui.douyin.com/s/" in url:
                status, resp_headers, _ = self._http_get_raw(url, follow_redirects=False)
                url = resp_headers.get("Location", resp_headers.get("location", url))
            
            # 浏览器渲染
            browser.navigate(url)
            
            # 提取数据
            result = browser.console("""
                const text = document.body.innerText;
                const lines = text.split('\\n').filter(l => l.trim());
                const songs = [];
                const title = document.querySelector('h1')?.textContent?.trim() || '未知歌单';
                let i = 0;
                while (i < lines.length) {
                    const line = lines[i].trim();
                    if (/^\\d+$/.test(line) && i + 2 < lines.length) {
                        const songName = lines[i + 1]?.trim();
                        const artistAlbum = lines[i + 2]?.trim();
                        if (songName && artistAlbum && artistAlbum.includes('•')) {
                            const artists = artistAlbum.split('•')[0].trim();
                            songs.push({name: songName, artists});
                            i += 3;
                            continue;
                        }
                    }
                    i++;
                }
                JSON.stringify({title, songs});
            """)
            
            data = json.loads(result)
            playlist = Playlist(
                name=data.get("title", "未知歌单"),
                source="qishui",
                tracks=[
                    Track(
                        name=s["name"],
                        artists=[a.strip() for a in s["artists"].split(",") if a.strip()]
                    )
                    for s in data.get("songs", [])
                ]
            )
            
            print(f"✅ 解析汽水音乐歌单: {playlist.name} ({len(playlist.tracks)} 首)")
            return playlist
            
        except Exception as e:
            print(f"❌ 解析汽水音乐失败: {e}")
            return None


# ============ 品味分析器 ============

class TasteAnalyzer:
    """品味分析器 - 使用 artist_genre_map.json"""
    
    def __init__(self, skill_dir: str = None):
        """
        Args:
            skill_dir: SKILL.md 所在目录，用于加载 data 文件
        """
        if skill_dir is None:
            skill_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.skill_dir = skill_dir
        self.data_dir = os.path.join(skill_dir, "data")
        
        # 加载流派映射表
        self.genre_map = self._load_genre_map()
    
    def _load_genre_map(self) -> dict:
        """加载 artist_genre_map.json"""
        filepath = os.path.join(self.data_dir, "artist_genre_map.json")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_artist_genres(self, artist_name: str) -> List[str]:
        """获取艺术家的流派标签"""
        if artist_name in self.genre_map:
            return self.genre_map[artist_name].get("genres", [])
        return []
    
    def analyze(self, playlists: List[Playlist]) -> TasteProfile:
        """分析多个歌单，构建品味画像"""
        artist_counter = Counter()
        genre_counter = Counter()
        total_tracks = 0
        sources = set()
        playlist_names = []
        
        for playlist in playlists:
            playlist_names.append(playlist.name)
            sources.add(playlist.source)
            
            for track in playlist.tracks:
                total_tracks += 1
                
                # 统计艺术家
                for artist in track.artists:
                    if artist:
                        artist_counter[artist] += 1
                        
                        # 统计流派
                        genres = self.get_artist_genres(artist)
                        for genre in genres:
                            genre_counter[genre] += 1
        
        # 归一化流派比例
        total_genre_count = sum(genre_counter.values())
        genres = {}
        if total_genre_count > 0:
            for genre, count in genre_counter.most_common(10):
                genres[genre] = round(count / total_genre_count, 3)
        
        return TasteProfile(
            total_tracks=total_tracks,
            total_playlists=len(playlists),
            top_artists=artist_counter.most_common(10),
            genres=genres,
            sources=list(sources),
            playlist_names=playlist_names
        )
    
    def to_prompt(self, profile: TasteProfile, theme: str = None) -> str:
        """
        生成 mmx music 提示词
        
        Args:
            profile: 品味画像
            theme: 用户指定的主题（可选）
        """
        parts = []
        
        # 添加主题
        if theme:
            parts.append(theme)
        
        # 添加 Top 艺术家参考
        if profile.top_artists:
            artists = [a[0] for a in profile.top_artists[:3]]
            parts.append(f"style reference: {', '.join(artists)}")
        
        # 添加流派
        if profile.genres:
            top_genres = list(profile.genres.keys())[:3]
            parts.append(f"genres: {', '.join(top_genres)}")
        
        return ", ".join(parts) if parts else "pop music, mainstream style"
    
    def print_report(self, profile: TasteProfile):
        """打印品味分析报告"""
        print("\n" + "=" * 50)
        print("📊 音乐品味画像")
        print("=" * 50)
        
        print(f"\n📁 数据来源: {', '.join(profile.sources)}")
        print(f"🎵 歌单数量: {profile.total_playlists}")
        print(f"🎶 总歌曲数: {profile.total_tracks}")
        
        if profile.genres:
            print(f"\n🎼 流派分布:")
            for genre, ratio in list(profile.genres.items())[:5]:
                bar = "█" * int(ratio * 20)
                print(f"  {genre:20s} {ratio*100:5.1f}% {bar}")
        
        print(f"\n🎤 Top 10 艺术家:")
        for i, (artist, count) in enumerate(profile.top_artists, 1):
            print(f"  {i:2d}. {artist:20s} {count:3d} 首")
        
        print("=" * 50)


# ============ 命令行测试 ============

if __name__ == "__main__":
    import sys
    
    parser = PlaylistParser()
    analyzer = TasteAnalyzer()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # 示例 URL
        url = "https://y.qq.com/n3/other/pages/details/playlist.html?id=6390157139"
        print(f"使用示例 URL: {url}")
        print("提示: 可传入 URL 作为参数\n")
    
    # 解析歌单
    playlist = parser.parse(url)
    
    if playlist:
        # 分析品味
        profile = analyzer.analyze([playlist])
        
        # 打印报告
        analyzer.print_report(profile)
        
        # 展示前10首歌
        print(f"\n📋 前 10 首歌曲:")
        for i, track in enumerate(playlist.tracks[:10], 1):
            artists_str = "、".join(track.artists)
            print(f"  {i:2d}. {track.name} / {artists_str}")
    else:
        print("❌ 解析失败")
