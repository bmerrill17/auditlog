# Audit Logger Demo

This demo microservice allows users to interact with a RESTful API in order to submit, query, and audit events of any nature.

The microservice is written in python, uses a Snowflake database as a data storage solution, and is deployable through Docker.

The service is optimized primarily for writing events to the log (especially events of an established type) as I believe this would be
the most common case presented to the service. To this end, I chose to implement a muti-table data storage solution: one table to store
invariant data (required for all events logged), and an additional table for each event type that has 1+ variant (non-standard)
field.

In accordance with the instruction to make minimal use of other's code, I have not used a more all-in-one API solution
(such as one available through Django). However, in the interest of practicality and time-efficiency, I have used elements
of some frameworks (below) in the development of this microservice.

Although I am pleased with the funcitonality of the microservice, there are some areas which could use future improvements
to flesh out the microservice into a better app (below). There are also some assumptions (below), which I have made in the
development of this app.

# Frameworks Used

Pandas - data storage

Flask/Flask_RESTful - to construct basic API building blocks

SQLAlchemy - communication between application (Python) and database (Snowflake)

# Areas for improvement

Authentication - I have implemented a very simple authentication check for each API endpoint, that compares a passed API key
with a static-stored value. The static API Key is a simple string:
```
static_key = '732N4FW9JQW99MD'
```

Querying based on non-equality parameters - The current iteration of the microservice only accepts queries based on equality
check (e.g. date=2022-04-10), but in a future release, it should accept relational queries as well (e.g. date<2022-04-10)

# Assumptions

Once a new event type is created, its fields will not change subsequently

An audit log service should not have DELETE or PUT endpoints, as it would compromise the integrity of the log to allow
deletions or modifications to event records.

# Deployment

DockerHub Deployment:

Please make sure Docker is installed and user is logged in to DockerHub, then run the following command to pull, deploy,
and run the microservice:

```
docker run -p 5000:5000 -d bmerrill17/auditlogdemo
```

The service will then be running locally on a Docker container in the background and will be ready for use/testing through
the localhost's 5000 port.

# Testing

To pull basic (invariant) data for all existing logs:

```
curl "localhost:5000/logs/732N4FW9JQW99MD"
```

Returns a 200 status code and a dictionary containing standard data for all logs in the database. Return dictionary if no POSTs yet submitted:
```
{"data": {"event_id": {"0": 1, "1": 2, "2": 3, "3": 4, "4": 5, "5": 6}, "date": {"0": "2022-04-10", "1": "2022-04-10",
"2": "2022-04-10", "3": "2022-04-10", "4": "2022-04-10", "5": "2022-04-11"}, "time": {"0": "19:38:15.289146",
"1": "19:38:30.870430", "2": "19:38:37.472618", "3": "21:03:22.113793", "4": "21:09:56.030534", "5": "00:18:47.474154"},
"source": {"0": "Salesforce", "1": "Salesforce", "2": "serverlog", "3": "Salesforce", "4": "Manual entry", "5": "Salesforce"},
"event_type": {"0": "customer billed", "1": "customer billed", "2": "server crash", "3": "customer added", "4": "customer added",
"5": "customer billed"}, "log_text": {"0": "customer billed for Ubuntu Advantage", "1": "customer billed for Ubuntu Advantage Plus",
"2": "interal server 454 crashed", "3": "customer 7563 added", "4": "customer 8673 added", "5": "customer billed for Ubuntu Advantage"}}}
```
<br>

To pull all (invariant + variant) data for one specifc log by id (e.g. event_id=1):

```
curl "localhost:5000/logs/732N4FW9JQW99MD/1"
```

Returns a 200 status code and a dictionary containing all data for the log with passed event_id. Return dicitonary:
```
{"data": {"event_id": {"0": 1}, "date": {"0": "2022-04-10"}, "time": {"0": "19:38:15.289146"}, "source":
{"0": "Salesforce"}, "event_type": {"0": "customer billed"}, "log_text": {"0": "customer billed for Ubuntu Advantage"},
"customer_id": {"0": "83674"}, "bill_amount": {"0": "1999.99"}}}
```

<br>

To query the record logs based on some parameters, which can be invariant or variant fields (e.g. customer_id=8673 and
source=Salesforce):

```
curl "localhost:5000/logs/732N4FW9JQW99MD/query?customer_id=8673&source=Salesforce"
```

Returns a 200 status code and a dictionary containing all data for the logs that meet the specified parameters.
Return dictionary if no relevant POSTs yet submitted:

```
{"data": {"event_id": {"4": 6}, "date": {"4": "2022-04-11"}, "time": {"4": "00:18:47.474154"}, "source":
{"4": "Salesforce"}, "event_type": {"4": "customer billed"}, "log_text": {"4": "customer billed for Ubuntu Advantage"},
"customer_id": {"4": "8673"}, "bill_amount": {"4": "1999.99"}}}
```

<br>

To post a new event:

```
curl -d "source=Salesforce&log_text=customer billed for Ubuntu Advantage&event_type=customer billed&customer_id=34653&&bill_amount=1999.99" localhost:5000/logs/732N4FW9JQW99MD
```

Returns a 200 status code and a dictionary containing the new data. Return dictionary:

```
{"added log": {"date": {"0": "2022-04-11"}, "time": {"0": "02:08:40.637618"}, "event_id": {"0": 7},
"source": {"0": "Salesforce"}, "log_text": {"0": "customer billed for Ubuntu Advantage"}, "event_type": {"0": "customer billed"},
"customer_id": {"0": "34653"}, "bill_amount": {"0": "1999.99"}}}
```
