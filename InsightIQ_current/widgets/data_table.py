
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QTableView,
    QHeaderView,
    QAbstractItemView,
)


class DataFrameModel(QAbstractTableModel):
    def __init__(self, frame=None, anomaly_column=None):
        super().__init__()
        self.frame = frame
        self.anomaly_column = anomaly_column

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid() or self.frame is None:
            return 0
        return len(self.frame.index)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid() or self.frame is None:
            return 0
        return len(self.frame.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or self.frame is None:
            return None

        value = self.frame.iloc[index.row(), index.column()]

        if role == Qt.DisplayRole:
            return str(value)

        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignVCenter | Qt.AlignLeft)

        if (
            role == Qt.BackgroundRole
            and self.anomaly_column in self.frame.columns
        ):
            if bool(self.frame.iloc[index.row()][self.anomaly_column]):
                return QColor("#FCE7F3")

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole or self.frame is None:
            return None

        if orientation == Qt.Horizontal:
            return str(self.frame.columns[section])

        return str(section + 1)


class DataTable(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.ElideRight)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.setShowGrid(False)
        self.setCornerButtonEnabled(False)

        self.verticalHeader().setVisible(True)
        self.verticalHeader().setDefaultSectionSize(38)
        self.verticalHeader().setMinimumWidth(42)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(125)
        header.setDefaultSectionSize(165)
        header.setStretchLastSection(False)

        self.setStyleSheet("""
            QTableView {
                background-color: #FFFFFF;
                alternate-background-color: #FAF8FF;
                color: #403354;
                border: 1px solid #E8DFF8;
                border-radius: 10px;
                gridline-color: #F0EAF8;
                selection-background-color: #E9DFFC;
                selection-color: #403354;
                font-size: 10pt;
                outline: none;
            }

            QTableView::item {
                padding: 8px 12px;
                border-bottom: 1px solid #F0EAF8;
            }

            QTableView::item:hover {
                background-color: #F3EEFF;
            }

            QHeaderView::section {
                background-color: #F1EBFC;
                color: #5D477D;
                padding: 12px 10px;
                border: none;
                border-bottom: 1px solid #E2D6F5;
                font-weight: 600;
                font-size: 10pt;
            }

            QHeaderView::section:hover {
                background-color: #EAE0FA;
            }

            QScrollBar:horizontal,
            QScrollBar:vertical {
                background-color: #F8F5FD;
                border: none;
                border-radius: 5px;
                margin: 2px;
            }

            QScrollBar:horizontal {
                height: 10px;
            }

            QScrollBar:vertical {
                width: 10px;
            }

            QScrollBar::handle:horizontal,
            QScrollBar::handle:vertical {
                background-color: #D5C6F0;
                border-radius: 5px;
                min-width: 30px;
                min-height: 30px;
            }

            QScrollBar::handle:horizontal:hover,
            QScrollBar::handle:vertical:hover {
                background-color: #BCA7E8;
            }

            QScrollBar::add-line,
            QScrollBar::sub-line {
                width: 0px;
                height: 0px;
            }
        """)

    def set_frame(self, frame, anomaly_column=None):
        self.setSortingEnabled(False)
        self.setModel(DataFrameModel(frame, anomaly_column))

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultSectionSize(165)

        if frame is not None:
            for column, name in enumerate(frame.columns):
                column_name = str(name).lower().replace("_", " ")

                if "product" in column_name or "category" in column_name:
                    width = 190
                elif "date" in column_name:
                    width = 155
                elif "revenue" in column_name:
                    width = 165
                elif "region" in column_name:
                    width = 145
                elif "units" in column_name or "quantity" in column_name:
                    width = 140
                else:
                    width = 165

                self.setColumnWidth(column, width)

        self.setSortingEnabled(True)
id="fnt0nd"
