JSON files representing data coming from some APIs.

canvas.course.json is a file representing the data for a Canvas course site.  Please note the idea of "site".  A course site could represent a single section of a course, or in some cases multiple sections of a course.  

canvas.course.sections.json is a file representing the section data for a Canvas course site.  Usually there will only be one section-- but this data usually represents the connection between the Canvas LMS and the actual Student Information System at Duke.

canvas.enrollments.json is a file representing the student enrollments for a course site in Canvas.  An enrollment connects a student/user with a course site, the role of a user in the site and the section of the user to the course.

canvas.user.json is a file representing a user/student in Canvas.  This is a global reference for a user in Canvas akin to your NetID account and contains information such as email.  We use DukeID to connect users in Canvas to their Duke accounts (Single sign-on, etc.)

fuqua.couchdb.zoom.canvas_config_1583.json represents an application specific (Fuqua's Canvas Zoom LTI integration) data file for linking Zoom meetings and recordings with a Canvas course site and sections.   The name of the file is important as it is used to identify the particular Canvas course site (in this case the number 1583 is the ID of the Canvas course site).  There is one file for each Canvas course site in the CouchDB database.

fuqua.couchdb.zoom.credential-0200021.json represents the Zoom oAuth credentials for a particular user.  This file contains the access token and renewal token so that the application can make API calls on behalf of the user.  As I mentioned, we use DUKEID to link users to credentials-- so the number "0200021" represents the Duke ID of a user (in this case, me).  There is one file for each registered oAuth user.

fuqua.couchdb.zoom.meeting_report_147734772.json represents an application data file containing the details of Zoom meeting attendance for a particular meeting.   The number "147734772" represents the zoom meeting ID.  We cache the report data for meetings so we don't have to constantly hit the Zoom API to get data we have already pulled when generating reports.  After you build an API-based application-- before you go to production-- you will optimize the application and one thing to consider is the chatter and volume and cost of communicating with APIs.

The files above with "couchdb" in their name are files that I store in a CouchDB database.  The "canvas" files above are direct JSON output from API calls to the Canvas API.

fuqua.couchdb.jobpostings.12e360e8-425c-4cb1-a324-dd13aee80324.json is an unrelated sample JSON file for a different project of mine that we use for student job postings for the Fuqua Volunteer Corps.  Each job posting is a separate file.   It's a simple example.  


