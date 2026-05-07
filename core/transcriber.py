import os
import sys
import whisper

_model = None


# 실행 위치 기준 경로
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.getcwd()


# 모델 가져오기
def get_model():
    global _model

    if _model is None:
        model_path = os.path.join(get_base_path(), "models", "medium.pt")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"모델 파일 없음: {model_path}")

        print("Whisper 모델 로딩 중...")
        _model = whisper.load_model(model_path)
        print("모델 로딩 완료")

    return _model


def transcribe_files(file_paths):
    results = []

    # 모델 로드
    model = get_model()

    for i, file_path in enumerate(file_paths, 1):
        file_name = os.path.basename(file_path)
        print(f"[{i}/{len(file_paths)}] 처리중: {file_name}")

        try:
            result = model.transcribe(file_path, language="ko")

            # preview 저장
            preview_path = file_path.replace(".mp3", "_preview.txt")

            with open(preview_path, "w", encoding="utf-8") as pf:
                pf.write(result["text"])

            if "segments" not in result:
                result["segments"] = []
            

            results.append({
                "file": file_name,
                "path": file_path,
                "result": result if result else {
                    "text": "[EMPTY]",
                    "segments": []
                }
            })

        except Exception as e:
            print(f"❌ 실패: {file_name} → {e}")

            results.append({
                "file": file_name,
                "path": file_path,
                "result": {
                    "text": f"[ERROR]: {str(e)}",
                    "segments": []
                }
            })

    return results