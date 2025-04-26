import customtkinter as ctk
import threading
import keyboard
import time
import os
import sys
from win10toast import ToastNotifier
from PIL import Image, ImageTk

class ClaimApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ProgsLand - Автоматический отправитель команд")
        self.root.geometry("900x700")
        self.root.resizable(False, False)
        
        # Пути к иконкам
        self.icon_path = self.resource_path("icon.png")
        self.notification_icon = self.resource_path("notification.ico")
        
        # Установка иконки приложения
        try:
            self.root.iconbitmap(self.icon_path)
        except Exception as e:
            print(f"Не удалось загрузить иконку: {e}")
        
        # Инициализация системы уведомлений
        self.toaster = ToastNotifier()
        
        # Настройка стиля customtkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Шрифты
        self.title_font = ("Verdana", 24, "bold")
        self.label_font = ("Verdana", 14)
        self.button_font = ("Verdana", 14, "bold")
        self.log_font = ("Consolas", 12)
        
        self.running = False
        self.thread = None
        
        self.create_widgets()
        self.center_window()
        
        # Показать уведомление при запуске
        self.show_notification(
            "ProgsLand запущен", 
            "Автоматический отправитель команд готов к работе",
            icon_path=self.notification_icon
        )

    def resource_path(self, relative_path):
        """Получает абсолютный путь к ресурсу для работы с PyInstaller"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)

    def show_notification(self, title, message, duration=5, icon_path=None):
        """Показывает уведомление Windows"""
        try:
            self.toaster.show_toast(
                title,
                message,
                icon_path=icon_path,
                duration=duration,
                threaded=True
            )
        except Exception as e:
            self.log(f"Ошибка уведомления: {str(e)}")

    def center_window(self):
        """Центрирует окно на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """Создает все элементы интерфейса"""
        # Главный контейнер
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Заголовок
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(pady=(10, 20))
        
        # Попробуем загрузить иконку для заголовка
        try:
            icon_image = Image.open(self.icon_path)
            icon_image = icon_image.resize((40, 40), Image.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(icon_image)
            self.logo_label = ctk.CTkLabel(self.header_frame, image=self.logo_image, text="")
            self.logo_label.pack(side="left", padx=10)
        except Exception as e:
            print(f"Не удалось загрузить иконку для интерфейса: {e}")
        
        self.header_label = ctk.CTkLabel(
            self.header_frame, 
            text="Автоматический отправитель команд", 
            font=self.title_font
        )
        self.header_label.pack(side="left", padx=10)
        
        # Панель для ввода команды
        self.command_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.command_frame.pack(fill="x", padx=50, pady=10)
        
        self.command_label = ctk.CTkLabel(
            self.command_frame, 
            text="Команда для отправки:", 
            font=self.label_font
        )
        self.command_label.pack(anchor="w")
        
        self.command_entry = ctk.CTkEntry(
            self.command_frame, 
            width=600, 
            height=40, 
            font=self.label_font,
            placeholder_text="Введите команду, например: /claim"
        )
        self.command_entry.pack(fill="x", pady=5)
        
        # Панель для ввода интервала
        self.interval_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.interval_frame.pack(fill="x", padx=50, pady=10)
        
        self.interval_label = ctk.CTkLabel(
            self.interval_frame, 
            text="Интервал отправки (секунды):", 
            font=self.label_font
        )
        self.interval_label.pack(anchor="w")
        
        self.interval_entry = ctk.CTkEntry(
            self.interval_frame, 
            width=150, 
            height=40, 
            font=self.label_font,
            placeholder_text="60"
        )
        self.interval_entry.pack(fill="x", pady=5)
        
        # Кнопка Start/Stop
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(pady=20)
        
        self.toggle_button = ctk.CTkButton(
            self.button_frame, 
            text="СТАРТ", 
            command=self.toggle_claim, 
            width=200, 
            height=50, 
            font=self.button_font,
            fg_color="#2E8B57",
            hover_color="#3CB371",
            corner_radius=10
        )
        self.toggle_button.pack()
        
        # Таймер
        self.timer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.timer_frame.pack(pady=10)
        
        self.timer_label = ctk.CTkLabel(
            self.timer_frame, 
            text="00:00", 
            font=("Verdana", 24, "bold"),
            text_color="#FFD700"
        )
        self.timer_label.pack()
        
        self.timer_text = ctk.CTkLabel(
            self.timer_frame, 
            text="До следующей отправки:", 
            font=self.label_font
        )
        self.timer_text.pack()
        
        # Текстовое поле для логов
        self.log_frame = ctk.CTkFrame(self.main_frame)
        self.log_frame.pack(fill="both", expand=True, padx=50, pady=(10, 20))
        
        self.log_label = ctk.CTkLabel(
            self.log_frame, 
            text="Журнал событий", 
            font=self.label_font
        )
        self.log_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(
            self.log_frame, 
            width=800, 
            height=200, 
            font=self.log_font,
            wrap="word",
            fg_color="#1E1E1E",
            border_width=2,
            border_color="#3E3E3E"
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Статус бар
        self.status_bar = ctk.CTkLabel(
            self.main_frame, 
            text="Готов к работе", 
            font=("Verdana", 12),
            anchor="w",
            fg_color="#2B2B2B",
            corner_radius=0
        )
        self.status_bar.pack(fill="x", padx=0, pady=(10, 0))

    def toggle_claim(self):
        """Обрабатывает нажатие кнопки старт/стоп"""
        if not self.running:
            command = self.command_entry.get()
            interval = self.interval_entry.get()

            if not command:
                self.show_error("Ошибка", "Пожалуйста, введите команду для отправки.")
                return
                
            if not interval.isdigit() or int(interval) <= 0:
                self.show_error("Ошибка", "Пожалуйста, введите корректный интервал.")
                return

            self.running = True
            self.toggle_button.configure(text="СТОП", fg_color="#B22222", hover_color="#CD5C5C")
            self.status_bar.configure(text="Работаю...")
            
            self.show_notification(
                "ProgsLand - Запущено", 
                f"Автоматическая отправка команды '{command}' каждые {interval} секунд",
                icon_path=self.notification_icon
            )
            
            self.thread = threading.Thread(target=self.send_claim, args=(command, int(interval)), daemon=True)
            self.thread.start()
        else:
            self.running = False
            self.toggle_button.configure(text="СТАРТ", fg_color="#2E8B57", hover_color="#3CB371")
            self.status_bar.configure(text="Остановлено пользователем")
            self.update_timer(0)
            
            self.show_notification(
                "ProgsLand - Остановлено", 
                "Автоматическая отправка команд прекращена",
                icon_path=self.notification_icon
            )

    def send_claim(self, command, interval):
        """Отправляет команду с заданным интервалом"""
        self.log("Подготовка к работе...")
        self.log("У вас есть 10 секунд, чтобы переключиться в нужное окно.")
        
        # Первое уведомление о подготовке (10 секунд)
        self.show_notification(
            "ProgsLand - Подготовка", 
            f"Начинаем через 10 секунд. Переключитесь в нужное окно.\nКоманда: {command}\nИнтервал: {interval} сек",
            duration=10,
            icon_path=self.notification_icon
        )
        
        # Первый таймер всегда 10 секунд
        for i in range(10, 0, -1):
            if not self.running:
                return
            self.update_timer(i)
            time.sleep(1)

        self.log("Начинаем автоматическую отправку команды...")
        
        while self.running:
            try:
                # Отправка команды
                keyboard.write(command)
                keyboard.press_and_release("enter")
                log_msg = f"[{time.strftime('%H:%M:%S')}] Команда отправлена: '{command}'"
                self.log(log_msg)
                
                # Уведомление об отправке (только для интервалов >= 30 сек)
                if interval >= 30:
                    self.show_notification(
                        "ProgsLand - Команда отправлена",
                        log_msg,
                        duration=5,
                        icon_path=self.notification_icon
                    )
                
                # Обратный отсчет основного интервала
                for i in range(interval, 0, -1):
                    if not self.running:
                        return
                    
                    # Уведомления за 5 и 1 минуту
                    if i == 300:  # 5 минут
                        self.show_notification(
                            "ProgsLand - Напоминание",
                            f"До следующей отправки осталось 5 минут\nКоманда: {command}",
                            duration=10,
                            icon_path=self.notification_icon
                        )
                        self.log("Уведомление: До следующей отправки 5 минут")
                    elif i == 60:  # 1 минута
                        self.show_notification(
                            "ProgsLand - Напоминание",
                            f"До следующей отправки осталось 1 минута\nКоманда: {command}",
                            duration=10,
                            icon_path=self.notification_icon
                        )
                        self.log("Уведомление: До следующей отправки 1 минута")
                    
                    self.update_timer(i)
                    time.sleep(1)
                    
            except Exception as e:
                error_msg = f"Ошибка: {str(e)}"
                self.log(error_msg)
                self.show_notification(
                    "ProgsLand - Ошибка", 
                    error_msg,
                    icon_path=self.notification_icon
                )
                self.running = False
                self.root.after(0, lambda: self.toggle_button.configure(
                    text="СТАРТ", 
                    fg_color="#2E8B57",
                    hover_color="#3CB371"
                ))
                self.status_bar.configure(text="Ошибка выполнения")
                break

    def update_timer(self, seconds_left):
        """Обновляет таймер на интерфейсе"""
        minutes, seconds = divmod(seconds_left, 60)
        time_str = f"{minutes:02}:{seconds:02}"
        self.timer_label.configure(text=time_str)
        
        if seconds_left <= 5:
            self.timer_label.configure(text_color="#FF6347")
        else:
            self.timer_label.configure(text_color="#FFD700")

    def log(self, message):
        """Добавляет сообщение в лог"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.root.update_idletasks()
        
    def show_error(self, title, message):
        """Показывает сообщение об ошибке"""
        self.log(f"ОШИБКА: {message}")
        ctk.CTkMessagebox(
            title=title,
            message=message,
            icon="cancel",
            corner_radius=10
        )

if __name__ == "__main__":
    root = ctk.CTk()
    app = ClaimApp(root)
    root.mainloop()