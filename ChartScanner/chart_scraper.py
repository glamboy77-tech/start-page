import asyncio
from playwright.async_api import async_playwright
import os
import traceback
from dotenv import load_dotenv
from playwright_stealth import stealth

# Output directory for screenshots (shared with homepage)
OUTPUT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "homepage", "data")
)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# .env 파일에서 환경변수 로드
load_dotenv()

async def scrape_chart(url, output_file, width=800, height=2000, name=""):
    """일반 차트 스크린샷 저장"""
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
            
            print(f"\n[{name}] 접속 중: {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            print(f"[{name}] 페이지 로딩 중...")
            await page.wait_for_timeout(5000)
            
            print(f"[{name}] 스크린샷 캡처 중...")
            await page.screenshot(path=output_file, full_page=False)
            
            file_size = os.path.getsize(output_file)
            size_kb = file_size / 1024
            print(f"[{name}]  완료! {output_file} ({size_kb:.2f} KB)")
            
            await browser.close()
            return True
            
    except Exception as e:
        print(f"[{name}]  오류 발생: {e}")
        if browser:
            try:
                await browser.close()
            except:
                pass
        return False

async def main():
    """모든 차트 스크린샷 생성"""
    
    charts = [
        {
            "name": "Shazam Korea",
            "url": "https://www.shazam.com/charts/viral/south-korea",
            "output": os.path.join(OUTPUT_DIR, "shazam_viral_korea.png"),
            "type": "normal"
        },
        {
            "name": "Shazam Global",
            "url": "https://www.shazam.com/charts/viral/world",
            "output": os.path.join(OUTPUT_DIR, "shazam_viral_global.png"),
            "type": "normal"
        },
        {
            "name": "YouTube Shorts Korea",
            "url": "https://charts.youtube.com/charts/TopShortsSongs/kr/daily",
            "output": os.path.join(OUTPUT_DIR, "youtube_shorts_korea.png"),
            "type": "normal"
        },
        {
            "name": "YouTube Shorts Global",
            "url": "https://charts.youtube.com/charts/TopShortsSongs/global/daily",
            "output": os.path.join(OUTPUT_DIR, "youtube_shorts_global.png"),
            "type": "normal"
        }
    ]
    
    print("=" * 70)
    print("차트 스크린샷 생성 시작")
    print("=" * 70)
    
    results = []
    for chart in charts:
        try:
            success = await scrape_chart(chart["url"], chart["output"], name=chart["name"])
            
            results.append({
                "name": chart["name"],
                "output": chart["output"],
                "success": success
            })
            
        except KeyboardInterrupt:
            print(f"\n 사용자에 의해 중단됨")
            break
        except Exception as e:
            print(f"\n {chart['name']} 생성 실패: {e}")
            results.append({
                "name": chart["name"],
                "output": chart["output"],
                "success": False
            })
            continue
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("생성 결과")
    print("=" * 70)
    
    for result in results:
        status = " 성공" if result["success"] else " 실패"
        print(f"{status} - {result['name']}: {result['output']}")
    
    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count
    
    print("\n" + "=" * 70)
    print(f"완료: {success_count}개 성공, {fail_count}개 실패")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
