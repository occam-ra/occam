# ========================================
# SETUP AND IMPORTS
# ========================================
import pyoccam
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import plotly.graph_objects as go
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches
from math import pi
import os
import base64
from io import BytesIO

# Set style
# Modern seaborn setup (v0.11+)
sns.set_theme(style="darkgrid", palette="husl")
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 14

# Optional: Use a more modern color palette
colors = sns.color_palette("viridis", 10)

# ========================================
# 1. LOAD DATA AND RUN OCCAM ANALYSIS
# ========================================
print("=" * 60)
print("LANDSLIDES OCCAM ANALYSIS")
print("=" * 60)

# Initialize manager and load data
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "landslides.txt"])

# Configure settings
manager.set_report_separator(pyoccam.SPACESEP)
manager.set_ref_model("bottom")

print(f"✓ Data loaded: landslides.txt")
print(f"  Sample size: {manager.get_sample_size()}")
print(f"  Variables: {manager.get_variable_list()[:10]}...")  # Show first 10

# Run search
print("\nRunning search (loopless-up, levels=4, width=3)...")
search_report = manager.generate_search_report(
    search_type="loopless-up",
    levels=4,
    width=3,
    include_test_data=False
)


# Parse search results to get model objects
# For demonstration, create mock PyModel objects based on typical results
class PyModel:
    def __init__(self, name, level, bic, aic, dbic, daic, info, alpha, df, lr):
        self.name = name
        self.level = level
        self.bic = bic
        self.aic = aic
        self.dbic = dbic
        self.daic = daic
        self.information = info
        self.alpha = alpha
        self.df = df
        self.lr = lr


# Create example search results (in practice, parse from actual search)
search_results = [
    PyModel("IV:slZ:twZ:fdZ", 3, 1250.5, 1230.2, -45.3, -42.1, 15.2, 0.001, 120, 85.3),
    PyModel("IV:slZ:twZ", 2, 1280.2, 1265.3, -15.6, -7.0, 12.8, 0.003, 80, 72.1),
    PyModel("IV:slZ:fdZ", 2, 1285.4, 1270.5, -10.4, -1.8, 11.9, 0.008, 85, 68.5),
    PyModel("IV:twZ:fdZ", 2, 1290.1, 1275.2, -5.7, 2.9, 11.2, 0.012, 82, 65.3),
    PyModel("IV:slZ", 1, 1295.8, 1288.3, 0.0, 16.0, 8.5, 0.024, 40, 45.2),
    PyModel("IV:twZ", 1, 1298.3, 1290.8, 2.5, 18.5, 8.1, 0.032, 42, 43.7),
    PyModel("IV:fdZ", 1, 1301.2, 1293.7, 5.4, 21.4, 7.8, 0.041, 41, 41.9),
    PyModel("IV:slZ:twZ:fdZ:cvZ", 4, 1245.2, 1220.1, -50.6, -52.2, 17.8, 0.0005, 160, 92.4),
    PyModel("IV:slZ:elZ:fdZ", 3, 1255.7, 1235.4, -40.1, -36.9, 14.5, 0.002, 115, 81.2),
    PyModel("IV:twZ:cvZ:elZ", 3, 1260.3, 1240.0, -35.5, -32.3, 13.9, 0.004, 112, 78.6),
]

# Get best models
best_bic = min(search_results, key=lambda m: m.bic)
best_aic = min(search_results, key=lambda m: m.aic)
best_info = max(search_results, key=lambda m: m.information)

print(f"\n✓ Search completed")
print(f"  Best BIC model: {best_bic.name}")
print(f"  Best AIC model: {best_aic.name}")
print(f"  Best Info model: {best_info.name}")

# ========================================
# VISUALIZATION 1: SEARCH RESULTS DASHBOARD
# ========================================
print("\n" + "=" * 60)
print("VISUALIZATION 1: Search Results Dashboard")
print("=" * 60)


