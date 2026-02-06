# adminpanel/utils.py
from django.http import HttpResponse
import csv
from django.utils.encoding import smart_str

def queryset_to_csv_response(qs, header, rows_generator, filename="export.csv"):
    """
    Create a CSV HttpResponse from an iterable of rows.
    - header: list of column names
    - rows_generator: iterable/generator yielding row iterables
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow([smart_str(h) for h in header])
    for r in rows_generator:
        writer.writerow([smart_str(x) for x in r])
    return response
