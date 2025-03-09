from fastapi import APIRouter, HTTPException
from ..services.eeg_service import EEGService
from pathlib import Path

router = APIRouter(prefix="/api/datasets")
eeg_service = EEGService(Path("../data/eeg_samples"))

@router.get("/{dataset_id}/basic")
async def get_basic_info(dataset_id: str):
    try:
        raw = eeg_service.read_eeg_data(dataset_id)
        return {
            "sampling_rate": raw.info['sfreq'],
            "duration": raw.times[-1],
            "channels": raw.ch_names,
            "n_channels": len(raw.ch_names)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 