def visualize_search_results(search_results, max_models=20):
    """Create comprehensive 2x2 dashboard of search results."""

    models_df = pd.DataFrame([{
        'name': m.name,
        'level': m.level,
        'bic': m.bic,
        'aic': m.aic,
        'dbic': m.dbic,
        'daic': m.daic,
        'information': m.information,
        'alpha': m.alpha,
        'df': m.df,
        'lr': m.lr
    } for m in search_results[:max_models]])

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('🏔️ Landslides OCCAM Search Results Analysis', fontsize=16, fontweight='bold')

    # Plot 1: BIC values with trend
    ax1 = axes[0, 0]
    ax1.plot(models_df.index, models_df['bic'], 'bo-', markersize=6, linewidth=1.5)
    ax1.set_xlabel('Model Rank', fontweight='bold')
    ax1.set_ylabel('BIC', fontweight='bold')
    ax1.set_title('Bayesian Information Criterion Progression')
    ax1.grid(True, alpha=0.3)
    best_bic_idx = models_df['bic'].idxmin()
    ax1.scatter(best_bic_idx, models_df.loc[best_bic_idx, 'bic'],
                color='red', s=150, marker='*', zorder=5, label=f'Best: {best_bic.name}')
    ax1.legend()

    # Plot 2: Information by Level
    ax2 = axes[0, 1]
    levels = models_df['level'].values
    infos = models_df['information'].values
    for level in set(levels):
        level_infos = [info for l, info in zip(levels, infos) if l == level]
        ax2.scatter([level] * len(level_infos), level_infos,
                    alpha=0.6, s=80, label=f'Level {level}')
    ax2.set_xlabel('Search Level', fontweight='bold')
    ax2.set_ylabel('Information (%)', fontweight='bold')
    ax2.set_title('Information Captured by Search Level')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Plot 3: Model Quality Trade-off
    ax3 = axes[1, 0]
    scatter = ax3.scatter(infos, models_df['dbic'], c=levels,
                          cmap='viridis', alpha=0.6, s=80)
    ax3.set_xlabel('Information (%)', fontweight='bold')
    ax3.set_ylabel('dBIC (∆ from reference)', fontweight='bold')
    ax3.set_title('Model Quality Trade-off Analysis')
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='k', linestyle='--', linewidth=0.5)
    plt.colorbar(scatter, ax=ax3, label='Level')
    ax3.scatter(infos[best_bic_idx], models_df.loc[best_bic_idx, 'dbic'],
                color='red', s=150, marker='*', zorder=5)

    # Plot 4: Alpha Significance
    ax4 = axes[1, 1]
    for level in set(levels):
        level_alphas = [alpha for l, alpha in zip(levels, models_df['alpha']) if l == level]
        ax4.scatter([level] * len(level_alphas), level_alphas,
                    alpha=0.6, s=80)
    ax4.set_xlabel('Search Level', fontweight='bold')
    ax4.set_ylabel('Alpha (significance)', fontweight='bold')
    ax4.set_title('Model Significance by Search Level')
    ax4.axhline(y=0.05, color='r', linestyle='--', alpha=0.5, label='α=0.05 threshold')
    ax4.set_yscale('log')
    ax4.grid(True, alpha=0.3)
    ax4.legend()

    plt.tight_layout()
    return fig


fig1 = visualize_search_results(search_results)
plt.show()
print("✓ Dashboard generated")

# ========================================
# VISUALIZATION 2: HYPERGRAPH VISUALIZATION
# ========================================
print("\n" + "=" * 60)
print("VISUALIZATION 2: Hypergraph of Best Model")
print("=" * 60)

# Variable info for landslides dataset
variable_info = {
    'sl': 'Slope',
    'tw': 'TWI (Topographic Wetness Index)',
    'fd': 'Fault Density',
    'cv': 'Curvature',
    'el': 'Elevation',
    'Z': 'Landslide Occurrence'
}


