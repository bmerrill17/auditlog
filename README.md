# Audit Logger Demo

This demo microservice allows users to interact with a RESTful API in order to submit, query, and audit events of any nature. I have developed and tested it to act as a portfolio demo and to get practice creating APIs.

The microservice is written in python, uses a Snowflake database as a data storage solution, and is deployable through Docker.

The service is optimized primarily for writing events to the log (especially events of an established type) as I believe this would be
the most common case presented to the service. To this end, I chose to implement a muti-table data storage solution: one table to store
invariant data (required for all events logged), and an additional table for each event type that has 1+ variant (non-standard)
field.

As this project is primarily a demo of my development skills, I have not used a more all-in-one API solution
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
{"data": {"event_id": {"0": 1, "1": 2, "2": 3, "3": 4}, "date": {"0": "2022-04-11", "1": "2022-04-11", "2": "2022-04-11", "3": "2022-04-11"}, "time": {"0": "03:03:57.516757", "1": "03:06:39.374290", "2": "03:07:25.419086", "3": "03:08:22.498176"}, "source": {"0": "Salesforce", "1": "Salesforce", "2": "Salesforce", "3": "Server log"}, "event_type": {"0": "customer billed", "1": "added", "2": "customer billed", "3": "server crash"}, "log_text": {"0": "customer billed for Ubuntu Advantage", "1": "customer 7777 added", "2": "customer billed for Ubuntu Advantage", "3": "server 9476 crashed"}}}
```
<br>

To pull all (invariant + variant) data for one specifc log by id (e.g. event_id=1):

```
curl "localhost:5000/logs/732N4FW9JQW99MD/1"
```

Returns a 200 status code and a dictionary containing all data for the log with passed event_id. Return dicitonary:
```
{"data": {"event_id": {"0": 1}, "date": {"0": "2022-04-11"}, "time": {"0": "03:03:57.516757"}, "source": {"0": "Salesforce"}, "event_type": {"0": "customer billed"}, "log_text": {"0": "customer billed for Ubuntu Advantage"}, "customer_id": {"0": "74851"}, "bill_amount": {"0": "1999.99"}}}
```

<br>

To query the record logs based on some parameters, which can be invariant or variant fields (e.g. customer_id=8673 and
source=Salesforce):

```
curl "localhost:5000/logs/732N4FW9JQW99MD/query?customer_id=7777&source=Salesforce"
```

Returns a 200 status code and a dictionary containing all data for the logs that meet the specified parameters.
Return dictionary if no relevant POSTs yet submitted:

```
{"data": {"event_id": {"2": 3}, "date": {"2": "2022-04-11"}, "time": {"2": "03:07:25.419086"}, "source": {"2": "Salesforce"}, "event_type": {"2": "customer billed"}, "log_text": {"2": "customer billed for Ubuntu Advantage"}, "customer_id": {"2": "7777"}, "bill_amount": {"2": "1999.99"}}}
```

<br>

To post a new event:

```
curl -d "source=Salesforce&log_text=customer billed for Ubuntu Advantage&event_type=customer billed&customer_id=8888&bill_amount=1999.99" localhost:5000/logs/732N4FW9JQW99MD
```

Returns a 200 status code and a dictionary containing the new data. Return dictionary:

```
{"added log": {"date": {"0": "2022-04-11"}, "time": {"0": "02:08:40.637618"}, "event_id": {"0": 5},
"source": {"0": "Salesforce"}, "log_text": {"0": "customer billed for Ubuntu Advantage"}, "event_type": {"0": "customer billed"},
"customer_id": {"0": "8888"}, "bill_amount": {"0": "1999.99"}}}
```
