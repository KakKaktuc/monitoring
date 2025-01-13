import tkinter as tk
from tkinter import *
from tkinter import ttk
import psutil
import threading
import mysql.connector as mysql
import time

# Глобальные переменные для управления потоком записи и таймером
recording = False
recording_thread = None
start_time = None
timer_running = False

def update_system_info():
    while True:
        cpu_percent = psutil.cpu_percent(interval=1)
        ram_free = f"{psutil.virtual_memory().free / (1024**2):.2f}"
        ram_total = f"{psutil.virtual_memory().total / (1024**2):.2f}"
        disk_free = f"{psutil.disk_usage('/').free / (1024**3):.2f}"
        disk_total = f"{psutil.disk_usage('/').total / (1024**3):.2f}"

        cpu_label.config(text=f"Загруженность ЦП: {cpu_percent}%")
        ram_label.config(text=f"Использование ОЗУ: {ram_free}/{ram_total} МБ")
        disk_label.config(text=f"Использование ПЗУ: {disk_free}/{disk_total} ГБ")

        time.sleep(1)

def record_system_metrics():
    global recording
    connect = mysql.connect(user='desktop', password='1', host='localhost', database='desktop_records')
    cursor = connect.cursor()

    while recording:
        cpu_percent = psutil.cpu_percent(interval=1)
        ram_free = psutil.virtual_memory().free / (1024**2)
        ram_total = psutil.virtual_memory().total / (1024**2)
        disk_free = psutil.disk_usage('/').free / (1024**3)
        disk_total = psutil.disk_usage('/').total / (1024**3)

        query = "INSERT INTO system_metrics (cpu_percent, ram_free, ram_total, disk_free, disk_total) VALUES (%s, %s, %s, %s, %s)"
        values = (cpu_percent, ram_free, ram_total, disk_free, disk_total)
        cursor.execute(query, values)
        connect.commit()

        time.sleep(1)  # Задержка между записями

    cursor.close()
    connect.close()

def update_timer():
    global start_time, timer_running
    if timer_running:
        elapsed_time = time.time() - start_time
        timer_label.config(text=f"Время записи: {int(elapsed_time)} сек")
        window.after(1000, update_timer)  # Обновление таймера каждую секунду

def start_recording():
    global recording, recording_thread, start_time, timer_running
    recording = True
    start_time = time.time()
    timer_running = True

    recording_thread = threading.Thread(target=record_system_metrics, daemon=True)
    recording_thread.start()

    start_button.pack_forget()  # Скрываем кнопку "Начать запись"
    stop_button.pack()  # Показываем кнопку "Остановить запись"
    timer_label.pack()  # Показываем таймер
    update_timer()  # Запускаем обновление таймера

def stop_recording():
    global recording, timer_running
    recording = False
    timer_running = False

    if recording_thread:
        recording_thread.join()  # Ожидание завершения потока

    stop_button.pack_forget()  # Скрываем кнопку "Остановить запись"
    start_button.pack()  # Показываем кнопку "Начать запись"
    timer_label.config(text="Время записи: 0 сек")  # Сбрасываем таймер

def show_history():
    history_window = Toplevel(window)
    history_window.title("История записей")

    # Создаем Treeview для отображения данных
    columns = ("id", "cpu_percent", "ram_free", "ram_total", "disk_free", "disk_total")
    tree = ttk.Treeview(history_window, columns=columns, show="headings")
    tree.heading("id", text="ID")
    tree.heading("cpu_percent", text="ЦП (%)")
    tree.heading("ram_free", text="ОЗУ свободно (МБ)")
    tree.heading("ram_total", text="ОЗУ всего (МБ)")
    tree.heading("disk_free", text="ПЗУ свободно (ГБ)")
    tree.heading("disk_total", text="ПЗУ всего (ГБ)")

    # Подключаемся к базе данных и получаем данные
    connect = mysql.connect(user='desktop', password='1', host='localhost', database='desktop_records')
    cursor = connect.cursor()
    cursor.execute("SELECT * FROM system_metrics")
    rows = cursor.fetchall()

    # Вставляем данные в Treeview
    for row in rows:
        tree.insert("", "end", values=row)

    tree.pack(fill="both", expand=True)

    cursor.close()
    connect.close()

window = Tk()
window.title("Мониторинг")

info_label = ttk.Label(window, text="Уровень загруженности")
info_label.pack()

cpu_label = ttk.Label(window, text="Загруженность ЦП: ", style="TLabel")
cpu_label.pack()

ram_label = ttk.Label(window, text="Использование ОЗУ: ", style="TLabel")
ram_label.pack()

disk_label = ttk.Label(window, text="Использование ПЗУ: ", style="TLabel")
disk_label.pack()

start_button = tk.Button(window, text="Начать запись", command=start_recording)
start_button.pack()

stop_button = tk.Button(window, text="Остановить запись", command=stop_recording)

timer_label = ttk.Label(window, text="Время записи: 0 сек", style="TLabel")

history_button = tk.Button(window, text="Показать историю", command=show_history)
history_button.pack()

update_thread = threading.Thread(target=update_system_info, daemon=True)
update_thread.start()

window.mainloop()