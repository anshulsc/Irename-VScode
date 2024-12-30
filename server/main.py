from fastapi import FastAPI

app = FastAPI(
    title = "IRename",
    description="SCAM 2024 Project",
    version="0.1")


@app.get("/")
async def root():
    return{
        "message": "IRename API is successfully running"
    }



from api import renaming
app.include_router(renaming.router)