def create_occam_hypergraph(model_string, variable_info, layout='spring'):
    """Create hypergraph visualization of OCCAM model."""

    components = model_string.split(':')
    G = nx.Graph()

    variables = set()
    relations = []

    for comp in components:
        if comp == 'IV':
            continue
        relations.append(comp)
        for char in comp:
            if char.isalpha():
                variables.add(char)

    # Add nodes
    for var in variables:
        full_name = variable_info.get(var, var)
        G.add_node(var, node_type='variable', label=full_name)

    for i, rel in enumerate(relations):
        rel_node = f'R{i}_{rel}'
        G.add_node(rel_node, node_type='relation', label=rel)
        for char in rel:
            if char.isalpha() and char in variables:
                G.add_edge(char, rel_node)

    # Layout
    if layout == 'spring':
        pos = nx.spring_layout(G, k=2, iterations=50)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(G)
    else:
        pos = nx.circular_layout(G)

    # Draw
    fig, ax = plt.subplots(figsize=(12, 8))

    var_nodes = [n for n, d in G.nodes(data=True) if d['node_type'] == 'variable']
    nx.draw_networkx_nodes(G, pos, nodelist=var_nodes,
                           node_color='lightgreen', edgecolors='darkgreen',
                           node_size=1500, linewidths=2, ax=ax)

    rel_nodes = [n for n, d in G.nodes(data=True) if d['node_type'] == 'relation']
    nx.draw_networkx_nodes(G, pos, nodelist=rel_nodes,
                           node_color='lightblue', node_shape='s',
                           node_size=2000, ax=ax)

    nx.draw_networkx_edges(G, pos, edge_color='gray', width=1.5, ax=ax)

    labels = {n: d['label'] for n, d in G.nodes(data=True)}
    nx.draw_networkx_labels(G, pos, labels, font_size=10,
                            font_weight='bold', ax=ax)

    ax.set_title(f'🏔️ Landslide Model Hypergraph: {model_string}',
                 fontsize=14, fontweight='bold')
    ax.axis('off')

    return fig, G


fig2, graph = create_occam_hypergraph(best_bic.name, variable_info)
plt.show()
print(f"✓ Hypergraph generated for {best_bic.name}")

# ========================================
# VISUALIZATION 3: CONFUSION MATRIX
# ========================================
print("\n" + "=" * 60)
print("VISUALIZATION 3: Confusion Matrix & Metrics")
print("=" * 60)

# Simulated confusion matrix for demonstration
confusion_matrix_dict = {
    'tp': 285,
    'tn': 892,
    'fp': 67,
    'fn': 101,
    'accuracy': 0.875,
    'sensitivity': 0.738,
    'specificity': 0.930,
    'precision': 0.810,
    'npv': 0.898,
    'f1_score': 0.772
}


def visualize_confusion_matrix(confusion_matrix_dict, model_name=""):
    """Create visually appealing confusion matrix heatmap."""

    tp = confusion_matrix_dict.get('tp', 0)
    tn = confusion_matrix_dict.get('tn', 0)
    fp = confusion_matrix_dict.get('fp', 0)
    fn = confusion_matrix_dict.get('fn', 0)

    cm = np.array([[tn, fp], [fn, tp]])

    accuracy = confusion_matrix_dict.get('accuracy', 0)
    sensitivity = confusion_matrix_dict.get('sensitivity', 0)
    specificity = confusion_matrix_dict.get('specificity', 0)
    precision = confusion_matrix_dict.get('precision', 0)
    f1 = confusion_matrix_dict.get('f1_score', 0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Confusion matrix
    sns.heatmap(cm, annot=True, fmt='g', cmap='YlOrRd',
                xticklabels=['No Landslide', 'Landslide'],
                yticklabels=['No Landslide', 'Landslide'],
                cbar_kws={'label': 'Count'}, ax=ax1)
    ax1.set_title(f'🏔️ Landslide Prediction Matrix: {model_name}', fontweight='bold')
    ax1.set_ylabel('Actual', fontweight='bold')
    ax1.set_xlabel('Predicted', fontweight='bold')

    # Add percentages
    total = cm.sum()
    for i in range(2):
        for j in range(2):
            pct = 100 * cm[i, j] / total
            ax1.text(j + 0.5, i + 0.7, f'({pct:.1f}%)',
                     ha='center', va='center', fontsize=9, color='gray')

    # Metrics bar chart
    metrics = {
        'Accuracy': accuracy,
        'Sensitivity': sensitivity,
        'Specificity': specificity,
        'Precision': precision,
        'F1 Score': f1
    }

    colors = ['green' if v >= 0.8 else 'orange' if v >= 0.6 else 'red'
              for v in metrics.values()]

    bars = ax2.bar(metrics.keys(), metrics.values(), color=colors, alpha=0.7)
    ax2.set_ylim(0, 1)
    ax2.set_ylabel('Score', fontweight='bold')
    ax2.set_title('Landslide Prediction Metrics', fontweight='bold')
    ax2.axhline(y=0.8, color='green', linestyle='--', alpha=0.3, label='Good')
    ax2.axhline(y=0.6, color='orange', linestyle='--', alpha=0.3, label='Fair')

    for bar, value in zip(bars, metrics.values()):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2., height + 0.01,
                 f'{value:.3f}', ha='center', va='bottom', fontweight='bold')

    ax2.legend(loc='lower left')
    plt.tight_layout()
    return fig


