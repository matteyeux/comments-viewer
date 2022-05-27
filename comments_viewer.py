import binaryninjaui

from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QTreeView


class CommentsViewerDialog(QDialog):
    def __init__(self, bv):
        super(CommentsViewerDialog, self).__init__()
        self.bv = bv

        # UI
        self.comments_model = CommentsModel(bv)

        self.match_view = QTreeView()
        self.match_view.setModel(self.comments_model)

        self.match_view.setSelectionMode(QTreeView.ExtendedSelection)

        self.match_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.match_view.doubleClicked.connect(self.match_view_double_clicked)

        self.match_view.setRootIsDecorated(False)
        self.match_view.setFont(binaryninjaui.getMonospaceFont(self))

        for i in range(len(self.comments_model.comments_info)):
            self.match_view.resizeColumnToContents(i)

        self.match_view.setSortingEnabled(True)
        self.match_view.sortByColumn(0, Qt.AscendingOrder)

        layout = QVBoxLayout()
        layout.addWidget(self.match_view)

        self.setLayout(layout)
        self.setWindowTitle("Comments Viewer")
        self.resize(700, 350)
        flags = self.windowFlags()
        flags |= Qt.WindowMaximizeButtonHint
        flags &= ~Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)

    def match_view_double_clicked(self, index):
        if not index.isValid():
            assert False
            return
        entry = self.comments_model.entries[index.row()]
        address = entry["address"]
        self.bv.navigate(self.bv.file.view, address)

class CommentsModel(QAbstractItemModel):
    def __init__(self, bv):
        super(CommentsModel, self).__init__()

        def col_field(key, default=None):
            def f(i):
                entry = self.entries[i]
                result = entry[key]
                if result is None:
                    return default
                return result

            return f

        def col_field_fmt(key, fmt):
            return lambda i: fmt.format(self.entries[i][key])

        def col_addr_field(key):
            return lambda i: "{:x}".format(self.entries[i][key])

        # Column name, sort key, display function
        self.comments_info = [
            ("Address", "address", col_addr_field("address")),
            ("Function", "function", col_field("function")),
            ("Comment", "comment", col_field("comment")),
        ]

        self.entries = []

        for function in bv.functions:
            for addr in function.comments.keys():
                entry = {}
                entry["address"] = addr
                entry["function"] = function.name
                entry["comment"] = function.comments[addr]
                self.entries.append(entry)

    def index(self, row, col, parent):
        if parent.isValid():
            # No children
            return QModelIndex()

        if row >= len(self.entries):
            return QModelIndex()
        if col >= len(self.comments_info):
            return QModelIndex()

        return self.createIndex(row, col)

    def parent(self, index):
        # Flat tree, no parent
        return QModelIndex()

    def rowCount(self, parent):
        # No children
        if parent.isValid():
            return 0
        return len(self.entries)

    def columnCount(self, parent):
        return len(self.comments_info)

    def data(self, index, role):
        if index.row() >= len(self.entries):
            return None

        name, key, display = self.comments_info[index.column()]
        if role == Qt.DisplayRole:
            return display(index.row())
        return None

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation != Qt.Horizontal:
            return None

        name, key, display = self.comments_info[section]
        return name

    def sort(self, col, order):
        self.beginResetModel()

        name, key, display = self.comments_info[col]
        self.entries.sort(key=lambda k: k[key], reverse=(order != Qt.AscendingOrder))

        self.endResetModel()


def view_comments(bv):
    # Qt
    assert QApplication.instance() is not None

    global dialog
    dialog = CommentsViewerDialog(bv)
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
