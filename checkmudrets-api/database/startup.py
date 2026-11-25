"""Безопасная диагностика ошибок запуска без текста исключений драйвера."""
import re
import ssl


SQLSTATE_HINTS = {
    "3D000": "Проверь имя базы данных в настройках Session pooler.",
    "42501": "Проверь права роли PostgreSQL на текущем этапе.",
    "42P01": "Проверь наличие таблиц, нужных для миграции.",
    "42703": "Проверь состояние столбцов прикладной схемы.",
    "42704": "Проверь наличие нужных объектов и ролей Supabase.",
    "23505": "Проверь дубликаты перед созданием уникального индекса.",
    "25006": "Проверь, что сервер разрешает изменения схемы.",
    "26000": "Проверь режим Session pooler и порт 5432.",
    "42P05": "Проверь режим Session pooler и порт 5432.",
    "55P03": "Дождись, пока другой запуск или транзакция освободит блокировку.",
    "53300": "Проверь лимиты соединений Supabase.",
}


def startup_failure(stage: str, error: BaseException) -> str:
    chain = []
    current = error
    while current is not None and all(current is not item for item in chain):
        chain.append(current)
        # SQLAlchemy 2.1 хранит ошибку asyncpg в orig, адаптеры 2.0 используют __cause__.
        wrapped = getattr(current, "orig", None)
        current = (
            wrapped if isinstance(wrapped, BaseException)
            else current.__cause__ or (None if current.__suppress_context__ else current.__context__)
        )

    driver = next((item for item in reversed(chain) if type(item).__module__.startswith("asyncpg.")), chain[-1])
    sqlstate = None
    for item in reversed(chain):
        code = getattr(item, "sqlstate", None) or getattr(item, "pgcode", None)
        if isinstance(code, str) and re.fullmatch(r"[0-9A-Z]{5}", code):
            sqlstate = code
            break

    category = stage.split(".", 1)[0]
    hint = SQLSTATE_HINTS.get(sqlstate, "")
    if any(isinstance(item, ssl.SSLError) for item in chain):
        category = "tls"
        hint = "Проверь CA Supabase, имя хоста и срок действия сертификата."
    elif stage == "connect" and sqlstate and sqlstate.startswith("28"):
        category = "authentication"
        hint = "Проверь роль и пароль из строки Session pooler и URL-кодирование пароля."
    elif not hint and stage == "connect":
        hint = "Проверь доступность хоста и порта Session pooler."

    return (
        f"Ошибка запуска БД (stage={stage}, category={category}, "
        f"driver={type(driver).__name__}, sqlstate={sqlstate or '-'}). {hint}"
    ).rstrip()
