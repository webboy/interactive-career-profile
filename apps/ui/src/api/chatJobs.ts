import { sleep } from "./client";
import { createPublicChatJob, getPublicChatJob } from "./public";
import type {
  PollChatJobOptions,
  PublicChatJobStatusResponse,
  PublicChatRequest,
} from "./types";

export async function pollPublicChatJob(
  jobId: string,
  sessionId: string,
  options: PollChatJobOptions = {},
): Promise<PublicChatJobStatusResponse> {
  const intervalMs = options.intervalMs ?? 500;
  const maxAttempts = options.maxAttempts ?? 60;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const status = await getPublicChatJob(jobId, sessionId);
    if (status.status === "completed" || status.status === "failed") {
      return status;
    }
    await sleep(intervalMs, options.signal);
  }

  throw new Error("Chat job polling timed out");
}

export async function submitAndPollPublicChat(
  body: PublicChatRequest,
  options: PollChatJobOptions = {},
): Promise<PublicChatJobStatusResponse> {
  const created = await createPublicChatJob(body);
  return pollPublicChatJob(created.job_id, body.session_id, options);
}
