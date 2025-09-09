import json
import streamlit as st
import hashlib
import jwt
import time
from typing import Dict, Optional, Tuple

# Путь к файлу с пользователями
USERS_FILE = "users.json"

# Секретный ключ для JWT (в реальном проекте должен быть в .env)
JWT_SECRET = "eduai_hub_secret_key_2024"
JWT_ALGORITHM = "HS256"

def load_users() -> Dict:
    """Загружает пользователей из JSON файла"""
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

def save_users(users: Dict) -> bool:
    """Сохраняет пользователей в JSON файл"""
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def hash_password(password: str) -> str:
    """Хеширует пароль"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, password: str, role: str) -> Tuple[bool, str]:
    """
    Регистрирует нового пользователя
    Возвращает (успех, сообщение)
    """
    users = load_users()
    
    # Проверяем, что пользователь не существует
    if username in users:
        return False, "Пользователь с таким именем уже существует"
    
    # Проверяем валидность роли
    if role not in ["student", "teacher"]:
        return False, "Неверная роль пользователя"
    
    # Создаем нового пользователя
    users[username] = {
        "password_hash": hash_password(password),
        "role": role,
        "created_at": int(time.time())
    }
    
    # Сохраняем
    if save_users(users):
        return True, "Пользователь успешно зарегистрирован"
    else:
        return False, "Ошибка при сохранении пользователя"

def authenticate_user(username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Аутентифицирует пользователя
    Возвращает (успех, сообщение, данные_пользователя)
    """
    users = load_users()
    
    if username not in users:
        return False, "Пользователь не найден", None
    
    user_data = users[username]
    password_hash = hash_password(password)
    
    if user_data["password_hash"] != password_hash:
        return False, "Неверный пароль", None
    
    return True, "Успешная авторизация", user_data

def create_jwt_token(username: str, user_data: Dict) -> str:
    """Создает JWT токен для пользователя"""
    payload = {
        "username": username,
        "role": user_data["role"],
        "created_at": user_data.get("created_at", int(time.time())),
        "exp": int(time.time()) + (24 * 60 * 60)  # Токен действует 24 часа
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def validate_jwt_token(token: str) -> Optional[Dict]:
    """Проверяет JWT токен и возвращает данные пользователя"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "username": payload["username"],
            "role": payload["role"],
            "created_at": payload.get("created_at", "unknown")
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def is_authenticated() -> bool:
    """Проверяет, авторизован ли пользователь"""
    # Проверяем session_state
    if st.session_state.get("authenticated", False):
        return True
    
    # Проверяем JWT токен в URL параметрах
    try:
        query_params = st.query_params
        token = query_params.get("token")
        
        if token:
            user_data = validate_jwt_token(token)
            if user_data:
                # Восстанавливаем данные пользователя
                st.session_state["authenticated"] = True
                st.session_state["user_data"] = user_data
                st.session_state["jwt_token"] = token
                return True
            else:
                # Токен невалиден, очищаем URL
                st.query_params.clear()
    except Exception:
        pass
    
    return False

def get_current_user() -> Optional[Dict]:
    """Возвращает данные текущего пользователя"""
    if is_authenticated():
        return st.session_state.get("user_data")
    return None

def get_current_username() -> str:
    """Возвращает имя текущего пользователя"""
    user_data = get_current_user()
    return user_data.get("username", "Unknown") if user_data else "Unknown"

def get_current_role() -> str:
    """Возвращает роль текущего пользователя"""
    user_data = get_current_user()
    return user_data.get("role", "student") if user_data else "student"

def login_user(username: str, user_data: Dict):
    """Устанавливает пользователя как авторизованного"""
    st.session_state["authenticated"] = True
    st.session_state["user_data"] = {
        "username": username,
        "role": user_data["role"],
        "created_at": user_data.get("created_at", "unknown")
    }
    
    # Создаем JWT токен
    token = create_jwt_token(username, st.session_state["user_data"])
    st.session_state["jwt_token"] = token
    
    # Добавляем токен в URL для персистентности
    try:
        st.query_params["token"] = token
    except Exception:
        pass

def logout_user():
    """Выход пользователя из системы"""
    # Очищаем URL параметры
    try:
        st.query_params.clear()
    except Exception:
        pass
    
    st.session_state["authenticated"] = False
    st.session_state["user_data"] = None
    st.session_state["jwt_token"] = None

def render_login_page():
    """Отображает страницу входа/регистрации"""
    st.set_page_config(page_title="EduAI Hub - Вход", page_icon="🎓", layout="wide")
    
    
    st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
    
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border: 1px solid #eaeaea;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        background: #fff;
    }
    
    .card {
        border: 1px solid #eaeaea;
        border-radius: 16px;
        padding: 16px 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        background: #fff;
        margin-bottom: 12px;
    }
    
    div.stButton > button {
        border-radius: 10px;
        padding: 0.55rem 1rem;
        border: 1px solid #e5e7eb;
        width: 100%;
    }
    
    .muted { color: #6b7280; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)
    
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.title("🎓 EduAI Hub")
        st.markdown("### Платформа для эффективного обучения")
        st.divider()
        
        # Переключатель между входом и регистрацией
        tab_login, tab_register = st.tabs(["Вход", "Регистрация"])
        
        with tab_login:
            st.markdown("### Вход в систему")
            
            with st.form("login_form"):
                username = st.text_input("Имя пользователя", placeholder="Введите ваше имя")
                password = st.text_input("Пароль", type="password", placeholder="Введите пароль")
                
                submitted = st.form_submit_button("Войти", use_container_width=True)
                
                if submitted:
                    if not username or not password:
                        st.error("Пожалуйста, заполните все поля")
                    else:
                        success, message, user_data = authenticate_user(username, password)
                        if success:
                            login_user(username, user_data)
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        
        with tab_register:
            st.markdown("### Регистрация")
            
            with st.form("register_form"):
                new_username = st.text_input("Имя пользователя", placeholder="Выберите имя пользователя", key="reg_username")
                new_password = st.text_input("Пароль", type="password", placeholder="Придумайте пароль", key="reg_password")
                confirm_password = st.text_input("Подтвердите пароль", type="password", placeholder="Повторите пароль", key="reg_confirm")
                role = st.selectbox("Роль", ["student", "teacher"], format_func=lambda x: "Студент" if x == "student" else "Преподаватель")
                
                submitted = st.form_submit_button("Зарегистрироваться", use_container_width=True)
                
                if submitted:
                    if not new_username or not new_password or not confirm_password:
                        st.error("Пожалуйста, заполните все поля")
                    elif new_password != confirm_password:
                        st.error("Пароли не совпадают")
                    elif len(new_password) < 4:
                        st.error("Пароль должен содержать минимум 4 символа")
                    else:
                        success, message = register_user(new_username, new_password, role)
                        if success:
                            st.success(message)
                            st.info("Теперь вы можете войти в систему")
                        else:
                            st.error(message)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Информация о ролях
        st.markdown("---")
        with st.expander("ℹ️ О ролях пользователей"):
            st.markdown("""
            **Студент** — может:
            - Выполнять задания и получать оценки
            - Участвовать в кросс-проверке
            - Просматривать материалы курса
            - Видеть свой прогресс в лидерборде
            
            **Преподаватель** — может:
            - Все возможности студента
            - Загружать материалы курса
            - Просматривать статистику всех студентов
            - Управлять заданиями
            """)

def require_auth():
    """Декоратор для защиты страниц - проверяет авторизацию"""
    if not is_authenticated():
        render_login_page()
        st.stop()