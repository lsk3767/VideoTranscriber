def format_time(seconds):
    try:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)

        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    except:
        return "00:00:00,000"


def save_srt(results, output_path):

    with open(output_path, "w", encoding="utf-8") as f:

        # chunk별 반복
        for item in results:

            file_name = item.get("file", "unknown")

            result = item.get("result", {})

            segments = result.get("segments", [])

            # segments 없으면 skip
            if not segments:
                continue

            # =========================
            # chunk 헤더
            # =========================
            chunk_name = file_name.replace(".mp3", "")

            f.write("\n")
            f.write("=" * 50 + "\n")
            f.write(f"[ {chunk_name} ]\n")
            f.write("=" * 50 + "\n\n")

            index = 1

            # =========================
            # 자막 작성
            # =========================
            for segment in segments:

                start_sec = segment.get("start", 0)
                end_sec = segment.get("end", 0)

                text = segment.get("text", "").strip()

                # 빈 텍스트 skip
                if not text:
                    continue

                start = format_time(start_sec)
                end = format_time(end_sec)

                f.write(f"{index}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")

                index += 1