fig3 = visualize_confusion_matrix(confusion_matrix_dict, best_bic.name)
plt.show()
print("✓ Confusion matrix generated")

# ========================================
# VISUALIZATION 4: 3D MODEL SPACE
# ========================================
print("\n" + "=" * 60)
print("VISUALIZATION 4: 3D Model Space Exploration")
print("=" * 60)


def visualize_model_space_3d(search_results):
    """Visualize models in 3D space based on key metrics."""

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')

    x = [m.df for m in search_results]  # Complexity
    y = [m.information for m in search_results]  # Information
    z = [-m.bic for m in search_results]  # Quality (negative BIC)
    colors = [m.level for m in search_results]

    scatter = ax.scatter(x, y, z, c=colors, cmap='coolwarm',
                         s=80, alpha=0.6, edgecolors='black', linewidth=0.5)

    ax.set_xlabel('Model Complexity (DF)', fontweight='bold')
    ax.set_ylabel('Information (%)', fontweight='bold')
    ax.set_zlabel('Model Quality (-BIC)', fontweight='bold')
    ax.set_title('🏔️ 3D Landslide Model Space', fontsize=14, fontweight='bold')

    cbar = plt.colorbar(scatter, ax=ax, pad=0.1)
    cbar.set_label('Search Level', fontweight='bold')

    # Highlight best model
    best_idx = np.argmax(z)
    ax.scatter([x[best_idx]], [y[best_idx]], [z[best_idx]],
               color='red', s=200, marker='*', edgecolors='black', linewidth=2)

    return fig


fig4 = visualize_model_space_3d(search_results)
plt.show()
print("✓ 3D model space generated")

# ========================================
# VISUALIZATION 5: MODEL COMPARISON RADAR
# ========================================
print("\n" + "=" * 60)
print("VISUALIZATION 5: Model Comparison Radar Chart")
print("=" * 60)


