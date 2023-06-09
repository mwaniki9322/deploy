from online_marketing.celery import app
from . models import TaskItem


@app.task
def index_tasks_items_task():
    items = TaskItem.objects.order_by('id')
    index = 1

    for item in items:
        item.index = index
        item.save()

        # Increment index by 1
        index += 1

    return 'Indexing complete'
