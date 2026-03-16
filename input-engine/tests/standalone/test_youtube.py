"""
Standalone validation: youtube-transcript-api + yt-dlp for YouTube extraction.
Run: uv run --with "youtube-transcript-api>=1.0.0" --with "yt-dlp>=2024.0.0" python input-engine/tests/standalone/test_youtube.py
No FastAPI dependency required.
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

# v1.0.0+ uses instance methods
ytt_api = YouTubeTranscriptApi()


@dataclass
class TestResult:
    video_id: str
    category: str
    description: str
    # Transcript
    transcript_success: bool = False
    transcript_type: str = "none"  # manual, auto-generated, none
    transcript_length: int = 0
    transcript_preview: str = ""
    transcript_error: str | None = None
    # Metadata (yt-dlp)
    metadata_success: bool = False
    title: str | None = None
    channel: str | None = None
    duration_seconds: int | None = None
    view_count: int | None = None
    has_chapters: bool = False
    chapter_count: int = 0
    description_length: int = 0
    thumbnail_url: str | None = None
    metadata_error: str | None = None
    # Timing
    transcript_time_ms: int = 0
    metadata_time_ms: int = 0


# Stable, well-known YouTube videos for testing
TEST_VIDEOS = [
    {
        "video_id": "dQw4w9WgXcQ",
        "category": "Standard video (manual captions)",
        "description": "Rick Astley — Never Gonna Give You Up, manually captioned",
    },
    {
        "video_id": "jNQXAC9IVRw",
        "category": "Auto-generated captions",
        "description": "Me at the zoo — first YouTube video, likely auto-captions only",
    },
    {
        "video_id": "ZZ5LpwO-An4",
        "category": "Long video",
        "description": "HEYYEYAAEYAAAEYAEYAA — tests longer content handling",
    },
    {
        "video_id": "rfscVS0vtbw",
        "category": "Tutorial with chapters",
        "description": "freeCodeCamp Python tutorial — long, has chapters",
    },
    {
        "video_id": "9bZkp7q19f0",
        "category": "Non-English with auto-captions",
        "description": "PSY - Gangnam Style — Korean, auto-captions in multiple languages",
    },
    {
        "video_id": "INVALID_VIDEO_ID_12345",
        "category": "Invalid video ID",
        "description": "Non-existent video — should fail gracefully",
    },
]


def test_transcript(video_id: str) -> dict:
    """Test transcript extraction with youtube-transcript-api."""
    result = {
        "success": False,
        "type": "none",
        "length": 0,
        "preview": "",
        "error": None,
        "time_ms": 0,
    }

    start = time.time()
    try:
        # v1.0.0+: instance method
        transcript_list = ytt_api.list(video_id)

        # Try manual first, then auto-generated
        transcript = None
        caption_type = "none"
        try:
            transcript = transcript_list.find_manually_created_transcript(["en"])
            caption_type = "manual"
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
                caption_type = "auto-generated"
            except Exception:
                # Try any available transcript
                for t in transcript_list:
                    transcript = t
                    caption_type = f"{'manual' if not t.is_generated else 'auto-generated'} ({t.language_code})"
                    break

        if transcript:
            fetched = transcript.fetch()
            full_text = " ".join(snippet.text for snippet in fetched)
            result["success"] = True
            result["type"] = caption_type
            result["length"] = len(full_text)
            result["preview"] = full_text[:300]
        else:
            result["error"] = "No transcripts found in any language"

    except TranscriptsDisabled:
        result["error"] = "Transcripts are disabled for this video"
    except NoTranscriptFound:
        result["error"] = "No transcript found"
    except VideoUnavailable:
        result["error"] = "Video is unavailable"
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
    finally:
        result["time_ms"] = int((time.time() - start) * 1000)

    return result


def test_metadata(video_id: str) -> dict:
    """Test metadata extraction with yt-dlp."""
    result = {
        "success": False,
        "title": None,
        "channel": None,
        "duration_seconds": None,
        "view_count": None,
        "has_chapters": False,
        "chapter_count": 0,
        "description_length": 0,
        "thumbnail_url": None,
        "error": None,
        "time_ms": 0,
    }

    start = time.time()
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        proc = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", "--no-warnings", url],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if proc.returncode != 0:
            result["error"] = f"yt-dlp failed: {proc.stderr.strip()[:200]}"
            return result

        data = json.loads(proc.stdout)
        result["success"] = True
        result["title"] = data.get("title")
        result["channel"] = data.get("channel") or data.get("uploader")
        result["duration_seconds"] = data.get("duration")
        result["view_count"] = data.get("view_count")
        result["description_length"] = len(data.get("description", ""))
        result["thumbnail_url"] = data.get("thumbnail")

        chapters = data.get("chapters") or []
        result["has_chapters"] = len(chapters) > 0
        result["chapter_count"] = len(chapters)

    except subprocess.TimeoutExpired:
        result["error"] = "yt-dlp timed out after 30s"
    except json.JSONDecodeError as e:
        result["error"] = f"Failed to parse yt-dlp JSON: {e}"
    except FileNotFoundError:
        result["error"] = "yt-dlp not found — install with: uv tool install yt-dlp"
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
    finally:
        result["time_ms"] = int((time.time() - start) * 1000)

    return result


def print_result(video: dict, transcript: dict, metadata: dict, index: int):
    """Print test results for a single video."""
    t_status = "PASS" if transcript["success"] else "FAIL"
    m_status = "PASS" if metadata["success"] else "FAIL"

    print(f"\n{'='*80}")
    print(f"Test {index + 1}: {video['category']}")
    print(f"Video ID: {video['video_id']}")
    print(f"Description: {video['description']}")

    print(f"\n  Transcript [{t_status}] ({transcript['time_ms']}ms)")
    if transcript["success"]:
        print(f"    Type: {transcript['type']}")
        print(f"    Length: {transcript['length']:,} chars")
        print(f"    Preview: {transcript['preview'][:150]}...")
    else:
        print(f"    Error: {transcript['error']}")

    print(f"\n  Metadata [{m_status}] ({metadata['time_ms']}ms)")
    if metadata["success"]:
        print(f"    Title: {metadata['title']}")
        print(f"    Channel: {metadata['channel']}")
        duration = metadata["duration_seconds"]
        if duration:
            mins, secs = divmod(duration, 60)
            print(f"    Duration: {mins}:{secs:02d}")
        print(f"    Views: {metadata['view_count']:,}" if metadata["view_count"] else "    Views: N/A")
        print(f"    Chapters: {metadata['chapter_count']}" if metadata["has_chapters"] else "    Chapters: None")
        print(f"    Description: {metadata['description_length']:,} chars")
    else:
        print(f"    Error: {metadata['error']}")


def main():
    print("=" * 80)
    print("YOUTUBE EXTRACTION STANDALONE VALIDATION")
    print(f"Testing {len(TEST_VIDEOS)} videos")
    print("=" * 80)

    all_results = []
    for i, video in enumerate(TEST_VIDEOS):
        print(f"\n>>> Testing {i + 1}/{len(TEST_VIDEOS)}: {video['description']}")

        transcript = test_transcript(video["video_id"])
        metadata = test_metadata(video["video_id"])
        all_results.append({"video": video, "transcript": transcript, "metadata": metadata})
        print_result(video, transcript, metadata, i)
        time.sleep(1)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    t_passed = sum(1 for r in all_results if r["transcript"]["success"])
    m_passed = sum(1 for r in all_results if r["metadata"]["success"])
    print(f"Transcript extraction: {t_passed}/{len(all_results)} passed")
    print(f"Metadata extraction:   {m_passed}/{len(all_results)} passed")
    print()

    print(f"{'Category':<35} {'Transcript':<12} {'Type':<20} {'Metadata':<10} {'Chapters'}")
    print("-" * 95)
    for r in all_results:
        cat = r["video"]["category"][:34]
        t_ok = "PASS" if r["transcript"]["success"] else "FAIL"
        t_type = r["transcript"]["type"] if r["transcript"]["success"] else "-"
        m_ok = "PASS" if r["metadata"]["success"] else "FAIL"
        chaps = str(r["metadata"]["chapter_count"]) if r["metadata"]["has_chapters"] else "-"
        print(f"{cat:<35} {t_ok:<12} {t_type:<20} {m_ok:<10} {chaps}")

    # JSON output
    print("\n\n--- JSON OUTPUT ---")
    print(json.dumps(all_results, indent=2, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
