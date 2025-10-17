# Job-Portal

# Introduction
Here is a comprehensive explanation that how to setup the job portal, what functions does it have, and how to use it with your local environment.
	The job portal is built based on python functions and Mongodb, which allows the user to search for any information that has been stored in Mongodb with specific information.
	
# Setup
The folder structure looks like:
--Miniproject2 (main folder)
	-- docker-compose.yml
-- data (data folder)
	-- companies.csv
	-- education.csv
	-- industries.csv
	-- jobs_detail.csv
	-- jobs.csv
	-- skills.csv
-- requirements.txt
-- run-app.py
-- run-app_docker.py
-- transform.py
-- app (app folder)
	-- __init__.py
	-- jobs.py
	-- utils.py
	-- __pycache__(pycache folder)

Inside the data folder, we have 6 .csv files. They are all the datasets that we are going to store in Mongodb. Instead of using relational database, we preprocess the datasets into collections before putting them into Mongodb. We first run the transform.py (either within any IDLE or run in the terminal within the miniproject2 folder. The file can transform the 6 .csv files into two json files, as two collections we can use later: jobs and industries. The job collection merges nearly all of the .csvs into the collection itself and is very supportive for search by queries. The industries is mainly based on the industries.csv, where recorded information from the .csv files that is not quite important for jobs collection. 
After we have the two .json files, we are ready to import them to mongodb. We can use ‘docker-compose upto build the container for mongo. Then, use the command ‘docker-compose exec -it mongodb sh’ in another terminal window under the folder miniproject2 to go to the shell window. Inside the shell window, first go to where the .json files are.with ‘cd ds5760/mongo’. Then, use ‘mongoimport --db careerhub --collection jobs --file jobs.json --jsonArray’ and ‘mongoimport --db careerhub --collection industries --file industries.json --jsonArray’ to import the two files into Mongodb. We can now ‘exit’ from the shell window, and run the ‘python run-app.py’. Now, it’s time to open the postman to use our flask app over there. 

Running the flask app
	After we open the postman, we can connect to the localhost:5000 to see what functions within the app. Here, I’m going to use some short texts and screenshot to show 16 different queries and explain about their outputs.

1.	GET + localhost:5000/

<img width="468" height="659" alt="image" src="https://github.com/user-attachments/assets/ac9732ee-98c2-4d9a-b63c-92e9d09198ac" />

This will lead us to a welcome page.

2.	POST + localhost:5000/create/jobPost

<img width="468" height="305" alt="image" src="https://github.com/user-attachments/assets/7b6b305e-14dc-40b5-9453-250c26394122" />

This will create a new job into the job collection. The users will have to enter the field that required (company, title, industry_name), and others are optional.

3.	GET +  localhost:5000/jobs/’job_id’
 
<img width="468" height="339" alt="image" src="https://github.com/user-attachments/assets/7c6819a5-8636-4d1e-af0e-0dd62b976bd0" />

This will find us the detail information of a job by its id (380 is what we’ve just created)

4.	GET + localhost:5000/jobs/industry/Finance

<img width="468" height="318" alt="image" src="https://github.com/user-attachments/assets/afa6051a-e31c-423d-8823-c8dd45920352" />

This will find all the jobs whose industry is finance(Note that ‘finance’ will be case insensitive here

5.	GET + localhost:5000/jobs/salary?min_salary =x&max_salary=y (or either one of them)

<img width="308" height="201" alt="image" src="https://github.com/user-attachments/assets/d85391c1-bc8e-4c4d-b819-a1b9a6a7b8f5" />

This will return the jobs that minimum salary is 80000

<img width="292" height="207" alt="image" src="https://github.com/user-attachments/assets/3a8979fe-97bd-4a3a-b464-aba9eac1f293" />

This will return the jobs that maximum salary is 60000

<img width="280" height="184" alt="image" src="https://github.com/user-attachments/assets/81767589-2b0f-4963-80cd-fa21c966c9ce" />

This will return the jobs that salary is between 50000 & 100000

6.	 GET + localhost:5000/jobs/location/’location_value’

<img width="468" height="248" alt="image" src="https://github.com/user-attachments/assets/03a46a82-e9f4-447d-b978-ee6f5f8c76d3" />

This will return the jobs by specific location(case insensitive)

7.	GET + localhost:5000/jobs/skill/’skill_value’

<img width="468" height="260" alt="image" src="https://github.com/user-attachments/assets/67356c97-d32c-4d6b-a934-30ac8e0129c7" />

This will return the jobs by a single specific skill (case insensitive)

8.	GET + localhost:5000/jobs/skill/’skill_value1’&’skill_value2’&’skill_value3’….

<img width="468" height="416" alt="image" src="https://github.com/user-attachments/assets/37aff008-8cb7-46f1-931c-e2584a6db850" />

This will return the jobs with at least two skills defined (case insensitive)

9.	GET + localhost:5000/jobs/company/’company_name’

<img width="468" height="425" alt="image" src="https://github.com/user-attachments/assets/cf9b197f-037f-4548-9413-02c6f6e5960f" />

This will return the jobs by company name (case insensitive)

10.	GET + localhost:5000/jobs/count-by-industry

<img width="468" height="250" alt="image" src="https://github.com/user-attachments/assets/3ea1717c-0982-4c0b-a393-c8d02d21b22e" />

This will return the number of jobs group by industry

11.	GET + localhost:5000/jobs/top-salary

<img width="486" height="441" alt="image" src="https://github.com/user-attachments/assets/54768430-93c9-4f6a-9124-f47ff0c7d561" />

This will return the jobs with top salary (descending order)

12.	GET + localhost:5000/companies/hiring

<img width="486" height="426" alt="image" src="https://github.com/user-attachments/assets/0237214b-e63b-445a-a680-e2e46b27f00c" />

This will return the company names that are hiring (Alphabetically)

13.	GET + localhost:5000/jobs/degree/Masters

<img width="468" height="283" alt="image" src="https://github.com/user-attachments/assets/fcd2ed08-6e84-4a7b-82e7-84019e0634f3" />

This will return what degree that each job requires (case insensitive)

14.	GET + localhost:5000/jobs/experience?experience_level = ‘level_value’ 

<img width="468" height="517" alt="image" src="https://github.com/user-attachments/assets/2bdf5f3a-8628-4e7e-946a-e8d5f6236775" />

This will return jobs based on specific experience of levels. Here, I set year of experience 1 or 2: entry level; 3-4 mid level; >5 senior level (case insensitive)

15.	PUT + localhost:5000/job/’job_id’

<img width="468" height="488" alt="image" src="https://github.com/user-attachments/assets/4a30dacb-8a3c-462b-921c-0270c33b62d4" />

This will return a message that any field of a job has been updated based on specific job id. Basically the users have to enter the field that wants to be updated. 

16.	DELETE + localhost:5000/job/’job_id’

<img width="468" height="522" alt="image" src="https://github.com/user-attachments/assets/a6aa9544-62be-45fb-a312-d23b1f1f3700" />
 
This will return a message that the job has been deleted based on the job id provided

# Summary
Here is all the detailed setup and commands/functions for this job portal. Hope you have fun with it!

Additional information:
	There are some parts that I used GenAi to support with. They are all the comments, and the examples to input when querying.

