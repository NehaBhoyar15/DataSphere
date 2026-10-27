import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
                              QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem)
from widgets.chart_widget import ChartWidget
from widgets.data_table import DataTable
from widgets.notification import NotificationBanner


class ClusteringPage(QWidget):
    def __init__(self, data_service, parent=None):
        super().__init__(parent); self.data_service = data_service
        root = QVBoxLayout(self); title = QLabel("Clustering, anomalies & PCA"); title.setObjectName("pageTitle"); root.addWidget(title)
        controls = QHBoxLayout(); self.method = QComboBox(); self.method.addItems(["K-Means", "DBSCAN"]); self.k = QSpinBox(); self.k.setRange(2, 8); self.k.setValue(3); self.components = QSpinBox(); self.components.setRange(2, 3); self.components.setValue(2); self.overlay = QCheckBox("Cluster overlay"); self.overlay.setChecked(True)
        run = QPushButton("Run analysis"); run.clicked.connect(self.run); elbow = QPushButton("Elbow curve"); elbow.clicked.connect(self.elbow)
        for label, widget in [("Method", self.method), ("Clusters", self.k), ("PCA components", self.components)]: controls.addWidget(QLabel(label)); controls.addWidget(widget)
        controls.addWidget(self.overlay); controls.addWidget(run); controls.addWidget(elbow); root.addLayout(controls)
        self.banner = NotificationBanner("Analyze numeric columns with local demo fallbacks."); root.addWidget(self.banner)
        row = QHBoxLayout(); self.chart = ChartWidget(); self.elbow_chart = ChartWidget(); row.addWidget(self.chart); row.addWidget(self.elbow_chart); root.addLayout(row, 2)
        self.table = DataTable()
        self.profile = QTableWidget(0, 0)
        tables = QHBoxLayout(); tables.addWidget(self.table, 2); tables.addWidget(self.profile, 1)
        root.addLayout(tables, 1); self.run()

    def numeric(self):
        return self.data_service.data.select_dtypes(include="number").dropna()

    def run(self):
        try:
            frame = self.numeric()
            if frame.shape[1] < 2: raise ValueError("Need at least two numeric columns.")
            X = frame.to_numpy()
            from sklearn.preprocessing import StandardScaler
            from sklearn.cluster import KMeans, DBSCAN
            from sklearn.decomposition import PCA
            from sklearn.ensemble import IsolationForest
            scaled = StandardScaler().fit_transform(X)
            labels = KMeans(n_clusters=self.k.value(), random_state=42, n_init=10).fit_predict(scaled) if self.method.currentText() == "K-Means" else DBSCAN(eps=1.2, min_samples=5).fit_predict(scaled)
            pca = PCA(n_components=2).fit_transform(scaled)
            anomaly = IsolationForest(random_state=42, contamination=.08).fit_predict(scaled) == -1
            self.chart.ax.clear()
            colors = labels if self.overlay.isChecked() else np.zeros(len(labels))
            self.chart.ax.scatter(pca[:, 0], pca[:, 1], c=colors, cmap="viridis", s=35)
            if anomaly.any():
                self.chart.ax.scatter(pca[anomaly, 0], pca[anomaly, 1], facecolors="none", edgecolors="#f87171", s=100, linewidths=1.5, label="Anomaly")
                self.chart.ax.legend()
            self.chart.ax.set_title("2D PCA • cluster labels"); self.chart.apply_theme(); self.chart.canvas.draw_idle()
            shown = frame.copy(); shown["Cluster"] = labels; shown["Anomaly"] = anomaly
            self.table.set_frame(shown, "Anomaly")
            profiles = shown.groupby("Cluster")[list(frame.columns)].mean().round(2)
            self.profile.setRowCount(len(profiles)); self.profile.setColumnCount(len(profiles.columns) + 1)
            self.profile.setHorizontalHeaderLabels(["Cluster"] + [str(c) for c in profiles.columns])
            for row, (cluster, values) in enumerate(profiles.iterrows()):
                self.profile.setItem(row, 0, QTableWidgetItem(str(cluster)))
                for col, value in enumerate(values, 1): self.profile.setItem(row, col, QTableWidgetItem(str(value)))
            self.profile.resizeColumnsToContents()
            score = "—"
            try:
                from sklearn.metrics import silhouette_score
                score = f"{silhouette_score(scaled, labels):.3f}" if len(set(labels)) > 1 else "single cluster"
            except Exception: pass
            explained = f"{(np.var(pca[:, 0]) + np.var(pca[:, 1])) / np.var(scaled):.1%}"
            self.banner.setText(f"{self.method.currentText()} complete • {len(frame)} rows • silhouette score: {score} • PCA variance: {explained} • {int(anomaly.sum())} anomalies flagged.")
            self.banner.set_level("warning" if anomaly.any() else "success")
        except ImportError:
            self.banner.setText("scikit-learn is needed for clustering. Install requirements.txt."); self.banner.set_level("error")
        except Exception as exc:
            self.banner.setText(str(exc)); self.banner.set_level("error")

    def elbow(self):
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import silhouette_score
            X = StandardScaler().fit_transform(self.numeric())
            ks = range(2, 8); scores = [KMeans(n_clusters=k, random_state=42, n_init=10).fit(X).inertia_ for k in ks]
            self.elbow_chart.ax.clear(); self.elbow_chart.ax.plot(list(ks), scores, marker="o", color="#f59e0b"); self.elbow_chart.ax.set_title("Elbow curve"); self.elbow_chart.ax.set_xlabel("K"); self.elbow_chart.ax.set_ylabel("Inertia"); self.elbow_chart.apply_theme(); self.elbow_chart.canvas.draw_idle()
        except Exception as exc: self.banner.setText(str(exc)); self.banner.set_level("error")