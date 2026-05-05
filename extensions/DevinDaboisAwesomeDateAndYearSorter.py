#Made by DevinDaboi
#my first extension🔥🔥🔥

import os
from datetime import datetime
EXTENSION_NAME = "DevinDaboisAwesomeDateAndYearSorter"
EXTENSION_PRIORITY = 1

def file_target_resolve(context):
    filedate = datetime.fromtimestamp(os.path.getctime(context.source_path))
    month = filedate.strftime('%B')
    year = filedate.strftime('%Y')
    return {"category": f"{context.original_category}/{year}/{month}", "reason": "sorted into date and year"}
