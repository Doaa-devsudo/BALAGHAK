"""The agent that talks to the user, classifies the report and saves it.  Owner: Person 2 (Agent)

STUB: returns a fixed reply. Replace with the real agent (LLM + tools).
Do NOT change run_agent's name or signature.

Tools the real agent should have:
  - search_guidelines(complaint)  -> rag.search_guidelines
  - save_report(...)              -> storage.add_report, then notify.send_to_n8n
"""


def run_agent(user_input: str, history: list[dict]) -> str:
    """Return the assistant's reply in Arabic.

    history = [{"role": "user" | "assistant", "content": "..."}, ...]  (previous messages only)

    STUB: fixed reply.
    """
    return "تم استلام بلاغك (رد تجريبي)"


if __name__ == "__main__":
    history = []
    while True:
        msg = input("أنت: ")
        if msg in ("exit", "خروج"):
            break
        reply = run_agent(msg, history)
        print("النظام:", reply)
        history += [{"role": "user", "content": msg}, {"role": "assistant", "content": reply}]
