# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""This is A Customer.

Customer Are A Persons who orders our services or products.

"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    """Customer Model.

    This class represents a customer in the system.

    Attributes:
        id (int): The unique identifier for the customer.
        name (str): The name of the customer.
        email (str): The email address of the customer.
    """

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(15), unique=True, nullable=True)
    telegram_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)

    def __repr__(self) -> str:
        """Return a string representation of the Customer."""
        return f"<Customer id={self.id} name={self.name} email={self.email}>"
