import os
import subprocess
import sys


# ffmpeg 경로 자동 찾기 (개발 + exe 둘 다 대응)
def get_ffmpeg_path():

    # exe 실행 위치 기준
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)

    # 개발 환경
    else:
        base_path = os.getcwd()

    ffmpeg_path = os.path.join(base_path, "ffmpeg", "ffmpeg.exe")

    if not os.path.exists(ffmpeg_path):
        raise FileNotFoundError(f"ffmpeg.exe 못찾음: {ffmpeg_path}")

    return ffmpeg_path


def split_video(video_path, output_dir, segment_time=300, noise_reduce=True):
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    os.makedirs(output_dir, exist_ok=True)

    output_pattern = os.path.join(output_dir, f"{video_name}_chunk_%03d.mp3")

    ffmpeg_path = get_ffmpeg_path()

    # ffmpeg 존재 체크
    if not os.path.exists(ffmpeg_path):
        raise FileNotFoundError(f"ffmpeg.exe 못찾음: {ffmpeg_path}")

    if noise_reduce:
        audio_filter = "afftdn,highpass=f=200,lowpass=f=3000"

        command = [
            ffmpeg_path,
            "-i", video_path,
            "-vn",
            "-af", audio_filter,
            "-f", "segment",
            "-segment_time", str(segment_time),
            output_pattern
        ]
    else:
        command = [
            ffmpeg_path,
            "-i", video_path,
            "-vn",
            "-f", "segment",
            "-segment_time", str(segment_time),
            output_pattern
        ]

    # 실행
    subprocess.run(command, check=True)



