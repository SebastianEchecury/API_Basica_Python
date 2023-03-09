from pydantic import BaseModel

class Employee(BaseModel):
    id: str | None
    username: str
    name: str
    lastname: str
    mail: str


class EmployeeDB(Employee):
    birthDate: str
    disabled: bool | None
    password: str | None
    admin: bool | None


class EmployeeResponse(Employee):
    age: int 