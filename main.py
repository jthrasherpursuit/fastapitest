# Import dependencies
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy.engine import URL

# Define SQLMethod classes
class PatientRecordBase(SQLModel):
  firstname: str
  lastname: str 
  middlename: str
  addressln1: str
  addressln2: str
  city: str
  state: str
  zip: str
  phone: str
  email: str

class PatientRecord(PatientRecordBase, table=True):
  id: int | None = Field(default=None, primary_key=True)

class PatientRecordUpdate(SQLModel):
  firstname: str | None = None
  lastname: str | None = None
  middlename: str | None = None
  addressln1: str | None = None
  addressln2: str | None = None
  city: str | None = None
  state: str | None = None
  zip: str | None = None
  phone: str | None = None
  email: str | None = None

# Establish SQL Session
connection_string = 'Driver={ODBC Driver 18 for SQL Server};Server=DESKTOP-UQEA2I0\\MSSQLSERVER01;Database=Test;Trusted_Connection=Yes;Encrypt=Optional'
connection_url = URL.create(
    "mssql+pyodbc", query={"odbc_connect": connection_string}
)
engine = create_engine(connection_url)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# Declare FastAPI functions
app = FastAPI()

## Create new PatientRecord
@app.post("/patients/", status_code=201, response_model=PatientRecord)
def create_record(patient: PatientRecordBase, session: SessionDep):
    db_patient = PatientRecord.model_validate(patient)
    session.add(db_patient)
    session.commit()
    session.refresh(db_patient)
    return db_patient

## Get list of PatientRecords
@app.get("/patients/", response_model=list[PatientRecord])
def read_patients(session: SessionDep):
  patients = session.exec(select(PatientRecord)).all()
  return patients

## Get specific PatientRecord by id
@app.get("/patients/{patient_id}", response_model=PatientRecord)
def read_patient(patient_id: int, session: SessionDep):
   patient = session.get(PatientRecord, patient_id)
   if not patient:
      raise HTTPException(status_code=404, detail="Patient not found")
   return patient

## Update PatientRecord
@app.patch("/patients/{patient_id}", response_model=PatientRecord)
def update_patient(patient_id: int, patient: PatientRecordUpdate, session: SessionDep):
   db_patient = session.get(PatientRecord, patient_id)
   if not db_patient:
      raise HTTPException(status_code=404, detail="Patient not found")
   patient_dump = patient.model_dump(exclude_unset=True)
   db_patient.sqlmodel_update(patient_dump)
   session.add(db_patient)
   session.commit()
   session.refresh(db_patient)
   return db_patient

## Delete PatientRecord
@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: int, session: SessionDep):
   patient = session.get(PatientRecord, patient_id)
   if not patient:
      raise HTTPException(status_code=404, detail="Patient not found")
   session.delete(patient)
   session.commit()
   return {"ok": True}