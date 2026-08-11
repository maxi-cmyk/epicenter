import type { ActivityEvent } from "@epicenter/shared/contracts";

import styles from "./Dashboard.module.css";

export function ActivityRail({ activity }: { activity: ActivityEvent[] }) {
  return (
    <section aria-labelledby="activity-title" className={styles.activityRail}>
      <h2 id="activity-title">What just changed</h2>
      <div>
        {activity.map((event) => (
          <article key={event.id}>
            <time>{new Date(event.occurred_at).toLocaleTimeString("en-SG", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "UTC" })}</time>
            <span className={`${styles.eventMark} ${styles[`event_${event.tone}`]}`} />
            <div><strong>{event.label}</strong><p>{event.detail}</p></div>
          </article>
        ))}
      </div>
    </section>
  );
}
