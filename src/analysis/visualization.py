import matplotlib
# Use 'Agg' backend for non-interactive plotting (headless)
# This prevents "Starting a Matplotlib GUI outside of the main thread" warnings/errors
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
import re

class Visualizer:
    MAX_HEATMAP_CLUSTER_ROWS = 500
    MAX_HEATMAP_TICK_LABELS = 100

    @staticmethod
    def _format_group_label(group_value, *, prefix_cluster: bool) -> str:
        if prefix_cluster:
            try:
                return f"Cluster {int(group_value)}"
            except Exception:
                return f"Cluster {group_value}"
        return str(group_value)
    @staticmethod
    def plot_heatmap(data, labels, feature_names, output_path, dpi=300, cmap="Spectral_r"):
        """
        Generates heatmap of cluster mean expression levels.
        """
        df = pd.DataFrame(data, columns=feature_names)
        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.replace([np.inf, -np.inf], np.nan)
        df['Cluster'] = labels

        cluster_means = df.groupby('Cluster').mean(numeric_only=True)
        cluster_means = cluster_means.replace([np.inf, -np.inf], np.nan)

        # Drop fully invalid columns/rows first; scipy linkage requires finite input.
        cluster_means = cluster_means.dropna(axis=1, how='all').dropna(axis=0, how='all')
        if cluster_means.empty:
            raise ValueError("Heatmap data contains no valid numeric values after cleaning.")

        # Fill remaining gaps with the column mean so hierarchical clustering receives finite values.
        cluster_means = cluster_means.apply(lambda col: col.fillna(col.mean()), axis=0)
        cluster_means = cluster_means.fillna(0.0)

        col_min = cluster_means.min(axis=0)
        col_range = cluster_means.max(axis=0) - col_min
        normalized = cluster_means.subtract(col_min, axis=1)
        normalized = normalized.divide(col_range.replace(0, np.nan), axis=1)
        normalized = normalized.fillna(0.0)

        if not np.isfinite(normalized.to_numpy()).all():
            raise ValueError("Heatmap normalization produced non-finite values.")

        row_cluster = 1 < normalized.shape[0] <= Visualizer.MAX_HEATMAP_CLUSTER_ROWS
        col_cluster = normalized.shape[1] > 1

        g = sns.clustermap(
            normalized,
            cmap=cmap,
            figsize=(12, 10),
            annot=False,
            row_cluster=row_cluster,
            col_cluster=col_cluster,
            dendrogram_ratio=(0.05, 0.05),
            tree_kws={'linewidths': 1.5},
            cbar_kws={'label': 'Normalized intensity', 'orientation': 'vertical'},
        )

        # Seaborn reorders heatmap rows after hierarchical clustering.
        # Explicitly reset tick positions and labels from the reordered index
        # so the cluster labels on the right match each heatmap row exactly.
        row_order = g.dendrogram_row.reordered_ind if g.dendrogram_row is not None else list(range(normalized.shape[0]))
        ordered_labels = normalized.index.to_numpy()[row_order]
        g.ax_heatmap.set_yticks(np.arange(len(ordered_labels)) + 0.5)
        if len(ordered_labels) <= Visualizer.MAX_HEATMAP_TICK_LABELS:
            g.ax_heatmap.set_yticklabels([str(label) for label in ordered_labels], rotation=0)
        else:
            g.ax_heatmap.set_yticklabels([])
        g.ax_heatmap.yaxis.tick_right()
        g.ax_heatmap.yaxis.set_label_position("right")
        g.ax_heatmap.tick_params(axis='y', length=0, pad=2, labelsize=9)
        g.ax_heatmap.set_ylabel("Cluster")
        
        # Adjust colorbar
        # The colorbar is in g.cax
        g.cax.set_title("Normalized\nintensity", fontsize=10, loc='left', pad=10)
        # Remove the default label set by cbar_kws if we want custom title placement
        g.cax.set_ylabel("") 
        
        # Move colorbar to Top-Right corner of the figure
        # Fixed position to ensure it doesn't overlap with the heatmap
        # [left, bottom, width, height] in figure coordinates (0-1)
        # Position: Even further right (1.02 to be outside main plot area if needed, 
        # but 0.95 is safer inside figure bounds)
        # Previous was 0.9, 0.8. The heatmap extends to right.
        # Let's move it further right.
        g.cax.set_position([0.98, 0.8, 0.02, 0.15])
        
        # Add black border to colorbar
        # g.cax is an Axes object, we can add a patch or set spines
        # Setting outline via spines
        for spine in g.cax.spines.values():
            spine.set_visible(True)
            spine.set_color('black')
            spine.set_linewidth(1)
            
        # Ensure ticks are visible and styled
        g.cax.tick_params(labelsize=8, color='black', width=1, length=3)
        
        # Save
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()
        
    @staticmethod
    def _get_high_contrast_palette(n_clusters):
        """
        Generate a high-contrast palette for large number of clusters.
        Combines multiple distinct palettes to maximize visual difference.
        """
        if n_clusters <= 20:
            return sns.color_palette("tab20", n_clusters)
        
        # Strategy: Combine tab20, tab20b, tab20c for up to 60 colors
        # These palettes are designed for categorical data and offer better contrast than husl
        palettes = []
        for name in ["tab20", "tab20b", "tab20c"]:
            palettes.extend(sns.color_palette(name))
            
        if n_clusters <= len(palettes):
            return palettes[:n_clusters]
        
        # If > 60, fallback to husl but shuffle to avoid adjacent similarities
        import random
        # Use fixed seed for reproducibility
        rng = random.Random(42)
        
        # Generate ample colors
        colors = sns.color_palette("husl", n_clusters)
        # Convert to list to shuffle
        colors = list(colors)
        rng.shuffle(colors)
        
        return colors

    @staticmethod
    def _sanitize_filename_part(value):
        text = str(value).strip()
        text = re.sub(r'[<>:"/\\|?*]+', "_", text)
        text = re.sub(r"\s+", "_", text)
        return text[:80] or "Unknown"

    @staticmethod
    def _infer_embedding_axis_labels(output_path):
        path_str = str(output_path).lower()
        if "umap" in path_str:
            return "UMAP1", "UMAP2"
        if "tsne" in path_str or "t-sne" in path_str:
            return "tSNE1", "tSNE2"
        return "Dim 1", "Dim 2"

    @staticmethod
    def _style_embedding_axes(ax, x_label, y_label):
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(0.05, 0.02, x_label, transform=ax.transAxes,
                fontsize=14, fontweight='normal', va='bottom', ha='left')
        ax.annotate('', xy=(0.2, 0.028), xytext=(0.12, 0.028), xycoords='axes fraction',
                    arrowprops=dict(arrowstyle="->", color='black', lw=1.5))
        ax.text(0.02, 0.05, y_label, transform=ax.transAxes,
                fontsize=14, fontweight='normal', va='bottom', ha='left', rotation=90)
        ax.annotate('', xy=(0.028, 0.2), xytext=(0.028, 0.12), xycoords='axes fraction',
                    arrowprops=dict(arrowstyle="->", color='black', lw=1.5))

    @staticmethod
    def plot_embedding_2d(embedding, labels, output_path, dpi=300):
        x_label, y_label = Visualizer._infer_embedding_axis_labels(output_path)

        plt.figure(figsize=(10, 10))
        labels = np.asarray(labels)
        unique_labels = np.unique(labels)
        n_clusters = len(unique_labels)

        prefix_cluster = np.issubdtype(labels.dtype, np.number)
        
        # Use optimized palette
        palette = Visualizer._get_high_contrast_palette(n_clusters)
        
        for i, label in enumerate(unique_labels):
            mask = labels == label
            # Increased alpha to 1.0 and adjusted size for clearer points
            # Removed edgecolors to avoid outlining artifacts
            # linewidths=0 explicitly disables edge drawing
            plt.scatter(embedding[mask, 0], embedding[mask, 1], 
                        c=[palette[i]], label=Visualizer._format_group_label(label, prefix_cluster=prefix_cluster), 
                        s=8, alpha=1.0, edgecolors='none', linewidths=0)
            
        ax = plt.gca()
        Visualizer._style_embedding_axes(ax, x_label, y_label)
        
        # Custom legend positioned below the plot
        import matplotlib.lines as mlines
        
        # Create legend handles
        legend_handles = []
        for i, label in enumerate(unique_labels):
            # Create a custom circular marker handle
            handle = mlines.Line2D([], [], color='white', marker='o', 
                                   markerfacecolor=palette[i], markersize=10, 
                                   label=Visualizer._format_group_label(label, prefix_cluster=prefix_cluster))
            legend_handles.append(handle)
        
        # Calculate number of columns for legend (e.g. 5 columns like in reference)
        n_cols = 5
        
        # Add legend below the plot
        # bbox_to_anchor=(0.5, -0.05) centers it below axis
        # loc='upper center' aligns the top-center of legend box to that anchor
        ax.legend(handles=legend_handles, loc='upper center', 
                  bbox_to_anchor=(0.5, 0.0), ncol=n_cols, 
                  frameon=False, fontsize=10, handletextpad=0.1)
        
        # Adjust layout to make room for legend
        plt.tight_layout()
        # Add extra space at bottom for legend
        plt.subplots_adjust(bottom=0.15)
        
        plt.savefig(output_path, dpi=dpi)
        plt.close()

    @staticmethod
    def plot_embedding_2d_highlight_series(embedding, labels, output_dir, prefix, dpi=300):
        labels = np.asarray(labels)
        unique_labels = np.unique(labels)
        if len(unique_labels) == 0:
            return []

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        x_label, y_label = Visualizer._infer_embedding_axis_labels(prefix)
        palette = Visualizer._get_high_contrast_palette(len(unique_labels))
        color_map = {label: palette[i] for i, label in enumerate(unique_labels)}
        saved_paths = []

        for label in unique_labels:
            fig, ax = plt.subplots(figsize=(10, 10))
            mask = labels == label
            ax.scatter(
                embedding[~mask, 0], embedding[~mask, 1],
                c=['#c0c0c0'], s=8, alpha=0.35, edgecolors='none', linewidths=0,
            )
            ax.scatter(
                embedding[mask, 0], embedding[mask, 1],
                c=[color_map[label]], s=10, alpha=1.0, edgecolors='none', linewidths=0,
                label=str(label),
            )
            Visualizer._style_embedding_axes(ax, x_label, y_label)
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, 0.0), ncol=1,
                      frameon=False, fontsize=10, handletextpad=0.1)
            plt.tight_layout()
            plt.subplots_adjust(bottom=0.12)

            file_name = f"{prefix}_{Visualizer._sanitize_filename_part(label)}.png"
            output_path = output_dir / file_name
            plt.savefig(output_path, dpi=dpi)
            plt.close(fig)
            saved_paths.append(str(output_path))

        return saved_paths

    @staticmethod
    def plot_embedding_3d(embedding, labels, output_path, dpi=300):
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        labels = np.asarray(labels)
        unique_labels = np.unique(labels)
        n_clusters = len(unique_labels)

        prefix_cluster = np.issubdtype(labels.dtype, np.number)
        
        palette = Visualizer._get_high_contrast_palette(n_clusters)
        
        for i, label in enumerate(unique_labels):
            mask = labels == label
            # Increased alpha to 1.0 and adjusted size
            ax.scatter(embedding[mask, 0], embedding[mask, 1], embedding[mask, 2],
                       c=[palette[i]], label=Visualizer._format_group_label(label, prefix_cluster=prefix_cluster), 
                       s=8, alpha=1.0, edgecolors='none', linewidths=0)
            
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', ncol=1 if n_clusters <= 20 else 2)
        ax.set_title("3D Dimensionality Reduction")
        ax.set_xlabel("Dim 1")
        ax.set_ylabel("Dim 2")
        ax.set_zlabel("Dim 3")
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi)
        plt.close()

    @staticmethod
    def plot_percentage_stacked_bar_chart(percentages_df, output_path, dpi=300):
        df = pd.DataFrame(percentages_df).copy()
        if df.shape[0] == 0 or df.shape[1] == 0:
            raise ValueError("No data available for plotting.")

        n_samples = df.shape[0]
        fig_width = max(10, 1.2 * n_samples + 2)
        fig_height = 7

        colors = Visualizer._get_high_contrast_palette(df.shape[1])

        ax = df.plot(kind="bar", stacked=True, figsize=(fig_width, fig_height), color=colors, width=0.8)
        ax.set_ylabel("Percentage (%)")
        ax.set_xlabel("Sample")
        ax.set_ylim(0, 100)
        ax.legend(title="Cell Type", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
        plt.close()
