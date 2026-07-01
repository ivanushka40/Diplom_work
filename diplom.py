from requests import session
from sqlalchemy import select
from uvicorn import run
from fastapi import FastAPI, HTTPException, Body, Path
from pydantic import BaseModel

from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

app = FastAPI()

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    password: Mapped[str]

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str]
    id_documentation: Mapped[int] = mapped_column()
    id_user: Mapped[int] = mapped_column()


class CreateUser(BaseModel):
    name: str
    password: str
engine = create_async_engine(
    "postgresql+asyncpg://postgres:postgres@127.0.0.1/postgres",
    echo=True,
)


@app.post("/create-all")
async def create_all():
    conn = await engine.connect()
    await conn.run_sync(Base.metadata.create_all)
    await conn.commit()
    await conn.close()

@app.post("/users")
async def create_user(
        data: CreateUser,
):
    conn = await engine.connect()
    session = AsyncSession(conn)
    new_user = User(
        name=data.name,
        password=data.password,
    )
    session.add(new_user)
    await session.flush()
    result = {
        "id": new_user.id,
        "name": data.name,
    }

    await session.commit()
    await conn.close()
    return result

from typing import Annotated

@app.post("/documents")
async def create_document(payload: Annotated[dict,Body()]):
    conn = await engine.connect()
    session = AsyncSession(conn)
    new_document = Document(
        text = payload["text"],
        id_documentation= payload["id_documentation"],

    )
    session.add(new_document)
    await session.flush()
    result = {
        "text": new_document.text, "id": new_document.id, "id_documentation": new_document.id_documentation,
    }
    await conn.commit()
    await conn.close()
    return result



# '''
# POST /documents HTTP/1.1
#
# {"id_documentation":5, "text":"план здания"}
# '''

@app.get("/documents/{id_document}")
async def get_document(id_document: Annotated[int, Path()]):
    conn = await engine.connect()
    session = AsyncSession(conn)
    stmt = (select(Document)
            .where(Document.id == id_document))
    result = await session.execute(stmt)
    rows = result.all()
    if len(documents) == 0:
        raise HTTPException(status_code=404)

    document = rows[0][0]
    result = {
        "id": document.id,
        "texy": document.text,
        "id-document": document.id_document,
        "id_user": document.id_user,
    }
    await conn.close()
    return result

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    conn = await engine.connect()
    session = AsyncSession(conn)
    stmt = (select(User)
            .where(User.id == user_id))
    result = await session.execute(stmt)
    users = result.all()
    if len(users) == 0:
        raise HTTPException(status_code=404)

    user = users[0][0]
    result = {
        "id": user.id,
        "name": user.name,
    }
    await conn.close()
    return result


@app.delete("/documents/{id_document}")
async def delete_document(id_document: int):
    conn = await engine.connect()
    session = AsyncSession(conn)
    stmt = (delete(Document).where(Document.id == id_document))
    await session.execute(stmt)
    await conn.commit()
    await conn.close()

run(app)