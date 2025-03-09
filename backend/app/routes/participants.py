from fastapi import APIRouter
import pandas as pd

router = APIRouter()

@router.get("/api/participants")
async def get_participants_info():
    df = pd.read_csv("../data/eeg_samples/participants.tsv", sep='\t')
    return {
        "total_count": len(df),
        "group_stats": df.groupby('Group').agg({
            'Age': ['mean', 'min', 'max'],
            'Gender': 'count'
        }).to_dict()
    } 