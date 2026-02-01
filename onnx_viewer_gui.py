#!/usr/bin/env python3
"""
ONNX模型信息探索器 - GUI应用程序
用于探索和显示ONNX模型的详细信息
"""

import sys
import onnx
from collections import defaultdict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QSplitter, QFrame,
    QHeaderView, QTabWidget, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ONNXModelExplorer(QMainWindow):
    """ONNX模型信息探索器主窗口"""

    def __init__(self):
        super().__init__()
        self.model = None
        self.model_path = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("ONNX模型信息探索器 v2.0")
        self.resize(1000, 700)

        # 主容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 顶部文件选择区域
        file_panel = self.create_file_panel()
        main_layout.addWidget(file_panel)

        # 主内容区域（使用分割器）
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：模型结构树
        left_panel = self.create_structure_panel()
        splitter.addWidget(left_panel)

        # 右侧：详细信息标签页
        right_panel = self.create_detail_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # 状态栏
        self.statusBar().showMessage("请加载ONNX模型文件 | 版本 2.0.0")

    def create_file_panel(self):
        """创建文件选择面板"""
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        panel.setMaximumHeight(80)

        layout = QHBoxLayout(panel)

        # 标签
        label = QLabel("模型文件:")
        label.setFont(QFont("Arial", 11))
        layout.addWidget(label)

        # 文件路径输入框
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("选择 .onnx 模型文件...")
        self.file_path_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(self.file_path_edit)

        # 浏览按钮
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self.browse_file)
        layout.addWidget(browse_btn)

        # 加载按钮
        self.load_btn = QPushButton("加载模型")
        self.load_btn.setFixedWidth(120)
        self.load_btn.clicked.connect(self.load_model)
        layout.addWidget(self.load_btn)

        return panel

    def create_structure_panel(self):
        """创建模型结构面板"""
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(panel)

        # 标题
        title = QLabel("模型结构")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # 树形控件
        self.structure_tree = QTreeWidget()
        self.structure_tree.setHeaderLabel("节点层级")
        self.structure_tree.itemClicked.connect(self.on_tree_item_clicked)
        layout.addWidget(self.structure_tree)

        return panel

    def create_detail_panel(self):
        """创建详细信息面板"""
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(panel)

        # 标题
        title = QLabel("详细信息")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # 标签页控件
        self.tab_widget = QTabWidget()

        # 概览标签页
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        self.overview_text = QTextEdit()
        self.overview_text.setReadOnly(True)
        self.overview_text.setFont(QFont("Consolas", 9))
        overview_layout.addWidget(self.overview_text)
        self.tab_widget.addTab(overview_tab, "概览")

        # 输入输出标签页
        io_tab = QWidget()
        io_layout = QVBoxLayout(io_tab)
        self.io_table = QTableWidget()
        self.io_table.setColumnCount(4)
        self.io_table.setHorizontalHeaderLabels(["名称", "类型", "形状", "数据类型"])
        self.io_table.horizontalHeader().setStretchLastSection(True)
        io_layout.addWidget(self.io_table)
        self.tab_widget.addTab(io_tab, "输入/输出")

        # 节点详情标签页
        node_tab = QWidget()
        node_layout = QVBoxLayout(node_tab)
        self.node_detail_text = QTextEdit()
        self.node_detail_text.setReadOnly(True)
        self.node_detail_text.setFont(QFont("Consolas", 9))
        node_layout.addWidget(self.node_detail_text)
        self.tab_widget.addTab(node_tab, "节点详情")

        # 图形属性标签页
        graph_tab = QWidget()
        graph_layout = QVBoxLayout(graph_tab)
        self.graph_text = QTextEdit()
        self.graph_text.setReadOnly(True)
        self.graph_text.setFont(QFont("Consolas", 9))
        graph_layout.addWidget(self.graph_text)
        self.tab_widget.addTab(graph_tab, "图属性")

        layout.addWidget(self.tab_widget)

        return panel

    def browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择ONNX模型文件", "", "ONNX模型 (*.onnx);;所有文件 (*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def load_model(self):
        """加载ONNX模型"""
        file_path = self.file_path_edit.text()
        if not file_path:
            self.statusBar().showMessage("[!] 请先选择模型文件")
            return

        try:
            self.statusBar().showMessage("[*] 正在加载模型...")
            onnx.checker.check_model(file_path)
            self.model = onnx.load(file_path)
            self.model_path = file_path

            # 更新UI
            self.update_overview()
            self.update_io_table()
            self.update_structure_tree()
            self.update_graph_info()
            self.clear_node_detail()

            self.statusBar().showMessage(f"[OK] 模型加载成功: {file_path}")

        except Exception as e:
            self.statusBar().showMessage(f"[X] 加载失败: {str(e)}")
            self.overview_text.clear()
            self.overview_text.append(f"[X] 错误: {str(e)}")

    def update_overview(self):
        """更新概览信息"""
        if not self.model:
            return

        info = []
        info.append("=" * 50)
        info.append("ONNX 模型概览")
        info.append("=" * 50)
        info.append(f"\n[*] 文件路径: {self.model_path}")

        # 模型信息
        info.append(f"\n[*] 元数据:")
        graph = self.model.graph

        info.append(f"  - 模型名称: {self.model.graph.name}")

        if self.model.metadata_props:
            info.append(f"  - 元数据属性:")
            for prop in self.model.metadata_props:
                info.append(f"    - {prop.key}: {prop.value}")

        # Opset信息
        info.append(f"\n[*] Opset信息:")
        for opset in self.model.opset_import:
            domain = opset.domain if opset.domain else "默认域"
            info.append(f"  - {domain}: version {opset.version}")

        # 图信息
        info.append(f"\n[*] 图统计:")
        info.append(f"  - 输入数量: {len(graph.input)}")
        info.append(f"  - 输出数量: {len(graph.output)}")
        info.append(f"  - 节点数量: {len(graph.node)}")
        info.append(f"  - 初始值数量: {len(graph.initializer)}")

        # 按操作类型统计
        op_count = defaultdict(int)
        for node in graph.node:
            op_count[node.op_type] += 1

        info.append(f"\n[*] 操作类型统计 (共 {len(op_count)} 种):")
        for op_type, count in sorted(op_count.items(), key=lambda x: -x[1]):
            info.append(f"  - {op_type}: {count}")

        # IR版本
        info.append(f"\n[*] IR版本: {self.model.ir_version}")

        # 生产者信息
        if self.model.producer_name:
            info.append(f"\n[*] 生产者: {self.model.producer_name} {self.model.producer_version or ''}")

        self.overview_text.clear()
        self.overview_text.append("\n".join(info))

    def update_io_table(self):
        """更新输入输出表格"""
        if not self.model:
            return

        self.io_table.setRowCount(0)

        graph = self.model.graph

        # 添加输入
        for input_tensor in graph.input:
            row = self.io_table.rowCount()
            self.io_table.insertRow(row)
            self.io_table.setItem(row, 0, QTableWidgetItem(input_tensor.name))
            self.io_table.setItem(row, 1, QTableWidgetItem("输入"))

            # 获取形状
            shape = self.get_tensor_shape(input_tensor)
            self.io_table.setItem(row, 2, QTableWidgetItem(str(shape)))

            # 获取数据类型
            dtype = self.get_dtype_name(input_tensor.type.tensor_type.elem_type)
            self.io_table.setItem(row, 3, QTableWidgetItem(dtype))

        # 添加输出
        for output_tensor in graph.output:
            row = self.io_table.rowCount()
            self.io_table.insertRow(row)
            self.io_table.setItem(row, 0, QTableWidgetItem(output_tensor.name))
            self.io_table.setItem(row, 1, QTableWidgetItem("输出"))

            # 获取形状
            shape = self.get_tensor_shape(output_tensor)
            self.io_table.setItem(row, 2, QTableWidgetItem(str(shape)))

            # 获取数据类型
            dtype = self.get_dtype_name(output_tensor.type.tensor_type.elem_type)
            self.io_table.setItem(row, 3, QTableWidgetItem(dtype))

        # 调整列宽
        self.io_table.resizeColumnsToContents()

    def update_structure_tree(self):
        """更新结构树"""
        if not self.model:
            return

        self.structure_tree.clear()

        graph = self.model.graph

        # 添加输入节点
        input_item = QTreeWidgetItem(["[IN] 输入"])
        for input_tensor in graph.input:
            shape = self.get_tensor_shape(input_tensor)
            dtype = self.get_dtype_name(input_tensor.type.tensor_type.elem_type)
            item = QTreeWidgetItem([f"{input_tensor.name}\n{shape} | {dtype}"])
            item.setData(0, Qt.UserRole, {"type": "input", "tensor": input_tensor})
            input_item.addChild(item)
        self.structure_tree.addTopLevelItem(input_item)

        # 按操作类型分组节点
        op_groups = defaultdict(list)
        for node in graph.node:
            op_groups[node.op_type].append(node)

        # 添加节点
        nodes_item = QTreeWidgetItem(["[OP] 节点"])
        for op_type in sorted(op_groups.keys()):
            op_item = QTreeWidgetItem([f"{op_type} ({len(op_groups[op_type])})"])
            for node in op_groups[op_type]:
                inputs = ", ".join(node.input) if node.input else "无"
                outputs = ", ".join(node.output) if node.output else "无"
                item_text = f"{node.name}\n输入: {inputs}\n输出: {outputs}"
                item = QTreeWidgetItem([item_text])
                item.setData(0, Qt.UserRole, {"type": "node", "node": node})
                op_item.addChild(item)
            nodes_item.addChild(op_item)
        self.structure_tree.addTopLevelItem(nodes_item)

        # 添加初始值
        if graph.initializer:
            init_item = QTreeWidgetItem(["[W] 初始值 (权重)"])
            for init in graph.initializer:
                dtype = self.get_dtype_name(init.data_type)
                item = QTreeWidgetItem([f"{init.name}\n形状: {list(init.dims)} | {dtype}"])
                item.setData(0, Qt.UserRole, {"type": "initializer", "tensor": init})
                init_item.addChild(item)
            self.structure_tree.addTopLevelItem(init_item)

        # 添加输出节点
        output_item = QTreeWidgetItem(["[OUT] 输出"])
        for output_tensor in graph.output:
            shape = self.get_tensor_shape(output_tensor)
            dtype = self.get_dtype_name(output_tensor.type.tensor_type.elem_type)
            item = QTreeWidgetItem([f"{output_tensor.name}\n{shape} | {dtype}"])
            item.setData(0, Qt.UserRole, {"type": "output", "tensor": output_tensor})
            output_item.addChild(item)
        self.structure_tree.addTopLevelItem(output_item)

        # 展开所有
        self.structure_tree.expandAll()

    def update_graph_info(self):
        """更新图信息"""
        if not self.model:
            return

        graph = self.model.graph

        info = []
        info.append("=" * 50)
        info.append("计算图属性")
        info.append("=" * 50)
        info.append(f"\n[*] 图名称: {graph.name}")

        # 节点详情
        info.append(f"\n[*] 所有节点 ({len(graph.node)} 个):")
        for i, node in enumerate(graph.node):
            info.append(f"\n[{i}] {node.op_type} - {node.name}")
            if node.attribute:
                info.append("  属性:")
                for attr in node.attribute:
                    info.append(f"    - {attr.name}: {self.get_attr_value(attr)}")
            if node.input:
                info.append(f"  输入: {', '.join(node.input)}")
            if node.output:
                info.append(f"  输出: {', '.join(node.output)}")

        self.graph_text.clear()
        self.graph_text.append("\n".join(info))

    def on_tree_item_clicked(self, item, column):
        """树节点点击事件"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        self.tab_widget.setCurrentIndex(2)  # 切换到节点详情标签页

        if data["type"] == "input":
            self.show_tensor_info(data["tensor"], "输入")
        elif data["type"] == "output":
            self.show_tensor_info(data["tensor"], "输出")
        elif data["type"] == "node":
            self.show_node_info(data["node"])
        elif data["type"] == "initializer":
            self.show_initializer_info(data["tensor"])

    def show_tensor_info(self, tensor, tensor_type):
        """显示张量信息"""
        info = []
        info.append("=" * 50)
        info.append(f"{tensor_type}张量信息")
        info.append("=" * 50)
        info.append(f"\n[*] 名称: {tensor.name}")
        info.append(f"\n[*] 形状: {self.get_tensor_shape(tensor)}")
        info.append(f"\n[*] 数据类型: {self.get_dtype_name(tensor.type.tensor_type.elem_type)}")

        # 显示维度信息
        if tensor.type.tensor_type.shape.dim:
            info.append(f"\n[*] 维度详情:")
            for i, dim in enumerate(tensor.type.tensor_type.shape.dim):
                dim_name = dim.dim_param if dim.dim_param else "?"
                dim_value = str(dim.dim_value) if hasattr(dim, 'dim_value') and dim.dim_value > 0 else dim_name
                info.append(f"  - 维度 {i}: {dim_value}")

        self.node_detail_text.clear()
        self.node_detail_text.append("\n".join(info))

    def show_node_info(self, node):
        """显示节点信息"""
        info = []
        info.append("=" * 50)
        info.append("节点详细信息")
        info.append("=" * 50)
        info.append(f"\n[*] 节点名称: {node.name}")
        info.append(f"\n[*] 操作类型: {node.op_type}")

        if node.domain:
            info.append(f"\n[*] 域: {node.domain}")

        if node.input:
            info.append(f"\n[*] 输入:")
            for i, inp in enumerate(node.input):
                info.append(f"  {i+1}. {inp}")

        if node.output:
            info.append(f"\n[*] 输出:")
            for i, out in enumerate(node.output):
                info.append(f"  {i+1}. {out}")

        if node.attribute:
            info.append(f"\n[*] 属性:")
            for attr in node.attribute:
                info.append(f"  - {attr.name}: {self.get_attr_value(attr)}")

        if node.doc_string:
            info.append(f"\n[*] 文档: {node.doc_string}")

        self.node_detail_text.clear()
        self.node_detail_text.append("\n".join(info))

    def show_initializer_info(self, init):
        """显示初始化器信息"""
        info = []
        info.append("=" * 50)
        info.append("初始化器 (权重) 信息")
        info.append("=" * 50)
        info.append(f"\n[*] 名称: {init.name}")
        info.append(f"\n[*] 形状: {list(init.dims)}")
        info.append(f"\n[*] 数据类型: {self.get_dtype_name(init.data_type)}")

        # 计算大小
        import numpy as np
        total_elements = np.prod(init.dims) if init.dims else 0
        info.append(f"\n[*] 元素数量: {total_elements}")

        # 数据位置
        if init.raw_data:
            info.append(f"\n[*] 数据: 原始数据 ({len(init.raw_data)} bytes)")
        elif hasattr(init, 'float_data') and init.float_data:
            info.append(f"\n[*] 数据: float64数组 ({len(init.float_data)} 个值)")
            if len(init.float_data) <= 10:
                info.append(f"  值: {list(init.float_data)}")
        elif hasattr(init, 'int64_data') and init.int64_data:
            info.append(f"\n[*] 数据: int64数组 ({len(init.int64_data)} 个值)")

        self.node_detail_text.clear()
        self.node_detail_text.append("\n".join(info))

    def clear_node_detail(self):
        """清除节点详情"""
        self.node_detail_text.clear()
        self.node_detail_text.append("请从左侧模型结构树中选择节点查看详细信息...")

    def get_tensor_shape(self, tensor):
        """获取张量形状"""
        try:
            dims = tensor.type.tensor_type.shape.dim
            shape = []
            for dim in dims:
                if dim.dim_value > 0:
                    shape.append(str(dim.dim_value))
                elif dim.dim_param:
                    shape.append(dim.dim_param)
                else:
                    shape.append("?")
            return f"[{', '.join(shape)}]"
        except:
            return "[?]"

    def get_dtype_name(self, dtype):
        """获取数据类型名称"""
        dtype_names = {
            0: "UNDEFINED",
            1: "FLOAT32",
            2: "UINT8",
            3: "INT8",
            4: "UINT16",
            5: "INT16",
            6: "INT32",
            7: "INT64",
            8: "STRING",
            9: "BOOL",
            10: "FLOAT16",
            11: "DOUBLE",
            12: "UINT32",
            13: "UINT64",
            14: "COMPLEX64",
            15: "COMPLEX128",
            16: "BFLOAT16"
        }
        return dtype_names.get(dtype, f"UNKNOWN({dtype})")

    def get_attr_value(self, attr):
        """获取属性值"""
        if attr.HasField('f'):
            return attr.f
        elif attr.HasField('i'):
            return attr.i
        elif attr.HasField('s'):
            return attr.s.decode('utf-8')
        elif attr.ints:
            return list(attr.ints)
        elif attr.floats:
            return list(attr.floats)
        elif attr.strings:
            return [s.decode('utf-8') for s in attr.strings]
        else:
            return str(attr)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = ONNXModelExplorer()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
