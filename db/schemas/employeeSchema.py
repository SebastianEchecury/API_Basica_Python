from datetime import datetime

def employeeScheme(employee) -> dict:  # Con el -> dict defino que devuelvo un dict
    edad = int((datetime.now() - datetime.strptime(employee["birthDate"], "%d/%m/%Y")).days / 365)
    return {"id": str(employee["_id"]), # el id viene como objeto entonces lo transformo en string
            "username": employee["username"],
            "name": employee["name"],
            "lastname": employee["lastname"],
            "mail": employee["mail"],
            "age": edad,
            "birthDate": employee["birthDate"],
            "disabled": employee["disabled"]}

def employeesScheme(employees) -> list:
    emps = list()
    for employee in employees:
        emps.append(employeeScheme(employee))
    return emps
