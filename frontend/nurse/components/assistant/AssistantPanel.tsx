"use client";

import { FormEvent, useState } from "react";
import { Bot, ChevronDown, Send, X } from "lucide-react";

import { askAssistant, type AssistantReply } from "@/lib/api";
import { Button } from "@epicenter/shared/ui/Button";

import styles from "./AssistantPanel.module.css";

const STARTERS = [
  "Summarise the queue and longest wait",
  "Explain today's operational metrics",
  "What needs attention in the queue?",
];

export function AssistantPanel({ available }: { available: boolean }) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState(STARTERS[0]);
  const [reply, setReply] = useState<AssistantReply | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || sending || !available) return;
    setSending(true);
    setError(null);
    try {
      setReply(await askAssistant(trimmed));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The assistant could not respond.");
    } finally {
      setSending(false);
    }
  }

  return (
    <section className={`${styles.shell} ${open ? styles.open : ""}`} aria-label="Operations assistant">
      <button className={styles.trigger} disabled={!available} onClick={() => setOpen((value) => !value)} type="button">
        <Bot aria-hidden="true" size={18} />
        <span>
          <strong>Operations assistant</strong>
          <small>{available ? "Ask about queue and clinic operations" : "Reconnect to clinic data to use"}</small>
        </span>
        {open ? <X aria-hidden="true" size={18} /> : <ChevronDown aria-hidden="true" size={18} />}
      </button>
      {open ? (
        <div className={styles.body}>
          <div className={styles.starters} aria-label="Suggested questions">
            {STARTERS.map((starter) => (
              <button key={starter} onClick={() => setMessage(starter)} type="button">{starter}</button>
            ))}
          </div>
          <form className={styles.form} onSubmit={submit}>
            <label htmlFor="assistant-question">Ask a clinic operations question</label>
            <div className={styles.composer}>
              <textarea id="assistant-question" maxLength={1500} onChange={(event) => setMessage(event.target.value)} rows={2} value={message} />
              <Button disabled={sending || !message.trim()} icon={<Send aria-hidden="true" size={15} />} type="submit">
                {sending ? "Checking…" : "Ask"}
              </Button>
            </div>
          </form>
          {error ? <p className={styles.error} role="alert">{error}</p> : null}
          {reply ? (
            <article className={styles.reply} aria-live="polite">
              <div className={styles.replyHead}>
                <strong>Assistant response</strong>
                {reply.synthetic ? <span>Synthetic data</span> : null}
              </div>
              <p>{reply.content}</p>
              {reply.source_labels.length ? <small>Sources: {reply.source_labels.join(" · ")}</small> : null}
            </article>
          ) : null}
          <p className={styles.boundary}>Read and explain only. Staff still confirm every determination.</p>
        </div>
      ) : null}
    </section>
  );
}
