"""
Antutor Benchmark Visualizer — Advanced Dashboard
==================================================
Locust --csv 출력 결과를 읽어 6개 차트가 포함된 종합 대시보드를 생성합니다.
(stats.csv 및 stats_history.csv 모두 활용)

[사용법]
  python visualize.py --prefix results/bench
"""

import argparse
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from datetime import datetime

# ---------------------------------------------------------------------------
# 스타일 설정
# ---------------------------------------------------------------------------
sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams['font.family'] = 'Segoe UI' if os.name == 'nt' else 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

PALETTE = {
    "/benchmark/sync":         "#E74C3C",   # 빨강 — 직렬
    "/benchmark/async":        "#2ECC71",   # 초록 — 병렬
    "/benchmark/sync [fixed]": "#F1948A",   # 연빨강
    "/benchmark/async [fixed]":"#82E0AA",   # 연초록
}

# ---------------------------------------------------------------------------
# 데이터 로드 헬퍼
# ---------------------------------------------------------------------------
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
    return df

def load_history(prefix: str):
    path = f"{prefix}_stats_history.csv"
    if not os.path.exists(path):
        print(f"[WARNING] History 파일을 찾을 수 없습니다: {path}")
        return None

    df = pd.read_csv(path)
    # Aggregated만 사용하거나 혹은 Name별로 분리 가능. 여기선 경향성을 위해 Aggregated 사용
    # 하지만 Sync/Async 구분을 위해 Name이 있는 경우 필터링
    df = df.dropna(subset=['Name']) if 'Name' in df.columns else df
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
    df['Elapsed'] = (df['Timestamp'] - df['Timestamp'].min()).dt.total_seconds()
    return df

# ---------------------------------------------------------------------------
# 메인 시각화 함수
# ---------------------------------------------------------------------------
def visualize(prefix: str):
    stats_df = load_stats(prefix)
    history_df = load_history(prefix)

    fig = plt.figure(figsize=(20, 14))
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.4, wspace=0.3)

    # --- 1. 평균 지연 시간 (Latency) ---
    ax1 = fig.add_subplot(gs[0, 0])
    sns.barplot(x='Label', y='Average Response Time', data=stats_df, palette=PALETTE.values(), ax=ax1)
    ax1.set_title('① Average E2E Latency (ms)', fontweight='bold')
    ax1.set_ylabel('ms')
    for p in ax1.patches:
        ax1.annotate(f"{p.get_height():.0f}", (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', fontsize=10, fontweight='bold', xytext=(0, 5), textcoords='offset points')

    # --- 2. 처리량 (Throughput) ---
    ax2 = fig.add_subplot(gs[0, 1])
    sns.barplot(x='Label', y='Requests/s', data=stats_df, palette=PALETTE.values(), ax=ax2)
    ax2.set_title('② Throughput (RPS)', fontweight='bold')
    ax2.set_ylabel('Requests/sec')
    for p in ax2.patches:
        ax2.annotate(f"{p.get_height():.3f}", (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', fontsize=10, fontweight='bold', xytext=(0, 5), textcoords='offset points')

    # --- 3. 지연 시간 트렌드 (Time Series) ---
    ax3 = fig.add_subplot(gs[1, 0])
    if history_df is not None:
        # 'Total Average Response Time' 은 누적 평균이므로, 구간별 값인 'Average Response Time' (있다면) 혹은 percentile 사용
        # stats_history에는 'Total Average Response Time'이 있음
        sns.lineplot(x='Elapsed', y='Total Average Response Time', data=history_df, ax=ax3, color='#34495E', linewidth=2)
        ax3.set_title('③ Latency Trend over Time', fontweight='bold')
        ax3.set_ylabel('Avg Latency (ms)')
        ax3.set_xlabel('Elapsed Time (s)')
    else:
        ax3.text(0.5, 0.5, 'History data not available', ha='center', va='center', transform=ax3.transAxes)

    # --- 4. 사용자 수 및 부하 추이 ---
    ax4 = fig.add_subplot(gs[1, 1])
    if history_df is not None:
        ax4.fill_between(history_df['Elapsed'], history_df['User Count'], color='#AED6F1', alpha=0.5)
        sns.lineplot(x='Elapsed', y='User Count', data=history_df, ax=ax4, color='#2E86C1')
        ax4.set_title('④ Load Progression (User Count)', fontweight='bold')
        ax4.set_ylabel('Number of Users')
        ax4.set_xlabel('Elapsed Time (s)')
    else:
        ax4.text(0.5, 0.5, 'History data not available', ha='center', va='center', transform=ax4.transAxes)

    # --- 5. 상세 지연 시간 분포 (p90, p99) ---
    ax5 = fig.add_subplot(gs[2, 0])
    melt_df = stats_df.melt(id_vars='Label', value_vars=['90%', '99%'], var_name='Metric', value_name='Latency')
    sns.barplot(x='Label', y='Latency', hue='Metric', data=melt_df, ax=ax5, palette='muted')
    ax5.set_title('⑤ Tail Latency (p90, p99)', fontweight='bold')
    ax5.set_ylabel('ms')

    # --- 6. 실패율 (%) ---
    ax6 = fig.add_subplot(gs[2, 1])
    stats_df['FailRate'] = (stats_df['Failure Count'] / stats_df['Request Count']) * 100
    sns.barplot(x='Label', y='FailRate', data=stats_df, palette=PALETTE.values(), ax=ax6)
    ax6.set_title('⑥ Failure Rate (%)', fontweight='bold')
    ax6.set_ylabel('%')
    ax6.set_ylim(0, 100)
    for p in ax6.patches:
        ax6.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', fontsize=10, fontweight='bold', xytext=(0, 5), textcoords='offset points')

    # 전체 제목
    plt.suptitle(f"Antutor Performance Analysis: Sync vs Async ({datetime.now().strftime('%Y-%m-%d')})", 
                 fontsize=22, fontweight='bold', y=0.98)
    
    output_path = f"{prefix}_analysis.png"
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    print(f"[SUCCESS] Dashboard saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", required=True)
    args = parser.parse_args()
    visualize(args.prefix)
