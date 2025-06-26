from fastapi import FastAPI

app = FastAPI(
    title="Multi-Agent AI Platform",
    description="An AI platform for complex goal-oriented tasks using a multi-agent system.",
    version="0.1.0",
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Multi-Agent AI Platform!"}
