from fastapi import APIRouter
import mne

router = APIRouter()  # 创建路由器

@router.get("/api/datasets/{dataset_id}/plot")  # 使用router而不是app
async def get_eeg_plot(dataset_id: str, start_time: float = 0, duration: float = 10):
    raw = mne.io.read_raw_edf(f"../data/eeg_samples/sub-{dataset_id}/eeg/sub-{dataset_id}_task-flankersFAR_eeg.edf")
    data, times = raw[:, int(start_time*raw.info['sfreq']):int((start_time+duration)*raw.info['sfreq'])]
    return {
        "data": data.tolist(),
        "times": times.tolist(),
        "channels": raw.ch_names
    } 