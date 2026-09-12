# src/screener/engine.py

import yaml
import numpy as np
import pandas as pd

class ScreenerEngine:
    def __init__(self, config_path: str = "config/screener_config.yaml"):
        """Load configuration rules from YAML."""
        with open(config_path, "r") as file:
            self.config = yaml.safe_load(file)

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess metrics like ICR 'Debt Free' text to infinity/float."""
        df = df.copy()
        if 'icr' in df.columns:
            df['icr'] = df['icr'].replace(
                ['Debt Free', 'DEBT FREE', 'debt free', 'N/A', None], np.inf
            )
            df['icr'] = pd.to_numeric(df['icr'], errors='coerce').fillna(np.inf)
        return df

    def winsorize_and_scale(self, series: pd.Series, lower_p: float = 0.10, upper_p: float = 0.90, invert: bool = False) -> pd.Series:
        """Applies P10/P90 winsorisation and scales values strictly to a 0-100 range."""
        # Force conversion to numeric float series first
        clean_series = pd.to_numeric(
            series.replace(['Debt Free', 'DEBT FREE', 'debt free', 'N/A', None, np.inf, -np.inf], np.nan),
            errors='coerce'
        )
        
        p10 = clean_series.quantile(lower_p)
        p90 = clean_series.quantile(upper_p)
        
        if pd.isna(p10) or pd.isna(p90) or p10 == p90:
            return pd.Series(50.0, index=series.index)
            
        clipped = clean_series.clip(lower=p10, upper=p90)
        
        if invert:
            scaled = 100.0 * (p90 - clipped) / (p90 - p10)
        else:
            scaled = 100.0 * (clipped - p10) / (p90 - p10)
            
        return scaled.fillna(50.0)

    def calculate_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.preprocess_data(df)
        sector_col = 'broad_sector' if 'broad_sector' in df.columns else 'sector'
        
        df['s_roe'] = 0.0
        df['s_roce'] = 0.0
        df['s_npm'] = 0.0
        df['s_fcf_cagr'] = 0.0
        df['s_cfo_pat'] = 0.0
        df['s_fcf_flag'] = np.where(pd.to_numeric(df.get('fcf', 0), errors='coerce').fillna(0) > 0, 100.0, 0.0)
        df['s_rev_cagr'] = 0.0
        df['s_pat_cagr'] = 0.0
        df['s_de'] = 0.0
        df['s_icr'] = 0.0

        for sector_name, group in df.groupby(sector_col):
            idx = group.index
            if 'roe' in df.columns:
                df.loc[idx, 's_roe'] = self.winsorize_and_scale(group['roe'])
            if 'roce' in df.columns:
                df.loc[idx, 's_roce'] = self.winsorize_and_scale(group['roce'])
            if 'npm' in df.columns:
                df.loc[idx, 's_npm'] = self.winsorize_and_scale(group['npm'])
            if 'fcf_cagr_5yr' in df.columns:
                df.loc[idx, 's_fcf_cagr'] = self.winsorize_and_scale(group['fcf_cagr_5yr'])
            if 'cfo_pat_ratio' in df.columns:
                df.loc[idx, 's_cfo_pat'] = self.winsorize_and_scale(group['cfo_pat_ratio'])
            if 'rev_cagr_5yr' in df.columns:
                df.loc[idx, 's_rev_cagr'] = self.winsorize_and_scale(group['rev_cagr_5yr'])
            if 'pat_cagr_5yr' in df.columns:
                df.loc[idx, 's_pat_cagr'] = self.winsorize_and_scale(group['pat_cagr_5yr'])
            if 'de_ratio' in df.columns:
                df.loc[idx, 's_de'] = self.winsorize_and_scale(group['de_ratio'], invert=True)
            if 'icr' in df.columns:
                df.loc[idx, 's_icr'] = self.winsorize_and_scale(group['icr'])

        df['profitability_score'] = (0.15 * df['s_roe']) + (0.10 * df['s_roce']) + (0.10 * df['s_npm'])
        df['cash_quality_score']  = (0.15 * df['s_fcf_cagr']) + (0.10 * df['s_cfo_pat']) + (0.05 * df['s_fcf_flag'])
        df['growth_score']        = (0.10 * df['s_rev_cagr']) + (0.10 * df['s_pat_cagr'])
        df['leverage_score']      = (0.10 * df['s_de']) + (0.05 * df['s_icr'])

        df['composite_quality_score'] = (
            df['profitability_score'] + df['cash_quality_score'] + 
            df['growth_score'] + df['leverage_score']
        ).round(2)

        temp_cols = ['s_roe', 's_roce', 's_npm', 's_fcf_cagr', 's_cfo_pat', 
                     's_fcf_flag', 's_rev_cagr', 's_pat_cagr', 's_de', 's_icr',
                     'profitability_score', 'cash_quality_score', 'growth_score', 'leverage_score']
        df.drop(columns=temp_cols, inplace=True, errors='ignore')
        return df

    def apply_filters(self, df: pd.DataFrame, criteria: dict) -> pd.DataFrame:
        df = self.preprocess_data(df)
        df = self.calculate_composite_score(df)
        
        skip_de_sectors = self.config.get('sector_exceptions', {}).get('de_ratio_skip_sectors', [])
        mask = pd.Series(True, index=df.index)
        
        for key, threshold in criteria.items():
            if threshold is None:
                continue
            if key == 'de_declining_yoy' and threshold is True:
                if 'de_ratio_yoy_change' in df.columns:
                    mask &= (df['de_ratio_yoy_change'] < 0)
                continue

            if key.endswith('_min'):
                metric = key[:-4]
                if metric in df.columns:
                    val_col = pd.to_numeric(df[metric].replace('Debt Free', np.inf), errors='coerce')
                    mask &= (val_col >= threshold)
            elif key.endswith('_max'):
                metric = key[:-4]
                if metric in df.columns:
                    val_col = pd.to_numeric(df[metric], errors='coerce')
                    if metric == 'de_ratio':
                        sector_col = 'broad_sector' if 'broad_sector' in df.columns else 'sector'
                        if sector_col in df.columns:
                            is_financial = df[sector_col].isin(skip_de_sectors)
                            passes_de = (val_col <= threshold) | is_financial
                            mask &= passes_de
                        else:
                            mask &= (val_col <= threshold)
                    else:
                        mask &= (val_col <= threshold)

        filtered_df = df[mask].copy()
        return filtered_df.sort_values(by='composite_quality_score', ascending=False)

    def run_preset(self, df: pd.DataFrame, preset_key: str) -> pd.DataFrame:
        """Run a preset defined in config/screener_config.yaml."""
        presets = self.config.get('presets', {})
        if preset_key not in presets:
            raise ValueError(f"Preset '{preset_key}' not found in configuration.")
        return self.apply_filters(df, presets[preset_key]['criteria'])