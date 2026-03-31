from fastapi import FastAPI, UploadFile, File, HTTPException
from supabase import create_client
from uuid import uuid4
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("BUCKET_NAME")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Helper: Upload avatar
# -----------------------------
def upload_avatar(file: UploadFile):
    file_ext = file.filename.split(".")[-1]
    file_name = f"{uuid4()}.{file_ext}"

    res = supabase.storage.from_(BUCKET).upload(
        file_name,
        file.file,
        {"content-type": file.content_type}
    )

    if res.get("error"):
        raise HTTPException(status_code=500, detail="Upload failed")

    public_url = supabase.storage.from_(BUCKET).get_public_url(file_name)
    return public_url


# -----------------------------
# CREATE scientist (POST)
# -----------------------------
@app.post("/scientists")
async def create_scientist(
    name: str,
    field: str = "",
    description: str = "",
    avatar: UploadFile = File(None)
):
    avatar_url = None

    if avatar:
        avatar_url = upload_avatar(avatar)

    data = {
        "name": name,
        "field": field,
        "description": description,
        "avatar_url": avatar_url
    }

    result = supabase.table("scientists2").insert(data).execute()

    return result.data


# -----------------------------
# GET all scientists
# -----------------------------
@app.get("/scientists")
def get_scientists():
    result = supabase.table("scientists2").select("*").execute()
    return result.data


# -----------------------------
# GET single scientist
# -----------------------------
@app.get("/scientists/{scientist_id}")
def get_scientist(scientist_id: str):
    result = supabase.table("scientists2") \
        .select("*") \
        .eq("id", scientist_id) \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(404, "Scientist not found")

    return result.data


# -----------------------------
# UPDATE scientist (PATCH)
# -----------------------------
@app.patch("/scientists/{scientist_id}")
async def update_scientist(
    scientist_id: str,
    name: str = None,
    field: str = None,
    description: str = None,
    avatar: UploadFile = File(None)
):
    updates = {}

    if name:
        updates["name"] = name
    if field:
        updates["field"] = field
    if description:
        updates["description"] = description

    if avatar:
        avatar_url = upload_avatar(avatar)
        updates["avatar_url"] = avatar_url

    result = supabase.table("scientists2") \
        .update(updates) \
        .eq("id", scientist_id) \
        .execute()

    return result.data


# -----------------------------
# DELETE scientist
# -----------------------------
@app.delete("/scientists/{scientist_id}")
def delete_scientist(scientist_id: str):
    # Optional: fetch avatar URL to delete file
    record = supabase.table("scientists2") \
        .select("avatar_url") \
        .eq("id", scientist_id) \
        .single() \
        .execute()

    if record.data and record.data["avatar_url"]:
        # Extract file name
        file_name = record.data["avatar_url"].split("/")[-1]
        supabase.storage.from_(BUCKET).remove([file_name])

    result = supabase.table("scientists2") \
        .delete() \
        .eq("id", scientist_id) \
        .execute()

    return {"message": "Deleted"}
