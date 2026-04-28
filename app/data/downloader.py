"""
NHANES Data Downloader - Download and manage NHANES data from CDC

Supports:
- XPT (SAS Transport) file download from CDC
- Multi-cycle data merging
- Automatic survey weight handling
- Local caching to avoid re-downloads
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
import httpx

from ..config import NHANES_BASE_URL, NHANES_CACHE, SURVEY_PARAMS

logger = logging.getLogger(__name__)

# NHANES variable code -> file prefix mapping (most common)
NHANES_FILE_MAP = {
    # Demographics
    "RIDAGEYR": "DEMO", "RIAGENDR": "DEMO", "RIDRETH1": "DEMO", "RIDRETH3": "DEMO",
    "DMDEDUC2": "DEMO", "INDFMPIR": "DEMO", "DMDMARTL": "DEMO",
    "WTMEC2YR": "DEMO", "WTINT2YR": "DEMO", "SDMVPSU": "DEMO", "SDMVSTRA": "DEMO",
    "RIDEXPRG": "DEMO", "DMDBORN4": "DEMO",
    # Body Measures
    "BMXBMI": "BMX", "BMXWT": "BMX", "BMXHT": "BMX", "BMXWAIST": "BMX",
    "BMXHEAD": "BMX", "BMXARML": "BMX", "BMXLEG": "BMX",
    # Blood Pressure
    "BPXSY1": "BPX", "BPXSY2": "BPX", "BPXSY3": "BPX", "BPXSY4": "BPX",
    "BPXDI1": "BPX", "BPXDI2": "BPX", "BPXDI3": "BPX", "BPXDI4": "BPX",
    "BPQ050A": "BPQ", "BPQ020": "BPQ",
    # Lab - Cholesterol
    "LBXTC": "TCHOL", "LBDTCSI": "TCHOL",
    "LBDHDD": "HDL", "LBXHDD": "HDL",
    "LBXTR": "TRIGLY", "LBDTRSI": "TRIGLY", "LBDLDL": "TRIGLY",
    # Lab - Glucose / Diabetes
    "LBXGLU": "GLU", "LBDGLUSI": "GLU",
    "LBXIN": "INS", "LBDINSI": "INS",
    "LBXGH": "HBA1C",
    "DIQ010": "DIQ", "DIQ050": "DIQ",
    # Medical Conditions
    "MCQ160C": "MCQ", "MCQ160D": "MCQ", "MCQ160E": "MCQ", "MCQ160F": "MCQ",
    "MCQ220": "MCQ", "MCQ300A": "MCQ", "MCQ300B": "MCQ",
    # Cardiovascular
    "CDQ001": "CDQ", "CDQ002": "CDQ", "CDQ003": "CDQ", "CDQ004": "CDQ",
    # Smoking
    "SMQ020": "SMQ", "SMQ040": "SMQ",
    # Alcohol
    "ALQ101": "ALQ", "ALQ111": "ALQ", "ALQ120Q": "ALQ", "ALQ130": "ALQ",
    # Physical Activity
    "PAQ605": "PAQ", "PAQ610": "PAQ", "PAQ620": "PAQ", "PAQ635": "PAQ",
    "PAQ650": "PAQ", "PAQ665": "PAQ",
    # Diet
    "DBQ700": "DBQ", "DBQ197": "DBQ", "DBQ223A": "DBQ",
    # Dietary Recall
    "DR1TKCAL": "DR1TOT", "DR1TPROT": "DR1TOT", "DR1TTFAT": "DR1TOT",
    "DR1TCARB": "DR1TOT", "DR1TFIBE": "DR1TOT", "DR1TSUGR": "DR1TOT",
    "DR1TSODI": "DR1TOT", "DR1TPOTA": "DR1TOT", "DR1TIRON": "DR1TOT",
    "DR1TCAFF": "DR1TOT", "DR1TALCO": "DR1TOT",
    # Health Care
    "HUQ010": "HUQ", "HUQ030": "HUQ", "HUQ050": "HUQ",
    # Kidney
    "KIQ022": "KIQ_U", "KIQ025": "KIQ_U", "KIQ026": "KIQ_U",
    # Hepatitis
    "HEQ010": "HEQ",
    # Sleep
    "SLQ050": "SLQ", "SLQ060": "SLQ", "SLQ080": "SLQ", "SLQ100": "SLQ",
    # Depression
    "DPQ010": "DPQ", "DPQ020": "DPQ", "DPQ030": "DPQ", "DPQ040": "DPQ",
    "DPQ050": "DPQ", "DPQ060": "DPQ", "DPQ070": "DPQ", "DPQ080": "DPQ",
    "DPQ090": "DPQ", "DPQ100": "DPQ",
    # Weight History
    "WHD010": "WHQ", "WHD020": "WHQ", "WHQ030": "WHQ", "WHD050": "WHQ",
    "WHD110": "WHQ", "WHD120": "WHQ", "WHD140": "WHQ", "WHD150": "WHQ",
}

# NHANES data file prefix -> (URL path, year suffix) mapping
# CDC uses different naming conventions across cycles
CYCLE_FILE_MAP = {
    "1999-2000": lambda prefix: f"{prefix}",
    "2001-2002": lambda prefix: f"{prefix}_B",
    "2003-2004": lambda prefix: f"{prefix}_C",
    "2005-2006": lambda prefix: f"{prefix}_D",
    "2007-2008": lambda prefix: f"{prefix}_E",
    "2009-2010": lambda prefix: f"{prefix}_F",
    "2011-2012": lambda prefix: f"{prefix}_G",
    "2013-2014": lambda prefix: f"{prefix}_H",
    "2015-2016": lambda prefix: f"{prefix}_I",
    "2017-2018": lambda prefix: f"{prefix}_J",
}


class NHANESDownloader:
    """Download and manage NHANES data from CDC."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or NHANES_CACHE
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self.cache_dir / "download_manifest.json"
        self._manifest = self._load_manifest()
    
    def _load_manifest(self) -> dict:
        if self._manifest_path.exists():
            return json.loads(self._manifest_path.read_text())
        return {}
    
    def _save_manifest(self):
        self._manifest_path.write_text(json.dumps(self._manifest, indent=2, default=str))
    
    def _cache_key(self, cycle: str, prefix: str) -> str:
        return f"{cycle}_{prefix}"
    
    def _cache_path(self, cycle: str, prefix: str) -> Path:
        key = self._cache_key(cycle, prefix)
        return self.cache_dir / f"{key}.parquet"
    
    def _build_url(self, cycle: str, prefix: str) -> str:
        """Build CDC download URL for a given cycle and data file prefix."""
        # CDC URL pattern: https://wwwn.cdc.gov/Nchs/Nhanes/{cycle}/{FILENAME}.XPT
        # Cycle format in URL: e.g., "1999-2000" -> "1999-2000"
        # File naming varies by cycle
        if cycle == "1999-2000":
            filename = f"{prefix}.XPT"
        else:
            # Extract cycle letter suffix
            cycle_letter = cycle.split("-")[0][-2:]  # e.g., "01" from "2001"
            cycle_map = {
                "2001-2002": "B", "2003-2004": "C", "2005-2006": "D",
                "2007-2008": "E", "2009-2010": "F", "2011-2012": "G",
                "2013-2014": "H", "2015-2016": "I", "2017-2018": "J",
            }
            suffix = cycle_map.get(cycle, "")
            filename = f"{prefix}_{suffix}.XPT"
        
        return f"{NHANES_BASE_URL}/{cycle}/{filename}"
    
    def download_file(self, cycle: str, prefix: str, force: bool = False) -> Optional[pd.DataFrame]:
        """Download a single NHANES XPT file and cache as parquet."""
        cache_file = self._cache_path(cycle, prefix)
        key = self._cache_key(cycle, prefix)
        
        # Check cache
        if cache_file.exists() and not force:
            logger.info(f"Loading from cache: {key}")
            return pd.read_parquet(cache_file)
        
        url = self._build_url(cycle, prefix)
        logger.info(f"Downloading: {url}")
        
        try:
            with httpx.Client(timeout=120, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()
            
            # Parse XPT file
            import io
            df = pd.read_sas(io.BytesIO(resp.content), format="xport")
            
            if df.empty:
                logger.warning(f"Empty dataset: {url}")
                return None
            
            # Add metadata columns
            df["_cycle"] = cycle
            df["_download_time"] = datetime.now().isoformat()
            
            # Cache as parquet
            df.to_parquet(cache_file, index=False)
            self._manifest[key] = {
                "cycle": cycle,
                "prefix": prefix,
                "url": url,
                "rows": len(df),
                "cols": len(df.columns),
                "downloaded_at": datetime.now().isoformat(),
            }
            self._save_manifest()
            
            logger.info(f"Downloaded {len(df)} rows, {len(df.columns)} columns from {key}")
            return df
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error downloading {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None
    
    def get_required_files(self, variables: List[str]) -> Dict[str, List[str]]:
        """Determine which data files are needed for a set of variables."""
        needed = {}
        for var in variables:
            var_upper = var.upper()
            if var_upper in NHANES_FILE_MAP:
                prefix = NHANES_FILE_MAP[var_upper]
                if prefix not in needed:
                    needed[prefix] = []
                needed[prefix].append(var_upper)
        return needed
    
    def download_for_study(
        self,
        variables: List[str],
        cycles: List[str],
        progress_callback=None
    ) -> Dict[str, pd.DataFrame]:
        """Download all data files needed for a study across specified cycles."""
        needed_files = self.get_required_files(variables)
        results = {}
        total = len(needed_files) * len(cycles)
        done = 0
        
        for cycle in cycles:
            for prefix in needed_files:
                done += 1
                if progress_callback:
                    progress_callback(done, total, f"Downloading {prefix} for {cycle}")
                
                df = self.download_file(cycle, prefix)
                if df is not None:
                    key = f"{cycle}_{prefix}"
                    results[key] = df
        
        return results
    
    def merge_cycles(
        self,
        dataframes: Dict[str, pd.DataFrame],
        prefix: str,
        cycles: List[str]
    ) -> pd.DataFrame:
        """Merge the same data file across multiple cycles."""
        frames = []
        for cycle in cycles:
            key = f"{cycle}_{prefix}"
            if key in dataframes:
                df = dataframes[key].copy()
                df["_cycle"] = cycle
                frames.append(df)
        
        if not frames:
            return pd.DataFrame()
        
        # Find common columns (excluding metadata)
        common_cols = set(frames[0].columns)
        for f in frames[1:]:
            common_cols &= set(f.columns)
        
        meta_cols = {"_cycle", "_download_time"}
        common_cols -= meta_cols
        
        merged = pd.concat(
            [f[list(common_cols) | {"_cycle"}] for f in frames],
            ignore_index=True
        )
        
        logger.info(f"Merged {prefix} across {len(frames)} cycles: {len(merged)} total rows")
        return merged
    
    def list_cached(self) -> List[dict]:
        """List all cached NHANES data files."""
        return list(self._manifest.values())
    
    def clear_cache(self):
        """Remove all cached data."""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True)
        self._manifest = {}
        self._save_manifest()
