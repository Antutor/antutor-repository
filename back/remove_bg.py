import os
import subprocess
import sys

def install_and_run():
    print("🚀 배경 제거 라이브러리(rembg)를 설치하는 중입니다... (1~2분 정도 소요될 수 있습니다)")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rembg", "Pillow"])
    except Exception as e:
        print("라이브러리 설치에 실패했습니다. pip install rembg 를 직접 실행해주세요.")
        return
        
    print("✅ 설치 완료! 이미지 배경 제거를 시작합니다.")
    from rembg import remove
    from PIL import Image
    import io
    
    # 이미지 폴더 절대 경로 설정
    img_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "front", "public", "images"))
    
    images = [
        "academic_ant_avatar.png",
        "market_ant_avatar.png",
        "macro_ant_avatar.png"
    ]
    
    for img_name in images:
        img_path = os.path.join(img_dir, img_name)
        if not os.path.exists(img_path):
            print(f"❌ 파일을 찾을 수 없습니다: {img_path}")
            continue
            
        print(f"✨ 작업 중: {img_name}...")
        try:
            with open(img_path, "rb") as i:
                input_data = i.read()
                
            # alpha_matting 옵션이 오히려 가짜 체크무늬 배경에서 노이즈를 유발하므로 기본 설정으로 되돌립니다.
            output_data = remove(input_data)
            
            with open(img_path, "wb") as o:
                o.write(output_data)
                
            print(f"🎉 성공! {img_name}의 배경이 투명하게 제거되었습니다.")
        except Exception as e:
            print(f"❌ {img_name} 작업 실패: {e}")
            
    print("모든 작업이 완료되었습니다! 브라우저를 새로고침해서 예쁜 개미들을 확인해보세요!")

if __name__ == "__main__":
    install_and_run()
