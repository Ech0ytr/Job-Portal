from app import app
from bson.json_util import dumps, loads
from flask import request, jsonify
import json
import ast # helper library for parsing data from string
from importlib.machinery import SourceFileLoader
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import re

# 1. Connect to the client 
client = MongoClient(host="localhost", port=27017)

# Import the utils module
utils = SourceFileLoader('*', './app/utils.py').load_module()

# 2. Select the database
db = client.careerhub # 'use mydb'
# Select the collection
jobs_collection = db.jobs  # Collection: jobs
industries_collection = db.industries

# Convert MongoDB ObjectId to string for JSON serialization
def serialize_doc(doc):
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])  
    return doc

# route decorator that defines which routes should be navigated to this function
@app.route("/") # '/' for directing all default traffic to this function get_initial_response()
def get_initial_response():

    # Message to the user
    message = {
        'apiVersion': 'v1.0',
        'status': '200',
        'message': 'Welcome to Careerhub: Your job portal!'
    }
    resp = jsonify(message)
    # Returning the object
    return resp

# Create a new job post
@app.route("/create/jobPost", methods=['POST'])
def create_job():
    """Function to create new job posting"""
    try:
        # Get JSON data
        try:
            body = request.get_json(force=True)
        except:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate title
        if 'title' not in body or not body['title']:
            return jsonify({"error": "Title is required"}), 400
        
        # Validate company
        if 'company' not in body or 'name' not in body['company']:
            return jsonify({"error": "Company name is required"}), 400
        
        # Validate industry
        if 'industry_name' not in body.get('company', {}):
            return jsonify({"error": "Industry is required"}), 400
        
        # Generate job_id
        max_job = jobs_collection.find_one(sort=[("job_id", -1)])
        new_job_id = (max_job['job_id'] + 1) if max_job else 1
        body['job_id'] = new_job_id
        
        # Insert
        record_created = jobs_collection.insert_one(body)
        
        if record_created:
            return jsonify({
                "message": "Job post created successfully",
                "job_id": new_job_id,
                "inserted_id": str(record_created.inserted_id)
            }), 201
            
    except Exception as e:
        print(e)
        return jsonify({"error": "Server error"}), 500

# Get complete job details by job_id 
@app.route('/jobs/<int:job_id>', methods=['GET'])
def get_job_by_id(job_id):
    """
    Get complete job details by job_id 

    Example:
        GET http://localhost:5000/jobs/0
        Returns job with job_id = 0
    """
    try:
        # Query MongoDB for job with matching job_id
        result = jobs_collection.find_one({"job_id": job_id})
        
        # If document not found
        if not result:
            return jsonify({
                "error": f"Job with ID {job_id} not found",
                "job_id": job_id
            }), 404
        
        # Convert ObjectId to string for JSON serialization
        result = serialize_doc(result)
        
        # Return the job document
        return jsonify(result), 200
    
    except Exception as e:
        # Error while trying to fetch the job
        return jsonify({"error": str(e)}), 500

# Get all jobs in a specific industry 
@app.route('/jobs/industry/<industry_name>', methods=['GET'])
def get_jobs_by_industry(industry_name):
    """
    Get all jobs in a specific industry 
    
    Example:
        GET http://localhost:5000/jobs/industry/Finance
        GET http://localhost:5000/jobs/industry/finance  
        GET http://localhost:5000/jobs/industry/FINANCE  
    """
    try:
        # Query MongoDB using regex for case-insensitive match
        jobs = jobs_collection.find({
            "company.industry_name": {
                "$regex": f"^{industry_name}$",
                "$options": "i"  
            }
        })
        
        # Convert cursor to list
        jobs_list = list(jobs)
        
        # Check if any jobs were found
        if jobs_list:
            # Serialize all jobs 
            jobs_list = [serialize_doc(job) for job in jobs_list]
            
            # Return jobs with count
            return jsonify({
                "industry": industry_name,
                "count": len(jobs_list),
                "jobs": jobs_list
            }), 200
        else:
            # No jobs found for this industry
            return jsonify({
                "error": f"No jobs found for industry: {industry_name}",
                "industry": industry_name,
                "count": 0
            }), 404
    
    except Exception as e:
        # Error while trying to fetch jobs
        return jsonify({"error": str(e)}), 500
    
