"""生成论文所有实验图表"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 11

FIG_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def save(fig, name):
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {path}")


# ===== Figure 1: System Architecture =====

def fig_architecture():
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')
    ax.set_title('Figure 1: Orchestrator System Architecture', fontsize=14, fontweight='bold', pad=20)

    def box(x, y, w, h, text, color='#4A90D9', fontsize=10, bold=False):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='#333', linewidth=1.5, alpha=0.9)
        ax.add_patch(rect)
        weight = 'bold' if bold else 'normal'
        ax.text(x + w/2, y + h/2, text, ha='center', va='center',
                fontsize=fontsize, fontweight=weight, color='white' if color != '#F5F5F5' else 'black')

    def arrow(x1, y1, x2, y2, color='#666'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5))

    # User
    box(0.5, 6.5, 2, 1, 'User\nRequest', '#2C3E50', 11, True)

    # Orchestrator
    box(4, 6, 4, 1.5, 'Orchestrator\n(Meta-Cognitive Dispatcher)', '#E74C3C', 12, True)

    # Architect
    box(0.5, 4, 2.5, 1, 'Architect\n(API Contract)', '#3498DB', 10)

    # Frontend
    box(4, 3.5, 2.5, 1, 'Frontend Dev\n(cline_runner)', '#27AE60', 10)

    # Backend
    box(7.5, 3.5, 2.5, 1, 'Backend Dev\n(code_executor)', '#27AE60', 10)

    # QA
    box(0.5, 2, 2.5, 1, 'QA Engineer\n(Validator)', '#F39C12', 10)

    # DevOps
    box(4, 2, 2.5, 1, 'DevOps\n(Docker/CI)', '#F39C12', 10)

    # Rule Engine
    box(7.5, 2, 2.5, 1, 'Rule Engine\n(Auto-Events)', '#8E44AD', 10)

    # Project Store
    box(4, 0.3, 4, 1, 'Project Store (JSON Persistence)', '#7F8C8D', 10)

    # Arrows
    arrow(2.5, 7, 4, 6.75)  # User -> Orchestrator
    arrow(5, 6, 1.75, 5)    # Orchestrator -> Architect
    arrow(5.5, 6, 5.25, 4.5)  # Orchestrator -> Frontend
    arrow(7, 6, 8.75, 4.5)  # Orchestrator -> Backend
    arrow(5, 3.5, 1.75, 3)  # Frontend -> QA
    arrow(8.75, 3.5, 5.25, 3)  # Backend -> DevOps
    arrow(5, 2, 6, 1.3)     # DevOps -> Store
    arrow(8.75, 2, 7, 1.3)  # Rule Engine -> Store

    # Parallel indicator
    ax.annotate('Parallel', xy=(6.25, 4.5), fontsize=9, color='#E74C3C',
                fontweight='bold', ha='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#FECDD3', alpha=0.8))

    save(fig, 'fig1_architecture.png')


# ===== Figure 2: Execution Flow =====

def fig_execution_flow():
    fig, ax = plt.subplots(1, 1, figsize=(14, 6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis('off')
    ax.set_title('Figure 2: Three-Phase Execution Flow', fontsize=14, fontweight='bold', pad=20)

    def box(x, y, w, h, text, color='#4A90D9', fontsize=9):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor='#333', linewidth=1.2, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center',
                fontsize=fontsize, color='white', fontweight='bold')

    # Phase A
    ax.text(2.5, 5.5, 'Phase A: Planning', fontsize=12, fontweight='bold', ha='center', color='#2C3E50')
    box(0.5, 4.2, 4, 1, 'Orchestrator → Architect\nGenerate API Contract', '#3498DB')
    ax.text(2.5, 3.8, '~2 min', fontsize=9, ha='center', color='#666', style='italic')

    # Phase B
    ax.text(7.5, 5.5, 'Phase B: Parallel Development', fontsize=12, fontweight='bold', ha='center', color='#2C3E50')
    box(5.5, 4.2, 2, 1, 'Frontend\nDev', '#27AE60')
    box(8, 4.2, 2, 1, 'Backend\nDev', '#27AE60')
    ax.text(7.5, 3.8, '~2 min (parallel)', fontsize=9, ha='center', color='#666', style='italic')

    # Phase C
    ax.text(12, 5.5, 'Phase C: Verify', fontsize=12, fontweight='bold', ha='center', color='#2C3E50')
    box(10.5, 4.2, 3, 1, 'Integration\nCheck', '#E74C3C')
    ax.text(12, 3.8, '~1 min', fontsize=9, ha='center', color='#666', style='italic')

    # Timeline
    ax.plot([0.5, 13.5], [3.2, 3.2], 'k-', linewidth=2)
    for x, label in [(0.5, '0s'), (2.5, '120s'), (5.5, '240s'), (7.5, '300s'), (10.5, '420s'), (13.5, '575s')]:
        ax.plot(x, 3.2, 'ko', markersize=6)
        ax.text(x, 2.9, label, ha='center', fontsize=8, color='#333')

    # Sequential comparison
    ax.text(7, 2.2, 'Sequential (previous): ~474s', fontsize=10, ha='center',
            color='#E74C3C', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FECDD3', alpha=0.7))
    ax.text(7, 1.5, 'Parallel (optimized): ~575s (with Architect phase)', fontsize=10, ha='center',
            color='#27AE60', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#D5F5E3', alpha=0.7))

    # Phase B parallel bracket
    ax.annotate('', xy=(5.5, 4.7), xytext=(10, 4.7),
                arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=2))
    ax.text(7.75, 4.95, 'asyncio.gather()', fontsize=8, ha='center', color='#E74C3C', family='monospace')

    save(fig, 'fig2_execution_flow.png')


# ===== Figure 3: Token Consumption Comparison =====

def fig_token_comparison():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Data
    categories = ['Single Cline\n(Baseline)', 'Orchestrator-team\n(Original)', 'Orchestrator-team\n(Optimized)']
    prompt_tokens = [254597, 221763, 220000]
    completion_tokens = [16283, 25243, 69000]
    total_tokens = [270880, 247006, 289069]

    # Left: Stacked bar
    ax = axes[0]
    x = np.arange(len(categories))
    w = 0.5
    bars1 = ax.bar(x, prompt_tokens, w, label='Prompt Tokens', color='#3498DB', alpha=0.85)
    bars2 = ax.bar(x, completion_tokens, w, bottom=prompt_tokens, label='Completion Tokens', color='#E74C3C', alpha=0.85)
    ax.set_ylabel('Tokens')
    ax.set_title('(a) Token Consumption Breakdown', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=9)
    ax.legend()
    ax.set_yscale('log')
    ax.grid(axis='y', alpha=0.3)

    # Right: Token efficiency (bytes/token)
    ax = axes[1]
    file_bytes = [21905, 49509, 40000]
    efficiency = [b / t for b, t in zip(file_bytes, total_tokens)]
    colors = ['#3498DB', '#E74C3C', '#27AE60']
    bars = ax.bar(categories, efficiency, color=colors, alpha=0.85, edgecolor='#333')
    ax.set_ylabel('Bytes / Token')
    ax.set_title('(b) Token Efficiency', fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars, efficiency):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                f'{val:.4f}', ha='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    save(fig, 'fig3_token_comparison.png')


# ===== Figure 4: Time Breakdown =====

def fig_time_breakdown():
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))

    # Gantt-like chart
    phases = [
        ('Orchestrator Analysis', 0, 420, '#E74C3C'),
        ('Architect (API Contract)', 420, 480, '#3498DB'),
        ('Frontend Dev (parallel)', 480, 575, '#27AE60'),
        ('Backend Dev (parallel)', 480, 575, '#27AE60'),
    ]

    for i, (label, start, end, color) in enumerate(phases):
        ax.barh(i, end - start, left=start, height=0.5, color=color, alpha=0.85, edgecolor='#333')
        ax.text(start + (end - start)/2, i, f'{label}\n({end-start}s)',
                ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    ax.set_yticks(range(len(phases)))
    ax.set_yticklabels([p[0] for p in phases], fontsize=9)
    ax.set_xlabel('Time (seconds)')
    ax.set_title('Figure 4: Optimized Multi-Agent Time Breakdown (575s total)', fontweight='bold')
    ax.set_xlim(0, 650)
    ax.grid(axis='x', alpha=0.3)

    # Add total time annotation
    ax.annotate('Total: 575s', xy=(575, 3.5), fontsize=11, fontweight='bold',
                color='#E74C3C', ha='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FECDD3', alpha=0.7))

    # Parallel indicator
    ax.annotate('Parallel', xy=(527, 1), fontsize=9, color='#27AE60',
                fontweight='bold', ha='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#D5F5E3', alpha=0.8))

    plt.tight_layout()
    save(fig, 'fig4_time_breakdown.png')


# ===== Figure 5: File Output Comparison =====

def fig_file_comparison():
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    files = {
        'index.html': (4895, 2354, 2387),
        'style.css': (12619, 7955, 7041),
        'app.js': (0, 10510, 7122),
        'server.py': (4340, 5226, 3630),
        'tasks.json': (3, 2, 2),
        'requirements.txt': (48, 29, 47),
        'Dockerfile': (0, 374, 758),
        'README.md': (0, 5018, 3751),
    }

    x = np.arange(len(files))
    w = 0.25
    cline_vals = [v[0] for v in files.values()]
    orch_orig = [v[1] for v in files.values()]
    orch_opt = [v[2] for v in files.values()]

    ax.bar(x - w, cline_vals, w, label='Single Cline', color='#3498DB', alpha=0.85)
    ax.bar(x, orch_orig, w, label='Orchestrator (original)', color='#E74C3C', alpha=0.85)
    ax.bar(x + w, orch_opt, w, label='Orchestrator (optimized)', color='#27AE60', alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(list(files.keys()), rotation=30, ha='right', fontsize=9)
    ax.set_ylabel('File Size (bytes)')
    ax.set_title('Figure 5: Output File Size Comparison', fontweight='bold')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    save(fig, 'fig5_file_comparison.png')


# ===== Figure 6: Architecture Comparison =====

def fig_arch_comparison():
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    configs = [
        ('Single Agent (Cline)', ['LLM\n+ Tools'], '#3498DB'),
        ('Orchestrator-team\n(Original)', ['Orchestrator', 'Architect', 'Frontend', 'Backend', 'QA', 'DevOps'], '#E74C3C'),
        ('Orchestrator-team\n(Optimized)', ['Orchestrator', 'Architect', 'Frontend\n(parallel)', 'Backend\n(parallel)', 'Rule\nEngine'], '#27AE60'),
    ]

    for ax, (title, agents, color) in zip(axes, configs):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        ax.set_title(title, fontsize=11, fontweight='bold')

        n = len(agents)
        for i, agent in enumerate(agents):
            y = 8 - i * (8 / max(n, 1))
            rect = FancyBboxPatch((1, y), 8, 1.2, boxstyle="round,pad=0.1",
                                  facecolor=color, edgecolor='#333', linewidth=1, alpha=0.85)
            ax.add_patch(rect)
            ax.text(5, y + 0.6, agent, ha='center', va='center', fontsize=9, color='white', fontweight='bold')

        if n > 1:
            for i in range(n - 1):
                y1 = 8 - i * (8 / max(n, 1)) + 0.1
                y2 = 8 - (i + 1) * (8 / max(n, 1)) + 1.1
                ax.annotate('', xy=(5, y2), xytext=(5, y1),
                            arrowprops=dict(arrowstyle='->', color='#666', lw=1))

    plt.tight_layout()
    save(fig, 'fig6_arch_comparison.png')


# ===== Table 1: Benchmark Results =====

def table_benchmark():
    fig, ax = plt.subplots(1, 1, figsize=(12, 4))
    ax.axis('off')

    data = [
        ['Metric', 'Single Cline', 'Orchestrator\n(original)', 'Orchestrator\n(optimized)'],
        ['Status', 'failed', 'completed', 'completed'],
        ['Time (s)', '302', '474', '575'],
        ['LLM Calls', '1', '29', '36'],
        ['Prompt Tokens', '254,597', '221,763', '~220,000'],
        ['Completion Tokens', '16,283', '25,243', '~69,000'],
        ['Total Tokens', '270,880', '247,006', '289,069'],
        ['Output Files', '5', '16', '10'],
        ['Output (bytes)', '21,905', '49,509', '~40,000'],
        ['Token Efficiency', '0.081', '0.200', '~0.14'],
        ['Silent Delivery', 'N/A', 'No', 'Yes'],
        ['Parallel Exec', 'N/A', 'No', 'Yes'],
    ]

    table = ax.table(cellText=data, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.4)

    # Style header
    for j in range(4):
        table[0, j].set_facecolor('#2C3E50')
        table[0, j].set_text_props(color='white', fontweight='bold')

    # Style rows
    for i in range(1, len(data)):
        for j in range(4):
            if i % 2 == 0:
                table[i, j].set_facecolor('#F8F9FA')

    ax.set_title('Table 1: Benchmark Comparison Results', fontsize=12, fontweight='bold', pad=20)
    save(fig, 'table1_benchmark.png')


if __name__ == "__main__":
    print("Generating figures...")
    fig_architecture()
    fig_execution_flow()
    fig_token_comparison()
    fig_time_breakdown()
    fig_file_comparison()
    fig_arch_comparison()
    table_benchmark()
    print("All figures generated!")
