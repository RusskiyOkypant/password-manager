import os
import json
import random
import base64
import socket
import tempfile
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from yadisk import YaDisk
import time

class PasswordManager:
    def __init__(self, token, local_file='data/passwords.encrypted', remote_file='password_sync/passwords.encrypted'):
        # Создаём папку для локального файла, если её нет
        local_dir = os.path.dirname(local_file)
        if local_dir and not os.path.exists(local_dir):
            os.makedirs(local_dir)

        self.token = token
        self.local_file = local_file
        self.remote_file = remote_file
        self.data = {'services': {}}
        self.master_password = None
        self.modified = False
        self.has_internet = self.check_internet_connection()
        self.last_activity = time.time()
        self.locked = False
        self._conflict = False

        try:
            self.yandex_disk = YaDisk(token=token)
            try:
                self.yandex_disk.check_token()
                self.token_valid = True
            except:
                self.token_valid = False
                print("Предупреждение: Неверный токен Яндекс.Диска. Синхронизация отключена.")
        except Exception as e:
            print(f"Ошибка инициализации YaDisk: {e}")
            self.yandex_disk = None
            self.token_valid = False

    # ---------- Работа с интернетом и синхронизацией ----------
    def check_internet_connection(self, host="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error:
            return False

    def check_and_download(self):
        if not self.has_internet or not self.token_valid or not self.yandex_disk:
            return False
        try:
            local_exists = os.path.exists(self.local_file)
            try:
                remote_info = self.yandex_disk.get_meta(self.remote_file)
                remote_mtime = remote_info.modified.replace(tzinfo=timezone.utc)
            except Exception:
                return False
            if local_exists:
                local_mtime = datetime.fromtimestamp(
                    os.path.getmtime(self.local_file), tz=timezone.utc
                )
                if remote_mtime > local_mtime:
                    self.yandex_disk.download(self.remote_file, self.local_file)
                    print("Файл успешно загружен с Яндекс.Диска")
                    return True
            else:
                self.yandex_disk.download(self.remote_file, self.local_file)
                print("Файл успешно загружен с Яндекс.Диска")
                return True
        except Exception as e:
            print(f"Ошибка при проверке обновлений: {e}")
            return False

    def upload_if_modified(self):
        if not self.modified or not self.has_internet or not self.token_valid or not self.yandex_disk:
            return False
        try:
            try:
                self.yandex_disk.get_meta('/password_sync')
            except:
                try:
                    self.yandex_disk.mkdir('/password_sync')
                except:
                    pass
            self.yandex_disk.upload(self.local_file, self.remote_file, overwrite=True)
            print("Файл успешно загружен на Яндекс.Диск")
            self.modified = False
            return True
        except Exception as e:
            print(f"Ошибка загрузки на Яндекс.Диск: {e}")
            return False

    # ---------- Криптография ----------
    def _generate_key(self, password, salt):
        password = password.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))

    def _encrypt_data(self, data):
        salt = os.urandom(16)
        key = self._generate_key(self.master_password, salt)
        fernet = Fernet(key)
        encrypted = fernet.encrypt(json.dumps(data).encode())
        return salt + encrypted

    def _decrypt_data(self, encrypted_data):
        salt = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        key = self._generate_key(self.master_password, salt)
        fernet = Fernet(key)
        try:
            decrypted = fernet.decrypt(ciphertext)
            return json.loads(decrypted)
        except:
            return None

    def _load_data(self):
        if not os.path.exists(self.local_file):
            return None
        with open(self.local_file, 'rb') as f:
            encrypted_data = f.read()
        return self._decrypt_data(encrypted_data)

    def _save_data(self):
        self.data['_version'] = self.data.get('_version', 0) + 1
        encrypted = self._encrypt_data(self.data)
        with open(self.local_file, 'wb') as f:
            f.write(encrypted)
        self.modified = True
        self.last_activity = time.time()
        # Бэкап больше не создаётся здесь

    # ---------- Генерация пароля ----------
    def _generate_password(self, custom_password=None):
        if custom_password:
            return custom_password
        symbols = '*&$#?@abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
        return ''.join(random.choice(symbols) for _ in range(20))

    # ---------- Инициализация и разблокировка ----------
    def initialize(self):
        if self.has_internet and self.token_valid:
            try:
                success = self.check_and_download()
                if success:
                    print("Синхронизация с Яндекс.Диском выполнена успешно")
                # Если не удалось, просто молчим (это не критично, если локальный файл существует)
            except Exception as e:
                print(f"Ошибка при инициализации синхронизации: {e}")
        return os.path.exists(self.local_file)

    def unlock_vault(self, password):
        self.master_password = password
        if os.path.exists(self.local_file):
            loaded_data = self._load_data()
            if loaded_data is not None:
                # Конвертация старых записей (если есть поле 'password')
                services = loaded_data.get('services', {})
                for name, data in services.items():
                    if 'password' in data and 'current_password' not in data:
                        data['current_password'] = data.pop('password')
                        if 'history' not in data:
                            data['history'] = []
                        if 'username' not in data:
                            data['username'] = ''
                        if 'notes' not in data:
                            data['notes'] = ''
                self.data = loaded_data
                self.locked = False
                self.last_activity = time.time()
                self._conflict = False

                # Проверяем конфликт с облаком (если есть интернет и токен)
                if self.has_internet and self.token_valid:
                    conflict_status = self._check_remote_conflict()
                    if conflict_status == 'conflict':
                        self._conflict = True
                    elif conflict_status == 'newer_remote':
                        try:
                            self.yandex_disk.download(self.remote_file, self.local_file)
                            loaded_data = self._load_data()
                            if loaded_data is not None:
                                self.data = loaded_data
                                self.modified = False
                                self.last_activity = time.time()
                        except Exception:
                            pass
                return True
        return False

    def create_vault(self, password, confirm_password):
        if password != confirm_password:
            return False
        self.master_password = password
        self._save_data()
        self.create_backup(limit=10)  # <-- добавлено
        if self.has_internet and self.token_valid:
            try:
                self.upload_if_modified()
            except:
                pass
        return True

    # ---------- Управление сервисами (с новыми полями username и notes) ----------
    def add_service(self, service_name, password=None, url=None, username=None, notes=None):
        if service_name in self.data['services']:
            return False
        final_password = password if password else self._generate_password()
        self.data['services'][service_name] = {
            'current_password': final_password,
            'history': [],
            'url': url or "",
            'username': username or "",
            'notes': notes or "",
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_accessed': None
        }
        self._save_data()
        self.create_backup(limit=10)
        return True

    def update_service(self, service_name, new_password=None, new_username=None, new_notes=None):
        if service_name not in self.data['services']:
            return False
        service = self.data['services'][service_name]
        if new_password is not None:
            old_password = service['current_password']
            final_password = new_password if new_password else self._generate_password()
            if old_password != final_password:
                history = service.get('history', [])
                history.append({
                    'password': old_password,
                    'changed_at': datetime.now(timezone.utc).isoformat()
                })
                if len(history) > 5:
                    history.pop(0)
                service['history'] = history
                service['current_password'] = final_password
                service['created_at'] = datetime.now(timezone.utc).isoformat()
        if new_username is not None:
            service['username'] = new_username
        if new_notes is not None:
            service['notes'] = new_notes
        self._save_data()
        self.create_backup(limit=10)
        return True

    def update_service_url(self, service_name, new_url):
        if service_name not in self.data['services']:
            return False
        self.data['services'][service_name]['url'] = new_url
        self._save_data()
        self.create_backup(limit=10)
        return True

    def delete_service(self, service_name):
        if service_name in self.data['services']:
            del self.data['services'][service_name]
            self._save_data()
            self.create_backup(limit=10)
            return True
        return False

    def get_service(self, service_name):
        return self.data['services'].get(service_name)

    def list_services(self):
        return sorted(self.data['services'].keys())

    # ---------- История и отложенная замена ----------
    def generate_pending_password(self, service_name, custom_password=None):
        if service_name not in self.data['services']:
            return None
        final_password = custom_password if custom_password else self._generate_password()
        self.data['services'][service_name]['pending_password'] = final_password
        return final_password

    def confirm_password_change(self, service_name):
        service = self.data['services'].get(service_name)
        if not service:
            return False
        pending = service.get('pending_password')
        if not pending:
            return False
        old_password = service['current_password']
        if old_password == pending:
            service['pending_password'] = None
            self._save_data()
            return True
        history = service.get('history', [])
        history.append({
            'password': old_password,
            'changed_at': datetime.now(timezone.utc).isoformat()
        })
        if len(history) > 5:
            history.pop(0)
        service['history'] = history
        service['current_password'] = pending
        service['pending_password'] = None
        service['created_at'] = datetime.now(timezone.utc).isoformat()
        self._save_data()
        return True

    def cancel_password_change(self, service_name):
        service = self.data['services'].get(service_name)
        if not service:
            return False
        if 'pending_password' in service:
            del service['pending_password']
        return True

    def restore_password_from_history(self, service_name, index=0):
        service = self.data['services'].get(service_name)
        if not service:
            return False
        history = service.get('history', [])
        if not history or index >= len(history):
            return False
        restored_entry = history.pop(index)
        restored_password = restored_entry['password']
        current = service['current_password']
        service['history'].append({
            'password': current,
            'changed_at': datetime.now(timezone.utc).isoformat()
        })
        if len(service['history']) > 5:
            service['history'] = service['history'][-5:]
        service['current_password'] = restored_password
        self._save_data()
        self.create_backup(limit=10)
        return True

    # ---------- Вспомогательные методы ----------
    def get_password_age_status(self, created_at):
        created_date = datetime.fromisoformat(created_at).replace(tzinfo=timezone.utc)
        current_date = datetime.now(timezone.utc)
        age = (current_date - created_date).days
        if age >= 180:
            return "Требуется замена", "red"
        elif age >= 90:
            return "Рекомендуется замена", "orange"
        else:
            return "Актуальный", "green"

    def update_last_accessed(self, service_name):
        if service_name in self.data['services']:
            msk_time = datetime.now(timezone.utc) + timedelta(hours=3)
            self.data['services'][service_name]['last_accessed'] = msk_time.isoformat()
            self._save_data()  # без бэкапа
            return True
        return False

    def get_sync_status(self):
        if not self.has_internet:
            return "⚠ Нет интернета", (1, 0.5, 0, 1)
        elif not self.token_valid:
            return "⚠ Неверный токен", (1, 0.5, 0, 1)
        else:
            return "✓ Синхронизация активна", (0, 0.8, 0, 1)

    # ---------- Автоблокировка ----------
    def update_activity(self):
        self.last_activity = time.time()

    def is_locked(self, timeout_seconds=300):
        if self.master_password is None:
            return True
        if time.time() - self.last_activity > timeout_seconds:
            self.lock()
            return True
        return False

    def lock(self):
        self.master_password = None
        self.locked = True

    def unlock(self, password):
        return self.unlock_vault(password)

    # ---------- Смена мастер-пароля ----------
    def change_master_password(self, old_password, new_password):
        if not self.unlock_vault(old_password):
            return False
        if not new_password or len(new_password) < 4:
            return False
        self.master_password = new_password
        self._save_data()
        self.create_backup(limit=10)
        return True

    # ---------- Экспорт и импорт данных ----------
    def export_data(self, password, format='json', file_path=None):
        if not self.unlock_vault(password):
            return None
        services = self.data.get('services', {})
        if format.lower() == 'json':
            export_data = {
                'exported_at': datetime.now(timezone.utc).isoformat(),
                'services': services
            }
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                return True
            return json_str
        elif format.lower() == 'csv':
            import csv
            from io import StringIO
            output = StringIO()
            writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['Сервис', 'Логин', 'Пароль', 'URL', 'Заметки', 'Создан', 'Последний доступ'])
            for name, data in services.items():
                writer.writerow([
                    name,
                    data.get('username', ''),
                    data.get('current_password', ''),
                    data.get('url', ''),
                    data.get('notes', ''),
                    data.get('created_at', ''),
                    data.get('last_accessed', '')
                ])
            csv_str = output.getvalue()
            if file_path:
                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    f.write(csv_str)
                return True
            return csv_str
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")

    def import_data(self, file_path, password, format='json', merge=False):
        if not self.unlock_vault(password):
            return False
        if not os.path.exists(file_path):
            return False
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if format.lower() == 'json':
            try:
                imported = json.loads(content)
                imported_services = imported.get('services', {})
            except:
                return False
        elif format.lower() == 'csv':
            import csv
            from io import StringIO
            imported_services = {}
            reader = csv.DictReader(StringIO(content), delimiter=';')
            expected_headers = ['Сервис', 'Логин', 'Пароль', 'URL', 'Заметки', 'Создан', 'Последний доступ']
            if reader.fieldnames != expected_headers:
                reader = csv.DictReader(StringIO(content), delimiter=',')
                if reader.fieldnames != expected_headers:
                    return False
            for row in reader:
                name = row.get('Сервис', '').strip()
                if not name:
                    continue
                imported_services[name] = {
                    'current_password': row.get('Пароль', ''),
                    'username': row.get('Логин', ''),
                    'url': row.get('URL', ''),
                    'notes': row.get('Заметки', ''),
                    'created_at': row.get('Создан', datetime.now(timezone.utc).isoformat()),
                    'last_accessed': row.get('Последний доступ', None),
                    'history': []
                }
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")
        if merge:
            for name, data in imported_services.items():
                if name not in self.data['services']:
                    self.data['services'][name] = data
        else:
            self.data['services'] = imported_services
        self._save_data()
        self.create_backup(limit=10)
        return True

    # ---------- Работа с историей сервиса ----------
    def get_service_history(self, service_name):
        service = self.data['services'].get(service_name)
        if not service:
            return []
        return service.get('history', [])

    def clear_service_history(self, service_name):
        service = self.data['services'].get(service_name)
        if not service:
            return False
        service['history'] = []
        self._save_data()
        self.create_backup(limit=10)
        return True

    # ---------- Дополнительные методы для работы с логином/заметками ----------
    def update_service_username(self, service_name, new_username):
        if service_name not in self.data['services']:
            return False
        self.data['services'][service_name]['username'] = new_username
        self._save_data()
        self.create_backup(limit=10)
        return True

    def update_service_notes(self, service_name, new_notes):
        if service_name not in self.data['services']:
            return False
        self.data['services'][service_name]['notes'] = new_notes
        self._save_data()
        self.create_backup(limit=10)
        return True

    # ---------- Генерация пароля с настройками ----------
    def generate_custom_password(self, length=20, use_symbols=True, use_digits=True,
                                 use_uppercase=True, use_lowercase=True):
        chars = ''
        if use_lowercase:
            chars += 'abcdefghijklmnopqrstuvwxyz'
        if use_uppercase:
            chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        if use_digits:
            chars += '1234567890'
        if use_symbols:
            chars += '*&$#?@'
        if not chars:
            return ''
        return ''.join(random.choice(chars) for _ in range(length))

    def generate_password_from_config(self):
        from utils.config import get_config_value
        length = get_config_value('password_length', 20)
        use_symbols = get_config_value('use_symbols', True)
        use_digits = get_config_value('use_digits', True)
        use_uppercase = get_config_value('use_uppercase', True)
        use_lowercase = get_config_value('use_lowercase', True)
        return self.generate_custom_password(length, use_symbols, use_digits, use_uppercase, use_lowercase)

    # ---------- Поиск сервисов ----------
    def search_services(self, query):
        if not query or len(query.strip()) == 0:
            return self.list_services()
        query_lower = query.strip().lower()
        results = []
        for name, data in self.data['services'].items():
            if query_lower in name.lower():
                results.append(name)
                continue
            if query_lower in data.get('username', '').lower():
                results.append(name)
                continue
            if query_lower in data.get('url', '').lower():
                results.append(name)
                continue
            if query_lower in data.get('notes', '').lower():
                results.append(name)
                continue
        return sorted(results)

    # ---------- Обработка конфликтов синхронизации ----------
    def _check_remote_conflict(self):
        if not self.has_internet or not self.token_valid or not self.yandex_disk:
            return 'ok'
        try:
            remote_info = self.yandex_disk.get_meta(self.remote_file)
        except:
            return 'ok'
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name
            self.yandex_disk.download(self.remote_file, tmp_path)
            with open(tmp_path, 'rb') as f:
                encrypted_data = f.read()
            if not self.master_password:
                os.remove(tmp_path)
                return 'error'
            salt = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            key = self._generate_key(self.master_password, salt)
            fernet = Fernet(key)
            decrypted = fernet.decrypt(ciphertext)
            remote_data = json.loads(decrypted)
            remote_version = remote_data.get('_version', 0)
            os.remove(tmp_path)

            local_version = self.data.get('_version', 0)
            if remote_version > local_version:
                if self.modified:
                    return 'conflict'
                else:
                    return 'newer_remote'
            else:
                return 'ok'
        except Exception as e:
            print(f"Ошибка при проверке конфликта: {e}")
            return 'error'

    def resolve_conflict(self, choice='local'):
        if choice == 'local':
            self._save_data()
            self.create_backup(limit=10)
            self.upload_if_modified()
            self.modified = False
            return True
        elif choice == 'remote':
            try:
                self.yandex_disk.download(self.remote_file, self.local_file)
                loaded_data = self._load_data()
                if loaded_data is not None:
                    self.data = loaded_data
                    self.modified = False
                    self.last_activity = time.time()
                    return True
            except Exception as e:
                print(f"Ошибка загрузки облачной версии: {e}")
                return False
        return False

    # ---------- Резервное копирование ----------
    def create_backup(self, backup_dir='backups', limit=10):
        if not os.path.exists(self.local_file):
            return False
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"passwords_{timestamp}.encrypted"
        backup_path = os.path.join(backup_dir, backup_name)
        try:
            import shutil
            shutil.copy2(self.local_file, backup_path)
            print(f"Резервная копия создана: {backup_path}")
            # Удаляем старые копии, оставляя только последние `limit`
            all_backups = self.list_backups(backup_dir)
            if len(all_backups) > limit:
                for old in all_backups[limit:]:
                    os.remove(os.path.join(backup_dir, old))
            return backup_path
        except Exception as e:
            print(f"Ошибка создания резервной копии: {e}")
            return False

    def list_backups(self, backup_dir='backups'):
        if not os.path.exists(backup_dir):
            return []
        files = [f for f in os.listdir(backup_dir) if f.startswith('passwords_') and f.endswith('.encrypted')]
        # Сортируем по дате (имя содержит timestamp)
        files.sort(reverse=True)
        result = []
        for f in files:
            # Извлекаем дату из имени файла
            try:
                timestamp_str = f.replace('passwords_', '').replace('.encrypted', '')
                dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                date_str = dt.strftime("%d.%m.%Y %H:%M:%S")
            except:
                date_str = "Неизвестно"
            result.append({'name': f, 'date': date_str, 'path': os.path.join(backup_dir, f)})
        return result

    def restore_backup(self, backup_name, backup_dir='backups'):
        if not self.master_password:
            return False
        backup_path = os.path.join(backup_dir, backup_name)
        if not os.path.exists(backup_path):
            return False
        try:
            import shutil
            shutil.copy2(backup_path, self.local_file)
            loaded_data = self._load_data()
            if loaded_data is not None:
                self.data = loaded_data
                self.modified = True
                self._save_data()
                return True
            else:
                return False
        except Exception as e:
            print(f"Ошибка восстановления: {e}")
            return False