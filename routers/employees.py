from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends
from db.models.employee import Employee, EmployeeDB, EmployeeResponse
from db.schemas.employeeSchema import employeeScheme, employeesScheme
from db.client import dbClient
import secrets
import string
from passlib.context import CryptContext
from services.mailSender import sendMail
import bcrypt


router = APIRouter(prefix="/employees",
                   tags=["employees"],
                   responses={404: {"message": "not found"} }
)


def searchEmployee(field: str, key):
    try:
        employee = employeeScheme(dbClient.employees.find_one({field: key}))
        return EmployeeResponse(**employee)
    except:
        return {"error": "Employee not found"}

def generatePassword():
    letters = string.ascii_letters
    digits = string.digits
    special_chars = string.punctuation

    alphabet = letters + digits + special_chars

    pwd_length = 12

    pwd = ''
    for i in range(pwd_length):
        pwd += ''.join(secrets.choice(alphabet))
    
    return pwd

def modifyStatusEmployee(username: str, status: bool):
    if type(searchEmployee('username', username)) != EmployeeResponse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User doesnt exist")

    dbClient.employees.find_one_and_update({'username': username}, 
                                           { '$set': {'disabled': status} })
    

# Create a new employee
@router.post("/", status_code=status.HTTP_201_CREATED) #, response_model=Employee
async def newEmployee(employee: EmployeeDB):
    
    if type(searchEmployee('username', employee.username)) == EmployeeResponse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists")
    
    passEmployee = generatePassword()
    employee.password = bcrypt.hashpw(passEmployee.encode('utf-8'), bcrypt.gensalt())
    employee.disabled = False
    employeeDict = dict(employee)
    del employeeDict["id"]
    id = dbClient.employees.insert_one(employeeDict).inserted_id
    newEmployee = employeeScheme(dbClient.employees.find_one({"_id": ObjectId(id)}))
    sendMail(newEmployee['mail'], passEmployee)
    return EmployeeResponse(**newEmployee)

# Get employees
@router.get("/")
async def getEmployees():
    return employeesScheme(dbClient.employees.find())

# Get employees (just enabled)
@router.get("/enabled")
async def getEmployees():
    return employeesScheme(dbClient.employees.find({"disabled": False}))

# Delete employee (disable)
@router.put("/disable/{username}")
async def disableEmployee(username: str):
    modifyStatusEmployee(username, True)
    
# Enable employee
@router.put("/enable/{username}")
async def enableEmployee(username: str):
    modifyStatusEmployee(username, False)
    

# Change password
@router.put("/cp/")
async def changePassword(data: dict):
    if type(searchEmployee('username', data['username'])) != EmployeeResponse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User doesnt exist")
    
    empPass = dbClient.employees.find_one({"username": data['username']})

    if bcrypt.checkpw(data['oldPassword'].encode('utf-8'), empPass['password']):#empPass['password'] == data['oldPassword']:
        dbClient.employees.find_one_and_update({"username": data['username']}, 
                                               { '$set': {"password": bcrypt.hashpw(data['newPassword'].encode('utf-8'), bcrypt.gensalt())}})
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is wrong")
   
