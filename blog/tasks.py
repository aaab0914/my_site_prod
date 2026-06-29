from celery import shared_task


@shared_task
def ping_blog_task():
    return "blog-task-ok"
