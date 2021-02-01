from atlassian import Jira
import pandas as pd
from datetime import datetime

import os
import smtplib
import imghdr
from email.message import EmailMessage
#function to retrieve tickets
#source: https://levelup.gitconnected.com/jira-api-with-python-and-pandas-c1226fd41219
def retrieve_all_query_results(jira_instance: Jira, query_string: str) -> list:
    issues_per_query = 100
    list_of_jira_issues = []

    # Get the total issues in the results set. This is one extra request but it keeps things simple.
    num_issues_in_query_result_set = jira_instance.jql(query_string, limit = 0)["total"]
    print(f"Query `{query_string}` returns {num_issues_in_query_result_set} issues")

    # Use floor division + 1 to calculate the number of requests needed
    for query_number in range(0, (num_issues_in_query_result_set // issues_per_query) + 1):
        results = jira_instance.jql(query_string, limit = issues_per_query, start = query_number * issues_per_query)
        list_of_jira_issues.extend(results["issues"])
    return list_of_jira_issues

def email_loop(data_set,subject_text,part1,part2,apostrophe,link,EMAIL_PASSWORD,EMAIL_ADDRESS,users,nomad):
    #function to retrieve matching email
    def getemail(name,data):
        for i in range(len(data)):
            if data['name'][i] == name:
                return str(data['email'][i])

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        for i in range(len(data_set)):
            msg = EmailMessage()
            msg['Subject'] = 'Your ticket ' + data_set['key'][i] +': ' + data_set['summary'][i] + subject_text
            msg['From'] = EMAIL_ADDRESS
            msg.set_content('This is a plain text email')

            if data_set['key'][i][:5] == "NOMAD":
                #if a ticket is for nomad, and created by one of nomad_ok,
                #send only to creator
                creator = getemail(data_set['creator'][i],users)
                assignee = getemail(data_set['assignee'][i],users)
                if creator in nomad:
                    msg['To'] = creator
                if assignee in nomad:
                    msg['To'] = assignee

            elif past_due['key'][i][:5] != "NOMAD":
                msg['To'] = getemail(data_set['creator'][i],users) , getemail(data_set['assignee'][i],users)

            content=apostrophe[1]+part1[1:]+link+data_set['key'][i]+part2[:-2]+apostrophe[1]
            msg.add_alternative(content[3:-3],subtype='html')
            smtp.send_message(msg)

#email account info
EMAIL_ADDRESS = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PW')

#reading in list of emails
#directory should be changed
users = pd.read_csv("C:/Users/ChongK/Desktop/lf_python/export_users.csv")



#fields of interest
foi = ["id","key", "fields.summary","fields.creator.displayName","fields.creator.accountId","fields.assignee.displayName","fields.assignee.accountId","fields.duedate"]

one_due=retrieve_all_query_results(jira_instance,"duedate > 0days AND duedate > -1days AND NOT duedate > 1days")
one_due = pd.json_normalize(one_due)
if len(one_due) != 0:
    one_due = one_due[foi]

seven_due=retrieve_all_query_results(jira_instance,"duedate > 7days AND duedate > -7days AND NOT duedate > 7days AND status in (Backlog, Queue)")
seven_due = pd.json_normalize(seven_due)
if len(seven_due) != 0:
    seven_due = seven_due[foi]

past_due=retrieve_all_query_results(jira_instance,"duedate < now() AND resolution = Unresolved AND status != Done")
past_due = pd.json_normalize(past_due)
if len(past_due) != 0:
    past_due = past_due[foi]

one_due = one_due.rename(columns={"fields.summary": "summary","fields.creator.displayName": "creator", "fields.assignee.displayName": "assignee", "fields.creator.accountId": "creatorId","fields.assignee.accountId":"accountID"})
seven_due = seven_due.rename(columns={"fields.summary": "summary","fields.creator.displayName": "creator", "fields.assignee.displayName": "assignee", "fields.creator.accountId": "creatorId","fields.assignee.accountId":"accountID"})
past_due = past_due.rename(columns={"fields.summary": "summary","fields.creator.displayName": "creator", "fields.assignee.displayName": "assignee", "fields.creator.accountId": "creatorId","fields.assignee.accountId":"accountID"})

part1_1 = """ ""<pre>
Hello! This is a friendly reminder that your ticket is due in 1 day.
You can check the details here: <a href=" """

part1_7 = """ ""<pre>
Hello! This is a friendly reminder that your ticket is due in 7 days.
You can check the details here: <a href=" """

part1_past = """ ""<pre>
Hello! This is a friendly reminder that your ticket is past due.
Please make sure to reschedule the due date for the ticket if necessary.
You can check the details here: <a href=" """

part2 =""" ">link to ticket</a>
Thank you!
</pre>""  """

sub_1 = " is due in a day!"
sub_7 = " is due in 7 days!"
sub_past = " is overdue!"

apos = """ " """
link = "https://lotusflare.atlassian.net/browse/"

#List of people in NOMAD team that would like to receive emails
nomad_ok = []

#3 iterations for 1 day due, 7 days due, and past due tickets

#one day due emails
email_loop(one_due,sub_1,part1_1,part2,apos,link,EMAIL_PASSWORD,EMAIL_ADDRESS,users,nomad_ok)

#seven day due emails
email_loop(seven_due,sub_7,part1_7,part2,apos,link,EMAIL_PASSWORD,EMAIL_ADDRESS,users,nomad_ok)

#past due emails
email_loop(past_due,sub_past,part1_past,part2,apos,link,EMAIL_PASSWORD,EMAIL_ADDRESS,users,nomad_ok)
