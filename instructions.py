# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 17:09:28 2024

@author: Bruno
"""
PRETEXT = '''
You are a controlling analyst working on behalf of the CONTRACTOR in the contract below. Your task is to read the contract, and extract the information from that contract to fill a spreadsheet.

START OF CONTRACT'''

POST_TEXT = '''
END OF CONTRACT

Your response should follow the format in this example:

Start date: 22-Jul-2024 | Text reference: This Technology Services Agreement (“Agreement”), dated 22-Jul-2024 (the “Effective Date”)

From that, extract this information

1) How many hours will the teams member perform per day (if 45 per week, answer should be 9, and if 40, answer should be 8): _ | Text reference: _
2) Contractor is allowed to bill vacations (if it says that the rate will not vary, it means a yes): YES/NO | Text reference: _
3) Overtime can be charged at an increased rate? (If yes, express it as a %, like 100% or 150%): _ | Text reference: _
4) What is the minimum engagement period in the "TECHNOLOGY SERVICES AGREEMENT" (not the Statement of Work) in months (input only the number): _ | Text reference _
5) What is the minimum engagement period in the "Statement of work" in months (input only the number or NA if missing): _ | Text reference: _
6) Is there an administrative fee that charges an extra percentage for reimbursments? If yes, put in the extra percentage, and if not, put a NO: _ | Text reference _
7) Is there a clause stating that there will be an automatic increase in rate/fees or rate adjustment? If so, is it automatic or not: YES/NO | Text reference: _
8) If there is a clause stating that there will be a rate/fees increase or adjustment, how much will it be (it should be something like CPI+5% or +5%): _ | Text reference _
9) The new rate after the increase will be rounded to next largest integer: Larger Integer/NO | Text reference _
10) Is there any special considerations in the rate increase: _
11) Repeat the rate increase clause: _
12) What's the term lenght for the first invoice, i.e the number of days that the client has to pay the contractor: _ | Text reference _
13) What's the term lenght for the every invoice after the first?: _ | Text reference _
14) Is there a clause stating that the contractor can bill the client after the first two weeks?: YES/NO | Text reference _
15) Budget Limitations - Is there a not to exceed amount in any contract? YES/NO | Text reference _
16) Is there a Money Back Guarantee Clause?: YES/NO | Text reference _
17) Is there a clause that allows the the contractor to bill the client in advance?
18) From the Statement of Work, extract the information and return a table of the roles and the rate that will be charged to the client, as well as the number of developers in each role.
19) Is there a clause regarding the backfilling at no cost: Y/N | Text reference _
20) Is there a clause related to a working interview period: Y/N | Text reference _
21) Is there a clause related to a ramp up period: Y/N | Text reference _
22) Is there a clause related to trial period: Y/N | Text reference _
23) Is there a clause related to an "On call fee": Y/N | Text reference _
24) Is there a clause or concession that mentions a volume discount: Y/N | Text reference _
25) Is there a clause mentioning a credit or milestone: Y/N | Text reference _
26) Is there a clause regarding the idle time? If yes, is the contractor allowed to bill those idle hours: YES/NO | Text reference _
27) Worked holidays will be billed at regular rate, or at an increased rate: YES/NO | Text reference _

Please don't hallucinate, make it clear when you are unsure, and make sure that answer all of the 27 questions I asked.
'''

# POST_TEXT = '''
# END OF CONTRACT

# Your response should follow the format in this example:

# Start date: 22-Jul-2024 | Text reference: This Technology Services Agreement (“Agreement”), dated 22-Jul-2024 (the “Effective Date”)

# From that, extract this information:
# 1) Contractor is allowed to bill vacations (if it says that the rate will not vary, it means a yes): YES/NO | Text reference: _
# '''
