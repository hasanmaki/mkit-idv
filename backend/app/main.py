from pydantic import BaseModel


def main():
    print("Hello from backend!")


if __name__ == "__main__":
    main()


class User(BaseModel):
    id: int
    name: str
    email: str
