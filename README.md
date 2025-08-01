# 🌽 Corn on the Job

## Developers
Developed by **Jamie Sipes & Van Din** at Ruston High School Chapter #617 for the 2025 FBLA Website Coding & Development competition.

## About The Project
Corn on the Job is a dynamic job search application designed to bridge the gap between students at Ruston High School and local employment opportunities. The platform is tailored to support three distinct user roles: students seeking work, employers looking to hire, and administrators who oversee the platform. Our goal is to connect students with meaningful career opportunities by providing a user-friendly platform that makes the job search process simple, efficient, and accessible. We aim to **nurture** growth, **empower** talent, and **help individuals find their perfect job**, *one kernel at a time*.

## Key Features
* **Role-Based Access Control:** Distinct dashboards and functionalities for Students, Employers, and Administrators.
* **Dynamic Job Listings:** Employers can post jobs which are then reviewed and approved by administrators.
* **Student Application System:** Students can browse jobs, submit applications with resume uploads, and track their application history.
* **Employer Dashboard:** Employers can manage their job postings, view their status (pending or approved), and review incoming applications from students.
* **Administrative Panel:** Admins have oversight of the entire platform, with the ability to approve, deny, or delete job postings and monitor site activity.
* **Search and Sort:** Users can search for specific jobs and sort listings to refine their search.
* **Secure Authentication:** User accounts are protected with hashed passwords and a session-based login system.

## User Roles & Features

### Student
A student account allows users to view and apply for approved job postings. The application process is streamlined, enabling students to submit their experience summary, contact details, and resume directly to the employer.

* **Dashboard:** View personal statistics, such as total jobs applied for and recent application activity.
* **Browse & Apply:** Search, sort, and apply for job listings.
* **Save Jobs:** Keep track of interesting opportunities by saving them for later.
* **Track Applications:** View a history of all submitted applications.

*(To test, use Username: `student` and Password: `student`)*

### Employer
An employer account allows local businesses to post job openings. Employers provide a job title, description, company name, logo, and a contact email for applications. All submissions are sent to an administrator for review before being published.

* **Post Jobs:** Create and submit new job listings for administrative review.
* **Manage Postings:** View all submitted jobs and their current status (Approved or Pending Review).
* **View Applications:** Access a dedicated page to see all student applications for their specific job postings.
* **Dashboard:** See an overview of their active listings and total applications received.

*(To test, use Username: `employer` and Password: `employer`)*

### Admin
The admin account has the highest level of control. From a dedicated backend panel, an administrator can approve, deny, or delete any job posting on the platform, ensuring all content is appropriate for students.

* **Review Job Postings:** Approve or deny new job submissions from employers.
* **Manage Live Listings:** Delete any previously approved job posting.
* **Site-Wide Dashboard:** Monitor key metrics like total users, active listings, and pending jobs.

*(To test, use Username: `admin` and Password: `admin`)*

## Technologies Used
* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python with the Flask framework
* **Database:** SQLite
* **Security:** Werkzeug for password hashing and secure filename handling

## Running Corn on the Job on Your Device
COTJ is not currently deployed live, but it can be run on a local machine by following these steps:

1.  Ensure you have Python 3 installed on your system.
2.  Download and install the Flask library. You can do this by running `pip install Flask` in your terminal.
3.  Download or clone the COTJ repository to your computer.
4.  Open the project folder in a code editor like VS Code and run the `server.py` file.
5.  The console will display a local address (it should look something like `http://127.0.0.1:5000`). Ctrl+click or copy-paste this link into your web browser.
6.  You are now running a local instance of Corn on the Job!