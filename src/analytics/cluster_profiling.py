import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.abspath('.'))

from src.dashboard.utils.db import get_companies, get_ratios

def run_cluster_profiling(output_dir: str = "output", reports_dir: str = "reports"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # 1. Load Ratios and Companies
    df_comps = get_companies()
    df_ratios = get_ratios(year=2024)
    if df_ratios.empty:
        df_ratios = get_ratios()

    # 2. Load Cluster Assignments
    cluster_csv = os.path.join(output_dir, "cluster_labels.csv")
    if not os.path.exists(cluster_csv):
        print("[!] cluster_labels.csv not found. Running Day 36 first...")
        from src.analytics.clustering import run_kmeans_clustering
        run_kmeans_clustering(output_dir, reports_dir)
    
    df_clusters = pd.read_csv(cluster_csv)
    df = df_ratios.merge(df_clusters, on="company_id", how="inner")
    df = df.merge(df_comps[['company_id', 'sector']], on="company_id", how="left")

    # 3. Correlation Heatmap (10 KPIs)
    kpi_cols = ['roe', 'roce', 'de_ratio', 'pe_ratio', 'pb_ratio', 'opm', 'rev_cagr_5yr', 'pat_cagr_5yr', 'fcf', 'dividend_yield']
    valid_kpis = [c for c in kpi_cols if c in df.columns]

    corr_df = df[valid_kpis].apply(pd.to_numeric, errors='coerce').corr()

    fig, ax = plt.subplots(figsize=(8, 6), dpi=200)
    sns.heatmap(corr_df, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, ax=ax, linewidths=0.5)
    ax.set_title("Nifty 100 — 10 KPI Correlation Heatmap", fontsize=11, fontweight="bold")
    plt.tight_layout()
    heatmap_path = os.path.join(reports_dir, "correlation_heatmap.png")
    plt.savefig(heatmap_path)
    plt.close()
    print(f"[✓] Saved correlation heatmap to {heatmap_path}")

    # 4. Outlier Detection (Z-score > 3 per sector)
    outliers = []
    for sector_name, group in df.groupby("sector"):
        for metric in valid_kpis:
            vals = pd.to_numeric(group[metric], errors='coerce').dropna()
            if len(vals) > 3 and vals.std() > 0:
                z_scores = (vals - vals.mean()) / vals.std()
                for idx, z in z_scores.items():
                    if abs(z) > 3.0:
                        cid = group.loc[idx, 'company_id']
                        outliers.append({
                            "company_id": cid,
                            "sector": sector_name,
                            "metric": metric,
                            "value": group.loc[idx, metric],
                            "z_score": round(z, 2)
                        })

    df_outliers = pd.DataFrame(outliers)
    outlier_path = os.path.join(output_dir, "outlier_report.csv")
    df_outliers.to_csv(outlier_path, index=False)
    print(f"[✓] Exported {outlier_path} ({len(df_outliers)} outliers flagged)")

    # 5. Portfolio Summary Stats (P10 to P90)
    stats_list = []
    percentiles = [0.10, 0.25, 0.50, 0.75, 0.90]
    p_names = ['P10', 'P25', 'P50', 'P75', 'P90']

    for metric in valid_kpis:
        vals = pd.to_numeric(df[metric], errors='coerce').dropna()
        if not vals.empty:
            p_vals = np.quantile(vals, percentiles)
            stat_row = {
                "metric": metric,
                "mean": round(vals.mean(), 2),
                "std": round(vals.std(), 2)
            }
            for name, val in zip(p_names, p_vals):
                stat_row[name] = round(val, 2)
            stats_list.append(stat_row)

    df_stats = pd.DataFrame(stats_list)
    stats_path = os.path.join(output_dir, "portfolio_stats.csv")
    df_stats.to_csv(stats_path, index=False)
    print(f"[✓] Exported {stats_path} (Percentile portfolio statistics)")

if __name__ == "__main__":
    run_cluster_profiling()
