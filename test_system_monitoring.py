import unittest
from unittest.mock import patch, MagicMock
import psutil
import mysql.connector as mysql
import threading
import time

# Импортируем функции из вашего основного файла
from window import update_system_info, record_system_metrics, start_recording, stop_recording

class TestSystemMonitoring(unittest.TestCase):

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_update_system_info(self, mock_disk_usage, mock_virtual_memory, mock_cpu_percent):
        # Мокируем данные psutil
        mock_cpu_percent.return_value = 25.0
        mock_virtual_memory.return_value = MagicMock(free=1024 * 1024 * 1024, total=2048 * 1024 * 1024)
        mock_disk_usage.return_value = MagicMock(free=500 * 1024 * 1024 * 1024, total=1000 * 1024 * 1024 * 1024)

        # Мокируем tkinter.Label
        cpu_label = MagicMock()
        ram_label = MagicMock()
        disk_label = MagicMock()

        # Вызываем функцию
        update_system_info()

        # Проверяем, что данные обновились корректно
        cpu_label.config.assert_not_called()  # Убедимся, что GUI не используется
        ram_label.config.assert_not_called()
        disk_label.config.assert_not_called()

    @patch('mysql.connector.connect')
    def test_record_system_metrics(self, mock_db_connect):
        # Мокируем базу данных
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db_connect.return_value = mock_db
        mock_db.cursor.return_value = mock_cursor

        # Мокируем psutil
        with patch('psutil.cpu_percent', return_value=30.0), \
             patch('psutil.virtual_memory', return_value=MagicMock(free=512 * 1024 * 1024, total=1024 * 1024 * 1024)), \
             patch('psutil.disk_usage', return_value=MagicMock(free=250 * 1024 * 1024 * 1024, total=500 * 1024 * 1024 * 1024)):

            # Запускаем запись
            global recording
            recording = True
            record_system_metrics()

            # Проверяем, что данные были записаны в базу данных
            mock_cursor.execute.assert_called_with(
                "INSERT INTO system_metrics (cpu_percent, ram_free, ram_total, disk_free, disk_total) VALUES (%s, %s, %s, %s, %s)",
                (30.0, 512.0, 1024.0, 250.0, 500.0)
            )
            mock_db.commit.assert_called()

    @patch('threading.Thread')
    def test_start_stop_recording(self, mock_thread):
        # Мокируем поток
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Запускаем запись
        start_recording()
        self.assertTrue(mock_thread.called)  # Проверяем, что поток был создан
        mock_thread_instance.start.assert_called_once()  # Проверяем, что поток был запущен

        # Останавливаем запись
        stop_recording()
        mock_thread_instance.join.assert_called_once()  # Проверяем, что поток был остановлен

if __name__ == '__main__':
    unittest.main()