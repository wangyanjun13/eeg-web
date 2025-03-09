from pathlib import Path
import mne

class EEGService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        if not self.data_dir.exists():
            raise ValueError(f"数据目录不存在: {self.data_dir}")

    def get_dataset_path(self, dataset_id: str) -> Path:
        return self.data_dir / f"sub-{dataset_id}/eeg"
    
    def read_eeg_data(self, dataset_id: str):
        # 构建数据文件路径
        subject_dir = f"sub-{dataset_id}"
        eeg_dir = self.data_dir / subject_dir / 'eeg'
        
        # 查找.set文件
        set_files = list(eeg_dir.glob('*.set'))
        if not set_files:
            raise FileNotFoundError(f"未找到EEG数据文件: {eeg_dir}")
        
        # 读取第一个.set文件
        raw = mne.io.read_raw_eeglab(
            str(set_files[0]),
            montage_units='mm',  # 指定单位
            preload=True
        )
        return raw 