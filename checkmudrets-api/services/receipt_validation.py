"""Проверка реквизитов и арифметики без изменения денежных значений."""
import re
import unicodedata
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from pydantic import ValidationError

from schemas.receipt_input import ReceiptInput, ReceiptLine, ReceiptWarning
from utils.formatting import CATEGORY_EMOJI

CENT = Decimal("0.01")
ZERO = Decimal(0)
SERVICE_LINE = re.compile(
    r"^(?:(?:ндс|итого(?:\s+к\s+оплате)?|всего\s+к\s+оплате|к\s+оплате|сдача|скидка|"
    r"наличными|безналичными|электронными|кассир|способ\s+оплаты|оплата\s+картой|"
    r"номер\s+карты|банковская\s+карта|платежная\s+карта|терминал|эквайринг|регистрационный\s+номер)"
    r"(?=$|[\s:%#\d])|(?:инн|кпп|фн|фд|фпд?|ккт|рн\s+ккт)(?=$|[\s:#\d]))", re.IGNORECASE
)


def cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def as_decimal(value) -> Decimal:
    return Decimal(str(value))


def number_text(value: Decimal) -> str:
    return format(value, "f").replace(".", ",")


def is_service(text: str | None) -> bool:
    return bool(text and SERVICE_LINE.match(text.strip()))


def normalize_ocr_name(raw: str | None, proposed: str | None) -> str | None:
    if not raw:
        return None
    cleaned = re.sub(r"^\d+[.)]\s+", "", " ".join(raw.split()))

    def compact(value):
        return "".join(unicodedata.normalize("NFKC", value).casefold().split())

    if proposed and compact(proposed) == compact(cleaned):
        return " ".join(proposed.split())
    return re.sub(r"(?<=\d)\s*(кг|г|мл|л)\b", lambda match: " " + match[1].lower(), cleaned, flags=re.IGNORECASE)


def validate_receipt(receipt: ReceiptInput, today: date | None = None) -> list[ReceiptWarning]:
    today = today or date.today()
    warnings = []
    if receipt.date is None:
        warnings.append(ReceiptWarning(message="Дата покупки неизвестна. Такой чек не участвует в аналитике по датам."))
    elif receipt.date > today:
        warnings.append(ReceiptWarning(message="Дата покупки позже сегодняшнего дня. Проверь дату на чеке.", blocking=True, retry=True))
    if not receipt.items:
        warnings.append(ReceiptWarning(message="Добавь хотя бы одну товарную позицию.", blocking=True, retry=True))
    if receipt.total is None:
        warnings.append(ReceiptWarning(message="Укажи сумму к оплате из чека.", blocking=True))

    for index, line in enumerate(receipt.items, 1):
        def warn(message, **flags):
            warnings.append(ReceiptWarning(item=index, message=f"Позиция {index}. {message}", **flags))

        if not line.name:
            warn("Введи читаемое название товара.", blocking=True)
        if is_service(line.name) or is_service(line.raw_name):
            warn("Похоже на служебную строку. Удали её из товарных позиций.", blocking=True, retry=True)
        if line.category not in CATEGORY_EMOJI:
            warn("Выбери категорию товара.", blocking=True)
        if (line.package_size is None) != (line.package_unit is None):
            warn("Укажи и размер, и единицу упаковки или оставь оба поля пустыми.", blocking=True)
        if line.total is None:
            warn("Укажи оплаченную стоимость позиции.", blocking=True)
        if line.quantity is None or line.price is None:
            warn("Количество или цена за единицу неизвестны. Арифметику позиции нельзя проверить.")
        elif line.total is not None:
            expected = cents(line.quantity * line.price) - (line.discount or ZERO)
            if expected < 0 or abs(expected - line.total) > CENT:
                warn(f"Количество × цена − скидка даёт {number_text(expected)} ₽, в строке указано {number_text(line.total)} ₽.", retry=True)

    if receipt.items and receipt.total is not None and all(line.total is not None for line in receipt.items):
        expected = sum((line.total for line in receipt.items), ZERO) - (receipt.discount or ZERO)
        if expected < 0 or abs(expected - receipt.total) > CENT:
            warnings.append(ReceiptWarning(
                message=f"Позиции за вычетом общей скидки дают {number_text(expected)} ₽, итог на чеке — {number_text(receipt.total)} ₽.", retry=True,
            ))
    return warnings


def from_ocr(payload: dict) -> tuple[ReceiptInput, list[ReceiptWarning]]:
    """Нечитаемые и некорректные поля остаются пустыми до ручной проверки."""
    issues = []

    def clean(model, values, item=None):
        values = {key: value for key, value in values.items() if key in model.model_fields}
        for key, value in values.items():
            if isinstance(value, str):
                values[key] = value.replace("\x00", "").strip() or None
            if key in {"price", "total", "quantity", "package_size", "discount"} and isinstance(values[key], str):
                values[key] = re.sub(r"\s", "", values[key]).replace(",", ".")
        try:
            return model.model_validate(values)
        except ValidationError as exc:
            for error in exc.errors():
                field = error["loc"][0]
                if field != "items":
                    values[field] = None
                    labels = {"date": "дата", "quantity": "количество", "price": "цена", "total": "стоимость", "discount": "скидка"}
                    label = labels.get(field, "реквизит товара")
                    prefix = f"Позиция {item}. " if item else ""
                    issues.append(ReceiptWarning(item=item, message=f"{prefix}Некорректный реквизит: {label}. Проверь оригинал.", retry=True))
            return model.model_validate(values)

    items = []
    raw_items = payload.get("items")
    if isinstance(raw_items, list):
        if len(raw_items) > 120:
            issues.append(ReceiptWarning(message="В обработку вошли первые 120 позиций. Проверь состав чека.", retry=True))
        for raw in raw_items[:120]:
            if not isinstance(raw, dict):
                continue
            if is_service(raw.get("name") if isinstance(raw.get("name"), str) else None) or is_service(
                raw.get("raw_name") if isinstance(raw.get("raw_name"), str) else None
            ):
                continue
            line = clean(ReceiptLine, raw, len(items) + 1)
            name = normalize_ocr_name(line.raw_name, line.name)
            brand = line.brand
            if brand and brand.casefold() not in (line.raw_name or "").casefold():
                brand = None
            items.append(line.model_copy(update={"name": name, "brand": brand}))

    receipt = clean(ReceiptInput, {**payload, "items": items})
    return receipt, issues + validate_receipt(receipt)
