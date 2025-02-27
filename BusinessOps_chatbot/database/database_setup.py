import sqlite3

# Connect to SQLite database (creates the file if it doesn't exist)
conn = sqlite3.connect("talent_management.db")
cursor = conn.cursor()


cursor.execute("PRAGMA foreign_keys = ON;")

# Create the table (Ensuring compatibility with SQLite)
cursor.execute("""
CREATE TABLE IF NOT EXISTS company (
    id INTEGER PRIMARY KEY,
    company_name TEXT NOT NULL,
    company_category TEXT,
    company_turnover TEXT,
    email TEXT UNIQUE,
    number_of_employee TEXT,
    phone TEXT,
    company_address TEXT,
    msme_registration_no TEXT,
    gst_registration_no TEXT,
    linkedin_url TEXT,
    company_website TEXT,
    about_company TEXT,
    is_active INTEGER,
    plan_id INTEGER,
    expire_date DATE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    company_id INTEGER,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    phone TEXT,
    user_type INTEGER,
    is_active INTEGER,
    department TEXT,
    permission TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS add_profile (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    company_id INTEGER,
    profile_name TEXT,
    job_title TEXT,
    professional_summary TEXT,
    key_skill TEXT,
    experience TEXT,
    certificate TEXT,
    charge_rate TEXT,
    charge_rate_dollar REAL,
    charge_rate_inr REAL,
    education TEXT,
    projects TEXT,
    employee_type TEXT,
    availability TEXT,
    linkedin_account_id TEXT,
    profile_image TEXT,
    profile_resume TEXT,
    mobile TEXT,
    email TEXT,
    location TEXT,
    gender TEXT,
    country TEXT,
    state TEXT,
    city TEXT,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE
);
""")

companies = [
    (1, "Tech Solutions", "IT Services", "$5M", "contact@tech.com", "200", "1112223333", "123 Tech Street", "MSME001", "GST001", "linkedin.com/tech", "techsolutions.com", "IT consulting firm", 1, 1, "2026-01-01"),
    (2, "Finance Corp", "Finance", "$10M", "hr@financecorp.com", "500", "2223334444", "456 Finance Road", "MSME002", "GST002", "linkedin.com/fin", "financecorp.com", "Financial services", 1, 2, "2026-02-01"),
    (3, "Marketing Pros", "Marketing", "$3M", "info@marketing.com", "100", "3334445555", "789 Market Ave", "MSME003", "GST003", "linkedin.com/mkt", "marketingpros.com", "Marketing agency", 0, 3, "2025-12-01"),
    (4, "Health Plus", "Healthcare", "$7M", "contact@healthplus.com", "300", "4445556666", "321 Health Lane", "MSME004", "GST004", "linkedin.com/healthplus", "healthplus.com", "Healthcare services", 1, 1, "2026-03-01"),
    (5, "EduWorld", "Education", "$4M", "info@eduworld.com", "150", "5556667777", "567 Edu Street", "MSME005", "GST005", "linkedin.com/eduworld", "eduworld.com", "Education services", 1, 2, "2026-04-01"),
    (6, "Retail Masters", "Retail", "$8M", "sales@retailmasters.com", "600", "6667778888", "890 Retail Road", "MSME006", "GST006", "linkedin.com/retailmasters", "retailmasters.com", "Retail chain", 1, 3, "2026-05-01"),
    (7, "Auto Experts", "Automobile", "$12M", "contact@autoexperts.com", "700", "7778889999", "567 Auto Lane", "MSME007", "GST007", "linkedin.com/autoexperts", "autoexperts.com", "Automobile services", 1, 1, "2026-06-01"),
    (8, "Foodie Haven", "Food Industry", "$6M", "support@foodiehaven.com", "250", "8889990000", "321 Food Street", "MSME008", "GST008", "linkedin.com/foodiehaven", "foodiehaven.com", "Food and Beverage", 1, 2, "2026-07-01"),
    (9, "Green Energy", "Energy", "$15M", "info@greenenergy.com", "400", "9990001111", "654 Green Avenue", "MSME009", "GST009", "linkedin.com/greenenergy", "greenenergy.com", "Renewable energy company", 1, 3, "2026-08-01"),
    (10, "Travel Now", "Travel & Tourism", "$9M", "support@travelnow.com", "350", "1112223333", "876 Travel Blvd", "MSME010", "GST010", "linkedin.com/travelnow", "travelnow.com", "Travel and tourism services", 1, 1, "2026-09-01")
]