# Get jobs within a specific salary range
@app.route('/jobs/salary', methods=['GET'])
def get_jobs_by_salary():
    """
    Get jobs within a specific salary range
    
    Example:
        GET http://localhost:5000/jobs/salary?min_salary=50000&max_salary=100000
        GET http://localhost:5000/jobs/salary?min_salary=80000
        GET http://localhost:5000/jobs/salary?max_salary=60000
    """
    try:
        # Use utils to parse query parameters from the URL
        query_params = utils.parse_query_params(request.query_string)
        
        # Extract min and max salary with default values
        min_salary = int(query_params.get('min_salary', 0))
        max_salary = int(query_params.get('max_salary', 999999999))
        
        # Query MongoDB for jobs within the salary range
        jobs = jobs_collection.find({
            "average_salary": {
                "$gte": min_salary,
                "$lte": max_salary
            }
        })
        
        # Convert cursor to list
        jobs_list = list(jobs)
        
        # Check if any jobs were found
        if jobs_list:
            # Serialize all jobs 
            jobs_list = [serialize_doc(job) for job in jobs_list]
            
            # Return jobs with salary range info and count
            return jsonify({
                "salary_range": {
                    "min": min_salary,
                    "max": max_salary
                },
                "count": len(jobs_list),
                "jobs": jobs_list
            }), 200
        else:
            # No jobs found in this salary range
            return jsonify({
                "error": f"No jobs found with salary between ${min_salary} and ${max_salary}",
                "salary_range": {
                    "min": min_salary,
                    "max": max_salary
                },
                "count": 0
            }), 404
    
    except ValueError:
        # Error if salary values cannot be converted to integers
        return jsonify({
            "error": "Invalid salary values. Please provide valid integers.",
            "hint": "Example: /jobs/salary?min_salary=50000&max_salary=100000"
        }), 400
    
    except Exception as e:
        # Error while trying to fetch jobs
        return jsonify({"error": str(e)}), 500
    
# Get all jobs in a specific location 
@app.route('/jobs/location/<location>', methods=['GET'])
def get_jobs_by_location(location):
    """
    Get all jobs in a specific location 
    
    Example:
        GET http://localhost:5000/jobs/location/New York, USA
        GET http://localhost:5000/jobs/location/San Francisco, CA
        GET http://localhost:5000/jobs/location/london, uk  
    """
    try:
        # Query MongoDB using regex for case-insensitive match
        jobs = jobs_collection.find({
            "company.headquarters": {
                "$regex": f"^{location}$",
                "$options": "i"  
            }
        })
        
        # Convert cursor to list
        jobs_list = list(jobs)
        
        # Check if any jobs were found
        if jobs_list:
            # Serialize all jobs 
            jobs_list = [serialize_doc(job) for job in jobs_list]
            
            # Return jobs with location info and count
            return jsonify({
                "location": location,
                "count": len(jobs_list),
                "jobs": jobs_list
            }), 200
        else:
            # No jobs found in this location
            return jsonify({
                "error": f"No jobs found in location: {location}",
                "location": location,
                "count": 0
            }), 404
    
    except Exception as e:
        # Error while trying to fetch jobs
        return jsonify({"error": str(e)}), 500
    
#  Get all jobs that require a specific skill 
@app.route('/jobs/skill/<skill_name>', methods=['GET'])
def get_jobs_by_skill(skill_name):
    """
    Get all jobs that require a specific skill 
    
    Example:
        GET http://localhost:5000/jobs/skill/Python
        GET http://localhost:5000/jobs/skill/python 
        GET http://localhost:5000/jobs/skill/Excel
        GET http://localhost:5000/jobs/skill/Machine Learning
    """
    try:
        # Query MongoDB for jobs where skills array contains the skill
        jobs = jobs_collection.find({
            "skills": {
                "$regex": f"^{skill_name}$",
                "$options": "i"  
            }
        })
        
        # Convert cursor to list
        jobs_list = list(jobs)
        
        # Check if any jobs were found
        if jobs_list:
            # Serialize all jobs 
            jobs_list = [serialize_doc(job) for job in jobs_list]
            
            # Return jobs with skill info and count
            return jsonify({
                "skill": skill_name,
                "count": len(jobs_list),
                "jobs": jobs_list
            }), 200
        else:
            # No jobs found requiring this skill
            return jsonify({
                "error": f"No jobs found requiring skill: {skill_name}",
                "skill": skill_name,
                "count": 0
            }), 404
    
    except Exception as e:
        # Error while trying to fetch jobs
        return jsonify({"error": str(e)}), 500
    
