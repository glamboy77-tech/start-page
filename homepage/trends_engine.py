import billboard
import requests
import json
import re
from datetime import datetime, timedelta, timezone
import sys

# 멜론 라이브러리 임포트 시도
try:
    from melon import ChartData as MelonChartData
except ImportError:
    MelonChartData = None

def is_embeddable(video_id):
    """
    해당 비디오 ID가 외부 사이트에서 재생(임베드) 가능한지 확인합니다.
    """
    if not video_id:
        return False
    try:
        # 임베드 URL에 직접 요청하여 재생 가능 여부 확인
        url = f"https://www.youtube.com/embed/{video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        # 재생 제한 문구가 포함되어 있는지 확인
        if "UNPLAYABLE" in response.text or "disabled-by-owner" in response.text or "disabled by the video owner" in response.text:
            return False
        return True
    except:
        # 오류 발생 시 일단 재생 가능하다고 가정
        return True

def fetch_youtube_data(query):
    """
    유튜브에서 검색하여 재생 가능한(임베드 허용) 비디오 ID와 썸네일을 가져옵니다.
    차단된 경우 [Audio], [Lyric Video] 순으로 대체 영상을 검색합니다.
    """
    # 검색 순서: 공식 뮤직비디오 -> 가사 비디오 -> 오피셜 오디오
    search_types = ["official music video", "lyric video", "official audio"]
    
    clean_query = query.replace('"', '').replace("'", "")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    for suffix in search_types:
        try:
            full_query = f"{clean_query} {suffix}"
            search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(full_query)}&hl=en"
            
            response = requests.get(search_url, headers=headers, timeout=10)
            video_ids = re.findall(r"\"videoId\":\"([a-zA-Z0-9_-]{11})\"", response.text)
            
            if not video_ids:
                video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", response.text)

            for vid in video_ids[:5]:  # 상위 5개 결과 중 확인
                if len(vid) == 11 and vid not in ["None", "null", "undefined"]:
                    if is_embeddable(vid):
                        return {
                            'id': vid,
                            'thumbnail': f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
                        }
                    else:
                        print(f"  └─ 영상 {vid} 는 퍼가기 제한됨. 다른 영상 찾는 중...")
                        
        except Exception as e:
            print(f"YouTube 검색 시도 중 오류: {e}")
            continue
            
    return {'id': None, 'thumbnail': None}

def fetch_billboard(chart_name='hot-100', limit=10):
    print(f"Billboard {chart_name} 차트 데이터를 가져오는 중...")
    try:
        chart = billboard.ChartData(chart_name)
        chart_data = []
        for song in chart[:limit]:
            # 쌍따옴표 제거로 JSON 깨짐 방지
            title = song.title.replace('"', '')
            artist = song.artist.replace('"', '')
            
            query = f"{title} {artist}"
            yt_data = fetch_youtube_data(query)
            
            # 모든 이미지를 유튜브 썸네일로 강제 고정
            videoId = yt_data.get('id')
            image_url = f"https://i.ytimg.com/vi/{videoId}/hqdefault.jpg" if videoId else None
            
            chart_data.append({
                "rank": song.rank,
                "title": title,
                "artist": artist,
                "image": image_url,
                "videoId": videoId
            })
    
        return chart_data
    except Exception as e:
        print(f"Billboard {chart_name} 데이터 가져오기 실패: {e}")
        return []

def fetch_melon():
    print("Melon 실시간 차트 데이터를 가져오는 중...")
    if MelonChartData is None:
        print("Melon 라이브러리가 설치되지 않아 건너뜁니다.")
        return []
    
    try:
        chart = MelonChartData() 
        chart_data = []
        
        count = 0
        for i in range(len(chart)):
            if count >= 10:
                break
            song = chart[i] 
            
            rank = i + 1
            title = ""
            artist = ""
            image = ""
            
            if isinstance(song, dict):
                title = (song.get('title') or "").replace('"', '')
                artist = (song.get('artist') or "").replace('"', '')
            else:
                title = (getattr(song, 'title', '') or "").replace('"', '')
                artist = (getattr(song, 'artist', '') or "").replace('"', '')
                
            query = f"{title} {artist}"
            yt_data = fetch_youtube_data(query)

            # 모든 이미지를 유튜브 썸네일로 강제 고정
            videoId = yt_data.get('id')
            image = f"https://i.ytimg.com/vi/{videoId}/hqdefault.jpg" if videoId else None

            chart_data.append({
                "rank": rank,
                "title": title,
                "artist": artist,
                "image": image,
                "videoId": videoId
            })
            count += 1
            
        return chart_data
    except Exception as e:
        print(f"Melon 데이터 가져오기 실패: {e}")
        return []

