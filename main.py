#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication
from app.watermark_app import WatermarkApp

def main():
    # 确保中文显示正常
    os.environ['QT_FONT_DPI'] = '96'
    os.environ['QT_SCALE_FACTOR'] = '1.0'
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = WatermarkApp()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()