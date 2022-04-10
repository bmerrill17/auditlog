import pandas as pd
import datetime as dt

logs = pd.DataFrame(
    [{"date": str(dt.datetime.now(dt.timezone.utc).date()), "time": str(dt.datetime.now(dt.timezone.utc).time()),
      "source": "Salesforce", "log_text": "customer billed for Ubuntu Advantage", "customer_id": '84084', "bill_amount": 1999.99}])

api_key_static = '732N4FW9JQW99MD'