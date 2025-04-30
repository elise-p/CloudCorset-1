# Welcome to **Cloud Corset** ☁️👗

Visit the website here: http://cloudcorset.s3-website-us-east-1.amazonaws.com/ 

Cloud Corset is an application where you can get daily notifications on what to wear based on today's weather.  
Right now, you can choose from 5 cities depending on where you live (I plan to expand this later).  
To sign up, just enter your email, name, and city on the website!

**Note:**  
This GitHub repo only stores the code for now because the infrastructure is deployed directly through the AWS Console.  
In the future, I plan to migrate everything to Terraform for full infrastructure-as-code.

---

## AWS Infrastructure Overview

![Cloud Corset Architecture Diagram](https://github.com/user-attachments/assets/0e0b7bc5-75aa-4078-b5be-ef47a9f74ca2)

**How it works:**
- Users sign up by submitting their email, name, and city through a static website hosted on S3.
- The form submission triggers an API Gateway, which stores the user info into DynamoDB.
- Every hour, EventBridge triggers a Step Functions workflow:
  - The Step Function checks which cities are currently between 6–7 AM local time.
  - If there are users living in those cities, it fetches the outfit recommendation.
  - The recommendation is emailed to the users via Mailgun.

---

## Things I Learned

- At first, I tried using DynamoDB `getItem` or `scan`, but realized they aren't good for retrieving multiple grouped users.  
  I had to do the DynamoDB query manually inside the Lambda to make it work.
- To avoid creating a separate EventBridge rule for each city (which doesn’t scale well), I switched to using a single hourly EventBridge ping. This way, even as the app grows, the maximum number of pings per day stays at 24.

---

## Future Improvements

- Add more cities for users to choose from.
- Fix some bugs in the `getOutfit` algorithm (sometimes there are still empty time blocks).
- Add an option for users to opt out or change their cities.
- Add CloudWatch for better analytics (currently in progress).
- Create a welcome email when users sign up (in progress).
- Schedule emails to be sent exactly at 6 AM instead of approximately between 6–7 AM.