# Get all jobs that require ALL of the specified skills
@app.route('/jobs/skills/<skill_names>', methods=['GET'])
def get_jobs_by_multiple_skills(skill_names):
    """
    Get all jobs that require AT LEAST 2 of the specified skills.

    Example:
        GET /jobs/skills/Python&SQL&JAVA
        GET /jobs/skills/Excel&Communication
        GET /jobs/skills/Python&Machine%20Learning&SQL
    """
    try:
        # Split the skill_names string by '&' delimiter
        skills_list = skill_names.split('&')
        skills_list = [skill.strip() for skill in skills_list if skill.strip()]

        if len(skills_list) < 2:
            return jsonify({
                "error": "Please provide at least two skills to match.",
                "skills_provided": skills_list
            }), 400

        # Build $or query for MongoDB
        skill_conditions = [
            {"skills": {"$regex": f"^{re.escape(skill)}$", "$options": "i"}}
            for skill in skills_list
        ]

        # Query jobs that match ANY of the skills
        jobs_cursor = jobs_collection.find({"$or": skill_conditions})

        # Filter jobs that match AT LEAST 2 of the skills
        matched_jobs = []
        for job in jobs_cursor:
            job_skills = job.get("skills", [])
            match_count = sum(
                any(re.fullmatch(skill, s, re.IGNORECASE) for s in job_skills)
                for skill in skills_list
            )
            if match_count >= 2:
                matched_jobs.append(serialize_doc(job))

        # Return results
        if matched_jobs:
            return jsonify({
                "skills_required": skills_list,
                "count": len(matched_jobs),
                "jobs": matched_jobs
            }), 200
        else:
            return jsonify({
                "error": f"No jobs found requiring at least 2 of: {', '.join(skills_list)}",
                "skills_required": skills_list,
                "count": 0
            }), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all jobs posted by a specific company 
@app.route('/jobs/company/<company_name>', methods=['GET'])
def get_jobs_by_company(company_name):
    """
    Get all jobs posted by a specific company 
    
    Example:
        GET http://localhost:5000/jobs/company/Quantum Finance Group
        GET http://localhost:5000/jobs/company/quantum finance group  
        GET http://localhost:5000/jobs/company/Google
        GET http://localhost:5000/jobs/company/Microsoft
    """
    try:
        # Query MongoDB for jobs where company name matches
        jobs = jobs_collection.find({
            "company.name": {
                "$regex": f"^{company_name}$",
                "$options": "i"  
            }
        })
        
        # Convert cursor to list
        jobs_list = list(jobs)
        
        # Check if any jobs were found
        if jobs_list:
            # Serialize all jobs 
            jobs_list = [serialize_doc(job) for job in jobs_list]
            
            # Return jobs with company info and count
            return jsonify({
                "company": company_name,
                "count": len(jobs_list),
                "jobs": jobs_list
            }), 200
        else:
            # No jobs found from this company
            return jsonify({
                "error": f"No jobs found from company: {company_name}",
                "company": company_name,
                "count": 0
            }), 404
    
    except Exception as e:
        # Error while trying to fetch jobs
        return jsonify({"error": str(e)}), 500

# Get count of jobs per industry, sorted by count (descending)
@app.route('/jobs/count-by-industry', methods=['GET'])
def count_jobs_by_industry():
    """
    Get count of jobs per industry, sorted by count (descending)
    
    Example:
        GET http://localhost:5000/jobs/count-by-industry
    """
    try:
        # Use MongoDB aggregation pipeline to group and count
        pipeline = [
            # Stage 1: Group by industry_name and count
            {
                "$group": {
                    "_id": "$company.industry_name",  
                    "job_count": {"$sum": 1}          
                }
            },
            # Stage 2: Sort by job_count in descending order 
            {
                "$sort": {"job_count": -1}
            },
            # Stage 3: Reshape the output to have cleaner field names
            {
                "$project": {
                    "_id": 0,                          
                    "industry": "$_id",                
                    "job_count": 1                     
                }
            }
        ]
        
        # Execute the aggregation pipeline
        result = list(jobs_collection.aggregate(pipeline))
        
        # Return the aggregated results
        return jsonify({
            "total_industries": len(result),
            "industries": result
        }), 200
    
    except Exception as e:
        # Error while trying to aggregate
        return jsonify({"error": str(e)}), 500
    
