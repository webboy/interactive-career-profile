from app.services.chat_dispatcher import dispatch_chat_job


def test_dispatch_chat_job_enqueues_celery_task(monkeypatch):
    dispatched: list[str] = []

    def _delay(job_id: str) -> None:
        dispatched.append(job_id)

    monkeypatch.setattr("app.services.chat_dispatcher.run_chat_job_task.delay", _delay)

    dispatch_chat_job("job-123")

    assert dispatched == ["job-123"]
