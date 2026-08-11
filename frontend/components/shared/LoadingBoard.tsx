import styles from "./Shared.module.css";

export function LoadingBoard() {
  return (
    <div aria-label="Loading clinic readiness" aria-live="polite" className={styles.loadingBoard} role="status">
      <span className={styles.loadingLine} />
      <span className={styles.loadingLine} />
      <span className={styles.loadingLine} />
    </div>
  );
}