# Get the top 5 highest-paying jobs
@app.route('/jobs/top-salary', methods=['GET'])
def get_top_salary_jobs():
    """
    Get the top 5 highest-paying jobs
    
    Example:
        GET http://localhost:5000/jobs/top-salary
    """
    try:
        # Query MongoDB with sort and limit
        # Sort by average_salary descending (-1), then by job_id ascending (1) for deterministic ties
        jobs = jobs_collection.find().sort([
            ("average_salary", -1), 
            ("job_id", 1)            
        ]).limit(5)                 
        
        # Convert cursor to list
        jobs_list = list(jobs)
        
        # Serialize all jobs 
        jobs_list = [serialize_doc(job) for job in jobs_list]
        
        # Return top 5 jobs
        return jsonify({
            "count": len(jobs_list),
            "top_jobs": jobs_list
        }), 200
    
    except Exception as e:
        # Error while trying to fetch jobs
        return jsonify({"error": str(e)}), 500
    
# Get a unique list of companies that currently have at least one open job
@app.route('/companies/hiring', methods=['GET'])
def get_companies_hiring():
    """
    Get a unique list of companies that currently have at least one open job
    
    Example:
        GET http://localhost:5000/companies/hiring
    """
    try:
        # Use MongoDB distinct() to get unique company names
        company_names = jobs_collection.distinct("company.name")
        
        # Sort the list alphabetically (case-insensitive)
        company_names_sorted = sorted(company_names, key=str.lower)
        
        # Return the sorted list of companies
        return jsonify({
            "count": len(company_names_sorted),
            "companies": company_names_sorted
        }), 200
    
    except Exception as e:
        # Error while trying to fetch companies
        return jsonify({"error": str(e)}), 500
    
# Get all jobs that require a specific degree level
@app.route('/jobs/degree/<degree_name>', methods=['GET'])
def get_jobs_by_degree(degree_name):
    """
    Get all jobs that require a specific degree level 
    
    Example:
        GET http://localhost:5000/jobs/degree/Bachelors
        GET http://localhost:5000/jobs/degree/bachelors  
        GET http://localhost:5000/jobs/degree/Masters
        GET http://localhost:5000/jobs/degree/PhD
        GET http://localhost:5000/jobs/degree/Diploma
    """
    try:
        # Query MongoDB for jobs where education level matches
        jobs = jobs_collection.find({
            "education.level": {
                "$regex": f"^{degree_name}$",
                "$options": "i"  
            }
        })
        
        # Convert cursor to list
        jobs_list = list(jobs)
        
        # Check if any jobs were found
        if jobs_list:
            # Serialize all jobs 
            jobs_list = [serialize_doc(job) for job in jobs_list]
            
            # Return jobs with degree info and count
            return jsonify({
                "degree": degree_name,
                "count": len(jobs_list),
                "jobs": jobs_list
            }), 200
        else:
            # No jobs found requiring this degree
            return jsonify({
                "error": f"No jobs found requiring degree: {degree_name}",
                "degree": degree_name,
                "count": 0
            }), 404
    
    except Exception as e:
        # Error while trying to fetch jobs
        return jsonify({"error": str(e)}), 500
    
