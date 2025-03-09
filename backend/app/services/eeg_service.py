from pathlib import Path
import mne
import pandas as pd

class EEGService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
    
    def get_dataset_path(self, dataset_id: str) -> Path:
        return self.data_dir / f"sub-{dataset_id}/eeg"
    
    def read_eeg_data(self, dataset_id: str):
        eeg_dir = self.get_dataset_path(dataset_id)
        set_files = list(eeg_dir.glob("*.set"))
        if not set_files:
            raise FileNotFoundError(f"No .set files found for dataset {dataset_id}")
        return mne.io.read_raw_eeglab(str(set_files[0]), montage_units='cm') 