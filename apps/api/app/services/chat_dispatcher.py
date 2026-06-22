from app.worker.tasks import run_chat_job_task


def dispatch_chat_job(job_id: str) -> None:
    run_chat_job_task.delay(job_id)
