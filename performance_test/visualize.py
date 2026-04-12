import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set aesthetic style for professional capstone report
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'Segoe UI' # Clean font for Windows
plt.rcParams['axes.unicode_minus'] = False

def visualize_real_world_results(csv_path='real_results_stats.csv'):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Please run Locust benchmarking first.")
        print("Command: locust -f performance_test/locustfile.py --headless -u 5 -r 1 --run-time 2m --host http://localhost:8000 --csv real_results")
        return

    # 1. Data Loading
    df = pd.read_csv(csv_path)
    
    # Filter only the relevant benchmark endpoints
    df = df[df['Name'].isin(['/benchmark/sync', '/benchmark/async'])]
    
    # Map more descriptive names for the chart
    name_map = {
        '/benchmark/sync': 'Sequential Architecture\n(Sync Retrieval + Sync Agents)',
        '/benchmark/async': 'Optimized Parallel Architecture\n(Async RAG + Parallel Agents)'
    }
    df['ArchName'] = df['Name'].map(name_map)
    
    # Define primary colors
    colors = ["#E74C3C", "#2ECC71"] # Elegant Red and Green
    
    # Create Figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
    plt.subplots_adjust(wspace=0.35)

    # --- Plot 1: Average Response Time ---
    sns.barplot(
        x='ArchName', 
        y='Average Response Time', 
        data=df, 
        palette=colors, 
        ax=ax1,
        hue='ArchName',
        legend=False
    )
    ax1.set_title('Avg. E2E Latency (Lower is Better)', fontsize=15, fontweight='bold', pad=25)
    ax1.set_ylabel('Execution Time (ms)', fontsize=13)
    ax1.set_xlabel('', fontsize=12)
    
    # Annotate values
    for p in ax1.patches:
        ax1.annotate(f'{p.get_height():.0f} ms', 
                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha = 'center', va = 'center', 
                    xytext = (0, 10), 
                    textcoords = 'offset points',
                    fontsize=12, fontweight='bold')

    # --- Plot 2: Requests Per Second ---
    sns.barplot(
        x='ArchName', 
        y='Requests/s', 
        data=df, 
        palette=colors, 
        ax=ax2,
        hue='ArchName',
        legend=False
    )
    ax2.set_title('System Throughput (Higher is Better)', fontsize=15, fontweight='bold', pad=25)
    ax2.set_ylabel('Requests Per Second (RPS)', fontsize=13)
    ax2.set_xlabel('', fontsize=12)

    # Annotate values
    for p in ax2.patches:
        ax2.annotate(f'{p.get_height():.2f} RPS', 
                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha = 'center', va = 'center', 
                    xytext = (0, 10), 
                    textcoords = 'offset points',
                    fontsize=12, fontweight='bold')

    # Overall Header
    plt.suptitle('Antutor Multi-Agent Performance Mastery: Real-world Benchmark Analysis', 
                 fontsize=20, fontweight='bold', y=1.05)
    
    plt.figtext(0.5, 0.01, "* Measured using real News API, KG Retrieval, and Local LLM (Gemma 3:1b) inference.", 
                ha="center", fontsize=10, style='italic', color='gray')

    # Save professionally
    output_filename = 'real_performance_analysis.png'
    plt.savefig(output_filename, bbox_inches='tight', dpi=300)
    print(f"\n[Success] Chart saved as {output_filename}")
    plt.show()

if __name__ == "__main__":
    visualize_real_world_results()
