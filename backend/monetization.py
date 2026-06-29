from sqlalchemy.orm import Session

from database import User

INSUFFICIENT_BALANCE_MESSAGE = "餘額不足，請儲值"


def consume_one_diamond(db: Session, user: User) -> bool:
    """每次對話固定扣除 1 顆鑽石。餘額不足時回傳 False。"""
    if user.diamonds_balance <= 0:
        return False

    user.diamonds_balance -= 1
    db.add(user)
    db.commit()
    db.refresh(user)
    return True
