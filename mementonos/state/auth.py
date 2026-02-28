import reflex as rx
import asyncio
import os
from pathlib import Path
import secrets
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Optional
from mementonos.utils.security import hash_password, create_jwt, decode_jwt, encrypt_master_key
from mementonos.mementonos import app
from sqlmodel import select
from mementonos.models import User, Pair

from mementonos.utils.logger import get_logger 

pair_codes: Dict[str, dict] = {}
logger = get_logger()

RATE_LIMIT = 3
RATE_WINDOW_MIN = 5
ip_attempts = {}

class AuthState(rx.State):
    # UI состояния
    show_modal: bool = False
    modal_type: str = ""  # "login", "create_pair", "find_pair"

    username: str = ""
    password: str = ""
    password_confirm: str = ""
    pair_code_input: str = ""
    generated_code: str = ""
    error_message: str = ""

    time_left: int = 0           # оставшееся время в секундах
    timer_gen: int = 0           # счётчик для идентификации активного таймера (чтобы старые задачи завершались)

    polling_active: bool = False

    authenticated: bool = False
    current_user_id: Optional[int] = None
    # Сессия
    token: str = rx.Cookie(name="mementonos_token", path="/")

    @rx.var(cache=False)
    def raw_token(self) -> str:
        return self.token

    @rx.event
    def check_auth(self):
        if not self.raw_token:
            if self.authenticated or self.current_user_id is not None:
                self.authenticated = False
                self.current_user_id = None
            return

        payload = decode_jwt(self.raw_token)
        sub = payload.get("sub")

        new_authenticated = bool(sub)
        new_user_id = int(sub) if sub else None

        if new_authenticated != self.authenticated or new_user_id != self.current_user_id:
            self.authenticated = new_authenticated
            self.current_user_id = new_user_id

    @rx.event
    def redirect_root_based_on_auth(self):
        if not self.authenticated and self.router.page.path != "/":
            return rx.redirect("/")
        
        return None
    
    @rx.event
    def redirect_feed_based_on_auth(self):
        if self.authenticated and self.router.page.path != "/feed":
            return rx.redirect("/feed")
        
        return None

    def open_login(self):
        self.modal_type = "login"
        self.show_modal = True
        self.clear_form()

    def open_create_pair(self):
        self.modal_type = "create_pair"
        self.show_modal = True
        self.clear_form()

    def open_find_pair(self):
        self.modal_type = "find_pair"
        self.show_modal = True
        self.clear_form()

    def close_modal(self):
        self.show_modal = False
        self.polling_active = False
        self.clear_form()

    def clear_form(self):
        self.username = ""
        self.password = ""
        self.password_confirm = ""
        self.pair_code_input = ""
        if self.generated_code in pair_codes:
            del pair_codes[self.generated_code]
        self.generated_code = ""
        self.error_message = ""

    def get_client_ip(self) -> str:
        if hasattr(self, "router") and hasattr(self.router, "headers"):
            h = self.router.headers
            if hasattr(h, "raw_headers"):
                raw = h.raw_headers
                if hasattr(raw, "_data"):
                    ip = raw._data.get("asgi-scope-client")
                    if ip:
                        return ip

    def check_rate_limit(self) -> bool:
        ip = self.get_client_ip()
        now = datetime.utcnow()

        attempts: deque[datetime] = ip_attempts.setdefault(ip, deque(maxlen=RATE_LIMIT))

        while attempts and now - attempts[0] >= timedelta(minutes=RATE_WINDOW_MIN):
            attempts.popleft()

        if len(attempts) >= RATE_LIMIT:
            oldest = attempts[0]
            wait_sec = (oldest + timedelta(minutes=RATE_WINDOW_MIN) - now).total_seconds()
            wait_min = max(1, round(wait_sec / 60))
            self.error_message = f"Слишком много попыток. Подожди примерно {wait_min} минут."
            return False

        attempts.append(now)
        return True

    def generate_pair_code(self):
        if not self.check_rate_limit():
            return

        if not self.username or len(self.username) < 3:
            self.error_message = "Никнейм минимум 3 символа"
            return
        if self.password != self.password_confirm or len(self.password) < 6:
            self.error_message = "Пароли не совпадают или слишком короткие"
            return

        code = secrets.token_hex(3).upper()
        expires_timestamp = int((datetime.utcnow() + timedelta(minutes=5)).timestamp())
        kdf_salt_creator = os.urandom(16)

        pair_codes[code] = {
            "creator_nick": self.username,
            "hashed_pw": hash_password(self.password),
            "plain_pw": self.password,
            "kdf_salt_creator": kdf_salt_creator,
            "expires": expires_timestamp,
            "ip": self.get_client_ip(),
        }

        self.generated_code = code

        self.time_left = 5 * 60 
        self.timer_gen += 1 # инвалидируем предыдущий таймер (если был)
        yield AuthState.tick # запускаем фоновую задачу
        yield AuthState.poll_for_pair

    @rx.event(background=True)
    async def poll_for_pair(self):
        if not self.username or not self.generated_code:
            return

        async with self:
            self.polling_active = True

        while self.polling_active and self.generated_code:
            if self.router.session.client_token not in app.event_namespace.token_to_sid:
                logger.info('Exiting poll_for_pair')
                break

            await asyncio.sleep(2.5)

            async with self:
                with rx.session() as session:
                    user = session.exec(
                        select(User).where(User.nick == self.username)
                    ).first()

                    if user and user.pair_id is not None:
                        self.token = create_jwt(
                            user_id=user.id,
                            pair_id=user.pair_id
                        )
                        yield AuthState.check_auth
                        self.close_modal()
                        yield rx.redirect("/feed")
                        break
        async with self:
            self.polling_active = False

    def join_pair(self):
        if not self.check_rate_limit():
            return

        if not self.username or len(self.username) < 3:
            self.error_message = "Никнейм минимум 3 символа"
            return
        if self.password != self.password_confirm or len(self.password) < 6:
            self.error_message = "Пароли не совпадают или слишком короткие"
            return

        code = self.pair_code_input.strip().upper()
        if code not in pair_codes:
            self.error_message = "Код не найден или истёк"
            return

        data = pair_codes[code]
        if int(datetime.utcnow().timestamp()) >= data["expires"]:
            del pair_codes[code]
            self.error_message = "Код истёк"
            return

        with rx.session() as session:
            existing = session.exec(select(User).where(User.nick == self.username)).first()
            if existing:
                self.error_message = "Ваш никнейм уже занят"
                return
            
            existing = session.exec(select(User).where(User.nick == data["creator_nick"])).first()
            if existing:
                self.error_message = "Никнейм партнёра уже занят"
                return

            joiner = User(
                nick=self.username,
                hashed_pw=hash_password(self.password),
                kdf_salt=os.urandom(16),
            )
            session.add(joiner)
            session.flush()

            creator = User(
                nick=data["creator_nick"],
                hashed_pw=data["hashed_pw"],
                kdf_salt=os.urandom(16),
            )
            session.add(creator)
            session.flush()

            master_key = os.urandom(32)

            enc_creator = encrypt_master_key(
                master_key,
                data["plain_pw"],
                creator.kdf_salt
                )
            enc_joiner = encrypt_master_key(
                master_key,
                self.password,
                joiner.kdf_salt
            )

            pair = Pair(
                user1_id=creator.id,
                user2_id=joiner.id,
            )
            session.add(pair)
            session.flush()
            
            creator.pair_id = pair.id
            joiner.pair_id = pair.id

            creator.encrypted_master_key = enc_creator
            joiner.encrypted_master_key = enc_joiner

            session.commit()

            base_dir = Path("assets/user_data") / str(pair.id)
            try:
                base_dir.mkdir(parents=True, exist_ok=True)

                (base_dir / "common").mkdir(exist_ok=True)

                (base_dir / str(creator.id)).mkdir(exist_ok=True)
                (base_dir / str(joiner.id)).mkdir(exist_ok=True)

                logger.info(f"Созданы директории для пары {pair.id}: {base_dir}")
            except Exception as e:
                logger.error(f"Ошибка при создании папок для пары {pair.id}: {e}")

            self.token = create_jwt(joiner.id, pair.id)
            yield AuthState.check_auth

        data["plain_pw"] = None
        del pair_codes[code]
        self.close_modal()
        
        yield rx.toast.success("Пара создана! Добро пожаловать.")
        yield rx.redirect("/feed")

    def login(self):
        if not self.username or not self.password:
            self.error_message = "Введите никнейм и пароль"
            return

        with rx.session() as session:
            user = session.exec(
                select(User).where(User.nick == self.username)
            ).first()

            if not user:
                yield rx.toast.error("Неверный пароль или имя пользователя", position="top-right")
                return

            # Проверяем пароль
            if hash_password(self.password) !=user.hashed_pw:
                self.error_message = "Неверный пароль"
                yield rx.toast.error("Неверный пароль", position="top-right")
                return

            pair_id = user.pair_id if user.pair_id else None

            self.token = create_jwt(
                user_id=user.id,
                pair_id=pair_id,
            )
            yield AuthState.check_auth

            self.close_modal()
            self.error_message = ""

            yield rx.toast.success(
                f"Добро пожаловать, {user.nick}!",
                position="top-right",
                duration=4000
            )
            yield rx.redirect("/feed")

    @rx.var
    def time_left_str(self) -> str:
        """Форматирует оставшееся время в ММ:СС"""
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    @rx.event(background=True)
    async def tick(self):
        """Фоновая задача: уменьшает time_left каждую секунду, пока таймер актуален."""
        # Запоминаем идентификатор текущего запуска
        async with self:
            current_gen = self.timer_gen

        while True:
            if self.router.session.client_token not in app.event_namespace.token_to_sid:
                logger.info('Exiting tick')
                break

            async with self:
                # Если таймер устарел (запущен новый) или время вышло — завершаем
                if self.timer_gen != current_gen or self.time_left <= 0:
                    break
            await asyncio.sleep(1)
            async with self:
                # Уменьшаем только если всё ещё актуально и есть что уменьшать
                if self.timer_gen == current_gen and self.time_left > 0:
                    self.time_left -= 1