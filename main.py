from fastapi import FastAPI, UploadFile, File, HTTPException
from bs4 import BeautifulSoup
import re

app = FastAPI()

# In-memory storage dictionary
course_catalog = {}

@app.post("/api/v1/admin/catalog/import")
async def import_catalog(file: UploadFile = File(...)):
    # Read and parse the uploaded HTML file
    contents = await file.read()
    soup = BeautifulSoup(contents, 'html.parser')
    
    # Find the table in the DOM
    table = soup.find('table')
    if not table:
        raise HTTPException(status_code=400, detail="No table found in the uploaded HTML document.")
        
    # Extract all rows, skipping the header row
    rows = table.find_all('tr')[1:]
    
    courses_added = 0
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 5:
            course_code = cols[0].text.strip()
            title = cols[1].text.strip()
            credits_text = cols[2].text.strip()
            prereqs_raw = cols[3].text.strip()
            cross_listed_raw = cols[4].text.strip()
            
            # Use Regex to extract strict course codes (e.g., "COSC 1047") from messy strings
            course_code_pattern = r'[A-Z]{4}\s\d{4}'
            
            prereqs = re.findall(course_code_pattern, prereqs_raw) if prereqs_raw.lower() != 'none' else []
            cross_listed = re.findall(course_code_pattern, cross_listed_raw) if cross_listed_raw.lower() != 'none' else []
            
            # Save to application memory
            course_catalog[course_code] = {
                "course_code": course_code,
                "title": title,
                "credits": int(credits_text) if credits_text.isdigit() else credits_text,
                "prerequisites": prereqs,
                "cross_listed": cross_listed
            }
            courses_added += 1
            
    return {"message": f"Successfully ingested {courses_added} courses into memory."}

@app.get("/api/v1/catalog/courses/{course_code}")
async def get_course(course_code: str):
    # Format the course code to ensure it matches the stored keys (e.g., "COSC 3506")
    formatted_code = course_code[:4].upper() + " " + course_code[4:] if len(course_code) >= 8 and " " not in course_code else course_code.upper()
    
    if formatted_code not in course_catalog:
        raise HTTPException(status_code=404, detail="Course not found in catalog.")
        
    return course_catalog[formatted_code]