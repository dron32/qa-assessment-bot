"""AES шифрование для сырых текстов."""

import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)


class TextEncryption:
    """Класс для шифрования/дешифрования текстов."""
    
    def __init__(self):
        self._fernet: Optional[Fernet] = None
        self._initialize_fernet()
    
    def _initialize_fernet(self):
        """Инициализация Fernet для шифрования."""
        settings = get_settings()
        encryption_key = getattr(settings, 'encryption_key', None)
        
        if not encryption_key:
            logger.warning("encryption_key_not_set", action="encryption_init")
            return
            
        try:
            # Если ключ в формате base64, используем как есть
            if len(encryption_key) == 44 and encryption_key.endswith('='):
                key = base64.b64decode(encryption_key)
            else:
                # Иначе генерируем ключ из пароля
                salt = b'qa_assessment_salt'  # В продакшене должен быть уникальный
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
            
            self._fernet = Fernet(key)
            logger.info("encryption_initialized", action="encryption_init")
            
        except Exception as exc:
            logger.error("encryption_init_failed", action="encryption_init", error=str(exc))
            self._fernet = None
    
    def encrypt(self, text: str) -> Optional[str]:
        """Шифрует текст."""
        if not self._fernet or not text:
            return text
            
        try:
            encrypted_bytes = self._fernet.encrypt(text.encode('utf-8'))
            encrypted_text = base64.b64encode(encrypted_bytes).decode('utf-8')
            
            logger.debug("text_encrypted", action="encrypt", text_length=len(text))
            return encrypted_text
            
        except Exception as exc:
            logger.error("encryption_failed", action="encrypt", error=str(exc))
            return text  # Возвращаем исходный текст в случае ошибки
    
    def decrypt(self, encrypted_text: str) -> Optional[str]:
        """Дешифрует текст."""
        if not self._fernet or not encrypted_text:
            return encrypted_text
            
        try:
            # Проверяем, что это зашифрованный текст
            if not encrypted_text.startswith('gAAAAAB') and len(encrypted_text) < 100:
                # Вероятно, это незашифрованный текст
                return encrypted_text
                
            encrypted_bytes = base64.b64decode(encrypted_text.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            decrypted_text = decrypted_bytes.decode('utf-8')
            
            logger.debug("text_decrypted", action="decrypt", text_length=len(decrypted_text))
            return decrypted_text
            
        except Exception as exc:
            logger.error("decryption_failed", action="decrypt", error=str(exc))
            return encrypted_text  # Возвращаем исходный текст в случае ошибки
    
    def is_encrypted(self, text: str) -> bool:
        """Проверяет, зашифрован ли текст."""
        if not text:
            return False
        # Простая эвристика: зашифрованные тексты обычно длинные и содержат base64 символы
        return len(text) > 50 and all(c.isalnum() or c in '+/=' for c in text)


# Глобальный экземпляр
_encryption_instance: Optional[TextEncryption] = None


def get_encryption() -> TextEncryption:
    """Получает глобальный экземпляр шифрования."""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = TextEncryption()
    return _encryption_instance


def encrypt_text(text: str) -> str:
    """Удобная функция для шифрования текста."""
    return get_encryption().encrypt(text) or text


def decrypt_text(encrypted_text: str) -> str:
    """Удобная функция для дешифрования текста."""
    return get_encryption().decrypt(encrypted_text) or encrypted_text


def generate_encryption_key() -> str:
    """Генерирует новый ключ шифрования."""
    key = Fernet.generate_key()
    return base64.b64encode(key).decode('utf-8')