def fetch_youtube_trending():
    print("YouTube 급상승 차트 데이터를 가져오는 중...")
    chart_data = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'Accept-Language': 'ko-KR,ko;q=0.9'}
        # 한국 유튜브 급상승 음악 페이지
        url = "https://www.youtube.com/feed/trending?bp=4gINGgt5dG1hcV9jaGFydA%3D%3D" 
        res = requests.get(url, headers=headers, timeout=15)
        
        # 비디오 정보 덩어리들을 추출
        # 유튜브의 복잡한 JSON 구조에서 제목과 채널명을 가급적 정확히 뽑아냅니다.
        titles = re.findall(r'\"title\":{\"runs\":\[{\"text\":\"(.*?)\"}\]', res.text)
        video_ids = re.findall(r'\"videoId\":\"([a-zA-Z0-9_-]{11})\"', res.text)
        channel_names = re.findall(r'\"longBylineText\":{\"runs\":\[{\"text\":\"(.*?)\"}\]', res.text)
        
        count = 0
        added_ids = set()
        for i in range(len(video_ids)):
            vid = video_ids[i]
            if vid in added_ids: continue
            
            # 검색 결과 중 실제 영상 제목과 매칭 (필터링 필요)
            title = titles[i] if i < len(titles) else f"Trending Video {count+1}"
            artist = channel_names[i] if i < len(channel_names) else "YouTube Korea"
            
            # 불필요한 공통 문구 제거
            title = title.replace('\\u0026', '&').replace('\"', '')
            artist = artist.replace('\\u0026', '&').replace('\"', '')
            
            if "youtube" in title.lower() or "trending" in title.lower(): continue

            chart_data.append({
                "rank": count + 1,
                "title": title,
                "artist": artist,
                "image": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "videoId": vid
            })
            added_ids.add(vid)
            count += 1
            if count >= 10: break
            
        return chart_data
    except Exception as e:
        print(f"YouTube Trending 실패: {e}")
        return []

def load_json_chart(filepath, json_key, chart_name):
    """
    JSON 파일에서 차트 데이터를 읽고 YouTube 정보를 추가합니다.
    JSON 파일 형식: {"key": [{"rank": 1, "title": "곡제목", "artist": "가수명"}, ...]}
    """
    print(f"{chart_name} 차트 데이터를 로드하는 중...")
    chart_data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        items = json_data.get(json_key, [])
        
        for item in items:
            if len(chart_data) >= 10:
                break
            
            title = item.get('title', '').replace('"', '')
            artist = item.get('artist', '').replace('"', '')
            
            if not title or not artist:
                continue
            
            # YouTube에서 곡 검색
            query = f"{title} {artist}"
            yt_data = fetch_youtube_data(query)
            
            chart_data.append({
                "rank": len(chart_data) + 1,
                "title": title,
                "artist": artist,
                "image": f"https://i.ytimg.com/vi/{yt_data['id']}/hqdefault.jpg" if yt_data['id'] else None,
                "videoId": yt_data['id']
            })
        
        return chart_data
    except FileNotFoundError:
        print(f"파일을 찾을 수 없음: {filepath}")
        return []
    except Exception as e:
        print(f"{chart_name} 로드 실패: {e}")
        return []

def main():
    print("=== 데이터 수집 시작 (배치 모드) ===")
    
    # 1. 데이터 수집
    billboard_hot100 = fetch_billboard('hot-100')
    billboard_rock = fetch_billboard('hot-rock-songs')
    melon_data = fetch_melon()
    shazam_korea = load_json_chart('data/shazam_korea.json', 'shazam_korea', 'Shazam Korea')
    spotify_global = load_json_chart('data/spotify_global.json', 'spotify_global', 'Spotify Global')
    youtube_shorts_korea = load_json_chart('data/youtube_shorts_korea.json', 'youtube_shorts_korea', 'YouTube Shorts Korea')
    youtube_shorts_global = load_json_chart('data/youtube_shorts_global.json', 'youtube_shorts_global', 'YouTube Shorts Global')
    
    # KST (한국 시간) 생성
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    
    # 2. 데이터 구조화
    final_data = {
        "last_updated": now_kst.strftime("%Y-%m-%d %H:%M:%S"),
        "billboard": billboard_hot100,
        "billboard_rock": billboard_rock,
        "melon": melon_data,
        "shazam_korea": shazam_korea,
        "spotify_global": spotify_global,
        "youtube_shorts_korea": youtube_shorts_korea,
        "youtube_shorts_global": youtube_shorts_global
    }
    
    # 3. JS 파일로 저장
    js_content = f"const rankData = {json.dumps(final_data, ensure_ascii=False, indent=4)};"
    with open('rank_data.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 데이터 수집 및 저장 완료: rank_data.js")

if __name__ == "__main__":
    main()
