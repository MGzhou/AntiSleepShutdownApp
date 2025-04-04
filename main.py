import sys
import subprocess
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QPushButton,QSpinBox, QGroupBox,QStyleOptionSpinBox,QStyle, QMessageBox, QSizePolicy)

from PySide6.QtGui import QPainter, QIcon, QFont
from PySide6.QtCore import Qt, QTimer
import win32api
import win32con

class AntiSleepShutdownApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("AntiSleepShutdownApp")
        self.setWindowIcon(QIcon("app.ico"))  # 请准备一个图标文件或移除这行
        
        # 使用相对大小而不是固定大小
        self.setMinimumSize(380, 400)
        self.resize(380, 400)
        
        # 设置主窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QGroupBox {
                font: bold;
                border: 2px solid #4C566A;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: border;
                left: 20px;
                bottom:10px;
                padding: 0 0px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 0.5em 1em;
                text-align: center;
                text-decoration: none;
                margin: 0.25em 0.125em;
                border-radius: 4px;
                min-width: 5em;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QPushButton#stopButton {
                background-color: #f44336;
            }
            QPushButton#stopButton:hover {
                background-color: #d32f2f;
            }
            QTimeEdit, QSpinBox, QLineEdit {
                padding: 0.3em;
                border: 1px solid #ccc;
                border-radius: 4px;
                min-width: 3em;
            }
            QLabel#countdownLabel {
                font: bold;
                color: #d32f2f;
                qproperty-alignment: AlignCenter;
                padding: 0.5em;
            }
            QLabel {
                padding: 0.2em;
            }
        """)
        
        self.initUI()
        self.initTimers()

    def initUI(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 防息屏功能区域
        self.createAntiSleepGroup()
        main_layout.addWidget(self.anti_sleep_group)
        
        # 定时关机功能区域
        self.createShutdownGroup()
        main_layout.addWidget(self.shutdown_group)
        
        # 倒计时显示
        self.countdown_label = QLabel("")
        self.countdown_label.setObjectName("countdownLabel")
        self.countdown_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.countdown_label)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
    def createAntiSleepGroup(self):
        self.anti_sleep_group = QGroupBox("防止息屏设置")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 点击间隔设置
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("点击间隔(秒):"))
        self.click_interval = CustomSpinBox()
        self.click_interval.setRange(10, 3600)
        self.click_interval.setValue(60)
        interval_layout.addWidget(self.click_interval)
        interval_layout.addStretch()
        layout.addLayout(interval_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        self.start_anti_sleep_btn = QPushButton("开始防息屏")
        self.start_anti_sleep_btn.clicked.connect(self.startAntiSleep)
        button_layout.addWidget(self.start_anti_sleep_btn)
        
        self.stop_anti_sleep_btn = QPushButton("停止")
        self.stop_anti_sleep_btn.setObjectName("stopButton")
        self.stop_anti_sleep_btn.clicked.connect(self.stopAntiSleep)
        self.stop_anti_sleep_btn.setEnabled(False)
        button_layout.addWidget(self.stop_anti_sleep_btn)
        
        layout.addLayout(button_layout)
        self.anti_sleep_group.setLayout(layout)
        
    def createShutdownGroup(self):
        self.shutdown_group = QGroupBox("定时关机设置")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 倒计时设置
        self.countdown_layout = QHBoxLayout()
        self.countdown_layout.addWidget(QLabel("关机倒计时:"))
        self.hours_spin = CustomSpinBox()
        self.hours_spin.setRange(0, 23)
        self.hours_spin.setValue(1)
        self.countdown_layout.addWidget(self.hours_spin)
        self.countdown_layout.addWidget(QLabel("小时"))
        
        self.minutes_spin = CustomSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(0)
        self.countdown_layout.addWidget(self.minutes_spin)
        self.countdown_layout.addWidget(QLabel("分钟"))
        
        self.countdown_layout.addStretch()
        layout.addLayout(self.countdown_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        self.set_shutdown_btn = QPushButton("设置关机")
        self.set_shutdown_btn.clicked.connect(self.setShutdown)
        button_layout.addWidget(self.set_shutdown_btn)
        
        self.cancel_shutdown_btn = QPushButton("取消关机")
        self.cancel_shutdown_btn.setObjectName("stopButton")
        self.cancel_shutdown_btn.clicked.connect(self.cancelShutdown)
        self.cancel_shutdown_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_shutdown_btn)
        
        layout.addLayout(button_layout)
        self.shutdown_group.setLayout(layout)
        
    def initTimers(self):
        # 防息屏定时器
        self.anti_sleep_timer = QTimer()
        self.anti_sleep_timer.timeout.connect(self.simulateClick)
        
        # 关机倒计时定时器
        self.shutdown_timer = QTimer()
        self.shutdown_timer.timeout.connect(self.updateCountdown)
        
        self.shutdown_time = None
        
    def startAntiSleep(self):
        interval = self.click_interval.value() * 1000  # 转换为毫秒
        self.anti_sleep_timer.start(interval)
        self.start_anti_sleep_btn.setEnabled(False)
        self.stop_anti_sleep_btn.setEnabled(True)
        QMessageBox.information(self, "提示", f"已开始防息屏，每 {interval//1000} 秒模拟一次鼠标点击")
        
    def stopAntiSleep(self):
        self.anti_sleep_timer.stop()
        self.start_anti_sleep_btn.setEnabled(True)
        self.stop_anti_sleep_btn.setEnabled(False)
        QMessageBox.information(self, "提示", "已停止防息屏")
        
    def simulateClick(self):
        # 获取当前鼠标位置
        pos = win32api.GetCursorPos()
        
        # 如果鼠标在(0,0)位置则停止
        if pos == (0, 0):
            self.stopAntiSleep()
            return
            
        # 模拟鼠标点击
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, pos[0], pos[1], 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, pos[0], pos[1], 0, 0)
        
    def setShutdown(self):
        # 倒计时关机
        hours = self.hours_spin.value()
        minutes = self.minutes_spin.value()
        if hours == 0 and minutes == 0:
            QMessageBox.warning(self, "警告", "关机时间不能为0")
            return
            
        total_seconds = hours * 3600 + minutes * 60
        self.shutdown_time = datetime.now() + timedelta(seconds=total_seconds)
        
        # 设置Windows关机
        # os.system(f"shutdown -s -t {total_seconds}")
        subprocess.run(
            ["shutdown", "-s", '-t', str(total_seconds)],  # 命令及其参数
            shell=True,          # 在 Windows 上通常需要设置为 True
            creationflags=subprocess.CREATE_NO_WINDOW  # 避免弹窗
        )
    
        # 更新UI
        self.set_shutdown_btn.setEnabled(False)
        self.cancel_shutdown_btn.setEnabled(True)
        self.countdown_layout.setEnabled(False)
        
        # 启动倒计时显示
        self.shutdown_timer.start(1000)
        self.updateCountdown()
        
    def cancelShutdown(self):
        # 取消Windows关机
        # os.system("shutdown -a")
        
        subprocess.run(
            ["shutdown", "-a"],  # 命令及其参数
            shell=True,          # 在 Windows 上通常需要设置为 True
            creationflags=subprocess.CREATE_NO_WINDOW  # 避免弹窗
        )
        # 停止定时器
        self.shutdown_timer.stop()
        
        # 更新UI
        self.set_shutdown_btn.setEnabled(True)
        self.cancel_shutdown_btn.setEnabled(False)
        self.countdown_layout.setEnabled(True)
        
        self.countdown_label.setText("已取消关机计划")
        self.shutdown_time = None
        
    def updateCountdown(self):
        if not self.shutdown_time:
            return
            
        remaining = self.shutdown_time - datetime.now()
        if remaining.total_seconds() <= 0:
            self.countdown_label.setText("正在关机...")
            self.shutdown_timer.stop()
            return
            
        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.countdown_label.setText(f"将在 {hours:02d}:{minutes:02d}:{seconds:02d} 后关机")
        
    def closeEvent(self, event):
        # 关闭窗口时停止所有定时器
        if self.anti_sleep_timer.isActive():
            self.anti_sleep_timer.stop()
            
        if self.shutdown_timer.isActive():
            reply = QMessageBox.question(
                self, '确认', 
                '定时关机任务仍在运行，关闭窗口不会取消关机计划。确定要关闭吗?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
                
        event.accept()

class CustomSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置范围和初始值
        self.setRange(0, 100)
        self.setValue(1)
        
        # font-size: 14px;
        # min-width: 80px;
        # 应用样式
        self.setStyleSheet("""
            QSpinBox {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 2px;
                background: white;

            }
            QSpinBox:hover{
                border: 2px solid #047ad8;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                subcontrol-origin: padding;
                width: 24px;
                border-left: 1px solid #3498db;
                background: #f8f9fa;
            }
            
            QSpinBox::up-button {
                border-left: 1px solid #e1e1e1;
                border-right: 1px solid #cccccc;
                border-top: 1px solid #cccccc;
                border-bottom: 1px solid #cccccc;
                subcontrol-position: top right;
                
                border-top-right-radius: 2px;
            }
            
            QSpinBox::down-button {
                border-left: 1px solid #e1e1e1;
                border-right: 1px solid #cccccc;
                border-bottom: 1px solid #cccccc;
                subcontrol-position: bottom right;
                border-bottom-right-radius: 2px;
            }
            
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 0;
                height: 0;
                image: none;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #e9ecef;
            }
        """)

    def paintEvent(self, event):
        # 先调用父类的绘制
        super().paintEvent(event)
        
        # 获取样式选项
        opt = QStyleOptionSpinBox()
        self.initStyleOption(opt)
        
        # 创建 painter
        painter = QPainter(self)

        font = self.font()  # 获取当前控件的字体
        font.setBold(True)  # 设置字体为加粗
        # font.setPointSize(8)  # 设置字体大小为14点
        painter.setFont(font)
        painter.setPen(Qt.black)
        
        # 获取样式
        style = self.style()
        
        # 绘制 "+" 符号
        up_rect = style.subControlRect(QStyle.CC_SpinBox, opt, QStyle.SC_SpinBoxUp, self)
        painter.drawText(up_rect, Qt.AlignCenter, "+")
        
        # 绘制 "-" 符号
        down_rect = style.subControlRect(QStyle.CC_SpinBox, opt, QStyle.SC_SpinBoxDown, self)
        painter.drawText(down_rect, Qt.AlignCenter, "-")
        
        painter.end()


if __name__ == "__main__":
    # 创建应用实例
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 9))  # 设置默认字体
    
    # 创建并显示窗口
    window = AntiSleepShutdownApp()
    window.show()
    
    sys.exit(app.exec())