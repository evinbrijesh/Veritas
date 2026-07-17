"""
Agent 2/9 — Metadata extraction.
Pulls EXIF (images), container metadata (video, via pymediainfo/ffmpeg),
and file-system timestamps. This feeds both the timeline agent and the
correlation agent (e.g. GPS coordinates -> co-location correlation).
"""
import exifread
from app.agents.state import PipelineState


def extract_image_metadata(file_path: str) -> dict:
    with open(file_path, "rb") as f:
        tags = exifread.process_file(f, details=False)

    return {
        "gps": {
            "lat": str(tags.get("GPS GPSLatitude", "")),
            "lon": str(tags.get("GPS GPSLongitude", "")),
        },
        "datetime_original": str(tags.get("EXIF DateTimeOriginal", "")),
        "camera_model": str(tags.get("Image Model", "")),
        "software": str(tags.get("Image Software", "")),  # useful: editing/generation tool traces
    }


def metadata_agent(state: PipelineState) -> PipelineState:
    results = {}
    for path, ingestion_info in state["ingestion_results"].items():
        if ingestion_info["file_type"] in [".jpg", ".jpeg", ".png", ".tiff"]:
            results[path] = extract_image_metadata(path)
        else:
            # TODO: video branch via pymediainfo for .mp4/.mov/.avi
            results[path] = {"note": "non-image metadata extraction not yet implemented in scaffold"}
    state["metadata_results"] = results
    return state
