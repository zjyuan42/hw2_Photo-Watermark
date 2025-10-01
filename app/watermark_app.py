#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QListWidget, QListWidgetItem, QTabWidget, QGroupBox, QFormLayout,
    QComboBox, QSpinBox, QDoubleSpinBox, QColorDialog, QFontDialog, QTextEdit,
    QSlider, QCheckBox, QSplitter, QMessageBox, QLineEdit, QGridLayout
)
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, QColor, QFont, QPen, QIcon, QBrush, QTransform
)
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal, pyqtSlot
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import json
from datetime import datetime

class WatermarkApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('图片水印工具')
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化数据
        self.images = []  # 存储图片路径列表
        self.selected_image_idx = -1  # 当前选中的图片索引
        self.watermark_type = 'text'  # 默认文本水印
        self.text_watermark = '示例水印'
        self.font = QFont()
        self.font.setFamily('SimHei')
        self.font.setPointSize(24)
        self.color = QColor(255, 255, 255, 128)  # 白色半透明
        self.opacity = 50  # 背景不透明度 0-100
        self.text_opacity = 100  # 文字不透明度 0-100
        self.position = 'center'  # 水印位置
        self.rotation = 0  # 旋转角度
        self.scale = 100  # 缩放比例
        self.spacing = 50  # 平铺间距
        self.tile = False  # 是否平铺
        self.watermark_image_path = ''  # 水印图片路径
        self.templates = {}  # 水印模板
        self.output_format = 'jpg'  # 输出格式
        self.output_quality = 95  # 输出质量
        self.resize_enabled = False  # 是否调整大小
        self.resize_width = 1920  # 调整后宽度
        self.resize_height = 1080  # 调整后高度
        self.resize_keep_ratio = True  # 保持比例
        
        # 加载模板
        self.load_templates()
        
        # 创建UI
        self.init_ui()
        
    def init_ui(self):
        # 创建主部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 菜单栏
        self.create_menu_bar()
        
        # 顶部工具栏
        toolbar = self.addToolBar('工具栏')
        toolbar.setMovable(False)
        
        # 导入按钮
        import_btn = QPushButton('导入图片')
        import_btn.clicked.connect(self.import_images)
        toolbar.addWidget(import_btn)
        
        # 批量导入按钮
        batch_import_btn = QPushButton('批量导入')
        batch_import_btn.clicked.connect(self.import_batch_images)
        toolbar.addWidget(batch_import_btn)
        
        # 导出按钮
        export_btn = QPushButton('导出图片')
        export_btn.clicked.connect(self.export_images)
        toolbar.addWidget(export_btn)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板 - 图片列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 图片列表
        self.image_list = QListWidget()
        self.image_list.setIconSize(QSize(100, 100))
        self.image_list.setViewMode(QListWidget.IconMode)
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setMovement(QListWidget.Static)
        self.image_list.setSpacing(5)
        self.image_list.itemClicked.connect(self.on_image_selected)
        left_layout.addWidget(QLabel('图片列表:'))
        left_layout.addWidget(self.image_list)
        
        # 导出设置
        export_group = QGroupBox('导出设置')
        export_layout = QFormLayout(export_group)
        
        # 输出格式
        self.format_combo = QComboBox()
        self.format_combo.addItems(['jpg', 'png'])
        self.format_combo.currentTextChanged.connect(lambda text: setattr(self, 'output_format', text))
        export_layout.addRow('输出格式:', self.format_combo)
        
        # 输出质量
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(95)
        self.quality_spin.valueChanged.connect(lambda value: setattr(self, 'output_quality', value))
        export_layout.addRow('输出质量:', self.quality_spin)
        
        # 调整大小
        self.resize_check = QCheckBox('调整图片大小')
        self.resize_check.stateChanged.connect(self.on_resize_toggled)
        export_layout.addRow('', self.resize_check)
        
        # 宽度和高度
        resize_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(1920)
        self.width_spin.valueChanged.connect(self.on_width_changed)
        self.width_spin.setEnabled(False)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(1080)
        self.height_spin.valueChanged.connect(self.on_height_changed)
        self.height_spin.setEnabled(False)
        
        resize_layout.addWidget(QLabel('宽度:'))
        resize_layout.addWidget(self.width_spin)
        resize_layout.addWidget(QLabel('高度:'))
        resize_layout.addWidget(self.height_spin)
        
        # 保持比例
        self.keep_ratio_check = QCheckBox('保持比例')
        self.keep_ratio_check.setChecked(True)
        self.keep_ratio_check.stateChanged.connect(lambda state: setattr(self, 'resize_keep_ratio', state == Qt.Checked))
        self.keep_ratio_check.setEnabled(False)
        resize_layout.addWidget(self.keep_ratio_check)
        
        export_layout.addRow('', resize_layout)
        
        left_layout.addWidget(export_group)
        
        # 右侧面板 - 预览和设置
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 预览区域
        preview_group = QGroupBox('预览')
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel('请导入图片')
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        preview_layout.addWidget(self.preview_label)
        
        right_layout.addWidget(preview_group)
        
        # 设置选项卡
        self.tab_widget = QTabWidget()
        
        # 水印类型选项卡
        self.watermark_type_tab = QWidget()
        self.watermark_type_layout = QVBoxLayout(self.watermark_type_tab)
        
        type_group = QGroupBox('水印类型')
        type_layout = QHBoxLayout(type_group)
        
        self.text_radio = QPushButton('文本水印')
        self.text_radio.setCheckable(True)
        self.text_radio.setChecked(True)
        self.text_radio.clicked.connect(lambda: self.set_watermark_type('text'))
        
        self.image_radio = QPushButton('图片水印')
        self.image_radio.setCheckable(True)
        self.image_radio.clicked.connect(lambda: self.set_watermark_type('image'))
        
        type_layout.addWidget(self.text_radio)
        type_layout.addWidget(self.image_radio)
        
        self.watermark_type_layout.addWidget(type_group)
        
        # 文本水印设置
        self.text_watermark_group = QGroupBox('文本水印设置')
        text_watermark_layout = QFormLayout(self.text_watermark_group)
        
        # 文本内容
        self.text_edit = QTextEdit()
        self.text_edit.setText('示例水印')
        self.text_edit.textChanged.connect(self.on_text_changed)
        text_watermark_layout.addRow('文本内容:', self.text_edit)
        
        # 字体设置
        self.font_btn = QPushButton('选择字体')
        self.font_btn.clicked.connect(self.select_font)
        text_watermark_layout.addRow('字体:', self.font_btn)
        
        # 字体预览
        self.font_preview = QLabel('示例水印')
        self.font_preview.setFont(self.font)
        text_watermark_layout.addRow('预览:', self.font_preview)
        
        # 颜色设置
        self.color_btn = QPushButton('选择颜色')
        self.color_btn.setStyleSheet(f'background-color: rgba({self.color.red()}, {self.color.green()}, {self.color.blue()}, {self.color.alpha()/255})')
        self.color_btn.clicked.connect(self.select_color)
        text_watermark_layout.addRow('颜色:', self.color_btn)
        
        self.watermark_type_layout.addWidget(self.text_watermark_group)
        
        # 图片水印设置
        self.image_watermark_group = QGroupBox('图片水印设置')
        image_watermark_layout = QFormLayout(self.image_watermark_group)
        
        # 选择水印图片
        self.image_path_edit = QLineEdit()
        self.image_path_edit.setReadOnly(True)
        select_image_btn = QPushButton('选择水印图片')
        select_image_btn.clicked.connect(self.select_watermark_image)
        
        image_path_layout = QHBoxLayout()
        image_path_layout.addWidget(self.image_path_edit)
        image_path_layout.addWidget(select_image_btn)
        
        image_watermark_layout.addRow('水印图片:', image_path_layout)
        
        self.watermark_type_layout.addWidget(self.image_watermark_group)
        self.image_watermark_group.hide()
        
        # 布局和样式选项卡
        self.layout_tab = QWidget()
        self.layout_layout = QVBoxLayout(self.layout_tab)
        
        # 位置设置
        position_group = QGroupBox('水印位置')
        position_layout = QGridLayout(position_group)
        
        positions = [
            ('左上', 'top_left'), ('上中', 'top_center'), ('右上', 'top_right'),
            ('左中', 'middle_left'), ('中心', 'center'), ('右中', 'middle_right'),
            ('左下', 'bottom_left'), ('下中', 'bottom_center'), ('右下', 'bottom_right')
        ]
        
        row, col = 0, 0
        for label, pos in positions:
            btn = QPushButton(label)
            btn.setCheckable(True)
            if pos == 'center':
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, p=pos: self.set_position(p) if checked else None)
            position_layout.addWidget(btn, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        self.layout_layout.addWidget(position_group)
        
        # 透明度设置
        opacity_group = QGroupBox('透明度设置')
        opacity_layout = QVBoxLayout(opacity_group)
        
        # 背景透明度
        opacity_layout.addWidget(QLabel('背景透明度:'))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        
        self.opacity_label = QLabel(f'{self.opacity}%')
        self.opacity_label.setAlignment(Qt.AlignCenter)
        opacity_layout.addWidget(self.opacity_label)
        
        # 文字透明度
        opacity_layout.addWidget(QLabel('文字透明度:'))
        self.text_opacity_slider = QSlider(Qt.Horizontal)
        self.text_opacity_slider.setRange(0, 100)
        self.text_opacity_slider.setValue(100)
        self.text_opacity_slider.valueChanged.connect(self.on_text_opacity_changed)
        opacity_layout.addWidget(self.text_opacity_slider)
        
        self.text_opacity_label = QLabel(f'{self.text_opacity}%')
        self.text_opacity_label.setAlignment(Qt.AlignCenter)
        opacity_layout.addWidget(self.text_opacity_label)
        
        self.layout_layout.addWidget(opacity_group)
        
        # 旋转和缩放设置
        transform_group = QGroupBox('变换设置')
        transform_layout = QFormLayout(transform_group)
        
        # 旋转
        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(-180, 180)
        self.rotation_spin.setValue(0)
        self.rotation_spin.valueChanged.connect(lambda value: setattr(self, 'rotation', value))
        transform_layout.addRow('旋转角度:', self.rotation_spin)
        
        # 缩放
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(1, 500)
        self.scale_spin.setValue(100)
        self.scale_spin.valueChanged.connect(lambda value: setattr(self, 'scale', value))
        transform_layout.addRow('缩放比例:', self.scale_spin)
        
        # 平铺设置
        self.tile_check = QCheckBox('平铺水印')
        self.tile_check.stateChanged.connect(lambda state: setattr(self, 'tile', state == Qt.Checked))
        transform_layout.addRow('', self.tile_check)
        
        # 间距设置
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(1, 500)
        self.spacing_spin.setValue(50)
        self.spacing_spin.valueChanged.connect(lambda value: setattr(self, 'spacing', value))
        transform_layout.addRow('平铺间距:', self.spacing_spin)
        
        self.layout_layout.addWidget(transform_group)
        
        # 模板选项卡
        self.template_tab = QWidget()
        self.template_layout = QVBoxLayout(self.template_tab)
        
        # 模板列表
        template_group = QGroupBox('水印模板')
        template_layout = QVBoxLayout(template_group)
        
        self.template_list = QListWidget()
        template_layout.addWidget(QLabel('可用模板:'))
        template_layout.addWidget(self.template_list)
        
        template_btn_layout = QHBoxLayout()
        self.save_template_btn = QPushButton('保存当前配置为模板')
        self.save_template_btn.clicked.connect(self.save_template)
        
        self.load_template_btn = QPushButton('加载模板')
        self.load_template_btn.clicked.connect(self.load_template)
        
        self.delete_template_btn = QPushButton('删除模板')
        self.delete_template_btn.clicked.connect(self.delete_template)
        
        template_btn_layout.addWidget(self.save_template_btn)
        template_btn_layout.addWidget(self.load_template_btn)
        template_btn_layout.addWidget(self.delete_template_btn)
        
        template_layout.addLayout(template_btn_layout)
        
        self.template_layout.addWidget(template_group)
        
        # 添加选项卡
        self.tab_widget.addTab(self.watermark_type_tab, '水印类型')
        self.tab_widget.addTab(self.layout_tab, '布局和样式')
        self.tab_widget.addTab(self.template_tab, '模板')
        
        right_layout.addWidget(self.tab_widget)
        
        # 添加面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([300, 900])
        
        main_layout.addWidget(splitter)
        
        # 应用设置
        self.apply_btn = QPushButton('应用水印')
        self.apply_btn.clicked.connect(self.apply_watermark_to_preview)
        main_layout.addWidget(self.apply_btn)
        
    def create_menu_bar(self):
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 导入图片动作
        import_action = file_menu.addAction('导入图片')
        import_action.triggered.connect(self.import_images)
        
        # 批量导入动作
        batch_import_action = file_menu.addAction('批量导入')
        batch_import_action.triggered.connect(self.import_batch_images)
        
        # 导出图片动作
        export_action = file_menu.addAction('导出图片')
        export_action.triggered.connect(self.export_images)
        
        # 退出动作
        exit_action = file_menu.addAction('退出')
        exit_action.triggered.connect(self.close)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        # 关于动作
        about_action = help_menu.addAction('关于')
        about_action.triggered.connect(self.show_about)
    
    def import_images(self):
        # 导入单个图片
        file_path, _ = QFileDialog.getOpenFileName(
            self, '导入图片', '', '图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff)'
        )
        if file_path:
            self.add_image(file_path)
    
    def import_batch_images(self):
        # 批量导入图片
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, '批量导入图片', '', '图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff)'
        )
        if file_paths:
            for file_path in file_paths:
                self.add_image(file_path)
    
    def add_image(self, file_path):
        # 添加图片到列表
        if file_path not in self.images:
            self.images.append(file_path)
            
            # 创建列表项
            item = QListWidgetItem()
            item.setText(os.path.basename(file_path))
            
            # 创建缩略图
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                item.setIcon(QIcon(scaled_pixmap))
            
            self.image_list.addItem(item)
            
            # 如果是第一张图片，自动选中
            if len(self.images) == 1:
                self.image_list.setCurrentRow(0)
                self.on_image_selected(self.image_list.currentItem())
    
    def on_image_selected(self, item):
        # 当选中图片时
        if item:
            self.selected_image_idx = self.image_list.row(item)
            self.update_preview()
    
    def update_preview(self):
        # 更新预览
        if self.selected_image_idx >= 0 and self.selected_image_idx < len(self.images):
            file_path = self.images[self.selected_image_idx]
            pixmap = QPixmap(file_path)
            
            if not pixmap.isNull():
                # 调整预览大小
                max_width = self.preview_label.width()
                max_height = self.preview_label.height()
                scaled_pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled_pixmap)
            else:
                self.preview_label.setText('无法加载图片')
        else:
            self.preview_label.setText('请选择图片')
    
    def set_watermark_type(self, type_):
        # 设置水印类型
        self.watermark_type = type_
        
        # 更新按钮状态
        self.text_radio.setChecked(type_ == 'text')
        self.image_radio.setChecked(type_ == 'image')
        
        # 显示或隐藏相应的设置
        self.text_watermark_group.setVisible(type_ == 'text')
        self.image_watermark_group.setVisible(type_ == 'image')
    
    def on_text_changed(self):
        # 当文本内容改变时
        self.text_watermark = self.text_edit.toPlainText()
        self.font_preview.setText(self.text_watermark)
    
    def select_font(self):
        # 选择字体
        font, ok = QFontDialog.getFont(self.font, self, '选择字体')
        if ok:
            self.font = font
            self.font_preview.setFont(font)
    
    def select_color(self):
        # 选择颜色
        color = QColorDialog.getColor(self.color, self, '选择颜色')
        if color.isValid():
            self.color = color
            self.color_btn.setStyleSheet(f'background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()/255})')
    
    def select_watermark_image(self):
        # 选择水印图片
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择水印图片', '', '图片文件 (*.jpg *.jpeg *.png *.bmp)'
        )
        if file_path:
            self.watermark_image_path = file_path
            self.image_path_edit.setText(file_path)
    
    def set_position(self, position):
        # 设置水印位置
        self.position = position
        
        # 更新按钮状态
        for btn in self.findChildren(QPushButton):
            if btn.text() in ['左上', '上中', '右上', '左中', '中心', '右中', '左下', '下中', '右下']:
                pos_map = {
                    '左上': 'top_left', '上中': 'top_center', '右上': 'top_right',
                    '左中': 'middle_left', '中心': 'center', '右中': 'middle_right',
                    '左下': 'bottom_left', '下中': 'bottom_center', '右下': 'bottom_right'
                }
                btn.setChecked(pos_map.get(btn.text()) == position)
    
    def on_opacity_changed(self, value):
        # 当背景透明度改变时
        self.opacity = value
        self.opacity_label.setText(f'{value}%')
        
        # 更新颜色的透明度
        self.color.setAlpha(int(value * 2.55))
        self.color_btn.setStyleSheet(f'background-color: rgba({self.color.red()}, {self.color.green()}, {self.color.blue()}, {self.color.alpha()/255})')
        
    def on_text_opacity_changed(self, value):
        # 当文字透明度改变时
        self.text_opacity = value
        self.text_opacity_label.setText(f'{value}%')
    
    def on_resize_toggled(self, state):
        # 当调整大小选项改变时
        enabled = state == Qt.Checked
        self.resize_enabled = enabled
        self.width_spin.setEnabled(enabled)
        self.height_spin.setEnabled(enabled)
        self.keep_ratio_check.setEnabled(enabled)
    
    def on_width_changed(self, width):
        # 当宽度改变时
        self.resize_width = width
        if self.resize_keep_ratio and self.selected_image_idx >= 0 and self.selected_image_idx < len(self.images):
            # 保持比例调整高度
            file_path = self.images[self.selected_image_idx]
            image = QImage(file_path)
            if not image.isNull():
                ratio = image.height() / image.width()
                self.resize_height = int(width * ratio)
                self.height_spin.setValue(self.resize_height)
    
    def on_height_changed(self, height):
        # 当高度改变时
        self.resize_height = height
        if self.resize_keep_ratio and self.selected_image_idx >= 0 and self.selected_image_idx < len(self.images):
            # 保持比例调整宽度
            file_path = self.images[self.selected_image_idx]
            image = QImage(file_path)
            if not image.isNull():
                ratio = image.width() / image.height()
                self.resize_width = int(height * ratio)
                self.width_spin.setValue(self.resize_width)
    
    def apply_watermark_to_preview(self):
        # 应用水印到预览
        if self.selected_image_idx >= 0 and self.selected_image_idx < len(self.images):
            file_path = self.images[self.selected_image_idx]
            
            # 创建带水印的图片
            try:
                watermarked_image = self.apply_watermark(file_path)
                
                # 显示预览
                max_width = self.preview_label.width()
                max_height = self.preview_label.height()
                scaled_pixmap = watermarked_image.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled_pixmap)
                
            except Exception as e:
                QMessageBox.critical(self, '错误', f'应用水印时出错: {str(e)}')
    
    def apply_watermark(self, image_path):
        print(f"开始应用水印: {image_path}")
        print(f"水印参数: type={self.watermark_type}, opacity={self.opacity}, position={self.position}, rotation={self.rotation}, tile={self.tile}")
        
        # 应用水印到图片
        try:
            print("正在打开原图...")
            image = Image.open(image_path).convert('RGBA')
            print(f"原图尺寸: {image.size}")
            
            # 创建一个透明图层用于绘制水印
            print("创建水印图层...")
            watermark_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark_layer)
            
            if self.watermark_type == 'text':
                # 文本水印
                print("处理文本水印...")
                text = self.text_watermark
                print(f"水印文本: {text}")
                
                # 计算水印区域大小（占图片宽度的90%，高度的20%）
                watermark_width = int(image.width * 0.9)
                watermark_height = int(image.height * 0.2)
                print(f"水印区域尺寸: {watermark_width}x{watermark_height}")
                
                # 计算位置（根据用户选择的位置参数）
                x, y = self.get_position(image.width, image.height, watermark_width, watermark_height)
                print(f"水印区域位置: ({x}, {y})")
                
                # 绘制半透明白色背景
                bg_opacity = int(self.opacity * 2)
                print(f"背景透明度: {bg_opacity}")
                draw.rectangle([x, y, x + watermark_width, y + watermark_height], fill=(255, 255, 255, bg_opacity))
                
                # 全新的文本渲染方法
                print("绘制文本水印...")
                
                # 使用用户选择的颜色
                text_color = (self.color.red(), self.color.green(), self.color.blue())
                text_opacity = int(self.text_opacity * 2.55)  # 根据用户设置的文字透明度
                print(f"文本颜色: {text_color}, 透明度: {text_opacity}")
                
                # 关键改进：使用ImageFont模块指定字体和大小
                # 不再使用多次偏移绘制的方法，改为单个清晰文本
                try:
                    # 尝试加载系统字体
                    # 对于中文，我们需要确保字体支持中文显示
                    from PIL import ImageFont
                    
                    # 获取用户选择的字体大小并进行适当缩放
                    # 由于PIL和PyQt的字体大小单位可能不同，添加缩放因子
                    user_font_size = self.font.pointSize()
                    # 根据水印区域高度和用户选择的字体大小计算最终字体大小
                    # 缩放因子需要根据实际显示效果调整
                    scale_factor = min(watermark_height / 100, watermark_width / (len(text) * 10))  # 确保文字不会溢出
                    font_size = max(12, int(user_font_size * scale_factor * 1.5))  # 设置最小字体大小为12
                    print(f"用户选择的字体大小: {user_font_size}, 计算后字体大小: {font_size}")
                    
                    # 尝试加载几种常见的支持中文的字体
                    font_path = None
                    font = None
                    
                    # 首先尝试使用用户选择的字体
                    user_font_family = self.font.family()
                    print(f"用户选择的字体: {user_font_family}")
                    
                    # 方法1: 尝试直接通过字体名称加载（PIL可能能够查找系统字体）
                    try:
                        font = ImageFont.truetype(user_font_family, font_size)
                        print(f"成功直接通过字体名称加载: {user_font_family}")
                    except Exception as e:
                        print(f"直接加载字体失败: {e}")
                        
                        # 方法2: 尝试根据字体名称查找字体文件
                        # 预定义的字体名称到文件路径的映射
                        font_name_to_path = {
                            'SimHei': 'C:/Windows/Fonts/simhei.ttf',
                            'SimSun': 'C:/Windows/Fonts/simsun.ttc',
                            'Microsoft YaHei': 'C:/Windows/Fonts/msyh.ttf',
                            'KaiTi': 'C:/Windows/Fonts/simkai.ttf',
                            'Arial': 'C:/Windows/Fonts/arial.ttf',
                            'Times New Roman': 'C:/Windows/Fonts/times.ttf',
                            'Courier New': 'C:/Windows/Fonts/cour.ttf',
                            'Comic Sans MS': 'C:/Windows/Fonts/comic.ttf',
                            'Impact': 'C:/Windows/Fonts/impact.ttf',
                            'Verdana': 'C:/Windows/Fonts/verdana.ttf',
                            'Georgia': 'C:/Windows/Fonts/georgia.ttf',
                            'Tahoma': 'C:/Windows/Fonts/tahoma.ttf',
                            'Bradley Hand ITC': 'C:/Windows/Fonts/bradhitc.ttf',
                        }
                        
                        # 尝试直接匹配字体名称
                        if user_font_family in font_name_to_path:
                            user_font_path = font_name_to_path[user_font_family]
                            if os.path.exists(user_font_path):
                                try:
                                    font = ImageFont.truetype(user_font_path, font_size)
                                    print(f"成功加载用户选择的字体: {user_font_path}")
                                except Exception as e:
                                    print(f"加载用户选择的字体出错: {e}")
                    
                    # 如果用户字体加载失败，尝试加载默认的中文字体
                    if font is None:
                        print("尝试加载默认中文字体")
                        possible_fonts = [
                            'C:/Windows/Fonts/simhei.ttf',  # 黑体
                            'C:/Windows/Fonts/simsun.ttc',  # 宋体
                            'C:/Windows/Fonts/msyh.ttf',    # 微软雅黑
                            'C:/Windows/Fonts/simkai.ttf',  # 楷体
                        ]
                        
                        for fp in possible_fonts:
                            if os.path.exists(fp):
                                font_path = fp
                                try:
                                    font = ImageFont.truetype(fp, font_size)
                                    print(f"成功加载默认字体: {fp}")
                                    break
                                except Exception as e:
                                    print(f"加载字体 {fp} 时出错: {e}")
                                    continue
                    
                    # 如果无法加载字体，使用默认字体但调整大小
                    if font is None:
                        print("无法加载指定字体，使用默认字体")
                        # 使用一个非常简单的方法：绘制文本的同时填充内部
                        
                        # 计算文本位置（居中）
                        text_x = x + (watermark_width // 4)  # 稍微靠左，避免文字太分散
                        text_y = y + (watermark_height // 4)  # 稍微靠上
                        print(f"文本绘制位置: ({text_x}, {text_y})")
                        
                        # 为确保文字清晰可见，使用一个非常基础但有效的方法：
                        # 1. 先绘制一个实心的文字轮廓
                        # 2. 再在中间绘制相同的文字填充内部
                        
                        # 绘制外轮廓（使用略微放大的偏移）
                        for offset_x in range(-10, 11):
                            for offset_y in range(-10, 11):
                                if offset_x != 0 or offset_y != 0:  # 避免重复绘制中心
                                    draw.text((text_x + offset_x, text_y + offset_y), text, fill=text_color + (text_opacity,))
                
                        # 绘制内部填充（纯色）
                        draw.text((text_x, text_y), text, fill=(255, 0, 0, text_opacity))  # 使用红色填充内部
                    else:
                        # 字体加载成功，使用指定字体绘制
                        print("使用指定字体绘制文本")
                        
                        # 计算文本位置（居中）
                        # 获取文本的边界框来精确计算居中位置
                        try:
                            # 尝试获取文本尺寸
                            bbox = draw.textbbox((0, 0), text, font=font)
                            text_width = bbox[2] - bbox[0]
                            text_height = bbox[3] - bbox[1]
                            print(f"文本尺寸: {text_width}x{text_height}")
                            
                            # 计算居中位置
                            text_x = x + (watermark_width - text_width) // 2
                            text_y = y + (watermark_height - text_height) // 2
                        except Exception as e:
                            print(f"获取文本边界框失败: {e}")
                            # 使用简单计算
                            text_x = x + (watermark_width // 4)
                            text_y = y + (watermark_height // 4)
                        
                        print(f"文本绘制位置: ({text_x}, {text_y})")
                        
                        # 绘制文本
                        draw.text((text_x, text_y), text, font=font, fill=text_color + (text_opacity,))
                except ImportError:
                    print("ImageFont模块不可用，使用简单文本绘制")
                    # 简单绘制方法
                    text_x = x + (watermark_width // 4)
                    text_y = y + (watermark_height // 4)
                    draw.text((text_x, text_y), text, fill=text_color + (text_opacity,))
                
                # 另外添加一些小的辅助标记，确认水印应用
                print("添加辅助标记...")
                # 在水印区域的四个角落绘制小方块，使用与文字相同的颜色和透明度
                corner_size = 25
                draw.rectangle([x, y, x + corner_size, y + corner_size], fill=text_color + (text_opacity,))
                draw.rectangle([x + watermark_width - corner_size, y, x + watermark_width, y + corner_size], fill=text_color + (text_opacity,))
                draw.rectangle([x, y + watermark_height - corner_size, x + corner_size, y + watermark_height], fill=text_color + (text_opacity,))
                draw.rectangle([x + watermark_width - corner_size, y + watermark_height - corner_size, x + watermark_width, y + watermark_height], fill=text_color + (text_opacity,))
                
                # 添加额外的辅助信息，以便我们可以验证水印是否被添加
                # 在图片左上角添加一个小的红色标记
                draw.rectangle([10, 10, 30, 30], fill=(255, 0, 0, 255))
                print("已添加左上角红色标记作为水印应用的确认")
            else:
                # 图片水印
                print("处理图片水印...")
                if not self.watermark_image_path or not os.path.exists(self.watermark_image_path):
                    raise Exception('请选择一个有效的水印图片')
                
                print(f"使用水印图片: {self.watermark_image_path}")
                # 打开水印图片
                watermark_image = Image.open(self.watermark_image_path).convert('RGBA')
                print(f"水印图片原始尺寸: {watermark_image.size}")
                
                # 调整水印图片大小
                width, height = watermark_image.size
                new_width = int(width * self.scale / 100)
                new_height = int(height * self.scale / 100)
                watermark_image = watermark_image.resize((new_width, new_height), Image.LANCZOS)
                print(f"调整后水印尺寸: {new_width}x{new_height}")
                
                # 调整水印透明度
                if self.opacity != 100:
                    print(f"调整水印透明度为: {self.opacity}%")
                    # 创建一个新的图像用于调整透明度
                    watermark_with_opacity = Image.new('RGBA', watermark_image.size)
                    for x in range(watermark_image.width):
                        for y in range(watermark_image.height):
                            r, g, b, a = watermark_image.getpixel((x, y))
                            watermark_with_opacity.putpixel((x, y), (r, g, b, int(a * self.opacity / 100)))
                    watermark_image = watermark_with_opacity
                
                # 应用旋转
                if self.rotation != 0:
                    print(f"应用旋转: {self.rotation}度")
                    watermark_image = watermark_image.rotate(self.rotation, expand=1)
                    print(f"旋转后水印尺寸: {watermark_image.size}")
                
                # 获取水印尺寸
                watermark_width, watermark_height = watermark_image.size
                
                # 平铺水印
                if self.tile:
                    print(f"应用平铺效果，间距: {self.spacing}")
                    for x in range(0, image.width + watermark_width, self.spacing):
                        for y in range(0, image.height + watermark_height, self.spacing):
                            watermark_layer.paste(watermark_image, (x, y), watermark_image)
                else:
                    # 计算水印位置
                    position = self.get_position(image.width, image.height, watermark_width, watermark_height)
                    print(f"计算得到的水印位置: {position}")
                    
                    # 粘贴水印
                    watermark_layer.paste(watermark_image, position, watermark_image)
            
            # 合并图片和水印
            print("合并原图和水印...")
            result = Image.alpha_composite(image, watermark_layer)
            
            # 调整图片大小（如果需要）
            if self.resize_enabled:
                print(f"调整图片大小至: {self.resize_width}x{self.resize_height}")
                result = result.resize((self.resize_width, self.resize_height), Image.LANCZOS)
            
            # 转换为QPixmap返回
            try:
                print("开始转换为QPixmap...")
                # 直接使用PIL的tobytes方法转换，避免numpy可能的问题
                rgb_image = result.convert('RGB')
                width, height = rgb_image.size
                print(f"转换前图像尺寸: {width}x{height}")
                data = rgb_image.tobytes("raw", "RGB")
                print(f"图像数据大小: {len(data)}字节")
                q_image = QImage(data, width, height, 3 * width, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_image)
                print("转换QPixmap成功")
                return pixmap
            except Exception as e:
                # 如果转换失败，尝试备选方案
                print(f"转换图像时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                # 使用更简单的方式转换
                print("尝试备选转换方案...")
                try:
                    return QPixmap.fromImage(QImage.fromData(result.convert('RGB').tobytes()))
                except Exception as e2:
                    print(f"备选转换方案也失败: {str(e2)}")
                    raise
        except Exception as e:
            print(f"应用水印过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_position(self, image_width, image_height, watermark_width, watermark_height):
        # 获取水印位置
        positions = {
            'top_left': (10, 10),
            'top_center': ((image_width - watermark_width) // 2, 10),
            'top_right': (image_width - watermark_width - 10, 10),
            'middle_left': (10, (image_height - watermark_height) // 2),
            'center': ((image_width - watermark_width) // 2, (image_height - watermark_height) // 2),
            'middle_right': (image_width - watermark_width - 10, (image_height - watermark_height) // 2),
            'bottom_left': (10, image_height - watermark_height - 10),
            'bottom_center': ((image_width - watermark_width) // 2, image_height - watermark_height - 10),
            'bottom_right': (image_width - watermark_width - 10, image_height - watermark_height - 10)
        }
        
        return positions.get(self.position, positions['center'])
    
    def export_images(self):
        # 导出图片
        if not self.images:
            QMessageBox.warning(self, '警告', '请先导入图片')
            return
        
        # 选择导出目录
        directory = QFileDialog.getExistingDirectory(self, '选择导出目录', '')
        if not directory:
            return
        
        # 导出进度
        total = len(self.images)
        success_count = 0
        
        for i, image_path in enumerate(self.images):
            try:
                # 应用水印
                watermarked_pixmap = self.apply_watermark(image_path)
                
                # 生成文件名
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(directory, f'{base_name}_watermark_{timestamp}.{self.output_format}')
                
                # 保存图片
                if self.output_format == 'jpg':
                    watermarked_pixmap.save(output_path, 'JPEG', quality=self.output_quality)
                else:
                    watermarked_pixmap.save(output_path, 'PNG')
                
                success_count += 1
                
            except Exception as e:
                QMessageBox.warning(self, '警告', f'导出图片 {os.path.basename(image_path)} 时出错: {str(e)}')
        
        QMessageBox.information(self, '完成', f'共 {success_count}/{total} 张图片导出成功')
    
    def load_templates(self):
        # 加载水印模板
        try:
            template_file = 'watermark_templates.json'
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
                
                # 更新模板列表
                self.template_list.clear()
                for name in self.templates.keys():
                    self.template_list.addItem(name)
        except Exception as e:
            print(f'加载模板时出错: {str(e)}')
    
    def save_template(self):
        # 保存水印模板
        template_name, ok = QInputDialog.getText(self, '保存模板', '请输入模板名称:')
        if ok and template_name:
            # 保存当前配置
            template = {
                'watermark_type': self.watermark_type,
                'text_watermark': self.text_watermark,
                'font': {
                    'family': self.font.family(),
                    'pointSize': self.font.pointSize()
                },
                'color': {
                    'red': self.color.red(),
                    'green': self.color.green(),
                    'blue': self.color.blue(),
                    'alpha': self.color.alpha()
                },
                'opacity': self.opacity,
                'position': self.position,
                'rotation': self.rotation,
                'scale': self.scale,
                'spacing': self.spacing,
                'tile': self.tile,
                'watermark_image_path': self.watermark_image_path
            }
            
            self.templates[template_name] = template
            
            # 保存到文件
            try:
                with open('watermark_templates.json', 'w', encoding='utf-8') as f:
                    json.dump(self.templates, f, ensure_ascii=False, indent=4)
                
                # 更新模板列表
                self.template_list.clear()
                for name in self.templates.keys():
                    self.template_list.addItem(name)
                
                QMessageBox.information(self, '成功', f'模板 "{template_name}" 保存成功')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'保存模板时出错: {str(e)}')
    
    def load_template(self):
        # 加载水印模板
        selected_item = self.template_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, '警告', '请先选择一个模板')
            return
        
        template_name = selected_item.text()
        if template_name in self.templates:
            template = self.templates[template_name]
            
            # 应用模板配置
            self.set_watermark_type(template['watermark_type'])
            
            if template['watermark_type'] == 'text':
                self.text_watermark = template['text_watermark']
                self.text_edit.setText(self.text_watermark)
                self.font_preview.setText(self.text_watermark)
                
                # 恢复字体
                self.font = QFont()
                self.font.setFamily(template['font']['family'])
                self.font.setPointSize(template['font']['pointSize'])
                self.font_preview.setFont(self.font)
            else:
                self.watermark_image_path = template['watermark_image_path']
                self.image_path_edit.setText(self.watermark_image_path)
            
            # 恢复颜色
            color_data = template['color']
            self.color = QColor(color_data['red'], color_data['green'], color_data['blue'], color_data['alpha'])
            self.color_btn.setStyleSheet(f'background-color: rgba({self.color.red()}, {self.color.green()}, {self.color.blue()}, {self.color.alpha()/255})')
            
            # 恢复其他设置
            self.opacity = template['opacity']
            self.opacity_slider.setValue(self.opacity)
            self.opacity_label.setText(f'{self.opacity}%')
            
            self.set_position(template['position'])
            
            self.rotation = template['rotation']
            self.rotation_spin.setValue(self.rotation)
            
            self.scale = template['scale']
            self.scale_spin.setValue(self.scale)
            
            self.spacing = template['spacing']
            self.spacing_spin.setValue(self.spacing)
            
            self.tile = template['tile']
            self.tile_check.setChecked(self.tile)
            
            QMessageBox.information(self, '成功', f'模板 "{template_name}" 加载成功')
    
    def delete_template(self):
        # 删除水印模板
        selected_item = self.template_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, '警告', '请先选择一个模板')
            return
        
        template_name = selected_item.text()
        reply = QMessageBox.question(self, '确认', f'确定要删除模板 "{template_name}" 吗？', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if template_name in self.templates:
                del self.templates[template_name]
                
                # 保存到文件
                try:
                    with open('watermark_templates.json', 'w', encoding='utf-8') as f:
                        json.dump(self.templates, f, ensure_ascii=False, indent=4)
                    
                    # 更新模板列表
                    self.template_list.clear()
                    for name in self.templates.keys():
                        self.template_list.addItem(name)
                    
                    QMessageBox.information(self, '成功', f'模板 "{template_name}" 删除成功')
                except Exception as e:
                    QMessageBox.critical(self, '错误', f'删除模板时出错: {str(e)}')
    
    def show_about(self):
        # 显示关于对话框
        QMessageBox.about(self, '关于', '图片水印工具\n\n版本: 1.0\n\n一个简单易用的图片水印添加工具')
    
    def resizeEvent(self, event):
        # 重写调整大小事件
        super().resizeEvent(event)
        self.update_preview()

# 为了兼容性，添加QInputDialog的导入
from PyQt5.QtWidgets import QInputDialog