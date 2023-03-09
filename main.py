from fastapi import FastAPI
from routers import employees, employees_jwt_auth

app = FastAPI()

app.include_router(employees.router)
app.include_router(employees_jwt_auth.router)


@app.get("/")
async def root():
    return "Hola Mundo"#{"message": "Hola Mundo2"}