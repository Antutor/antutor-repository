"""
Antutor Benchmark Visualizer
==============================
Locust --csv 출력 결과를 읽어 4개 차트를 생성합니다.

[사용법]
  python visualize.py                      # 기본: real_results_stats.csv
  python visualize.py --prefix results/s2  # results/s2_stats.csv 사용
"""

import argparse
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

# ---------------------------------------------------------------------------
# 스타일 설정
# ---------------------------------------------------------------------------
sns.set_theme(style="whitegrid", font_scale=1.15)
plt.rcParams['font.family'] = 'Segoe UI'
plt.rcParams['axes.unicode_minus'] = False

PALETTE = {
    "/benchmark/sync":         "#E74C3C",   # 빨강 — 직렬
    "/benchmark/async":        "#2ECC71",   # 초록 — 병렬
    "/benchmark/sync [fixed]": "#F1948A",   # 연빨강
    "/benchmark/async [fixed]":"#82E0AA",   # 연초록
}
DEFAULT_COLORS = ["#E74C3C", "#2ECC71", "#F1948A", "#82E0AA"]

# ---------------------------------------------------------------------------
# 레이블 매핑
# ---------------------------------------------------------------------------
LABEL_MAP = {
    "/benchmark/sync":         "Sync\n(Sequential)",
    "/benchmark/async":        "Async\n(Parallel)",
    "/benchmark/sync [fixed]": "Sync\n[fixed]",
    "/benchmark/async [fixed]":"Async\n[fixed]",
}


def load_stats(prefix: str) -> pd.DataFrame:
    path = f"{prefix}_stats.csv"
    if not os.path.exists(path):
        print(f"[ERROR] 파일을 찾을 수 없습니다: {path}")
        print("  Locust 실행 후 --csv 옵션으로 CSV를 먼저 생성하세요.")
        sys.exit(1)

    df = pd.read_csv(path)
    # benchmark 관련 행만 필터링 (Aggregated 행 제외)
    df = df[df['Name'].str.startswith('/benchmark')]
    if df.empty:
        print("[ERROR] /benchmark 관련 데이터가 없습니다.")
        sys.exit(1)

    df['Label'] = df['Name'].map(LABEL_MAP).fillna(df['Name'])
    df['Color'] = df['Name'].map(PALETTE).fillna("#95A5A6")
    return df


def annotate_bars(ax, fmt="{:.0f}", unit=""):
    for p in ax.patches:
        h = p.get_height()
        if h > 0:
            ax.annotate(
                fmt.format(h) + unit,
                (p.get_x() + p.get_width() / 2., h),
                ha='center', va='bottom',
                fontsize=10, fontweight='bold',
                xytext=(0, 4), textcoords='offset points'
            )


def visualize(prefix: str):
    df = load_stats(prefix)

    fig = plt.figure(figsize=(18, 11))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    ax1 = fig.add_subplot(gs[0, 0])  # 평균 응답시간
    ax2 = fig.add_subplot(gs[0, 1])  # 처리량 (RPS)
    ax3 = fig.add_subplot(gs[1, 0])  # p90 / p99 지연시간
    ax4 = fig.add_subplot(gs[1, 1])  # 실패율

    colors = df['Color'].tolist()

    # ── Plot 1: 평균 응답시간 (ms) ──────────────────────────────
    sns.barplot(x='Label', y='Average Response Time', data=df,
                palette=colors, ax=ax1, hue='Label', legend=False)
    ax1.set_title('① Avg. E2E Latency (↓ Better)', fontweight='bold')
    ax1.set_ylabel('Response Time (ms)')
    ax1.set_xlabel('')
    annotate_bars(ax1, "{:.0f}", " ms")

    # ── Plot 2: 처리량 (RPS) ─────────────────────────────────────
    sns.barplot(x='Label', y='Requests/s', data=df,
                palette=colors, ax=ax2, hue='Label', legend=False)
    ax2.set_title('② Throughput (↑ Better)', fontweight='bold')
    ax2.set_ylabel('Requests Per Second (RPS)')
    ax2.set_xlabel('')
    annotate_bars(ax2, "{:.2f}", " RPS")

    # ── Plot 3: p90 / p99 지연시간 비교 ─────────────────────────
    percentile_cols = ['90%', '99%']
    available_cols  = [c for c in percentile_cols if c in df.columns]
    if available_cols:
        df_pct = df[['Label'] + available_cols].melt(
            id_vars='Label', var_name='Percentile', value_name='Latency (ms)'
        )
        sns.barplot(x='Label', y='Latency (ms)', hue='Percentile',
                    data=df_pct, ax=ax3, palette=["#5DADE2", "#1A5276"])
        ax3.set_title('③ Tail Latency — p90 & p99 (↓ Better)', fontweight='bold')
        ax3.set_ylabel('Latency (ms)')
        ax3.set_xlabel('')
        ax3.legend(title='Percentile', fontsize=9)
        annotate_bars(ax3, "{:.0f}", " ms")
    else:
        ax3.text(0.5, 0.5, 'p90/p99 데이터 없음\n(Locust 버전 확인)', ha='center', va='center',
                 transform=ax3.transAxes, fontsize=12, color='gray')
        ax3.set_title('③ Tail Latency', fontweight='bold')

    # ── Plot 4: 실패율 (%) ───────────────────────────────────────
    if 'Failure Count' in df.columns and 'Request Count' in df.columns:
        df['Failure Rate (%)'] = (df['Failure Count'] / df['Request Count'].replace(0, 1)) * 100
    else:
        df['Failure Rate (%)'] = 0.0

    sns.barplot(x='Label', y='Failure Rate (%)', data=df,
                palette=colors, ax=ax4, hue='Label', legend=False)
    ax4.set_title('④ Failure Rate (↓ Better)', fontweight='bold')
    ax4.set_ylabel('Failure Rate (%)')
    ax4.set_xlabel('')
    ax4.set_ylim(0, max(df['Failure Rate (%)'].max() * 1.4, 5))
    annotate_bars(ax4, "{:.1f}", "%")

    # ── 전체 제목 + 캡션 ─────────────────────────────────────────
    plt.suptitle(
        'Antutor Multi-Agent: Sync vs. Async Architecture — Performance Benchmark',
        fontsize=17, fontweight='bold', y=1.01
    )
    plt.figtext(
        0.5, -0.02,
        "* Measured using real News API, Knowledge Graph retrieval, and local LLM inference (Ollama).\n"
        "  Sync = Sequential Draft+Rebuttal calls  |  Async = asyncio.gather + LangGraph parallel nodes",
        ha="center", fontsize=9, style='italic', color='gray'
    )

    output = f"{prefix}_analysis.png"
    plt.savefig(output, bbox_inches='tight', dpi=200)
    print(f"\n[✅ 저장 완료] {output}")
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antutor Benchmark Visualizer")
    parser.add_argument(
        "--prefix", default="real_results",
        help="Locust --csv 옵션에 사용한 이름 (예: results/s2)"
    )
    args = parser.parse_args()
    visualize(args.prefix)
