import os
import time
import sys

from core.splitter import split_video
from core.transcriber import transcribe_files
from core.srt import save_srt


# 실행 위치 기준 경로 (개발 + exe 대응)
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.getcwd()


def prepare_video(video_path, segment_time=300):
    base_path = get_base_path()

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    folder_name = f"{video_name}_{int(time.time())}"

    base_dir = os.path.join(base_path, "data", "outputs", folder_name)
    chunk_dir = os.path.join(base_dir, "chunks")
    srt_dir = os.path.join(base_dir, "srt")

    # 폴더 무조건 생성
    os.makedirs(chunk_dir, exist_ok=True)
    os.makedirs(srt_dir, exist_ok=True)

    print(f"폴더 생성: {base_dir}")
    print("분할 시작")

    split_video(video_path, chunk_dir, segment_time)

    # chunk 파일 안전하게 읽기
    chunk_files = [
        os.path.join(chunk_dir, f)
        for f in sorted(os.listdir(chunk_dir))
        if f.endswith(".mp3")
    ]

    return {
        "base_dir": base_dir,
        "chunk_dir": chunk_dir,
        "srt_dir": srt_dir,
        "chunk_files": chunk_files
    }


def transcribe_selected(base_dir, srt_dir, selected_chunk_files, output_name="selected"):
    print("Whisper 시작")

    results = transcribe_files(selected_chunk_files)

    full_text = ""

    for item in results:
        file_name = item.get("file", "unknown")

        result_data = item.get("result", {})
        text = result_data.get("text", "[텍스트 없음]")

        full_text += f"\n\n===== {file_name} =====\n"
        full_text += text

    # 경로 안전 보장
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(srt_dir, exist_ok=True)

    txt_path = os.path.join(base_dir, f"{output_name}.txt")
    srt_path = os.path.join(srt_dir, f"{output_name}.srt")

    # None 방지 체크
    if not txt_path or not srt_path:
        raise ValueError("파일 경로 생성 실패")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    save_srt(results, srt_path)

    print("완료")
    print(f"TXT: {txt_path}")
    print(f"SRT: {srt_path}")

    return txt_path, srt_path