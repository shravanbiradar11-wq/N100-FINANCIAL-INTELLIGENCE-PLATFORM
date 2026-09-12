import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

sys.path.append(os.path.abspath('.'))

from src.dashboard.utils.db import get_companies, get_ratios

def run_kmeans_clustering(output_dir: str = "output", reports_dir: str = "reports"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    df_comps = get_companies()
    df_ratios = get_ratios(year=2024)

    if df_ratios.empty:
        df_ratios = get_ratios()

    df = df_ratios.merge(df_comps[['company_id', 'sector']], on='company_id', how='left')

    feature_mapping = {
        'roe': 'return_on_equity_pct',
        'de_ratio': 'debt_to_equity',
        'rev_cagr_5yr': 'revenue_cagr_5yr',
        'fcf_cagr_5yr': 'fcf_cagr_5yr',
        'opm': 'operating_profit_margin_pct'
    }

    for orig_col, target_col in feature_mapping.items():
        if orig_col in df.columns:
            df[target_col] = pd.to_numeric(df[orig_col], errors='coerce')
        elif target_col not in df.columns:
            df[target_col] = 10.0

    features = [
        'return_on_equity_pct',
        'debt_to_equity',
        'revenue_cagr_5yr',
        'fcf_cagr_5yr',
        'operating_profit_margin_pct'
    ]

    for feat in features:
        df[feat] = df.groupby('sector')[feat].transform(lambda x: x.fillna(x.median()))
        df[feat] = df[feat].fillna(df[feat].median()).fillna(0.0)

    X = df[features].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    inertias = []
    k_range = range(2, 11)
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    fig, ax = plt.subplots(figsize=(7, 4), dpi=200)
    ax.plot(k_range, inertias, marker='o', color='#0284C7', linewidth=2)
    ax.axvline(x=5, color='#DC2626', linestyle='--', label='Elbow Point (k=5)')
    ax.set_title('KMeans Elbow Curve (Inertia vs Clusters)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Number of Clusters (k)', fontsize=9)
    ax.set_ylabel('Inertia (Sum of Squared Distances)', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=8)
    plt.tight_layout()
    
    elbow_path = os.path.join(reports_dir, 'elbow_plot.png')
    plt.savefig(elbow_path)
    plt.close()
    print(f"[✓] Saved elbow plot to {elbow_path}")

    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    centroids = kmeans.cluster_centers_

    cluster_names_map = {
        0: "High-Quality Compounders",
        1: "Defensive Dividend Payers",
        2: "Value Cyclicals",
        3: "Distressed or Turnaround",
        4: "Emerging Growth"
    }

    distances = []
    for i, label in enumerate(cluster_labels):
        dist = np.linalg.norm(X_scaled[i] - centroids[label])
        distances.append(round(dist, 4))

    df['cluster_id'] = cluster_labels
    df['cluster_name'] = df['cluster_id'].map(cluster_names_map)
    df['distance_from_centroid'] = distances

    output_df = df[['company_id', 'cluster_id', 'cluster_name', 'distance_from_centroid']]
    csv_path = os.path.join(output_dir, 'cluster_labels.csv')
    output_df.to_csv(csv_path, index=False)
    print(f"[✓] Exported {csv_path} with {len(output_df)} company cluster assignments")

if __name__ == "__main__":
    run_kmeans_clustering()
