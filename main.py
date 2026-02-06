from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import pandas as pd
import os
import uuid
import json
import asyncio
import logging
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
from prometheus_client import Counter, Histogram, generate_latest
from langfuse import Langfuse
import time

# Import Agents
from agents.ingestion_agent import IngestionAgent
from agents.profiling_agent import DataProfilingAgent
from agents.cleaning_agent import CleaningAgent
from agents.mapper_agent import MapperAgent
from rag.rag_engine import RAGSystem
from templates_config import get_template_spec

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Settings
class Settings(BaseSettings):
    database_url: str
    redis_url: str
    openai_api_key: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    s3_bucket: Optional[str] = None
    environment: str = "development"
    jwt_secret_key: str = "your-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Initialize FastAPI
app = FastAPI(
    title="AutoInsight API",
    description="AI-Powered Data Cleaning & Analytics System",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Security
security = HTTPBearer()

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
UPLOAD_COUNT = Counter('file_uploads_total', 'Total file uploads')
DASHBOARD_GENERATION_COUNT = Counter('dashboard_generations_total', 'Total dashboard generations')

# Langfuse for MLOps monitoring
langfuse = Langfuse(
    secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
    public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
    host=os.environ.get("LANGFUSE_HOST")
)

# Database connections
def get_db():
    conn = psycopg2.connect(settings.database_url)
    try:
        yield conn
    finally:
        conn.close()

def get_redis():
    return redis.from_url(settings.redis_url)

# S3 client
def get_s3_client():
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        return boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
    return None

# Pydantic models
class UploadResponse(BaseModel):
    message: str
    file_id: str
    filename: str

class DashboardRequest(BaseModel):
    file_id: str
    template_image: str
    api_key: Optional[str] = None

class DashboardResponse(BaseModel):
    status: str
    template: Dict[str, Any]
    mapping: Dict[str, Any]
    data: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

# Global RAG System (cached)
rag_system = None

async def get_rag_system(api_key: Optional[str] = None):
    global rag_system
    key = api_key or settings.openai_api_key
    if key:
        if not rag_system or rag_system.api_key != key:
            rag_system = RAGSystem(api_key=key)
        return rag_system
    return None

# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(duration)
    
    return response

# Routes
@app.get("/", response_class=JSONResponse)
async def root():
    return {"message": "AutoInsight API", "version": "2.0.0"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        # Check database connection
        conn = psycopg2.connect(settings.database_url)
        conn.close()
        
        # Check Redis connection
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        
        return HealthResponse(
            status="healthy",
            timestamp=str(time.time()),
            version="2.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db=Depends(get_db),
    s3_client=Depends(get_s3_client)
):
    UPLOAD_COUNT.inc()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    # Validate file type
    ingestion_agent = IngestionAgent()
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in ingestion_agent.supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {ext}. Supported: {ingestion_agent.supported_extensions}"
        )
    
    file_id = str(uuid.uuid4())
    saved_filename = f"{file_id}{ext}"
    
    try:
        if s3_client and settings.s3_bucket:
            # Upload to S3
            content = await file.read()
            s3_client.put_object(
                Bucket=settings.s3_bucket,
                Key=saved_filename,
                Body=content
            )
            file_location = f"s3://{settings.s3_bucket}/{saved_filename}"
        else:
            # Fallback to local storage
            os.makedirs('uploads', exist_ok=True)
            file_path = os.path.join('uploads', saved_filename)
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            file_location = file_path
        
        # Store file metadata in database
        conn = db
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO files (id, filename, original_filename, file_location, file_size, upload_time)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (file_id, saved_filename, file.filename, file_location, len(content))
        )
        conn.commit()
        
        logger.info(f"File uploaded successfully: {file_id}")
        
        return UploadResponse(
            message="File uploaded successfully",
            file_id=file_id,
            filename=saved_filename
        )
        
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/generate-dashboard", response_model=DashboardResponse)
async def generate_dashboard(
    request: DashboardRequest,
    db=Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    DASHBOARD_GENERATION_COUNT.inc()
    
    if not request.file_id or not request.template_image:
        raise HTTPException(status_code=400, detail="Missing file_id or template_image")
    
    try:
        # Get file info from database
        conn = db
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM files WHERE id = %s", (request.file_id,))
        file_record = cursor.fetchone()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Load data
        ingestion = IngestionAgent()
        if file_record['file_location'].startswith('s3://'):
            # Load from S3
            s3_client = get_s3_client()
            bucket, key = file_record['file_location'][5:].split('/', 1)
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            df = pd.read_csv(obj['Body']) if file_record['filename'].endswith('.csv') else pd.read_excel(obj['Body'])
        else:
            # Load from local file
            df = ingestion.load_file(file_record['file_location'])
        
        # Initialize RAG
        rag = await get_rag_system(request.api_key)
        
        # Langfuse tracking
        generation = langfuse.generation(
            name="dashboard_generation",
            input={
                "file_id": request.file_id,
                "template": request.template_image,
                "data_shape": df.shape
            }
        )
        
        # Profiling & Cleaning
        profiler = DataProfilingAgent(df)
        profile = profiler.column_profile()
        
        cleaner = CleaningAgent(rag_system=rag)
        cleaned_df = cleaner.clean_data(df, profile)
        
        # Get Template Spec
        template_spec = get_template_spec(os.path.basename(request.template_image))
        
        # AI Mapping
        if rag:
            try:
                mapper = MapperAgent(cleaned_df, api_key=rag.api_key)
                mapping = mapper.map_columns(template_spec)
                if not mapping:
                    mapping = heuristic_mapping(cleaned_df, template_spec)
            except Exception as e:
                logger.warning(f"AI mapping failed, using heuristic: {str(e)}")
                mapping = heuristic_mapping(cleaned_df, template_spec)
        else:
            mapping = heuristic_mapping(cleaned_df, template_spec)
        
        # Generate Dashboard Data
        if rag:
            try:
                dashboard_data = mapper.generate_dashboard_data(mapping)
            except Exception as e:
                logger.warning(f"AI data generation failed, using simple: {str(e)}")
                dashboard_data = generate_simple_data(cleaned_df, mapping)
        else:
            dashboard_data = generate_simple_data(cleaned_df, mapping)
        
        # Update Langfuse with results
        generation.end(
            output={
                "mapping": mapping,
                "template": template_spec,
                "data_points": len(dashboard_data)
            }
        )
        
        # Store dashboard generation in database
        cursor.execute(
            """
            INSERT INTO dashboard_generations (file_id, template_image, mapping_data, dashboard_data, generation_time)
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (request.file_id, request.template_image, json.dumps(mapping), json.dumps(dashboard_data))
        )
        conn.commit()
        
        return DashboardResponse(
            status="success",
            template=template_spec,
            mapping=mapping,
            data=dashboard_data
        )
        
    except Exception as e:
        logger.error(f"Dashboard generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/metrics")
async def metrics():
    return generate_latest()

# Helper functions (same as Flask version)
def heuristic_mapping(df, template_spec):
    mapping = {}
    nums = df.select_dtypes(include=['number']).columns.tolist()
    cats = df.select_dtypes(include=['object', 'category']).columns.tolist()
    dates = df.select_dtypes(include=['datetime']).columns.tolist()
    
    if not dates:
        for col in cats:
            if 'date' in col.lower() or 'time' in col.lower():
                dates.append(col)

    for comp in template_spec['components']:
        cid = comp['id']
        ctype = comp['type']
        
        if ctype == 'kpi':
            if nums:
                mapping[cid] = {"column": nums[0], "aggregation": "sum"}
                nums.append(nums.pop(0))
            else:
                mapping[cid] = {"column": None, "aggregation": "count"}
                
        elif ctype in ('line', 'line_chart'):
            if dates and nums:
                mapping[cid] = {"x": dates[0], "y": nums[0], "type": "line"}
            elif len(nums) >= 2:
                 mapping[cid] = {"x": nums[0], "y": nums[1], "type": "line"}
            else:
                mapping[cid] = None
                
        elif ctype in ('bar', 'bar_chart'):
            if cats and nums:
                mapping[cid] = {"x": cats[0], "y": nums[0], "type": "bar"}
            else:
                mapping[cid] = None
                
    return mapping

def generate_simple_data(df, mapping):
    data = {}
    for comp_id, config in mapping.items():
        if not config:
             data[comp_id] = {"value": "N/A", "label": "No Data"}
             continue
             
        if "aggregation" in config:
             col = config["column"]
             if col and col in df.columns:
                 val = df[col].sum() if config["aggregation"] == "sum" else df[col].count()
                 data[comp_id] = {"value": str(round(val, 2)), "label": col}
             else:
                 data[comp_id] = {"value": str(len(df)), "label": "Count"}
        elif "x" in config:
             x = config["x"]
             y = config["y"]
             if x in df.columns and y in df.columns:
                 grp = df.groupby(x)[y].sum().head(10)
                 data[comp_id] = {
                     "type": config.get("type", "bar"),
                     "labels": grp.index.astype(str).tolist(),
                     "datasets": [{"label": y, "data": grp.values.tolist()}]
                 }
    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
