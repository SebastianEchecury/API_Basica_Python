from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends
from db.models.employee import Employee, EmployeeDB, EmployeeResponse
from db.schemas.employeeSchema import employeeScheme, employeesScheme
from db.client import dbClient
import secrets
import string
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from services.mailSender import sendMail
import bcrypt


router = APIRouter(prefix="/employeesJWT",
                   tags=["employees"],
                   responses={404: {"message": "not found"} }
)


# Encryption algorithm
ALGORITHM = "HS256"
ACCESS_TOKEN_DURATION = 5 # token valid for 5 minutes
# openssl rand -hex 32
SECRET = "9ab9b3b99ecbc593bafb3b603fc9e9fab6b9f8a08d5cc356e8e52681b6c1c2db"

crypt = CryptContext(schemes=["bcrypt"])
oauth2 = OAuth2PasswordBearer(tokenUrl="login")

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
    

async def authEmployee(token: str = Depends(oauth2)):
    exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                              detail="Invalid authentication credentials", 
                              headers={"WWW-Authenticate": "Bearer"})
    try:
        username = jwt.decode(token, SECRET, algorithms=[ALGORITHM]).get("sub") # Me quedo con el parametro sub, luego de decodificar el token
        if username is None:
            raise exception
        
    except JWTError:
        raise exception  
          
    employee = EmployeeDB(**employeeScheme(dbClient.employees.find_one({"username": username})))
    return employee

async def isAdmin(employee: EmployeeDB = Depends(authEmployee)): # De la dependencia recibo un usuario (de authUser)
    if employee.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="User is disabled")
    return employee.admin

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
async def disableEmployee(username: str, admin: bool = Depends(isAdmin)):
    modifyStatusEmployee(username, True)
    
# Enable employee
@router.put("/enable/{username}")
async def enableEmployee(username: str, admin: bool = Depends(isAdmin)):
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
   

@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()): # No busca por username
    employee = dbClient.employees.find_one({"username": form.username})
    if employee['username'] is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect employee")
    
    if not bcrypt.checkpw(form.password.encode('utf-8'), employee['password']):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is incorrect")

    if not employee['admin']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unauthorized")

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_DURATION) 
    accessToken = {"sub": employee['username'],
                   "exp": expire}
                            # Encripto accessToken con el algoritmo ALGORITHM
    return {"access_token": jwt.encode(accessToken, SECRET, algorithm=ALGORITHM), "token_type": "bearer"}


