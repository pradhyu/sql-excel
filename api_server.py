from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loader import ExcelLoader
import pandas as pd
import os

app = FastAPI(title="Excel-SQLite API", description="REST API for querying Excel files via SQLite")

# Initialize loader with SQLite backend
loader = ExcelLoader(backend='sqlite')

class LoadRequest(BaseModel):
    path: str
    force: bool = False

class QueryRequest(BaseModel):
    query: str

@app.post("/load")
def load_data(request: LoadRequest):
    """Load Excel files from a path."""
    if not os.path.exists(request.path):
        raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
    
    try:
        tables = loader.load_path(request.path, force=request.force)
        return {"status": "success", "loaded_tables": tables, "count": len(tables)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def execute_query(request: QueryRequest):
    """Execute a SQL query."""
    try:
        result = loader.execute_query(request.query)
        if isinstance(result, pd.DataFrame):
            return {
                "status": "success", 
                "type": "data", 
                "data": result.to_dict(orient='records'),
                "columns": list(result.columns),
                "row_count": len(result)
            }
        elif result is None:
             return {"status": "success", "type": "message", "message": "Query executed successfully."}
        else:
             return {"status": "error", "message": str(result)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tables")
def list_tables():
    """List all available tables with metadata."""
    try:
        details = loader.get_table_details()
        return {"tables": details}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema/{table_name}")
def get_schema(table_name: str):
    """Get schema for a specific table."""
    schema = loader.get_schema(table_name)
    if schema:
        return {"table": table_name, "schema": schema}
    else:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