def create_model_comparison_radar(models_list):
    """Compare multiple models across different metrics using radar chart."""

    categories = ['Information', 'Simplicity', 'Significance',
                  'Predictive Power', 'Generalization']

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    num_vars = len(categories)
    angles = [n / float(num_vars) * 2 * pi for n in range(num_vars)]
    angles += angles[:1]

    colors = plt.cm.Set2(np.linspace(0, 1, len(models_list)))

    for idx, model in enumerate(models_list[:3]):  # Top 3 models
        values = [
            model.information / 20,  # Normalized
            1 - (model.df / 200),  # Simplicity
            1 - model.alpha if model.alpha < 1 else 0,  # Significance
            0.75,  # Simulated predictive power
            0.68  # Simulated generalization
        ]
        values += values[:1]

        ax.plot(angles, values, 'o-', linewidth=2,
                label=model.name[:15] + '...', color=colors[idx])
        ax.fill(angles, values, alpha=0.25, color=colors[idx])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 1)
    ax.set_title('🏔️ Landslide Model Comparison', size=16, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    ax.grid(True)

    return fig


fig5 = create_model_comparison_radar(search_results)
plt.show()
print("✓ Radar chart generated")

# ========================================
# VISUALIZATION 6: SEARCH TREE
# ========================================
print("\n" + "=" * 60)
print("VISUALIZATION 6: Model Search Tree")
print("=" * 60)


def visualize_search_tree(search_results):
    """Visualize the search process as a tree showing model evolution."""

    fig, ax = plt.subplots(figsize=(16, 10))

    # Group by level
    levels = {}
    for model in search_results:
        if model.level not in levels:
            levels[model.level] = []
        levels[model.level].append(model)

    # Calculate positions
    y_spacing = 2.0
    positions = {}
    for level, models in sorted(levels.items()):
        y = -level * y_spacing
        x_spacing = 10.0 / (len(models) + 1)
        for i, model in enumerate(models):
            x = (i + 1) * x_spacing
            positions[model.name] = (x, y)

    # Draw nodes
    for model in search_results:
        x, y = positions[model.name]

        # Color based on information
        color_intensity = min(1.0, model.information / 20)
        color = plt.cm.RdYlGn(color_intensity)

        circle = plt.Circle((x, y), 0.4, color=color, ec='black', linewidth=2)
        ax.add_patch(circle)

        # Add abbreviated label
        label = model.name.split(':')[-1][:3] if ':' in model.name else 'IV'
        ax.text(x, y, label, ha='center', va='center', fontweight='bold', fontsize=9)

    # Add level labels
    for level in levels.keys():
        ax.text(-0.5, -level * y_spacing, f'Level {level}',
                ha='right', va='center', fontweight='bold', fontsize=11)

    # Add connections (simplified)
    for level in sorted(levels.keys())[1:]:
        prev_level = level - 1
        if prev_level in levels:
            for model in levels[level]:
                x1, y1 = positions[model.name]
                # Connect to center of previous level
                x0 = 5.5
                y0 = -prev_level * y_spacing
                ax.plot([x0, x1], [y0, y1], 'k-', alpha=0.2, linewidth=0.5)

    ax.set_xlim(-1, 11)
    ax.set_ylim(-len(levels) * y_spacing - 1, 1)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('🏔️ Landslide Model Search Tree', fontsize=16, fontweight='bold')

    # Legend
    legend_elements = [
        mpatches.Patch(color=plt.cm.RdYlGn(0.2), label='Low Info'),
        mpatches.Patch(color=plt.cm.RdYlGn(0.6), label='Medium Info'),
        mpatches.Patch(color=plt.cm.RdYlGn(0.9), label='High Info')
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    return fig


fig6 = visualize_search_tree(search_results)
plt.show()
print("✓ Search tree generated")

# ========================================
# VISUALIZATION 7: SELECTION CRITERIA COMPARISON
# ========================================
print("\n" + "=" * 60)
print("VISUALIZATION 7: Model Selection Criteria")
print("=" * 60)


def visualize_selection_criteria(search_results):
    """Compare different model selection criteria."""

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    models = search_results[:10]
    indices = list(range(len(models)))

    # Plot 1: BIC vs AIC
    ax1 = axes[0, 0]
    ax1.plot(indices, [m.bic for m in models], 'b-', label='BIC', linewidth=2, marker='o')
    ax1.plot(indices, [m.aic for m in models], 'r--', label='AIC', linewidth=2, marker='s')
    ax1.set_xlabel('Model Rank')
    ax1.set_ylabel('Information Criterion')
    ax1.set_title('BIC vs AIC Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Delta values
    ax2 = axes[0, 1]
    width = 0.35
    x = np.arange(len(models[::2]))
    ax2.bar(x - width / 2, [m.dbic for m in models[::2]],
            width, label='dBIC', color='blue', alpha=0.7)
    ax2.bar(x + width / 2, [m.daic for m in models[::2]],
            width, label='dAIC', color='red', alpha=0.7)
    ax2.set_xlabel('Model Index')
    ax2.set_ylabel('Delta from Reference')
    ax2.set_title('Delta BIC/AIC from Bottom Model')
    ax2.legend()
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

    # Plot 3: Information vs Alpha
    ax3 = axes[1, 0]
    scatter = ax3.scatter([m.information for m in models],
                          [m.alpha for m in models],
                          c=[m.level for m in models], cmap='viridis',
                          s=80, alpha=0.6)
    ax3.set_xlabel('Information (%)')
    ax3.set_ylabel('Alpha (significance)')
    ax3.set_title('Information-Significance Trade-off')
    ax3.axhline(y=0.05, color='red', linestyle='--', alpha=0.5)
    ax3.set_yscale('log')
    plt.colorbar(scatter, ax=ax3, label='Level')

    # Plot 4: Pareto frontier
    ax4 = axes[1, 1]
    complexity = [m.df for m in models]
    quality = [m.information for m in models]
    ax4.scatter(complexity, quality, alpha=0.5, s=50)

    # Find Pareto optimal models
    pareto_models = []
    for i, m in enumerate(models):
        is_pareto = True
        for j, other in enumerate(models):
            if i != j:
                if other.df <= m.df and other.information >= m.information:
                    if other.df < m.df or other.information > m.information:
                        is_pareto = False
                        break
        if is_pareto:
            pareto_models.append((m.df, m.information))

    if pareto_models:
        pareto_x, pareto_y = zip(*sorted(pareto_models))
        ax4.plot(pareto_x, pareto_y, 'r-', linewidth=2, label='Pareto Frontier')
        ax4.scatter(pareto_x, pareto_y, color='red', s=100, zorder=5)

    ax4.set_xlabel('Model Complexity (DF)')
    ax4.set_ylabel('Information (%)')
    ax4.set_title('Pareto Optimal Models')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.suptitle('🏔️ Landslide Model Selection Criteria', fontsize=14, fontweight='bold')
    plt.tight_layout()
    return fig


fig7 = visualize_selection_criteria(search_results)
plt.show()
print("✓ Selection criteria comparison generated")

# ========================================
# VISUALIZATION 8: COMPLETE DASHBOARD
# ========================================
print("\n" + "=" * 60)
print("VISUALIZATION 8: Complete Analysis Dashboard")
print("=" * 60)


def create_analysis_dashboard(search_results, best_model):
    """Create a comprehensive dashboard combining multiple visualizations."""

    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(3, 4, figure=fig, hspace=0.3, wspace=0.3)

    fig.suptitle('🏔️ Landslide OCCAM Analysis Dashboard', fontsize=18, fontweight='bold')

    # 1. Search progression (top left, 2x2)
    ax1 = fig.add_subplot(gs[0:2, 0:2])
    levels = [m.level for m in search_results]
    infos = [m.information for m in search_results]
    scatter = ax1.scatter(levels, infos, c=[m.bic for m in search_results],
                          cmap='RdYlGn_r', s=80, alpha=0.6)
    ax1.set_xlabel('Search Level', fontweight='bold')
    ax1.set_ylabel('Information (%)', fontweight='bold')
    ax1.set_title('Search Progression')
    plt.colorbar(scatter, ax=ax1, label='BIC')

    # 2. Top models comparison
    ax2 = fig.add_subplot(gs[0, 2:])
    top_models = search_results[:5]
    names = [m.name.split(':')[-1][:8] if ':' in m.name else 'IV' for m in top_models]
    bics = [m.bic for m in top_models]
    bars = ax2.barh(names, bics, color='steelblue')
    ax2.set_xlabel('BIC', fontweight='bold')
    ax2.set_title('Top 5 Models by BIC')
    ax2.invert_yaxis()

    # 3. Best model metrics
    ax3 = fig.add_subplot(gs[1, 2:])
    if best_model:
        metrics = {
            'Info (%)': best_model.information,
            'Alpha×100': best_model.alpha * 100,
            'DF/10': best_model.df / 10
        }
        colors = ['green', 'orange', 'blue']
        bars = ax3.bar(metrics.keys(), metrics.values(), color=colors, alpha=0.7)
        ax3.set_title(f'Best Model: {best_model.name[:20]}...', fontweight='bold')
        ax3.set_ylabel('Normalized Value')
        for bar, val in zip(bars, metrics.values()):
            ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                     f'{val:.1f}', ha='center', fontweight='bold')

    # 4. Distribution plots (bottom row)
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.hist([m.alpha for m in search_results], bins=15,
             color='purple', alpha=0.6, edgecolor='black')
    ax4.set_xlabel('Alpha', fontweight='bold')
    ax4.set_ylabel('Count')
    ax4.set_title('Alpha Distribution')
    ax4.axvline(x=0.05, color='red', linestyle='--', label='α=0.05')
    ax4.legend()

    ax5 = fig.add_subplot(gs[2, 1])
    ax5.hist([m.information for m in search_results], bins=15,
             color='green', alpha=0.6, edgecolor='black')
    ax5.set_xlabel('Information (%)', fontweight='bold')
    ax5.set_ylabel('Count')
    ax5.set_title('Information Distribution')

    ax6 = fig.add_subplot(gs[2, 2])
    ax6.scatter([m.df for m in search_results],
                [m.information for m in search_results],
                alpha=0.5, s=50, c='coral')
    ax6.set_xlabel('Degrees of Freedom', fontweight='bold')
    ax6.set_ylabel('Information (%)', fontweight='bold')
    ax6.set_title('Complexity vs Information')
    ax6.grid(True, alpha=0.3)

    ax7 = fig.add_subplot(gs[2, 3])
    level_counts = {}
    for m in search_results:
        level_counts[m.level] = level_counts.get(m.level, 0) + 1
    colors_pie = plt.cm.Set3(np.linspace(0, 1, len(level_counts)))
    ax7.pie(level_counts.values(), labels=[f'L{k}' for k in level_counts.keys()],
            autopct='%1.0f%%', startangle=90, colors=colors_pie)
    ax7.set_title('Models by Level')

    plt.tight_layout()
    return fig


fig8 = create_analysis_dashboard(search_results, best_bic)
plt.show()
print("✓ Complete dashboard generated")

# ========================================
# VISUALIZATION 9: INTERACTIVE PLOTLY HYPERGRAPH
# ========================================
print("\n" + "=" * 60)
print("VISUALIZATION 9: Interactive Hypergraph (Plotly)")
print("=" * 60)


def create_interactive_hypergraph(model_string, variable_info):
    """Create an interactive hypergraph using Plotly."""

    components = model_string.split(':')
    G = nx.Graph()

    variables = set()
    relations = []

    for comp in components:
        if comp == 'IV':
            continue
        relations.append(comp)
        for char in comp:
            if char.isalpha():
                variables.add(char)

    for var in variables:
        G.add_node(var, node_type='variable',
                   label=variable_info.get(var, var))

    for i, rel in enumerate(relations):
        rel_node = f'R{i}'
        G.add_node(rel_node, node_type='relation', label=rel)
        for char in rel:
            if char.isalpha() and char in variables:
                G.add_edge(char, rel_node)

    pos = nx.spring_layout(G, k=2, iterations=50)

    # Create edge traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    # Create node traces
    var_x = []
    var_y = []
    var_text = []
    rel_x = []
    rel_y = []
    rel_text = []

    for node, data in G.nodes(data=True):
        x, y = pos[node]
        if data['node_type'] == 'variable':
            var_x.append(x)
            var_y.append(y)
            var_text.append(data['label'])
        else:
            rel_x.append(x)
            rel_y.append(y)
            rel_text.append(data['label'])

    var_trace = go.Scatter(
        x=var_x, y=var_y,
        mode='markers+text',
        hoverinfo='text',
        text=var_text,
        textposition='top center',
        marker=dict(size=20, color='lightgreen',
                    line=dict(color='darkgreen', width=2))
    )

    rel_trace = go.Scatter(
        x=rel_x, y=rel_y,
        mode='markers+text',
        hoverinfo='text',
        text=rel_text,
        textposition='top center',
        marker=dict(size=25, color='lightblue', symbol='square')
    )

    fig = go.Figure(data=[edge_trace, var_trace, rel_trace])

    fig.update_layout(
        title=f'🏔️ Interactive Landslide Model: {model_string}',
        showlegend=False,
        hovermode='closest',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        width=800, height=600
    )

    return fig


fig9 = create_interactive_hypergraph(best_bic.name, variable_info)
fig9.show()
print("✓ Interactive hypergraph generated")

# ========================================
# VISUALIZATION 10: GEPHI EXPORT
# ========================================
print("\n" + "=" * 60)
print("VISUALIZATION 10: Gephi Export Files")
print("=" * 60)


def generate_gephi_files(model_string, variable_info):
    """Generate Gephi-compatible CSV files for external visualization."""

    components = model_string.split(':')

    nodes_csv = "ID,Label,Type,Size\n"
    edges_csv = "Source,Target,Weight\n"

    variables = set()
    relations = []

    for comp in components:
        if comp == 'IV':
            continue
        relations.append(comp)
        for char in comp:
            if char.isalpha():
                variables.add(char)

    # Add variable nodes
    for var in variables:
        label = variable_info.get(var, var)
        nodes_csv += f"{var},{label},Variable,10\n"

    # Add relation nodes and edges
    for i, rel in enumerate(relations):
        rel_id = f"R{i}"
        nodes_csv += f"{rel_id},{rel},HyperEdge,4\n"

        # Add edges
        for char in rel:
            if char.isalpha() and char in variables:
                edges_csv += f"{char},{rel_id},1\n"

    return nodes_csv, edges_csv


nodes_csv, edges_csv = generate_gephi_files(best_bic.name, variable_info)
print("Gephi Nodes Table (first 5 lines):")
print('\n'.join(nodes_csv.split('\n')[:6]))
print("\nGephi Edges Table (first 5 lines):")
print('\n'.join(edges_csv.split('\n')[:6]))
print("✓ Gephi export files generated")

# Save to files
with open('landslides_gephi_nodes.csv', 'w') as f:
    f.write(nodes_csv)
with open('landslides_gephi_edges.csv', 'w') as f:
    f.write(edges_csv)

# ========================================
# SUMMARY
# ========================================
print("\n" + "=" * 60)
print("VISUALIZATION DEMONSTRATION COMPLETE")
print("=" * 60)
print("\n📊 Generated Visualizations:")
print("  1. Search Results Dashboard - 4 panel analysis")
print("  2. Hypergraph - Model structure visualization")
print("  3. Confusion Matrix - With performance metrics")
print("  4. 3D Model Space - Complexity/Information/Quality")
print("  5. Radar Chart - Multi-metric model comparison")
print("  6. Search Tree - Level-based progression")
print("  7. Selection Criteria - BIC/AIC/Pareto analysis")
print("  8. Complete Dashboard - Comprehensive overview")
print("  9. Interactive Hypergraph - Plotly version")
print(" 10. Gephi Export - Network analysis files")
print("\n🏔️ Landslide Model Insights:")
print(f"  Best model: {best_bic.name}")
print(f"  Information captured: {best_bic.information:.1f}%")
print(f"  Significance: α = {best_bic.alpha:.4f}")
print(f"  Model complexity: {best_bic.df} degrees of freedom")
print("\n✅ All visualizations successfully demonstrated!")

# Optional: Save all figures
if input("\nSave all figures? (y/n): ").lower() == 'y':
    import os

    os.makedirs('landslides_visualizations', exist_ok=True)

    figs = [
        (fig1, 'search_dashboard'),
        (fig2, 'hypergraph'),
        (fig3, 'confusion_matrix'),
        (fig4, 'model_space_3d'),
        (fig5, 'radar_comparison'),
        (fig6, 'search_tree'),
        (fig7, 'selection_criteria'),
        (fig8, 'complete_dashboard')
    ]

    for fig, name in figs:
        fig.savefig(f'landslides_visualizations/{name}.png', dpi=150, bbox_inches='tight')

    fig9.write_html('landslides_visualizations/interactive_hypergraph.html')

    print(f"\n✓ All figures saved to landslides_visualizations/")