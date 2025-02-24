from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langchain.server import add_routes

app = FastAPI()


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


class MyRunnable(Runnable):
    def invoke(self, input):
        # 实现你的逻辑
        return f"Processed: {input}"

add_routes(app, MyRunnable()) 

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
