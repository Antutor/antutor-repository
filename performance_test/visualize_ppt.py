import argparse
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# ---------------------------------------------------------------------------
# 스타일 설정 (PPT 발표용으로 폰트 크기 확대)
# ---------------------------------------------------------------------------
sns.set_theme(style="whitegrid", font_scale=1.4)
plt.rcParams['font.family'] = 'Segoe UI' if os.name == 'nt' else 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

PALETTE = {
    "Sync": "#E74C3C",          # 빨강 — 직렬
    "Async": "#2ECC71",         # 초록 — 병렬
    "Sync (Fixed)": "#F1948A",  # 연빨강
    "Async (Fixed)": "#82E0AA", # 연초록
}

def load_stats(prefix: str):
    path = f"{prefix}_stats.csv"
    if not os.path.exists(path):
        print(f"[ERROR] 파일을 찾을 수 없습니다: {path}")
        sys.exit(1)

    df = pd.read_csv(path)
    df = df[df['Name'].str.startswith('/benchmark')]
    if df.empty:
        print("[ERROR] /benchmark 관련 데이터가 없습니다.")
        sys.exit(1)
    
    # Label 설정
    df['Label'] = df['Name'].replace({
        "/benchmark/sync": "Sync",
        "/benchmark/async": "Async",
        "/benchmark/sync [fixed]": "Sync (Fixed)",
        "/benchmark/async [fixed]": "Async (Fixed)"
    })
    
    # 데이터 가공 (단위 변환 및 추가 계산)
    # ms를 분(Minutes) 단위로 변환
    df['Avg Latency (Min)'] = df['Average Response Time'] / 60000.0 
    # 실패율 계산
    df['Fail Rate (%)'] = (df['Failure Count'] / df['Request Count']) * 100.0
    
    # 정렬 (의도된 순서대로 표시하기 위함)
    order = ["Sync", "Sync (Fixed)", "Async", "Async (Fixed)"]
    df['Label'] = pd.Categorical(df['Label'], categories=order, ordered=True)
    df = df.sort_values('Label')
    
    return df

def visualize_ppt(prefix: str):
    df = load_stats(prefix)

    # PPT 슬라이드에 적합한 가로로 긴 1x3 비율
    fig, axes = plt.subplots(1, 3, figsize=(24, 7))
    plt.subplots_adjust(wspace=0.3)

    # --- 1. 평균 지연 시간 (분 단위) ---
    sns.barplot(x='Label', y='Avg Latency (Min)', data=df, palette=PALETTE, ax=axes[0])
    axes[0].set_title('① Average Latency (Minutes)', fontweight='bold', pad=15)
    axes[0].set_ylabel('Minutes')
    axes[0].set_xlabel('')
    for p in axes[0].patches:
        axes[0].annotate(f"{p.get_height():.1f} min", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='bottom', fontsize=14, fontweight='bold', xytext=(0, 5), textcoords='offset points')

    # --- 2. 실패율 (%) ---
    sns.barplot(x='Label', y='Fail Rate (%)', data=df, palette=PALETTE, ax=axes[1])
    axes[1].set_title('② Failure Rate (%)', fontweight='bold', pad=15)
    axes[1].set_ylabel('%')
    axes[1].set_xlabel('')
    axes[1].set_ylim(0, 100)
    for p in axes[1].patches:
        axes[1].annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='bottom', fontsize=14, fontweight='bold', xytext=(0, 5), textcoords='offset points')

    # --- 3. 총 처리 요청 수 (건) ---
    sns.barplot(x='Label', y='Request Count', data=df, palette=PALETTE, ax=axes[2])
    axes[2].set_title('③ Total Handled Requests', fontweight='bold', pad=15)
    axes[2].set_ylabel('Count')
    axes[2].set_xlabel('')
    for p in axes[2].patches:
        axes[2].annotate(f"{int(p.get_height())} req", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='bottom', fontsize=14, fontweight='bold', xytext=(0, 5), textcoords='offset points')

    # 전체 제목
    plt.suptitle(f"Backend Optimization Result: Sync vs Async", 
                 fontsize=26, fontweight='bold', y=1.05)
    
    output_path = f"{prefix}_ppt_analysis.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[SUCCESS] PPT Dashboard saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", required=True)
    args = parser.parse_args()
    visualize_ppt(args.prefix)