# Insert companies
cursor.executemany("""
INSERT INTO company (id, company_name, company_category, company_turnover, email, number_of_employee, phone, company_address,
                     msme_registration_no, gst_registration_no, linkedin_url, company_website, about_company, is_active, plan_id, expire_date)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", companies)

users = [
    (1, 1, "Alice Johnson", "alice@example.com", "hashed_pw", "1234567890", 1, 1, "HR", "Admin"),
    (2, 2, "Bob Williams", "bob@example.com", "hashed_pw", "9876543210", 2, 1, "Sales", "User"),
    (3, 3, "Charlie Davis", "charlie@example.com", "hashed_pw", "5556667777", 1, 0, "IT", "Manager"),
    (4, 4, "David Smith", "david@example.com", "hashed_pw", "1112233445", 1, 1, "Healthcare", "User"),
    (5, 5, "Emma Watson", "emma@example.com", "hashed_pw", "2223344556", 2, 1, "Education", "Admin"),
    (6, 6, "Franklin Howard", "frank@example.com", "hashed_pw", "3334455667", 1, 1, "Retail", "Manager"),
    (7, 7, "Grace Lee", "grace@example.com", "hashed_pw", "4445566778", 2, 0, "Automobile", "User"),
    (8, 8, "Henry Adams", "henry@example.com", "hashed_pw", "5556677889", 1, 1, "Food Industry", "User"),
    (9, 9, "Ivy Brown", "ivy@example.com", "hashed_pw", "6667788990", 2, 1, "Energy", "Admin"),
    (10, 10, "Jack Wilson", "jack@example.com", "hashed_pw", "7778899001", 1, 1, "Travel & Tourism", "User")
]

cursor.executemany("""
INSERT INTO users (id, company_id, full_name, email, password, phone, user_type, is_active, department, permission)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", users)

profiles = [
    (1, 1, 1, "Alice Johnson", "HR Manager", "HR expert with 10 years experience", "Recruitment, Payroll", "10 years", "HR Cert", "$50/hr", 50, 4000, "MBA in HR", "Project A", "Full-Time", "Available", "alice_hr123", "img1.jpg", "resume1.pdf", "1234567890", "alice@example.com", "New York", "Female", "USA", "NY", "NYC", 100),
    (2, 2, 2, "Bob Williams", "Sales Manager", "Expert in finance sales", "Sales, Negotiation", "8 years", "Sales Cert", "$60/hr", 60, 4800, "BBA in Marketing", "Project B", "Part-Time", "Available", "bob_sales456", "img2.jpg", "resume2.pdf", "9876543210", "bob@example.com", "London", "Male", "UK", "ENG", "London", 150),
    (3, 3, 3, "Charlie Davis", "IT Consultant", "IT project management", "DevOps, Cloud", "6 years", "IT Cert", "$70/hr", 70, 5600, "BSc in CS", "Project C", "Freelancer", "Unavailable", "charlie_it789", "img3.jpg", "resume3.pdf", "5556667777", "charlie@example.com", "Mumbai", "Male", "India", "MH", "Mumbai", 200),
    (4, 4, 4, "David Smith", "Healthcare Specialist", "Experienced in medical consultancy", "Medical, Research", "12 years", "Medical Cert", "$55/hr", 55, 4400, "MBBS, MD", "Project D", "Full-Time", "Available", "david_health101", "img4.jpg", "resume4.pdf", "1112233445", "david@example.com", "Los Angeles", "Male", "USA", "CA", "LA", 120),
    (5, 5, 5, "Emma Watson", "Education Consultant", "Expert in academic training", "Teaching, Curriculum Design", "7 years", "Education Cert", "$65/hr", 65, 5200, "M.Ed in Education", "Project E", "Part-Time", "Available", "emma_edu567", "img5.jpg", "resume5.pdf", "2223344556", "emma@example.com", "Sydney", "Female", "Australia", "NSW", "Sydney", 180),
    (6, 6, 6, "Franklin Howard", "Retail Manager", "Retail business and operations", "Supply Chain, Sales", "9 years", "Retail Cert", "$58/hr", 58, 4640, "BBA in Retail", "Project F", "Freelancer", "Unavailable", "frank_retail789", "img6.jpg", "resume6.pdf", "3334455667", "frank@example.com", "Toronto", "Male", "Canada", "ON", "Toronto", 160),
    (7, 7, 7, "Grace Lee", "Automobile Engineer", "Expert in automobile design", "Automobile, CAD", "5 years", "Automobile Cert", "$62/hr", 62, 4960, "B.Tech in Mechanical Engg", "Project G", "Full-Time", "Available", "grace_auto321", "img7.jpg", "resume7.pdf", "4445566778", "grace@example.com", "Berlin", "Female", "Germany", "BE", "Berlin", 140),
    (8, 8, 8, "Henry Adams", "Food Industry Consultant", "Expert in food safety & quality", "Food Processing, Safety", "11 years", "Food Industry Cert", "$53/hr", 53, 4240, "MSc in Food Tech", "Project H", "Part-Time", "Available", "henry_food999", "img8.jpg", "resume8.pdf", "5556677889", "henry@example.com", "Paris", "Male", "France", "IDF", "Paris", 170),
    (9, 9, 9, "Ivy Brown", "Energy Consultant", "Renewable energy specialist", "Solar, Wind, Efficiency", "10 years", "Energy Cert", "$68/hr", 68, 5440, "MSc in Energy Science", "Project I", "Freelancer", "Unavailable", "ivy_energy654", "img9.jpg", "resume9.pdf", "6667788990", "ivy@example.com", "Dubai", "Female", "UAE", "DU", "Dubai", 190),
    (10, 10, 10, "Jack Wilson", "Travel & Tourism Expert", "Specialist in travel planning", "Tourism, Hospitality", "8 years", "Tourism Cert", "$57/hr", 57, 4560, "BA in Hospitality", "Project J", "Full-Time", "Available", "jack_tour123", "img10.jpg", "resume10.pdf", "7778899001", "jack@example.com", "Rome", "Male", "Italy", "LAZ", "Rome", 130)
]


# Insert profiles
cursor.executemany("""
INSERT INTO add_profile (id, user_id, company_id, profile_name, job_title, professional_summary, key_skill, experience, certificate, charge_rate, 
                         charge_rate_dollar, charge_rate_inr, education, projects, employee_type, availability, linkedin_account_id, profile_image, 
                         profile_resume, mobile, email, location, gender, country, state, city, view_count)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", profiles)

# Commit and close
conn.commit()
conn.close()

print("Database setup completed successfully!")