# Get jobs based on experience level requirement
@app.route('/jobs/experience', methods=['GET'])
def get_jobs_by_experience():
    """
    Get jobs based on experience level derived from 'years_of_experience' field.

    Example:
        GET /jobs/experience?experience_level=Entry Level
        GET /jobs/experience?experience_level=Mid Level
        GET /jobs/experience?experience_level=Senior Level
    """
    try:
        # Parse query parameters
        query_params = utils.parse_query_params(request.query_string)
        experience_level = query_params.get('experience_level', '').strip().lower()

        if not experience_level:
            return jsonify({
                "error": "experience_level parameter is required",
                "hint": "Example: /jobs/experience?experience_level=Entry Level"
            }), 400

        # Fetch all jobs
        jobs_cursor = jobs_collection.find({})
        matched_jobs = []

        for job in jobs_cursor:
            exp_str = job.get("years_of_experience", "")
            if '-' not in exp_str:
                continue  # skip malformed entries

            try:
                lower_bound = int(exp_str.split('-')[0])
            except ValueError:
                continue  # skip non-numeric entries

            # Match based on experience level
            if experience_level == "entry level" and lower_bound in [1, 2]:
                matched_jobs.append(serialize_doc(job))
            elif experience_level == "mid level" and 2 < lower_bound < 5:
                matched_jobs.append(serialize_doc(job))
            elif experience_level == "senior level" and lower_bound >= 5:
                matched_jobs.append(serialize_doc(job))

        if matched_jobs:
            return jsonify({
                "experience_level": experience_level.title(),
                "count": len(matched_jobs),
                "jobs": matched_jobs
            }), 200
        else:
            return jsonify({
                "error": f"No jobs found for experience level: {experience_level.title()}",
                "experience_level": experience_level.title(),
                "count": 0
            }), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
# Partially update a job posting by job_id
@app.route('/job/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    """
    Partially update a job posting by job_id
    
    Example:
        PUT http://localhost:5000/job/0
        Body: {"average_salary": 95000, "remote": false}
    """
    try:
        # Get JSON data from request body
        body = request.get_json(force=True)
        if not body:
            return jsonify({"error": "No data provided or invalid JSON"}), 400

        # Validate that body is not empty
        if not body:
            return jsonify({"error": "Request body cannot be empty"}), 400
        
        # Remove job_id from body if present 
        if 'job_id' in body:
            body.pop('job_id')
            
        # If body is now empty after removing job_id, return error
        if not body:
            return jsonify({
                "error": "No valid fields to update",
                "hint": "job_id cannot be updated. Provide other fields."
            }), 400
        
        # Define allowed fields 
        allowed_fields = [
            'title', 'years_of_experience', 'description', 'responsibilities',
            'company', 'education', 'skills', 'employment_type', 'average_salary',
            'benefits', 'remote', 'job_posting_url', 'posting_date', 'closing_date'
        ]
        
        # Check for unknown fields 
        unknown_fields = [field for field in body.keys() if field not in allowed_fields]
        if unknown_fields:
            return jsonify({
                "error": f"Unknown fields: {', '.join(unknown_fields)}",
                "allowed_fields": allowed_fields
            }), 400
        
        # Build the update operation using $set
        update_operation = {"$set": body}
        
        # Update the job in MongoDB
        result = jobs_collection.update_one(
            {"job_id": job_id},      
            update_operation         
        )
        
        # Check if job was found and updated
        if result.matched_count == 0:
            # No job found with this job_id
            return jsonify({
                "error": f"Job with ID {job_id} not found",
                "job_id": job_id
            }), 404
        
        # Check if any modifications were actually made
        if result.modified_count > 0:
            # Job was updated successfully
            return jsonify({
                "message": "Job updated successfully",
                "job_id": job_id,
                "updated_fields": list(body.keys())
            }), 200
        else:
            # Job was found but no changes were made 
            return jsonify({
                "message": "No modifications made (values unchanged)",
                "job_id": job_id,
                "fields_checked": list(body.keys())
            })
        
    except Exception as e:
        # Error while trying to update job
        print(e)
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    
# Delete a job posting by job_id
@app.route('/job/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """
    Delete a job posting by job_id
    
    Example:
        DELETE http://localhost:5000/job/381
    """
    try:
        # Delete the job from MongoDB
        result = jobs_collection.delete_one({"job_id": job_id})
        
        # Check if a job was actually deleted
        if result.deleted_count > 0:
            # Job was found and deleted successfully
            return jsonify({
                "message": "Job deleted successfully",
                "job_id": job_id
            }), 200
        else:
            # No job found with this job_id
            return jsonify({
                "error": f"Job with ID {job_id} not found",
                "job_id": job_id
            }), 404
    
    except Exception as e:
        # Error while trying to delete job
        print(e)
        return jsonify({"error": f"Server error: {str(e)}"}), 500