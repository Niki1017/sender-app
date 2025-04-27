import customtkinter as ctk
import threading
import keyboard
import time
import os
import sys
from win10toast import ToastNotifier
from PIL import Image, ImageTk
import requests
import tempfile
import zipfile
import shutil
from packaging import version


class Updater:
    def __init__(self, current_version, repo_url):
        self.current_version = current_version
        self.repo_url = repo_url.rstrip('/')
        self.latest_version = None
        self.update_url = None

    def check_for_updates(self):
        try:
            # Получаем информацию о последнем релизе из GitHub API
            api_url = f"https://api.github.com/repos/{self.repo_url}/releases/latest"
            response = requests.get(api_url)
            response.raise_for_status()
            
            release_info = response.json()
            self.latest_version = release_info['tag_name'].lstrip('v')
            
            # Ищем asset с именем AutoSender_Windows.zip
            for asset in release_info.get('assets', []):
                if "AutoSender_Windows" in asset['name'] and asset['name'].endswith('.zip'):
                    self.update_url = asset['browser_download_url']
                    break
            
            if not self.update_url:
                return False
                
            return version.parse(self.latest_version) > version.parse(self.current_version)
        except Exception as e:
            print(f"Ошибка при проверке обновлений: {e}")
            return False

    def download_update(self):
        try:
            # Создаем временную директорию
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")
            
            # Скачиваем архив с обновлением
            response = requests.get(self.update_url, stream=True)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return zip_path
        except Exception as e:
            print(f"Ошибка при загрузке обновления: {e}")
            return None

    def apply_update(self, zip_path):
        try:
            # Распаковываем архив
            temp_dir = os.path.dirname(zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Находим исполняемый файл обновления
            for file in os.listdir(temp_dir):
                if file.endswith('.exe'):
                    # Заменяем текущий исполняемый файл
                    current_exe = sys.executable
                    new_exe = os.path.join(temp_dir, file)
                    
                    # В Windows нельзя заменить работающий exe, поэтому используем трюк с bat-файлом
                    bat_path = os.path.join(os.path.dirname(current_exe), "update.bat")
                    with open(bat_path, 'w') as bat_file:
                        bat_file.write(f"""
                        @echo off
                        timeout /t 1 /nobreak >nul
                        del "{current_exe}"
                        rename "{new_exe}" "{os.path.basename(current_exe)}"
                        start "" "{current_exe}"
                        del "{bat_path}"
                        """)
                    
                    os.startfile(bat_path)
                    sys.exit(0)
                    return True
        except Exception as e:
            print(f"Ошибка при установке обновления: {e}")
            return False
        finally:
            # Удаляем временные файлы
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

        return False

    def get_version_info(self):
        """Возвращает строку с информацией о версиях"""
        if self.latest_version:
            if version.parse(self.latest_version) > version.parse(self.current_version):
                return f"Текущая версия: {self.current_version} (доступно обновление до {self.latest_version})"
            else:
                return f"Текущая версия: {self.current_version} (актуальная)"
        return f"Текущая версия: {self.current_version}"


class ClaimApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoSender")
        self.root.geometry("600x600")
        self.root.resizable(False, False)
        
        # Установка текущей версии и репозитория
        self.current_version = "1.0.0"  # Замените на актуальную версию
        self.repo_url = "Niki1017/sender-app"  # Замените на ваш репозиторий
        
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
            "AutoSender запущен", 
            "Автоматический отправитель команд готов к работе",
            icon_path=self.notification_icon
        )
        
        # Автоматическая проверка обновлений при запуске (через 3 секунды)
        self.root.after(3000, self.check_updates)

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
        
        # Кнопка проверки обновлений
        self.update_button = ctk.CTkButton(
            self.button_frame,
            text="Проверить обновления",
            command=self.check_updates,
            width=200,
            height=30,
            font=("Verdana", 12),
            fg_color="#1E90FF",
            hover_color="#4682B4"
        )
        self.update_button.pack(pady=10)
        
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
        
        # Обновляем информацию о версии
        self.update_status_with_version()

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
                "AutoSender - Запущено", 
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
                "AutoSender - Остановлено", 
                "Автоматическая отправка команд прекращена",
                icon_path=self.notification_icon
            )

    def send_claim(self, command, interval):
        """Отправляет команду с заданным интервалом"""
        self.log("Подготовка к работе...")
        self.log("У вас есть 10 секунд, чтобы переключиться в нужное окно.")
        
        # Первое уведомление о подготовке (10 секунд)
        self.show_notification(
            "AutoSender - Подготовка", 
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
                        "AutoSender - Команда отправлена",
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
                            "AutoSender - Напоминание",
                            f"До следующей отправки осталось 5 минут\nКоманда: {command}",
                            duration=10,
                            icon_path=self.notification_icon
                        )
                        self.log("Уведомление: До следующей отправки 5 минут")
                    elif i == 60:  # 1 минута
                        self.show_notification(
                            "AutoSender - Напоминание",
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
                    "AutoSender - Ошибка", 
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
        msg = ctk.CTkMessagebox(
            title=title,
            message=message,
            icon="cancel",
            corner_radius=10
        )
        return msg

    def check_updates(self):
        """Проверяет наличие обновлений и предлагает их установить"""
        self.log("Проверка обновлений...")
        updater = Updater(current_version=self.current_version, repo_url=self.repo_url)
        
        try:
            if updater.check_for_updates():
                self.log(f"Доступна новая версия: {updater.latest_version}")
                
                # Спросим пользователя, хочет ли он обновиться
                dialog = ctk.CTkMessagebox(
                    title="Доступно обновление",
                    message=f"Доступна версия {updater.latest_version}. Установить сейчас?",
                    option_1="Да",
                    option_2="Нет",
                    icon="question"
                )
                
                if dialog.get() == "Да":
                    self.log("Загрузка обновления...")
                    zip_path = updater.download_update()
                    
                    if zip_path:
                        self.log("Установка обновления...")
                        if updater.apply_update(zip_path):
                            self.log("Обновление успешно установлено. Приложение будет закрыто.")
                            self.show_notification(
                                "Обновление установлено",
                                "Приложение будет перезапущено с новой версией",
                                icon_path=self.notification_icon
                            )
                            time.sleep(2)
                            self.root.destroy()
                        else:
                            self.log("Ошибка при установке обновления")
                            self.show_notification(
                                "Ошибка обновления",
                                "Не удалось установить обновление",
                                icon_path=self.notification_icon
                            )
                    else:
                        self.log("Ошибка при загрузке обновления")
                        self.show_notification(
                            "Ошибка загрузки",
                            "Не удалось загрузить обновление",
                            icon_path=self.notification_icon
                        )
                else:
                    self.log("Пользователь отказался от обновления")
            else:
                self.log("У вас актуальная версия программы")
                self.show_notification(
                    "Обновлений нет",
                    "У вас установлена последняя версия программы",
                    icon_path=self.notification_icon
                )
        except Exception as e:
            self.log(f"Ошибка при проверке обновлений: {str(e)}")
            self.show_notification(
                "Ошибка проверки обновлений",
                f"Не удалось проверить обновления: {str(e)}",
                icon_path=self.notification_icon
            )
        
        # Обновляем информацию о версии в статус баре
        self.update_status_with_version()

    def update_status_with_version(self):
        """Обновляет статус бар с информацией о версии"""
        updater = Updater(current_version=self.current_version, repo_url=self.repo_url)
        self.status_bar.configure(text=f"Готов к работе | {updater.get_version_info()}")


if __name__ == "__main__":
    root = ctk.CTk()
    app = ClaimApp(root)
    root.mainloop()