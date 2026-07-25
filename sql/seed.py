import os
import sys
import random
from datetime import date, timedelta
import mysql.connector
import bcrypt
from faker import Faker

# Add parent directory to path to import calculations
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from calculations import calc_emi, calc_risk_score

fake = Faker('en_IN')

# Seed setting
random.seed(42)
Faker.seed(42)

def seed_database():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database="loaniq_db"
    )
    cur = conn.cursor(dictionary=True)

    print("Disabling foreign key checks and truncating tables...")
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    cur.execute("TRUNCATE TABLE collateral")
    cur.execute("TRUNCATE TABLE emi_schedule")
    cur.execute("TRUNCATE TABLE payments")
    cur.execute("TRUNCATE TABLE loans")
    cur.execute("TRUNCATE TABLE loan_applications")
    cur.execute("TRUNCATE TABLE borrowers")
    cur.execute("TRUNCATE TABLE users")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()

    print("Seeding users...")
    users_data = [
        ("admin", "admin123", "admin"),
        ("officer", "off123", "officer"),
        ("officer2", "off456", "officer"),
        ("viewer", "view123", "viewer"),
    ]
    user_ids = {}
    officer_ids = []
    
    for u, p, r in users_data:
        hashed = bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (u, hashed, r)
        )
        user_id = cur.lastrowid
        user_ids[u] = user_id
        if r in ['officer', 'admin']:
            officer_ids.append(user_id)
            
    conn.commit()

    print("Seeding 150 borrowers...")
    borrower_ids = []
    borrowers_list = []
    
    for _ in range(150):
        name = fake.name()
        email = fake.email()
        phone = fake.phone_number()[:15].replace(" ", "").replace("-", "")
        if not phone.startswith("+"):
            phone = "+91" + phone[-10:]
        phone = phone[:15]
        
        credit_score = random.choices(
            [random.randint(300, 599), random.randint(600, 699), random.randint(700, 900)],
            weights=[15, 35, 50],
            k=1
        )[0]
        
        annual_income = random.choices(
            [random.randint(250000, 500000), random.randint(500001, 1200000), random.randint(1200001, 3500000)],
            weights=[30, 50, 20],
            k=1
        )[0]
        
        emp_type = random.choice(['Salaried', 'Self-Employed', 'Business', 'Government'])
        prop_area = random.choice(['Urban', 'Semi-Urban', 'Rural'])
        existing_loans = random.choices([0, 1, 2, 3], weights=[50, 30, 15, 5], k=1)[0]
        dob = fake.date_of_birth(minimum_age=22, maximum_age=58)
        
        cur.execute("""
            INSERT INTO borrowers 
            (full_name, email, phone, credit_score, annual_income, employment_type, property_area, existing_loans, date_of_birth) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, email, phone, credit_score, annual_income, emp_type, prop_area, existing_loans, dob))
        
        b_id = cur.lastrowid
        borrower_ids.append(b_id)
        borrowers_list.append({
            'borrower_id': b_id,
            'credit_score': credit_score,
            'annual_income': annual_income,
            'employment_type': emp_type,
            'existing_loans': existing_loans,
            'dob': dob
        })
        
    conn.commit()

    print("Seeding 250 loan applications...")
    application_ids = []
    
    # Define loan type properties
    loan_types = {
        'Home Loan': {'amt_range': (1500000, 7500000), 'rate_range': (8.0, 10.5), 'tenure_range': (120, 240)},
        'Business Loan': {'amt_range': (500000, 3000000), 'rate_range': (11.0, 15.5), 'tenure_range': (12, 60)},
        'Vehicle Loan': {'amt_range': (300000, 1500000), 'rate_range': (9.0, 12.0), 'tenure_range': (36, 84)},
        'Education Loan': {'amt_range': (200000, 1200000), 'rate_range': (8.5, 11.5), 'tenure_range': (36, 120)},
        'Personal Loan': {'amt_range': (50000, 500000), 'rate_range': (12.0, 18.0), 'tenure_range': (12, 48)}
    }
    
    today = date.today()
    
    # We want to create applications over the last 2 years
    for i in range(250):
        borrower = random.choice(borrowers_list)
        b_id = borrower['borrower_id']
        credit_score = borrower['credit_score']
        annual_income = borrower['annual_income']
        emp_type = borrower['employment_type']
        existing = borrower['existing_loans']
        
        purpose = random.choices(
            ['Home Loan', 'Personal Loan', 'Education Loan', 'Vehicle Loan', 'Business Loan'],
            weights=[30, 25, 15, 15, 15],
            k=1
        )[0]
        
        cfg = loan_types[purpose]
        loan_amount = round(random.randint(*cfg['amt_range']), -4)
        interest_rate = round(random.uniform(*cfg['rate_range']), 2)
        tenure = round(random.randint(*cfg['tenure_range']), -1)
        if tenure == 0:
            tenure = 12
            
        # Calculate risk/approval details
        monthly_inc = annual_income / 12
        emi = calc_emi(loan_amount, interest_rate, tenure)
        emi_ratio = round((emi / monthly_inc) * 100, 1)
        prob = calc_risk_score(credit_score, emi_ratio, existing, emp_type)
        
        # Calculate age for ML model input
        dob = borrower.get('dob', date(1995, 1, 1))
        age = today.year - dob.year
        
        # Predict ML default probability and risk band
        from modules.ml_model import predict_loan_default
        ml_prob, ml_band = predict_loan_default({
            'credit_score': credit_score,
            'annual_income': annual_income,
            'employment_type': emp_type,
            'existing_loans': existing,
            'loan_amount': loan_amount,
            'loan_purpose': purpose,
            'interest_rate': interest_rate,
            'tenure_months': tenure,
            'age': age
        })
        
        # Decide status
        # Keep some applications pending/review, rest approved or rejected
        # Recent ones (past 30 days) have a higher chance of being pending or review
        days_ago = random.randint(0, 730)
        applied_at_date = today - timedelta(days=days_ago)
        applied_at = applied_at_date.strftime('%Y-%m-%d %H:%M:%S')
        
        is_recent = days_ago <= 30
        
        if is_recent and random.random() < 0.35:
            status = 'pending'
            reviewed_by = None
        else:
            if ml_band == "Low":
                status = "approved"
            elif ml_band == "Medium":
                status = "review"
            else:
                status = "rejected"
            
            reviewed_by = random.choice(officer_ids)

        cur.execute("""
            INSERT INTO loan_applications 
            (borrower_id, reviewed_by, loan_amount, loan_purpose, interest_rate, tenure_months, status, approval_probability, ml_default_probability, ml_risk_band, applied_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (b_id, reviewed_by, loan_amount, purpose, interest_rate, tenure, status, prob, ml_prob, ml_band, applied_at))
        
        app_id = cur.lastrowid
        application_ids.append({
            'application_id': app_id,
            'borrower_id': b_id,
            'loan_amount': loan_amount,
            'loan_purpose': purpose,
            'interest_rate': interest_rate,
            'tenure_months': tenure,
            'status': status,
            'applied_at_date': applied_at_date
        })

    conn.commit()

    print("Seeding loans, EMI schedules, payments, and collateral...")
    approved_apps = [app for app in application_ids if app['status'] == 'approved']
    
    loans_seeded = 0
    payments_seeded = 0
    schedule_seeded = 0
    collateral_seeded = 0
    
    for app in approved_apps:
        app_id = app['application_id']
        b_id = app['borrower_id']
        amount = app['loan_amount']
        purpose = app['loan_purpose']
        rate = app['interest_rate']
        tenure = app['tenure_months']
        applied_date = app['applied_at_date']
        
        # Disbursement date: 3 to 10 days after applied_at
        disbursed_date = applied_date + timedelta(days=random.randint(3, 10))
        
        # Processing fee: 1% to 2%
        processing_fee = round(amount * random.uniform(0.01, 0.02), 2)
        
        # We need to determine the status behavior of this loan
        # Types: 'active', 'closed', 'defaulted', 'npa'
        # Check if tenure has fully elapsed relative to today
        max_possible_months_paid = 0
        temp_date = disbursed_date
        while temp_date + timedelta(days=30) <= today:
            max_possible_months_paid += 1
            temp_date += timedelta(days=30)
            
        is_tenure_ended = max_possible_months_paid >= tenure
        
        if is_tenure_ended:
            # If tenure ended, loan should be closed (or defaulted/npa if they didn't pay)
            behavior = random.choices(['closed', 'npa', 'defaulted'], weights=[92, 6, 2], k=1)[0]
        else:
            # Tenure is ongoing
            behavior = random.choices(['active', 'defaulted', 'npa'], weights=[92, 5, 3], k=1)[0]
            
        # Determine how many months actually get paid
        if behavior == 'closed':
            months_to_pay = tenure
            loan_status = 'closed'
        elif behavior == 'active':
            months_to_pay = max_possible_months_paid
            loan_status = 'active'
        elif behavior == 'defaulted':
            # Missed 1 or 2 recent payments
            missed = random.choice([1, 2])
            months_to_pay = max(0, max_possible_months_paid - missed)
            loan_status = 'defaulted'
        elif behavior == 'npa':
            # Missed 3 or more payments (>= 90 days overdue)
            missed = random.randint(3, 6)
            months_to_pay = max(0, max_possible_months_paid - missed)
            loan_status = 'npa'
            
        # Calculate EMI Schedule & Payments
        emi = calc_emi(amount, rate, tenure)
        r_rate = rate / 1200
        
        opening_balance = amount
        schedule_entries = []
        payments_entries = []
        last_pay_date = None
        outstanding = amount
        
        for m in range(1, tenure + 1):
            due_date = disbursed_date + timedelta(days=30 * m)
            
            # Amortization details
            interest_comp = round(opening_balance * r_rate, 2)
            principal_comp = round(emi - interest_comp, 2)
            if principal_comp > opening_balance:
                principal_comp = opening_balance
                emi_actual = round(principal_comp + interest_comp, 2)
            else:
                emi_actual = emi
                
            closing_balance = round(opening_balance - principal_comp, 2)
            if closing_balance < 0.05:
                closing_balance = 0.00
                
            is_paid = (m <= months_to_pay) and (due_date <= today)
            
            schedule_entries.append({
                'month_number': m,
                'opening_balance': opening_balance,
                'emi_amount': emi_actual,
                'principal': principal_comp,
                'interest': interest_comp,
                'closing_balance': closing_balance,
                'due_date': due_date,
                'is_paid': is_paid
            })
            
            if is_paid:
                # Create payment record
                # Payment date is usually on or close to due_date
                pay_date = due_date + timedelta(days=random.randint(-3, 3))
                if pay_date > today:
                    pay_date = today
                    
                payments_entries.append({
                    'amount_paid': emi_actual,
                    'principal_component': principal_comp,
                    'interest_component': interest_comp,
                    'payment_date': pay_date,
                    'payment_mode': random.choice(['NEFT', 'UPI', 'Cash', 'Cheque'])
                })
                last_pay_date = pay_date
                outstanding = closing_balance
                
            opening_balance = closing_balance
            
        # Write loan record first
        cur.execute("""
            INSERT INTO loans 
            (application_id, outstanding_balance, disbursement_date, last_payment_date, loan_status, processing_fee)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (app_id, outstanding, disbursed_date, last_pay_date, loan_status, processing_fee))
        
        loan_id = cur.lastrowid
        loans_seeded += 1
        
        # Write EMI schedules
        for se in schedule_entries:
            cur.execute("""
                INSERT INTO emi_schedule 
                (loan_id, month_number, opening_balance, emi_amount, principal, interest, closing_balance, due_date, is_paid)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (loan_id, se['month_number'], se['opening_balance'], se['emi_amount'], se['principal'], se['interest'], se['closing_balance'], se['due_date'], se['is_paid']))
            schedule_seeded += 1
            
        # Write Payments
        for pe in payments_entries:
            cur.execute("""
                INSERT INTO payments 
                (loan_id, amount_paid, principal_component, interest_component, payment_date, payment_mode)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (loan_id, pe['amount_paid'], pe['principal_component'], pe['interest_component'], pe['payment_date'], pe['payment_mode']))
            payments_seeded += 1
            
        # Seed Collateral for Property, Business, Vehicle
        if purpose in ['Home Loan', 'Business Loan', 'Vehicle Loan']:
            col_type = 'Property' if purpose == 'Home Loan' else ('Vehicle' if purpose == 'Vehicle Loan' else random.choice(['FD', 'Gold', 'Property']))
            est_value = round(amount * random.uniform(1.2, 2.0), -4)
            
            descriptions = {
                'Property': [
                    "Residential Apartment, 2 BHK in semi-urban area",
                    "Independent House with land plot",
                    "Commercial retail shop space",
                    "Agricultural land plot"
                ],
                'Vehicle': [
                    "Toyota Innova SUV (2024 model)",
                    "Maruti Suzuki Swift hatchback",
                    "Tata Nexon Compact SUV",
                    "Mahindra Scorpio SUV"
                ],
                'FD': [
                    "Fixed Deposit Receipt #FD-7789412",
                    "Fixed Deposit Receipt #FD-9988224",
                    "Term Deposit Certificate with State Bank"
                ],
                'Gold': [
                    "Gold Ornaments - 22 Carat, 150 grams",
                    "Gold Bullion Bars - 24 Carat, 100 grams"
                ]
            }
            
            desc = random.choice(descriptions.get(col_type, ["Asset collateral for loan"]))
            
            cur.execute("""
                INSERT INTO collateral 
                (borrower_id, loan_id, collateral_type, estimated_value, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (b_id, loan_id, col_type, est_value, desc))
            collateral_seeded += 1

    conn.commit()
    cur.close()
    conn.close()
    
    print("\n--- Seeding Summary ---")
    print(f"Users Seeded: {len(users_data)}")
    print(f"Borrowers Seeded: 150")
    print(f"Applications Seeded: 250")
    print(f"Loans Seeded: {loans_seeded}")
    print(f"EMI Schedule Entries Seeded: {schedule_seeded}")
    print(f"Payment Records Seeded: {payments_seeded}")
    print(f"Collateral Records Seeded: {collateral_seeded}")
    print("-----------------------")
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()