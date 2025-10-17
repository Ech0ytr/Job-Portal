import pandas as pd          
import json                  
from datetime import datetime 
import ast                   

# Load all CSV files 
def load_data():
    jobs_df = pd.read_csv('data/jobs.csv')
    jobs_detail_df = pd.read_csv('data/jobs_detail.csv')
    companies_df = pd.read_csv('data/companies.csv')
    industries_df = pd.read_csv('data/industries.csv')
    education_df = pd.read_csv('data/education.csv')
    skills_df = pd.read_csv('data/skills.csv')

    return jobs_df, jobs_detail_df, companies_df, industries_df, education_df, skills_df

# Create lookup dictionaries
def create_lookups(companies_df, industries_df, education_df, skills_df):
    # Create lookup dictionaries
    companies_dict = companies_df.set_index('id').to_dict('index')
    industries_dict = industries_df.set_index('id').to_dict('index')
    education_dict = education_df.set_index('id').to_dict('index')
    skills_dict = skills_df.set_index('id')['skill'].to_dict()
    
    # Combine all lookup dicts
    lookups = {
        'companies': companies_dict,
        'industries': industries_dict,
        'education': education_dict,
        'skills': skills_dict
    }

    return lookups

# Convert skill IDs to skill names
def parse_skills(skills_string, skills_dict):
    # Handle missing or NaN skill fields
    if not skills_string or pd.isna(skills_string):
        return []
    
    # Parse JSON-formatted skill IDs
    skill_ids = json.loads(skills_string)

    # Convert each skill ID to its corresponding name
    skill_names = []
    for skill_id in skill_ids:
        if skill_id in skills_dict:
            skill_names.append(skills_dict[skill_id])

    return skill_names

# Convert date strings to ISO format
def convert_date(date_string):
    # Handle missing or invalid date values
    if not date_string or pd.isna(date_string):
        return None

    # Parse date and convert to ISO (YYYY-MM-DD) format
    date_obj = datetime.strptime(date_string, "%m/%d/%Y")

    return date_obj.isoformat()

# Merge and transform job + detail data
def transform_jobs(jobs_df, jobs_detail_df, lookups):
    merged_df = pd.merge(
        jobs_df,
        jobs_detail_df,
        left_on='id',     
        right_on='job_id', 
        how='inner'        
    )

    jobs_list = []

    # Iterate through merged rows to construct job documents
    for index, row in merged_df.iterrows():
    
        # Get company_id from the row
        company_id = row['company_id']

        # Look up company details
        company_info = lookups['companies'][company_id]

        # Get industry_id from company
        industry_id = company_info['industry_id']

        # Look up industry name with error handling
        if industry_id in lookups['industries']:
            industry_name = lookups['industries'][industry_id]['industry_name']
        else:
            # Handle missing industry_id
            industry_name = "Unknown"
            print(f"Warning: Industry ID {industry_id} not found for company {company_id}")

        # Build company object
        company = {
            'company_id': company_id,
            'name': company_info['company_name'],
            'headquarters': company_info['company_headquarters'],
            'size': company_info['company_size'],
            'type': company_info['company_type'],
            'website': company_info['company_website'],
            'description': company_info['company_description'],
            'industry_id': industry_id,
            'industry_name': industry_name
        }

        # Get education_id from the row
        education_id = row['education_id']

        # Look up education details
        education_info = lookups['education'][education_id]

        # Build education object
        education = {
            'education_id': education_id,
            'level': education_info['level'],
            'field': education_info['field']
        }

        # Use the parse_skills function
        skills = parse_skills(row['skills_requirement'], lookups['skills'])

        # Use the convert_date function
        posting_date = convert_date(row['posting_date'])
        closing_date = convert_date(row['closing_date'])

        # Convert to boolean
        remote = row['remote'] == True

        job_doc = {
            'job_id': int(row['id']),  
            'title': row['title'],
            'years_of_experience': row['years_of_experience'],
            'description': row['description'],
            'responsibilities': row['responsibilities'],
            'company': company,
            'education': education,
            'skills': skills,
            'employment_type': row['employment_type'],
            'average_salary': int(row['average_salary']),
            'benefits': row['benefits'],
            'remote': remote,
            'job_posting_url': row['job_posting_url'],
            'posting_date': posting_date,
            'closing_date': closing_date
        }

        jobs_list.append(job_doc)

    return jobs_list

# Transform industries data
def transform_industries(industries_df):   
    # Convert DataFrame to list of dictionaries
    industries_list = industries_df.to_dict('records')
    
    # Rename 'id' to 'industry_id' to match schema
    for industry in industries_list:
        industry['industry_id'] = industry.pop('id')
    
    print(f"✓ Transformed {len(industries_list)} industries")
    return industries_list

# Save transformed data to JSON files
def save_json(data, filename):
    print(f"Saving data to {filename}...")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Successfully saved {filename}")

def main():
    """
    Main execution function.
    Orchestrates the entire transformation process.
    """
    print("="*60)
    print("CareerHub Data Transformation Script")
    print("="*60)
    
    # Step 1: Load all CSV files
    print("\n[1/5] Loading CSV files...")
    jobs_df, jobs_detail_df, companies_df, industries_df, education_df, skills_df = load_data()
    
    # Step 2: Create lookup dictionaries
    print("\n[2/5] Creating lookup dictionaries...")
    lookups = create_lookups(companies_df, industries_df, education_df, skills_df)
    
    # Step 3: Transform jobs data
    print("\n[3/5] Transforming jobs data...")
    jobs = transform_jobs(jobs_df, jobs_detail_df, lookups)
    
    # Step 4: Transform industries data
    print("\n[4/5] Transforming industries data...")
    industries = transform_industries(industries_df)
    
    # Step 5: Save to JSON files
    print("\n[5/5] Saving to JSON files...")
    save_json(jobs, 'jobs.json')
    save_json(industries, 'industries.json')
    
    print("\n" + "="*60)
    print("✓ Transformation Complete!")
    print("="*60)
    print(f"  - {len(jobs)} jobs saved to jobs.json")
    print(f"  - {len(industries)} industries saved to industries.json")
    print("\nNext step: Import into MongoDB")

if __name__ == "__main__":
    # Run the main transformation
    main()
    
    # Optional: Verify the output
    print("\n" + "="*60)
    print("Verification")
    print("="*60)
    
    # Load and check the saved files
    with open('jobs.json', 'r') as f:
        jobs_data = json.load(f)
        print(f"✓ jobs.json contains {len(jobs_data)} documents")
        print(f"  First job: {jobs_data[0]['title']} at {jobs_data[0]['company']['name']}")
    
    with open('industries.json', 'r') as f:
        industries_data = json.load(f)
        print(f"✓ industries.json contains {len(industries_data)} documents")
        print(f"  First industry: {industries_data[0]['industry_name']}")